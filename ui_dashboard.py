# ui_dashboard.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TelemetryDashboard:
    def __init__(self, root, on_close_callback):
        self.root = root
        self.root.title("Avionics ECU Software-in-the-Loop Environment")
        self.root.geometry("1000x650")
        self.on_close_callback = on_close_callback
        
        # Bind close event hook securely
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Shared Dynamic Variables
        self.slider_throttle = tk.DoubleVar(value=0.0)
        self.slider_altitude = tk.DoubleVar(value=0.0)
        self.fault_active = tk.BooleanVar(value=False)
        
        # Setup UI Panels
        self._build_control_widgets()
        self._build_charts()
        
    def _build_control_widgets(self):
        control_frame = ttk.LabelFrame(self.root, text=" Flight Deck Controls & Sensor Inputs ")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Throttle (Pilot Command Engine Demand Indicator)
        ttk.Label(control_frame, text="Power Lever Angle (Throttle %):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        t_scale = ttk.Scale(control_frame, from_=0.0, to=100.0, variable=self.slider_throttle, orient=tk.HORIZONTAL, length=250)
        t_scale.grid(row=0, column=1, padx=5, pady=5)
        self.lbl_throttle = ttk.Label(control_frame, text="0.0%")
        self.lbl_throttle.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Simulated Flight Altitude Environment Slider
        ttk.Label(control_frame, text="Atmospheric Altitude (Feet):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        a_scale = ttk.Scale(control_frame, from_=0.0, to=45000.0, variable=self.slider_altitude, orient=tk.HORIZONTAL, length=250)
        a_scale.grid(row=1, column=1, padx=5, pady=5)
        self.lbl_alt = ttk.Label(control_frame, text="0 ft")
        self.lbl_alt.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # FADEC Engineering Fault Testing Injector Button Switch
        self.btn_fault = tk.Button(control_frame, text="INJECT RPM SENSOR FAULT", bg="#d9534f", fg="white", font=('Helvetica', 9, 'bold'), command=self._toggle_fault)
        self.btn_fault.grid(row=0, column=3, rowspan=2, padx=40, pady=5)
        
        # Live System Telemetry Status Messaging Display Banner
        self.lbl_status = tk.Label(self.root, text="SYSTEM STATUS: INITIALIZING", font=('Helvetica', 12, 'bold'), bg="#5cb85c", fg="white", pady=4)
        self.lbl_status.pack(fill=tk.X, padx=10, pady=2)

    def _build_charts(self):
        # Matplotlib Graph Configuration Matrix
        self.fig, (self.ax_rpm, self.ax_egt) = plt.subplots(2, 1, figsize=(10, 5))
        self.fig.tight_layout(pad=2.5)
        
        self.time_data, self.throttle_data, self.rpm_data, self.egt_data = [], [], [], []
        
        self.line_th, = self.ax_rpm.plot([], [], 'b--', label='Pilot Command Target (%)')
        self.line_rpm, = self.ax_rpm.plot([], [], 'g-', label='Core Rotational Output Speed (% N1)')
        self.ax_rpm.set_title("Engine Speed Performance Characteristics")
        self.ax_rpm.set_ylabel("Percentage (%)")
        self.ax_rpm.set_ylim(-5, 115)
        self.ax_rpm.legend(loc="upper left")
        self.ax_rpm.grid(True, linestyle=":")
        
        self.line_egt, = self.ax_egt.plot([], [], 'r-', label='Exhaust Temperature (°C)')
        self.ax_egt.set_title("Turbine Structural Core Thermal Profiles")
        self.ax_egt.set_xlabel("Elapsed Sim Time (Seconds)")
        self.ax_egt.set_ylabel("Temp (°C)")
        self.ax_egt.set_ylim(0, 900)
        self.ax_egt.legend(loc="upper left")
        self.ax_egt.grid(True, linestyle=":")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _toggle_fault(self):
        # Toggle state
        is_active = not self.fault_active.get()
        self.fault_active.set(is_active)
        if is_active:
            self.btn_fault.config(text="CLEAR FAULT SYSTEM ARMED", bg="#f0ad4e")
        else:
            self.btn_fault.config(text="INJECT RPM SENSOR FAULT", bg="#d9534f")

    def refresh(self, t, throttle, rpm, egt, msg, is_limiting):
        # Update text metrics dynamically
        self.lbl_throttle.config(text=f"{throttle:.1f}%")
        self.lbl_alt.config(text=f"{self.slider_altitude.get():,.0f} ft")
        self.lbl_status.config(text=f"ECU STATUS BANNER: {msg}")
        
        # Color status banner according to risk
        if "FAULT" in msg:
            self.lbl_status.config(bg="#d9534f")
        elif is_limiting:
            self.lbl_status.config(bg="#f0ad4e")
        else:
            self.lbl_status.config(bg="#5cb85c")
            
        # Append lists for graphing rolling layout windows
        self.time_data.append(t)
        self.throttle_data.append(throttle)
        self.rpm_data.append(rpm)
        self.egt_data.append(egt)
        
        # Crop datasets to show rolling view of the last 15 seconds
        if len(self.time_data) > 750:
            self.time_data.pop(0)
            self.throttle_data.pop(0)
            self.rpm_data.pop(0)
            self.egt_data.pop(0)
            
        # Draw dynamic plotting updates smoothly
        if self.time_data:
            self.line_th.set_data(self.time_data, self.throttle_data)
            self.line_rpm.set_data(self.time_data, self.rpm_data)
            self.line_egt.set_data(self.time_data, self.egt_data)
            
            curr_min_t = self.time_data[0]
            curr_max_t = self.time_data[-1]
            # Handle minimal time range step to avoid plotting width warnings
            if curr_max_t == curr_min_t:
                curr_max_t += 0.1
                
            self.ax_rpm.set_xlim(curr_min_t, curr_max_t)
            self.ax_egt.set_xlim(curr_min_t, curr_max_t)
            
            self.canvas.draw_idle()

    def close_window(self):
        self.on_close_callback()
