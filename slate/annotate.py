from __future__ import print_function

import argparse
import curses
import datetime
import logging
import string
import sys

from .data import *
from .config import *
from .view import *

class Annotator(object):
    def __init__(self, config, filenames, current_mode, args):
        self.current_mode = current_mode
        self.current_num = None
        self.search_term = ''
        self.partial_typing = ''
        self.cfilename = -1
        self.filename = None
        self.filenames = filenames
        self.datum = None
        self.view = None
        self.window = None
        self.config = config
        self.args = args
        self.action_to_function = {
            'delete-query-char': self.delete_typing_char,
            'leave-query-mode': self.leave_typing_mode,
            'enter-query-mode': self.enter_typing_mode,
            'clear-query': self.clear_query,
            'add-to-query': self.add_to_typing,
            'delete-label-char': self.delete_typing_char,
            'assign-text-label': self.assign_text,
            'enter-label-mode': self.enter_typing_mode,
            'add-to-label': self.add_to_typing,
            'toggle-line-numbers': self.toggle_line_numbers,
            'move-up': self.move,
            'move-down': self.move,
            'move-left': self.move,
            'move-right': self.move,
            'move-link-up': self.move,
            'move-link-down': self.move,
            'move-link-left': self.move,
            'move-link-right': self.move,
            'jump-up': self.move,
            'jump-down': self.move,
            'jump-left': self.move,
            'jump-right': self.move,
            'extend-up': self.change_span,
            'extend-down': self.change_span,
            'extend-left': self.change_span,
            'extend-right': self.change_span,
            'contract-up': self.change_span,
            'contract-down': self.change_span,
            'contract-left': self.change_span,
            'contract-right': self.change_span,
            'extend-link-up': self.change_span,
            'extend-link-down': self.change_span,
            'extend-link-left': self.change_span,
            'extend-link-right': self.change_span,
            'contract-link-up': self.change_span,
            'contract-link-down': self.change_span,
            'contract-link-left': self.change_span,
            'contract-link-right': self.change_span,
            'search-previous': self.search,
            'search-next': self.search,
            'search-link-previous': self.search,
            'search-link-next': self.search,
            'page-up': self.shift_view,
            'page-down': self.shift_view,
            'toggle-help': self.modify_display,
            'toggle-progress': self.modify_display,
            'toggle-legend': self.modify_display,
            'toggle-current-mark': self.modify_display,
            'next-file': self.change_file,
            'previous-file': self.change_file,
            'quit': self.save_or_quit,
            'save-and-quit': self.save_or_quit,
            'save': self.save_or_quit,
            'create-link': self.create_link,
            'create-link-and-move': self.create_link,
            'edit-annotation': self.edit_annotation,
            'remove-annotation': self.remove_annotation,
            'update-num': self.update_number,
        }

    def move(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        direction = action.split('-')[-1]
        jump = 'jump' in action
        link = 'link' in action

        num = 1
        if self.current_num == 0:
            jump = True
            self.current_num = None
        elif self.current_num is not None:
            num = self.current_num
            self.current_num = None

        self.view.move(direction, num, jump, link)

    def toggle_line_numbers(self, user_input, action):
        self.view.line_numbers = not self.view.line_numbers

    def change_span(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        change = action.split('-')[0]
        direction = action.split('-')[-1]
        # TODO: Support these adjustments to the linking_pos too. This requires
        # edits to view and also to config
        link = 'link' in action

        num = 1
        jump = False
        if self.current_num == 0:
            jump = True
            self.current_num = None
        elif self.current_num is not None:
            num = self.current_num
            self.current_num = None

        self.view.adjust(direction, num, change, jump, link)

    def delete_typing_char(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if self.current_mode[-1] == 'write_query':
            self.search_term = self.search_term[:-1]
        else:
            self.partial_typing = self.partial_typing[:-1]

    def leave_typing_mode(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if len(self.current_mode) > 1:
            self.current_mode.pop()

    def assign_text(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if len(self.current_mode) > 1:
            self.current_mode.pop()
            self.datum.modify_annotation([self.view.cursor], self.partial_typing)
            self.partial_typing = ''

    def enter_typing_mode(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if 'query' in action:
            self.current_mode.append('write_query')
        else:
            self.current_mode.append('write_label')
            self.partial_typing = ''

    def clear_query(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        self.search_term = ''

    def add_to_typing(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        char = user_input[0]
        if user_input[0] == 'SPACE':
            char = ' '
        if self.current_mode[-1] == 'write_query':
            self.search_term += char
        else:
            self.partial_typing += char

    def change_file(self, user_input, action):
        if self.current_mode[-1] != 'no_file':
            self.save_or_quit(None, 'save')

        direction = 1 if 'next' in action else -1
        if self.current_mode[-1] == 'no_file':
            if (self.cfilename < 0) == (direction > 0):
                self.current_mode.pop()
                self.cfilename += direction
        elif 0 <= self.cfilename + direction < len(self.filenames):
            self.cfilename += direction
            self.filename, start_pos, output_file, annotation_files = \
                    self.filenames[self.cfilename]
            self.datum = Datum(self.filename, self.config, output_file, annotation_files)
            self.get_view(self.datum, self.config, self.cfilename, len(self.filenames), start_pos, self.view)
        elif self.current_mode != 'no_file':
            self.cfilename += direction
            self.current_mode.append('no_file')

    def modify_display(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if 'help' in action:
            self.view.toggle_help()
        elif 'progress' in action:
            self.view.toggle_progress()
        elif 'legend' in action:
            self.view.toggle_legend()
        elif 'current-mark' in action:
            self.view.toggle_current_mark()

    def shift_view(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if 'up' in action:
            self.view.shift_view()
        else:
            self.view.shift_view(True)

    def update_number(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        num = int(user_input[0])
        if self.current_num is None:
            self.current_num = 0
        else:
            self.current_num *= 10
        self.current_num += num

    def remove_annotation(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if self.current_mode[-1] != 'read':
            spans = [self.view.cursor]
            if self.current_mode[-1] == 'link':
                spans = [self.view.linking_pos]
            self.datum.remove_annotation(spans)

    def edit_annotation(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        if self.current_mode[-1] == 'category':
            label = self.config.get_label_for_input(user_input)
            self.datum.modify_annotation([self.view.cursor], label)

    def create_link(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        self.datum.modify_annotation([self.view.cursor, self.view.linking_pos])
        if 'and-move' in action:
            if self.config.annotation == 'line':
                self.view.move('down', 1, False, True)
                self.view.put_cursor_beside_link()
            else:
                self.view.move('right', 1, False, True)
                self.view.put_cursor_beside_link()
            self.view.must_show_linking_pos = True

    def save_or_quit(self, user_input, action):
        if 'save' in action:
            if self.current_mode[-1] != 'read':
                self.datum.write_out()

            # TODO: Save both cursor and linking pos
            if 0 <= self.cfilename < len(self.filenames):
                cur = self.filenames[self.cfilename]
                pos = self.view.cursor
                if self.config.annotation_type == 'link':
                    pos = self.view.linking_pos
                self.filenames[self.cfilename] = (cur[0], pos, cur[2], cur[3])

        if 'quit' in action:
            if 'save' not in action:
                # TODO: Have an 'are you sure?' step
                pass
            return 'quit'

    def search(self, user_input, action):
        if self.current_mode[-1] == 'no_file':
            return

        direction = action.split('-')[-1]
        jump = False
        link = 'link' in action

        num = 1
        if self.current_num == 0:
            jump = True
            self.current_num = None
        elif self.current_num is not None:
            num = self.current_num
            self.current_num = None

        if len(self.search_term) > 0:
            self.view.search(self.search_term, direction, num, jump, link)
        else:
            # Used when comparing files to go to the next/previous annotation
            # Or when not comparing files to go to the next unannotated thing
            # When there is nothing unannotated, it jumps to the next self-linked item
            self.view.search(None, direction, num, jump, link)


    def input_to_symbol(self, num):
        if num in key_to_symbol:
            return key_to_symbol[num]
        else:
            return "UNKNOWN"

    def get_view(self, config, file_num, total_files, position, prev_view=None):
        cursor = position
        link = position if self.config.annotation_type == 'link' else None
        self.view = View(self.window, cursor, link, self.datum, self.config, file_num, total_files, prev_view)

    def annotate(self, window_in):
        self.window = window_in

        # Set color combinations
        curses.use_default_colors()
        for num, fore, back in COLORS:
            curses.init_pair(num, fore, back)

        # No blinking cursor
        curses.curs_set(0)

        self.cfilename = 0
        self.filename, start_pos, output_file, annotation_files = self.filenames[self.cfilename]
        self.datum = Datum(self.filename, self.config, output_file, annotation_files)
        self.get_view(self.config, self.cfilename, len(self.filenames), start_pos)
        if not self.args.hide_help:
            self.view.toggle_help()

        last_num = None
        at_end = None
        nsteps = 0
        user_input = []
        while True:
            # Draw screen
            if self.current_mode[-1] == 'no_file':
                self.view.render_edgecase(self.cfilename >= 0)
            else:
                # Set current search term appearance
                tmp_term = self.search_term
                if self.current_mode[-1] == 'write_query':
                    tmp_term = '\\'+ tmp_term

                self.view.render(tmp_term, self.partial_typing)
            self.view.must_show_linking_pos = False

            # Get input
            ch = self.window.getch()
            next_user_input = self.input_to_symbol(ch)
            logging.debug("Input {} converted to {} in mode {}".format(ch, next_user_input, self.current_mode))
            user_input.append(next_user_input)
            tuser_input = tuple(user_input)
            if (self.current_mode[-1], tuser_input) not in self.config.valid_prefixes:
                if (None, tuser_input) not in self.config.valid_prefixes:
                    if (self.current_mode[-1], tuser_input) not in self.config.input_to_action:
                        if (None, tuser_input) not in self.config.input_to_action:
                            user_input = [next_user_input]
                            tuser_input = (next_user_input,)
            nsteps += 1
            if nsteps % 100 == 0 and self.current_mode[-1] == 'category':
                self.datum.write_out()

            # Determine what to do for the input
            action = None
            function = None
            if (self.current_mode[-1], tuser_input) in self.config.input_to_action:
                action = self.config.input_to_action[self.current_mode[-1], tuser_input]
                if action in self.action_to_function:
                    function = self.action_to_function[action]
            elif (None, tuser_input) in self.config.input_to_action:
                action = self.config.input_to_action[None, tuser_input]
                if action in self.action_to_function:
                    function = self.action_to_function[action]
            logging.debug("{} {} -> {} {}".format(self.current_mode, tuser_input, action, function))

            # Do it!
            if function is not None:
                outcome = function(tuser_input, action)
                user_input = []
                if outcome == 'quit':
                    break

            # Clear the screen in preparation for rendering it again
            self.window.clear()

        # Write out information for continuing annotation later
        out_filename = self.args.log_prefix + '.todo'
        out = open(out_filename, "w")
        for fname, start_pos, output_file, annotation_files in self.filenames:
            parts = [
                fname,
                output_file,
                str(start_pos), # TODO - simplified value here
                ' '.join(annotation_files)
            ]
            print(" ".join(parts), file=out)
        out.close()

def ext_annotate(window_in, annotator):
    annotator.annotate(window_in)

def main():
    stime = datetime.datetime.now().strftime('%Y-%m-%d.%H-%M-%S')

    parser = argparse.ArgumentParser(
            description='A tool for annotating text data.',
            fromfile_prefix_chars='@')
    parser.add_argument('data', nargs="*",
            help='Files to be annotated')
    parser.add_argument('-d', '--data-list', nargs="+",
            help='Files containing lists of files to be annotated')

    parser.add_argument('-t', '--ann-type',
            choices=['categorical', 'link'],
            default='categorical',
            help='The type of annotation being done.')
    parser.add_argument('-s', '--ann-scope',
            choices=['character', 'token', 'line', 'document'],
            default='token',
            help='The scope of annotation being done.')
    parser.add_argument('-c', '--config-file',
            help='A file containing configuration information.')
    parser.add_argument('-l', '--log-prefix',
            default="annotation_log."+ stime,
            help='Prefix for logging files')
    parser.add_argument('-ld', '--log-debug',
            action='store_true',
            help='Provide detailed logging.')

    parser.add_argument('-hh', '--hide-help',
            action='store_true',
            help='Do not show help on startup.')
    parser.add_argument('-r', '--readonly',
            action='store_true',
            help='Do not allow changes or save annotations.')
    parser.add_argument('-o', '--overwrite',
            default=False,
            action='store_true',
            help='If they exist already, read abd overwrite output files.')

    parser.add_argument('-ps', '--prevent-self-links',
            default=False,
            action='store_true',
            help='Prevent an item from being linked to itself.')
    parser.add_argument('-pf', '--prevent-forward-links',
            default=False,
            action='store_true',
            help='Prevent a link from an item to one after it.')

    parser.add_argument('--do-not-show-linked',
            default=False,
            action='store_true',
            help='Do not have a special color to indicate any linked token.')
    parser.add_argument('--alternate-comparisons',
            default=False,
            action='store_true',
            help='Activate alternative way of showing different annotations '
            '(one colour per set of markings, rather than counts).')

    args = parser.parse_args()

    if len(args.data) == 0 and args.data_list is None:
        parser.error("No filenames or data lists provided")

    # Set up logging
    logging_level = logging.DEBUG if args.log_debug else logging.INFO
    logging.basicConfig(filename=args.log_prefix + '.log', level=logging_level)
    logging.info("Executed with: {}".format(' '.join(sys.argv)))
    logging.info("Arguments interpreted as: {}".format(args))
    if logging_level == logging.INFO:
        sys.tracebacklimit = 1

    ### Process configuration
    config = None
    if args.config_file is not None:
        config = Config(args)
    else:
        config = Config(args, 
            {
                'label:a': (('SPACE', 'a'), 'green'),
                'label:s': (('SPACE', 's'), 'blue'),
                'label:d': (('SPACE', 'd'), 'magenta'),
                'label:v': (('SPACE', 'v'), 'red'),
            }
        )

    file_info = args.data
    if args.data_list is not None:
        for filename in args.data_list:
            if len(glob.glob(filename)) == 0:
                raise Exception("Cannot open / find '{}'".format(filename))
            for line in open(filename):
                file_info.append(line.strip())

    filenames = process_fileinfo(file_info, config)
    if len(filenames) == 0:
        print("Found no files")
        sys.exit(0)

    config_out = open(args.log_prefix + '.config', 'w')
    print(config, file=config_out)
    config_out.close()

    # Set the current mode
    current_mode = []
    if args.readonly:
        current_mode.append('read')
    elif args.ann_type == 'categorical':
        current_mode.append('category')
    elif args.ann_type == 'link':
        current_mode.append('link')

    ### Start interface
    annotator = Annotator(config, filenames, current_mode, args)
    curses.wrapper(ext_annotate, annotator)
