This is a tool for labeling text documents.
Slate supports annotation at different scales (spans of characters, tokens, and lines, or a document) and of different types (free text, labels, and links).
This covers a range of tasks, such as Part-of-Speech tagging, Named Entity Recognition, Text Classification (including Sentiment Analysis), Discourse Structure, and more.

Why use this tool over the range of other text annotation tools out there?

- Fast
- Trivial installation
- Focuses all of the screen space on annotation (good for large fonts)
- Terminal based, so it works in constrained environments (e.g. only allowed ssh access to a machine)
- Not difficult to configure and modify

Note - this repository is **not** for the "Segment and Link-based Annotation Tool, Enhanced", which can be found [here](https://bitbucket.org/dainkaplan/slate/wiki/Home) and was first presented at [LREC 2010](http://www.lrec-conf.org/proceedings/lrec2010/pdf/129_Paper.pdf).
See 'Citing' below for additional notes on that work.

## Installation

Two options:

### 1. Install with pip
```bash
pip install slate-nlp
```

Then run from any directory in one of two ways:
```
slate
python -m slate
```

### 2. Or download and run without installing
Either download as a zip file:
```bash
curl https://codeload.github.com/jkkummerfeld/slate/zip/master -o "slate.zip"
unzip slate.zip
cd slate-master
```
Or clone the repository:
```bash
git clone https://github.com/jkkummerfeld/slate
cd slate
```

Then run with either of:
```
python slate.py
./slate.py
```
To run from another directory, use:
```
python PATH_TO_SLATE/slate.py
PATH_TO_SLATE/slate.py
```

### Requirements

The code requires only Python (2 or 3) and can be run out of the box.
Your terminal must be at least 80 characters wide and 20 tall to use the tool.

## Citing

If you use this tool in your work, please cite:

```
@InProceedings{acl19slate,
  title     = {SLATE: A Super-Lightweight Annotation Tool for Experts},
  author    = {Jonathan K. Kummerfeld},
  booktitle = {Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations},
  location  = {Florence, Italy},
  month     = {July},
  year      = {2019},
  pages     = {7--12},
  doi       = {10.18653/v1/P19-3002},
  url       = {https://aclweb.org/anthology/papers/P/P19/P19-3002/},
  software  = {https://jkk.name/slate},
}
```

While presenting this work at ACL I learned of another annotation tool called SLATE.
That tool was first described in "Annotation Process Management Revisited", [Kaplan et al. (LREC 2010)](http://www.lrec-conf.org/proceedings/lrec2010/pdf/129_Paper.pdf) and then in "Slate - A Tool for Creating and Maintaining Annotated Corpora", [Kaplan et al. (JLCL 2011)](https://jlcl.org/content/2-allissues/12-Heft2-2011/11.pdf).
It takes a very different approach, using a web based interface that includes a suite of project management tools as well as annotation.
The code it available at [https://bitbucket.org/dainkaplan/slate/wiki/Home](https://bitbucket.org/dainkaplan/slate/wiki/Home).

## Getting Started

Note: if you used pip to install, reaplce `python slate.py` with `slate` everywhere below.

Run `python slate.py <filename>` to start annotating `<filename>` with labels over spans of tokens.
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
Named Entity Recognition annotation |  `python slate.py tutorial/ner.md -t categorical -s token -o -c ner-book.config -l log.tutorial.ner.txt -sl -sm`
Labelling spans of text in a document | `python slate.py tutorial/label.md -t categorical -s token -o -l log.tutorial.label.txt`
Linking lines in a document | `python slate.py tutorial/link.md -t link -s line -o -l log.tutorial.link.txt`

### Example Workflow

This tool has already been used for two annotation efforts involving multiple annotators ([Durrett et al., 2017](http://jkk.name/publication/emnlp17forums/) and [Kummerfeld et al., 2018](http://jkk.name/publication/arxiv18disentangle/)).
Our workflow was as follows:

- Create a repository containing (1) the annotation guide, (2) the data to be annotated divided into user-specific folders.
- Each annotator downloaded slate and used it to do their annotations and commit the files to the repository.
- Either the whole group or the project leader went through files that were annotated by multiple people, using the adjudication mode in the tool.

### Comparing Annotations

The tool supports displaying annotations for the purpose of adjudicating disagreements.
There are two steps involved.
Specifically, you can request that a set of other annotation files be read.
Then, whenever one of those annotation files includes something that your current adjudication does not, the text is shown in red.

#### Data list file creation
A  data list file contains a series of lines in the format:

```
raw_file [output_file [cur_position [other_annotations]]]
```

For example, this line says there is a raw text file `my-book.txt`, that the adjudications should be saved in `annotations-adjudicated.txt`, that annotation should start at the very start of `my-book.txt` and that there are three existing annotations to be compared:

```
my-book.txt annotations-adjudicated.txt ((0, 0), (0, 0)) my-book.txt.annotations1 my-book.txt.annotations2 my-book.txt.annotations3
```

Note: you can have as many "other_annotation" files as you want.

#### Run slate with the data list file
Now run slate as follows:

```
python slate.py -d data-list-file [any other arguments]
```

#### Example

The tutorial folder contains two example data list files:

- `tutorial/data/list_with_disagreements.category.txt`
- `tutorial/data/list_with_disagreements.link.txt`

You can use them as follows:

```
cd tutorial/data
python ../../slate.py -d list_with_disagreements.category.txt -t categorical -s token
```

#### Efficiency Tip

You can save time by putting annotations that all annotators agreed on into the `annotations-adjudicated.txt` file.
This bash pipeline will do that if you replace:

- `ANNOTATION_FILES` with the names of all of your annotation files, separated by spaces
- `N_FILES` with the number of annotation files you have

```
cat ANNOTATION_FILES | sort | uniq -c | awk -v count=N_FILES '$1 == count' | sed 's/^ *[0-9]* *//' > annotations-adjudicated.txt
```

Breaking this down, it does the following:
- `cat ANNOTATION_FILES `, print the annotation files in the terminal
- `sort `, sort their contents together
- `uniq -c `, where there are consecutive lines that are the same, only keep one, and also indicate how many times each line occurred
- `awk -v count=N_FILES '$1 == count' `, only keep lines where the number at the start matches `N_FILES`
- `sed 's/^ *[0-9]* *//' > annotations-adjudicated.txt`, remove the number at the start of the line (placed there by the `uniq` command)

## Detailed Usage Instructions

### Invocation options

```
usage: slate.py [-h] [-d DATA_LIST [DATA_LIST ...]] [-t {categorical,link}]
                [-s {character,token,line,document}] [-c CONFIG_FILE] [-l LOG_PREFIX] [-ld]
                [-sh] [-sl] [-sp] [-sm] [-r] [-o] [-ps] [-pf] [--do-not-show-linked]
                [--alternate-comparisons]
                [data ...]

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
  -sh, --show-help      Show help on startup.
  -sl, --show-legend    Start with legend showing.
  -sp, --show-progress  Start with progress showing.
  -sm, --show-mark      Start with mark showing.
  -r, --readonly        Do not allow changes or save annotations.
  -o, --overwrite       If they exist already, read and overwrite output files.
  -ps, --prevent-self-links
                        Prevent an item from being linked to itself.
  -pf, --prevent-forward-links
                        Prevent a link from an item to one after it.
  --do-not-show-linked  Do not have a special color to indicate any linked token.
  --alternate-comparisons
                        Activate alternative way of showing different annotations (one colour
                        per set of markings, rather than counts).
```

You may also define arguments in a file and pass them in as follows:

```bash
python slate.py @arguments.txt
```

### Keybindings

The tool shows files one at a time in plain text. Default commands are shown below.

Note: special keys such as `ENTER` and `BACKSPACE` may not work on non-OS-X operating systems. That is why in all places where they are used we have an alternative as well.

Type                        | Key                                                       | Labelling Affect                 | Linking Affect
--------------------------- | --------------------------------------------------------- | -------------------------------- | ---------------------
Movement                    | <kbd>j</kbd> or <kbd>&larr;</kbd>                         | move to the left                 | move selected item to the left
&nbsp;                      | <kbd>i</kbd> or <kbd>&uarr;</kbd>                         | move up a line                   | move selected item up a line
&nbsp;                      | <kbd>o</kbd> or <kbd>&darr;</kbd>                         | move down a line                 | move selected item down a line
&nbsp;                      | <kbd>;</kbd> or <kbd>&rarr;</kbd>                         | move to the right                | move selected item to the right
&nbsp;                      | <kbd>J</kbd> or [<kbd>Shift</kbd> + <kbd>&larr;</kbd>]        | go to the start of the line      | move linking item to the left
&nbsp;                      | <kbd>I</kbd> or [<kbd>Shift</kbd> + <kbd>&uarr;</kbd>]        | go to first line                 | move linking item up a line
&nbsp;                      | <kbd>O</kbd> or [<kbd>Shift</kbd> + <kbd>&darr;</kbd>]        | go to last line                  | move linking item down a line
&nbsp;                      | <kbd>:</kbd> or [<kbd>Shift</kbd> + <kbd>&rarr;</kbd>]        | go to the end of the line        | move linking item to the right
Edit Span                   | <kbd>m</kbd>                                              | extend left                      | extend selected item left
&nbsp;                      | <kbd>k</kbd>                                              | contract left side               | contract selected item left
&nbsp;                      | <kbd>/</kbd>                                              | extend right                     | extend selected item right
&nbsp;                      | <kbd>l</kbd>                                              | contract right side              | contract selected item right
&nbsp;                      | <kbd>M</kbd>                                              | -                                | extend linking item left
&nbsp;                      | <kbd>K</kbd>                                              | -                                | contract linking item left
&nbsp;                      | <kbd>?</kbd>                                              | -                                | extend linking item right
&nbsp;                      | <kbd>L</kbd>                                              | -                                | contract linking item right
Label Annotation (default)  | <kbd>Space</kbd> then <kbd>a</kbd>                        | [un]mark this item as a          | -
&nbsp;                      | <kbd>Space</kbd> then <kbd>s</kbd>                        | [un]mark this item as s          | -
&nbsp;                      | <kbd>Space</kbd> then <kbd>d</kbd>                        | [un]mark this item as d          | -
&nbsp;                      | <kbd>Space</kbd> then <kbd>v</kbd>                        | [un]mark this item as v          | -
Link Annotation             | <kbd>d</kbd>                                              | -                                | create a link and move right / down
&nbsp;                      | <kbd>D</kbd>                                              | -                                | create a link
Either Annotation mode      | <kbd>u</kbd>                                              | undo annotation on this item     | undo all annotations for the current item

Shared commands:

Type                        | Mode   | Key                                             | Affect               
--------------------------- | ------ | ----------------------------------------------- | ----------------------------
Searching                   | Normal | <kbd>\\</kbd>                                    | enter query editing mode
&nbsp;                      | Query  | <kbd>?</kbd> or <kbd>Enter</kbd>                    | exit query editing mode
&nbsp;                      | Query  | <kbd>!</kbd> or <kbd>Backspace</kbd>                    | delete last character in query
&nbsp;                      | Query  | characters except <kbd>?</kbd> and <kbd>!</kbd> | add character to query
&nbsp;                      | Normal | <kbd>p</kbd>                                    | go to previous match
&nbsp;                      | Normal | <kbd>n</kbd>                                    | go to next match
&nbsp;                      | Normal | <kbd>P</kbd>                                    | go to previous match for linking line
&nbsp;                      | Normal | <kbd>N</kbd>                                    | go to next match for linking line
Assigning text labels       | Normal | <kbd>t</kbd>                                    | enter label editing mode
&nbsp;                      | Label  | <kbd>?</kbd> or <kbd>Enter</kbd>                    | exit label editing mode and assign the label
&nbsp;                      | Label  | <kbd>!</kbd> or <kbd>Backspace</kbd>                    | delete last character in label
&nbsp;                      | Label  | characters except <kbd>?</kbd> and <kbd>!</kbd> | add character to label
Saving, exiting, etc        | Normal | <kbd>]</kbd>                                    | save and go to next file         
&nbsp;                      | Normal | <kbd>[</kbd>                                    | save and go to previous file     
&nbsp;                      | Normal | <kbd>q</kbd>                                    | save and quit                    
&nbsp;                      | Normal | <kbd>s</kbd>                                    | save                             
&nbsp;                      | Normal | <kbd>Q</kbd>                                    | quit                             
Misc                        | Normal | <kbd>#</kbd>                                    | toggle line numbers
&nbsp;                      | Normal | <kbd>h</kbd>                                    | toggle help info (default on)    
&nbsp;                      | Normal | <kbd>{</kbd> or <kbd>PAGE-UP</kbd>              | shift view up 5 lines
&nbsp;                      | Normal | <kbd>}</kbd> or <kbd>PAGE-DOWN</kbd>            | shift view down 5 lines
&nbsp;                      | Normal | <kbd>></kbd> then <kbd>p</kbd>                  | toggle showing progress through files
&nbsp;                      | Normal | <kbd>></kbd> then <kbd>l</kbd>                  | toggle showing legend for labels
&nbsp;                      | Normal | <kbd>></kbd> then <kbd>m</kbd>                  | toggle showing the mark on the current item

### Misc

To annotate multiple files, specify more than one as an argument.
For greater control, provide a list of files in a file specified with `--data-list` / `-d`.
The list should be formatted as follows, where [] indicate optional values:

```
raw_file [annotation_file [starting_position [additional_annotation_files]]]
```

For example, these commands will create a file list, use it, then return to it later:

```bash
find . -name *txt > filenames_todo
./slate.py -d filenames_todo -l do_later
# ... do some work, then quit, go away, come back...
./slate.py -d do_later.todo -l do_even_later -o
```

Note, the `-o` flag is added so it will allow you to edit the annotations you have already created.
Otherwise the system will complain that you are overwriting existing annotation files.

When the `additional_annotation_files` are included it activates an adjudication mode.
By default, all annotations that appear in all additional files are added to the current annotations.
Disagreements are coloured in the text, but will disappear once a decision is made (using the normal annotation commands).

### Running in Windows

Users have reported a range of issues when trying to run slate:

- Underlining, which is used to show the currently selected text, does not work.
- Shift keys do not work

Here are a few things to try that others have found helpful:

- Use the Windows Subsystem for Linux (WSL) with Ubuntu
- Reinstall ncurses, or install windows-curses
- If you hit an encoding issue, try converting your raw text file to ASCII
- Try powershell
- Use a config file with different keybindings, to avoid needing shift

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

#### Changing the label set / Adding labels

The label set is defined in your config file (see an example config [here](https://github.com/jkkummerfeld/slate/blob/master/tutorial/config-example.txt)).

See lines like this for label definitions:

```
Label:          a                         SPACE_a green
```

The format is:
```
Label:        <label>                    <command> <colour>
```

You can add / edit / remove these lines to define your own label scheme. For example, for NER you may want to do:

```
Label:          O                         SPACE_a green
Label:          LOC                       SPACE_s blue
Label:          PER                       SPACE_d red
Label:          ORG                       SPACE_f yellow
Label:          MISC                      SPACE_v magenta
```

For an example of a custom config file, see [ner-book.config](ner-book.config)

The current set of available colours is: [green, blue, white, cyan, magenta, red, yellow].
Note that by default white is used for regular text and cyan is used for cases where multiple labels apply to the same content.

To define more colours, edit the top of `slate/config.py`.
By varying both the text colour (foreground) and background colour you can achieve quite a range of variations.
You can also define any RGB colour you want using the curses [init_color](https://docs.python.org/3/library/curses.html#curses.init_color) function and the [init_pair](https://docs.python.org/3/library/curses.html#curses.init_pair) function.

# Questions

If you have a question please either:

- Open an issue on [github](https://github.com/jkkummerfeld/slate/issues).
- Mail me at [jonathan.kummerfeld@sydney.edu.au](mailto:jonathan.kummerfeld@sydney.edu.au).

# Contributions

If you find a bug in the code, please submit an issue, or even better, a pull request with a fix.

# Acknowledgments

This tool is based in part upon work supported by IBM under contract 4915012629, and by ONR under MURI grant N000140911081.
Any opinions, findings, conclusions or recommendations expressed are those of the authors and do not necessarily reflect the views of IBM.

