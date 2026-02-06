## Large Language Model

FlightPath Data integrates with most AI LLM APIs. This form allows you to specify model and endpoint connectivity.

The model is expected to be one of the commercial LLMs. The Claude, Gemini, and GPT families have been tested. Other similar models may also give good results.

The `model` field is a technical model name, like `claude-sonnet-4-5-20250929` or `gpt-5.1-2025-11-13`.

The `api_base` field holds the URL of an LLM API endpoint.

The `api_key` field holds your LLM API key, if a key is required. For commercial services we anticipate a key will always be needed. While we don't recommend self-hosting, if you self-host, a key may not be needed.

Since your API key is a valuable secret we recommend holding it in an env var. You can do this by setting the field to `LLM_API_KEY`. FlightPath Data looks for an `LLM_API_KEY` variable in the OS or `env.json` variables file. You can use the `env` config tab to setup an `LLM_API_KEY` environment variable that will be active across FlightPath Data sessions.

FlightPath Server likewise requires `LLM_API_KEY` be in either `config.ini` or the `env.json` file. Using `env.json` as the variable substitution source protects one project's variables from leaking into other projects. You can create or sync your `LLM_API_KEY` to a FlightPath Server project using the `server` tab. Right-click on a project name and select `Sync config` and/or `Sync env` to configure LLM support on the server side.


