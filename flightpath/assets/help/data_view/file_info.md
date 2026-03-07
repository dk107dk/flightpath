## Profiling a Data File

FlightPath profiles data files to give you the info you need for creating validation and upgrading scripts.

When you click the `File info` button, FlightPath takes a sample from the currently open file and generates a report. The report presents the overview information about your file:

* Header count
* Total line count
* Lines with data
* Blank lines
* Lines with blank header values
* Duplicate lines

And basic demographics for each header:

* Index number
* Header name
* Data types seen in header
* Duplicate values
* Distinct values check
* Min value (if number)
* Max value (if number)
* Nullability

### More info from AI

If you plug in your AI API using the Config dialog, you can also ask AI questions about your file. To do this open Config and select the `llm` tab to enter your API endpoint and key. Then right-click in the data view and select `Ask a question`.



