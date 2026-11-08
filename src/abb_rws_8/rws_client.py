import httpx
import ssl

class RWSClient:
    def __init__(self, base_url: str, username: str, password: str, verify: bool | ssl.SSLContext = True ) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password

        self._http_client: httpx.Client = httpx.Client(
            base_url=self.base_url,
            auth=httpx.BasicAuth(self.username, self.password),
            headers={"Accept": "application/hal+json;v=2.0"},
            timeout=5.0,
            verify=verify,
        )

    def get_services(self) -> tuple[int, list[str]]:
        response: httpx.Response = self._http_client.get("/rw")
        response.raise_for_status()
        resources = response.json()["_embedded"]["resources"]
        service_names: list[str] = []
        for service in resources:
            service_names.append(service["_title"])
        return response.status_code, service_names

    def close(self) -> None:
        self._http_client.close()
