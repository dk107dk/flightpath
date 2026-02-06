## Sample Size

This drop-down selects the number of lines of data to send to the AI backend to use in generating csvpath statements.

The considerations are:
* If you don't give the AI enough representative sample data your generated csvpaths will be brittle
* If you give a larger sample, the time it takes to generate the csvpaths can get significantly longer
* Unless you are self-hosting the AI model, the more data you feed the AI the more it costs for the API call
* Remember that some data files have many headers; sometimes so much so that even a small sample may result in a relatively large amount of data

Generally 50 lines is enough of a sample. Your sample might not be 100% representative. But given that the csvpath statements generated are just a starting point, you will often get close enough with a small sample.

In early 2026 typical API call costs to the leading AI companies were in the $.02 to $.07 cent range. With more data or higher cost models, the numbers can certainly go up. You mileage may vary.

For most users, self-hosting models will not be a good option. It is quite easy to run FlightPath against a model running locally in Ollama, for example. However, our experience suggests that quality of the CsvPath statements generated suffers considerably on smaller models. Mid-range models running with >=64 GB RAM may be suitable, potentially with tweaks to the prompt contexts; however, for most users that will not be a competitive use of resources.


