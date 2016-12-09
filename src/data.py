from __future__ import print_function

import glob

from config import AnnType, AnnScope
from sys import stderr

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
                        # (4, 2) is labeled 'buy' and 'sell'
                        labels = set(fields[3:])
                        self.marked[source] = labels
                    elif self.config.annotation_type == AnnType.link:
                        # Format example:
                        # (4, 2) - (4, 1) (4, 0)
                        # (4, 2) is linked to the two words before it
                        targets = []
                        for i in range(3, len(fields), 2):
                            line = get_num(fields[i])
                            token = get_num(fields[i + 1])
                            targets.append((line, token))
                        self.marked[source] = targets
                    elif self.config.annotation_type == AnnType.text:
                        # Format example:
                        # (4, 2) - blah blah blah
                        # (4, 2) is labeled "blah blah blah"
                        self.marked[source] = ' '.join(fields[3:])
                elif self.config.annotation == AnnScope.line:
                    source = int(fields[0])
                    if self.config.annotation_type == AnnType.categorical:
                        # Format example:
                        # 3 - buy sell
                        # line 3 is labeled 'buy' and 'sell'
                        self.marked[source] = set(fields[2:])
                    elif self.config.annotation_type == AnnType.link:
                        # Format example:
                        # 3 - 4 1
                        # line 3 is linked to lines 1 and 4
                        targets = {int(v) for v in fields[2:]}
                        self.marked[source] = targets
                    elif self.config.annotation_type == AnnType.text:
                        # Format example:
                        # 3 - blah blah
                        # line 3 is labeled "blah blah"
                        self.marked[source] = ' '.join(fields[2:])

    def get_markings(self, position):
        if position in self.marked:
            return self.marked[position]
        else:
            return set()

    def annotation_filename(self):
        return self.filename + ".annotations"

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


