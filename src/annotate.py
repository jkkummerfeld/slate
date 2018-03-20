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

current_mode = Mode.category
current_num = None

def action_move(action, view, config):
    global current_num, current_mode

    direction = action.split('-')[-1]
    jump = 'jump' in action
    link = 'link' in action

    num = 1
    if current_num == 0:
        jump = True
    elif current_num is not None:
        num = current_num
        current_num = None

    view.move(direction, num, jump, link)

action_to_function = {
    'delete-query-char': None,
    'leave-query-mode': None,
    'enter-query-mode': None,
    'move-up': action_move,
    'move-down': action_move,
    'move-left': action_move,
    'move-right': action_move,
    'move-link-up': action_move,
    'move-link-down': action_move,
    'move-link-left': action_move,
    'move-link-right': action_move,
    'jump-up': action_move,
    'jump-down': action_move,
    'jump-left': action_move,
    'jump-right': action_move,
    'extend-up': None,
    'extend-down': None,
    'extend-left': None,
    'extend-right': None,
    'contract-up': None,
    'contract-down': None,
    'contract-left': None,
    'contract-right': None,
    'next-match': None,
    'prev-match': None,
    'page-up': None,
    'page-down': None,
    'help-toggle': None,
    'next-file': None,
    'prev-file': None,
    'quit': None, # Have an 'are you sure?' step
    'save-and-quit': None,
    'save': None,
    'create-link': None,
    'create-link-and-move': None,
    'remove-annotation': None,
    'update-num': None,
}

def get_view(window, datum, config, file_num, total_files, position, show_help):
    cursor = position
    link = position if config.annotation_type == AnnType.link else None
    return View(window, cursor, link, datum, config, file_num, total_files, show_help)

def annotate(window, config, filenames):
    global current_mode

    # Set color combinations
    for num, fore, back in COLORS:
        curses.init_pair(num, fore, back)

    # No blinking cursor
    curses.curs_set(0)

    cfilename = 0
    filename, start_pos, output_file, annotation_files = filenames[cfilename]
    datum = Datum(filename, config, output_file, annotation_files)
    view = get_view(window, datum, config, cfilename, len(filenames),
            start_pos, True)

    last_num = None
    at_end = None
    search_term = ''
    typing_command = False
    nsteps = 0
    while True:
        if at_end is not None:
            # Draw screen
            view.render_edgecase(at_end)
            # Get input
            user_input = window.getch()
            if at_end == 'start' and user_input in [ord('.'), ord("/")]:
                at_end = None
            elif at_end == 'end' and user_input in [ord(','), ord("\\")]:
                at_end = None
            elif user_input == ord("q"):
                break
        elif typing_command:
            # Draw screen
            view.render("/"+ search_term)
            view.must_show_linking_pos = False
            # Get input
            user_input = window.getch()
            nsteps += 1
            if nsteps % 100 == 0 and config.mode == Mode.category:
                datum.write_out()

            # TODO: Hacky, these numbers were worked out by hand.
            if user_input in [ord('?'), 10]: # Enter
                typing_command = False
            elif user_input in [ord('!'), 263, 127]: # Backspace
                search_term = search_term[:-1]
            elif user_input in [ord(v) for v in string.printable]:
                search_term += chr(user_input)
        else:
            # Draw screen
            view.render(search_term)
            view.must_show_linking_pos = False
            # Get input
            user_input = window.getch()
            logging.info("Read {} in mode {}".format(user_input, current_mode))
            nsteps += 1
            if nsteps % 100 == 0 and config.mode == Mode.category:
                datum.write_out()

            action = None
            function = None
            if (current_mode, user_input) in input_to_action:
                action = input_to_action[current_mode, user_input]
                if action in action_to_function:
                    function = action_to_function[action]
            elif (None, user_input) in input_to_action:
                action = input_to_action[None, user_input]
                if action in action_to_function:
                    function = action_to_function[action]

            logging.info("{} {} -> {} {}".format(current_mode, user_input, action, function))

            if function is not None:
                function(action, view, config)
            elif user_input == ord('\\'):
                typing_command = True
                search_term = ''
            elif user_input in [
                    curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT,
                    curses.KEY_RIGHT, ord('j'), ord('i'), ord('o'), ord(';')
                    ]:
                direction = 'up'
                if user_input == curses.KEY_DOWN: direction = 'down'
                if user_input == curses.KEY_LEFT: direction = 'left'
                if user_input == curses.KEY_RIGHT: direction = 'right'
                if user_input == ord('o'): direction = 'down'
                if user_input == ord('j'): direction = 'left'
                if user_input == ord(';'): direction = 'right'

                num = 1
                jump = False
                if last_num == 0:
                    jump = True
                elif last_num is not None:
                    num = last_num
                    last_num = None

                view.move(direction, num, jump)
            elif user_input in [ord('I'), 337]:
                # Note - 337 is SHIFT + UP on a mac keyboard
                if config.annotation_type == AnnType.link:
                    view.move('up', 1, False, True)
                    view.must_show_linking_pos = True
                else:
                    view.move('up', 1, True)
            elif user_input in [ord('O'), 336]:
                # Note - 336 is SHIFT + DOWN on a mac keyboard
                if config.annotation_type == AnnType.link:
                    view.move('down', 1, False, True)
                    view.must_show_linking_pos = True
                else:
                    view.move('down', 1, True)
            elif user_input in [curses.KEY_SLEFT, ord('J')]:
                if config.annotation_type == AnnType.link:
                    view.move('left', 1, False, True)
                else:
                    view.move('left', 1, True)
            elif user_input in [curses.KEY_SRIGHT, ord(':')]:
                if config.annotation_type == AnnType.link:
                    view.move('right', 1, False, True)
                else:
                    view.move('right', 1, True)
            elif user_input in [ord('m'), ord('M'), ord('k'), ord('K'),
                    ord('l'), ord('L'), ord('/'), ord('?')
                    ]:
                symbol = chr(user_input)
                direction = 'right'
                change = 'extend' if symbol in 'mkl/' else 'contract'
                if symbol.lower() == 'm': direction = 'left'
                if symbol.lower() == 'k': direction = 'up'
                if symbol.lower() == 'l': direction = 'down'
                num = 1
                jump = False
                if last_num == 0:
                    jump = True
                elif last_num is not None:
                    num = last_num
                view.adjust(direction, num, change, jump)
            elif user_input in [curses.KEY_PPAGE, ord("o")]:
                view.shift_view()
            elif user_input in [curses.KEY_NPAGE, ord("l")]:
                view.shift_view(True)
            elif user_input == ord("h"):
                view.toggle_help()
            elif user_input in [ord("P"), ord("n")]:
                # TODO: previous search term or disagreement
                pass
            elif user_input in [ord("N"), ord("p")]:
                # TODO: next search term or disagreement
                pass
            elif user_input == ord("d") and config.mode == Mode.category:
                if config.annotation_type == AnnType.link:
                    datum.modify_annotation([view.cursor, view.linking_pos])
                    if config.annotation == AnnScope.line:
                        view.move('down', 1, False, True)
                        view.put_cursor_beside_link()
                    else:
                        view.move('right', 1, False, True)
                        view.put_cursor_beside_link()
                    view.must_show_linking_pos = True
            elif user_input == ord("D") and config.mode == Mode.category:
                if config.annotation_type == AnnType.link:
                    datum.modify_annotation([view.cursor, view.linking_pos])
            elif user_input == ord("u") and config.mode == Mode.category:
                spans = [view.cursor]
                if config.annotation_type == AnnType.link:
                    spans.append(view.linking_pos)
                datum.remove_annotation(spans)
            elif user_input in [ord('s'), ord('b'), ord('r')]:
                if config.mode == Mode.category:
                    if config.annotation_type != AnnType.link:
                        datum.modify_annotation([view.cursor], chr(user_input))
            elif user_input in [ord(c) for c in ",.q"]:
                # If we can get another file, do
                if config.mode == Mode.category:
                    datum.write_out()
                # TODO: Set to linking line rather than cursor where
                # appropriate
                cur = filenames[cfilename]
                pos = view.cursor
                if config.annotation_type == AnnType.link:
                    pos = view.linking_pos
                filenames[cfilename] = (cur[0], pos, cur[2], cur[3])
                if user_input == ord('q'):
                    break

                direction = 1 if user_input == ord('.') else -1
                if 0 <= cfilename + direction < len(filenames):
                    cfilename += direction
                    filename, start_pos, output_file, annotation_files = \
                            filenames[cfilename]
                    datum = Datum(filename, config, output_file,
                            annotation_files)
                    view = get_view(window, datum, config, cfilename,
                            len(filenames), start_pos, view.show_help)
                elif direction > 0:
                    at_end = 'end'
                else:
                    at_end = 'start'

            if user_input in [ord(n) for n in '0123456789']:
                last_num = int(chr(user_input))
            else:
                last_num = None

        window.clear()

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
    parser = argparse.ArgumentParser(description='A tool for annotating text data with extra information.', fromfile_prefix_chars='@')
    parser.add_argument('data', help='File containing a list of files to annotate')
    parser.add_argument('--log_prefix', help='Prefix for logging files (otherwise none)', default="annotation_log")
    parser.add_argument('--readonly', help='Do not allow changes or save annotations.', default=False)
    parser.add_argument('--overwrite', help='If they exist already, overwrite output files.', default=False, action='store_true')
    parser.add_argument('--show_linked', help='Have a highlight to indicate any linked token.', default=False, action='store_true')
    parser.add_argument('--allow_self_links', help='Allow an item to be linked to itself.', default=False, action='store_true')
    parser.add_argument('--alternate_comparisons', help='Activate alternative way of showing different annotations (one colour per set of markings, rather than counts).', default=False, action='store_true')
    parser.add_argument('--ann_type', help='The type of annotation being done.', choices=[v for v in AnnType.__members__], default='link')
    parser.add_argument('--ann_scope', help='The scope of annotation being done.', choices=[v for v in AnnScope.__members__], default='line')
    parser.add_argument('--mode', help='High-level control of what the tool does.', choices=[v for v in Mode.__members__], default='link')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_prefix + '.log', level=logging.DEBUG)

    logging.info("New run!")

    for opt in input_to_action:
        logging.info("{} is {}".format(opt, input_to_action[opt]))

    current_mode = Mode[args.mode]

    ### Process configuration
    mode = Mode.read if args.readonly else Mode.category
    config = get_config(args, mode)
    filenames = read_filenames(args.data, config)
    if len(filenames) == 0:
        print("File '{}' contained no filenames".format(args.data))
        sys.exit(0)

    ### Start interface
    curses.wrapper(annotate, config, filenames)
