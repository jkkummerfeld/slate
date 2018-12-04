## Why use this tool?

- Fast
- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Works in constrained environments (e.g. only allowed ssh access to a machine)
- Easily configurable and modifiable

## Installation

Simply clone or download this repository.
The code requires just Python 3 and can be run out of the box.

Step by step, in a terminal, you can either download a zip file:

```bash
wget -O slate.zip https://github.com/jkkummerfeld/slate/archive/master.zip
unzip slate.zip
cd slate-master
```

Or clone the repository:

```bash
git clone https://github.com/jkkummerfeld/slate
cd slate
```

## Tutorials:

These tutorials are independent

Task | Command
---- | --------
Annotating labels for spans of text in a document | `python3 src/annotate.py example/label-example.md -hh --ann-type categorical --ann-scope token --overwrite`
Annotating links in a document | `python3 src/annotate.py example/link-example.md -hh --ann-type link --ann-scope line --overwrite`

## Usage:

You will be shown files one at a time in plain text. Commands are:

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

To annotate multiple files, specify more than one as an argument.
For greater control, provide a list of files in a file specified with `--data-list`.
The list should be formatted as follows, where [] indicate optional values:

```
raw_file [annotation_file [starting_position [additional_annotation_files]]]
```

For example, these commands will create a file list, use it, then return to it later:

```bash
$ find . | grep 'txt$' > filenames_todo
$ ./slate/src/annotate.py --data-list filenames_todo --log-prefix do_later
... do some work, then quit, go away, come back...
$ ./slate/src/annotate.py --data-list dp_later.todo --log-prefix do_even_later
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

