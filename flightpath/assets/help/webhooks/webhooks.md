## Webhooks

You can add webhooks that are called at the end of a run. There are four cases where a webhook can be called:
* After any run
* After a run where all statements are valid
* After a run where any statements are invalid
* After a run that has one or more errors

Each webhook configuration consists of:
* A URL to call using an HTTP POST
* A string that defines properties for a JSON payload to be POSTed to the URL

The properties definition is a set of name-value pairs separated by commas. A name-value pair looks like:

```
    name > value
```

You can read that as `name` points to `value`.

As well as being static, values can also come from the run's metadata or variables using these forms:
* `meta|name` *(e.g. `meta|description`)*
* `var|name` *(e.g. `var|first_name`)*

A `meta|` value will come from the external comment metadata fields of a csvpath. A `var|` value will come from the csvpath variables.

Since webhooks are called at the end of a run, not in the context of a particular csvpath statement, you have to keep in mind that all the metadata is bundled together. Likewise with variables, you're working from a superset of variables where the last variable setter wins.

A value that is in ALL CAPS will be swapped for a value identified by that name in the OS or FlightPath env vars.

This is an example of a webhooks properties definition:

```
    name > meta|name, time > var|today, content-type > text/plain, token > MY_KEY
```

It might create a payload for the webhook call that looks like this:

```json
{
  "content-type": "text/plain",
  "token": "a3cf-11b3-9012-ffe8-d38f-afe4",
  "name": "my csvpath statement",
  "time": "2025-04-03 14:11:23.353189+00:00"
}
```



