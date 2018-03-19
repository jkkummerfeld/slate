from __future__ import print_function

import logging
import glob
import sys

from config import *

def read_filenames(arg, config):
    # File containing lines of the form:
    #  raw_filename [output_filename [cur_line cur_token [other_annotations]]]
    #
    if len(glob.glob(arg)) == 0:
        raise Exception("Cannot open / find '{}'".format(arg))
    file_info = [line.strip() for line in open(arg).readlines()]
    filenames = []
    for line in file_info:
        parts = line.split()
        next_part = 0

        # Input data
        raw_file = parts[0]
        next_part += 1

        # Output file name
        output_file = raw_file + ".annotations"
        if len(parts) > next_part:
            output_file = parts[next_part]
            next_part += 1

        # Start somewhere other than the top
        d = Document(raw_file)
        position = Span(config.annotation, d)
        if len(parts) > next_part:
            position_text = []
            depth = 0
            first = True
            while depth > 0 or first:
                for char in parts[next_part]:
                    if char == '(': depth += 1
                    if char == ')': depth -= 1
                position_text.append(parts[next_part])
                first = False
                next_part += 1
            position_text = ' '.join(position_text)

            span = eval(position_text)
            position = Span(config.annotation, d, span)

        # Additional annotations (used when comparing annotations)
        annotations = []
        if len(parts) > next_part:
            annotations = parts[next_part:]
        filenames.append((raw_file, position, output_file, annotations))

    # Check files exist (or do not exist if being created)
    missing = []
    extra = []
    for raw_file, _, output_file, annotations in filenames:
        if len(glob.glob(raw_file)) == 0:
            missing.append(raw_file)
        if not config.args.overwrite:
            if len(glob.glob(output_file)) != 0:
                extra.append(output_file)
        for annotation in annotations:
            if len(glob.glob(annotation)) == 0:
                missing.append(annotation)
    if len(missing) > 0 or len(extra) > 0:
        error = "Input Filename List Has Errors"
        if len(missing) > 0:
            error += "\n\nUnable to open:\n" + '\n'.join(missing)
        if len(extra) > 0:
            error += "\n\nOutput file already exists:\n" + '\n'.join(extra)
        raise Exception(error)
    return filenames

class Document(object):
    """Storage for the raw text data."""
    # TODO: Think about maintaining whitespace variations, probably just by
    # removing the .strip() below and then adjusting token selection to skip
    # blank tokens

    def __init__(self, filename):
        self.raw_text = open(filename).read()
        self.lines = self.raw_text.split("\n")

        self.tokens = []
        self.first_char = None
        self.last_char = None
        for line in self.raw_text.split("\n"):
            cur = []
            self.tokens.append(cur)
            for token in line.strip().split():
                if self.first_char is None:
                    self.first_char = (len(self.tokens) - 1, 0, 0)
                self.last_char = (len(self.tokens) - 1, len(cur), len(token) - 1)
                cur.append(token)
        assert self.first_char is not None, "Empty document"

    def get_3tuple(self, partial, start):
        if len(partial) == 3:
            return partial
        elif len(partial) == 0:
            if start: return self.first_char
            else: return self.last_char
        else:
            line = partial[0]

            token = 0
            if len(partial) == 1 and (not start):
                token = len(self.tokens[line]) - 1
            elif len(partial) == 2:
                token = partial[1]

            char = 0
            if not start:
                char = len(self.tokens[line][token]) - 1

            return (line, token, char)

    def next_match(self, pos, text, reverse=False):
        return pos
        # TODO:
###        if len(pos) == 1:
###            cline = pos[0]
###            delta = -1 if reverse else 1
###            while 0 <= cline < len(self.lines):
###                if text in self.lines[cline]:
###                    return (cline)
###                cline += delta
###        elif len(pos) > 1:
###            # Check this line first
###            if text in self.lines[pos[0]]:
###                parts = self.lines[pos[0]].split(text)
###                ctoken, cchar = 0, 0
###                options = []
###                for part in parts:
###                    # Advance
###                    for char in part:
###                        if char == ' ':
###                            ctoken += 1
###                            cchar = 0
###                        else:
###                            cchar += 1
###                    options.append((ctoken, cchar))
###                    for char in text:
###                        if char == ' ':
###                            ctoken += 1
###                            cchar = 0
###                        else:
###                            cchar += 1
###                pass
###        return pos

    def get_moved_pos(self, pos, right=0, down=0, maxjump=False, skip_blank=True):
        """Calculate a shifted version of  a given a position in this document.

        Co-ordinates are (line number, token number), with (0,0) as the top
        left, tokens increasing left to right and lines increasing top to
        bottom.
        """
        if len(pos) == 0: # This is the whole document, can't move
            return pos
        elif len(pos) == 1: # This is a line, ignore right
            npos = pos[0]
            if maxjump:
                if down < 0: npos = self.first_char[0]
                elif down > 0: npos = self.last_char[0]
            else:
                # Shift incrementally so we can optionally only count lines
                # that have tokens.
                shift = down
                delta = 1 if shift > 0 else -1
                while shift != 0 and self.first_char[0] <= npos + delta <= self.last_char[0]:
                    npos += delta
                    if (not skip_blank) or len(self.tokens[npos]) > 0:
                        shift -= delta

            return (npos,)
        elif len(pos) == 2: # Moving a token
            nline = pos[0]
            ntok = pos[1]

            # Vertical movement
            if maxjump:
                # We always want to be on a token, so go to the first or last
                # line with one.
                if down < 0: nline = self.first_char[0]
                elif down > 0: nline = self.last_char[0]
            else:
                # Shift incrementally so we can optionally only count lines
                # that have tokens.
                shift = down
                delta = 1 if shift > 0 else -1
                while shift != 0 and self.first_char[0] <= nline + delta <= self.last_char[0]:
                    nline += delta
                    if (not skip_blank) or len(self.tokens[nline]) > 0:
                        shift -= delta

            # Horizontal movement
            ntok = min(ntok, len(self.tokens[nline]) - 1)
            if maxjump:
                if right < 0: ntok = 0
                elif right > 0: ntok = len(self.tokens[nline]) - 1
            else:
                shift = right
                delta = 1 if shift > 0 else -1
                while shift != 0:
                    if delta == -1 and nline == self.first_char[0] and ntok == self.first_char[1]:
                        break
                    if delta == 1 and nline == self.last_char[0] and ntok == self.last_char[1]:
                        break
                    if 0 <= ntok + delta < len(self.tokens[nline]):
                        ntok += delta
                    else:
                        # Go forward/back to a line with tokens. Note, we know
                        # there are later/earlier lines, since otherwise we
                        # would have been at the last_char/first_char
                        # position.
                        nline += delta
                        while len(self.tokens[nline]) == 0:
                            nline += delta
                        ntok = 0 if delta > 0 else len(self.tokens[nline]) - 1
                    shift -= delta
            return (nline, ntok)
        else: # Moving a character
            # Vertical movement
            nline = pos[0]
            if maxjump:
                # We always want to be on a character, so go to the first or
                # last line with one.
                if down < 0: nline = self.first_char[0]
                elif down > 0: nline = self.last_char[0]
            else:
                # Shift incrementally because we only want to count lines that
                # have characters.
                shift = down
                delta = 1 if shift > 0 else -1
                while shift != 0 and self.first_char[0] <= nline + delta <= self.last_char[0]:
                    nline += delta
                    if (not skip_blank) or len(self.tokens[nline]) > 0:
                        shift -= delta

            # Horizontal movement
            ntok = min(len(self.tokens[nline]) - 1, pos[1])
            nchar = min(len(self.tokens[nline][ntok]) - 1, pos[2])
            if maxjump:
                if right < 0:
                    ntok = 0
                    nchar = 0
                elif right > 0:
                    ntok = len(self.tokens[nline]) - 1
                    nchar = len(self.tokens[nline][ntok]) - 1
            else:
                shift = right
                delta = 1 if shift > 0 else -1
                while shift != 0:
                    if delta == -1 and \
                            nline == self.first_char[0] and \
                            ntok == self.first_char[1] and \
                            nchar == self.first_char[1]:
                        break
                    if delta == 1 and \
                            nline == self.last_char[0] and \
                            ntok == self.last_char[1] and \
                            nchar == self.last_char[1]:
                        break
                    if 0 <= nchar + delta < len(self.tokens[nline][ntok]):
                        nchar += delta
                    elif delta < 0 and ntok > 0:
                        ntok -= 1
                        nchar = len(self.tokens[nline][ntok]) - 1
                    elif delta > 0 and ntok < len(self.tokens[nline]) - 1:
                        ntok += 1
                        nchar = 0
                    else:
                        # Go forward/back to a line with tokens. Note, we know
                        # there are later/earlier lines, since otherwise we
                        # would have been at the last_char/first_char
                        # position.
                        if nline + delta <= self.last_char[0]:
                            nline += delta
                            while len(self.tokens[nline]) == 0:
                                nline += delta
                            ntok = 0 if delta > 0 else len(self.tokens[nline]) - 1
                            nchar = 0 if delta > 0 else len(self.tokens[nline][ntok]) - 1
                    shift -= delta
            return (nline, ntok, nchar)

    def get_next_pos(self, pos):
        if len(pos) == 0:
            return pos
        elif len(pos) == 1:
            return self.get_moved_pos(pos, 0, 1)
        else:
            return self.get_moved_pos(pos, 1, 0)

    def get_previous_pos(self, pos):
        if len(pos) == 0:
            return pos
        elif len(pos) == 1:
            return self.get_moved_pos(pos, 0, -1)
        else:
            return self.get_moved_pos(pos, -1, 0)

class SpanCompare(Enum):
  smaller = 0
  smaller_left = 1
  overlap_end = 2
  overlap_right = 3
  cover = 4
  left_inside = 5
  equal = 6
  left_overlap = 7
  inside = 8
  inside_right = 9
  overlap_start = 10
  right_larger = 11
  larger = 12
  one_smaller = 13
  one_left = 14
  one_inside = 15
  one_right = 16
  one_larger = 17
  smaller_one = 18
  smaller_match = 19
  cover_one = 20
  equal_one = 21
  match_larger = 22
  larger_one = 23
  smaller_one_one = 24
  larger_one_one = 25


value_from_comparisons = {
#  s0s1 e0e1 s0e1 e0s1 s0e0 s1e1 SpanCompare                |-------|
  (1, 1, 1, 1, 1, 1): SpanCompare.smaller,          # .--.                 
  (1, 1, 1, 0, 1, 1): SpanCompare.smaller_left,     # .-----|              
  (1, 1, 1, -1, 1, 1): SpanCompare.overlap_end,     # .---------.          
  (1, 0, 1, -1, 1, 1): SpanCompare.overlap_right,   # .-------------|      
  (1, -1, 1, -1, 1, 1): SpanCompare.cover,          # .-------------------.
  (0, 1, 1, -1, 1, 1): SpanCompare.left_inside,     #       |---.          
  (0, 0, 1, -1, 1, 1): SpanCompare.equal,           #       |-------|      
  (0, -1, 1, -1, 1, 1): SpanCompare.left_overlap,   #       |-------------.
  (-1, 1, 1, -1, 1, 1): SpanCompare.inside,         #          .-.         
  (-1, 0, 1, -1, 1, 1): SpanCompare.inside_right,   #           .---|      
  (-1, -1, 1, -1, 1, 1): SpanCompare.overlap_start, #           .---------.
  (-1, -1, 0, -1, 1, 1): SpanCompare.right_larger,  #               |-----.
  (-1, -1, -1, -1, 1, 1): SpanCompare.larger,       #                  .--.
  (1, 1, 1, 1, 0, 1): SpanCompare.one_smaller,      # .                    
  (0, 1, 1, 0, 0, 1): SpanCompare.one_left,         #       |              
  (-1, 1, 1, -1, 0, 1): SpanCompare.one_inside,     #           .          
  (-1, 0, 0, -1, 0, 1): SpanCompare.one_right,      #               |      
  (-1, -1, -1, -1, 0, 1): SpanCompare.one_larger,   #                     .
  # Now consider cases where the second has width 0
  #                                                             |          
  (1, 1, 1, 1, 1, 0): SpanCompare.smaller_one,      #     .--.             
  (1, 0, 1, 0, 1, 0): SpanCompare.smaller_match,    #     .-----|          
  (1, -1, 1, -1, 1, 0): SpanCompare.cover_one,      #     .-----------.    
  (0, 0, 0, 0, 0, 0): SpanCompare.equal_one,        #           |          
  (0, -1, 0, -1, 1, 0): SpanCompare.match_larger,   #           |-----.    
  (-1, -1, -1, -1, 1, 0): SpanCompare.larger_one,   #              .--.    
  (1, 1, 1, 1, 0, 0): SpanCompare.smaller_one_one,  #     .                
  (-1, -1, -1, -1, 0, 0): SpanCompare.larger_one_one, #               .    
}

span_compare_ge = [
    SpanCompare.left_inside, SpanCompare.equal, SpanCompare.left_overlap,
    SpanCompare.inside, SpanCompare.inside_right, SpanCompare.overlap_start,
    SpanCompare.right_larger, SpanCompare.larger, SpanCompare.one_left,
    SpanCompare.one_inside, SpanCompare.one_right, SpanCompare.one_larger,
    SpanCompare.equal_one, SpanCompare.match_larger, SpanCompare.larger_one,
    SpanCompare.larger_one_one
]
span_compare_le = [
    SpanCompare.smaller, SpanCompare.smaller_left, SpanCompare.overlap_end,
    SpanCompare.overlap_right, SpanCompare.left_inside, SpanCompare.equal,
    SpanCompare.inside, SpanCompare.inside_right, SpanCompare.one_smaller,
    SpanCompare.one_left, SpanCompare.one_inside, SpanCompare.one_right,
    SpanCompare.smaller_one, SpanCompare.smaller_match, SpanCompare.equal_one,
    SpanCompare.smaller_one_one
]

class Span(object):
    """A continuous span of text.
    
    All annotations are on spans, some of which just happen to have a single element."""

    def __init__(self, scope, doc, span=None):
        self.start = None
        self.end = None
        self.doc = doc
        self.scope = scope

        # Most of the time a span will be provided to start from.
        if span is None:
            first = self.doc.first_char
            if scope == AnnScope.character:
                self.start = (first[0], first[1], first[2])
            elif scope == AnnScope.token:
                self.start = (first[0], first[1])
            elif scope == AnnScope.line:
                self.start = (first[0],)
            elif scope == AnnScope.document:
                self.start = ()
            else:
                raise Exception("Invalid scope")
            self.end = self.start
        else:
            # Check it has the right length
            length = 0
            if scope == AnnScope.character: length = 3
            elif scope == AnnScope.token: length = 2
            elif scope == AnnScope.line: length = 1
            elif scope == AnnScope.document: length = 0
            else: raise Exception("Invalid scope")

            if type(span) == tuple:
                if len(span) == 0:
                    self.start, self.end = (), ()
                else:
                    # TODO: Add a check that this position is valid for this
                    # doc
                    if type(span[0]) == int:
                        assert len(span) == length, "Got {} not {}".format(len(span), length)
                        self.start = span
                        self.end = span
                    else:
                        assert len(span[0]) == len(span[1]) == length
                        self.start = span[0]
                        self.end = span[1]
            else:
                assert len(span.start) == len(span.end) == length
                self.end = span.end
                self.start = span.start

    def _compare_tuples(self, a, b):
        # Returns a number that is the kind of delta going from a to b
        # (positive, negative, or zero)
        if len(a) == 0 or len(b) == 0:
            return 0
        if a[0] == b[0]:
            if len(a) == 1 or len(b) == 1:
                return 0
            if a[1] == b[1]:
                if len(a) == 2 or len(b) == 2:
                    return 0
                if a[2] == b[2]:
                    return 0
                elif a[2] < b[2]:
                    return 1
                else:
                    return -1
            elif a[1] < b[1]:
                return 1
            else:
                return -1
        elif a[0] < b[0]:
            return 1
        else:
            return -1

    def __hash__(self):
        return hash((self.start, self.end))
    def __eq__(self, other):
        if type(self) != type(other):
            return False
        elif self._compare_tuples(self.start, other.start) != 0:
            return False
        elif self._compare_tuples(self.end, other.end) != 0:
            return False
        else:
            return True
    def __lt__(self, other):
        assert type(self) == type(other)
        if self._compare_tuples(self.start, other.start) == 0:
            return self._compare_tuples(self.end, other.end) == 1
        return self._compare_tuples(self.start, other.start) == 1

    def __ne__(self, other):
        return not self.__eq__(other)
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        return not self.__le__(other)
    def __ge__(self, other):
        return not self.__lt__(other)

    def __repr__(self):
        return "Span({}, {})".format(self.start, self.end)

    def __str__(self):
        return str((self.start, self.end))

    def compare(self, other):
        '''Compares two spans and returns a SpanCompare.'''
        assert type(self) == type(other)

        s0 = self.doc.get_3tuple(self.start, True)
        e0 = self.doc.get_3tuple(self.end, False)
        s1 = other.doc.get_3tuple(other.start, True)
        e1 = other.doc.get_3tuple(other.end, False)

        s0s1 = self._compare_tuples(s0, s1)
        s0e1 = self._compare_tuples(s0, e1)
        e0s1 = self._compare_tuples(e0, s1)
        e0e1 = self._compare_tuples(e0, e1)
        s0e0 = self._compare_tuples(s0, e0)
        s1e1 = self._compare_tuples(s1, e1)

        return value_from_comparisons[s0s1, e0e1, s0e1, e0s1, s0e0, s1e1]

    def to_3tuple(self):
        if self.scope == AnnScope.character:
            return self
        start = self.doc.get_3tuple(start)
        end = self.doc.get_3tuple(end)
        return Span(AnnScope.character, self.doc, (start, end))

    def edited(self, direction=None, change=None, distance=1, maxjump=False):
        """Change this span, either moving both ends or only one.

        direction is left, right, up, down, next or previous
        change is move, expand, or contract
        distance is an integer, with negative numbers meaning max
        """
        logging.info("{} {} {} {}".format(self, direction, change, distance))
        new_start = self.start
        new_end = self.end

        if direction == 'next':
            new_start = self.doc.get_next_pos(self.start)
            new_end = self.doc.get_next_pos(self.end)
            return Span(self.scope, self.doc, (new_start, new_end))
        elif direction == 'previous':
            new_start = self.doc.get_previous_pos(self.start)
            new_end = self.doc.get_previous_pos(self.end)
            return Span(self.scope, self.doc, (new_start, new_end))

        right = 0
        down = 0
        if direction == 'left':
            right = -distance
        elif direction == 'right':
            right = distance
        elif direction == 'up':
            down = -distance
        elif direction == 'down':
            down = distance
        if change == 'contract':
            right *= -distance
            down *= -distance

        if change == "move":
            nstart = self.doc.get_moved_pos(new_start, right, down, maxjump)
            nend = self.doc.get_moved_pos(new_end, right, down, maxjump)
            logging.info("From {} and {} to {} and {}".format(self.start, self.end, nstart, nend))
            # Only move if it will change both (otherwise it is a shift).
            if nstart != self.start and nend != self.end:
                new_start = nstart
                new_end = nend
        else:
            move_start = (
                change == "extend" and (
                    direction == "left" or direction == "up")
            ) or (
                change == "contract" and (
                    direction == "right" or direction == "down"))

            if move_start:
                new_start = self.doc.get_moved_pos(new_start, right, down, maxjump)
            else:
                new_end = self.doc.get_moved_pos(new_end, right, down, maxjump)

        ans = Span(self.scope, self.doc, (new_start, new_end))
        logging.info("Returning {}".format(ans))
        return ans
    
    # How to do coreference resolution annotation:
    # - Normal mode is selecting a position using the edit function
    # - Switch to link mode and then toggle between mentions including this one (to indicate no prior link)

class Item(object):
    """One or more spans and a set of labels.

    This is used in Datum to keep track of annotations, and used in View to determine the current appearance."""
    def __init__(self, doc, init_span=None, init_label=None):
        self.doc = doc
        self.spans = []
        if type(init_span) == list:
            self.spans += init_span
        elif init_span is not None:
            self.spans.append(init_span)

        self.labels = set()
        if type(init_label) == set:
            self.labels.update(init_label)
        elif init_label is not None:
            self.labels.add(init_label)

    def __eq__(self, other):
        return self.spans == other.spans and self.labels == other.labels and self.doc == other.doc

    def __str__(self):
        labels = []
        for label in self.labels:
            labels.append(str(label))
        labels = ' '.join(labels)

        spans = '[' + ', '.join([str(s) for s in self.spans]) +']'
        if len(self.spans) == 1:
            spans = str(self.spans[0])
            if self.doc.get_next_pos(self.spans[0].start) == self.spans[0].end:
                spans = str(self.spans[0].start)
                if len(self.spans[0].start) == 1:
                    spans = str(self.spans[0].start[0])
        elif len(self.spans) > 1:
            all_single = True
            for s in self.spans:
                if self.doc.get_next_pos(s.start) != s.end:
                    all_single = False
            if all_single:
                spans = str([s.start for s in self.spans])
                if len(self.spans[0].start) == 1:
                    spans = " ".join([str(s.start[0]) for s in self.spans])

        return "{} - {}".format(spans, labels)

def get_spans(text, doc, config):
    # TODO: allow for <filename>:data

    spans = []
    if text[0] in '[(':
        spans = eval(text.strip())
        if type(spans) == int:
            spans = [(spans,)]
        elif type(spans) == tuple:
            spans = [spans]
        elif type(spans) == list:
            if len(spans) == 0:
                spans = [()]
            elif type(spans[0]) == int:
                spans = [(s,) for s in spans]
    else:
        for num in text.split():
            spans.append((int(num),))
    
    return [Span(config.annotation, doc, s) for s in spans]

def get_labels(text, config):
    labels = set()
    if config.annotation_type == AnnType.categorical:
        for label in text.strip().split():
            labels.add(label)
    elif config.annotation_type == AnnType.text:
        labels.add(text.strip().split())
    else:
        assert len(text.strip().split()) == 0

    return labels

def read_annotation_file(config, filename, doc):
    items = []

    if len(glob.glob(filename)) != 0:
        for line in open(filename):
            fields = line.strip().split()

            # Always lay out as:
            # [spans] - [labels]

            spans = get_spans(line.split('-')[0], doc, config)
            labels = get_labels('-'.join(line.split('-')[1:]), config)

            items.append(Item(doc, spans, labels))
            logging.info("Read"+ str(items[-1]))

    return items

class Datum(object):
    """Storage for a single file's data and annotations.

    Note, the structure of storage depends on the annotation type."""

    def __init__(self, filename, config, output_file, other_annotation_files):
        self.filename = filename
        self.config = config
        self.output_file = output_file
        self.doc = Document(filename)
        logging.info("Reading data from "+ self.output_file)
        self.annotations = read_annotation_file(config, self.output_file, self.doc)

        # TODO: read other annotations
        self.other_annotation_files = other_annotation_files

    def _set_color(self, color_dict, position, color):
        pass

    def get_all_markings(self, cursor, linking_pos):
        # TODO: Handle color given use of spans now instead of positions
        # TODO: Convert to character level
        # TODO: Convert to use info as spans
        ans = {}
        if cursor == linking_pos:
            ans[cursor.start] = LINK_CURSOR_COLOR
        else:
            ans[cursor.start] = CURSOR_COLOR
            if linking_pos is not None:
                ans[linking_pos.start] = LINK_COLOR

        logging.info("Markings with {} {}".format(repr(cursor), repr(linking_pos)))
        for item in self.annotations:
            logging.info("Get colour for item {}".format(item))
            # Get the standard color for this item based on its label
            base_color = None
            if self.config.annotation_type == AnnType.categorical:
                # For categorical use the configuration set
                for key in item.labels:
                    if key in self.config.keys:
                        modifier = self.config.keys[key]
                        if base_color is not None:
                            base_color = OVERLAP_COLOR
                        else:
                            base_color = modifier.color
            elif self.config.annotation_type == AnnType.link:
                # For links potentially indicate it is linked
                if self.config.args.show_linked:
                    base_color = YELLOW_COLOR
            logging.info("base is {}".format(base_color))
            
            has_cursor = False
            has_link = False
            for span in item.spans:
                if span == cursor:
                    has_cursor = True
                if span == linking_pos:
                    has_link = True

            for span in item.spans:
                pos = span.start
                done_end = False
                while not done_end:
                    this_color = DEFAULT_COLOR
                    if pos in ans:
                        this_color = ans[pos]
                    if this_color == DEFAULT_COLOR:
                        this_color = base_color
                    elif self.config.annotation_type == AnnType.categorical:
                        if this_color != CURSOR_COLOR:
                            this_color = OVERLAP_COLOR

                    if len(item.spans) > 1:
                        if pos == linking_pos.start:
                            this_color = LINK_COLOR
                            if pos == cursor.start:
                                this_color = LINK_CURSOR_COLOR
                        elif has_link:
                            this_color = REF_COLOR
                            if pos == cursor.start:
                                this_color = REF_CURSOR_COLOR

                    if this_color is not None:
                        ans[pos] = this_color

                    if pos == span.end:
                        done_end = True
                    else:
                        pos = self.doc.get_next_pos(pos)
                        if pos != span.end and this_color is not None:
                            # Handle the case of a space
                            if len(pos) < 3 or pos[2] == 0:
                                ans[pos[0], pos[1], -1] = this_color

        # TODO: Now do disagreement colours

        return ans

    def next_match(self, span, text, reverse=False):
        return self.doc.next_match(span, text, reverse)

    def get_item_with_spans(self, spans):
        for item in self.annotations:
            match = 0
            for span in item.spans:
                if span in spans:
                    match += 1
            logging.info("Compared: {} {} got {}".format(item.spans, spans, match))
            if len(item.spans) == len(spans) == match:
                return item
        return None

    def modify_annotation(self, spans, label=None):
        to_edit = self.get_item_with_spans(spans)
        if to_edit is None:
            # No item with these spans exists, create it
            nspans = [Span(self.config.annotation, self.doc, s) for s in spans]
            item = Item(self.doc, nspans, label)
            self.annotations.append(item)
        else:
            # Modify existing item
            if label is None:
                if len(to_edit.labels) == 0:
                    self.annotations.remove(to_edit)
            elif label in to_edit.labels:
                to_edit.labels.remove(label)
                if len(to_edit.labels) == 0:
                    self.annotations.remove(to_edit)
            else:
                to_edit.labels.add(label)

    def remove_annotation(self, spans):
        to_remove = self.get_item_with_spans(spans)
        logging.info("Removing {} for {}".format(to_remove, spans))
        if to_remove is not None:
            self.annotations.remove(to_remove)

    def write_out(self, filename=None):
        out_filename = self.output_file
        if filename is not None:
            out_filename = filename
        out = open(out_filename, 'w')
        for item in self.annotations:
            print(str(item), file=out)
        out.close()

