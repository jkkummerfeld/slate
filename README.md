## Why use this tool?

- Fast
- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Terminal based, so it works in constrained environments (e.g. only allowed ssh access to a machine)
- Not difficult to configurable and modifiable

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

Your terminal must be at least 80 characters wide and 20 tall to use the tool.

## Getting Started

Run `python src/annotate.py <filename>` to start annotating `<filename>` with labels over spans of tokens.
The entire interface is contained in your terminal, there is no GUI.
With command line arguments you can vary properties such as the type of annotation (labels or links) and scope of annotation (characters, tokens, lines, documents).

The input file should be plain text, organised however you like.
Prepare the data with your favourite sentence splitting and/or tokenisation software (e.g., [SpaCy](https://spacy.io)).
If you use Python 3 then unicode should be supported, but the code has not been tested extensively with non-English text (please share any issues!).

When you start the tool it displays a set of core commands by default.
These are also specified below, along with additional commands.

The tool saves annotations in a separate file (`<filename>.annotations` by default, this can be varied with a file list as described below).
Annotation files are formatted with one line per annotated item.
The item is specified with a tuple of numbers.
For labels, the item is followed by a hyphen and the list of labels.
For links, there are two items on the line before the hyphen.
For example, these are two annotation files, one for labels of token spans and the other for links between lines:

```
==> label.annotations <==
(2, 1) - label:a
((3, 5), (3, 8)) - label:a
(7, 8) - label:s label:a

==> link.annotations <==
13 0 - 
13 7 - 
16 7 - 
```

A few notes:
- The second label annotation is on a span of tokens, going from 5 to 8 on line 3.
- The third label annotation has two labels.
- The line annotations only have one number to specify the item.
- When the same line is linked to multiple other lines, each link is a separate item.

### Tutorials

Included in this repository are a set of interactive tutorials that teach you how to use the tool from within the tool itself.

Task | Command
---- | --------
Labelling spans of text in a document | `python src/annotate.py tutorial/label.md -t categorical -s token -o -hh -l log.tutorial.label.txt`
Linking lines in a document | `python src/annotate.py tutorial/link.md -t link -s line -o -hh -l log.tutorial.link.txt`
Comparing annotations | Coming soon!

### Example Workflow

This tool has already been used for two annotation efforts involving multiple annotators ([Durrett et al., 2017](http://jkk.name/publication/emnlp17forums/) and [Kummerfeld et al., 2018](http://jkk.name/publication/arxiv18disentangle/)).
Our workflow was as follows:

- Create a repository containing (1) the annotation guide, (2) the data to be annotated divided into user-specific folders.
- Each annotator downloaded slate and used it to do their annotations and commit the files to the repository.
- Either the whole group or the project leader went through files that were annotated by multiple people, using the adjudication mode in the tool.

## Detailed Usage Instructions

### Invocation options

```
usage: annotate.py [-h] [-d DATA_LIST [DATA_LIST ...]] [-t {categorical,link}]
                   [-s {character,token,line,document}] [-c CONFIG_FILE]
                   [-l LOG_PREFIX] [-ld] [-hh] [-r] [-o] [-ps] [-pf]
                   [--do-not-show-linked] [--alternate-comparisons]
                   [data [data ...]]

A tool for annotating text data.

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
                        Prefix for logging files
  -ld, --log-debug      Provide detailed logging.
  -hh, --hide-help      Do not show help on startup.
  -r, --readonly        Do not allow changes or save annotations.
  -o, --overwrite       If they exist already, read abd overwrite output
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

### Keybindings

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

### Misc

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

When the `additional_annotation_files` are included it activates an adjudication mode.
By default, all annotations that appear in all additional files are added to the current annotations.
Disagreements are coloured in the text, but will disappear once a decision is made (using the normal annotation commands).

Note - adjudication has not been as thoroughly tested.
Please share any issues you come across!

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

### Modifying the Code

Slate has a relatively small codebase (~2,200 lines) and is designed to make adding new functionality not too hard.
The code is divided up as follows:

 - `annotate.py`, the main program, this has the core loop that gets user input.
 - `config.py`, contains the default configuration, including colours and keyboard bindings.
 - `data.py`, classes to read, store and write data.
 - `view.py`, rendering the screen.

Logic for determining what colour goes where is split across two parts of the code.
In `data.py`, the set of labels for an item is determined.
In `view.py`, that set of labels is used to choose a suitable colour.

Adding a new command involves:

 - Adding the name and key to `input_action_list` in `config.py`
 - Adding a mapping from the name to a function in `action_to_function` in `annotate.py`
 - Adding or modifying a function in `annotate.py`
 - Modifying `data.py` or `view.py` to apply the action

