## Config

The main way to setup a CsvPath Framework project is through its config.ini settings. A project at its core is essentially just the config.ini file and a working folder. For instance, when you deploy a project to FlightPath Server you are simply creating a project folder on the server and copying a config.ini file to it.

A `config.ini` file can live anyplace you choose. By default, CsvPath Framework will generate a config file in `config/config.ini`. When you are working in FlightPath the default is that path, relative to your project's root directory. If you want to put your config values in another place do one of two things:

* Set a `CSVPATH_CONFIG_PATH` environment variable pointing to the file
* Make the `[config] path` key in the default `config/config.ini` file point to the file you actually want to use

In the latter case, CsvPath Framework will load your default config file and then reload using the file that you identify. It is important to remember that CsvPath will load the config.ini at its default location -- creating one if needed. But it will then check `[config] path` and reload if finds the path to another config file.

You must make sure your desired config file has a `[config] path` key that points to itself. If your `[config] path` keys create reload cycles, from one config file to the next and then back to the first, FlightPath will refuse to start, rather than entering an infinite config reload loop.

All that said, creating a config file that doesn't live at `config/config.ini` is not typical. More typically, when a separate config is needed, you would just create a new project.

### env.json

Some integrations look to OS env vars for their input values. CsvPath Framework will attempt to convert its config values by looking them up as env keys if the value is in ALL CAPS. This means that `config.ini` could have:

````
    [sftp]
     username = myusernameis
     password = SFTP_PASSWORD
````

With the result that `password` would become the value of the SFTP_PASSWORD env variable.

In the case of FlightPath Server, that strategy no longer works, because Server is a multi-user, multi-project environment. OS env vars could easily collide. Instead we can set:

````
    [config]
     allow_var_sub = yes
     var_sub_source = /home/FlightPathServer/mykey/myproject/config/env.json
````

This setting would make env var lookups happen against the `env.json` file, rather than the OS env vars. When your project deploys (via the API or using FlightPath) `mykey` becomes the hash of your API key and you can use any file below the project directory to store your env vars, as long as it contains only a JSON dict. By default we expect `config/env.json`.



