import os
import jsonpickle
import traceback

from flightpath_generator.client.run_tool import LiteLLMRunTool
from flightpath_generator.client.function_tool import LiteLLMFunctionTool

from flightpath.util.generator_utility import GeneratorUtility as geut
from flightpath.workers.jobs.job import Job

class AiGenerateCsvpathJob(Job):

    def __init__(self, *, parent, main, mdata:dict):
        super().__init__(main=main)
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        self.parent = parent
        self.mdata = mdata
        self.path = mdata.get("params", {}).get("document_path")
        self.instructions = mdata.get("params", {}).get("body", "")
        self.on_turn_update = None
        self.on_complete = None
        self.on_error = None

    @property
    def example(self) -> None:
        if self.path is None:
            return ""
        lines = []
        with open(self.path, "r") as file:
            for i, line in enumerate(file):
                lines.append(line)
                #
                # we don't have a chosen number of lines yet
                #
                if i > 20:
                    break
        return "\n".join(lines)

    def _on_generation(self, generation):
            if generation and self.on_turn_update:
                turns = generation.generator.get_turns(text_list=False)
                js = jsonpickle.encode(turns, unpicklable=False, indent=2)
                self.on_turn_update(js)

    def do_generate(self) -> None:
        print(f"job: do_generate: starting")
        try:
            tools = [
                LiteLLMRunTool().tool_definition(),
                LiteLLMFunctionTool().tool_definition()
            ]
            generator = geut.new_generator(main=self.main, callbacks=[self._on_generation], tools=tools)
            generator.version_key="validation"

            context = generator.context_manager.get_context()
            prompt = generator.prompt_manager.create_prompt()
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
            generation = generator.do_send(context=context, prompt=prompt, datapath=self.path)
            #
            # response_text is the plain text response from the assistant
            #
            text = generation.response_text
            if self.on_complete:
                self.on_complete(text)

        except Exception as e:
            print(traceback.format_exc())
            if self.on_error:
                self.on_error(str(e))





