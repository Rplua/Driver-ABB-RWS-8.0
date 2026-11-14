# ABB RobotWare 8 RWS Driver

`abb-rws-8` is a synchronous Python driver for ABB OmniCore controllers running
RobotWare 8. It uses Robot Web Services (RWS) 2.0 over HTTPS and WebSockets.

**Validation status** — Tested only on a RobotStudio Virtual Controller.
Validation on a physical ABB controller is pending.

## Install

Requires Python 3.13 or later. From the repository root:

```bash
uv sync --locked
```

To add the driver to another Python project from a local checkout:

```bash
uv add /path/to/Driver-ABB-RWS-8.0
```

For subscriptions, also install `websockets>=15,<18` in the consuming project,
or use `uv run --with 'websockets>=15,<18'` when running the example.

## Read controller information

Set `ABB_RWS_URL` to the controller's HTTPS base URL, including its port when
needed, and `ABB_RWS_USER` to a controller account. The example prompts for
the password.

```python
from getpass import getpass
from os import environ

from abb_rws_8.rws_client import RWSClient

robot = RWSClient(
    base_url=environ["ABB_RWS_URL"],
    username=environ["ABB_RWS_USER"],
    password=getpass("Controller password: "),
)

try:
    status, services = robot.get_services()
    name, controller_type = robot.controller.get_identity()
    execution_state = robot.rapid.get_execution_state()
    print(status, services)
    print(name, controller_type, execution_state)

    value = robot.rapid.read_variable("T_ROB1", "CoordinationData", "test_value")
    print(value)
finally:
    try:
        robot.logout()
    finally:
        robot.close()
```

Each client shares one HTTP session and cookie jar across its services. TLS
verification defaults to on. Pass an `ssl.SSLContext` to trust a custom CA.
The controller's certificate must match the host in the URL. The bundled
examples use `verify=False` for the local virtual-controller lab.

## Available operations

| Domain | Driver interface |
| --- | --- |
| RobotWare discovery | `robot.get_services()` returns the HTTP status and installed services. |
| Controller | `robot.controller.get_identity()` returns the controller name and type. |
| RAPID data | `robot.rapid.read_variable(task, module, variable)` and `write_variable(task, module, variable, value)` use RAPID literals as strings, for example `"42"`, `"TRUE"` or `"[1,2,3]"`. |
| RAPID execution | `get_execution_state()`, `get_program_pointer(task)`, `set_program_pointer(task, module, routine)`, `reset_program_pointer()`, `start()` and `stop()` are available on `robot.rapid`. The pointer lookup returns the module, routine and line/column position. |
| Control Station | `robot.control_station` registers the remote station, checks its type or the current write access holder, requests/releases write access, and sets the station's motion control permission. |
| Subscriptions | `robot.subscription.subscribe_variable(task, module, variable)` opens a WebSocket and returns it to the caller. |

HTTP failures raise `RWSHTTPError` with a `status_code`. Connection and timeout
failures raise `RWSConnectionError` and `RWSTimeoutError`. All three inherit
from `RWS8Exception`.

## Write a RAPID variable

Use the same client for registration, write access and the write. The PIN is
the remote control station PIN configured on the controller. Configure
`ABB_RWS_PIN` before running this inside the session above.

```python
from uuid import uuid4

station = robot.control_station
station.register_remote(
    name="Python RWS",
    station_id=f"{{{uuid4()}}}",
    pincode=environ["ABB_RWS_PIN"],
)
station.request_write_access()
try:
    robot.rapid.write_variable("T_ROB1", "CoordinationData", "test_value", "42")
finally:
    station.release_write_access()
```

For execution on a virtual controller, hold write access and call
`station.allow_motion_control(True)` before remote `start()`. Set the
program pointer to the desired routine before the first start. `start()`
requests one cycle from the current pointer. After a program stop, read the
execution state and pointer, then call `start()` again to resume from there.

## Watch a RAPID variable

Run this inside the client session. Each event is the raw XHTML message from
RWS. The WebSocket stays open until the caller closes it or the connection
ends. Close it before logging out.

```python
with robot.subscription.subscribe_variable(
    "T_ROB1", "CoordinationData", "test_value"
) as websocket:
    for event in websocket:
        print(event)
```

From the repository root, run the [subscription example](examples/watch_rapid_variable.py):

```bash
uv run --with 'websockets>=15,<18' python examples/watch_rapid_variable.py
```

Edit `test_value` in RobotStudio to see an event. Press Ctrl+C to exit.

## RobotStudio virtual controller examples

Set `ABB_RWS_URL` before running either bundled script. For a VM with a
proxy on port 8001, replace `<vm-ip>` with your VM's IP address:

```bash
export ABB_RWS_URL='https://<vm-ip>:8001'
```

Adjust the examples' credentials and test PIN to match your environment. In the
Parallels setup, a Windows TCP proxy listens on the VM's shared-network IP
at port 8001 and forwards connections to the virtual controller at
`127.0.0.1:80` inside Windows.

On the `RandyTest` virtual controller, define `PERS num test_value := 0;`
in the `CoordinationData` module in `T_ROB1`. Load the following program
module and set the pointer to `main` in RobotStudio before running the
examples. Release RobotStudio's write access before running a write test.

```rapid
MODULE RwsPointerTest
    PROC main()
        WaitTime 1;
    ENDPROC

    PROC UWU()
        WaitTime 8;
        test_value := test_value + 1;
    ENDPROC
ENDMODULE
```

```bash
uv run python examples/read_controller.py
uv run python examples/read_controller.py --write-test
uv run python examples/read_controller.py --reset-pointer
uv run python examples/read_controller.py --set-pointer RwsPointerTest UWU
uv run python examples/read_controller.py --start-test
uv run python examples/read_controller.py --stop-resume-test
```

The stop/resume example observes RAPID running, stops during `WaitTime`, logs
where the pointer stopped, checks the counter is still unchanged, resumes and
checks that RAPID finishes with the counter incremented exactly once.

See the [ABB RobotWare 8 RWS documentation](https://robotwebservices.robotics.abb.com/introduction?parent=Getting+started&resourceVersion=rw8)
for controller-specific requirements and endpoint details.
