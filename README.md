# SLATE, a Super-Lightweight Annotation Tool for Experts

A terminal-based text annotation tool written in Python.

## Why use this tool?

- Fast
- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Works in constrained environments (e.g. only allowed ssh access to a machine)
- Easily configurable and modifiable

# Usage:

These two simple tutorials explain how to use the tool for annotating labels or links:

```bash
python3 src/annotate.py example/label-example.md -hh --ann-type categorical --ann-scope token --overwrite

python3 src/annotate.py example/link-example.md -hh --ann-type link --ann-scope line --overwrite
```

To run with a set of 

Below is a complete list of commands for the two main modes.
The file should contain one filename per line.
If you wish, there can also be two numbers after each filename, indicating the line and token on which to start annotating.

You will be shown files one at a time in plain text. Commands for are:

Type                 | Key                         | Labelling Affect                 | Linking Affect
-------------------- | --------------------------- | -------------------------------- | ---------------------
Movement             | `j` or `LEFT`               | move to the left                 | move antecedent to previous word
                     | `i` or `UP`                 | move up a line                   | move antecedent up a line
                     | `o` or `DOWN`               | move down a line                 | move antecedent down a line
                     | `;` or `RIGHT`              | move to next word                | move antecedent to next word
                     | `SHIFT` + [`j` of `LEFT`]   | go to the start of the line      | move to previous word
                     | `SHIFT` + [`;` of `RIGHT`]  | go to last word in line          | move to next word
                     | c or up arrow + shift       | go to first line                 | move up a line
                     | v or down arrow + shift     | go to last line                  | move down a line
                     | /                           | -                                | start typing a search term
                     | n or P                      | -                                | move to next search match
                     | p or N                      | -                                | move to previous search match
Annotation           | `z`                         | [un]mark this token as z         | -
.                    | `x`                         | [un]mark this token as x         | -
.                    | `c`                         | [un]mark this token as c         | -
.                    | `d`                         | -                                | create a link and move down / right
.                    | `SHIFT` + `d`               | -                                | create a link
.                    | `u`                         | undo annotation on this token    | undo all annotations for the current item
Saving, exiting, etc | .                           | save and go to next file         | same
.                    | ,                           | save and go to previous file     | same
.                    | q                           | quit                             | same
.                    | h                           | toggle help info (default on)    | same

Note, when moving to the next or previous file, the current state is saved.
If annotations are being saved without overwriting raw data then the annotated version will be read in.
For example, if a file is annotated, then '/\' is typed, the file will be showing again with the new annotations.


Tokens are coloured as follows:

 - Blue on white, current token under consideration
 - Green on black, {} tokens
 - Yellow on black, [] tokens
 - Purple on black, || tokens
 - Cyan on black, multiple types for a single token

The tokens are also modified to show the annotations.

If a file is too long to display on a single screen, moving off the top or
bottom will cause redrawing so that the current token is always visible.

# Options:

TODO: Update

 - `-log <filename>`, default = `files_still_to_do`
 - `-overwrite [tf]`, default = false (annotations for a file will be saved in `<filename>.annotated`)

# Config file format

TODO: Update

A series of lines, each containing ([] are optional):

 - label, the string that is assigned
 - [key], the single key to press to make that annotation, default is to
 	 number from one upwards (only nine allowed).
 - [start symbol], the text that will be added before the token
 - [end symbol], the text that will be added after the token
 - [color], not implemented yet.

# Example:

```
>> find . | grep 'tok$' > filenames_todo
>> ./annotation_tool.py filenames_todo -log do_later
... do some work, then quit, go away, come back...
>> ./annotation_tool.py do_later -log do_even_later
```

# Notes on design choices

# TODO:

This week:
- Splash page of help rather than at the bottom
- Quit without saving
- Nicer examples
- Tutorials on each mode
- Legend/key giving keys and their labels + colors

Future improvements:
- Rather than highlighting text, use columns on the left (block of colour), for line mode at least. Not sure about tokens
- Add a calibration mode, where people type keys so I can figure out what they mean (and they could customise things).
- Add the ability to jump to the start/end of a paragraph (and expand / contract similarly)
- Allow multiple annotations of the same file at the same time
- For blank lines, option to print only one in a row
- Variable location of instructions
- Allow default key assignment to include 0
- Allow multi-key labels
- Allow auto-search over labels (i.e. user types characters and we search over labels to get the right one as they type)
- Allow definition of keys to jump to next match on a regex or even a simple string
- Add the option to read in the raw data when going back to a seen file
- Option to load all at start
- Option to only save on exit (not when changing files)
- Constrain annotations, e.g. a flag to not allow links to point in one direction
- Option to specify file names on the command line
- Make link vs. category vs. text changeable during annotation
- Write scripts to take standoff and create inline data (don't add inline as an output)
- Support undo to reverse actions
- Add logging of all edits to a file, so a crash can be recoverd from easily.
- Allow different default when resolving disagreements (rather than the union, only have those with agreement, or a majority). Note, this is subtle, as it interacts with the way colouring works.
- Ability to colour linked items as they are created (to see the history). Either always showing all using different colours, or showing what the cursor is linked to.
- Shortcut to jump to just before the link line
- Option to not allow annotation of some files (and not create a file)
- When the movement key is pressed multiple times in a row quickly, start jumping further [optional], or have a fast jump key?
- Look into the LAF format for data input / output
- Show the set of available labels
- Specify every chunk must be labeled, or only some
- Be able to annotate with errors (creating new errors along the way) and then sort by label
- Handling clusters (make the set visible)
- Nicer argument, error, and logging handling
- Look into Pythonista to make an iOS version
- Option to have jumping retain the span's size (at the moment it becomes a single item again)

Internal:
- Bug: Long text labels will cause a crash (if they span more than the width)
- Bug? More than one space in a row becomes one
- More intelligent calculation of view position (avoid dry runs)
- Saving both cursor and link for linking mode (in todo file) and reading similarly
- Improve speed of jumping back down
- For help, compose it out of a set of items, with line breaks changing when the screen is narrow

