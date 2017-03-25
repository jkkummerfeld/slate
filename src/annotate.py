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

def get_view(window, datum, config, file_num, total_files, position, show_help):
    cursor = position[:]
    link = position[:] if config.annotation_type == AnnType.link else [-1, -1]
    return View(window, cursor, link, datum, config, file_num, total_files, show_help)

def annotate(window, config, filenames):
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
            if nsteps % 100 == 0 and config.mode == Mode.annotate:
                datum.write_out()

###            logging.debug("Got:" + str(user_input))

            # TODO: Hacky, these numbers were worked out by hand.
            if user_input in [ord('?'), 10]:
                typing_command = False
            elif user_input in [ord('!'), 263, 127]:
                search_term = search_term[:-1]
            elif user_input in [ord(v) for v in string.printable]:
                search_term += chr(user_input)
        else:
            # Draw screen
            view.render(search_term)
            view.must_show_linking_pos = False
            # Get input
            user_input = window.getch()
            nsteps += 1
            if nsteps % 100 == 0 and config.mode == Mode.annotate:
                datum.write_out()

            # Note - First two are SHIFT + DOWN and SHIFT + UP, determined by
            # hand on two laptops.
            if user_input == ord('/'):
                typing_command = True
                search_term = ''
            elif user_input in [ord('c'), 337]:
                if config.annotation_type == AnnType.link:
                    view.move_up(True)
                    view.must_show_linking_pos = True
                else:
                    view.move_to_top()
            elif user_input in [ord('v'), 336]:
                if config.annotation_type == AnnType.link:
                    view.move_down(True)
                    view.must_show_linking_pos = True
                else:
                    view.move_to_bottom()
            elif user_input == curses.KEY_SLEFT:
                if config.annotation_type == AnnType.link:
                    view.move_left(True)
                else:
                    view.move_to_start()
            elif user_input == curses.KEY_SRIGHT:
                if config.annotation_type == AnnType.link:
                    view.move_right(True)
                else:
                    view.move_to_end()
            elif user_input == curses.KEY_UP:
                view.move_up()
            elif user_input == curses.KEY_DOWN:
                view.move_down()
            elif user_input == curses.KEY_LEFT:
                view.move_left()
            elif user_input == curses.KEY_RIGHT:
                view.move_right()
            elif user_input == ord("h"):
                view.toggle_help()
            elif user_input == ord("n"):
                if len(search_term) > 0:
                    view.next_match(search_term)
                else:
                    view.next_disagreement()
            elif user_input == ord("p"):
                if len(search_term) > 0:
                    view.previous_match(search_term)
                else:
                    view.previous_disagreement()
            elif user_input == ord("d") and config.mode == Mode.annotate:
                datum.modify_annotation(view.cursor, view.linking_pos)
                if config.annotation_type == AnnType.link:
                    if config.annotation == AnnScope.line:
                        view.move_down(True)
                        view.cursor[0] = view.linking_pos[0]
                        view.cursor[1] = view.linking_pos[1]
                        view.move_up()
                    else:
                        view.move_right(True)
                        view.cursor[0] = view.linking_pos[0]
                        view.cursor[1] = view.linking_pos[1]
                        view.move_left()
                    view.must_show_linking_pos = True
            elif user_input == ord("D") and config.mode == Mode.annotate:
                datum.modify_annotation(view.cursor, view.linking_pos)
            elif user_input == ord("u") and config.mode == Mode.annotate:
                datum.remove_annotation(view.cursor, view.linking_pos)
            elif user_input in [ord('s'), ord('b'), ord('r')]:
                if config.mode == Mode.annotate:
                    if config.annotation_type != AnnType.link:
                        datum.modify_annotation(view.cursor, view.linking_pos,
                                chr(user_input))
            elif user_input in [ord(c) for c in ",.q"]:
                # If we can get another file, do
                if config.mode == Mode.annotate:
                    datum.write_out()
                # TODO: Set to linking line rather than cursor where
                # appropriate
                filenames[cfilename][1][0] = view.cursor[0]
                filenames[cfilename][1][1] = view.cursor[1]
                if user_input == ord('q'):
                    break

                direction = 1 if user_input in [ord('.'), ord("/")] else -1
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

        window.clear()

    out_filename = args.log_prefix + '.todo'
    out = open(out_filename, "w")
    for filename, start_pos, output_file, annotation_files in filenames:
        parts = [
            filename,
            output_file,
            str(start_pos[0]), str(start_pos[1]),
            ' '.join(annotation_files)
        ]
        print(" ".join(parts), file=out)
    out.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A tool for annotating text data with extra information.')
    parser.add_argument('data', help='File containing a list of files to annotate')
    parser.add_argument('--log_prefix', help='Prefix for logging files (otherwise none)', default="annotation_log")
    parser.add_argument('--readonly', help='Do not allow changes or save annotations.', default=False)
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_prefix + '.log', level=logging.DEBUG)

    ### Process configuration
    mode = Mode.read if args.readonly else Mode.annotate
    config = get_default_config(args, mode)
    filenames = read_filenames(args.data, config)
    if len(filenames) == 0:
        print("File '{}' contained no filenames".format(args.data))
        sys.exit(0)

    ### Start interface
    curses.wrapper(annotate, config, filenames)
