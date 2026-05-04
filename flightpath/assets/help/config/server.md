## FlightPath Server

FlightPath Server is bundled with FlightPath Data. On MacOS it is embedded in FlightPath Data app's binary. On Windows it is a separate exe installed in the same folder as the app.

To run Server on MacOS, invoke the binary on the command line with the flag --server-mode like this:

````
    /Users/fredsmith/apps/FlightPath.app --server-mode
````

On Windows just double click the Server exe. There are instructions for running Server as a service on flightpathdata.com.

The path to your installation of FlightPath will of course be different depending on your OS. Please see the docs on https://www.flightpathdata.com for more information. Remember that you are operating within the MacOS or Windows sandbox. The sandboxes protect you, and they also have an impact on how applications run and how and where data is stored.

This config panel is for changing the `[server]` section of the current project's `config/config.ini`. You can set the location of the FlightPath Server, for example: http://localhost:8000, and an API key that let's you send requests. The form does not modify FlightPath Server's own config file. Again, see the documentation site for more on configuring FlightPath Server.

You can also shutdown a FlightPath Server from this form. To do so you must have an admin API key. When you shutdown FlightPath Server you are making an API call, not interacting with a local process. That means you cannot restart the server within the FlightPath Data app.

The API key you add to this form will be either a regular key or an admin key. A regular API key has a set of associated projects. A key enables complete control over its projects, so you should give a project's key only to those people who should be able to change the project in any way. Any API key enables a user to create new projects within the scope of that key. Since a project starts out as little more than a `config.ini` file creating new projects is simple and scales well to typical business use cases.


