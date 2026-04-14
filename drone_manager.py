from dronekit import connect
from config import DRONE_CONNECTIONS


class DroneManager:
    def __init__(self):
        self.vehicles = {}
        self.dynamic_drone_count = 1

    def connect_all_drones(self):
        for drone in DRONE_CONNECTIONS:
            drone_id = drone["id"]

            # Skip if already connected
            if drone_id in self.vehicles:
                continue

            connection = drone["connection"]
            baud = drone["baud"]

            self._connect_vehicle(drone_id, connection, baud)

    def connect_single_drone(self, connection, baud=None):
        """
        Dynamically connect drone from UI input
        """
        drone_id = f"Drone-{len(self.vehicles) + 1}"

        vehicle = self._connect_vehicle(
            drone_id,
            connection,
            baud
        )

        return drone_id, vehicle

    def _connect_vehicle(self, drone_id, connection, baud=None):
        """
        Common connection logic
        """
        if connection.startswith("tcp"):
            timeout = 5
        else:
            timeout = 20

        try:
            print(f"Connecting {drone_id}...")

            if baud:
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

            print(f"{drone_id} connected")
            return vehicle

        except Exception as e:
            print(f"Failed {drone_id}: {e}")
            return None

    def get_connected_drones(self):
        return self.vehicles