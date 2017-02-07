#!/usr/bin/env python3

from __future__ import print_function

import curses
import argparse
import logging
import sys

from data import *
from config import *
from view import *

def get_view(window, datum, config, file_num, total_files, position, show_help=True):
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
    filename, start_pos, annotation_files = filenames[cfilename]
    datum = Datum(filename, config, annotation_files)
    view = get_view(window, datum, config, cfilename, len(filenames), start_pos)

    at_end = None
    while True:
        if at_end is None:
            # Draw screen
            view.render()
            view.must_show_linking_pos = False
            # Get input
            user_input = window.getch()

            # Note - First two are SHIFT + DOWN and SHIFT + UP, determined by
            # hand on two laptops.
            if user_input in [ord('c'), 337]:
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
                if config.annotation_type == AnnType.link: view.move_left(True)
                else: view.move_to_start()
            elif user_input == curses.KEY_SRIGHT:
                if config.annotation_type == AnnType.link: view.move_right(True)
                else: view.move_to_end()
            elif user_input == curses.KEY_UP: view.move_up()
            elif user_input == curses.KEY_DOWN: view.move_down()
            elif user_input == curses.KEY_LEFT: view.move_left()
            elif user_input == curses.KEY_RIGHT: view.move_right()
            elif user_input == ord("h"):
                view.toggle_help()
            elif user_input == ord("n"):
                if config.annotation_type != AnnType.link:
                    view.next_number()
            elif user_input == ord("p"):
                if config.annotation_type != AnnType.link:
                    view.next_number()
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
            elif user_input in [ord('s'), ord('b'), ord('r')] and config.mode == Mode.annotate:
                if config.annotation_type != AnnType.link:
                    datum.modify_annotation(view.cursor, view.linking_pos,
                            chr(user_input))
            elif user_input in [ord("/"), ord("\\"), ord(','), ord('.')]:
                # If we can get another file, do
                if config.mode == Mode.annotate:
                    datum.write_out()
                # TODO: Set to linking line rather than cursor where appropriate
                filenames[cfilename] = (filename, view.cursor, annotation_files)
                direction = 1 if user_input in [ord('.'), ord("/")] else -1
                if 0 <= cfilename + direction < len(filenames):
                    cfilename += direction
                    filename, start_pos, annotation_files = filenames[cfilename]
                    datum = Datum(filename, config, annotation_files)
                    view = get_view(window, datum, config, cfilename,
                            len(filenames), start_pos, view.show_help)
                elif direction > 0:
                    at_end = 'end'
                else:
                    at_end = 'start'
            elif user_input == ord("q"):
                if config.mode == Mode.annotate:
                    datum.write_out()
                # TODO: Set to linking line rather than cursor where appropriate
                filenames[cfilename] = (filename, view.cursor, annotation_files)
                break
        else:
            # Draw screen
            view.render_edgecase(at_end)
            # Get input
            user_input = window.getch()
            if at_end == 'start' and user_input in [ord('.'), ord("/")]:
                at_end = None
            elif at_end == 'end' and user_input in [ord(','), ord("\\")]:
                at_end = None
            elif user_input == ord("q"): break

        window.clear()

    out_filename = "files_still_to_do"
    overwrite = False
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-log' and len(sys.argv) > i + 1:
            out_filename = sys.argv[i + 1]
        if sys.argv[i] == '-overwrite':
            overwrite = True
    out = open(out_filename, "w")
    for filename, start_pos, annotation_files in filenames:
        print("{} {} {} {}".format(filename, start_pos[0], start_pos[1], ' '.join(annotation_files)), file=out)
    out.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A tool for annotating text data with extra information.')
    parser.add_argument('data', help='File containing a list of files to annotate')
    parser.add_argument('--output', help='File containing a list of files to annotate', choices=['overwrite', 'inline', 'standoff'], default="overwrite")
    parser.add_argument('--log_prefix', help='Prefix for logging files (otherwise none)')
    args = parser.parse_args()

    logging.basicConfig(filename="debug.txt",level=logging.DEBUG)

    ### Start interface
    filenames = read_filenames(args.data)
    if len(filenames) == 0:
        print("File '{}' contained no filenames".format(args.data))
        sys.exit(0)
    mode = Mode.annotate
    for _, _, annotations in filenames:
        if len(annotations) > 1:
            mode = Mode.compare
    config = get_default_config(args, mode)
    curses.wrapper(annotate, config, filenames)
