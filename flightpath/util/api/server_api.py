from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Any, Self
import httpx
from flightpath.util.api import api_util as aput


class Result(NamedTuple):
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None


class ApiException(Exception): ...


class FlightPathServerApi(ABC):
    def __init__(self, host: str) -> None:
        if not host:
            raise ValueError("host is required")
        self._host = host
        self._key = None
        self._timeout = 5

    def __new__(cls, host: str) -> Self:
        #
        # callers call ping() first to check server is on
        # or defend against exceptions.
        #
        if cls == FlightPathServerApi:
            res = cls.discover(host)
            if res.success is False:
                raise ApiException(res[2])
            versions = res.data.get("message").get("api_versions")
            if versions is None:
                raise ApiException("Configuration returned does not include versions")
            if len(versions) == 0:
                raise ApiException("No versions available")
            #
            # versions must be whole integers. reasonable?
            #
            return aput.connect(host, versions)
        else:
            instance = super().__new__(cls)
            return instance

    # ====================
    # shared
    # ====================

    def _post(self, path: str, json: dict = None) -> Result:
        #
        # POST to `path` and normalize the outcome into a Result.
        # On a non-200 response, tries to pull a "detail" message out of the
        # JSON body; falls back to a generic message if that's not present
        # or the body isn't JSON.
        #
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(self._url(path), json=json, headers=self.headers)
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)

        return self._to_result(response)

    def _put(self, path: str, json: dict = None) -> Result:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.put(self._url(path), json=json, headers=self.headers)
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)
        return self._to_result(response)

    def _patch(self, path: str, json: dict = None) -> Result:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.patch(
                    self._url(path), json=json, headers=self.headers
                )
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)
        return self._to_result(response)

    def _get(self, path: str) -> Result:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(self._url(path), headers=self.headers)
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)
        return self._to_result(response)

    def _delete(self, path: str) -> Result:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.delete(self._url(path), headers=self.headers)
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)
        return self._to_result(response)

    def _to_result(self, response: httpx.Response) -> Result:
        if response.status_code > 199 and response.status_code < 300:
            try:
                return Result(True, response.json(), None, response.status_code)
            except ValueError:
                # not all 200s have a JSON body (e.g. plain ping)
                return Result(True, response.text, None, response.status_code)

        detail = None
        try:
            body = response.json()
            detail = body.get("detail") or body.get("message")
        except ValueError:
            pass

        msg = f"Server response: {response.status_code}"
        if detail:
            msg = f"{msg}: {detail}"
        return Result(False, None, msg, response.status_code)

    @property
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, host) -> None:
        self._host = host

    @property
    def key(self) -> str:
        return self._key

    @key.setter
    def key(self, key: str) -> None:
        self._key = key

    @property
    def headers(self) -> dict:
        return {"access_token": self._key, "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        return f"{self.host}/{path.lstrip('/')}"

    @classmethod
    def discover(cls, host: str) -> Result:
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(
                    host, headers={"Content-Type": "application/json"}
                )
            if response.status_code == 200:
                return Result(True, response.json(), None, response.status_code)
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)
        except Exception as ex:
            return Result(False, None, f"Unknown error: {ex}", -1)

    @classmethod
    def ping(cls, host: str) -> Result:
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(
                    host, headers={"Content-Type": "application/json"}
                )
            if response.status_code == 200:
                return Result(True, response.json(), None, response.status_code)
        except httpx.HTTPError as ex:
            return Result(False, None, f"Error sending request: {ex}", -1)
        except Exception as ex:
            return Result(False, None, f"Unknown error: {ex}", -1)

    # ====================
    # api
    # ====================

    """
    One method per server activity. Concrete subclasses (v1, v2, ...) decide
    how each activity maps to actual HTTP calls. Every method returns a
    Result -- never raises for ordinary failure modes (bad status code,
    connection error, malformed response). Implementations should reserve
    raised exceptions for programmer error (e.g. missing required args),
    not for "the server said no."
    """

    @abstractmethod
    def create_key(self, owner: str, owner_contact: str, key_name: str) -> Result:
        """Create a regular or admin key"""

    @abstractmethod
    def upload_env(self, name: str, env_str: str) -> Result:
        """Upload an env file for project `name`."""

    @abstractmethod
    def upload_config(self, name: str, config_str: str) -> Result:
        """Upload a project config for project `name`."""

    @abstractmethod
    def shutdown(self) -> Result:
        """Ask the server to shut down. data is the server's response message."""

    @abstractmethod
    def download_log(self, name: str) -> Result:
        """Download the csvpath.log for project `name`. data is the decoded log text."""

    @abstractmethod
    def download_config(self, name: str) -> Result:
        """Download the project config for project `name`. data is the config content."""

    @abstractmethod
    def download_env(self, name: str) -> Result:
        """Download the env file for project `name`. data is the env content."""

    @abstractmethod
    def get_project_names(self) -> Result:
        """List all project names known to the server. data is a list[str]."""

    @abstractmethod
    def delete_project(self, name: str) -> Result:
        """Delete project `name`."""

    @abstractmethod
    def create_project(self, name: str, config_str: str) -> Result:
        """Create a new project `name` with the given config."""
