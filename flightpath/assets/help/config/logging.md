## Logging

Like several other sections, the CsvPath Framework configures logging for individual csvpaths and for named-paths groups separately. This flexibility, combined with logging configuration overrides on a csvpath-by-csvpath basis, gives you the ability to cut down logging noise to help you better see what you're looking for.

The <i>csvpath</i> setting is for individual csvpath statements run by instances of the CsvPath Framework's <i>CsvPath</i> class. The <i>csvpaths</i> setting is for named-paths groups, specifically for logging in <i>CsvPaths</i> class instances that are running groups of csvpath statements.

Keep in mind that when you run a named-paths group a <i>CsvPaths</i> instance manages a set of <i>CsvPath</i> instances that each run one of the individual csvpaths in the named-paths group. Using FlightPath you generally don't really need to know those details. But when it's time to automate your preboarding process a basic understanding helps.



