import logging
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from abb_rws_8.exceptions import RWS8Exception

if TYPE_CHECKING:
    from websockets.sync.client import ClientConnection

    from abb_rws_8.rws_client import RWSClient


logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, rws_client: "RWSClient") -> None:
        self._rws_client = rws_client

    def subscribe_variable(
        self, task: str, module: str, variable: str
    ) -> "ClientConnection":
        """Subscribe to a RAPID variable and return its open WebSocket."""
        from websockets.sync.client import connect

        resource_path = f"/rw/rapid/symbol/RAPID/{task}/{module}/{variable}/data;value"
        form = {"resources": "1", "1": resource_path, "1-p": "1"}
        response = self._rws_client._post_form("/subscription", form)

        location = response.headers.get("Location")
        if location:
            websocket_url = self._websocket_url(location)
            cookie_header = self._get_cookie_header(websocket_url)
            logger.debug("Opening subscription WebSocket at %s", websocket_url)
            return connect(
                websocket_url,
                ssl=self._rws_client._websocket_tls,
                subprotocols=["rws_subscription"],
                additional_headers={"Cookie": cookie_header},
                proxy=None,
                open_timeout=5,
            )
        raise RWS8Exception(
            f"Subscription response for {task}/{module}/{variable} "
            "is missing a non-empty Location header"
        )

    def _websocket_url(self, location: str) -> str:
        poll_path = urlsplit(location)
        if not poll_path.path.startswith("/poll/"):
            raise RWS8Exception("Subscription did not return a WebSocket polling path")


        endpoint = urlsplit(self._rws_client.base_url)
        return urlunsplit(("wss", endpoint.netloc, poll_path.path, poll_path.query, ""))


    def _get_cookie_header(self, websocket_url: str) -> str:
        get_url = urlsplit(websocket_url)
        new_url = urlunsplit(("https", get_url.netloc, get_url.path, get_url.query, ""))
        cookie_header =  self._rws_client._http_client.build_request("GET", new_url).headers.get("Cookie")
        if cookie_header:
            return cookie_header
        raise RWS8Exception("No session cookies found for the WebSocket connection")
