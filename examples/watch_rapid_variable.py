import logging
import ssl
from getpass import getpass
from urllib.parse import urlsplit, urlunsplit

import httpx
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

BASE_URL = "https://10.211.55.4:8001"
RESOURCE = "/rw/rapid/symbol/RAPID/T_ROB1/CoordinationData/test_value/data;value"
logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    password = getpass("Controller password for admin: ")

    # Certificate verification is disabled for this virtual-controller example.
    tls = ssl.create_default_context()
    tls.check_hostname = False
    tls.verify_mode = ssl.CERT_NONE
    with httpx.Client(
        base_url=BASE_URL,
        auth=("admin", password),
        headers={"Accept": "application/xhtml+xml;v=2.0"},
        verify=tls,
        timeout=5.0,
        trust_env=False,
    ) as client:
        try:
            subscription = client.post(
                "/subscription",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;v=2.0",
                },
                data={"resources": "1", "1": RESOURCE, "1-p": "1"},
            )
            subscription.raise_for_status()
            location = urlsplit(subscription.headers.get("Location", ""))
            if not location.path.startswith("/poll/"):
                raise ValueError("Subscription did not return a WebSocket polling path")

            # Keep the polling path from ABB and use our VM forwarding port.
            endpoint = urlsplit(BASE_URL)
            websocket_url = urlunsplit(
                ("wss", endpoint.netloc, location.path, location.query, "")
            )
            cookie = client.build_request("GET", BASE_URL).headers.get("Cookie")
            if not cookie:
                raise ValueError("Controller did not provide session cookies")

            with connect(
                websocket_url,
                ssl=tls,
                subprotocols=["rws_subscription"],
                additional_headers={"Cookie": cookie},
                proxy=None,
                open_timeout=5,
            ) as websocket:
                logger.info("Connected. Change test_value in RobotStudio within 30 seconds.")
                logger.info("RAPID event: %s", websocket.recv(timeout=30))
            return 0
        except (httpx.HTTPError, WebSocketException, OSError, ValueError) as error:
            logger.error("Subscription test failed: %s", error)
            return 1
        finally:
            if client.cookies:
                try:
                    client.get("/logout").raise_for_status()
                except httpx.HTTPError as error:
                    logger.warning("Controller logout failed: %s", error)


if __name__ == "__main__":
    raise SystemExit(main())
