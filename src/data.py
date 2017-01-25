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
        annotations = []
        if len(parts) > 2:
            position = [int(parts[1]), int(parts[2])]
        if len(parts) > 4:
            annotations = parts[3:]
        if len(glob.glob(filename)) == 0:
            failed.append(filename)
        else:
            filenames.append((filename, position, annotations))
    if len(failed) > 0:
        raise Exception("File errors:\n{}".format('\n'.join(failed)))
    return filenames

def get_num(text):
    mod_text = []
    for char in text:
        if char not in '(),':
            mod_text.append(char)
    return int(''.join(mod_text))

def read_annotation_file(config, filename):
    marked = {}

    # Read standoff annotations if they exist. Note:
    #  - Whitespace variations are ignored.
    #  - Repeated labels / links are ignored.
    if len(glob.glob(filename)) != 0:
        for line in open(filename):
            fields = line.strip().split()
            if config.annotation == AnnScope.token:
                # All examples refer to word 2 on line 4
                source = (get_num(fields[0]), get_num(fields[1]))
                if config.annotation_type == AnnType.categorical:
                    # Format example:
                    # (4, 2) - buy sell
                    # means (4, 2) is labeled 'buy' and 'sell'
                    labels = set(fields[3:])
                    marked[source] = labels
                elif config.annotation_type == AnnType.link:
                    # Format example:
                    # (4, 2) - (4, 1) (4, 0)
                    # means (4, 2) is linked to the two words before it
                    targets = set()
                    for i in range(3, len(fields), 2):
                        line = get_num(fields[i])
                        token = get_num(fields[i + 1])
                        targets.add((line, token))
                    marked[source] = targets
                elif config.annotation_type == AnnType.text:
                    # Format example:
                    # (4, 2) - blah blah blah
                    # means (4, 2) is labeled "blah blah blah"
                    marked[source] = ' '.join(fields[3:])
            elif config.annotation == AnnScope.line:
                source = int(fields[0])
                if config.annotation_type == AnnType.categorical:
                    # Format example:
                    # 3 - buy sell
                    # means line 3 is labeled 'buy' and 'sell'
                    marked[source] = set(fields[2:])
                elif config.annotation_type == AnnType.link:
                    # Format example:
                    # 3 - 4 1
                    # means line 3 is linked to lines 1 and 4
                    targets = {int(v) for v in fields[2:]}
                    marked[source] = targets
                elif config.annotation_type == AnnType.text:
                    # Format example:
                    # 3 - blah blah
                    # means line 3 is labeled "blah blah"
                    marked[source] = ' '.join(fields[2:])
    return marked

class Datum(object):
    """Storage for a single file's data and annotations.

    Note, the structure of storage depends on the annotation type."""
    def __init__(self, filename, config, annotation_files):
        self.filename = filename
        self.annotation_files = annotation_files
        self.config = config

        self.marked = read_annotation_file(config, self.annotation_filename())

        self.tokens = []
        for line in open(filename):
            self.tokens.append([])
            for token in line.split():
                self.tokens[-1].append(token)

        self.marked_compare = []
        for filename in self.annotation_files:
            self.marked_compare.append(read_annotation_file(config, filename))
        self.disagree = set()
        for marked0 in self.marked_compare:
            for marked1 in self.marked_compare:
                if marked0 == marked1:
                    break
                for source in marked0:
                    if source not in marked1:
                        self.disagree.add(source)
                    elif marked0[source] != marked1[source]:
                        self.disagree.add(source)

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
                if pos in self.marked.get(linking_pos, []):
                    color = REF_CURSOR_COLOR
            else:
                if pos in self.disagree:
                    color = COMPARE_DISAGREE_CURSOR_COLOR
                
                count = 0
                for i, marked in enumerate(self.marked_compare):
                    if pos in marked.get(linking_pos, []):
                        color = COMPARE_REF_CURSOR_COLORS[i]
                        count += 1
                if count > 0 and count == len(self.marked_compare):
                    color = REF_CURSOR_COLOR
            if self.config.annotation_type == AnnType.text:
                text = self.marked.get(pos)
        elif pos == linking_pos:
            color = LINK_COLOR
        else:
            if pos in self.marked or linking_pos in self.marked:
                if self.config.annotation_type == AnnType.categorical:
                   for key in self.marked.get(pos, []):
                        modifier = self.config.keys[key]
                        if color != DEFAULT_COLOR: color = OVERLAP_COLOR
                        else: color = modifier.color
                elif self.config.annotation_type == AnnType.link:
                    if pos in self.marked.get(linking_pos, []):
                        color = REF_COLOR
                    elif pos in self.disagree:
                        color = COMPARE_DISAGREE_COLOR
            elif pos in self.disagree:
                color = COMPARE_DISAGREE_COLOR

            count = 0
            for i, marked in enumerate(self.marked_compare):
                if pos in marked.get(linking_pos, []):
                    color = COMPARE_REF_COLORS[i]
                    count += 1
            if count > 0 and count == len(self.marked_compare):
                color = REF_COLOR

        return (token, color, text)

    def annotation_filename(self):
        if len(self.annotation_files) == 1:
            return self.annotation_files[0]
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

    def check_equal(self, pos0, pos1):
        if self.config.annotation == AnnScope.line:
            return pos0[0] == pos1[0]
        else:
            return pos0 == pos1

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


