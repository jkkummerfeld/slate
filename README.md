# SLATE, a Super-Lightweight Annotation Tool for Experts

A terminal-based text annotation tool written in Python.

## Why use this tool?

- Fast
- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Works in constrained environments (e.g. only allowed ssh access to a machine)
- Easily configurable and modifiable

## Usage:

These two simple tutorials explain how to use the tool for annotating labels or links:

```bash
python3 src/annotate.py example/label-example.md -hh --ann-type categorical --ann-scope token --overwrite

python3 src/annotate.py example/link-example.md -hh --ann-type link --ann-scope line --overwrite
```

You will be shown files one at a time in plain text. Commands for are:

Type                        | Key                         | Labelling Affect                 | Linking Affect
--------------------------- | --------------------------- | -------------------------------- | ---------------------
Movement                    | `j` or `LEFT`               | move to the left                 | move selected item to the left
"                           | `SHIFT` + [`j` or `LEFT`]   | go to the start of the line      | move linking item to the left
"                           | `i` or `UP`                 | move up a line                   | move selected item up a line
"                           | `SHIFT` + [`i` or `UP`]     | go to first line                 | move linking item up a line
"                           | `o` or `DOWN`               | move down a line                 | move selected item down a line
"                           | `SHIFT` + [`o` or `DWON`]   | go to last line                  | move linking item down a line
"                           | `;` or `RIGHT`              | move to the right                | move selected item to the right
"                           | `SHIFT` + [`;` or `RIGHT`]  | go to the end of the line        | move linking item to the right
Edit Span                   | `m`                         | extend left                      | -
"                           | `SHIFT` + `m`               | contract left side               | -
"                           | `k`                         | extend up                        | -
"                           | `SHIFT` + `k`               | contract top                     | -
"                           | `l`                         | extend down                      | -
"                           | `SHIFT` + `l`               | contract bottom                  | -
"                           | `/`                         | extend right                     | -
"                           | `SHIFT` + `/`               | contract right side              | -
Label Annotation (default)  | `z`                         | [un]mark this item as z          | -
"                           | `x`                         | [un]mark this item as x          | -
"                           | `c`                         | [un]mark this item as c          | -
Link Annotation             | `d`                         | -                                | create a link and move down / right
"                           | `SHIFT` + `d`               | -                                | create a link
Either Annotation mode      | `u`                         | undo annotation on this item     | undo all annotations for the current item
Saving, exiting, etc        | `]`                         | save and go to next file         | same
"                           | `[`                         | save and go to previous file     | same
"                           | `q`                         | quit                             | same
"                           | `h`                         | toggle help info (default on)    | same

To annotate multiple files, specify more than one as an argument. For greater control, provide a list of files in a file specified with `--data-list`. The list should be formatted as follows:

```
raw_file [annotation_file [starting_position [other_annotations]]]
```

## Colours

Colours and keys are customisable. For labelling, the default is:

 - Underlined, current selected item
 - Green on black, 'z' items
 - Yellow on black, 'x' items
 - Purple on black, 'c' items
 - Cyan on black, multiple types for a single token

For linking, the default is:

 - Underlined, current selected item
 - Green on black, current linking item
 - Blue on black, item is linked to the current linking item
 - Yellow on black, item is in some link, though not with the current linking item

## Options:

This is directly from running `./annotate.py -h`:

```
positional arguments:
  data                  Files to be annotated

optional arguments:
  -h, --help            show this help message and exit
  --data-list DATA_LIST [DATA_LIST ...]
                        Files containing lists of files to be annotated
  --log-prefix LOG_PREFIX
                        Prefix for logging files (otherwise none)
  --readonly READONLY   Do not allow changes or save annotations.
  -hh, --hide-help      Do not show help on startup.
  --overwrite           If they exist already, overwrite output files.
  --do-not-show-linked  Do not have a special color to indicate any linked
                        token.
  --prevent-self-links  Prevent an item to be linked to itself.
  --prevent-forward-links
                        Prevent a link from an item to one after it.
  --alternate-comparisons
                        Activate alternative way of showing different
                        annotations (one colour per set of markings, rather
                        than counts).
  --ann-type {categorical,link}
                        The type of annotation being done.
  --ann-scope {character,token,line,document}
                        The scope of annotation being done.
  --config-file CONFIG_FILE
                        A file containing configuration information.
```

## Config file format

TODO: Update

A series of lines, each containing ([] are optional):

 - label, the string that is assigned
 - [key], the single key to press to make that annotation, default is to
 	 number from one upwards (only nine allowed).
 - [start symbol], the text that will be added before the token
 - [end symbol], the text that will be added after the token
 - [color], not implemented yet.

## Notes on design choices

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

