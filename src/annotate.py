#!/usr/bin/env python3

from __future__ import print_function

import curses
import argparse
import logging
import sys
import string

from data import *
from config import *
from view import *

prev_mode = None
current_mode = Mode.category
current_num = None
search_term = ''
cfilename = -1
filename = None
datum = None
view = None
window = None
config = None

def move(user_input, action):
    global current_num, current_mode, view
    if current_mode == Mode.no_file:
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

def change_span(user_input, action):
    global current_num, current_mode, view
    if current_mode == Mode.no_file:
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

    view.adjust(direction, num, change, jump)

def delete_query_char(user_input, action):
    global search_term
    if current_mode == Mode.no_file:
        return

    search_term = search_term[:-1]

def leave_query_mode(user_input, action):
    global current_mode, prev_mode
    if current_mode == Mode.no_file:
        return

    if prev_mode is not None:
        current_mode = prev_mode
        prev_mode = None

def enter_query_mode(user_input, action):
    global current_mode, prev_mode
    if current_mode == Mode.no_file:
        return

    prev_mode = current_mode
    current_mode = Mode.write_query

def add_to_query(user_input, action):
    global search_term
    if current_mode == Mode.no_file:
        return

    search_term += chr(user_input)

def change_file(user_input, action):
    global current_mode, prev_mode, cfilename, filename, datum, view, config

    if current_mode != Mode.no_file:
        save_or_quit(None, 'save')

    direction = 1 if 'next' in action else -1
    if current_mode == Mode.no_file:
        if (cfilename == 0 and direction == 1) or (cfilename != 0 and direction == -1):
            current_mode = prev_mode
            prev_mode = None
    elif 0 <= cfilename + direction < len(filenames):
        cfilename += direction
        filename, start_pos, output_file, annotation_files = \
                filenames[cfilename]
        datum = Datum(filename, config, output_file, annotation_files)
        view = get_view(datum, config, cfilename, len(filenames), start_pos,
                view.show_help)
    elif current_mode != Mode.no_file:
        prev_mode = current_mode
        current_mode = Mode.no_file

def toggle_help(user_input, action):
    global view
    if current_mode == Mode.no_file:
        return

    view.toggle_help()

def shift_view(user_input, action):
    global view
    if current_mode == Mode.no_file:
        return

    if 'up' in action:
        view.shift_view()
    else:
        view.shift_view(True)

def update_number(user_input, action):
    global current_num
    if current_mode == Mode.no_file:
        return

    num = int(chr(user_input))
    if current_num is None:
        current_num = 0
    else:
        current_num *= 10
    current_num += num

def remove_annotation(user_input, action):
    global view, current_mode, config
    if current_mode == Mode.no_file:
        return

    if current_mode != Mode.read:
        spans = [view.cursor]
        if current_mode == Mode.link:
            spans.append(view.linking_pos)
        datum.remove_annotation(spans)

def edit_annotation(user_input, action):
    global view, current_mode, datum
    if current_mode == Mode.no_file:
        return

    if current_mode == Mode.category:
        datum.modify_annotation([view.cursor], chr(user_input))

def create_link(user_input, action):
    global view, datum, config
    if current_mode == Mode.no_file:
        return

    datum.modify_annotation([view.cursor, view.linking_pos])
    if 'and-move' in action:
        if config.annotation == AnnScope.line:
            view.move('down', 1, False, True)
            view.put_cursor_beside_link()
        else:
            view.move('right', 1, False, True)
            view.put_cursor_beside_link()
        view.must_show_linking_pos = True

def save_or_quit(user_input, action):
    global current_mode, filenames, cfilename

    if 'save' in action:
        if current_mode != Mode.read:
            datum.write_out()

        # TODO: Save both cursor and linking pos
        cur = filenames[cfilename]
        pos = view.cursor
        if config.annotation_type == AnnType.link:
            pos = view.linking_pos
        filenames[cfilename] = (cur[0], pos, cur[2], cur[3])

    if 'quit' in action:
        if 'save' not in action:
            # Have an 'are you sure?' step
            pass
        return 'quit'

action_to_function = {
    'delete-query-char': delete_query_char,
    'leave-query-mode': leave_query_mode,
    'enter-query-mode': enter_query_mode,
    'add-to-query': add_to_query,
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
    'next-match': None, # TODO
    'prev-match': None, # TODO
    'page-up': shift_view,
    'page-down': shift_view,
    'help-toggle': toggle_help,
    'next-file': change_file,
    'prev-file': change_file,
    'quit': save_or_quit,
    'save-and-quit': save_or_quit,
    'save': save_or_quit,
    'create-link': create_link,
    'create-link-and-move': create_link,
    'edit-annotation': edit_annotation,
    'remove-annotation': remove_annotation,
    'update-num': update_number,
}

def get_view(datum, config, file_num, total_files, position, show_help):
    global window

    cursor = position
    link = position if config.annotation_type == AnnType.link else None
    return View(window, cursor, link, datum, config, file_num, total_files, show_help)

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
    view = get_view(datum, config, cfilename, len(filenames), start_pos, True)

    last_num = None
    at_end = None
    nsteps = 0
    while True:
        # Set current search term appearance
        tmp_term = search_term
        if current_mode == Mode.write_query:
            tmp_term = '/'+ tmp_term

        # Draw screen
        if current_mode == Mode.no_file:
            view.render_edgecase(cfilename > 0)
        else:
            view.render(tmp_term)
        view.must_show_linking_pos = False

        # Get input
        user_input = window.getch()
        logging.info("Read {} in mode {}".format(user_input, current_mode))
        nsteps += 1
        if nsteps % 100 == 0 and current_mode == Mode.category:
            datum.write_out()

        # Determine what to do for the input
        action = None
        function = None
        if (mode, user_input) in input_to_action:
            action = input_to_action[mode, user_input]
            if action in action_to_function:
                function = action_to_function[action]
        elif (None, user_input) in input_to_action:
            action = input_to_action[None, user_input]
            if action in action_to_function:
                function = action_to_function[action]
        logging.info("{} {} -> {} {}".format(mode, user_input, action, function))

        # Do it!
        if function is not None:
            outcome = function(user_input, action)
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
            str(start_pos),
            ' '.join(annotation_files)
        ]
        print(" ".join(parts), file=out)
    out.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='A tool for annotating text data.',
            fromfile_prefix_chars='@')
    parser.add_argument('data',
            help='File containing a list of files to annotate')
    parser.add_argument('--log_prefix', default="annotation_log",
            help='Prefix for logging files (otherwise none)')
    parser.add_argument('--readonly', default=False,
            help='Do not allow changes or save annotations.')
    parser.add_argument('--overwrite', default=False, action='store_true',
            help='If they exist already, overwrite output files.')
    parser.add_argument('--show_linked', default=False, action='store_true')
            help='Have a highlight to indicate any linked token.')
    parser.add_argument('--allow_self_links', default=False,
            action='store_true',
            help='Allow an item to be linked to itself.')
    parser.add_argument('--alternate_comparisons', default=False,
            action='store_true',
            help='Activate alternative way of showing different annotations (one colour per set of markings, rather than counts).')
    parser.add_argument('--ann_type',
            choices=[v for v in AnnType.__members__], default='link',
            help='The type of annotation being done.')
    parser.add_argument('--ann_scope',
            choices=[v for v in AnnScope.__members__], default='line',
            help='The scope of annotation being done.')
    parser.add_argument('--mode',
            choices=[v for v in Mode.__members__], default='link',
            help='High-level control of what the tool does.')

    args = parser.parse_args()

    logging.basicConfig(filename=args.log_prefix + '.log', level=logging.DEBUG)

    logging.info("New run!")

    for opt in input_to_action:
        logging.info("{} is {}".format(opt, input_to_action[opt]))


    ### Process configuration
    current_mode = Mode[args.mode]
    if args.readonly:
        current_mode = Mode.read

    config = get_config(args)
    for key in config.keys:
        logging.info(key)
        opt = (Mode.category, ord(key))
        assert opt not in input_to_action, "{} as input and key".format(opt)
        input_to_action[opt] = 'edit-annotation'


    filenames = read_filenames(args.data, config)
    if len(filenames) == 0:
        print("File '{}' contained no filenames".format(args.data))
        sys.exit(0)

    ### Start interface
    curses.wrapper(annotate, config, filenames)
