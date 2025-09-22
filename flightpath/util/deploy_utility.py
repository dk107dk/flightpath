import io
from configparser import ConfigParser


class DeployUtility:

    @classmethod
    def stringify(self, config:ConfigParser) -> str:
        string_buffer = io.StringIO()
        config.write(string_buffer)
        config_str = string_buffer.getvalue()
        return config_str

    @classmethod
    def configify(self, config_str:str) -> ConfigParser:
        if config_str is None:
            raise ValueError("Config string cannot be None")
        c = ConfigParser()
        c.read_string(config_str)
        return c

    @classmethod
    def make_deployable(cls, config_str:str) -> str:
        if config_str is None:
            raise ValueError("Config string cannot be None")
        #
        # if the config_str is going to FlightPath Server it will be reworked there too.
        # the server will change the paths to match the server-side project, and it will
        # make sure the path separators are correct for the OS. here we're just setting
        # the defaults for those items that need to be defaulted and switching on/off anything
        # that should be off.
        #
        config = cls.configify(config_str)
        config["config"]["path"] = "config/config.ini"
        config["config"]["allow_var_sub"] = "yes"
        config["config"]["var_sub_source"] = "config/env.json"
        config["cache"]["path"] = "cache"
        config["logging"]["log_file"] = "logs/csvpath.log"
        config["sqlite"]["db"] = "archive/csvpath.db"
        #
        # policing the sql access is hard so let's make an
        # admin handle it another way, at least for now.
        #
        config["sql"]["connection_string"] = ""
        #
        # assuming we're not deploying this config in another FlightPath Data or
        # CsvPath project, we don't need to know the server it's going into.
        #
        config["server"]["host"] = ""
        config["server"]["api_key"] = ""
        config["functions"]["imports"] = ""
        #
        # http(s) is a malware risk. local is a cross-project security risk.
        #
        config["inputs"]["allow_http_files"] = "no"
        config["inputs"]["allow_local_files"] = "no"

        return cls.stringify(config)


