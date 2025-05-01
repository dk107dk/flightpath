## Named-paths group templates

Templates use the location of arriving data to structure the archive of results. The csvpath loading dialog offers a template that tells where the output of runs is stored as named-results. This can be important for making your results easy to find and browse or for adding CsvPath Framework to an existing data operation.

Templates are completely optional. If you don't need a template for a named-paths group, it is of course easier to not add one.

### Usage and examples

A template has the form of a path. Within the path you can use colon-number tokens to pull segments names from the arrival path. The colon-number tokens are 0-based.

You must include a `:run_dir` token. `:run_dir` is the placeholder for a run's time-stamped main directory. The `:run_dir` holds the directories of the individual csvpaths in the run and the run's `manifest.json` file. `:run_dir` is not optional.

For example, a template like:

```
    customers/:1/:2/:run_dir/prod
```

has two colon-number replacements: `:1` and `:2`. Say we receive a new file at:

```
    inbound/Acme Inc/2025/May/05-2025-invoices.csv
```

A named-paths group called `invoices` loaded into `inputs/named_paths` sends its results to the archive under the name `invoices`. A run on June first at 1:30pm GMT starting with the file above and this `invoices` named-paths group:

```
    inputs/named_paths/invoices
```

would put its results `manifest.json` in the archive at:

```
    archive/invoices/customers/Acme Inc/2025/2025-06-01_13-30-00/prod/manifest.json
```

If you didn't apply the template to the named-paths group your run would land in the archive at:

```
    archive/invoices/2025-06-01_13-30-00/manifest.json
```

Either way is fine. It just depends on what structure you want for your archive.


