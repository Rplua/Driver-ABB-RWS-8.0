from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from abb_rws_8.rws_client import RWSClient

class ControlStationService:
    def __init__(self, client: "RWSClient") -> None:
        self._client = client

    def get_write_access_holder(self) -> tuple[str, str] | None:
        response = self._client._get("/rw/controlstation/writeaccess/status")
        states = response.json()["state"]
        state = states[0]
        held = state["control-station-write-access-held"]
        if  held == "false":
            return
        control_names = (state["held-by-control-station-Id"],state["held-by-control-station-name"])
        return  control_names

    def get_station_type(self) -> str :
        response = self._client._get("/rw/controlstation/type")
        states = response.json()["state"]
        state = states[0]
        return state["control-station-type"]

    def register_remote(self, name: str, station_id: str, pincode: str) -> None:
        self._client._post_form(
            "/rw/controlstation/register/remote",
            data={
                "control-station-name": name,
                "control-station-id": station_id,
                "pincode": pincode,
            },
        )
    def request_write_access(self) -> None:
        self._client._post_form("/rw/controlstation/writeaccess/request", data={})

    def release_write_access(self) -> None:
        self._client._post_form("/rw/controlstation/writeaccess/release", data={})