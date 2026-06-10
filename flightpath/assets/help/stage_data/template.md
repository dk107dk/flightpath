## Data staging templates

Templates use the location of arriving data to structure the named-files staging area and the archive of results. The data staging dialog offers a template that tells where a new file is stored as a named-file. This can be important for making your incoming files easy to find and browse or for adding CsvPath Framework to an existing data operation.

Templates are completely optional. If you don't need a template for a named-file, it is of course easier to not add one.

A template has the form of a path. Within the path you can use tokens to pull segments names from the arrival path. Tokens have a colon followed by a number or word. The tokens are:
- colon-number (e.g. `:3`) are a pointer to a path segment from the incoming file's original location
- datetime tokens

The colon-number tokens are 0-based.

The datetime tokens are the current datetime values:
- `:year`
- `:month`
- `:month_name`
- `:day`
- `:hour`
- `:hour_24`
- `:minute`
- `:second`

The `:month_name` token gives the full English month name. The `:hour_24` token gives current hour in 00-23.

You must include a `:filename` token at the end of the template. `:filename` is the placeholder for the name of the physical file to be registered. `:filename` is not optional.

### Usage and examples

For example, a template like:

```
    customers/:1/:2/:3/final/:filename
```

has three colon-number replacements: `:1`, `:2`, and `:3`. The `:filename` token is for the incoming file's name. It must come last and is not optional.

If we receive a new file at:

```
    inbound/Acme Inc/2025/May/05-2025-invoices.csv
```

A named-file called `invoices` in a staging folder at `inputs/named_files` and using that template would store `05-2025-invoices.csv` at:

```
    inputs/named_files/invoices/customers/Acme Inc/2025/May/final/05-2025-invoices.csv
```

If you didn't apply that template to the named-file you would access the new file at:

```
    inputs/named_files/invoices/05-2025-invoices.csv
```



