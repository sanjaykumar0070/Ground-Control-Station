import os
import sys
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QCheckBox,
    QFrame, QLineEdit
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView

from drone_manager import DroneManager
from drone_actions import (
    arm_drone,
    disarm_drone,
    takeoff_drone,
    land_drone
)
class GCSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Drone GCS Dashboard")
        self.setGeometry(100, 100, 1600, 900)

        # initializing vehicles(drones)
        self.drone_manager = DroneManager()
        self.vehicles = {}
        self.load_drones_async()

        self.selected_drone = None

        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Add 3 sections
        main_layout.addWidget(self.create_left_panel(), 3)
        main_layout.addWidget(self.create_middle_panel(), 4)
        main_layout.addWidget(self.create_right_panel(), 3)

        #Start live telemetry timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_live_data)
        # self.timer.start(1500)   #every 1 second
        self.map_loaded = False

    def load_drones_async(self):
        def task():
            self.drone_manager.connect_all_drones()
            self.vehicles = self.drone_manager.get_connected_drones()

            QTimer.singleShot(0, self.refresh_connected_devices)

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

    def refresh_live_data(self):
        try:
            self.refresh_map()

            # Update right panel if drone selected
            if self.selected_drone:
                self.update_right_panel(self.selected_drone)
        except Exception as e: 
            print("UI ERROR: ", e)

    # LEFT PANEL
    def create_left_panel(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Box)

        layout = QVBoxLayout()
        frame.setLayout(layout)

        title = QLabel("Drone Control")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        refresh_btn = QPushButton("🔄 Refresh Devices")
        refresh_btn.setFixedHeight(40)
        refresh_btn.clicked.connect(self.refresh_connected_devices)
        layout.addWidget(refresh_btn)

        # Grid for drones
        self.drone_grid = QGridLayout()

        connected_drones = list(self.vehicles.keys())
        row = 0
        col = 0

        for drone_id in connected_drones:
            drone_card = self.create_drone_card(drone_id)
            self.drone_grid.addWidget(drone_card, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.addLayout(self.drone_grid)
        layout.addStretch()
        return frame

    def create_drone_card(self, drone_id):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                background-color: #1e1e1e;
            }
        """)
        card.setFixedHeight(160)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        card.setLayout(layout)

        vehicle = self.vehicles.get(drone_id)

        is_connected = vehicle is not None

        status_color = "green" if is_connected else "red"
        status_text = "CONNECTED" if is_connected else "DISCONNECTED"

        drone_label = QLabel(f"🛸 {drone_id}")

        status_label = QLabel(status_text)
        status_label.setStyleSheet(
            f"color: white; background:{status_color}; padding:4px; border-radius:4px;"
        )

        details_btn = QPushButton("View Details")
        details_btn.clicked.connect(
            lambda _, d=drone_id: self.select_drone_and_center(d)
        )

        layout.addWidget(drone_label)
        layout.addWidget(status_label)
        layout.addStretch()
        layout.addWidget(details_btn)

        return card
    
    def refresh_connected_devices(self):
        print("Refreshing connected drones...")

        # reconnect all drones
        self.drone_manager.connect_all_drones()
        self.vehicles = self.drone_manager.get_connected_drones()

        # clear existing grid
        while self.drone_grid.count():
            item = self.drone_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # rebuild drone cards
        connected_drones = list(self.vehicles.keys())

        row = 0
        col = 0

        for drone_id in connected_drones:
            drone_card = self.create_drone_card(drone_id)
            self.drone_grid.addWidget(drone_card, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        print("Refresh completed")

    # MIDDLE PANEL
    def create_middle_panel(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Box)

        layout = QVBoxLayout()
        frame.setLayout(layout)

        map_title = QLabel("Live Drone Map")
        map_title.setFont(QFont("Arial", 14, QFont.Bold))

        # Load map
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(650)

        # html_path = os.path.abspath("map.html")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(base_dir, "map.html")
        with open(map_path, "r", encoding="utf-8") as file:
            html = file.read()

        self.map_view.setHtml(html)

        self.map_view.loadFinished.connect(self.on_map_loaded)

        # QTimer.singleShot(1200, self.refresh_map)

        layout.addWidget(map_title)
        layout.addWidget(self.map_view)

        return frame
    
    def on_map_loaded(self):
        print("Map HTML loaded")

        QTimer.singleShot(2000, self.enable_map_updates)

    def enable_map_updates(self):
        print("Map JS ready")
        self.map_loaded = True
        self.timer.start(1500)
    
    # RIGHT PANEL
    def create_right_panel(self):
        self.right_frame = QFrame()
        self.right_frame.setFrameShape(QFrame.Box)

        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)

        title = QLabel("Telemetry / Actions")
        title.setFont(QFont("Arial", 14, QFont.Bold))

        self.telemetry_label = QLabel("Select a drone")
        self.battery_label = QLabel("Battery: --")
        self.gps_label = QLabel("GPS: --")
        self.altitude_label = QLabel("Altitude: --")
        self.mode_label = QLabel("Mode: --")
        self.gps_fix_label = QLabel("GPS Fix: --")
        self.speed_label = QLabel("Speed: --")
        self.heading_label = QLabel("Heading: --")

        # FLIGHT MODES 
        self.guided_btn = QPushButton("GUIDED")
        self.loiter_btn = QPushButton("LOITER")
        self.stabilize_btn = QPushButton("STABILIZE")
        self.althold_btn = QPushButton("ALT HOLD")
        self.guided_btn.clicked.connect(lambda: self.change_selected_mode("GUIDED"))
        self.loiter_btn.clicked.connect(lambda: self.change_selected_mode("LOITER"))
        self.stabilize_btn.clicked.connect(lambda: self.change_selected_mode("STABILIZE"))
        self.althold_btn.clicked.connect(lambda: self.change_selected_mode("ALT_HOLD"))

        self.arm_toggle_btn = QPushButton("DISARMED")
        self.arm_toggle_btn.setFixedHeight(45)
        self.arm_toggle_btn.setEnabled(False)
        self.arm_toggle_btn.setStyleSheet(
            "background-color: red; color: white; font-weight: bold;"
        )
        self.arm_toggle_btn.clicked.connect(self.toggle_arm_disarm)

        self.altitude_input = QLineEdit()
        self.altitude_input.setPlaceholderText("Enter takeoff altitude (meters)")
        self.altitude_input.setText("0.5")

        self.takeoff_btn = QPushButton("Takeoff")
        self.takeoff_btn.setEnabled(False)
        self.takeoff_btn.clicked.connect(self.takeoff_selected_drone)

        self.land_btn = QPushButton("Land")
        self.land_btn.setEnabled(False)
        self.land_btn.clicked.connect(self.land_selected_drone)

        self.right_layout.addWidget(title)
        self.right_layout.addWidget(self.telemetry_label)
        self.right_layout.addWidget(self.battery_label)
        self.right_layout.addWidget(self.gps_label)
        self.right_layout.addWidget(self.altitude_label)
        self.right_layout.addWidget(self.mode_label)
        self.right_layout.addWidget(self.gps_fix_label)
        self.right_layout.addWidget(self.speed_label)
        self.right_layout.addWidget(self.heading_label)

        # ADDING BUTTONS
        self.right_layout.addWidget(self.guided_btn)
        self.right_layout.addWidget(self.loiter_btn)
        self.right_layout.addWidget(self.stabilize_btn)
        self.right_layout.addWidget(self.althold_btn)
        self.right_layout.addWidget(self.arm_toggle_btn)

        takeoff_layout = QHBoxLayout()
        takeoff_layout.addWidget(self.altitude_input)
        takeoff_layout.addWidget(self.takeoff_btn)

        self.right_layout.addLayout(takeoff_layout)
        self.right_layout.addWidget(self.land_btn)

        return self.right_frame
    
    def change_selected_mode(self, mode_name):
        # if not self.selected_drone:
        #     self.log_action("No drone selected")
        #     return

        vehicle = self.vehicles[self.selected_drone]

        thread = threading.Thread(
            target=self._mode_worker,
            args=(vehicle, mode_name),
            daemon=True
        )
        thread.start()

    def _mode_worker(self, vehicle, mode_name):
        from drone_actions import change_mode

        success = change_mode(vehicle, mode_name)

        # if success:
        #     self.log_action(f"Mode changed to {mode_name}")
        # else:
        #     self.log_action(f"Failed to change mode to {mode_name}")

        QTimer.singleShot(
            500,
            lambda: self.update_right_panel(self.selected_drone)
        )

    def toggle_arm_disarm(self):
        if not self.selected_drone:
            print("No drone selected")
            return

        vehicle = self.vehicles[self.selected_drone]

        def task():
            if vehicle.armed:
                disarm_drone(vehicle)
            else:
                arm_drone(vehicle)

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

        # refresh UI after small delay
        QTimer.singleShot(2000, self.update_arm_button_ui)

    def update_arm_button_ui(self):
        if not self.selected_drone:
            return

        vehicle = self.vehicles[self.selected_drone]

        if vehicle.armed:
            self.arm_toggle_btn.setText("ARMED")
            self.arm_toggle_btn.setStyleSheet(
                "background-color: green; color: white; font-weight: bold;"
            )
        else:
            self.arm_toggle_btn.setText("DISARMED")
            self.arm_toggle_btn.setStyleSheet(
                "background-color: red; color: white; font-weight: bold;"
            )

    # ACTION BUTTONS
    def takeoff_selected_drone(self):
        if not self.selected_drone:
            print("No drone selected")
            return

        vehicle = self.vehicles[self.selected_drone]

        try:
            altitude = float(self.altitude_input.text())
        except ValueError:
            print("Invalid altitude")
            return

        thread = threading.Thread(
            target=takeoff_drone,
            args=(vehicle, altitude),
            daemon=True
        )
        thread.start()
        
    def land_selected_drone(self):
        if not self.selected_drone:
            return
        
        if self.selected_drone:
            print(f"Landing drone {self.selected_drone}")
            vehicle = self.vehicles[self.selected_drone]
            land_drone(vehicle)

        QTimer.singleShot(1000, self.update_arm_button_ui)

    # TELEMETRY PANEL UPDATE
    def update_right_panel(self, drone_id):
        vehicle = self.vehicles.get(drone_id)

        if not vehicle:
            return
        
        self.selected_drone = drone_id

        battery = (
            vehicle.battery.level
            if vehicle.battery and vehicle.battery.level is not None
            else 0
        )

        lat = vehicle.location.global_frame.lat
        lon = vehicle.location.global_frame.lon
        alt = vehicle.location.global_relative_frame.alt
        mode = vehicle.mode.name
        gps_fix = vehicle.gps_0.fix_type
        speed = vehicle.groundspeed
        heading = vehicle.heading

        self.telemetry_label.setText(f"Drone ID: {drone_id}")
        self.battery_label.setText(f"Battery: {battery}%")
        self.gps_label.setText(f"GPS: {lat}, {lon}")
        self.altitude_label.setText(f"Altitude: {alt} m")
        self.mode_label.setText(f"Mode: {mode}")
        self.gps_fix_label.setText(f"GPS Fix: {gps_fix}")
        self.speed_label.setText(f"Speed: {speed} m/s")
        self.heading_label.setText(f"Heading: {heading}°")

        # Enable buttons
        self.arm_toggle_btn.setEnabled(True)
        self.takeoff_btn.setEnabled(True)
        self.land_btn.setEnabled(True)

        # Update arm/disarm color state
        self.update_arm_button_ui()

    def select_drone_and_center(self, drone_id):
        self.update_right_panel(drone_id)

        vehicle = self.vehicles.get(drone_id)
        if not vehicle:
            return

        lat = vehicle.location.global_frame.lat
        lon = vehicle.location.global_frame.lon

        self.center_selected_drone(lat, lon)

    def center_selected_drone(self, lat, lon):
        js_code = f"""
            centerDrone({lat}, {lon});
        """
        self.map_view.page().runJavaScript(js_code)
        
    # LIVE MAP
    def refresh_map(self):
        drone_list = []

        if not self.map_loaded:
            return
        
        for drone_id, vehicle in self.vehicles.items():
            location = vehicle.location.global_frame

            if not location:
                continue

            lat = location.lat
            lon = location.lon
            
            if lat is None or lon is None:
                continue

            drone_list.append({
                "id": drone_id,
                "lat": lat,
                "lon": lon
            })

            js_code = f"""
                updateDroneMarker(
                    '{drone_id}',
                    {lat},
                    {lon}
                );
            """

            try:
                self.map_view.page().runJavaScript(js_code)
            except Exception as e:
                print("Map JS error:", e)
        
        # Fit map only once
        if hasattr(self, "map_fitted") is False:
            self.map_fitted = True

            js_fit = f"""
                fitAllDrones({drone_list});
            """

            self.map_view.page().runJavaScript(js_fit)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = GCSMainWindow()
    window.show()

    sys.exit(app.exec())