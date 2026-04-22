## Large Language Models

FlightPath Data integrates with most AI LLM APIs. This form allows you to specify model and endpoint connectivity.

The model is expected to be one of the commercial LLMs. The leading AI models have been tested and give excellent results:
- Claude
- Gemini
- OpenAI

Other similar models may also be useful, but your mileage may vary.

### Note:
the most recent Claude, Gemini, and OpenAI models are quite good at helping with FlightPath Data and the CsvPath Framework. Older models are less strong, though some are still capable enough.

## The AI Config Settings

In the Config panel, look under the `llm` vertical tab. The `llm` tab allows you to set up your AI credentials for one project or all projects. If you add your credentials with the `Use for all projects` checkbox checked, you can still override the AI settings on a project-by-project basis.

### AI Model
The `model` field is a technical model name, like `claude-sonnet-4-5-20250929` or `gpt-5.1-2025-11-13`. See your vendor API account for the model name to use.

### AI API
The `api_base` field holds the URL of an LLM API endpoint.

The `api_key` field holds your LLM API key, if a key is required. For commercial services we anticipate a key will always be needed. While we don't recommend self-hosting, if you self-host, a key may not be needed.

Since your API key is a valuable secret we recommend holding it in an env var. You can do this by setting the field to `LLM_API_KEY`. FlightPath Data looks for an `LLM_API_KEY` variable in the OS or `env.json` variables file. You can use the `env` config tab to setup an `LLM_API_KEY` environment variable that will be active across FlightPath Data sessions.

FlightPath Server likewise requires `LLM_API_KEY` be in either `config.ini` or the `env.json` file. Using `env.json` as the variable substitution source protects one project's variables from leaking into other projects. You can create or sync your `LLM_API_KEY` to a FlightPath Server project using the `server` tab. Right-click on a project name and select `Sync config` and/or `Sync env` to configure LLM support on the server side.

### API Base
The well-known models don't need an API base. Those are the only models we recommend. They are:
- Claude
- Gemini
- OpenAI

### About the Generator INI File
The AI subsystem has its own `.ini` file. Generally you won't need to modify it. There are two configurations to be aware of.
- The turns limit
- The metadata directory

#### The Turns Limit
AI requests in FlightPath Data are turn-based conversations with tool use. Each turn in the conversation is a request from FlightPath Data to the API endpoint. This is similar to how a chatbot like Claude works: you ask a question, it answers, you may ask another question, and so forth.

When you configure a paid API, for example Claude or Gemini, you spend fractions of a penny to a small number of pennies per turn. These small amounts can add up, though typically they are small enough that they hardly matter. In order to make sure the AI doesn't run away making turn after turn behind the scenes we offer a turns limit. Typically it is 15. Most often, the most recent AI models find the right answer long before that.

What is a model doing in each turn? It is testing its answer for validity, so that what it gives you is a working solution. Each turn the AI requests that FlightPath test its answer. If the test is negative, the AI rethinks the problem and tries again. Most often we see the most recent models require four to six turns to get a result they think you need.

In FlightPath Data, as in all uses of AIs, the answers are often only mostly right. AIs are not mind readers and their answers will need some minor improvements. The most recent commercial models typically get their answer right or mostly right, making your review and improvements a minor effort.

To change the turns limit see the `[generations] turns_limit` key.

#### The Metadata Directory
The AI inputs and outputs are stored in the metadata directory. The directory holds:
- Template files that are combined into prompts
- The prompts sent to the AI API
- The results that come back from the API

Usually, you would not need to look in the metadata directory. Everything you need to do with AI you do in the FlightPath Data UI.

In some unusual situations you might want to use metadata directory assets. For example:
- Looking at the history of past API requests
- Adapting the prompt templates

We do not recommend adapting the prompt templates. They are carefully constructed and tested. It is unlikely that you would benefit by changing them.

The history of API calls could conceivably be more helpful. However, as the UI makes clear, you are intended to save the results of AI requests. The UI will not present them again in the future, in part because typically the moment they would be useful has passed. A set number of requests is retained. The controlling `.ini` file key is in `[generations] limit`, but again, this is not a value you would generally change.

&nbsp;
