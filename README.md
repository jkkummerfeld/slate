# SLATE, a Super-Lightweight Annotation Tool for Experts

A lightweight text annotation tool for use in a terminal

# Usage:

```sh
./annotation_tool.py <file with a list of files to annotate>
```

The file should contain one filename per line.
If you wish, there can also be two numbers after each filename, indicating the line and token on which to start annotating.

You will be shown files one at a time in plain text. Commands for are:

Type                 | Key                     | Labelling Affect                 | Linking Affect
-------------------- | ----------------------- | -------------------------------- | ---------------------
Movement             | left arrow              | move to previous word            | move antecedent to previous word
.                    | left arrow + shift      | go to first word in line         | move to previous word
.                    | right arrow             | move to next word                | move antecedent to next word
.                    | right arrow + shift     | go to last word in line          | move to next word
.                    | up arrow                | move up a line                   | move antecedent up a line
.                    | c or up arrow + shift   | go to first line                 | move up a line
.                    | down arrow              | move down a line                 | move antecedent down a line
.                    | v or down arrow + shift | go to last line                  | move down a line
.                    | /                       | -                                | start typing a search term
.                    | n or P                  | -                                | move to next search match
.                    | p or N                  | -                                | move to previous search match
Annotation           | r                       | [un]mark this token as ||        | -
.                    | s                       | [un]mark this token as {}        | -
.                    | b                       | [un]mark this token as []        | -
.                    | d                       | -                                | create a link and move down / right
.                    | D                       | -                                | create a link
.                    | u                       | undo annotation on this token    | undo all annotations for the current item
Saving, exiting, etc | .                       | save and go to next file         | same
.                    | ,                       | save and go to previous file     | same
.                    | q                       | quit                             | same
.                    | h                       | toggle help info (default on)    | same

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

 - `-log <filename>`, default = `files_still_to_do`
 - `-overwrite [tf]`, default = false (annotations for a file will be saved in `<filename>.annotated`)

# Config file format

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

# What makes this tool good?

- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Fast
- Works in constrained environments (e.g. only allowed ssh access to a machine)
- (eventually) easily configurable

# Notes on design choices


# TODO:

Experiments:
- 'Think aloud' user study
- Compare setup time with other tools for new users

Features:
- Rather than highlighting text, use columns on the left (block of colour), for line mode at least. Not sure about tokens
- Add a calibration mode, where people type keys so I can figure out what they mean (and they could customise things).
- Enable different scales of annotation (e.g. multiword span, or an entire sentence). Have sclaes (character, token, line, sentence, paragraph), types (item, span), labels (categories, free text, directed link, undirected link, set)
- Allow multiple annotations of the same file at the same time
- Space between token and label
- For blank lines, print only one in a row
- Variable location of instructions
- Adjustable keybinding
- Allow default key assignment to include 0
- Make special keys customisable
- Allow multi-key labels
- Allow auto-search over labels (i.e. user types characters and we search over labels to get the right one as they type)
- Allow definition of keys to jump to next match on a regex or even a simple string
- Add the option to read in the raw data when going back to a seen file
- Option to load all at start
- Option to only save on exit (not when changing files)
- Have instructions be a set of pieces that are adaptively arranged
- Constrain annotations, e.g. a flag to not allow links to point in one direction
- Option to specify file names on the command line
- Modes: editing annotations, comparing annotations (and resolving disagreements?)
- Write scripts to take standoff and create inline data (don't add inline as an output)
- Add logging of all edits to a file, so a crash can be recoverd from easily.
- Allow different default when resolving disagreements (rather than the union, only have those with agreement, or a majority). Note, this is subtle, as it interacts with the way colouring works.
- Ability to colour linked items as they are created (to see the history). Either always showing all using different colours, or showing what the cursor is linked to.
- Shortcut to jump to just before the link line
- Option to not allow annotation of some files (and not create a file)
- When the movement key is pressed multiple times in a row quickly, start jumping further [optional], or have a fast jump key?
- Look into the LAF format for data input / output
- Show the set of available labels
- Specify every chunk must be labeled, or only some
- Move view independently of cursor

Internal:
- What happens if we hit a word wider than the window?
- At the moment spacing is being lost (e.g. intentional multiple spaces)
- More intelligent calculation of view position (avoid dry runs)
- Nicer argument, error, and logging handling
- Don't re-render if there is no change to the view
- Start the link line after the cursor and don't allow them to overlap
- Saving both cursor and link for linking mode (in todo file) and reading similarly
- Work out how to get brighter colours (cf vim)
- Improve speed of jumping back down
- For help, compose it out of a set of items, with line breaks changing when the screen is narrow
