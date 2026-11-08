
from abb_rws_8.rws_client import RWSClient

base_url: str = "https://10.211.55.4:8001"
username: str = "admin"
password: str = "robotics"
robot = RWSClient(base_url=base_url, username=username, password=password, verify=False)

try:
    status_code, services = robot.get_services()
    print(status_code)
    for service in services:
        print(service)

finally:
    robot.close()
