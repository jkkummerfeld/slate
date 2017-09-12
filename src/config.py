from __future__ import print_function

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
    annotate = 0
    read = 1
    calibrate = 2

class Config(object):
    def __init__(self, keys, args):
        self.args = args
        self.keys = keys
        self.annotation = AnnScope[args.ann_scope]
        self.annotation_type = AnnType[args.ann_type]
        self.mode = Mode[args.mode]

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

def get_config(args, mode=Mode.annotate):
    return Config(
        {
            's': KeyConfig('s', 'SELL', 2, '{', '}'),
            'b': KeyConfig('b', 'BUY', 3, '[', ']'),
            'r': KeyConfig('r', 'RATE', 7, '|', '|'),
        },
        args
    )

SPECIAL_KEYS = {'u', 'q', 'h', 'p', 'n'}
# TODO: Consider simplifying, with the cursor being white background always
# (and being a modulator on top of whatever else is going on). Reason for
# caution is that in token level mode it can look bad.
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
]
OVERLAP_COLOR = 6
DEFAULT_COLOR = 4
CURSOR_COLOR = 1
LINK_COLOR = 2
HELP_COLOR = 5
REF_COLOR = 3
REF_CURSOR_COLOR = 8
LINK_CURSOR_COLOR = 9

COMPARE_DISAGREE_COLOR = 10
COMPARE_DISAGREE_CURSOR_COLOR = 11
# These indicate how many people labeled something, 1,2...
COMPARE_REF_COLORS = [12, 13]
COMPARE_REF_CURSOR_COLORS = [14, 15]
