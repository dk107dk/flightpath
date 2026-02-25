## Templates

Templates are used to store data from a registration or a run in a certain location. A file registration always goes to the named-files area. A template can make the file's destination within the named-files more specific. Likewise, the output of a run always goes to the archive area. Adding a template can position the files generated within the run more specifically to your needs.

Templates contain static text, filesystem file and directory separators, and dynamic tokens. The dynamic tokens are based on the path of the content that was registered. The registration path is broken up into directory and file names and those names can be referenced like `:0`, `:2`, or `:8`. The filename itself must be the last section of a template and it must be `:filename`.

For example, a file imported from:
```
    /User/fred/data/incoming/orders/2026/q2/acme inc/q2-orders-summary-vh.csv
```

Might have a template like:
```
    /:4/:5/:7/:filename
```

Which would result in the file being registered, say in a named-file `orders`, at this path:
```
    inputs/named_files/orders/2026/acme inc/q2-orders-summary-vh.csv
```

Given that the named-files area is configured at `inputs/named_files`, as it is by default.

