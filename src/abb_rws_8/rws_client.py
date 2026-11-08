import httpx


class RWSClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self._http_client: httpx.Client = httpx.Client(
            base_url=self.base_url,
            auth=httpx.BasicAuth(self.username, self.password),
            headers={"Accept": "application/hal+json;v=2.0"},
            timeout=5.0,
        )

    def get_services(self) -> str:
        return self.base_url + "/rw"

    def close(self) -> None:
        self._http_client.close()
