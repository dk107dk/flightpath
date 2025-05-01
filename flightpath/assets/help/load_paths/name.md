## Named-paths groups

FlightPath's mission is to collect raw data from upstream providers and process it into trustworthy data published for downstream consumers. It does this by applying CsvPath Language statements to data files. CsvPath Language statements, csvpaths, validate and upgrade source data.

Multiple csvpaths can be applied at once to a single data file as a named-paths group. Breaking csvpath logic into simple statements, rather than a big statement that tries to do everything, is more productive for development and testing.

To create a named-paths group you pick a name and assign one or more csvpath statements to it. You may also add a template that uses a raw source file's original location to determine where a processed results file should be stored. Templates are completely optional.

