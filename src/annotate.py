#!/usr/bin/env python3

from __future__ import print_function

import argparse
import curses
import datetime
import logging
import string
import sys

from data import *
from config import *
from view import *

current_mode = []
current_num = None
search_term = ''
partial_typing = ''
cfilename = -1
filename = None
datum = None
view = None
window = None
config = None

def move(user_input, action):
    global current_num, current_mode, view
    if current_mode[-1] == 'no_file':
        return

    direction = action.split('-')[-1]
    jump = 'jump' in action
    link = 'link' in action

    num = 1
    if current_num == 0:
        jump = True
        current_num = None
    elif current_num is not None:
        num = current_num
        current_num = None

    view.move(direction, num, jump, link)

def toggle_line_numbers(user_input, action):
    global view
    view.line_numbers = not view.line_numbers

def change_span(user_input, action):
    global current_num, current_mode, view
    if current_mode[-1] == 'no_file':
        return

    change = action.split('-')[0]
    direction = action.split('-')[-1]
    # TODO: Support these adjustments to the linking_pos too. This requires
    # edits to view and also to config
    link = 'link' in action

    num = 1
    jump = False
    if current_num == 0:
        jump = True
        current_num = None
    elif current_num is not None:
        num = current_num
        current_num = None

    view.adjust(direction, num, change, jump, link)

def delete_typing_char(user_input, action):
    global search_term, partial_typing
    if current_mode[-1] == 'no_file':
        return

    if current_mode[-1] == 'write_query':
        search_term = search_term[:-1]
    else:
        partial_typing = partial_typing[:-1]

def leave_typing_mode(user_input, action):
    global current_mode, partial_typing
    if current_mode[-1] == 'no_file':
        return

    if len(current_mode) > 1:
        current_mode.pop()

def assign_text(user_input, action):
    global current_mode, partial_typing
    if current_mode[-1] == 'no_file':
        return

    if len(current_mode) > 1:
        current_mode.pop()
        datum.modify_annotation([view.cursor], partial_typing)
        partial_typing = ''

def enter_typing_mode(user_input, action):
    global current_mode, partial_typing
    if current_mode[-1] == 'no_file':
        return

    if 'query' in action:
        current_mode.append('write_query')
    else:
        current_mode.append('write_label')
        partial_typing = ''

def clear_query(user_input, action):
    global current_mode, search_term, partial_typing
    if current_mode[-1] == 'no_file':
        return

    search_term = ''

def add_to_typing(user_input, action):
    global current_mode, search_term, partial_typing
    if current_mode[-1] == 'no_file':
        return

    char = user_input[0]
    if user_input[0] == 'SPACE':
        char = ' '
    if current_mode[-1] == 'write_query':
        search_term += char
    else:
        partial_typing += char

def change_file(user_input, action):
    global current_mode, cfilename, filename, datum, view, config

    if current_mode[-1] != 'no_file':
        save_or_quit(None, 'save')

    direction = 1 if 'next' in action else -1
    if current_mode[-1] == 'no_file':
        if (cfilename < 0) == (direction > 0):
            current_mode.pop()
            cfilename += direction
    elif 0 <= cfilename + direction < len(filenames):
        cfilename += direction
        filename, start_pos, output_file, annotation_files = \
                filenames[cfilename]
        datum = Datum(filename, config, output_file, annotation_files)
        view = get_view(datum, config, cfilename, len(filenames), start_pos, view)
    elif current_mode != 'no_file':
        cfilename += direction
        current_mode.append('no_file')

def modify_display(user_input, action):
    global view
    if current_mode[-1] == 'no_file':
        return

    if 'help' in action:
        view.toggle_help()
    elif 'progress' in action:
        view.toggle_progress()
    elif 'legend' in action:
        view.toggle_legend()

def shift_view(user_input, action):
    global view
    if current_mode[-1] == 'no_file':
        return

    if 'up' in action:
        view.shift_view()
    else:
        view.shift_view(True)

def update_number(user_input, action):
    global current_num
    if current_mode[-1] == 'no_file':
        return

    num = int(user_input[0])
    if current_num is None:
        current_num = 0
    else:
        current_num *= 10
    current_num += num

def remove_annotation(user_input, action):
    global view, current_mode, config
    if current_mode[-1] == 'no_file':
        return

    if current_mode[-1] != 'read':
        spans = [view.cursor]
        if current_mode[-1] == 'link':
            spans = [view.linking_pos]
        datum.remove_annotation(spans)

def edit_annotation(user_input, action):
    global view, current_mode, datum, config
    if current_mode[-1] == 'no_file':
        return

    if current_mode[-1] == 'category':
        label = config.get_label_for_input(user_input)
        datum.modify_annotation([view.cursor], label)

def create_link(user_input, action):
    global view, datum, config
    if current_mode[-1] == 'no_file':
        return

    datum.modify_annotation([view.cursor, view.linking_pos])
    if 'and-move' in action:
        if config.annotation == 'line':
            view.move('down', 1, False, True)
            view.put_cursor_beside_link()
        else:
            view.move('right', 1, False, True)
            view.put_cursor_beside_link()
        view.must_show_linking_pos = True

def save_or_quit(user_input, action):
    global view

    if 'save' in action:
        if current_mode[-1] != 'read':
            datum.write_out()

        # TODO: Save both cursor and linking pos
        if 0 <= cfilename < len(filenames):
            cur = filenames[cfilename]
            pos = view.cursor
            if config.annotation_type == 'link':
                pos = view.linking_pos
            filenames[cfilename] = (cur[0], pos, cur[2], cur[3])

    if 'quit' in action:
        if 'save' not in action:
            # TODO: Have an 'are you sure?' step
            pass
        return 'quit'

def search(user_input, action):
    global current_num, current_mode, view, search_term
    if current_mode[-1] == 'no_file':
        return

    direction = action.split('-')[-1]
    jump = False
    link = 'link' in action

    num = 1
    if current_num == 0:
        jump = True
        current_num = None
    elif current_num is not None:
        num = current_num
        current_num = None

    if len(search_term) > 0:
        view.search(search_term, direction, num, jump, link)
    else:
        # Used when comparing files to go to the next/previous annotation
        # Or when not comparing files to go to the next unannotated thing
        # When there is nothing unannotated, it jumps to the next self-linked item
        view.search(None, direction, num, jump, link)

action_to_function = {
    'delete-query-char': delete_typing_char,
    'leave-query-mode': leave_typing_mode,
    'enter-query-mode': enter_typing_mode,
    'clear-query': clear_query,
    'add-to-query': add_to_typing,
    'delete-label-char': delete_typing_char,
    'assign-text-label': assign_text,
    'enter-label-mode': enter_typing_mode,
    'add-to-label': add_to_typing,
    'toggle-line-numbers': toggle_line_numbers,
    'move-up': move,
    'move-down': move,
    'move-left': move,
    'move-right': move,
    'move-link-up': move,
    'move-link-down': move,
    'move-link-left': move,
    'move-link-right': move,
    'jump-up': move,
    'jump-down': move,
    'jump-left': move,
    'jump-right': move,
    'extend-up': change_span,
    'extend-down': change_span,
    'extend-left': change_span,
    'extend-right': change_span,
    'contract-up': change_span,
    'contract-down': change_span,
    'contract-left': change_span,
    'contract-right': change_span,
    'extend-link-up': change_span,
    'extend-link-down': change_span,
    'extend-link-left': change_span,
    'extend-link-right': change_span,
    'contract-link-up': change_span,
    'contract-link-down': change_span,
    'contract-link-left': change_span,
    'contract-link-right': change_span,
    'search-previous': search,
    'search-next': search,
    'search-link-previous': search,
    'search-link-next': search,
    'page-up': shift_view,
    'page-down': shift_view,
    'toggle-help': modify_display,
    'toggle-progress': modify_display,
    'toggle-legend': modify_display,
    'next-file': change_file,
    'previous-file': change_file,
    'quit': save_or_quit,
    'save-and-quit': save_or_quit,
    'save': save_or_quit,
    'create-link': create_link,
    'create-link-and-move': create_link,
    'edit-annotation': edit_annotation,
    'remove-annotation': remove_annotation,
    'update-num': update_number,
}

def input_to_symbol(num):
    if num in key_to_symbol:
        return key_to_symbol[num]
    else:
        return "UNKNOWN"

def get_view(datum, config, file_num, total_files, position, prev_view=None):
    global window

    cursor = position
    link = position if config.annotation_type == 'link' else None
    return View(window, cursor, link, datum, config, file_num, total_files, prev_view)

def annotate(window_in, config, filenames):
    global current_mode, search_term, cfilename, filename, datum, view, window

    window = window_in

    # Set color combinations
    for num, fore, back in COLORS:
        curses.init_pair(num, fore, back)

    # No blinking cursor
    curses.curs_set(0)

    cfilename = 0
    filename, start_pos, output_file, annotation_files = filenames[cfilename]
    datum = Datum(filename, config, output_file, annotation_files)
    view = get_view(datum, config, cfilename, len(filenames), start_pos)
    if not args.hide_help:
        view.toggle_help()

    last_num = None
    at_end = None
    nsteps = 0
    user_input = []
    while True:
        # Draw screen
        if current_mode[-1] == 'no_file':
            view.render_edgecase(cfilename >= 0)
        else:
            # Set current search term appearance
            tmp_term = search_term
            if current_mode[-1] == 'write_query':
                tmp_term = '\\'+ tmp_term

            view.render(tmp_term, partial_typing)
        view.must_show_linking_pos = False

        # Get input
        ch = window.getch()
        next_user_input = input_to_symbol(ch)
        logging.debug("Input {} converted to {} in mode {}".format(ch, next_user_input, current_mode))
        user_input.append(next_user_input)
        tuser_input = tuple(user_input)
        if (current_mode[-1], tuser_input) not in config.valid_prefixes:
            if (None, tuser_input) not in config.valid_prefixes:
                if (current_mode[-1], tuser_input) not in config.input_to_action:
                    if (None, tuser_input) not in config.input_to_action:
                        user_input = [next_user_input]
                        tuser_input = (next_user_input,)
        nsteps += 1
        if nsteps % 100 == 0 and current_mode[-1] == 'category':
            datum.write_out()

        # Determine what to do for the input
        action = None
        function = None
        if (current_mode[-1], tuser_input) in config.input_to_action:
            action = config.input_to_action[current_mode[-1], tuser_input]
            if action in action_to_function:
                function = action_to_function[action]
        elif (None, tuser_input) in config.input_to_action:
            action = config.input_to_action[None, tuser_input]
            if action in action_to_function:
                function = action_to_function[action]
        logging.debug("{} {} -> {} {}".format(current_mode, tuser_input, action, function))

        # Do it!
        if function is not None:
            outcome = function(tuser_input, action)
            user_input = []
            if outcome == 'quit':
                break

        # Clear the screen in preparation for rendering it again
        window.clear()

    # Write out information for continuing annotation later
    out_filename = args.log_prefix + '.todo'
    out = open(out_filename, "w")
    for filename, start_pos, output_file, annotation_files in filenames:
        parts = [
            filename,
            output_file,
            str(start_pos), # TODO - simplified value here
            ' '.join(annotation_files)
        ]
        print(" ".join(parts), file=out)
    out.close()

if __name__ == '__main__':
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
    # Set the current mode
    if args.readonly:
        current_mode.append('read')
    elif args.ann_type == 'categorical':
        current_mode.append('category')
    elif args.ann_type == 'link':
        current_mode.append('link')

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

    ### Start interface
    curses.wrapper(annotate, config, filenames)
