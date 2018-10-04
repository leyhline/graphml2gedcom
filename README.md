# graphml2gedcom

This is a really simple script with some assumptions about the style of the graph.
Of course, it's compatible with yEd's family tree format but the output has to be manually edited either way.

Otherwise, there are no dependencies and it's easy to run from the command line:

```
$ python3 graphml2gedcom.py --help
usage: graphml2gedcom.py [-h] [-o PATH] PATH

positional arguments:
  PATH                  Path to .graphml input file.

optional arguments:
  -h, --help            show this help message and exit
  -o PATH, --output PATH
                        Path where .ged output file should be written.
```
