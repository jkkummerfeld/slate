from __future__ import print_function

import curses
import re

from config import *

number_regex = re.compile('^[,0-9k]*[.]?[0-9][,0-9k]*[.]?[,0-9k]*$')
class View(object):
    def __init__(self, window, pos, datum, my_config, cnum, total_num):
        self.window = window
        self.pos = pos
        self.ref = None
        self.datum = datum
        self.top = 0
        self.show_help = True
        self.progress = "done {} / {}".format(cnum, total_num)
        self.config = my_config

        if self.config.annotation == AnnType.link:
            pass

    def instructions(self):
        return [
            self.progress + " Colors are blue-current green-sell yellow-buy cyan-both",
            "arrows (move about), n p (next & previous number, via regex)",
            "b (mark / unmark []), / \\ (next & previous file), q (quit), h (help)",
        ]

    def toggle_help(self):
        self.show_help = not self.show_help

    def move_left(self):
        if self.config.annotation == AnnScope.line:
            return
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
        if self.config.annotation == AnnScope.line:
            return
        self.pos[1] = 0

    def move_right(self):
        if self.config.annotation == AnnScope.line:
            return
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
        if self.config.annotation == AnnScope.line:
            return
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
        if self.config.annotation == AnnScope.line:
            return
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
        if self.config.annotation == AnnScope.line:
            return
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
        cline = 0
        for line_no, line in enumerate(self.datum.tokens):
            # If this line is above the top of what we are shwoing, skip it
            if line_no < self.top:
                continue

            line_color = DEFAULT_COLOR
            space_color = DEFAULT_COLOR
            current = False

            line_start = ''
            if self.config.annotation == AnnScope.line:
                for key in self.datum.get_markings(line_no):
                    modifier = self.config.keys[key]
                    if line_color != DEFAULT_COLOR:
                        line_color = OVERLAP_COLOR
                    else:
                        line_color = modifier.color
                    line_start += key + " "
                if len(line_start) > 0:
                    line_start += "| "
                # Always override if this is the cursor position
                if self.pos[0] == line_no:
                    current = True
                    line_color = CURSOR_COLOR

                # Set the space color to match
                space_color = line_color

            for token_no, token in enumerate(line):
                if token_no == 0:
                    token = line_start + token

                text_color = line_color
                if self.config.annotation == AnnScope.token:
                    cpair = (line_no, token_no)
                    current = (tuple(self.pos) == cpair)
                    for key in self.datum.get_markings(cpair):
                        modifier = self.config.keys[key]
                        if text_color != DEFAULT_COLOR:
                            text_color = OVERLAP_COLOR
                        else:
                            text_color = modifier.color
                        token = modifier.start_and_end(token, 0)[0]

                    # Always override if this is the cursor position
                    if current: text_color = CURSOR_COLOR

                length = len(token)
                if token_no > 0 and cpos > 0: length += 1 # To cover the space
                if cpos + length >= width:
                    cpos = 0
                    cline += 1

                if cline >= height:
                    # Not printing as we are off the screen
                    pass
                else:
                    if not trial:
                        if token_no > 0 and cpos > 0:
                            color = curses.color_pair(space_color)
                            self.window.addstr(cline, cpos, " ", color)
                            color = curses.color_pair(text_color)
                            self.window.addstr(cline, cpos + 1, token, color)
                        else:
                            color = curses.color_pair(text_color)
                            self.window.addstr(cline, cpos, token, color)
                    if current:
                        seen = True

                if token_no > 0 and cpos > 0:
                    cpos += 1
                cpos += len(token)
            cline += 1
            cpos = 0
        return seen

    def render(self):
        height, width = self.window.getmaxyx()

        # First, plan instructions
        main_height = height
        inst = self.instructions()
        if height >= len(inst) and self.show_help:
            main_height -= len(inst) + 2

        # Shift the top up if necessary
        if self.top > self.pos[0]:
            self.top = self.pos[0]
        # Do dry runs, shifting top down until the position is visible
        while not self.do_contents(height, width, True):
            self.top += 1

        # Next, draw contents
        self.do_contents(height, width)

        # Last, draw instructions
        if height >= len(inst) and self.show_help:
            cur = main_height + 1
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

