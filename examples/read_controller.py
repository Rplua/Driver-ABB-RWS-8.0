import logging
from argparse import ArgumentParser
from decimal import Decimal
from os import environ
from time import monotonic, sleep
from uuid import uuid4

import httpx

from abb_rws_8.exceptions import RWS8Exception
from abb_rws_8.rws_client import RWSClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def wait_for_execution_state(expected: str, timeout: float = 5) -> None:
    deadline = monotonic() + timeout
    while True:
        state = robot.rapid_service.get_execution_state()
        if state == expected:
            logger.info("RAPID execution state: %s", state)
            return
        if monotonic() >= deadline:
            raise RWS8Exception(f"Expected RAPID state {expected!r}, last observed {state!r}")
        sleep(0.2)


parser = ArgumentParser(description="Read controller information and the RAPID program pointer.")
test_mode = parser.add_mutually_exclusive_group()
test_mode.add_argument(
    "--write-test",
    action="store_true",
    help="Also write and read back test_value on the virtual controller.",
)
test_mode.add_argument(
    "--reset-pointer",
    action="store_true",
    help="Reset the program pointer to main on the stopped virtual controller.",
)
test_mode.add_argument(
    "--set-pointer",
    nargs=2,
    metavar=("MODULE", "ROUTINE"),
    help="Set the T_ROB1 program pointer on the stopped virtual controller.",
)
test_mode.add_argument(
    "--start-test",
    action="store_true",
    help="Run RwsPointerTest.UWU once on RandyTest and verify test_value.",
)
test_mode.add_argument(
    "--stop-resume-test",
    action="store_true",
    help="Stop RwsPointerTest.UWU during WaitTime and resume it on RandyTest.",
)
args = parser.parse_args()
run_test = args.start_test or args.stop_resume_test

base_url = environ.get("ABB_RWS_URL")
if not base_url:
    parser.error("Set ABB_RWS_URL to the controller HTTPS base URL.")
username: str = "admin"
password: str = "robotics"
robot = RWSClient(base_url=base_url, username=username, password=password, verify=False)

try:
    status_code, services = robot.get_services()
    name, controller_type = robot.controller_service.get_identity()
    holder = robot.control_station.get_write_access_holder()
    control_type = robot.control_station.get_station_type()
    logger.info("Controller name: %s", name)
    logger.info("Controller type: %s", controller_type)
    logger.info("HTTP status: %s", status_code)
    logger.info("Write access holder: %s", holder)
    logger.info("Control station type before registration: %s", control_type)
    for service in services:
        logger.info("RobotWare service: %s", service)

    value = robot.rapid_service.read_variable(
        task="T_ROB1",
        module="CoordinationData",
        variable="test_value",
    )
    logger.info("test_value = %r", value)

    module, routine, position = robot.rapid_service.get_program_pointer("T_ROB1")
    logger.info("Program pointer for T_ROB1 before any change: %s.%s at %s", module, routine, position)

    if run_test and (name, controller_type) != ("RandyTest", "VIRTUAL_CONTROLLER"):
        raise RWS8Exception("The execution tests require the RandyTest virtual controller.")

    target = args.set_pointer
    if run_test:
        wait_for_execution_state("stopped")
        target = ("RwsPointerTest", "UWU")
        expected_value = Decimal(value) + 1

    if args.write_test or args.reset_pointer or target:
        station_id = f"{{{uuid4()}}}"
        robot.control_station.register_remote(
            name="Python RWS Test",
            station_id=station_id,
            pincode="1234",
        )
        registered_type = robot.control_station.get_station_type()
        logger.info("Control station type after registration: %s", registered_type)

        robot.control_station.request_write_access()
        try:
            holder = robot.control_station.get_write_access_holder()
            if holder is None or holder[0].casefold() != station_id.casefold():
                raise RWS8Exception(
                    f"Could not verify write access for this station. Current holder: {holder!r}"
                )
            logger.info("Write access confirmed for %s (%s)", holder[1], holder[0])
            if args.reset_pointer:
                robot.rapid_service.reset_program_pointer()
                module, routine, position = robot.rapid_service.get_program_pointer("T_ROB1")
                logger.info("Program pointer for T_ROB1 after reset: %s.%s at %s", module, routine, position)
            elif target:
                target_module, target_routine = target
                robot.rapid_service.set_program_pointer("T_ROB1", target_module, target_routine)
                module, routine, position = robot.rapid_service.get_program_pointer("T_ROB1")
                logger.info("Program pointer for T_ROB1 after set: %s.%s at %s", module, routine, position)
                if (module.casefold(), routine.casefold()) != (
                    target_module.casefold(), target_routine.casefold()
                ):
                    raise RWS8Exception(
                        f"Expected program pointer at {target_module}.{target_routine}, "
                        f"got {module}.{routine}"
                    )
                if run_test:
                    robot.control_station.allow_motion_control(True)
                    logger.info("Motion control allowed for this remote station")
                    robot.rapid_service.start()
                    if args.stop_resume_test:
                        wait_for_execution_state("running")
                        robot.rapid_service.stop()
                        wait_for_execution_state("stopped")
                        stopped_module, stopped_routine, stopped_position = (
                            robot.rapid_service.get_program_pointer("T_ROB1")
                        )
                        logger.info(
                            "Program pointer after stop: %s.%s at %s",
                            stopped_module, stopped_routine, stopped_position,
                        )
                        if (stopped_module.casefold(), stopped_routine.casefold()) != (
                            target_module.casefold(), target_routine.casefold()
                        ):
                            raise RWS8Exception("Program pointer left the test routine before stop")
                        stopped_value = robot.rapid_service.read_variable(
                            "T_ROB1", "CoordinationData", "test_value"
                        )
                        if Decimal(stopped_value) != Decimal(value):
                            raise RWS8Exception(
                                f"test_value changed before resume: {value!r} -> {stopped_value!r}. "
                                "Check that WaitTime precedes the increment in the loaded UWU routine."
                            )

                        logger.info("Resuming RAPID from the stopped program pointer")
                        robot.rapid_service.start()

                    deadline = monotonic() + 15
                    while monotonic() < deadline:
                        updated_value = robot.rapid_service.read_variable(
                            "T_ROB1", "CoordinationData", "test_value"
                        )
                        if Decimal(updated_value) == expected_value:
                            if args.stop_resume_test:
                                wait_for_execution_state("stopped")
                                final_value = robot.rapid_service.read_variable(
                                    "T_ROB1", "CoordinationData", "test_value"
                                )
                                if Decimal(final_value) != expected_value:
                                    raise RWS8Exception(
                                        f"Expected final test_value {expected_value}, got {final_value}"
                                    )
                            logger.info("test_value after start = %s (before: %s)", updated_value, value)
                            break
                        sleep(0.2)
                    else:
                        raise RWS8Exception(
                            f"Expected test_value to reach {expected_value} after start"
                        )
            else:
                robot.rapid_service.write_variable(
                    task="T_ROB1",
                    module="CoordinationData",
                    variable="test_value",
                    value="11",
                )
                written_value = robot.rapid_service.read_variable(
                    task="T_ROB1",
                    module="CoordinationData",
                    variable="test_value",
                )
                logger.info("test_value after write = %r", written_value)
        finally:
            robot.control_station.release_write_access()
            logger.info("Write access released")
except RWS8Exception as error:
    logger.error("RWS operation failed: %s", error)
    if isinstance(error.__cause__, httpx.HTTPStatusError):
        logger.error("Controller error response: %s", error.__cause__.response.text)
    raise SystemExit(1) from None
finally:
    try:
        robot.logout()
    except RWS8Exception as error:
        logger.warning("Controller logout failed: %s", error)
    finally:
        robot.close()
