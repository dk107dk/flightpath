## Environment Vars

This panel is for setting environment variables. Env vars are used by the storage backends. They are also available to any other configuration in CsvPaths Framework by setting an env var value in `ALL CAPS`. CsvPath Framework will replace those values with the value of the env var key named.

FlightPath env vars are set here and saved in plain text JSON in the `.flightpath` config file in your home directory. This approach persists the env vars across multiple FlightPath sessions. You should be able to do all your work with env vars here, but if you run into trouble, you can always inspect and update `.flightpath` directly, then restart FlightPath.

Setting var values here does not change your env vars outside of FlightPath, but it does override them within FlightPath. You can, of course, also set env vars in the usual way, OS wide, outside of FlightPath. To delete a var, set it to an empty value. However, to delete a regular OS-wide env var, even one overridden in FlightPath and deleted for the current session, you must do it outside FlightPath and restart the application.

Unlike other config settings, when you make a change in the table shown above it is saved immediately. Note that, in some cases, if you make a change here to an env var used for an integration you may need to restart FlightPath for the change to take effect.

