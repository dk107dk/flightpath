## Config

The config panel is where you setup CsvPath Framework for your development workflow and production automation. The config values live in a config.ini file. Typically config.ini lives within the working directory at ./config/config.ini.

In production, a config lives with your automation scripts. The config file tells CsvPath Framework where to find named-files and named-paths and where to publish results. It also turns on any integrations you want to use, for example the OpenTelemetry or Slack integrations.

### Config sections
The config file has several sections for different purposes. It has a small number of settings keys in each section. The structure of the file follows the typical .ini form.

* cache - settings to help speed up opening large files
* config - sets the config file path
* errors - allows you to customize how errors are handled
* extensions - tells CsvPath Framework what files to consider data files
* inputs - points to your named-paths and named-files
* listeners - selects the integrations you want to run
* logging - settings for logging options
* results - indicates where you publish results
