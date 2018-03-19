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
    cursor = position
    link = position if config.annotation_type == AnnType.link else None
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
            nsteps += 1
            if nsteps % 100 == 0 and config.mode == Mode.annotate:
                datum.write_out()

            if user_input == ord('/'):
                typing_command = True
                search_term = ''
            elif user_input in [ord('c'), 337]:
                # Note - 337 is SHIFT + UP on a mac keyboard
                if config.annotation_type == AnnType.link:
                    view.move('up', 1, False, True)
                    view.must_show_linking_pos = True
                else:
                    view.move('up', 1, True)
            elif user_input in [ord('v'), 336]:
                # Note - 336 is SHIFT + DOWN on a mac keyboard
                if config.annotation_type == AnnType.link:
                    view.move('down', 1, False, True)
                    view.must_show_linking_pos = True
                else:
                    view.move('down', 1, True)
            elif user_input == curses.KEY_SLEFT:
                if config.annotation_type == AnnType.link:
                    view.move('left', 1, False, True)
                else:
                    view.move('left', 1, True)
            elif user_input == curses.KEY_SRIGHT:
                if config.annotation_type == AnnType.link:
                    view.move('right', 1, False, True)
                else:
                    view.move('right', 1, True)
            elif user_input == curses.KEY_UP:
                view.move('up', 1)
            elif user_input == curses.KEY_DOWN:
                view.move('down', 1)
            elif user_input == curses.KEY_LEFT:
                view.move('left', 1)
            elif user_input == curses.KEY_RIGHT:
                view.move('right', 1)
            elif user_input == ord("o"):
                view.shift_view()
            elif user_input == ord("l"):
                view.shift_view(True)
            elif user_input == ord("h"):
                view.toggle_help()
            elif user_input in [ord("P"), ord("n")]:
                # TODO: previous search term or disagreement
                pass
            elif user_input in [ord("N"), ord("p")]:
                # TODO: next search term or disagreement
                pass
            elif user_input == ord("d") and config.mode == Mode.annotate:
                if config.annotation_type == AnnType.link:
                    datum.modify_annotation([view.cursor, view.linking_pos])
                    if config.annotation == AnnScope.line:
                        view.move('down', 1, False, True)
                        view.put_cursor_beside_link()
                    else:
                        view.move('right', 1, False, True)
                        view.put_cursor_beside_link()
                    view.must_show_linking_pos = True
            elif user_input == ord("D") and config.mode == Mode.annotate:
                if config.annotation_type == AnnType.link:
                    datum.modify_annotation([view.cursor, view.linking_pos])
            elif user_input == ord("u") and config.mode == Mode.annotate:
                spans = [view.cursor]
                if config.annotation_type == AnnType.link:
                    spans.append(view.linking_pos)
                datum.remove_annotation(spans)
            elif user_input in [ord('s'), ord('b'), ord('r')]:
                if config.mode == Mode.annotate:
                    if config.annotation_type != AnnType.link:
                        datum.modify_annotation([view.cursor], chr(user_input))
            elif user_input in [ord(c) for c in ",.q"]:
                # If we can get another file, do
                if config.mode == Mode.annotate:
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
    parser.add_argument('--mode', help='High-level control of what the tool does.', choices=[v for v in Mode.__members__], default='annotate')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_prefix + '.log', level=logging.DEBUG)

    logging.info("New run!")

    ### Process configuration
    mode = Mode.read if args.readonly else Mode.annotate
    config = get_config(args, mode)
    filenames = read_filenames(args.data, config)
    if len(filenames) == 0:
        print("File '{}' contained no filenames".format(args.data))
        sys.exit(0)

    ### Start interface
    curses.wrapper(annotate, config, filenames)
