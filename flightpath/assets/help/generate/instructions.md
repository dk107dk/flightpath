## Instructions

Use this dialog to ask your AI to create one or more CsvPath Language validation statements. The statements will be based onthe sample data you provide and any instructions you include.

Your instructions can highlight aspects of your data you want to have checked. Instructions can look like:
```
   Make sure the average price of orders of widgets is less than $25.
```
Or:
```
   When city is Boston zipcode must start with 0.
```

Your requirements are sent to the AI configured in the Config panel's `llm` tab. The AI is allowed to check its answer using a CsvPath interpreter before returning its answer to you. That means you should get valid CsvPath Language statements back.

For an AI, CsvPath Language syntax is easy. What trips them up most is understanding your business rules. You must check the AI's work carefully. Even with the guardrails we put in place, mistakes and misunderstandings happen. It is best to think of the validation statements coming out of this feature as a quick start, not a finished product.

There are a few important things to be aware of:
* Your current file will be sampled. The sample is the first 50 or 100 lines. If sharing that data is not Ok, do not use this feature.
* The AI can iterate on its answer, using the CsvPath interpreter and reconsidering its answers. There is a limit on how many cycles it can execute. You set that limit in the `generator.ini`. Most AI API prices are very low, but the cycle limit helps protect you from unexpectedly heavy requests. You are, of course, responsible for API costs.
* Some AIs are more innately knowledgeable of CsvPath Language. Your results with Claude, for example, will typically be quite good. (This is true even when you simply use Claude's own app or website, as it already knows CsvPath Language). Other LLMs, particularly smaller self-hosted models, don't know the language and may struggle, even with the help we give them. We use local models in testing but would never use them for production quality answers.


