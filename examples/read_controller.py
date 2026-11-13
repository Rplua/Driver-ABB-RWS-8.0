import logging
from uuid import uuid4

import httpx

from abb_rws_8.exceptions import RWS8Exception
from abb_rws_8.rws_client import RWSClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

base_url: str = "https://10.211.55.4:8001"
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
finally:
    try:
        robot.logout()
    except RWS8Exception as error:
        logger.warning("Controller logout failed: %s", error)
    finally:
        robot.close()
