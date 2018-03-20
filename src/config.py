from __future__ import print_function

import string
import logging

from enum import Enum

import curses # Needed for colours

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

class AnnScope(Enum):
    character = 0
    token = 1
    line = 2
    document = 3

# TODO: Have a separate notion of 'single', 'continuous', 'discontiuous' (for the item selection), so the user could be linking a pair of discontinuous sets of lines

class AnnType(Enum):
    categorical = 0
    link = 1 #TODO: directed or undirected
    text = 2
    # TODO: sets

class Mode(Enum):
    category = 0
    read = 1
    calibrate = 2
    write_query = 3
    link = 4
    no_file = 5

class Config(object):
    def __init__(self, keys, args):
        self.args = args
        self.keys = keys
        self.annotation = AnnScope[args.ann_scope]
        self.annotation_type = AnnType[args.ann_type]

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

def get_config(args):
    return Config(
        {
            'z': KeyConfig('z', 'SELL', 2, '{', '}'),
            'x': KeyConfig('x', 'BUY', 3, '[', ']'),
            'c': KeyConfig('c', 'RATE', 7, '|', '|'),
        },
        args
    )

SPECIAL_KEYS = {'u', 'q', 'h', 'p', 'n'}
COLORS = [
    # Color combinations, (ID#, foreground, background)
    (1, curses.COLOR_BLACK, curses.COLOR_WHITE),
    (2, curses.COLOR_GREEN, curses.COLOR_BLACK),
    (3, curses.COLOR_BLUE, curses.COLOR_BLACK),
    (4, curses.COLOR_WHITE, curses.COLOR_BLACK),
    (5, curses.COLOR_BLACK, curses.COLOR_WHITE),
    (6, curses.COLOR_CYAN, curses.COLOR_BLACK),
    (7, curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    (8, curses.COLOR_BLUE, curses.COLOR_WHITE),
    (9, curses.COLOR_GREEN, curses.COLOR_WHITE),
    (10, curses.COLOR_RED, curses.COLOR_BLACK),
    (11, curses.COLOR_RED, curses.COLOR_WHITE),
    (12, curses.COLOR_CYAN, curses.COLOR_BLACK),
    (13, curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    (14, curses.COLOR_CYAN, curses.COLOR_WHITE),
    (15, curses.COLOR_MAGENTA, curses.COLOR_WHITE),
    (16, curses.COLOR_YELLOW, curses.COLOR_BLACK),
]

DEFAULT_COLOR = 4
OVERLAP_COLOR = 6
LINK_COLOR = 2
HELP_COLOR = 4
REF_COLOR = 3
IS_LINKED_COLOR = 16

COMPARE_DISAGREE_COLOR = 10
COMPARE_REF_COLORS = [12, 13]

input_action_list = [
    ('leave-query-mode', [
        (Mode.write_query, 10), # 10 is enter on OS X
        (Mode.write_query, '?'), ]),
    ('delete-query-char', [
        (Mode.write_query, 263),
        (Mode.write_query, 127), # 263 and 127 are backspace on OS X
        (Mode.write_query, '!'), ]), 
    ('enter-query-mode', [
        '\\', ]), 
    ('move-up', [
        curses.KEY_UP, 'i', ]),
    ('move-down', [
        curses.KEY_DOWN, 'o', ]),
    ('move-left', [
        curses.KEY_LEFT, 'j', ]),
    ('move-right', [
        curses.KEY_RIGHT, ';', ]),
    ('jump-up', [
        337, # 337 is shift up on OS X
        'I', ]),
    ('jump-down', [
        336, # 336 is shift down on OS X
        'O', ]),
    ('jump-left', [
        curses.KEY_SLEFT, 'J', ]),
    ('jump-right', [
        curses.KEY_SRIGHT, ':', ]),
    ('move-link-up', [
        (Mode.link, 337), (Mode.link, 'I'), ]),
    ('move-link-down', [
        (Mode.link, 336), (Mode.link, 'O'), ]),
    ('move-link-left', [
        (Mode.link, curses.KEY_SLEFT), (Mode.link, 'J'), ]),
    ('move-link-right', [
        (Mode.link, curses.KEY_SRIGHT), (Mode.link, ':'), ]),
    ('page-up', [
        curses.KEY_PPAGE, ]),
    ('page-down', [
        curses.KEY_NPAGE, ]),
    ('extend-up', [
        'k', ]),
    ('extend-down', [
        'l', ]),
    ('extend-left', [
        'm', ]),
    ('extend-right', [
        '/', ]),
    ('contract-up', [
        'K', ]),
    ('contract-down', [
        'L', ]),
    ('contract-left', [
        'M', ]),
    ('contract-right', [
        '?', ]),
    ('next-match', [
        'n', 'P', ]),
    ('prev-match', [
        'p', 'N', ]),
    ('help-toggle', [
        'h', ]),
    ('next-file', [
        ']', (Mode.no_file, ']'), (Mode.no_file, '.'), ]),
    ('prev-file', [
        '[', (Mode.no_file, '['), (Mode.no_file, ','), ]),
    ('quit', [
        'Q', ]),
    ('save-and-quit', [
        'q', ]),
    ('save', [
        's', ]),
    ('create-link', [
        (Mode.link, 'D'), ]),
    ('create-link-and-move', [
        (Mode.link, 'd'), ]),
    ('edit-annotation', [
        ]),
    ('remove-annotation', [
        (None, 'u'), ]),
    ('update-num', [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ]),
]
input_to_action = {}
for action, options in input_action_list:
    for opt in options:
        if type(opt) == int:
            opt = (None, opt)
        elif type(opt) == str:
            opt = (None, ord(opt))
        elif type(opt) == tuple and type(opt[1]) == str:
            opt = (opt[0], ord(opt[1]))
        assert opt not in input_to_action, "input {} used twice".format(opt)
        input_to_action[opt] = action

for char in string.printable:
    pair = (Mode.write_query, ord(char))
    if pair not in input_to_action:
        input_to_action[pair] = 'add-to-query'

