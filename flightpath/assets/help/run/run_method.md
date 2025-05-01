## Select the run method

Runs can happen four ways in FlightPath. *(The CsvPath Framework offers additional options when used programmatically).*

* Collect serially
* Fast-forward serially
* Collect breadth-first
* Fast-forward breadth-first

These methods have two basic form:

* Collect captures the data of each matching line
* Fast-forward captures nothing, but still results in metadata, error handling, printouts, etc.

The difference between the *serially* vs *breadth-first* approaches is that serial runs apply each csvpath statement in the named-paths group to the same data in turn, each finishing before the next starts. Whereas, in a breadth-first run each line is matched against each csvpath statement in the named-paths group one after another before the next line is considered.

There are lots of options and subtleties. However, unless you know you want breadth-first processing, it is easier to stick with serial runs until you know you need something more specific.

