### Linking Example

This file is intended to help learn about text linking with slate. It is
intended to be read and followed from within slate. If you are in the directory
containing slate, run it like so:

  >- `./src/annotate.py example/link-example.md -hh --ann-type link --ann-scope line --overwrite`

When linking, one item is marked with an underline, and another is marked with
green text. At the moment, the top line should be both green and underlined.

Try moving the lines:

  >- Move the underlined line down by pressing `DOWN` or `o`
  >- Move it up with `UP` or `i`
  >- Move the green line down by pressing `SHIFT` + `DOWN` (OS X only) or `SHIFT` + `o`
  >- Move it up with `SHIFT` + `UP` (OS X only) or `SHIFT` + `i`

If you are not using OS X it is possible to add support for the shift based
movement. Try typing "SHIFT + DOWN", look at the log file and see the line
about user input, and use that number in your keybindings (either in config.py
or a config file).

Links can be created in two ways:

  >- First, create a link by typing `SHIFT` + `d` (i.e. `D`).

Note that once linked, the text turns blue.

  >- Try removing the link by typing `SHIFT` + `d` again.
  >- Now try creating a link with just `d`.

Note that when typing lowercase `d`, after creating the link, the green line is
moved down one and the highlighted line is changed to be right above it. Also,
the lines that are part of a link are now yellow, so you can see that they are
part of a link.

  >- Move the green line back up one
  >- Move the underlined line somewhere else and create another link with `SHIFT` + `d`
  >- Now press `u` to undo all links for this green line

There are a range of options for customising the behaviour discussed here, see
the command line options for details.

