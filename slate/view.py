from __future__ import print_function

import _curses
import logging
import curses
import re
import sys

from .config import *
from .data import Span, span_compare_ge, span_compare_le

class View(object):
    def __init__(self, window, cursor, linking_pos, datum, my_config, cnum, total_num, prev_view=None):
        self.window = window
        self.cursor = cursor
        self.linking_pos = linking_pos
        self.datum = datum
        self.top = max(0, cursor.start[0] - self.window.getmaxyx()[0] - 10)
        self.show_help = False
        self.show_progress = False
        self.progress = "file {} / {}".format(cnum + 1, total_num)
        self.show_legend = False
        self.show_current_mark = False
        self.legend = []
        self.config = my_config
        self.line_numbers = False
        if prev_view is not None:
            self.show_help = prev_view.show_help
            self.show_progress = prev_view.show_progress
            self.show_legend = prev_view.show_legend
            self.line_numbers = prev_view.line_numbers

        self.last_moved_pos = cursor

        if self.config.annotation_type == 'categorical':
            for label, info in self.config.labels.items():
                self.legend.append(("{} {}".format(label, "+".join(info[0])), label))

        if self.config.args.prevent_self_links and self.cursor == self.linking_pos:
            # TODO: In this case move the linking pos along one step
            pass

    def instructions(self):
        shared = [
            "Misc      | ] [                   | save and go to next ] / previous [ file",
            "          | q Q                   | quit with or without saving            ",
            "          | s                     | save the current file                  ",
        ]
        if self.config.annotation_type == 'link':
            return [
                "Keybindings - to hide/show this, type 'h'",
                "Colours are underline:selected, green:linking, blue:linked, yellow:has_link",
                "Type      | Key                   | Affect                             ",
                "----------|-----------------------|------------------------------------",
                "Move      | j or LEFT             | move selected item to the left     ",
                "          | J or [SHIFT + LEFT]   | move linking item to the left      ",
                "          | i or UP               | move selected item up a line       ",
                "          | I or [SHIFT + UP]     | move linking item up a line        ",
                "          | o or DOWN             | move selected item down a line     ",
                "          | O or [SHIFT + DOWN]   | move linking item down a line      ",
                "          | ; or RIGHT            | move selected item to the right    ",
                "          | : or [SHIFT + RIGHT]  | move linking item to the right     ",
                "Annotate  | d                     | create a link and move down / right",
                "          | D                     | create a link                      ",
                "          | u                     | undo all annotations for this item ",
            ] + shared
        else:
            return [
                "Keybindings - to hide/show this, type 'h'",
                "Underline is current item, colours are labels",
                "Type      | Key                   | Affect                           ",
                "----------|-----------------------|----------------------------------",
                "Move      | j or LEFT             | move to the left                 ",
                "          | J or [SHIFT + LEFT]   | go to the start of the line      ",
                "          | i or UP               | move up a line                   ",
                "          | I or [SHIFT + UP]     | go to first line                 ",
                "          | o or DOWN             | move down a line                 ",
                "          | O or [SHIFT + DOWN]   | go to last line                  ",
                "          | ; or RIGHT            | move to the right                ",
                "          | : or [SHIFT + RIGHT]  | go to the end of the line        ",
                "Span Edit | m   /                 | extend left or right             ",
                "          | k   l                 | contract left or right           ",
                "Annotate  | SPACE then a, s, or d | [un]mark this item as a, s, or d ",
                "          | u                     | undo annotation on this item     ",
            ] + shared

    def toggle_help(self):
        self.show_help = not self.show_help
    def toggle_progress(self):
        self.show_progress = not self.show_progress
    def toggle_legend(self):
        self.show_legend = not self.show_legend
    def toggle_current_mark(self):
        self.show_current_mark = not self.show_current_mark

    def shift_view(self, down=False):
        self.last_moved_pos = None
        if down: self.top += 10
        else: self.top -= 10

    def _check_move_allowed(self, move_link, new_pos):
        if self.linking_pos is None:
            return True
        if self.config.args.prevent_forward_links:
            if move_link and self.cursor > new_pos:
                return False
            if (not move_link) and self.linking_pos < new_pos:
                return False
        if self.config.args.prevent_self_links:
            if move_link and self.cursor == new_pos:
                return False
            if (not move_link) and self.linking_pos == new_pos:
                return False
        return True

    def move(self, direction, distance, maxjump=False, move_link=False):
        # TODO: if self links are prevented, but forward links are allowed,
        # then skip over when moving.
        mover = self.cursor
        if move_link:
            mover = self.linking_pos
###            logging.debug("Moving linking pos")
###        logging.debug("Move {} {} {}".format(self.cursor, direction, distance))
        new_pos = mover.edited(direction, 'move', distance, maxjump)
###        logging.debug("Moving {} to {}".format(self.cursor, new_pos))
        if self._check_move_allowed(move_link, new_pos):
            if move_link:
                self.linking_pos = new_pos
            else:
                self.cursor = new_pos
            self.last_moved_pos = new_pos
        elif self.linking_pos is not None:
            # Move as far as possible
            if self.config.args.prevent_self_links:
                if move_link:
                    self.linking_pos = self.cursor.edited('next', 'move', 1, False)
                    self.last_moved_pos = self.linking_pos
                else:
                    self.cursor = self.linking_pos.edited('previous', 'move', 1, False)
                    self.last_moved_pos = self.cursor
            else:
                if move_link:
                    self.linking_pos = self.cursor
                else:
                    self.cursor = self.linking_pos
                self.last_moved_pos = self.cursor

    def search(self, query, direction, count, maxjump=False, move_link=False):
        logging.debug("Search {} {} {} {} {}".format(query, direction, count, maxjump, move_link))
        new_pos = None
        if query is None:
            if len(self.datum.disagreements) == 0:
                new_pos = self.datum.get_next_unannotated(self.cursor, self.linking_pos, direction, move_link)
                if new_pos == self.linking_pos or new_pos is None:
                    new_pos = self.datum.get_next_self_link(self.cursor, self.linking_pos, direction, move_link)
            else:
                new_pos = self.datum.get_next_disagreement(self.cursor, self.linking_pos, direction, move_link)
        else:
            mover = self.cursor
            if move_link:
                mover = self.linking_pos
            new_pos = mover.search(query, direction, count, maxjump)

        if new_pos is not None:
            if self._check_move_allowed(move_link, new_pos):
                if move_link:
                    self.linking_pos = new_pos
                else:
                    self.cursor = new_pos
                self.last_moved_pos = new_pos

    def adjust(self, direction, distance, change, maxjump, link):
        changer = self.cursor
        if link and self.linking_pos is not None:
            changer = self.linking_pos

        new_pos = changer.edited(direction, change, distance, maxjump)
        if self._check_move_allowed(link, new_pos):
            if link:
                self.linking_pos = new_pos
            else:
                self.cursor = new_pos
    
    def put_cursor_beside_link(self):
        self.cursor = self.linking_pos.edited('previous')

    def marking_to_color(self, marking):
        name = DEFAULT_COLOR
        modifier = curses.A_BOLD
        has_link = False
        has_ref = False
        has_self_link = False
        for mark in marking:
            if mark == 'cursor':
                modifier += curses.A_UNDERLINE
            elif mark == 'link':
                has_link = True
            elif mark == 'ref':
                has_ref = True
            elif mark == 'self-link':
                has_self_link = True
            elif mark == 'linked':
                name = IS_LINKED_COLOR
            elif mark in self.config.labels:
                if name != DEFAULT_COLOR:
                    name = OVERLAP_COLOR
                else:
                    name = self.config.get_color_for_label(mark)
            elif mark.startswith("compare-"):
                if 'ref' in mark:
                    count = int(mark.split("-")[-2])
                    if 'True' in mark and 'last' not in mark:
                        # First, cases where this is related to the current linking line
                        if name == DEFAULT_COLOR or name == COMPARE_DISAGREE_COLOR:
                            if count == 0:
                                name = REF_COLOR
                            else:
                                name = COMPARE_REF_COLOR
                    elif count > 0 and 'last' in mark:
                        # If unrelated, but there is a disagreement, indicate it
                        if name == DEFAULT_COLOR:
                            name = COMPARE_DISAGREE_COLOR
                else:
                    count = int(mark.split("-")[-2])
                    if name == DEFAULT_COLOR:
                        if count == 0:
                            key = mark.split("-")[-1]
                            if key in self.config.labels:
                                name = self.config.get_color_for_label(key)
                        else:
                            name = COMPARE_DISAGREE_COLOR
###                    key = mark.split("-")[-1]
###                    if key in self.config.labels:
###                        name = self.config.get_color_for_label(mark)
        # Override cases
        if has_link:
            if has_ref:
                if has_self_link:
                    name = SELF_LINK_COLOR
                else:
                    name = IS_LINKED_COLOR
            else:
                name = LINK_COLOR
        elif has_ref:
            name = REF_COLOR

        return curses.color_pair(name) + modifier

    def do_contents(self, height, width, markings, number_width, trial=False):
        # For linked items, colour them to indicate it
        # For labels, colour them always, and add beginning / end
        # For freeform text, include it at the bottom

        # Row and column indicate the position on the screen, while line and
        # token indicate the position in the text.
        first_span = None
        last_span = None
        row = -1
        for line_no, line in enumerate(self.datum.doc.tokens):
            # If this line is above the top of what we are shwoing, skip it
            if line_no < self.top:
                continue
            if row >= height:
                break
            if first_span is None:
                first_span = Span('character', self.datum.doc, (line_no, 0, 0))

            # Set
            row += 1
            column = number_width
            if (not trial) and column > 0:
                self.window.addstr(row, 0, str(line_no), curses.color_pair(LINE_NUMBER_COLOR))
            for token_no, token in enumerate(line):
                # Check if we are going on to the next line and adjust
                # accordingly.
                space_before = 1 if column > number_width else 0
                wide_token = False
                if column + len(token) + space_before > width:
                    if token_no != 0:
                        column = 0
                        row += 1
                        space_before = 0
                    else:
                        wide_token = True

                # If this takes us off the screen, stop
                if row >= height:
                    break

                end_pos = len(token) - 1
                if wide_token:
                    end_pos = width - column - space_before - 1
                last_span = Span('character', self.datum.doc, (line_no, token_no, end_pos))

                for char_no, char in enumerate(token):
                    if column >= width:
                        column = 0
                        row += 1
                        if row >= height:
                            break

                    # Allow multiple layers of color, with the more specific
                    # domainating
                    if space_before > 0:
                        if not trial:
                            mark = []
                            if () in markings:
                                mark = markings[()]
                            if (line_no,) in markings:
                                mark = markings[(line_no,)]
                            if (line_no, token_no, -1) in markings:
                                mark = markings[line_no, token_no, -1]
                            color = self.marking_to_color(mark)
                            self.window.addstr(row, column, ' ', color)
                        column += 1
                        space_before = 0

                    color = self.marking_to_color([])

                    if not trial:
                        mark = []
                        if () in markings:
                            mark = markings[()]
                        if (line_no,) in markings:
                            mark = markings[(line_no,)]
                        if (line_no, token_no) in markings:
                            mark = markings[line_no, token_no]
                        if (line_no, token_no, char_no) in markings:
                            mark = markings[line_no, token_no, char_no]
                        color = self.marking_to_color(mark)
                        try:
                            self.window.addstr(row, column, char, color)
                        except _curses.error as e:
                            logging.warn("Error caught in drawing extra lines 2")
                    column += 1

                if row >= height:
                    break

        # Tracks if we can see where we moved to
        seen_last_moved_pos = True
        if first_span is not None and last_span is not None:
            if self.last_moved_pos is not None:
                cmp_first = self.last_moved_pos.compare(first_span)
                cmp_last = self.last_moved_pos.compare(last_span)
                seen_last_moved_pos = cmp_first in span_compare_ge and \
                        cmp_last in span_compare_le
        return seen_last_moved_pos


    def render(self, current_search, current_typing):
        height, width = self.window.getmaxyx()

###        logging.debug("Render with '{}' and '{}'".format(current_search, current_typing))
        if self.show_help:
            if height < 20 or width < 80:
                raise Exception("Window too small - must be at least 80x20")
            self.render_help()
            return

        # Get content for extra lines
        extra_text_lines = []
        if self.show_progress: extra_text_lines.append(self.progress)
        if self.show_legend:
            cur = []
            length = 0
            for val, colour in self.legend:
                if length + 3 + len(val) > width:
                    extra_text_lines.append(cur)
                    cur = []
                    length = 0
                if length > 0:
                    length += 3
                length += len(val)
                cur.append((val, colour))
            extra_text_lines.append(cur)
        if len(current_search) > 0: extra_text_lines.append(current_search)
        if len(current_typing) > 0: extra_text_lines.append(current_typing)

        # Get colors for content
        markings = self.datum.get_all_markings(self.cursor, self.linking_pos)
###        logging.debug("markings: {}".format(markings))
        if self.show_current_mark:
            for key in markings:
                logging.debug("marking: {}: {}".format(key, markings[key]))
                marks = markings[key]
                if 'cursor' in marks:
                    for mark in marks:
                        if mark in self.config.labels:
                            extra_text_lines.append("Current: "+ mark)
                        elif 'compare-' in mark and 'ref' not in mark:
                            parts = mark.split("-")
                            count = len(self.datum.other_annotations) - int(parts[-2])
                            label = parts[-1]
                            extra_text_lines.append("{} marked as {}".format(count, label))

        # First, plan instructions
        main_height = height
        space_needed = len(extra_text_lines)
        if space_needed > 0:
            space_needed += 1
        elif len(self.datum.other_annotations) > 0:
            pass

        if height >= space_needed:
            main_height = main_height - space_needed

        # Shift the top up if necessary
        if self.config.annotation != 'document':
            if self.last_moved_pos is not None:
                if self.top > self.last_moved_pos.start[0]:
                    self.top = self.last_moved_pos.start[0]
                if self.top < self.last_moved_pos.start[0] - main_height:
                    self.top = self.last_moved_pos.start[0] - main_height

        # Work out width
        main_width = width
        number_width = 0
        if self.line_numbers:
            count = 1
            lines = len(self.datum.doc.lines)
            while lines > 1:
                count += 1
                lines /= 10
            number_width = count
            main_width -= number_width

        # Do dry runs, shifting top down until the position is visible
        while not self.do_contents(main_height, main_width, markings, number_width, True):
            self.top += 1

        # Next, draw contents
        self.do_contents(main_height, main_width, markings, number_width)

        if main_height < height:
            if len(extra_text_lines) > 0:
                row = main_height
                self.window.addstr(row, 0, "-" * width)
                row += 1

                color = curses.color_pair(HELP_COLOR) + curses.A_BOLD

                # Last, draw the text being typed
                for content in extra_text_lines:
                    try:
                        if isinstance(content, list):
                            position = 0
                            for text, tcolor in content:
                                if position != 0:
                                    self.window.addstr(row, position, " | ", color)
                                    position += 3
                                name = self.config.get_color_for_label(tcolor)
                                tcolor = curses.color_pair(name) + curses.A_BOLD
                                self.window.addstr(row, position, text, tcolor)
                                position += len(text)
                        else:
                            text = content
                            fmt = "{:<"+ str(width) +"}"
                            self.window.addstr(row, 0, fmt.format(text), color)
                        row += 1
                    except _curses.error as e:
                        logging.warn("Error caught in drawing extra lines")

        self.window.refresh()

    def render_help(self):
        self.window.clear()
        height, width = self.window.getmaxyx()

        row = 0
        color = curses.color_pair(HELP_COLOR) + curses.A_BOLD
        for line in self.instructions():
            fmt = "{:<"+ str(width) +"}"
            self.window.addstr(row, 0, fmt.format(line), color)
            row += 1

        self.window.refresh()

    def render_edgecase(self, at_end):
        self.window.clear()
        height, width = self.window.getmaxyx()
        pos = int(height / 2)
        edge = 'end' if at_end else 'start'
        line0 = "At "+ edge +" in the files."
        dir_key = '[' if at_end else ']'
        line1 = "Type 'q' to quit, or '"+ dir_key+ "' to go back."
        self.window.addstr(pos, 0, line0, curses.color_pair(HELP_COLOR) + curses.A_BOLD)
        self.window.addstr(pos + 1, 0, line1, curses.color_pair(DEFAULT_COLOR) + curses.A_BOLD)
        self.window.refresh()

