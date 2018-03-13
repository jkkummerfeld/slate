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

    def instructions(self):
        if self.config.annotation_type == AnnType.link:
            return [
                "----------------------------------------------------------------------------",
                self.progress + "  Colors are highlight:possible-link green:current blue:link",
                "arrows (move blue about), shift + arrows (move green)",
                "d + shift (mark as linked), d (mark as linked and move green down)",
                "u (undo visible links), / \\ (next & previous file), q (quit), h (help)",
                "Colours: match file0 file1 current",
            ]
        else:
            return [
                "----------------------------------------------------------------------------",
                self.progress + "  Colors are highlight-current blue-linked (TODO update)",
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
        elif move_link:
            return self.cursor >= new_pos
        else:
            return self.linking_pos <= new_pos

    def move(self, direction, distance, maxjump=False, move_link=False):
        mover = self.cursor
        if move_link:
            mover = self.linking_pos
        logging.info("Move {} {} {}".format(self.cursor, direction, distance))
        new_pos = mover.edited(direction, 'move', distance, maxjump)
        logging.info("Moving {} to {}".format(self.cursor, new_pos))
        if self._check_move_allowed(move_link, new_pos):
            if move_link:
                self.linking_pos = new_pos
            else:
                self.cursor = new_pos
    
    def put_cursor_beside_link(self):
        self.cursor = self.linking_pos.edited('previous')

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
                if column + len(token) + space_before >= width:
                    column = 0
                    row += 1
                    space_before = 0

                # If this takes us off the screen, stop
                if row >= height:
                    break
                last_span = Span(AnnScope.character, self.datum.doc, (line_no, token_no, len(token) - 1))

                for char_no, char in enumerate(token):
                    # Allow multiple layers of color, with the more specific
                    # domainating
                    color = curses.color_pair(DEFAULT_COLOR) + curses.A_BOLD
                    if not trial:
                        name = DEFAULT_COLOR
                        if () in markings:
                            name = markings[()]
                        if (line_no,) in markings:
                            name = markings[(line_no,)]
                        if (line_no, token_no) in markings:
                            name = markings[line_no, token_no]
                        if (line_no, token_no, char_no) in markings:
                            name = markings[line_no, token_no, char_no]
                        color = curses.color_pair(name) + curses.A_BOLD

                    if space_before > 0:
                        if not trial:
                            self.window.addstr(row, column, ' ', color)
                        column += 1
                        space_before = 0
                    if not trial:
                        self.window.addstr(row, column, char, color)
                    column += 1

        # Tracks if the cursor is vsible
        seen_cursor = False
        seen_linking_pos = False
        if first_span is not None and last_span is not None:
            cmp_first = self.cursor.compare(first_span) 
            cmp_last = self.cursor.compare(last_span) 
            seen_cursor = cmp_first in span_compare_ge and \
                    cmp_last in span_compare_le
            logging.info("Got {} {}".format(cmp_first, cmp_last))

            if self.linking_pos is not None:
                cmp_first = self.linking_pos.compare(first_span) 
                cmp_last = self.linking_pos.compare(last_span) 
                seen_linking_pos = cmp_first in span_compare_ge and \
                        cmp_last in span_compare_le
        logging.info("{} in {} {} ? {}".format(self.cursor, first_span, last_span, seen_cursor))

        if self.must_show_linking_pos:
            return seen_linking_pos
        else:
            return seen_cursor


    def render(self, current_search):
        height, width = self.window.getmaxyx()

        # First, plan instructions
        main_height = height - 1
        inst = self.instructions()
        space_needed = 0
        if self.show_help: space_needed += len(inst)
        if len(current_search) > 0: space_needed += 1
        if height >= space_needed:
            main_height = main_height - space_needed

        # Shift the top up if necessary
        if self.config.annotation != AnnScope.document:
            if self.must_show_linking_pos:
                if self.top > self.linking_pos[0]:
                    self.top = self.linking_pos[0]
            else:
                if self.top > self.cursor.start[0]:
                    self.top = self.cursor.start[0]

        # Get colors for content
        markings = self.datum.get_all_markings(self.cursor, self.linking_pos)
        logging.info(markings)

        # Do dry runs, shifting top down until the position is visible
        while not self.do_contents(main_height, width, markings, True):
            self.top += 1

        # Next, draw contents
        self.do_contents(main_height, width, markings)

        # Then, draw instructions
        if main_height < (height - 1) and self.show_help:
            cur = main_height
            for line in inst:
                if line.startswith("Colours"):
                    words = line.strip().split()
                    cur_col = 0
                    for word in words:
                        content = word +" "
                        base_color = curses.color_pair(HELP_COLOR)
                        if word == 'match': base_color = curses.color_pair(COMPARE_REF_COLORS[1])
                        elif word == 'file0': base_color = curses.color_pair(REF_COLOR)
                        elif word == 'file1': base_color = curses.color_pair(COMPARE_REF_COLORS[0])
                        elif word == 'current': base_color = curses.color_pair(LINK_COLOR)
                        self.window.addstr(cur, cur_col, content, base_color + curses.A_BOLD)
                        cur_col += len(content)
                    cur += 1
                else:
                    fmt = "{:<"+ str(width) +"}"
                    self.window.addstr(cur, 0, fmt.format(line), curses.color_pair(HELP_COLOR) + curses.A_BOLD)
                    cur += 1

        # Last, draw the text being typed
        if main_height < (height - 1) and len(current_search) > 0:
            cur = main_height
            if self.show_help: cur += len(inst)
            text = current_search
            fmt = "{:<"+ str(width) +"}"
            self.window.addstr(cur, 0, fmt.format(text), curses.color_pair(HELP_COLOR) + curses.A_BOLD)

        self.window.refresh()

    def render_edgecase(self, edge):
        self.window.clear()
        height, width = self.window.getmaxyx()
        pos = int(height / 2)
        line0 = "At "+ edge +" in the files."
        dir_key = ',' if edge == 'end' else '.'
        line1 = "Type 'q' to quit, or '"+ dir_key+ "' to go back."
        self.window.addstr(pos, 0, line0, curses.color_pair(HELP_COLOR) + curses.A_BOLD)
        self.window.addstr(pos + 1, 0, line1, curses.color_pair(DEFAULT_COLOR) + curses.A_BOLD)
        self.window.refresh()

