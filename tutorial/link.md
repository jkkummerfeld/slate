### Linking Example

This file is intended to help learn about text linking with slate. It is
intended to be read and followed from within slate. If you are in the directory
containing slate, run it like so:

```shell
python src/annotate.py tutorial/link.md -t link -s line -o -hh -l log.tutorial.link.txt
```

This command is also an example of how to run the code. It says to:

 - run the program with python (`python src/annotate.py`),
 - annotating this file (`tutorial/link.md`),
 - with links (`-t link`),
 - applied to lines (`-s line`),
 - reading and overwriting any existing annotation file (`-o`),
 - hiding the help at the start (`-hh`),
 - and logging to a specified file (`-l log.tutorial.link.txt`)

When linking, one item is marked with an underline, and another is marked with
green text. At the moment, the top line should be both green and underlined.

Try moving the lines:

  >- Move the underlined line down by pressing `DOWN` or `o`
  >- Move it up with `UP` or `i`
  >- Move the green line down by pressing `SHIFT` + `DOWN` (Not all platforms) or `SHIFT` + `o`
  >- Move it up with `SHIFT` + `UP`(Not all platforms) or `SHIFT` + `i`

If you do not find that the SHIFT commands work it is possible to add support
by looking at the log file for "INFO:root:Input" and then either (1) modifying
a config file to have an extra `Special_Key` line like those already present,
or (2) by editing src/config.py to have the relevant number in `special_keys`
on line 202.

Links can be created in two ways:

  >- First, create a link by typing `SHIFT` + `d` (i.e. `D`).

Note that once linked, the text is highlighted (if you linked a line to itself)
or becomes blue (if you linked two different lines).

  >- Try removing the link by typing `SHIFT` + `d` again.
  >- Now try creating a link with just `d`.

Note that when typing lowercase `d`, after creating the link, the green line is
moved down one and the underlined line is changed to be right above it. Also,
the lines that are part of a link are now yellow, so you can see that they are
part of a link.

  >- Move the green line back up one
  >- Move the underlined line somewhere else and create another link with `SHIFT` + `d`
  >- Now press `u` to undo all links for this green line

There are a range of options for customising the behaviour discussed here, see
the command line options for details.

For more commands please see the README.md file. For now, you can:

 >- Type `q` to save and quit

