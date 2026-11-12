from typing import TYPE_CHECKING

from abb_rws_8.exceptions import RWS8Exception

if TYPE_CHECKING:
    from abb_rws_8.rws_client import RWSClient


class SubscriptionService:
    def __init__(self, rws_client: "RWSClient") -> None:
        self._rws_client = rws_client

    def subscribe_variable(self, task: str, module: str, variable: str) -> str:
        """Create a RAPID variable subscription and return its WebSocket location."""
        resource_path = f"/rw/rapid/symbol/RAPID/{task}/{module}/{variable}/data;value"
        form = {"resources": "1", "1": resource_path, "1-p": "1"}
        response = self._rws_client._post_form("/subscription", form)

        location = response.headers.get("Location")
        if location:
            return location
        raise RWS8Exception(
            f"Subscription response for {task}/{module}/{variable} "
            "is missing a non-empty Location header"
        )
