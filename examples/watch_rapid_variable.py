import logging
from getpass import getpass

from websockets.exceptions import WebSocketException

from abb_rws_8.exceptions import RWS8Exception
from abb_rws_8.rws_client import RWSClient

BASE_URL = "https://10.211.55.4:8001"
logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    password = getpass("Controller password for admin: ")

    # The virtual controller uses a certificate that isn't trusted by this Mac.
    robot = RWSClient(
        base_url=BASE_URL,
        username="admin",
        password=password,
        verify=False,
    )
    try:
        with robot.subscription.subscribe_variable(
            task="T_ROB1",
            module="CoordinationData",
            variable="test_value",
        ) as websocket:
            logger.info("Connected. Change test_value in RobotStudio. Press Ctrl+C to stop.")
            for event in websocket:
                logger.info("RAPID event: %s", event)
        return 0
    except KeyboardInterrupt:
        return 0
    except (RWS8Exception, WebSocketException, OSError, ValueError) as error:
        logger.error("Subscription test failed: %s", error)
        return 1
    finally:
        try:
            robot.logout()
        except RWS8Exception as error:
            logger.warning("Controller logout failed: %s", error)
        finally:
            robot.close()


if __name__ == "__main__":
    raise SystemExit(main())
