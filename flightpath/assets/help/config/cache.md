## Cache

CsvPath Framework can cache the line count and headers the first time you use a file. For large files this can save quite a bit of time during development. Other forms of caching are not disk-based.

The setting indicates what directory should serve as the cache. The default is `./cache`. Cache files are very small. While CsvPath Framework does not limit the number of cache files, it is highly unlikely that your local development in a project will generate so many files it becomes a problem. You can of course delete cache files anytime.

Another thing to pay attention to is cached headers. Most CSV and XLSX files have a single set of headers. But a significant minority have multiple header rows, metadata, or prolegomena that is not data. In these cases, caching headers is not as valuable and could even be problematic.

When you are working with local files it makes sense to leave caching on. But when you deploy a configuration to production there could be reasons to turn caching off, particularly since you seldom reprocess files in production.  We would also recommend using modestly sized representative data samples for development. If you stick to that, caching does not have a big benefit.

To disable caching set the `use_cache` key to `no`. FlightPath caches files in the background. It continues to do this even if you turn the cache off for your own use.

