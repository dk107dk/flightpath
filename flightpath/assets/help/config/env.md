## Environment Vars

This panel is for setting environment variables. Env vars are used by the storage backends and some of the integrations in the *integrations* config section.

Env var values can be used in any configuration in CsvPaths Framework. To use an env var value in a config setting first name the env var in ALL CAPS. Then when you set an ALL CAPS config value, the Framework replaces it with the value of the same ALL CAPS env key.

So if your SFTP password is found in an env var called *SFTP_PASSWD* you would set up your *[sftp]* section in config.ini with something like:

````
    [sftp]
     username=Fred*
     password=SFTP_PASSWD*
````

FlightPath env vars are set here and saved in plain text JSON in the `.flightpath` config file in your home directory. This approach persists the env vars across multiple FlightPath sessions. You should be able to do all your work with env vars here, but if you run into trouble, you can always inspect and update `.flightpath` directly, then restart FlightPath.

Setting var values here does not change your env vars outside of FlightPath, but it does override them within FlightPath. You can, of course, also set env vars in the usual way, OS wide, outside of FlightPath. To delete a var, set it to an empty value. However, to delete a regular OS-wide env var, even one overridden in FlightPath and deleted for the current session, you must do it outside FlightPath and restart the application.

Unlike other config settings, when you make a change in the env vars table it is saved immediately. Note that, in some cases, if you make a change here to an env var used for an integration you may need to restart FlightPath for the change to take effect.

One final thing to be aware of. FlightPath Data uses OS env vars by default. As we described, you can add env vars that are persisted across session from the env config tab within the app. However, if you are using FlightPath Server you must use a JSON dictionary in an `env.json` file to get the same effect. `env.json` allows you to do substitution and configure integrations in exactly the same way as OS env vars, but is safe for a multi-user server environment.

You can use `env.json` in FlightPath Data as well. Doing so is an alternative to using OS env vars. The setting is in the `config` tab. However, you must be mindful if you are using the file not the OS. The file must be managed by editing it, rather than in the `env` tab. The `env` tab is only for OS env vars.
