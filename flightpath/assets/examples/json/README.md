# Using JSON


CsvPath Framework supports JSONL and JSONPath, as well as using JSON for
manifests and group description files. JSONL is a line-by-line file format
where each line is well-formed JSON with a linefeed at the end of each "row" of
data.


FlightPath supports editing JSONL files in two ways: using the grid view or
using the JSON view. If you use the grid view your data will be interpreted and
mapped to the grid structure as well as possible, with the understanding that
JSONL is not a perfect fit for a simple grid view. And when you save from the
grid view, you will pick a new filename and save the data as CSV.
Alternatively, you can right-click a JSONL file and select *Edit as JSON*. This
will open the JSONL file in the JSON editor. In this view you will have full
control of the data and format; however, you don't get the productivity that
comes from using the grid view.


JSONPath is available using the `jsonpath()` function. You can use the function
with any file format, not just JSONL. If a CSV file has a header with JSON
values, you can use the function to inspect that nested data.



