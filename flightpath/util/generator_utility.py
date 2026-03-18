import os
from typing import Callable

from flightpath_generator import Generator
from flightpath_generator.util.config import Config as GeneratorConfig

class GeneratorUtility:

    @classmethod
    def new_generator_config(cls, main) -> GeneratorConfig:
        cc = main.csvpath_config
        path = os.path.dirname(cc.configpath)
        path = os.path.join(path, "generator.ini")
        config = GeneratorConfig(cfg=cc, configpath=path)
        return config

    @classmethod
    def new_generator(cls, *, main, callbacks:list[Callable]=None, tools:list=None) -> Generator:
        config = cls.new_generator_config(main)
        generator = Generator(config)
        for c in callbacks if callbacks else []:
            generator.add_callback(c)
        generator.csvpath_config = main.csvpath_config
        generator.csvpath_logger = main.logger
        generator.tools = tools
        return generator


