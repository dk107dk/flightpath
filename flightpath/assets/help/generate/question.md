## Question

Use this dialog to ask your AI a question about CsvPath Language. Your AI is determined by the settings in the `llm` tab in the Config panel.

You can ask questions like:
```
   What is the average value of all prices from orders in EU countries?
```
Or:
```
   How can I get a count of the number of times a value appears in a header?
```
You can ask anything you need to know about how to use the language.

Your question is sent to the AI configured in `llm`. The AI is allowed to check its answer using a CsvPath interpreter before returning it to you. That means you should get valid CsvPath Language statements back. However, all AIs are fallible. You must check their work. Even with the guardrails we put in place, mistakes happen.

There are a few important things to be aware of:
* Your current file will be sampled. The sample is the first 50 or 100 lines. When you click the `Answer` button the sample is sent to the AI. If that sharing is not Ok for your data, do not use this feature.
* The AI can iterate on its answer, using the CsvPath interpreter and reconsidering its answers. There is a limit on how many cycles it can execute. You set that limit in the `generator.ini`. Most AI API prices are very low, but the cycle limit helps protect you from unexpectedly heavy requests. You are, of course, responsible for API costs.
* Some AIs are more innately knowledgeable of CsvPath Language. Your results with Claude, for example, will typically be quite good. (This is true even when you simply use Claude's own app or website, as it already knows CsvPath Language). Other LLMs, particularly smaller self-hosted models, don't know the language and may struggle, even with the help we give them. We use local models in testing but would never use them for production quality answers.


