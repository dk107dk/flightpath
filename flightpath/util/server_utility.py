import httpx
import traceback


class ServerUtility:
    @classmethod
    def download_config(
        self, *, host: str, project: str, headers: dict[str, str]
    ) -> str:
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{host}/projects/get_project_config"
                request = {"name": project}
                response = client.post(url, json=request, headers=headers)
                content = response.json()
                return content
            except Exception as ex:
                print(traceback.format_exc())
                code = -1 if response is None else response.status_code
                msg = f"Error sending request ({code}): {ex}"
                print(msg)
                return None

    @classmethod
    def download_env(self, *, host: str, project: str, headers: dict[str, str]) -> str:
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{host}/projects/get_env_file"
                request = {"name": project}
                response = client.post(url, json=request, headers=headers)
                content = response.json()
                return content
            except Exception as ex:
                print(traceback.format_exc())
                code = -1 if response is None else response.status_code
                msg = f"Error sending request ({code}): {ex}"
                print(msg)
                return None
