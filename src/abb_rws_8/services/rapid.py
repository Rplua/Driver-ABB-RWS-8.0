from typing import TYPE_CHECKING

from abb_rws_8.exceptions import RWS8Exception

if TYPE_CHECKING:
    from abb_rws_8.rws_client import RWSClient


class RapidService:
    def __init__(self, rws_client: "RWSClient") -> None:
        self.rws_client = rws_client

    def read_variable(self, task: str, module: str, variable: str) -> str:
        response = self.rws_client._get(f"/rw/rapid/symbol/RAPID/{task}/{module}/{variable}/data")
        state = response.json()["state"]

        for entry in state:
            if entry["_type"] == "rap-data":
                return entry["value"]
        raise RWS8Exception("RAPID variable value not found")
