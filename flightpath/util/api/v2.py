import base64

from .server_api import FlightPathServerApi, Result


class FlightPathServerApiV2(FlightPathServerApi):
    def __init__(self, host: str) -> None:
        super().__init__(host)

    def create_key(self, owner: str, owner_contact: str, key_name: str) -> Result:
        request = {
            "key_name": key_name,
            "key_owner_name": owner,
            "key_owner_contact": owner_contact,
        }
        return self._post("v2/admin/keys", json=request)

    def upload_env(self, name: str, env_str: str) -> Result:
        request = {"value": env_str}
        return self._put(f"v2/projects/{name}/env", json=request)

    def upload_config(self, name: str, config_str: str) -> Result:
        request = {"value": config_str}
        return self._put(f"v2/projects/{name}/config", json=request)

    def shutdown(self) -> Result:
        return self._post("v2/admin/shutdown")

    def download_log(self, name: str) -> Result:
        # request = {"name": name, "file_path": "logs/csvpath.log"}
        success, data, error_message, status_code = self._get(
            "/v2/projects/{name}/files/logs/csvpath.log"
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
        result = self._get(f"/v2/projects/{name}/config")
        if result.success:
            result = result._replace(data=result.data.get("value"))
        return result

    def download_env(self, name: str) -> Result:
        result = self._get(f"/v2/projects/{name}/env")
        if result.success:
            result = result._replace(data=result.data.get("value"))
        return result

    def get_project_names(self) -> Result:
        success, data, error_message, status_code = self._get("v2/projects")
        if not success:
            return Result(success, data, error_message, status_code)
        if isinstance(data, dict) and "names" in data:
            return Result(True, data["names"], status_code)
        return Result(False, None, f"Unexpected response: {data}", status_code)

    def delete_project(self, name: str) -> Result:
        return self._delete(f"v2/projects/{name}")

    def create_project(self, name: str, config_str: str) -> Result:
        request = {"name": name, "config_str": config_str}
        return self._post("v2/projects", json=request)
