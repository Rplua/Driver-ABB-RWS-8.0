from abb_rws_8.rws_client import RWSClient

base_url: str = "https://10.211.55.4:8001"
username: str = "admin"
password: str = "example-password"
robot = RWSClient(base_url=base_url, username=username, password=password)

try:
    print(robot.get_services())
finally:
    robot.close()
