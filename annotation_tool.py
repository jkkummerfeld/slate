#!/usr/bin/env python3

from __future__ import print_function

import curses, sys, re, glob

# Usage:
#   ./annotation_tool.py <filename>
# The file should contain a list of files to be annotated.
#
# You will be shown the first file in plain text. Commands are:
#
#  left arrow   - move to previous word (+shift, go to first)
#  right arrow  - move to next word (+shift, go to last)
#  up arrow     - move up a line (+shift, go to top)
#  down arrow   - move down a line (+shift, go to bottom)
#  n            - move to next numerical value
#  p            - move to previous numerical value
#  r            - mark this token as ||
#  s            - mark this token as {}
#  b            - mark this token as []
#  /  \         - save and go to next or previous file
#  u, b, s, r   - undo annotation on this token
#  q            - quit
#  h            - toggle help info (default on)
#
#
# The current token is blue, {} tokens are green and [] tokens are yellow. The
# tokens are also modified to show the {} and [].  If a file is too long to
# display on a single screen, moving off the top or bottom will cause redrawing
# so that the current token is always visible.

# TODO:
# - Previous files can not have annotations removed
# - Option to output to standoff annotations instead
# - adjustable keybinding

def read_file(filename):
  data = open(filename).read()
  return [line.split() for line in data.split("\n")]

def write_file(filename, data, markings, overwrite):
  out_filename = filename
  if not overwrite:
    out_filename += ".annotated"
  out = open(out_filename, 'w')
  for line_no, line in enumerate(data):
    if line_no != 0:
      print("", file=out)
    for token_no, token in enumerate(line):
      key = (line_no, token_no)
      ttoken = token
      if key in markings:
        if "s" in markings[key]:
          ttoken = "{" + ttoken +"}"
        if "b" in markings[key]:
          ttoken = "[" + ttoken +"]"
        if "r" in markings[key]:
          ttoken = "|" + ttoken +"|"
      print(ttoken, end=" ", file=out)

class View:
  def __init__(self, window, pos, marked, data, cnum, total_num):
    self.window = window
    self.pos = pos
    self.marked = marked
    self.data = data
    self.inst_lines = 3
    self.top = 0
    self.show_help = True
    self.progress = "done {} / {}".format(cnum, total_num)

  def do_contents(self, height, width, trial=False):
    # TODO: for blank lines, print only one in a row
    seen = False
    cpos = 0
    cline = self.inst_lines if self.show_help else 0
    for line_no, line in enumerate(self.data):
      # If this line is above the top of what we are shwoing, skip it
      if line_no < self.top:
        continue

      for token_no, token in enumerate(line):
        cpair = (line_no, token_no)
        current = (tuple(self.pos) == cpair)
        marked_sell = (cpair in self.marked and 's' in self.marked[cpair])
        marked_buy = (cpair in self.marked and 'b' in self.marked[cpair])
        marked_rate = (cpair in self.marked and 'r' in self.marked[cpair])

        colour = 4
        if marked_sell: colour = 2
        if marked_buy: colour = 3
        if marked_rate: colour = 7
        if marked_sell and (marked_buy or marked_rate): colour = 6
        if marked_buy and marked_rate: colour = 6
        if current: colour = 1
        ttoken = token
        if marked_sell: ttoken = '{' + ttoken + '}'
        if marked_buy: ttoken = '[' + ttoken + ']'
        if marked_rate: ttoken = '|' + ttoken + '|'

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
    if height >= self.inst_lines and self.show_help:
      line0 = self.progress + " Colours are blue-current green-sell yellow-buy cyan-both"
      line1 = "arrows (move about), n p (next & previous number, via regex)" 
      line2 = "b (mark / unmark []), / \\ (next & previous file), q (quit), h (help)"
      self.window.addstr(0, 0, "{:<80}".format(line0), curses.color_pair(5))
      self.window.addstr(1, 0, "{:<80}".format(line1), curses.color_pair(5))
      self.window.addstr(2, 0, "{:<80}".format(line2), curses.color_pair(5))

    # Shift the top up if necessary
    if self.top > self.pos[0]:
      self.top = self.pos[0]
    # Do dry runs, shifting top down until the position is visible
    while not self.do_contents(height, width, True):
      self.top += 1

    # Next, draw contents
    self.do_contents(height, width)
    self.window.refresh()

def annotate(window, filenames):
  out_filename = "files_still_to_do"
  overwrite = False
  for i in range(len(sys.argv)):
    if sys.argv[i] == '-log' and len(sys.argv) > i + 1:
      out_filename = sys.argv[i + 1]
    if sys.argv[i] == '-overwrite':
      overwrite = True
  out = open(out_filename, "w")

  # Set colour combinations
  curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
  curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
  curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.curs_set(0) # No blinking cursor

  cfilename = 0
  data = read_file(filenames[cfilename])

  ctoken = [0, 0]
  marked = {}
  view = View(window, ctoken, marked, data, cfilename, len(filenames))
  number_regex = re.compile('^[,0-9k]*[.]?[0-9][,0-9k]*[.]?[,0-9k]*$')
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
    elif c == curses.KEY_SLEFT:
      ctoken[1] = 0
    elif c == curses.KEY_RIGHT:
      ctoken[1] += 1
      if ctoken[1] >= len(data[ctoken[0]]):
        nline = ctoken[0] + 1
        while nline < len(data) and len(data[nline]) == 0:
          nline += 1
        if nline < len(data):
          ctoken[0] = nline
          ctoken[1] = 0
        else:
          ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == curses.KEY_SRIGHT:
      ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == curses.KEY_UP:
      if ctoken[0] > 0:
        nline = ctoken[0] - 1
        while nline >= 0 and len(data[nline]) == 0:
          nline -= 1
        if nline >= 0:
          ctoken[0] = nline
          if ctoken[1] >= len(data[ctoken[0]]):
            ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == 337:
      for line_no in range(len(data)):
        if len(data[line_no]) > 0:
          ctoken[0] = line_no
          if ctoken[1] >= len(data[ctoken[0]]):
            ctoken[1] = len(data[ctoken[0]]) - 1
          break
    elif c == curses.KEY_DOWN:
      if ctoken[0] < len(data) - 1:
        nline = ctoken[0] + 1
        while nline < len(data) and len(data[nline]) == 0:
          nline += 1
        if nline < len(data):
          ctoken[0] = nline
          if ctoken[1] >= len(data[ctoken[0]]):
            ctoken[1] = len(data[ctoken[0]]) - 1
    elif c == 336: # Worked out on a Mac by hand...
      for line_no in range(len(data) -1, -1, -1):
        if len(data[line_no]) > 0:
          ctoken[0] = line_no
          if ctoken[1] >= len(data[ctoken[0]]):
            ctoken[1] = len(data[ctoken[0]]) - 1
          break
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
            break
        if done:
          break
    elif c == ord("h"):
      view.show_help = not view.show_help
    elif c == ord("p"):
      # Find next position, use regex
      for line_no in range(ctoken[0], -1, -1):
        done = False
        for token_no in range(len(data[line_no]) - 1, -1, -1):
          if line_no == ctoken[0] and token_no >= ctoken[1]:
            continue
          if number_regex.match(data[line_no][token_no]):
            done = True
            ctoken[0] = line_no
            ctoken[1] = token_no
            break
        if done:
          break
    elif c in [ord('s'), ord('b'), ord('r')]:
      symbol = chr(c)
      if (ctoken[0], ctoken[1]) not in marked:
        marked[ctoken[0], ctoken[1]] = {symbol}
      elif symbol not in marked[ctoken[0], ctoken[1]]:
        marked[ctoken[0], ctoken[1]].add(symbol)
      elif len(marked[ctoken[0], ctoken[1]]) == 1:
        marked.pop((ctoken[0], ctoken[1]))
      else:
        marked[ctoken[0], ctoken[1]].remove(symbol)
    elif c == ord("u"):
      if (ctoken[0], ctoken[1]) in marked:
        marked.pop((ctoken[0], ctoken[1]))
    elif c == ord("/"):
      # write out
      write_file(filenames[cfilename], data, marked, overwrite)
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
    elif c == ord("\\"):
      # write out
      write_file(filenames[cfilename], data, marked, overwrite)
      # get previous
      if cfilename > 0:
        cfilename -= 1
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
  print("Usage:\n{} <file with a list of files to annotate>\nOptions:".format(sys.argv[0]))
  print("  -log <filename>, default = 'files_still_to_do']")
  print("  -overwrite t/f, default = false (will save annotations to a new file)")
  print("\nFor example:")
  print(">> find . | grep 'tok$' > filenames_todo")
  print(">> {} filenames_todo -log do_later\n... do some work, then quit, go away, come back...".format(sys.argv[0]))
  print(">> {} do_later -log do_even_later\n".format(sys.argv[0]))
  sys.exit(1)

### Read filename info
if len(glob.glob(sys.argv[1])) == 0:
  print("Cannot open / find '{}'".format(sys.argv[1]))
  sys.exit(1)
filenames = [line.strip() for line in open(sys.argv[1]).readlines()]
failed = False
for filename in filenames:
  if len(glob.glob(filename)) == 0:
    print("Cannot open / find '{}' from the filenames list".format(filename))
    failed = True
if failed:
  sys.exit(1)

### Start interface
curses.wrapper(annotate, filenames)

