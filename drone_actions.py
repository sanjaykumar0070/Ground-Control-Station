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
    """
    Attempts to arm the drone in the current mode.
    Returns:
        (bool, str) -> success, reason
    """
    try:
        current_mode = vehicle.mode.name

        print(f"Attempting arm in mode: {current_mode}")

        # Check heartbeat / connection
        if vehicle.last_heartbeat > 5:
            return False, "Heartbeat timeout (>5 sec)"

        # Check GPS status
        gps_fix = vehicle.gps_0.fix_type if vehicle.gps_0 else 0

        # Check EKF / armable state
        is_armable = vehicle.is_armable

        print(f"Mode: {current_mode}")
        print(f"GPS Fix: {gps_fix}")
        print(f"Armable: {is_armable}")

        # Try arm directly in current mode
        vehicle.armed = True

        timeout = 10
        start = time.time()

        while not vehicle.armed:
            if time.time() - start > timeout:
                # Detailed diagnostics
                reason = []

                if not vehicle.is_armable:
                    reason.append("Pre-arm checks not passed")

                if gps_fix < 3:
                    reason.append(
                        f"GPS fix insufficient (fix={gps_fix})"
                    )

                if vehicle.system_status.state != "ACTIVE":
                    reason.append(
                        f"System status={vehicle.system_status.state}"
                    )

                if vehicle.battery and vehicle.battery.level is not None:
                    if vehicle.battery.level < 20:
                        reason.append("Low battery")

                if vehicle.last_heartbeat > 5:
                    reason.append("Heartbeat timeout")

                if not reason:
                    reason.append(
                        "Autopilot rejected arming request"
                    )

                return False, " | ".join(reason)

            time.sleep(1)

        return True, f"Drone armed successfully in {current_mode}"

    except Exception as e:
        return False, f"Arm exception: {str(e)}"

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

    if not vehicle.armable:
        return

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

