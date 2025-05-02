## Set working directory

**FlightPath Data** enables you to create csvpaths and manage CsvPath Framework from a consistent development setup in a working directory. This button lets you choose the directory.

You can have as many working directories as you need to organize your different data projects. Each will have it's own configuration file, logging, and other assets. Each project can also share archives and staging locations, if that is desired.

When you pick a new directory that you haven't used before, FlightPath will generate a new config file and do other automatic setup and housekeeping. You can edit your config.ini file by hand or click the *Open config* button below to access configuration options through forms in a more controlled way.

The CsvPath Framework creates the following files and folders:
* archive
* cache
* config
    * config.ini
* inputs
* logs
* transfers

FlightPath creates:
* examples
    * definition.json
    * README.md
    * simple_model.csvpath
    * test.csv
    * test.csvpath

Keep in mind that FlightPath only shows you directories within your working directory and files that it recognizes as data, metadata, or csvpaths. You can set the extensions recognized as CSVs or CsvPath Language files in config using the `Open config` button.

