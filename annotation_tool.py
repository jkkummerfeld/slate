#!/usr/bin/env python3

import curses, sys

# Usage:
#   ./annotation_tool.py <filename>
# The file should contain a list of files to be annotated.
#
# You will be shown the first file in plain text. Commands are:
#
#  left arrow   - move to previous word
#  right arrow  - move to next word
#  up arrow     - move up a line
#  down arrow   - move down a line
#  s            - mark this token as {}
#  b            - mark this token as []
#  /            - save and go to next file
#  u            - undo annotation on this token
#
# The current token is blue, {} tokens are green and [] tokens are yellow. The
# tokens are also modified to show the {} and [].  If a file is too long to
# display on a single screen, it says so at the top, and the filename will be
# written out to a new file, "missed_files".

filenames = [line.strip() for line in open(sys.argv[1]).readlines()]

out = open("missed_files", "w")

def read_file(filename):
  data = open(filename).read()
  return [line.split() for line in data.split("\n")]

def write_file(filename, data, markings):
  out = open(filename + ".annotated", 'w')
  for line_no, line in enumerate(data):
    for token_no, token in enumerate(line):
      key = (line_no, token_no)
      if key in markings:
        if markings[key] == 's':
          print("{" + token +"}", end=" ", file=out)
        elif markings[key] == 'b':
          print("[" + token +"]", end=" ", file=out)
      else:
        print(token, end=" ", file=out)
    print("", file=out)

def annotate(window):
  height, width = window.getmaxyx()

  curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.curs_set(0) # No blinking cursor

  cfilename = 0
  data = read_file(filenames[cfilename])

  ctoken = [0, 0]
  marked = {}
  while True:
    # Draw screen
    cpos = 0
    cline = 0
    for line_no, line in enumerate(data):
      for token_no, token in enumerate(line):
        cpair = (line_no, token_no)
        current = (tuple(ctoken) == cpair)
        marked_sell = (cpair in marked and marked[cpair] == 's')
        marked_buy = (cpair in marked and marked[cpair] == 'b')

        length = len(token) + 2
        if marked_buy or marked_sell:
          length += 2

        if cpos + length >= width:
          cpos = 0
          cline += 1

        colour = 4
        if marked_sell: colour = 2
        if marked_buy: colour = 3
        if current: colour = 1
        ttoken = token
        if marked_sell: ttoken = '{' + token + '}'
        if marked_buy: ttoken = '[' + token + ']'

        if cline >= height:
          print(filenames[cfilename], file=out)
          window.addstr(0, 0, "FILE IS TOO LONG TO HANDLE THIS WAY, noted in output file missed_files")
        else:
          window.addstr(cline, cpos, ' '+ ttoken, curses.color_pair(colour))
        cpos += len(ttoken) + 1
      cline += 1
      cpos = 0
    window.refresh()

    c = window.getch()
    if c == curses.KEY_LEFT:
      ctoken[1] -= 1
      if ctoken[1] < 0:
        if ctoken[0] == 0:
          ctoken[1] = 0
        else:
          nline = ctoken[0] - 1
          while nline >= 0 and len(data[nline]) == 0:
            nline -= 1
          if nline >= 0:
            ctoken[0] = nline
            ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == curses.KEY_RIGHT:
      ctoken[1] += 1
      if ctoken[1] >= len(data[ctoken[0]]):
        if ctoken[0] == len(data) -1:
          ctoken[1] -= 1
        else:
          nline = ctoken[0] + 1
          while nline < len(data) and len(data[nline]) == 0:
            nline += 1
          if nline < len(data):
            ctoken[0] = nline
            ctoken[1] = 0
    elif c == curses.KEY_UP:
      if ctoken[0] > 0:
        nline = ctoken[0] - 1
        while nline >= 0 and len(data[nline]) == 0:
          nline -= 1
        if nline >= 0:
          ctoken[0] = nline
          if ctoken[1] >= len(data[ctoken[0]]):
            ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == curses.KEY_DOWN:
      if ctoken[0] < len(data) - 1:
        nline = ctoken[0] + 1
        while nline < len(data) and len(data[nline]) == 0:
          nline += 1
        if nline < len(data):
          ctoken[0] = nline
          if ctoken[1] >= len(data[ctoken[0]]):
            ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == ord("s"):
      marked[ctoken[0], ctoken[1]] = "s"
    elif c == ord("b"):
      marked[ctoken[0], ctoken[1]] = "b"
    elif c == ord("u"):
      if (ctoken[0], ctoken[1]) in marked:
        marked.pop((ctoken[0], ctoken[1]))
    elif c == ord("/"):
      # write out
      write_file(filenames[cfilename], data, marked)
      # get next
      cfilename += 1
      if len(filenames) <= cfilename:
        return
      data = read_file(filenames[cfilename])
      marked = {}
      ctoken = [0, 0]
    elif c == ord("q"):
      print('\n'.join(filenames[cfilename:]), file=out)
      return
    window.clear()

curses.wrapper(annotate)

out.close()
