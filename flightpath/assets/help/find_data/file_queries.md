## File References

File references find staged data files. They are a simple query language specific to CsvPath Framework that identifies data files in the staging area. The data staging area is configured in config.ini in the `[inputs]` section `files` key. See the config button at the bottom left for more.

A file reference has the form:

<i>$ <b>named-file-name</b> .files. <b>selector</b> : <b>0-2 limiters</b> . <b>optional date selector</b> . <b>0-2 limiters</b></i>

With these meanings:
* <b>named-file-name</b>: the name of a named-file
* <b>files</b>: the `files` datatype. This dialog also supports the `results` datatype.
* <b>selector</b>: a date, path, or SHA256 file fingerprint
* <b>limiters</b>: one or two limiters that narrow what the selector finds

### Selectors

A selector matches with a file by date, path or hash code. Dates and paths are prefix matched. Fingerprints are exact match.

A date selector must be in the form: YYYY-MM-DD_HH-MM-SS. When a date is used without a limiter it selects all matches in its smallest unit. The smallest unit is the right-most component of the selector. For example to match on all files that were registered between 10 AM and 11 AM you would use: `2025-06-14_10`. A date selector must start with at lease four digits and a dash; for example: `2025-`.

Path selectors are relative to the staging area root, starting below the named-file name. A named-file `orders` in a staging area defined as `/data` would register its files at `/data/orders`. A reference to an orders file for Acme Inc. in May might look like: `$orders.files.may/acme`.

### Limiters

Limiters are ranges, ordinals or dates. Each selector can have zero, one, or two limiters. A limiter is a colon followed by a value or keyword.

The three types of limiters are:

**Ranges**
<ul>
    <li>all</li>
    <li>before</li>
    <li>to</li>
    <li>after</li>
    <li>from</li>
    <li>yesterday</li>
    <li>today</li>
</ul>

**Ordinals**
<ul>
    <li>first</li>
    <li>last</li>
    <li>index</li>
</ul>

**Dates**
<ul>
    <li>Same form as a selector date, also prefix matched</li>
</ul>

Limiters look like: *$myfile.files.the/path:yesterday:first*

This reference selects the first file registered yesterday under the `myfile` named-file name that had a path starting in `the/path`.

### More Examples

All files registered under `orders` between the first moment of 2023 and the last moment of May 2024:

*$orders.files.2023-:after.2024-06-01:before*

The last `orders` file received from Acme Inc. that was stored under the companies directory:

*$orders.files.companies/acme/:last*

The first `orders` file from Acme Inc's US regions in 2025:

*$orders.files.companies/acme/US:from.2025-:from:first*


