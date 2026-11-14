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

    def write_variable(self, task: str, module: str, variable: str, value: str) -> None:
        self.rws_client._post_form(f"rw/rapid/symbol/RAPID/{task}/{module}/{variable}/data", data={"value": value})

    def get_program_pointer(self, task: str) -> tuple[str, str, str]:
        response = self.rws_client._get(f"/rw/rapid/tasks/{task}/pcp")
        state = response.json()["state"]
        for entry in state:
            if entry.get("_title") == "progpointer":
                break
        else:
            raise RWS8Exception(f"Program pointer entry not found for task {task}")

        try:
            return entry["modulemame"], entry["routinename"], entry["beginposition"]
        except KeyError as error:
            raise RWS8Exception(
                f"Program pointer position unavailable for task {task}"
            ) from error

    def reset_program_pointer(self) -> None:
        self.rws_client._post_form("/rw/rapid/execution/resetpp", data={})

    def set_program_pointer(self, task: str, module: str, routine: str) -> None:
        self.rws_client._post_form(
            f"/rw/rapid/tasks/{task}/pcp/routine-from-url",
            data={"routineurl": f"/RAPID/{task}/{module}/{routine}", "userlevel": "false"},
        )

    def start(self) -> None:
        self.rws_client._post_form(
            "/rw/rapid/execution/start",
            data={
                "regain": "continue",
                "execmode": "continue",
                "cycle": "once",
                "condition": "none",
                "stopatbp": "disabled",
                "alltaskbytsp": "false",
            },
        )

    def get_execution_state(self) -> str:
        """Return the controller's RAPID execution state."""
        response = self.rws_client._get("/rw/rapid/execution")
        for entry in response.json()["state"]:
            state = entry.get("ctrlexecstate")
            if isinstance(state, str) and state:
                return state
        raise RWS8Exception("RAPID execution state not found")

    def stop(self) -> None:
        """Request a RAPID program stop so execution can resume with start()."""
        self.rws_client._post_form(
            "/rw/rapid/execution/stop",
            data={"stopmode": "stop", "usetsp": "normal"},
        )
