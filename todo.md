# Bugs

- Colour in comparison mode (bad interaction with edits for self-link colour)
- If self links are prevented, but forward links are allowed, then we get stuck when trying to jump over the cursor.

# Ideas

Visual
- Legend/key giving keys and their labels + colors
- Rather than highlighting text, use columns on the left (block of colour), for line mode at least. Not sure about tokens
- Variable location of instructions
- For blank lines, option to print only one in a row
- Handling clusters (make the set visible)
- Show the set of available labels
- Ability to colour linked items as they are created (to see the history). Either always showing all using different colours, or showing what the cursor is linked to.
- Allow different default when resolving disagreements (rather than the union, only have those with agreement, or a majority). Note, this is subtle, as it interacts with the way colouring works.
- Option to highlight matches

Annotation
- Constrain annotations, e.g. a flag to not allow links to point in one direction
- Make link vs. category vs. text changeable during annotation
- Option to not allow annotation of some files (and not create a file)
- Specify every chunk must be labeled, or only some
- Allow auto-search over labels (i.e. user types characters and we search over labels to get the right one as they type)
- Be able to annotate with errors (creating new errors along the way) and then sort by label
- Be able to mix levels (e.g. dialogue acts per line, and named entities within the line)
- Look into the Concrete format (https://www.cs.jhu.edu/~vandurme/papers/concretely-annotated-corpora.pdf) amd the LAF format for data input / output
- Allow multiple annotations of the same file at the same time

Movement
- Jump to next/prev unannotated chunk
- Option to jump to a line
- Add the ability to jump to the start/end of a paragraph (and expand / contract similarly)
- Jump to next match on a regex
- Option to have jumping retain the span's size (at the moment it becomes a single item again)
- When the movement key is pressed multiple times in a row quickly, start jumping further [optional], or have a fast jump key?

Documentation
- Nicer examples
- Tutorials on each mode

Internal
- Change help to be a mode (currently other keys are interpreted while it is showing)
- Improve speed of jumping back down
- More intelligent calculation of view position (avoid dry runs)
- Saving both cursor and link for linking mode (in todo file) and reading similarly
- For help, compose it out of a set of items, with line breaks changing when the screen is narrow

Supplementary tools
- IAA calculator (at all possible scales)
- Take standoff and create inline data (instead of adding inline as an input / output)

Misc
- Add a calibration mode, where people type keys so I can figure out what they mean (and they could customise things).
- Option to specify file names on the command line
- Support undo to reverse actions
- Add the option to read in the raw data when going back to a seen file
- Option to load all at start
- Option to only save on exit (not when changing files)
- Nicer argument, error, and logging handling
- Add logging of all edits to a file, so a crash can be recoverd from easily.
