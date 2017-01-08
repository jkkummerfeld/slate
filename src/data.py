from __future__ import print_function

import glob

from config import *
from sys import stderr

def read_filenames(arg):
    if len(glob.glob(arg)) == 0:
        raise Exception("Cannot open / find '{}'".format(arg))
    file_info = [line.strip() for line in open(arg).readlines()]
    failed = []
    filenames = []
    for line in file_info:
        parts = line.split()
        filename = parts[0]
        position = [0, 0]
        if len(parts) > 2:
            position = [int(parts[1]), int(parts[2])]
        if len(glob.glob(filename)) == 0:
            failed.append(filename)
        else:
            filenames.append((filename, position))
    if len(failed) > 0:
        raise Exception("File errors:\n{}".format('\n'.join(failed)))
    return filenames

def get_num(text):
    mod_text = []
    for char in text:
        if char not in '(),':
            mod_text.append(char)
    return int(''.join(mod_text))

class Datum(object):
    """Storage for a single file's data and annotations.

    Note, the structure of storage depends on the annotation type."""
    def __init__(self, filename, config):
        self.filename = filename
        self.config = config
        self.tokens = []
        self.marked = {}

        # Read file
        for line in open(filename):
            self.tokens.append([])
            for token in line.split():
                self.tokens[-1].append(token)

        # Read standoff annotations if they exist. Note:
        #  - Whitespace variations are ignored.
        #  - Repeated labels / links are ignored.
        if len(glob.glob(self.annotation_filename())) != 0:
            for line in open(self.annotation_filename()):
                fields = line.strip().split()
                if self.config.annotation == AnnScope.token:
                    # All examples refer to word 2 on line 4
                    source = (get_num(fields[0]), get_num(fields[1]))
                    if self.config.annotation_type == AnnType.categorical:
                        # Format example:
                        # (4, 2) - buy sell
                        # means (4, 2) is labeled 'buy' and 'sell'
                        labels = fields[3:]
                        self.marked[source] = labels
                    elif self.config.annotation_type == AnnType.link:
                        # Format example:
                        # (4, 2) - (4, 1) (4, 0)
                        # means (4, 2) is linked to the two words before it
                        targets = set()
                        for i in range(3, len(fields), 2):
                            line = get_num(fields[i])
                            token = get_num(fields[i + 1])
                            targets.add((line, token))
                        self.marked[source] = targets
                    elif self.config.annotation_type == AnnType.text:
                        # Format example:
                        # (4, 2) - blah blah blah
                        # means (4, 2) is labeled "blah blah blah"
                        self.marked[source] = ' '.join(fields[3:])
                elif self.config.annotation == AnnScope.line:
                    source = int(fields[0])
                    if self.config.annotation_type == AnnType.categorical:
                        # Format example:
                        # 3 - buy sell
                        # means line 3 is labeled 'buy' and 'sell'
                        self.marked[source] = fields[2:]
                    elif self.config.annotation_type == AnnType.link:
                        # Format example:
                        # 3 - 4 1
                        # means line 3 is linked to lines 1 and 4
                        targets = {int(v) for v in fields[2:]}
                        self.marked[source] = targets
                    elif self.config.annotation_type == AnnType.text:
                        # Format example:
                        # 3 - blah blah
                        # means line 3 is labeled "blah blah"
                        self.marked[source] = ' '.join(fields[2:])

    def get_marked_token(self, pos, cursor, linking_pos):
        token = self.tokens[pos[0]][pos[1]]
        color = DEFAULT_COLOR
        text = None

        if self.config.annotation == AnnScope.line:
            pos = pos[0]
            linking_pos = linking_pos[0]
            cursor = cursor[0]
            # For categorical data, set the text
            if self.config.annotation_type == AnnType.categorical:
                text = ' '.join(self.marked.get(cursor, []))

        if pos == cursor:
            color = CURSOR_COLOR
            if pos == linking_pos:
                color = LINK_CURSOR_COLOR
            elif linking_pos in self.marked:
                if self.config.annotation_type == AnnType.link:
                    if pos in self.marked.get(linking_pos, []):
                        color = REF_CURSOR_COLOR
            if self.config.annotation_type == AnnType.text:
                text = self.marked.get(pos)
        elif pos == linking_pos:
            color = LINK_COLOR
        elif pos in self.marked or linking_pos in self.marked:
            if self.config.annotation_type == AnnType.categorical:
               for key in self.marked.get(pos, []):
                    modifier = self.config.keys[key]
                    if color != DEFAULT_COLOR: color = OVERLAP_COLOR
                    else: color = modifier.color
            elif self.config.annotation_type == AnnType.link:
                if pos in self.marked.get(linking_pos, []):
                    color = REF_COLOR
            else:
                pass
        else:
            pass

        return (token, color, text)

    def annotation_filename(self):
        return self.filename + ".annotations"

    def convert_to_key(self, pos):
        if self.config.annotation == AnnScope.line:
            return pos[0]
        else:
            return (pos[0], pos[1])

    def modify_annotation(self, pos, linking_pos, symbol=None):
        pos_key = self.convert_to_key(pos)
        item = symbol
        if self.config.annotation_type == AnnType.link:
            item = pos_key
            pos_key = self.convert_to_key(linking_pos)

        if pos_key not in self.marked:
            self.marked[pos_key] = {item}
        elif item not in self.marked[pos_key]:
            self.marked[pos_key].add(item)
        elif len(self.marked[pos_key]) == 1:
            # Given the first two conditions, we know there is a single
            # mark and it is this symbol.
            self.marked.pop(pos_key)
        else:
            self.marked[pos_key].remove(item)

    def remove_annotation(self, pos, ref):
        pos_key = self.convert_to_key(pos)
        if self.config.annotation_type == AnnType.link:
            pos_key = self.convert_to_key(ref)
        if pos_key in self.marked:
            self.marked.pop(pos_key)

    def write_out(self, filename=None):
        out_filename = self.annotation_filename()
        if filename is not None:
            out_filename = filename
        out = open(out_filename, 'w')

        for key in self.marked:
            source = str(key)
            info = self.marked[key]
            if self.config.annotation_type == AnnType.categorical:
                info = " ".join([str(v) for v in info])
            elif self.config.annotation_type == AnnType.link:
                info = " ".join([str(v) for v in info])
            elif self.config.annotation_type == AnnType.text:
                pass
            print("{} - {}".format(source, info), file=out)
        out.close()


