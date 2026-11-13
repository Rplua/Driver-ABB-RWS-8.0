import ssl

import httpx

from abb_rws_8.exceptions import RWSConnectionError, RWSHTTPError, RWSTimeoutError
from abb_rws_8.services.controller import ControllerService
from abb_rws_8.services.rapid import RapidService
from abb_rws_8.services.subscription import SubscriptionService


class RWSClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify: bool | ssl.SSLContext = True,
    ) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self._websocket_tls = verify if isinstance(verify, ssl.SSLContext) else None
        if verify is False:
            self._websocket_tls = ssl.create_default_context()
            self._websocket_tls.check_hostname = False
            self._websocket_tls.verify_mode = ssl.CERT_NONE
        self._http_client: httpx.Client = httpx.Client(
            base_url=self.base_url,
            auth=httpx.BasicAuth(self.username, self.password),
            headers={"Accept": "application/hal+json;v=2.0"},
            timeout=5.0,
            verify=verify,
        )
        self.controller = ControllerService(self)
        self.rapid = RapidService(self)
        self.subscription = SubscriptionService(self)

    def _get(
        self, resource_path: str, *, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        """Send a GET request and translate HTTPX failures into driver errors."""
        try:
            response = self._http_client.get(resource_path, headers=headers)
        except httpx.TimeoutException as err:
            raise RWSTimeoutError(f"Request timed out: GET {resource_path}") from err
        except httpx.ConnectError as err:
            raise RWSConnectionError("Failed to connect to the controller") from err

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise RWSHTTPError(
                status_code=response.status_code,
                message=f"GET {resource_path} failed with HTTP {response.status_code}",
            ) from err
        return response

    def get_services(self) -> tuple[int, list[str]]:
        response = self._get("/rw")
        resources = response.json()["_embedded"]["resources"]
        service_names: list[str] = []
        for service in resources:
            service_names.append(service["_title"])
        return response.status_code, service_names

    def _post_form(self, path: str, data: dict[str,str]) -> httpx.Response:
        """Send a POST request and translate HTTPX failures into driver errors."""
        try:
            response = self._http_client.post(path, data=data, headers={
                "Accept": "application/xhtml+xml;v=2.0",
                "Content-Type": "application/x-www-form-urlencoded;v=2.0",
            })
        except httpx.TimeoutException as err:
            raise RWSTimeoutError(f"Request timed out: POST {path}") from err
        except httpx.ConnectError as err:
            raise RWSConnectionError("Failed to connect to the controller") from err
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            raise RWSHTTPError(
                status_code=response.status_code,
                message=f"Post {path} failed with HTTP {response.status_code}",
            )from err
        return response

    def logout(self) -> None:
        """End the current controller session and clear its cookies."""
        if self._http_client.cookies:
            self._get("/logout", headers={"Accept": "application/xhtml+xml;v=2.0"})
            self._http_client.cookies.clear()

    def close(self) -> None:
        self._http_client.close()
