from dronekit import connect
from config import DRONE_CONNECTIONS


class DroneManager:
    def __init__(self):
        self.vehicles = {}

    def connect_all_drones(self):
        for drone in DRONE_CONNECTIONS:
            drone_id = drone["id"]

            # Skip if already connected
            if drone_id in self.vehicles:
                continue

            connection = drone["connection"]
            baud = drone["baud"]

            if connection.startswith("tcp"):
                timeout = 5
            else:
                timeout = 20

            try:
                print(f"Connecting {drone_id}...")
                if baud :
                    vehicle = connect(
                        connection, 
                        wait_ready=False,
                        baud=baud,
                        timeout=timeout
                    )
                else:
                    vehicle = connect(
                        connection,
                        wait_ready=False,
                        timeout=timeout
                    )

                self.vehicles[drone_id] = vehicle
                print(vehicle)
                print(f"{drone_id} connected")

            except Exception as e:
                print(f"Failed {drone_id}: {e}")

    def get_connected_drones(self):
        return self.vehicles