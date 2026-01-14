# Lookups

These example csvpaths create an index of zipcodes by city and perform lookups against it.

The data comes from data.gov: `catalog.data.gov/dataset/boundaries-us-zip-codes`. The extensive geo-coding data was removed for brevity.

To run this example:

1.  right-click to stage `Boundaries_US_Zip_Codes.csv` as a named-file called `zips`

2.  right-click to load `index_zipcodes.csvpaths` as a named-paths group called `zip_index`

3.  right-click to load `zipcoode_looksups.csvpaths` as a named-paths group called `zip_lookups`

4.  in the right-center window, right-click to run `zip_index` against the named-file `zips`

5.  again in the right-center window, right-click to run `zip_lookups` against the named-file `zips`

Staging named-files and loading named-paths groups are options on the context menu when you right-click a filename in the project directory tree on the left.

To run, right click on either the named-file folder or the named-paths folder in the windows on the right-hand side and select `New run`.

The result is a variable `"a"` with the value of Boston's zipcode




