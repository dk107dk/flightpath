## Environment Vars

This panel is for setting environment variables. Env vars are used by the storage backends and some of the integrations in the *integrations* config section.

Env var values can be used in any configuration in CsvPaths Framework. To use an env var value in a config setting first name the env var in ALL CAPS. Then when you set an ALL CAPS config value, the Framework replaces it with the value of the same ALL CAPS env key.

So if your SFTP password is found in an env var called *SFTP_PASSWD* you would set up your *[sftp]* section in config.ini with something like:

````
    [sftp]
     username=Fred*
     password=SFTP_PASSWD*

````


### Where the data comes from
What you see in this tab depends on your *Variable substitution source* setting in the Config tab. If your source is `env`, you will see the OS env vars combined with the FlightPath Data env vars set in `.flightpath` in your home directory. If your source is the path to a JSON file containing a dictionary, you will see just those keys and values.

### The FlightPath Data env
FlightPath Data is a single user, multi-project environment. That means that the OS vars will never conflict with another user, but two projects may have different env needs.

Vars set here are saved to plain text in JSON files. If your variable substitution source is `env`, meaning the OS environment, your changes made here are saved in the `.flightpath` config file in your home directory. This approach persists the env vars across multiple FlightPath sessions and makes them available to all projects.

Conversely, if your `config.ini` has a JSON file path as its `var_sub_source` setting, you see the contents of only that file here. No OS or `.flightpath` env vars are included. And your env vars are not shared with any other projects.

### Where the data goes
Setting var values here does not change your env vars outside of FlightPath, even if you are using OS env vars. Your changes do override any OS env vars that have the same key, but only within FlightPath. You can, of course, also set env vars in the usual way, OS wide, outside of FlightPath.

To delete a var, set it to an empty value. However, to delete a regular OS-wide env var you must do it outside FlightPath and restart the application. If you have a value in `.flightpath` that overrides an OS env var, you can remove the `.flightpath` override here, but you must restart FlightPath if you change the original OS env var.

Unlike other config settings, when you make a change in the env vars table it is saved immediately. Note that, in a few cases, if you make a change here to an env var used for an integration you may need to switch projects or restart FlightPath for the change to take effect.

### Using FlightPath Server
Like FlightPath Data, FlightPath Server supports multiple projects. However, unlike FlightPath Data, FlightPath Server is also a multi-user environment. That means for security and correct functioning, FlightPath Server only uses variable substitution JSON files. You cannot use the OS env vars in a server project.


