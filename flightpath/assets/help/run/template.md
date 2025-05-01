## Add a template *(optionally)*

Templates help you land your data in a specific place in the archive.

The location a template indicates for results is based on the original location of the data file, prior to it being staged in CsvPath Framework.

Templates use tokens to refer to the segments of the original path. A token looks like a colon with a number. E.g. `:2`. This token refers to the 3rd path segment because tokens are numbered from 0.

As an example, given an archive named `biz_ops` and a named-paths group named `processing` and a source data file originally received at:

```
    /companies/Acme/documents/invoices/2025/March
```

This template:

```
    :3/:1/:4/:5/:run_dir
```

Might result in the run results landing at:

```
    /biz_ops/processing/invoices/Acme/2025/March/2025-06-01_00-00-00
```

Templates are powerful, but not always needed. They are completely optional.

