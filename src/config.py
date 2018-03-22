from __future__ import print_function

import string
import logging

from enum import Enum

import curses # Needed for colours

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

name_to_color = {
    "green": 2,
    "blue": 3,
    "white": 4,
    "cyan": 6,
    "magenta": 7,
    "red": 10,
    "yellow": 16,
}

DEFAULT_COLOR = 4
OVERLAP_COLOR = 6
LINK_COLOR = 2
HELP_COLOR = 4
REF_COLOR = 3
IS_LINKED_COLOR = 16

COMPARE_DISAGREE_COLOR = 10
COMPARE_REF_COLORS = [12, 13]

class AnnScope(Enum):
    character = 0
    token = 1
    line = 2
    document = 3

# TODO: Have a separate notion of 'single', 'continuous', 'discontiuous' (for the item selection), so the user could be linking a pair of discontinuous sets of lines

class AnnType(Enum):
    categorical = 0
    link = 1 #TODO: directed or undirected
    # TODO: sets

class Mode(Enum):
    category = 0
    read = 1
    calibrate = 2
    write_query = 3
    link = 4
    no_file = 5
    write_label = 6


input_action_list = {
    'leave-query-mode': [
        (Mode.write_query, 10), # 10 is enter on OS X
        (Mode.write_query, '?'), ],
    'delete-query-char': [
        (Mode.write_query, 263),
        (Mode.write_query, 127), # 263 and 127 are backspace on OS X
        (Mode.write_query, '!'), ], 
    'assign-text-label': [
        (Mode.write_label, 10), # 10 is enter on OS X
        (Mode.write_label, '?'), ],
    'delete-label-char': [
        (Mode.write_label, 263),
        (Mode.write_label, 127), # 263 and 127 are backspace on OS X
        (Mode.write_label, '!'), ], 
    'enter-query-mode': [
        '\\', ], 
    'enter-label-mode': [
        't', ], 
    'move-up': [
        curses.KEY_UP, 'i', ],
    'move-down': [
        curses.KEY_DOWN, 'o', ],
    'move-left': [
        curses.KEY_LEFT, 'j', ],
    'move-right': [
        curses.KEY_RIGHT, ';', ],
    'jump-up': [
        337, # 337 is shift up on OS X
        'I', ],
    'jump-down': [
        336, # 336 is shift down on OS X
        'O', ],
    'jump-left': [
        curses.KEY_SLEFT, 'J', ],
    'jump-right': [
        curses.KEY_SRIGHT, ':', ],
    'move-link-up': [
        (Mode.link, 337), (Mode.link, 'I'), ],
    'move-link-down': [
        (Mode.link, 336), (Mode.link, 'O'), ],
    'move-link-left': [
        (Mode.link, curses.KEY_SLEFT), (Mode.link, 'J'), ],
    'move-link-right': [
        (Mode.link, curses.KEY_SRIGHT), (Mode.link, ':'), ],
    'page-up': [
        curses.KEY_PPAGE, ],
    'page-down': [
        curses.KEY_NPAGE, ],
    'extend-up': [
        'k', ],
    'extend-down': [
        'l', ],
    'extend-left': [
        'm', ],
    'extend-right': [
        '/', ],
    'contract-up': [
        'K', ],
    'contract-down': [
        'L', ],
    'contract-left': [
        'M', ],
    'contract-right': [
        '?', ],
    'next-match': [
        'n', 'P', ],
    'prev-match': [
        'p', 'N', ],
    'help-toggle': [
        'h', ],
    'next-file': [
        ']', (Mode.no_file, ']'), (Mode.no_file, '.'), ],
    'prev-file': [
        '[', (Mode.no_file, '['), (Mode.no_file, ','), ],
    'quit': [
        'Q', ],
    'save-and-quit': [
        'q', ],
    'save': [
        's', ],
    'create-link': [
        (Mode.link, 'D'), ],
    'create-link-and-move': [
        (Mode.link, 'd'), ],
    'edit-annotation': [
        ],
    'remove-annotation': [
        (None, 'u'), ],
    'update-num': [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ],
}

key_names = {
    curses.KEY_UP: "UP",
    curses.KEY_DOWN: "DOWN",
    curses.KEY_LEFT: "LEFT",
    curses.KEY_RIGHT: "RIGHT",
    curses.KEY_SLEFT: "SHIFT-LEFT",
    curses.KEY_SRIGHT: "SHIFT-RIGHT",
    curses.KEY_NPAGE: "NPAGE",
    curses.KEY_PPAGE: "PPAGE",
}
for c in string.printable:
    if c not in string.whitespace:
        key_names[ord(c)] = c
    elif c == ' ':
        key_names[ord(c)] = 'SPACE'
    elif c == '\n':
        key_names[ord(c)] = 'ENTER'

class Config(object):
    def __init__(self, args, labels={}):
        self.args = args
        self.labels = labels
        self.annotation = AnnScope[args.ann_scope]
        self.annotation_type = AnnType[args.ann_type]
        self.input_to_action = {}

        # Core key set as defined above
        for action in input_action_list:
            for opt in input_action_list[action]:
                if type(opt) == int:
                    self.add_keybinding(None, opt, action)
                elif type(opt) == str:
                    self.add_keybinding(None, ord(opt), action)
                elif type(opt) == tuple and type(opt[1]) == str:
                    self.add_keybinding(opt[0], ord(opt[1]), action)
                elif type(opt) == tuple and type(opt[1]) == int:
                    self.add_keybinding(opt[0], opt[1], action)

        # Fill in all other characters for searching
        for char in string.printable:
            if char != ' ' and char in string.whitespace:
                continue
            self.add_keybinding(Mode.write_query, ord(char), 'add-to-query',
                    False, True)
            self.add_keybinding(Mode.write_label, ord(char), 'add-to-label',
                    False, True)

        # Fill annotation keys
        for key in self.labels:
            self.add_keybinding(Mode.category, ord(key), 'edit-annotation')

        if args.config_file is not None:
            for line in open(args.config_file):
                # Set general command keybindings
                if line.startswith("Input:"):
                    _, action, mode, key = line.strip().split()
                    if len(key) > 2 and key[0] == key[-1] == '`':
                        key = int(key[1:-1])
                    elif len(key) > 1:
                        for name in key_names:
                            if key_names[name] == key:
                                key = name
                    else:
                        key = ord(key)
                    if mode == 'None':
                        mode = None
                    else:
                        mode = Mode[mode]
                    self.add_keybinding(mode, key, action, True)
                elif line.startswith("Label:"):
                    _, key, name, color = line.strip().split()
                    self.labels[key] = (name, color)

    def get_color_for_label(self, mark):
        name = self.labels[mark][1]
        return name_to_color[name]

    def add_keybinding(self, mode, key, action, overwrite=False, skip_ok=False):
        pair = (mode, key)
        if pair in self.input_to_action:
            if skip_ok:
                return
            if not overwrite:
                raise Exception("input {} used twice".format(pair))
        self.input_to_action[pair] = action

    def __str__(self):
        ans = []

        for mode, key in self.input_to_action:
            action = self.input_to_action[mode, key]
            if mode is None:
                mode = 'None'
            else:
                mode = mode.name
            key = key_names.get(key, "`{}`".format(str(key)))

            ans.append("Input: {:<25} {:<20} {}".format(action, mode, key))

        for key in self.labels:
            name, color = self.labels[key]
            ans.append("Label: {} {} {}".format(key, name, color))

        return "\n".join(ans)

