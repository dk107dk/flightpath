from typing import Callable

from flightpath_generator import Generator
from flightpath_generator.util.config import Config as GeneratorConfig
from flightpath_generator.util.generator_utility import (
    GeneratorUtility as FlightPathGeneratorUtility,
)


class GeneratorUtility:
    @classmethod
    def new_generator_config(cls, main) -> GeneratorConfig:
        cc = main.csvpath_config
        return FlightPathGeneratorUtility.new_generator_config(cc)

    @classmethod
    def new_generator(
        cls, *, main, callbacks: list[Callable] = None, tools: list = None
    ) -> Generator:
        config = cls.new_generator_config(main)
        generator = Generator(config)
        for c in callbacks if callbacks else []:
            generator.add_callback(c)
        generator.csvpath_config = main.csvpath_config
        generator.csvpath_logger = main.logger
        generator.tools = tools
        return generator
