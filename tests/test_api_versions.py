import unittest
import pytest

from flightpath.util.api import api_util as aput
from flightpath.util.api.server_api import ApiException, FlightPathServerApi
from flightpath.util.api.v1 import FlightPathServerApiV1


class TestApiVersions(unittest.TestCase):
    def test_parsed_versions_1(self) -> None:
        vs = aput._parse_versions(["v1", "v2"])
        assert vs == [2, 1]

        vs = aput._parse_versions(["v15", "v2", "v1", "v0", "v10"])
        assert vs == [15, 10, 2, 1, 0]

    def test_parsed_versions_2(self) -> None:
        with pytest.raises(ApiException):
            aput._parse_versions(["v1.5", "v2", "v1", "v0"])

    def test_versions_instance_1(self) -> None:
        versions = ["v1"]
        api = aput.connect("http://localhost:8000", versions)
        assert api is not None
        assert isinstance(api, FlightPathServerApi)
        assert isinstance(api, FlightPathServerApiV1)

    def test_versions_instance_2(self) -> None:
        versions = ["v1000"]
        with pytest.raises(ApiException):
            aput.connect("http://localhost:8000", versions)
