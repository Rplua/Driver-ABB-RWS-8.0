from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abb_rws_8.rws_client import RWSClient


class ControllerService:
    """Operations belonging to ABB Controller Service."""

    def __init__(self, client: "RWSClient") -> None:
        self._client = client

    def get_identity(self) -> tuple[str, str]:
        """Return the controller name and type."""
        response = self._client._get("/ctrl/identity")
        states = response.json()["state"]
        identity = states[0]
        return identity["ctrl-name"], identity["ctrl-type"]
