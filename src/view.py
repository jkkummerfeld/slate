from __future__ import print_function

import logging
import curses
import re
import sys

from config import *
from data import Span, span_compare_ge, span_compare_le

class View(object):
    def __init__(self, window, cursor, linking_pos, datum, my_config, cnum, total_num, show_help):
        self.window = window
        self.cursor = cursor
        self.linking_pos = linking_pos
        self.datum = datum
        self.top = max(0, cursor.start[0] - self.window.getmaxyx()[0] - 10)
        self.show_help = show_help
        self.progress = "file {} / {}".format(cnum + 1, total_num)
        self.config = my_config
        self.must_show_linking_pos = False

        if self.config.args.prevent_self_links and self.cursor == self.linking_pos:
            # TODO: In this case move the linking pos along one step
            pass

    def instructions(self):
        if self.config.annotation_type == AnnType.link:
            return [
                self.progress,
                "Colors are highlight:possible-link green:current blue:link",
                "arrows (move blue about), shift + arrows (move green)",
                "d + shift (mark as linked), d (mark as linked and move green down)",
                "u (undo visible links), / \\ (next & previous file), q (quit), h (help)",
            ]
        else:
            return [
                self.progress,
                "Colors are highlight-current blue-linked (TODO update)",
                "arrows (move about), n p (next & previous number, via regex)",
                "b (mark / unmark []), / \\ (next & previous file), q (quit), h (help)",
            ]

    def toggle_help(self):
        self.show_help = not self.show_help

    def shift_view(self, down=False):
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
###            logging.info("Moving linking pos")
###        logging.info("Move {} {} {}".format(self.cursor, direction, distance))
        new_pos = mover.edited(direction, 'move', distance, maxjump)
###        logging.info("Moving {} to {}".format(self.cursor, new_pos))
        if self._check_move_allowed(move_link, new_pos):
            if move_link:
                self.linking_pos = new_pos
            else:
                self.cursor = new_pos
    
    def adjust(self, direction, distance, change, maxjump=False):
        new_pos = self.cursor.edited(direction, change, distance, maxjump)
        if self._check_move_allowed(False, new_pos):
            self.cursor = new_pos
    
    def put_cursor_beside_link(self):
        self.cursor = self.linking_pos.edited('previous')

    def marking_to_color(self, marking):
        name = DEFAULT_COLOR
        modifier = curses.A_BOLD
        has_link = False
        has_ref = False
        for mark in marking:
            if mark == 'cursor':
                modifier += curses.A_UNDERLINE
            elif mark == 'link':
                has_link = True
            elif mark == 'ref':
                has_ref = True
            elif mark == 'linked':
                name = IS_LINKED_COLOR
            elif mark in self.config.labels:
                if name != DEFAULT_COLOR:
                    name = OVERLAP_COLOR
                else:
                    name = self.config.get_color_for_label(mark)
            elif mark.startswith("compare-"):
                if 'ref' in mark:
                    if 'False' in mark:
                        name = COMPARE_DISAGREE_COLOR
                    else:
                        count = int(mark.split("-")[-2])
                        name = COMPARE_REF_COLORS[count - 1]
                else:
                    if name == DEFAULT_COLOR:
                        name = COMPARE_DISAGREE_COLOR
###                    key = mark.split("-")[-1]
###                    if key in self.config.labels:
###                        name = self.config.get_color_for_label(mark)
        # Override cases
        if has_link:
            name = LINK_COLOR
        elif has_ref:
            name = REF_COLOR

        return curses.color_pair(name) + modifier

    def do_contents(self, height, width, markings, trial=False):
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
                first_span = Span(AnnScope.character, self.datum.doc, (line_no, 0, 0))

            # Set
            row += 1
            column = 0
            for token_no, token in enumerate(line):
                # Check if we are going on to the next line and adjust
                # accordingly.
                space_before = 1 if column > 0 else 0
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
                last_span = Span(AnnScope.character, self.datum.doc, (line_no, token_no, end_pos))

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

                    if not trial:
                        self.window.addstr(row, column, char, color)
                    column += 1

                if row >= height:
                    break

        # Tracks if the cursor is vsible
        seen_cursor = False
        seen_linking_pos = False
        if first_span is not None and last_span is not None:
###            logging.info("Trying {} vs. {} {}".format(self.cursor, first_span, last_span))
            cmp_first = self.cursor.compare(first_span) 
            cmp_last = self.cursor.compare(last_span) 
            seen_cursor = cmp_first in span_compare_ge and \
                    cmp_last in span_compare_le
###            logging.info("Got {} {}".format(cmp_first, cmp_last))

            if self.linking_pos is not None:
                cmp_first = self.linking_pos.compare(first_span) 
                cmp_last = self.linking_pos.compare(last_span) 
                seen_linking_pos = cmp_first in span_compare_ge and \
                        cmp_last in span_compare_le
###        logging.info("{} in {} {} ? {}".format(self.cursor, first_span, last_span, seen_cursor))

        if self.must_show_linking_pos:
            return seen_linking_pos
        else:
            return seen_cursor


    def render(self, current_search, current_typing):
        logging.info("Render with '{}' and '{}'".format(current_search, current_typing))
        if self.show_help:
            self.render_help()
            return

        height, width = self.window.getmaxyx()

        # Get content for extra lines
        extra_text_lines = []
        if len(current_search) > 0: extra_text_lines.append(current_search)
        if len(current_typing) > 0: extra_text_lines.append(current_typing)

        # Get colors for content
        markings = self.datum.get_all_markings(self.cursor, self.linking_pos)
        logging.info("markings: {}".format(markings))
        for key in markings:
            marks = markings[key]
            if 'cursor' in marks:
                for mark in marks:
                    if mark.startswith("label:"):
                        extra_text_lines.append(mark)
                    elif 'compare-' in mark and 'ref' not in mark:
                        parts = mark.split("-")
                        count = int(parts[-2])
                        label = parts[-1]
                        extra_text_lines.append("{} marked as {}".format(count, label))

        # First, plan instructions
        main_height = height - 1
        space_needed = len(extra_text_lines)
        if space_needed > 0:
            space_needed += 1
        elif len(self.datum.other_annotations) > 0:
            extra_text_lines.append("")
            space_needed = 2

        if height >= space_needed:
            main_height = main_height - space_needed

        # Shift the top up if necessary
        if self.config.annotation != AnnScope.document:
            if self.must_show_linking_pos:
                if self.top > self.linking_pos.start[0]:
                    self.top = self.linking_pos.start[0]
            else:
                if self.top > self.cursor.start[0]:
                    self.top = self.cursor.start[0]

        # Do dry runs, shifting top down until the position is visible
        while not self.do_contents(main_height, width, markings, True):
            self.top += 1

        # Next, draw contents
        self.do_contents(main_height, width, markings)

        if main_height < height:
            if len(extra_text_lines) > 0:
                row = main_height
                self.window.addstr(row, 0, "-" * width)
                row += 1

                color = curses.color_pair(HELP_COLOR) + curses.A_BOLD

                # Last, draw the text being typed
                for content in extra_text_lines:
                    text = content
                    fmt = "{:<"+ str(width) +"}"
                    self.window.addstr(row, 0, fmt.format(text), color)
                    row += 1

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
        dir_key = ',' if at_end else '.'
        line1 = "Type 'q' to quit, or '"+ dir_key+ "' to go back."
        self.window.addstr(pos, 0, line0, curses.color_pair(HELP_COLOR) + curses.A_BOLD)
        self.window.addstr(pos + 1, 0, line1, curses.color_pair(DEFAULT_COLOR) + curses.A_BOLD)
        self.window.refresh()

