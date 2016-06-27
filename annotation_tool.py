#!/usr/bin/env python3

import curses, sys, re

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
#  n            - move to next numerical value
#  p            - move to previous numerical value
#  s            - mark this token as {}
#  b            - mark this token as []
#  /            - save and go to next file
#  u, b, s      - undo annotation on this token
#  q            - quit
#
# The current token is blue, {} tokens are green and [] tokens are yellow. The
# tokens are also modified to show the {} and [].  If a file is too long to
# display on a single screen, moving off the top or bottom will cause redrawing
# so that the current token is always visible.

# TODO:
#  - add 'n'

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

class View:
  def __init__(self, window, pos, marked, data):
    self.window = window
    self.pos = pos
    self.marked = marked
    self.data = data
    self.inst_lines = 3
    self.top = 0

  def do_contents(self, height, width, trial=False):
    seen = False
    cpos = 0
    cline = self.inst_lines
    for line_no, line in enumerate(self.data):
      # If this line is above the top of what we are shwoing, skip it
      if line_no < self.top:
        continue

      for token_no, token in enumerate(line):
        cpair = (line_no, token_no)
        current = (tuple(self.pos) == cpair)
        marked_sell = (cpair in self.marked and self.marked[cpair] == 's')
        marked_buy = (cpair in self.marked and self.marked[cpair] == 'b')

        colour = 4
        if marked_sell: colour = 2
        if marked_buy: colour = 3
        if current: colour = 1
        ttoken = token
        if marked_sell: ttoken = '{' + token + '}'
        if marked_buy: ttoken = '[' + token + ']'

        length = len(ttoken) + 1
        if cpos + length >= width:
          cpos = 0
          cline += 1

        if cline >= height:
          # Not printing as we are off the screen
          pass
        else:
          if not trial:
            self.window.addstr(cline, cpos, ' '+ ttoken, curses.color_pair(colour))
          if current:
            seen = True
        cpos += len(ttoken) + 1
      cline += 1
      cpos = 0
    return seen

  def render(self):
    height, width = self.window.getmaxyx()

    # First, draw instructions
    if height >= self.inst_lines:
      self.window.addstr(0, 0, "Current token is blue, marked tokens are also coloured            ", curses.color_pair(5))
      self.window.addstr(1, 0, "arrows (move one token)  n p (next and previous number, via regex)", curses.color_pair(5))
      self.window.addstr(2, 0, "b (mark / unmark [])  / (next file)  q (quit)", curses.color_pair(5))

    # Shift the top up if necessary
    if self.top > self.pos[0]:
      self.top = self.pos[0]
    # Do dry runs, shifting top down until the position is visible
    while not self.do_contents(height, width, True):
      self.top += 1

    # Next, draw contents
    self.do_contents(height, width)
    self.window.refresh()

def annotate(window):
  filenames = [line.strip() for line in open(sys.argv[1]).readlines()]

  out_filename = "files_still_to_do"
  if len(sys.argv) > 2:
    out_filename = sys.argv[2]
  out = open(out_filename, "w")

  # Set colour combinations
  curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
  curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
  curses.curs_set(0) # No blinking cursor

  cfilename = 0
  data = read_file(filenames[cfilename])

  ctoken = [0, 0]
  marked = {}
  view = View(window, ctoken, marked, data)
  number_regex = re.compile('^[,0-9]*[.]?[0-9][,0-9]*[.]?[,0-9]*$')
  while True:
    # Draw screen
    view.render()

    # Get input
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
    elif c == ord("n"):
      # Find next position, use regex
      for line_no in range(ctoken[0], len(data)):
        done = False
        for token_no in range(len(data[line_no])):
          if line_no == ctoken[0] and token_no <= ctoken[1]:
            continue
          if number_regex.match(data[line_no][token_no]):
            done = True
            ctoken[0] = line_no
            ctoken[1] = token_no
        if done:
          break
    elif c == ord("p"):
      # Find next position, use regex
      for line_no in range(ctoken[0], -1, -1):
        done = False
        for token_no in range(len(data[line_no]), -1, -1):
          if line_no == ctoken[0] and token_no >= ctoken[1]:
            continue
          if number_regex.match(data[line_no][token_no]):
            done = True
            ctoken[0] = line_no
            ctoken[1] = token_no
        if done:
          break
    elif c == ord("s"):
      if (ctoken[0], ctoken[1]) in marked and marked[ctoken[0], ctoken[1]] == "s":
        marked.pop((ctoken[0], ctoken[1]))
      else:
        marked[ctoken[0], ctoken[1]] = "s"
    elif c == ord("b"):
      if (ctoken[0], ctoken[1]) in marked and marked[ctoken[0], ctoken[1]] == "b":
        marked.pop((ctoken[0], ctoken[1]))
      else:
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
        break
      data = read_file(filenames[cfilename])
      view.data = data

      # Reset, but do not rename as we want the view to have the same objects still
      marked.clear()
      ctoken[0] = 0
      ctoken[1] = 0
    elif c == ord("q"):
      print('\n'.join(filenames[cfilename:]), file=out)
      break
    window.clear()

  out.close()

if len(sys.argv) < 2:
  print("Usage:\n{} <file with a list of files to annotate> [<logging filename, default='files_still_to_do']".format(sys.argv[0]))
  print("\nFor example:\n> find . | grep 'tok$' > filenames_todo\n> {} filenames_todo do_later\n... do some work, then quit, go away, come back...\n> {} do_later do_even_later\n".format(sys.argv[0], sys.argv[0]))
  sys.exit(1)

curses.wrapper(annotate)

