## Config path

A `config.ini` file can live anyplace you choose. By default, CsvPath Framework will generate a config file in `config/config.ini`. If you want to put your config values in another place do one of two things:

* Set a `CSVPATH_CONFIG_PATH` environment variable pointing to the file
* Make the `[config]` section `path` key in the default `config/config.ini` file point to the file you actually want to use

In the latter case, CsvPath Framework will load your default config file and then reload using the file that you identify.


