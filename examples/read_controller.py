import logging

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
    name, controller_type = robot.controller.get_identity()
    logger.info("Controller name: %s", name)
    logger.info("Controller type: %s", controller_type)

    logger.info("HTTP status: %s", status_code)
    for service in services:
        logger.info("RobotWare service: %s", service)

    variables = (
        "test_value",
        "test_number",
        "test_true",
        "test_false",
        "test_text",
        "test_numbers",
        "test_record",
        "test_records",
    )
    for variable in variables:
        try:
            value = robot.rapid.read_variable(
                task="T_ROB1",
                module="CoordinationData",
                variable=variable,
            )
            logger.info("%s = %r (%s)", variable, value, type(value).__name__)
        except RWS8Exception as error:
            logger.error("Failed to read %s: %s", variable, error)
except RWS8Exception as error:
    logger.error("RWS operation failed: %s", error)
finally:
    robot.close()
