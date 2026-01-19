# Using headers


Headers are the names of values in a CSV, JSONL, or Excel file.  In a delimited
file, any given line may not have values for the headers. And headers can change
or be found at any point in a delimited file.


CsvPath Framework has many functions to help you work with headers. Most of the
functions are oriented towards creating validation rules or data upgrading.
Some of the header functions are quite unique. For example, in CsvPath Framework,
you can reset the headers to the values of the current line at any time.

Data upgrading is a key ability of CsvPath Language that sets it apart from
validation languages that only check structure and data type. You can use
CsvPath Lanaguage to transform data, much as you might use XSLT to transform XML.
The header functions are key to upgrading because they allow you to change the
shape of the data as it is matched line-by-line.

These examples will help you start exploring the headers functions so you can
start crafting your own rules.


