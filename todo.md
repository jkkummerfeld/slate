# Next Steps

- Change help to be a mode (currently other keys are interpreted while it is showing)
- Nicer examples
- Tutorials on each mode
- Legend/key giving keys and their labels + colors
- Rather than highlighting text, use columns on the left (block of colour), for line mode at least. Not sure about tokens
- Add a calibration mode, where people type keys so I can figure out what they mean (and they could customise things).
- Allow multiple annotations of the same file at the same time
- For blank lines, option to print only one in a row
- Variable location of instructions
- Allow auto-search over labels (i.e. user types characters and we search over labels to get the right one as they type)
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
- Option to not allow annotation of some files (and not create a file)
- Look into the Concrete format (https://www.cs.jhu.edu/~vandurme/papers/concretely-annotated-corpora.pdf) amd the LAF format for data input / output
- Show the set of available labels
- Specify every chunk must be labeled, or only some
- Be able to annotate with errors (creating new errors along the way) and then sort by label
- Handling clusters (make the set visible)
- Nicer argument, error, and logging handling
- Add the ability to jump to the start/end of a paragraph (and expand / contract similarly)
- Allow definition of keys to jump to next match on a regex or even a simple string
- Option to have jumping retain the span's size (at the moment it becomes a single item again)
- Shortcut to jump to just before the link line
- When the movement key is pressed multiple times in a row quickly, start jumping further [optional], or have a fast jump key?
- Be able to mix levels (e.g. dialogue acts per line, and named entities within the line)

### Internal

- More intelligent calculation of view position (avoid dry runs)
- Saving both cursor and link for linking mode (in todo file) and reading similarly
- Improve speed of jumping back down
- For help, compose it out of a set of items, with line breaks changing when the screen is narrow

### Supplementary tools

- IAA calculator (at all possible scales)
