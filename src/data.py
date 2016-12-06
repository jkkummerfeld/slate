from __future__ import print_function

import glob

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

        tmp_filename = filename
        if not config.overwrite:
            alternative = filename + ".annotated"
            if len(glob.glob(alternative)) > 0:
                tmp_filename = alternative

        for line in open(tmp_filename):
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
        if not self.config.overwrite:
            out_filename += ".annotated"
        out = open(out_filename, 'w')
        for line_no, line in enumerate(self.tokens):
            for token_no, token in enumerate(line):
                position = (line_no, token_no)
                if position in self.marked:
                    for key in self.marked[position]:
                        modifier = self.config.keys[key]
                        token = modifier.start_and_end(token, 0)[0]
                print(token, end=" ", file=out)
            print("", file=out)

