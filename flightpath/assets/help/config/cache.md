## Cache

CsvPath Framework can cache the line count and headers the first time you use a file. For large files this can save quite a bit of time during development. Other forms of caching are not disk-based. More disk caching may be added in the future.

The setting indicates what directory should be the cache. The default is `./cache`. Cache files are very small, but you will want to keep an eye on them. At this time CsvPath Framework does not limit the number of cache files. Most file systems can handle millions of small files, but performance and stability can eventually become a concern.

Another thing to pay attention to is cached headers. Most CSV and XLSX files have a single set of headers. But a significant minority have multiple header rows, metadata, or prolegomena that is not data. In these cases, caching headers is not as valuable and could even be problematic.

To disable caching the `use_cache` key can be set to `no`. We would recommend using modestly sized representative data samples for development. If you stick to that, caching may not have a big benefit.

