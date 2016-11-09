#!/usr/bin/env python3

from __future__ import print_function

import curses
import sys
import re
import glob

def print_usage(args):
    lines = [
        "Usage:",
        "{} <file with a list of files to annotate>".format(args[0]),
        "Options:",
        "    -log <filename>, default = 'files_still_to_do']",
        "    -output [overwrite, inline, standoff], default = standoff"
        "",
        "For further information, see README.md",
        "",
        "For example:",
        ">> find . | grep 'tok$' > filenames_todo",
        ">> {} filenames_todo -log do_later".format(args[0]),
        "... do some work, then quit, go away, come back...",
        ">> {} do_later -log do_even_later".format(args[0]),
    ]
    print('\n'.join(lines))

class KeyConfig(object):
    def __init__(self, key, label, color=2, start='{', end='}'):
        self.key = key
        self.label = label
        self.color = color
        self.start_mark = start
        self.end_mark = end

    def start(self, token, length=-1):
        ans = self.start_mark
        if length < 0:
            ans += self.label
        elif length > 0:
            ans += self.label[:length+1]
        ans += token
        return ans, self.color

    def end(self, token, length=-1):
        ans = token
        if length < 0:
            ans += self.label
        elif length > 0:
            ans += self.label[:length+1]
        ans += self.end_mark
        return ans, self.color

    def start_and_end(self, token, length=-1):
        ans = self.start_mark
        if length < 0:
            ans += self.label
        elif length > 0:
            ans += self.label[:length+1]

        ans += token

        if length < 0:
            ans += self.label
        elif length > 0:
            ans += self.label[:length+1]
        ans += self.end_mark
        return ans, self.color

class Config(object):
    def __init__(self, keys, min_unique_length=-1, overwrite=False):
        self.keys = keys
        self.unique_length = min_unique_length
        self.overwrite = overwrite

    def set_by_file(self, filename):
        self.keys = {}
        for line in open(filename):
            parts = line.strip().split()

            label = parts[0]

            # Default is to numerically assign keys in order, starting at 1
            key = str(len(self.keys) + 1)
            if len(parts) > 1:
                key = parts[1]
            if len(key) > 1:
                raise Exception("This key is too long: "+ key)
            if key in SPECIAL_KEYS:
                raise Exception("This key is a reserved value: "+ key)

            start = '{'
            if len(parts) > 2:
                start = parts[2]
            end = '}'
            if len(parts) > 3:
                end = parts[3]

            color = 0
            if len(parts) > 4:
                # TODO
                pass

            config = KeyConfig(key, label, color, start, end)

        # Find the shortest length at which prefixes of the labels are unique
        self.unique_length = -1
        for i in range(1, min(len(self.keys[key]) for key in self.keys)):
            done = True
            seen = set()
            for key in self.keys:
                start = self.keys[key][:i+1]
                if start in seen:
                    done = False
                    break
                seen.add(start)
            if done:
                self.unique_length = i
                break

def read_filenames(arg):
    if len(glob.glob(arg)) == 0:
        raise Exception("Cannot open / find '{}'".format(arg))
    filenames = [line.strip() for line in open(arg).readlines()]
    failed = []
    for filename in filenames:
        if len(glob.glob(filename)) == 0:
            failed.append(filename)
    if len(failed) > 0:
        raise Exception("File errors:\n{}".format('\n'.join(failed)))
    return filenames

class Datum(object):
    def __init__(self, filename, config):
        self.filename = filename
        self.config = config
        self.tokens = []
        self.marked = {}

        wrappers = {}
        for key in config.keys:
            modifier = config.keys[key]
            start = modifier.start('', config.unique_length)
            end = modifier.end('', config.unique_length)
            wrappers[start, end] = modifier

        for line in open(filename):
            self.tokens.append([])
            for token in line.split():
                # TODO: Handle ordering issue better
                change = True
                while change:
                    change = False
                    for start, end in wrappers:
                        if token.startswith(start[0]) and token.endswith(end[0]):
                            change = True
                            token = token[len(start[0]):-len(end[0])]
                            position = (len(self.tokens) - 1, len(self.tokens[-1]))
                            if position not in self.marked:
                                self.marked[position] = set()
                            self.marked[position].add(wrappers[start, end].key)
                self.tokens[-1].append(token)

    def write_out(self, filename=None):
        out_filename = filename
        if filename is None:
            out_filename = self.filename
        if not config.overwrite:
            out_filename += ".annotated"
        out = open(out_filename, 'w')
        for line_no, line in enumerate(self.tokens):
            for token_no, token in enumerate(line):
                position = (line_no, token_no)
                if position in self.marked:
                    for key in self.marked[position]:
                        modifier = config.keys[key]
                        token = modifier.start_and_end(token, 0)[0]
                print(token, end=" ", file=out)
            print("", file=out)

number_regex = re.compile('^[,0-9k]*[.]?[0-9][,0-9k]*[.]?[,0-9k]*$')
class View(object):
    def __init__(self, window, pos, datum, config, cnum, total_num):
        self.window = window
        self.pos = pos
        self.datum = datum
        self.inst_lines = 3
        self.top = 0
        self.show_help = True
        self.progress = "done {} / {}".format(cnum, total_num)
        self.config = config

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
                        modifier = config.keys[key]
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

DEFAULT_CONFIG = Config(
    {
        's': KeyConfig('s', 'SELL', 2, '{', '}'),
        'b': KeyConfig('b', 'BUY', 3, '[', ']'),
        'r': KeyConfig('r', 'RATE', 7, '|', '|'),
    },
    0
)

SPECIAL_KEYS = {'u', 'q', 'h', 'p', 'n'}
COLORS = [
    # Color combinations, (ID#, foreground, background)
    (1, curses.COLOR_BLUE, curses.COLOR_WHITE),
    (2, curses.COLOR_GREEN, curses.COLOR_BLACK),
    (3, curses.COLOR_YELLOW, curses.COLOR_BLACK),
    (4, curses.COLOR_WHITE, curses.COLOR_BLACK),
    (5, curses.COLOR_BLACK, curses.COLOR_WHITE),
    (6, curses.COLOR_CYAN, curses.COLOR_BLACK),
    (7, curses.COLOR_MAGENTA, curses.COLOR_BLACK),
]
OVERLAP_COLOR = 6
DEFAULT_COLOR = 4
CURSOR_COLOR = 1
HELP_COLOR = 5

def annotate(window, config, filenames):
    out_filename = "files_still_to_do"
    overwrite = False
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-log' and len(sys.argv) > i + 1:
            out_filename = sys.argv[i + 1]
        if sys.argv[i] == '-overwrite':
            overwrite = True
    out = open(out_filename, "w")

    # Set color combinations
    for num, fore, back in COLORS:
        curses.init_pair(num, fore, back)

    # No blinking cursor
    curses.curs_set(0)

    cfilename = 0
    datum = Datum(filenames[cfilename], config)
    view = View(window, [0, 0], datum, config, cfilename, len(filenames))

    while True:
        # Draw screen
        view.render()

        # Get input
        user_input = window.getch()
        if user_input == curses.KEY_LEFT: view.move_left()
        elif user_input == curses.KEY_SLEFT: view.move_to_start()
        elif user_input == curses.KEY_RIGHT: view.move_right()
        elif user_input == curses.KEY_SRIGHT: view.move_to_end()
        elif user_input == curses.KEY_UP: view.move_up()
        elif user_input == 337: view.move_to_top() # SHIFT + UP, Worked out on a Mac by hand...
        elif user_input == curses.KEY_DOWN: view.move_down()
        elif user_input == 336: view.move_to_bottom() # SHIFT + DOWN, Worked out on a Mac by hand...
        elif user_input == ord("n"): view.next_number()
        elif user_input == ord("h"): view.toggle_help()
        elif user_input == ord("p"): view.next_number()
        elif user_input == ord("u"): view.remove_annotation()
        elif user_input == ord("/"):
            datum.write_out()
            # get next
            cfilename += 1
            if len(filenames) <= cfilename:
                break
            datum = Datum(filenames[cfilename], config)
            view.datum = datum

            # Reset, but do not rename as we want the view to have the same
            # objects still
            view.pos = [0, 0]
        elif user_input == ord("\\"):
            datum.write_out()
            # get previous
            if cfilename > 0:
                cfilename -= 1
            datum = Datum(filenames[cfilename], config)
            view.datum = datum

            # Reset, but do not rename as we want the view to have the same
            # objects still
            view.pos = [0, 0]
        elif user_input == ord("q"): break
        elif user_input in [ord('s'), ord('b'), ord('r')]:
            view.modify_annotation(chr(user_input))
        window.clear()

    print('\n'.join(filenames[cfilename:]), file=out)
    out.close()

def read_config(filename):
    # TODO: this is a stub, actually implement reading a config
    keys = DEFAULT_CONFIG.keys
    unique_length = 0
    overwrite = True
    return Config(keys, unique_length, overwrite)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage(sys.argv)
        sys.exit(1)

    ### Start interface
    filenames = read_filenames(sys.argv[1])
    config = DEFAULT_CONFIG
    if len(sys.argv) > 2:
        config = read_config(sys.argv[2])
    curses.wrapper(annotate, config, filenames)
