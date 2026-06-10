## Directory Staging With a Regex

You may use a regular expression (regex) to limit the files registered in a directory. Regexes are a pattern matching language that can pick out certain file names for loading, skipping the others.

When you add a regex to the process of staging the contents of a directory, FlightPath iterates through all the files it finds and compares their names to the regex. If the regex doesn't match, the file isn't staged. The regex dialect is the same as the `regex()` CsvPath function, and is identical to Python regular expressions.



