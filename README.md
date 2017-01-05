# annotation-terminal-tool

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
                     | left arrow + shift      | go to first word in line         | move to previous word
                     | right arrow             | move to next word                | move antecedent to next word
                     | right arrow + shift     | go to last word in line          | move to next word
                     | up arrow                | move up a line                   | move antecedent up a line
                     | c or up arrow + shift   | go to first line                 | move up a line
                     | down arrow              | move down a line                 | move antecedent down a line
                     | v or down arrow + shift | go to last line                  | move down a line
                     | n                       | move to next numerical value     | -
                     | p                       | move to previous numerical value | -
Annotation           | r                       | [un]mark this token as ||        | -
                     | s                       | [un]mark this token as {}        | -
                     | b                       | [un]mark this token as []        | -
                     | d                       | -                                | create a link and move down / right
                     | D                       | -                                | create a link
                     | u                       | undo annotation on this token    | undo all annotations for the current item
Saving, exiting, etc | /                       | save and go to next file         | same
                     | \                       | save and go to previous file     | same
                     | q                       | quit                             | same
                     | h                       | toggle help info (default on)    | same

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

# TODO:

Features:
 - Enable different scales of annotation (e.g. multiword span, or an entire sentence)
 - Enable linking items rather than labeling them (and labeled links)
 - Space between token and label
 - For blank lines, print only one in a row
 - Variable location of instructions
 - Option to output to standoff annotations instead
 - Adjustable keybinding
 - Allow default key assignment to include 0
 - Make special keys customisable
 - Allow multi-key labels
 - Allow auto-search over labels (i.e. user types characters and we search over labels to get the right one as they type)
 - Allow definition of keys to jump to next match on a regex
 - Add the option to read in the raw data when going back to a seen file
 - Option to load all at start
 - Option to only save on exit (not when changing files)
 - Have instructions be a set of pieces that are adaptively arranged
 - Constrain annotations, e.g. a flag to not allow links to point in one direction
 - Allow storage of information about the last time editing, so we can pick up at the same position

Internal:
 - More intelligent calculation of view position (avoid dry runs)
 - Nicer argument, error, and logging handling
