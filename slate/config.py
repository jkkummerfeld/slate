from __future__ import print_function

import string
import logging

import curses # Needed for colours

back = curses.COLOR_WHITE
front = curses.COLOR_BLACK
# Switch for white backgrounds
###back = curses.COLOR_BLACK
###front = curses.COLOR_WHITE

COLORS = [
    # Color combinations, (ID#, foreground, background)
    (1, front, back),
    (2, curses.COLOR_GREEN, -1),
    (3, curses.COLOR_BLUE, -1),
    (4, back, -1),
    (5, front, back),
    (6, curses.COLOR_CYAN, -1),
    (7, curses.COLOR_MAGENTA, -1),
    (8, curses.COLOR_BLUE, back),
    (9, curses.COLOR_GREEN, back),
    (10, curses.COLOR_RED, -1),
    (11, curses.COLOR_RED, back),
    (12, curses.COLOR_CYAN, -1),
    (13, curses.COLOR_MAGENTA, -1),
    (14, curses.COLOR_CYAN, back),
    (15, curses.COLOR_MAGENTA, back),
    (16, curses.COLOR_YELLOW, -1),
    (17, front, back),
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
LINE_NUMBER_COLOR = 16
SELF_LINK_COLOR = 17

COMPARE_DISAGREE_COLOR = 10
COMPARE_REF_COLOR = 12

input_action_list = {
    'leave-query-mode': [
        ('write_query', "ENTER"),
        ('write_query', '?'), ],
    'delete-query-char': [
        ('write_query', "BACKSPACE"),
        ('write_query', '!'), ], 
    'assign-text-label': [
        ('write_label', "ENTER"),
        ('write_label', '?'), ],
    'delete-label-char': [
        ('write_label', "BACKSPACE"),
        ('write_label', '!'), ], 
    'clear-query': [
        '|', ],
    'enter-query-mode': [
        '\\', ],
    'enter-label-mode': [
        't', ],
    'toggle-line-numbers': [
        '#', ],
    'move-up': [
        "UP", 'i', ],
    'move-down': [
        "DOWN", 'o', ],
    'move-left': [
        "LEFT", 'j', ],
    'move-right': [
        "RIGHT", ';', ],
    'jump-up': [
        "SHIFT-UP", 'I', ],
    'jump-down': [
        "SHIFT-DOWN", 'O', ],
    'jump-left': [
        "SHIFT-LEFT", 'J', ],
    'jump-right': [
        "SHIFT-RIGHT", ':', ],
    'move-link-up': [
        ('link', "SHIFT-UP"), ('link', 'I'), ],
    'move-link-down': [
        ('link', "SHIFT-DOWN"), ('link', 'O'), ],
    'move-link-left': [
        ('link', "SHIFT-LEFT"), ('link', 'J'), ],
    'move-link-right': [
        ('link', "SHIFT-RIGHT"), ('link', ':'), ],
    'page-up': [
        "PPAGE", '{' ],
    'page-down': [
        "NPAGE", '}' ],
    'extend-up': [
         ],
    'extend-down': [
        ],
    'contract-up': [
         ],
    'contract-down': [
         ],
    'extend-left': [
        'm', ],
    'extend-right': [
        '/', ],
    'contract-left': [
        'k', ],
    'contract-right': [
        'l', ],
    'extend-link-left': [
        'M', ],
    'extend-link-right': [
        '?', ],
    'contract-link-left': [
        'K', ],
    'contract-link-right': [
        'L', ],
    'toggle-help': [
        'h', ],
    'next-file': [
        ']', ('no_file', ']'), ],
    'previous-file': [
        '[', ('no_file', '['), ],
    'quit': [
        'Q', ],
    'save-and-quit': [
        'q', ],
    'save': [
        's', ],
    'create-link': [
        ('link', 'D'), ],
    'create-link-and-move': [
        ('link', 'd'), ],
    'edit-annotation': [
        ],
    'remove-annotation': [
        (None, 'u'), ],
    'update-num': [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ],
    'toggle-progress': [
            ['>', 'p'], ],
    'toggle-legend': [
            ['>', 'l'], ],
    'toggle-current-mark': [
            ['>', 'm'], ],
    'search-previous': [
        'p', ],
    'search-next': [
        'n', ],
    'search-link-previous': [
        'P', ],
    'search-link-next': [
        'N', ],
}

# Fill in all other characters for searching
used = set()
for key in input_action_list:
    for item in input_action_list[key]:
        if type(item) == tuple:
            used.add((item[0], tuple(item[1])))
        else:
            used.add((None, tuple(item)))
###for item in used:
###    print("Used", item)
for char in string.printable:
    if char in string.whitespace:
        if char == ' ':
            char = 'SPACE'
        else:
            continue
    if ('write_query', (char,)) not in used:
        input_action_list.setdefault('add-to-query', []).append(('write_query', char))
    if ('write_label', (char,)) not in used:
        input_action_list.setdefault('add-to-label', []).append(('write_label', char))

key_to_symbol = {
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
        key_to_symbol[ord(c)] = c
    elif c == ' ':
        key_to_symbol[ord(c)] = 'SPACE'
    elif c == '\t':
        key_to_symbol[ord(c)] = 'TAB'
    elif c == '\n':
        key_to_symbol[ord(c)] = 'ENTER'
special_keys = { # OS X
    337: "SHIFT-UP",
    336: "SHIFT-DOWN",
    10: "ENTER",
    127: "BACKSPACE",
}
for key in special_keys:
    key_to_symbol[key] = special_keys[key]
symbol_to_key = {}
for key in key_to_symbol:
    symbol_to_key[key_to_symbol[key]] = key

def keydef_to_symbols(keydef):
    symbols = ['']
    for char in keydef:
        if char == '_' and len(symbols[-1]) > 0:
            symbols.append('')
        else:
            symbols[-1] += char
    return symbols

class Config(object):
    def __init__(self, args, labels={}):
        self.args = args
        self.labels = labels
        self.annotation = args.ann_scope
        self.annotation_type = args.ann_type
        self.input_to_action = {}

        if args.config_file is not None:
            for line in open(args.config_file):
                # Set general command keybindings
                if line.startswith("Input:"):
                    _, action, mode, key = line.strip().split()
                    symbols = tuple(keydef_to_symbols(key))
                    if mode == 'all':
                        mode = None
                    self.add_keybinding(mode, symbols, action)
                elif line.startswith("Label:"):
                    _, label, key, color = line.strip().split()
                    symbols = tuple(keydef_to_symbols(key))
                    self.labels[label] = (symbols, color)
                elif line.startswith("Special_Key:"):
                    _, symbol, key = line.strip().split()
                    special_keys[int(key)] = symbol
                    symbol_to_key[symbol] = key
                    key_to_symbol[key] = symbol
        else:
            # Core key set as defined above
            for action in input_action_list:
                for opt in input_action_list[action]:
                    mode, symbol = None, opt
                    if type(opt) == tuple:
                        mode = opt[0]
                        symbol = opt[1]
                    if type(symbol) == str:
                        symbol = [symbol]
                    self.add_keybinding(mode, tuple(symbol), action)
            # Provided labels
            for label in self.labels:
                key, _ = self.labels[label]
                self.add_keybinding('category', key, 'edit-annotation')

        # Fill annotation keys
        self.input_to_label = {}
        for label in self.labels:
            key, _ = self.labels[label]
            if type(key) == str:
                key = (key,)
            else:
                key = tuple(key)
            self.input_to_label[key] = label

        self.valid_prefixes = set()
        for mode, symbol in self.input_to_action:
            for i in range(1, len(symbol)):
                self.valid_prefixes.add((mode, symbol[:i]))
        for mode, symbol in self.input_to_action:
            if (mode, symbol) in self.valid_prefixes:
                raise Exception("input {} overlaps with a prefix".format(symbol))

    def get_color_for_label(self, mark):
        name = self.labels[mark][1]
        return name_to_color[name]

    def get_label_for_input(self, user_input):
        return self.input_to_label.get(user_input, None)

    def add_keybinding(self, mode, key, action):
        pair = (mode, key)
        if pair in self.input_to_action:
            raise Exception("input {} used twice".format(pair))
        self.input_to_action[pair] = action

    def __str__(self):
        ans = []

        for mode, key in self.input_to_action:
            action = self.input_to_action[mode, key]
            if mode is None:
                mode = 'all'
            key = "_".join(key)

            ans.append("{:<15} {:<25} {:<20} {}".format("Input:", action, mode, key))

        for label in self.labels:
            key, color = self.labels[label]
            key = "_".join(key)
            ans.append("{:<15} {:<25} {} {}".format("Label:", label, key, color))

        for key in special_keys:
            symbol = special_keys[key]
            ans.append("{:<15} {:<25} {}".format("Special_Key:", symbol, key))

        return "\n".join(ans)

