import base64

from .server_api import FlightPathServerApi, Result


class FlightPathServerApiV1(FlightPathServerApi):
    def __init__(self, host: str) -> None:
        super().__init__(host)

    def create_key(self, owner: str, owner_contact: str, key_name: str) -> Result:
        request = {
            "key_name": key_name,
            "key_owner_name": owner,
            "key_owner_contact": owner_contact,
        }
        return self._post("admin/new_key", json=request)

    def upload_env(self, name: str, env_str: str) -> Result:
        request = {"name": name, "env_str": env_str}
        return self._post("projects/set_env_file", json=request)

    def upload_config(self, name: str, config_str: str) -> Result:
        request = {"name": name, "config_str": config_str}
        return self._post("projects/set_project_config", json=request)

    def shutdown(self) -> Result:
        return self._get("admin/shutdown")

    def download_log(self, name: str) -> Result:
        request = {"name": name, "file_path": "logs/csvpath.log"}
        success, data, error_message, status_code = self._post(
            "projects/get_file", json=request
        )
        if not success:
            return Result(success, data, error_message, status_code)
        log = data.get("file_content") if isinstance(data, dict) else None
        if log is None:
            return Result(False, None, "Response did not include file_content")
        try:
            log = base64.b64decode(log).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as ex:
            return Result(
                False, None, f"Could not decode log content: {ex}", status_code
            )
        return Result(True, log, None, status_code)

    def download_config(self, name: str) -> Result:
        return self._post("projects/get_project_config", json={"name": name})

    def download_env(self, name: str) -> Result:
        return self._post("projects/get_env_file", json={"name": name})

    def get_project_names(self) -> Result:
        success, data, error_message, status_code = self._post(
            "projects/get_project_names", json={}
        )
        if not success:
            return Result(success, data, error_message, status_code)
        if isinstance(data, dict) and "names" in data:
            return Result(True, data["names"], status_code)
        return Result(False, None, f"Unexpected response: {data}", status_code)

    def delete_project(self, name: str) -> Result:
        return self._post("projects/delete_project", json={"name": name})

    def create_project(self, name: str, config_str: str) -> Result:
        request = {"name": name, "config_str": config_str}
        return self._post("projects/new_project", json=request)
