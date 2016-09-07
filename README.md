# annotation-terminal-tool

A lightweight text annotation tool for use in a terminal

# Usage:

`./annotation_tool.py <file with a list of files to annotate>`

You will be shown files one at a time in plain text. Commands are:

 - left arrow   - move to previous word (+shift, go to first)
 - right arrow  - move to next word (+shift, go to last)
 - up arrow     - move up a line (+shift, go to top)
 - down arrow   - move down a line (+shift, go to bottom)
 - n            - move to next numerical value
 - p            - move to previous numerical value
 - r            - mark this token as ||
 - s            - mark this token as {}
 - b            - mark this token as []
 - /  \         - save and go to next or previous file
 - u, b, s, r   - undo annotation on this token
 - q            - quit
 - h            - toggle help info (default on)

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

# Example:

```
>> find . | grep 'tok$' > filenames_todo
>> ./annotation_tool.py filenames_todo -log do_later
... do some work, then quit, go away, come back...
>> ./annotation_tool.py do_later -log do_even_later
```

# TODO:

 - Bug: Going backwards to files just annotated will either (1) show files without any annotations and overwrite the existing annotations, when creating <filename>.annotated files, (2) not allow existing annotations to be removed
 - Feature: Option to output to standoff annotations instead
 - Feature: Adjustable keybinding
