from __future__ import print_function

import curses
import re

from config import *

number_regex = re.compile('^[,0-9k]*[.]?[0-9][,0-9k]*[.]?[,0-9k]*$')
class View(object):
    def __init__(self, window, pos, datum, my_config, cnum, total_num):
        self.window = window
        self.pos = pos
        self.datum = datum
        self.inst_lines = 3
        self.top = 0
        self.show_help = True
        self.progress = "done {} / {}".format(cnum, total_num)
        self.config = my_config

    def modify_annotation(self, symbol):
        if (self.pos[0], self.pos[1]) not in self.datum.marked:
            self.datum.marked[self.pos[0], self.pos[1]] = {symbol}
        elif symbol not in self.datum.marked[self.pos[0], self.pos[1]]:
            self.datum.marked[self.pos[0], self.pos[1]].add(symbol)
        elif len(self.datum.marked[self.pos[0], self.pos[1]]) == 1:
            # Given the first two conditions, we know there is a single
            # mark and it is this symbol.
            self.datum.marked.pop((self.pos[0], self.pos[1]))
        else:
            self.datum.marked[self.pos[0], self.pos[1]].remove(symbol)

    def remove_annotation(self):
        if (self.pos[0], self.pos[1]) in self.datum.marked:
            self.datum.marked.pop((self.pos[0], self.pos[1]))

    def toggle_help(self):
        self.show_help = not self.show_help

    def move_left(self):
        self.pos[1] -= 1
        if self.pos[1] < 0:
            if self.pos[0] == 0:
                self.pos[1] = 0
            else:
                nline = self.pos[0] - 1
                while nline >= 0 and len(self.datum.tokens[nline]) == 0:
                    nline -= 1
                if nline >= 0:
                    self.pos[0] = nline
                    self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1

    def move_to_start(self):
        self.pos[1] = 0

    def move_right(self):
        self.pos[1] += 1
        if self.pos[1] >= len(self.datum.tokens[self.pos[0]]):
            nline = self.pos[0] + 1
            while nline < len(self.datum.tokens) and len(self.datum.tokens[nline]) == 0:
                nline += 1
            if nline < len(self.datum.tokens):
                self.pos[0] = nline
                self.pos[1] = 0
            else:
                self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1

    def move_to_end(self):
        self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1

    def move_up(self):
        if self.pos[0] > 0:
            nline = self.pos[0] - 1
            while nline >= 0 and len(self.datum.tokens[nline]) == 0:
                nline -= 1
            if nline >= 0:
                self.pos[0] = nline
                if self.pos[1] >= len(self.datum.tokens[self.pos[0]]):
                    self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1

    def move_to_top(self):
        for line_no in range(len(self.datum.tokens)):
            if len(self.datum.tokens[line_no]) > 0:
                self.pos[0] = line_no
                if self.pos[1] >= len(self.datum.tokens[self.pos[0]]):
                    self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1
                break

    def move_down(self):
        if self.pos[0] < len(self.datum.tokens) - 1:
            nline = self.pos[0] + 1
            while nline < len(self.datum.tokens) and len(self.datum.tokens[nline]) == 0:
                nline += 1
            if nline < len(self.datum.tokens):
                self.pos[0] = nline
                if self.pos[1] >= len(self.datum.tokens[self.pos[0]]):
                    self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1

    def move_to_bottom(self):
        for line_no in range(len(self.datum.tokens) -1, -1, -1):
            if len(self.datum.tokens[line_no]) > 0:
                self.pos[0] = line_no
                if self.pos[1] >= len(self.datum.tokens[self.pos[0]]):
                    self.pos[1] = len(self.datum.tokens[self.pos[0]]) - 1
                break

    # TODO: Combine these two
    def next_number(self):
        # Find next position, use regex
        for line_no in range(self.pos[0], len(self.datum.tokens)):
            done = False
            for token_no in range(len(self.datum.tokens[line_no])):
                if line_no == self.pos[0] and token_no <= self.pos[1]:
                    continue
                if number_regex.match(self.datum.tokens[line_no][token_no]):
                    done = True
                    self.pos = [line_no, token_no]
                    break
            if done:
                break
    def previous_number(self):
        # Find next position, use regex
        for line_no in range(self.pos[0], -1, -1):
            done = False
            for token_no in range(len(self.datum.tokens[line_no]) - 1, -1, -1):
                if line_no == self.pos[0] and token_no >= self.pos[1]:
                    continue
                if number_regex.match(self.datum.tokens[line_no][token_no]):
                    done = True
                    self.pos = [line_no, token_no]
                    break
            if done:
                break

    def do_contents(self, height, width, trial=False):
        seen = False
        cpos = 0
        cline = self.inst_lines if self.show_help else 0
        for line_no, line in enumerate(self.datum.tokens):
            # If this line is above the top of what we are shwoing, skip it
            if line_no < self.top:
                continue

            for token_no, token in enumerate(line):
                cpair = (line_no, token_no)
                current = (tuple(self.pos) == cpair)

                # Determine color and annotations to show
                color = DEFAULT_COLOR
                if cpair in self.datum.marked:
                    for key in self.datum.marked[cpair]:
                        modifier = self.config.keys[key]
                        if color != DEFAULT_COLOR:
                            color = OVERLAP_COLOR
                        else:
                            color = modifier.color
                        token = modifier.start_and_end(token, 0)[0]

                # Always override if this is the cursor position
                if current: color = CURSOR_COLOR

                if token_no > 0:
                    token = ' '+ token

                length = len(token)
                if cpos + length >= width:
                    cpos = 0
                    cline += 1

                if cline >= height:
                    # Not printing as we are off the screen
                    pass
                else:
                    if not trial:
                        self.window.addstr(cline, cpos, token, curses.color_pair(color))
                    if current:
                        seen = True
                cpos += len(token)
            cline += 1
            cpos = 0
        return seen

    def render(self):
        height, width = self.window.getmaxyx()

        # First, draw instructions
        if height >= self.inst_lines and self.show_help:
            line0 = self.progress + " Colors are blue-current green-sell yellow-buy cyan-both"
            line1 = "arrows (move about), n p (next & previous number, via regex)"
            line2 = "b (mark / unmark []), / \\ (next & previous file), q (quit), h (help)"
            self.window.addstr(0, 0, "{:<80}".format(line0), curses.color_pair(HELP_COLOR))
            self.window.addstr(1, 0, "{:<80}".format(line1), curses.color_pair(HELP_COLOR))
            self.window.addstr(2, 0, "{:<80}".format(line2), curses.color_pair(HELP_COLOR))

        # Shift the top up if necessary
        if self.top > self.pos[0]:
            self.top = self.pos[0]
        # Do dry runs, shifting top down until the position is visible
        while not self.do_contents(height, width, True):
            self.top += 1

        # Next, draw contents
        self.do_contents(height, width)
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

