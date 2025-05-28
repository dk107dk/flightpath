## Project picker

**FlightPath Data** enables you to create manage CsvPath Framework projects. Each project starts with the same generated assets CsvPath Framework gives you when you first load it. Additionally, FlightPath adds some example files to help you get started.

This drop-down shows all your projects, lets you quickly switch from one to another, and enables you to create new projects.

You can make as many projects as you need. Each will have it's own configuration file and be completely separate from the others. However, all projects can share archives and staging locations, if that is desired.

Projects exist within a projects directory. By default it is called FlightPath and lives in your home directory. If you use a copy of FlightPath installed from the Apple or Microsoft app stores the application runs in an OS-managed sandbox and your projects directory must also be in the sandbox.

You can open the projects directory from the Config Panel. Open the Config Panel by clicking the button at the bottom of the left-hand column. In the Config Panel, click on projects in the left-hand menu. Opening the directory in Finder or Explorer can be helpful in bulk-adding files to a FlightPath project.

CsvPath Framework creates the following files and folders:
* archive
* cache
* config
    * config.ini
* inputs
* logs
* transfers

You can change the locations of the directories using `config.ini` settings. `config.ini` can itself be moved; although, typically it is left in the config directory where it is generated. Moving `config.ini` is not hard, but it is beyond the scope of this documentation. If you need to do it, look at the docs on https://www.csvpath.org.

FlightPath additionally creates:
* examples
    * definition.json
    * README.md
    * simple_model.csvpath
    * test.csv
    * test.csvpath

Keep in mind that FlightPath only shows you directories within your working directory and files that it recognizes as data, metadata, or csvpaths. You can set the extensions recognized as CSV or CsvPath Language files in the Config Panel.

