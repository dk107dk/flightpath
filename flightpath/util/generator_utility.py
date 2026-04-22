from typing import Callable

from flightpath_generator import Generator
from flightpath_generator.util.config import Config as GeneratorConfig
from flightpath_generator.util.generator_utility import (
    GeneratorUtility as FlightPathGeneratorUtility,
)

from flightpath_generator.client.tools import GeneratorTool
from flightpath_generator.client.run_tool import LiteLLMRunTool
from flightpath_generator.client.function_tool import LiteLLMFunctionTool


class GeneratorUtility:
    @classmethod
    def new_generator_config(cls, main) -> GeneratorConfig:
        cc = main.csvpath_config
        return FlightPathGeneratorUtility.new_generator_config(cc)

    @classmethod
    def new_generator(
        cls, *, main, callbacks: list[Callable] = None, additional_tools: list = None
    ) -> Generator:
        config = cls.new_generator_config(main)
        generator = Generator(config)
        for c in callbacks if callbacks else []:
            generator.add_callback(c)
        generator.csvpath_config = main.csvpath_config
        generator.csvpath_logger = main.logger
        tools = [] if additional_tools is None else additional_tools
        tools += cls.std_tools()
        generator.tools = tools
        return generator

    @classmethod
    def std_tools(cls) -> list[GeneratorTool]:
        tools = [
            LiteLLMRunTool().tool_definition(),
            LiteLLMFunctionTool().tool_definition(),
        ]
        return tools
