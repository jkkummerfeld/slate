### Named Entity Recognition Labelling Example

This is a tutorial about text labelling for Named Entity Recognition with
slate. It is intended to be read and followed from within slate. When you see a
line with '>-' you should try out the command.

If you are in the directory containing slate, run it like so:

```shell
python slate.py tutorial/ner.md -t categorical -s token -o -c ner-book.config -l log.tutorial.ner.txt -sl -sm
```

This command is also an example of how to run the code. For an explanation of
all the parts, see the bottom of this file. For the full range of command line
arguments, see the README.md file.

When labelling, the current item is underlined. In this case, that means the
very first token of this document.  There are two ways to move the underline:

  >- Use the arrow keys to move left, up, down, and right
  >- Or use `j`, `i`, `o`, and `;` to move left, up, down and right,
     respectively

To select multiple tokens, start at the leftmost token, then:

  >- Hold `SHIFT` while moving to the right to expand your selection
  >- Hold `SHIFT` while moving to the left to contract your selection

To move, expand and contract faster:

  >- Type a number before any of the above commands and it will be repeated
     that many times

The command line arguments used for this tutorial also make it so that at the
bottom of the screen you can see:

 - A horizontal line
 - One or more lines listing the different labels, the colour they appear as,
   and the keys to apply them
 - One or more lines listing what labels are applied to the text that is
   currently selected.

To label an item, first move and expand to select the relevant text, then:

  >- Type `SPACE` and then `o` to apply the 'ORG' label

Note that the text has changed colour to indicate that it is labeled and the
label is disaplayed at the bottom of the screen.

  >- Type `SPACE` and then `o` again to remove the label
  >- Similarly, type `SPACE` and then `f` to apply the 'FAC' label

Note that various colours are used for the labels, but some repeat (future
versions of this code may use a wider range of colours).

It is possible to apply multiple labels to the same text, or have overlapping
labels. To see this in action:

  >- Type `SPACE` and then `o` to also apply the 'o' label

Note that at the bottom there are now multiple annotations shown. Also, the
text is in a cyan colour to indicate that it has multiple labels.

Now let's remove the annotations:

  >- Type `u` to remove both labels on this item

For more commands please see the README.md file. For now, you can:

 >- Type `q` to save and quit

#### Adjudication

Now we will learn how to compare annotations to create a consistent set of labels.

First, create two sets of annotations for some data.

Next, create a merged file that contains the cases where annotations agreed. One way to do this is with 

```
filenames="example.annotations0.txt example.annotations1.txt"
count=`ls $filenames | wc -l`
cat $filenames | sort | uniq -c | awk -v count=$count '$1 == count' | sed 's/^ *[0-9]* *//' > example.annotations.adjudicated.txt
```

Then create a file named "anno-file-list.txt" that looks like this:

```
tutorial/ner.md example.annotations.adjudicated.txt (1,0) example.annotations0.txt example.annotations1.txt
```

Run this command to start annotating, now with information about the existing annotations:

```
python slate.py -d anno-file-list.txt -t categorical -s token -o -c ner-book.config -l log.tutorial.ner.txt -sl -sm
```

Note - if this crashes with a `list index out of range` error then you need to change the `(1,0)` part of the line above because your data has a blank second line. Change the first number to be a line that does exist.

You will see that:

 - Any annotation in `example.annotations.adjudicated.txt` appears as a normal annotation.
 - Any annotation that is consistent across the different sets of annotations appears as a normal annotation.
 - Any tokens that have a disagreement in annotation appear in red.

You can now go through, assigning labels wherever you see red, resolving the disagreements between the annotations and creating one consistent set of annotations.

#### Command Explanation

The command for this tutorial is:

```shell
python slate.py tutorial/ner.md -t categorical -s token -o -c ner-book.config -l log.tutorial.ner.txt -sl -sm
```

It says to:

 - run the program with python (`python slate.py`),
 - annotating this file (`tutorial/ner.md`),
 - with categories (`-t categorical`),
 - applied to tokens (`-s token`),
 - reading and overwriting any existing annotation file (`-o`),
 - with a special configuration file (`-c ner-book.config`),
 - logging to a specified file (`-l log.tutorial.ner.txt`),
 - showing the set of possible labels (`-sl`),
 - and showing the labels under the cursor (`-sm`)
