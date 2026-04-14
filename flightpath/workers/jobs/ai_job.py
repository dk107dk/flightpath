import jsonpickle
import traceback

from flightpath_generator.client.run_tool import LiteLLMRunTool
from flightpath_generator.client.function_tool import LiteLLMFunctionTool

from flightpath.util.generator_utility import GeneratorUtility as geut
from flightpath.workers.jobs.job import Job


class AiJob(Job):
    def __init__(self, *, parent, main, mdata: dict):
        super().__init__(main=main)
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        self.parent = parent
        self.mdata = mdata
        self.path = mdata.get("params", {}).get("document_path")
        self.instructions = mdata.get("params", {}).get("instructions", "")
        self.on_turn_update = None
        self.on_complete = None
        self.on_error = None
        self._values = mdata.get("params", {})

    @property
    def values(self) -> dict[str, str]:
        return self._values

    @values.setter
    def values(self, vs: dict) -> None:
        self._values = vs

    def _on_generation(self, generation):
        if generation and self.on_turn_update:
            turns = generation.generator.get_turns(text_list=False)
            js = jsonpickle.encode(turns, unpicklable=False, indent=2)
            self.on_turn_update(js)

    def do_generate(self) -> None:
        try:
            tools = [
                LiteLLMRunTool().tool_definition(),
                LiteLLMFunctionTool().tool_definition(),
            ]
            generator = geut.new_generator(
                main=self.main, callbacks=[self._on_generation], tools=tools
            )
            generator.version_key = self.version

            context = generator.context_manager.get_context()
            prompt = generator.prompt_manager.create_prompt()
            #
            # need to create prompt rules replacement values and give them to the
            # prompt before the prompt is applied to the context
            #
            prompt.rules_values = self.values
            prompt.example_values = self.values
            #
            # context may have its own replacements. for now we just keep one batch
            # of replacement vars coming from the form properties.
            #
            context.background = self.values
            #
            # the prompt example is the csv or csvpath context
            #
            prompt.example = self.example
            #
            # the prompt rules are any instructions from the user
            #
            prompt.rules = self.instructions
            #
            # saving the prompt assembles it as JSON from the example, rules,
            # and a set of prompt components that are associated with each
            # version key; e.g. system prompts, examples, the csvpath grammar,
            # etc.
            #
            prompt.save()
            #
            # this sends the prompt to the API using LiteLLM. the generation
            # object is the set of all the inputs and outputs and logging for
            # one API call conversational turn. each turn creates a new generation
            # object. all the generations are saved, mostly as json, in a set
            # of several files.
            #
            generation = None
            generation = generator.do_send(
                context=context, prompt=prompt, datapath=self.path
            )
            #
            if generation:
                print(
                    f"done with generations: last generation: {generation}: {generation.name}"
                )
            else:
                raise ValueError("No generation returned")
            #
            # response_text is the plain text response from the assistant
            #
            if self.on_complete:
                print(
                    f"AiJob: calling back on_complete: {self.on_complete}: generation: {generation}"
                )
                self.on_complete(generation)
                print("AiJob: done with callback")
            else:
                raise Exception(
                    f"No on_complete call back set. Cannot handle final generation: {generation}."
                )
        except Exception as e:
            print(traceback.format_exc())
            if self.on_error:
                self.on_error(str(e))
            else:
                raise
