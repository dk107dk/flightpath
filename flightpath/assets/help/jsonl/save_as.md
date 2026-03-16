## Save As

This dialog enables you to save data to CSV, using the delimiter and quotechar of your choosing.
There are a few things to keep in mind.

* Even if your file is JSONL or Excel, you are saving to CSV
* You can save with whatever delimiters and quotechars you need
* Depending on your tool bar selections you may be saving a sample, not the whole data set

&nbsp;
### JSONL

JSONL is quite unlike CSV and the grid editor is not intended for JSONL editing. If you want
to edit JSONL, keeping the data in JSONL format, you should click the `Toggle source` button
to bring up the JSON/JSONL editor. Alternatively, right click on the file name and select
`Edit as JSON`.

The JSON editor works well for both line-oriented data and regular document-oriented JSON.
JSONL and JSON have different opinions about well-formedness. When you work with JSONL, the
editor handles pretty printing and well-formedness checks in JSONL-appropriate ways. When you
save JSONL, the editor saves the data correctly in line-by-line format.

### Sampling

FlightPath Data is a development and operations tool for CsvPath Framework automations, not a
general purpose CSV editor. Because of this, it focuses on samples, rather than on whole data
sets. If a file has more than 66,000 lines, FlightPath will load 66,000 lines and warn you that
it isn't loading the whole file. 66,000 lines is an arbitrary number based on the max size
of a legacy Excel file (.xls). While FlightPath can open larger
files, its mission doesn't require it to handle unlimited data sizes.



