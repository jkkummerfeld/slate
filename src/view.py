from __future__ import print_function

import curses
import re
import sys

from config import *

number_regex = re.compile('^[,0-9k]*[.]?[0-9][,0-9k]*[.]?[,0-9k]*$')
class View(object):
    def __init__(self, window, cursor, linking_pos, datum, my_config, cnum, total_num, show_help):
        self.window = window
        self.cursor = cursor
        self.linking_pos = linking_pos
        self.datum = datum
        self.top = max(0, cursor[0] - self.window.getmaxyx()[0] - 10)
        self.show_help = show_help
        self.progress = "file {} / {}".format(cnum + 1, total_num)
        self.config = my_config
        self.must_show_linking_pos = False

    def instructions(self):
        if self.config.annotation_type == AnnType.link:
            return [
                self.progress + "  Colors are highlight:possible-link green:current blue:link",
                "arrows (move blue about), shift + arrows (move green)",
                "d + shift (mark as linked), d (mark as linked and move green down)",
                "u (undo visible links), / \\ (next & previous file), q (quit), h (help)",
            ]
        else:
            return [
                self.progress + "  Colors are highlight-current blue-linked (TODO update)",
                "arrows (move about), n p (next & previous number, via regex)",
                "b (mark / unmark []), / \\ (next & previous file), q (quit), h (help)",
            ]

    def toggle_help(self):
        self.show_help = not self.show_help

    def _get_pos_to_move(self, move_link):
        return self.linking_pos if move_link else self.cursor

    def _check_move_allowed(self, move_link, move_down):
        if self.linking_pos[0] < 0:
            return True
        elif self.linking_pos[0] > self.cursor[0]:
            return True
        elif self.linking_pos[1] > self.cursor[1]:
            return True
        else:
            return move_link == move_down

    def move_left(self, move_link=False):
        if self.config.annotation == AnnScope.line:
            return
        if not self._check_move_allowed(move_link, False):
            return

        pos = self._get_pos_to_move(move_link)
        pos[1] -= 1
        if pos[1] < 0:
            if pos[0] == 0:
                pos[1] = 0
            else:
                nline = pos[0] - 1
                while nline >= 0 and len(self.datum.tokens[nline]) == 0:
                    nline -= 1
                if nline >= 0:
                    pos[0] = nline
                    pos[1] = len(self.datum.tokens[pos[0]]) - 1

    def move_to_start(self, move_link=False):
        if self.config.annotation == AnnScope.line:
            return
        if not self._check_move_allowed(move_link, False):
            return
        pos = self._get_pos_to_move(move_link)
        pos[1] = 0

    def move_right(self, move_link=False):
        if self.config.annotation == AnnScope.line:
            return
        if not self._check_move_allowed(move_link, True):
            return

        pos = self._get_pos_to_move(move_link)
        pos[1] += 1
        if pos[1] >= len(self.datum.tokens[pos[0]]):
            nline = pos[0] + 1
            while nline < len(self.datum.tokens) and len(self.datum.tokens[nline]) == 0:
                nline += 1
            if nline < len(self.datum.tokens):
                pos[0] = nline
                pos[1] = 0
            else:
                pos[1] = len(self.datum.tokens[pos[0]]) - 1

    def move_to_end(self, move_link=False):
        if self.config.annotation == AnnScope.line:
            return
        if not self._check_move_allowed(move_link, True):
            return
        pos = self._get_pos_to_move(move_link)
        pos[1] = len(self.datum.tokens[pos[0]]) - 1

    def move_up(self, move_link=False):
        if not self._check_move_allowed(move_link, False):
            return
        pos = self._get_pos_to_move(move_link)
        if pos[0] > 0:
            nline = pos[0] - 1
            while nline >= 0 and len(self.datum.tokens[nline]) == 0:
                nline -= 1
            if nline >= 0:
                pos[0] = nline
                if pos[1] >= len(self.datum.tokens[pos[0]]):
                    pos[1] = len(self.datum.tokens[pos[0]]) - 1

    def move_to_top(self, move_link=False):
        if not self._check_move_allowed(move_link, False):
            return
        pos = self._get_pos_to_move(move_link)
        for line_no in range(len(self.datum.tokens)):
            if len(self.datum.tokens[line_no]) > 0:
                pos[0] = line_no
                if pos[1] >= len(self.datum.tokens[pos[0]]):
                    pos[1] = len(self.datum.tokens[pos[0]]) - 1
                break

    def move_down(self, move_link=False):
        if not self._check_move_allowed(move_link, True):
            return
        pos = self._get_pos_to_move(move_link)
        if pos[0] < len(self.datum.tokens) - 1:
            nline = pos[0] + 1
            while nline < len(self.datum.tokens) and len(self.datum.tokens[nline]) == 0:
                nline += 1
            if nline < len(self.datum.tokens):
                pos[0] = nline
                if pos[1] >= len(self.datum.tokens[pos[0]]):
                    pos[1] = len(self.datum.tokens[pos[0]]) - 1

    def move_to_bottom(self, move_link=False):
        if not self._check_move_allowed(move_link, True):
            return
        pos = self._get_pos_to_move(move_link)
        for line_no in range(len(self.datum.tokens) -1, -1, -1):
            if len(self.datum.tokens[line_no]) > 0:
                pos[0] = line_no
                if pos[1] >= len(self.datum.tokens[pos[0]]):
                    pos[1] = len(self.datum.tokens[pos[0]]) - 1
                break

    def next_disagreement(self, reverse=False):
        npos = self.datum.next_disagreement(self.cursor, self.linking_pos,
                reverse)
        self.cursor, self.linking_pos = npos
    def previous_disagreement(self):
        self.next_disagreement(True)

    # TODO: Combine these two
    def next_number(self):
        if self.config.annotation == AnnScope.line:
            return
        # Find next position, use regex
        for line_no in range(self.cursor[0], len(self.datum.tokens)):
            done = False
            for token_no in range(len(self.datum.tokens[line_no])):
                if line_no == self.cursor[0] and token_no <= self.cursor[1]:
                    continue
                if number_regex.match(self.datum.tokens[line_no][token_no]):
                    done = True
                    self.cursor = [line_no, token_no]
                    break
            if done:
                break
    def previous_number(self):
        if self.config.annotation == AnnScope.line:
            return
        # Find next position, use regex
        for line_no in range(self.cursor[0], -1, -1):
            done = False
            for token_no in range(len(self.datum.tokens[line_no]) - 1, -1, -1):
                if line_no == self.cursor[0] and token_no >= self.cursor[1]:
                    continue
                if number_regex.match(self.datum.tokens[line_no][token_no]):
                    done = True
                    self.cursor = [line_no, token_no]
                    break
            if done:
                break

    def do_contents(self, height, width, trial=False):
        # For linked items, colour them to indicate it
        # For labels, colour them always, and add beginning / end
        # For freeform text, include it at the bottom

        # Tracks if the cursor is vsible
        seen_cursor = None
        seen_linking_pos = None

        # Row and column indicate the position on the screen, while line and
        # token indicate the position in the text.
        row = -1
        for line_no, line in enumerate(self.datum.tokens):
            # If this line is above the top of what we are shwoing, skip it
            if line_no < self.top:
                continue

            # Set
            row += 1
            column = 0
            for token_no, token in enumerate(line):
                pos = (line_no, token_no)
                cursor = (self.cursor[0], self.cursor[1])
                linking_pos = (self.linking_pos[0], self.linking_pos[1])
                # TODO: Only calculate color if it is going to be displayed
                token, color, test = self.datum.get_marked_token(pos, cursor,
                        linking_pos)

                length = len(token)

                # Check if we are going on to the next line and adjust
                # accordingly.
                space_before = 1 if column > 0 else 0
                if column + length + space_before >= width:
                    column = 0
                    row += 1
                elif space_before > 0:
                    length += space_before
                    token = " "+ token

                if row >= height:
                    # Not printing as we are off the screen.  Must wait till
                    # here in case we have a line wrapping above.
                    if self.datum.check_equal(pos, cursor):
                        seen_cursor = False
                    if self.datum.check_equal(pos, linking_pos):
                        seen_linking_pos = False
                    break
                else:
                    if not trial:
                        color = curses.color_pair(color)
                        self.window.addstr(row, column, token, color)
                    if self.datum.check_equal(pos, cursor) and seen_cursor is None:
                        seen_cursor = True
                    if self.datum.check_equal(pos, linking_pos) and seen_linking_pos is None:
                        seen_linking_pos = True

                column += len(token)

        if self.must_show_linking_pos:
            return seen_linking_pos
        else:
            return seen_cursor


    def render(self):
        height, width = self.window.getmaxyx()

        # First, plan instructions
        main_height = height - 1
        inst = self.instructions()
        if height >= len(inst) and self.show_help:
            main_height = main_height - len(inst)

        # Shift the top up if necessary
        if self.must_show_linking_pos:
            if self.top > self.linking_pos[0]:
                self.top = self.linking_pos[0]
        else:
            if self.top > self.cursor[0]:
                self.top = self.cursor[0]
        # Do dry runs, shifting top down until the position is visible
        while not self.do_contents(main_height, width, True):
            self.top += 1

        # Next, draw contents
        self.do_contents(main_height, width)

        # Last, draw instructions
        if height >= len(inst) and self.show_help:
            cur = main_height
            for line in inst:
                fmt = "{:<"+ str(width) +"}"
                self.window.addstr(cur, 0, fmt.format(line), curses.color_pair(HELP_COLOR))
                cur += 1

        self.window.refresh()

    def render_edgecase(self, edge):
        self.window.clear()
        height, width = self.window.getmaxyx()
        pos = int(height / 2)
        line0 = "At "+ edge +" in the files."
        dir_key = '/'
        if edge == 'end':
            dir_key = '\\'
        line1 = "Type 'q' to quit, or '"+ dir_key+ "' to go back."
        self.window.addstr(pos, 0, line0, curses.color_pair(HELP_COLOR))
        self.window.addstr(pos + 1, 0, line1, curses.color_pair(DEFAULT_COLOR))
        self.window.refresh()

