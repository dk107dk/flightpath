## AI Functions

This tab offers four activity functions that rely on your AI API.
* Generate CsvPath Language validation statements for a data sample
* Answer questions about CsvPath Language
* Give a plain English explanation of one or more csvpath statements
* Create a test data sample matching one or more csvpath statements

&nbsp;

You must have an AI API configured to use this tab. To configure access to your LLM model's API click the `Open Config` button at the bottom left and go to the `llm` tab.

When you use an activity on this tab you give your question or request a name and, optionally, instructions for how you want it completed, and click submit. Your request goes to a list of requests below the form.

When your answer is ready you will see the indicator to the left of the name of your request go from yellow to green. AI requests can take a few seconds to multiple minutes. You can watch the progress of a query by clicking its name. When you click the name you will see a Tracking tab open in the help and feedback tray at the bottom of the center area. The tracking information will tell you how many interactions FlightPath has had with the AI and what tools the AI used to verify its answer.

## Working with an AI

As you work with your AI, please remember that AI models are inherently non-deterministic and fallible.

Non-deterministic means that the results you see may be different each time you hit submit, regardless of if you changed your query or not. Even tiny changes in your input csvpath statements, your instructions, or any data sample you provide will cause the answer to receive to be unique.

The AI will run csvpath statements in the background in order to make sure its answer has a minimum level of correctness. That doesn't mean the AI fully intuited what you actually need, or made the ideal choices for how to achieve it. It is very possible you will need to iterate on the AI's output in order to craft the statements you need, just as you might iterate on validation rules with a colleague.

 Think of the AI as if it were a coworker. If you say the same thing two different ways you will likely get a similar answer, but not the same answer. Likewise, the first response you get may not answer the question fully or in the way that you wanted.

## The AI activities
### Generate validation statements

This activity creates one or more CsvPath Language validation statements that validate a data file. Open a data file to enable this activity.

### Answer questions

You can ask the AI for help with CsvPath Language. It will respond with code suggestions and, in some cases, some explanation. AI will use the open csvpath file for context, and you can optionally also have it consider your data sample.

### Explain csvpath statements

AI will give you a complete narrative explanation for one or more csvpath statements in the open file. You can optionally also include a data sample for more context.

### Generate test data
e
Using one or more csvpath statements in the open file, the AI will generate sample data that the statements will validate. You can add your requirements to your request to get more targeted validations.

## Tracking

When you run an AI activity you are triggering a series of calls to the model's API. The model will respond in the background first. It asks FlightPath Data questions to clarify its approach. Its questions are technical and have exact answers. The AI often generates its own test data to check its work.

You can see these back and forth exchanges in the `Tracking` tab. The `Tracking` tab opens in the help and feedback try at the bottom of the middle of your screen when you click on your query in the AI tab. The contents of the `Tracking` tab is a JSON array where each question and answer between FlightPath Data and the AI are logged. You can see:
* The model you are working with
* Where each turn in the conversation between FlightPath and AI is stored
* The templates that were used to construct the FlightPath side of the exchange
* An errors count
* Estimated tokens consumed by the API call
* An estimated cost of the API call
* Timing for the call

The full call and response chain is available, should you wish to explore. The prompt templates are also available and can be customized.

