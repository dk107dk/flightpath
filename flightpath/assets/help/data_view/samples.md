## Create samples

FlightPath enables development of CsvPath Language files and management of the data preboarding processes that run those files.

To speed development and maintain quality control, DataOps teams work with representative known-good and known-bad sample data. This toolbar helps you capture a sample from a data file.

You can capture and save a data sample in three ways:
* By collecting the first N lines of a file
* By collecting a random set of lines starting from the beginning of the file, or
* By selecting a random set of lines scattered throughout the file

You can, of course, work with an entire file. Saving a sample is just a way to help you create a fast-running and deterministic test data set. Once you have the perfect test data set you can start building csvpaths to validate and shape it. When your csvpaths are ready, use FlightPath to deploy them to production.

Keep in mind, FlightPath is not primarily a data wrangling tool. Its mission is to make developing csvpaths and managing the CsvPath Framework easy. There are many excellent CSV, Excel, and data frames development environments and command line tools that will help you manipulate your samples to support the scenario and unit tests you need.



