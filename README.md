## Why use this tool?

- Fast
- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Works in constrained environments (e.g. only allowed ssh access to a machine)
- Easily configurable and modifiable

## Installation

Simply clone or download this repository.
The code requires only Python (2 or 3) and can be run out of the box.

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

## Tutorials

Included in this repository are a set of interactive tutorials that teach you how to use the tool from within the tool itself.

Task | Command
---- | --------
Labelling spans of text in a document | `python src/annotate.py tutorial/label.md -t categorical -s token -o -hh -l log.tutorial.label.txt`
Linking lines in a document | `python src/annotate.py tutorial/link.md -t link -s line -o -hh -l log.tutorial.link.txt`
Comparing annotations | Coming soon!

## Detailed Usage Instructions

Run as:

```
python src/annotate.py [-h] [-d DATA_LIST [DATA_LIST ...]] [-l LOG_PREFIX] [-r]
                        [-hh] [-o] [-t {categorical,link}]
                        [-s {character,token,line,document}] [-c CONFIG_FILE] [-ps]
                        [-pf] [--do-not-show-linked] [--alternate-comparisons]
                        [data [data ...]]

positional arguments:
  data                  Files to be annotated

optional arguments:
  -h, --help            show this help message and exit
  -d DATA_LIST [DATA_LIST ...], --data-list DATA_LIST [DATA_LIST ...]
                        Files containing lists of files to be annotated
  -t {categorical,link}, --ann-type {categorical,link}
                        The type of annotation being done.
  -s {character,token,line,document}, --ann-scope {character,token,line,document}
                        The scope of annotation being done.
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        A file containing configuration information.
  -l LOG_PREFIX, --log-prefix LOG_PREFIX
                        Prefix for logging files (otherwise none)
  -hh, --hide-help      Do not show help on startup.
  -r, --readonly        Do not allow changes or save annotations.
  -o, --overwrite       If they exist already, read and overwrite output
                        files.
  -ps, --prevent-self-links
                        Prevent an item from being linked to itself.
  -pf, --prevent-forward-links
                        Prevent a link from an item to one after it.
  --do-not-show-linked  Do not have a special color to indicate any linked
                        token.
  --alternate-comparisons
                        Activate alternative way of showing different
                        annotations (one colour per set of markings, rather
                        than counts).
```

You may also define arguments in a file and pass them in as follows:

```bash
python src/annotate.py @arguments.txt
```

The tool shows files one at a time in plain text. Commands are:

Type                        | Key                         | Labelling Affect                 | Linking Affect
--------------------------- | --------------------------- | -------------------------------- | ---------------------
Movement                    | `j` or `LEFT`               | move to the left                 | move selected item to the left
&nbsp;                      | `i` or `UP`                 | move up a line                   | move selected item up a line
&nbsp;                      | `o` or `DOWN`               | move down a line                 | move selected item down a line
&nbsp;                      | `;` or `RIGHT`              | move to the right                | move selected item to the right
&nbsp;                      | `J` or [`SHIFT` + `LEFT`]   | go to the start of the line      | move linking item to the left
&nbsp;                      | `I` or [`SHIFT` + `UP`]     | go to first line                 | move linking item up a line
&nbsp;                      | `O` or [`SHIFT` + `DWON`]   | go to last line                  | move linking item down a line
&nbsp;                      | `:` or [`SHIFT` + `RIGHT`]  | go to the end of the line        | move linking item to the right
Edit Span                   | `m`                         | extend left                      | extend selected item left
&nbsp;                      | `k`                         | contract left side               | contract selected item left
&nbsp;                      | `/`                         | extend right                     | extend selected item right
&nbsp;                      | `l`                         | contract right side              | contract selected item right
&nbsp;                      | `M`                         | -                                | extend linking item left
&nbsp;                      | `K`                         | -                                | contract linking item left
&nbsp;                      | `?`                         | -                                | extend linking item right
&nbsp;                      | `L`                         | -                                | contract linking item right
Label Annotation (default)  | `SPACE` then `a`            | [un]mark this item as a          | -
&nbsp;                      | `SPACE` then `s`            | [un]mark this item as s          | -
&nbsp;                      | `SPACE` then `d`            | [un]mark this item as d          | -
&nbsp;                      | `SPACE` then `v`            | [un]mark this item as v          | -
Link Annotation             | `d`                         | -                                | create a link and move right / down
&nbsp;                      | `D`                         | -                                | create a link
Either Annotation mode      | `u`                         | undo annotation on this item     | undo all annotations for the current item

Shared commands:

Type                        | Mode   | Key                           | Affect               
--------------------------- | ------ | ----------------------------- | ----------------------------
Searching                   | Normal | `\`                           | enter query editing mode
&nbsp;                      | Query  | `?` or `ENTER`                | exit query editing mode
&nbsp;                      | Query  | `!` or `BACKSPACE`            | delete last character in query
&nbsp;                      | Query  | characters except `?` and `!` | add character to query
&nbsp;                      | Normal | `p`                           | go to previous match
&nbsp;                      | Normal | `n`                           | go to next match
&nbsp;                      | Normal | `P`                           | go to previous match for linking line
&nbsp;                      | Normal | `N`                           | go to next match for linking line
Assigning text labels       | Normal | `t`                           | enter label editing mode
&nbsp;                      | Label  | `?` or `ENTER`                | exit label editing mode and assign the label
&nbsp;                      | Label  | `!` or `BACKSPACE`            | delete last character in label
&nbsp;                      | Label  | characters except `?` and `!` | add character to label
Saving, exiting, etc        | Normal | `]`                           | save and go to next file         
&nbsp;                      | Normal | `[`                           | save and go to previous file     
&nbsp;                      | Normal | `q`                           | save and quit                    
&nbsp;                      | Normal | `s`                           | save                             
&nbsp;                      | Normal | `Q`                           | quit                             
Misc                        | Normal | `#`                           | toggle line numbers
&nbsp;                      | Normal | `h`                           | toggle help info (default on)    
&nbsp;                      | Normal | `{` or `PAGE-UP`              | shift view up 5 lines
&nbsp;                      | Normal | `}` or `PAGE-DOWN`            | shift view down 5 lines
&nbsp;                      | Normal | `>` then `p`                  | toggle showing progress through files
&nbsp;                      | Normal | `>` then `l`                  | toggle showing legend for labels [TODO]

Note: special keys such as `ENTER` and `BACKSPACE` may not work on non-OSX operating systems. That is why in all places where they are used we have an alternative as well.

To annotate multiple files, specify more than one as an argument.
For greater control, provide a list of files in a file specified with `--data-list`.
The list should be formatted as follows, where [] indicate optional values:

```
raw_file [annotation_file [starting_position [additional_annotation_files]]]
```

For example, these commands will create a file list, use it, then return to it later:

```bash
$ find . -name *txt > filenames_todo
$ ./slate/src/annotate.py -d filenames_todo -l do_later
... do some work, then quit, go away, come back...
$ ./slate/src/annotate.py -d do_later.todo -l do_even_later
```

## Customisation

Colours and keys are customisable. For labelling, the default is:

 - Underlined, current selected item
 - Green on black, 'a' items
 - Blue on black, 's' items
 - Magenta on black, 'd' items
 - Red on black, 'v' items
 - Cyan on black, multiple types for a single token

For linking, the default is:

 - Underlined, current selected item
 - Green on black, current linking item
 - Blue on black, item is linked to the current linking item
 - Yellow on black, item is in some link, though not with the current linking item


