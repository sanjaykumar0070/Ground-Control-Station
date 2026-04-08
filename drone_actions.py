import time
from dronekit import VehicleMode

def change_mode(vehicle, mode_name):
    """
    Changes drone flight mode safely
    """
    try:
        print(f"Changing mode to {mode_name}...")

        vehicle.mode = VehicleMode(mode_name)

        timeout = 5
        start = time.time()

        while vehicle.mode.name != mode_name:
            if time.time() - start > timeout:
                print(f"Mode change timeout: {mode_name}")
                return False

            print("Waiting for mode change...")
            time.sleep(0.5)

        print(f"Mode changed to {mode_name}")
        return True

    except Exception as e:
        print(f"Mode change failed: {e}")
        return False

def arm_drone(vehicle):
    if vehicle.armed:
        print("Drone already armed")
        return True

    print("Switching to STABILIZE mode...")
    vehicle.mode = VehicleMode("GUIDED")
    time.sleep(2)

    print("Arming motors...")
    vehicle.armed = True

    timeout = 10
    start = time.time()

    while not vehicle.armed:
        if time.time() - start > timeout:
            print("Arming timeout")
            return False

        print("Waiting for arming...")
        time.sleep(1)

    print("Drone armed successfully")
    return True

def disarm_drone(vehicle):
    """
    Disarms the drone
    """
    if not vehicle.armed:
        print("Drone already disarmed")
        return True

    print("Disarming drone...")
    vehicle.armed = False

    while vehicle.armed:
        print("Waiting for disarm...")
        time.sleep(1)

    print("Drone disarmed successfully")
    return True

def takeoff_drone(vehicle, altitude):
    """
    Arms and takes off to given altitude
    """
    arm_drone(vehicle)

    print(f"Taking off to {altitude} meters...")
    vehicle.simple_takeoff(altitude)

    while True:
        current_alt = vehicle.location.global_relative_frame.alt
        print(f"Current altitude: {current_alt}")

        if current_alt >= altitude * 0.95:
            print("Target altitude reached")
            break

        time.sleep(1)

def land_drone(vehicle):
    print("Landing ...")
    vehicle.mode = VehicleMode("LAND")

