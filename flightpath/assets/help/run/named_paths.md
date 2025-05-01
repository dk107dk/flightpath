## Select a named-paths group

Named-paths are collections of csvpath statements that are run as a group. The csvpath statements are written in CsvPath Language that validate or upgrade a data file.

A named-paths group can be identified by its name or by a more specific reference. References allow you to pick out one or more individual csvpath statements to run.

Named-paths references look like:

```
    $my_named_paths_name.csvpaths.a_statement_id_or_index
```

Named-paths groups may also contribute templates to the run. A template determines how the location of the original data file can contribute information to the location the run results will land. A template can be stored with the named-paths group. Templates can also be specified as a one-off when the run is started.

Templates have the form:

```
    segment/:2/another_segment/:1/:run_dir
```

Where `:2` indicates the 3rd segment of the original source location for the data used in the run. if this template is used in a run where the source file's original location was `/customers/invoices/2025/March` and the named-paths group was `ops` the results would be at an archive location like:

```
    my_archive/ops/segment/2025/another_segment/invoices/2025-05-23_09-23-00
```


