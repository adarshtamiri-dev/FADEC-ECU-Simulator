# main.py
import tkinter as tk
from engine import JetEngineSimulator
from ecu import ElectronicEngineControl
from ui_dashboard import TelemetryDashboard
from final_evaluation import EcuPerformanceEvaluator

class FlightSimulationRunner:
    def __init__(self):
        self.root = tk.Tk()
        self.dt = 0.02  # Time step representing 50 Hz processing frames
        self.current_time = 0.0
        self.simulation_running = True
        
        # Instantiate System Elements
        self.engine = JetEngineSimulator(dt=self.dt)
        self.ecu = ElectronicEngineControl(dt=self.dt)
        self.evaluator = EcuPerformanceEvaluator()
        self.dashboard = TelemetryDashboard(self.root, on_close_callback=self.terminate_simulation)
        
        # Trigger Periodic Execution Loop
        self.periodic_execution_loop()

    def periodic_execution_loop(self):
        """Main real-time loop synchronization tick."""
        if not self.simulation_running:
            return
            
        # 1. Read Inputs from Dashboard Sliders
        target_throttle = self.dashboard.slider_throttle.get()
        flight_altitude = self.dashboard.slider_altitude.get()
        fault_injected = self.dashboard.fault_active.get()
        
        # 2. Update Flight Conditions for the Engine
        self.engine.update_environment(flight_altitude)
        
        # 3. Read current sensors (with hardware fault injection support)
        simulated_rpm, simulated_egt, actual_fuel_flow = self.engine.step(
            commanded_fuel_pct=self.ecu.last_error, # ECU feedback loop bridge
            inject_fault=fault_injected
        )
        
        # 4. Run ECU control loop step
        calculated_fuel_command = self.ecu.compute_fuel_demand(
            pilot_throttle_pct=target_throttle,
            current_rpm_input=simulated_rpm,
            current_egt_input=simulated_egt
        )
        
        # Feed calculated fuel value straight back into physics simulation engine engine model 
        self.engine.step(commanded_fuel_pct=calculated_fuel_command, inject_fault=fault_injected)
        
        # 5. Log Data Vectors for Final Analytics Calculations
        self.evaluator.log_tick(
            t=self.current_time,
            throttle=target_throttle,
            rpm=simulated_rpm,
            egt=simulated_egt,
            fuel=calculated_fuel_command,
            status=self.ecu.status_message
        )

        
        # 6. Refresh GUI Graphics Dashboard Display
        self.dashboard.refresh(
            t=self.current_time,
            throttle=target_throttle,
            rpm=simulated_rpm,
            egt=simulated_egt,
            msg=self.ecu.status_message,
            is_limiting=self.ecu.limiter_active
        )
        
        # Increment Execution Frames Timelines
        self.current_time += self.dt
        
        # Reschedule next tick iteration to run in 20 milliseconds
        self.root.after(int(self.dt * 1000), self.periodic_execution_loop)

    def terminate_simulation(self):
        """Triggers system shutdown processing routines cleanly."""
        self.simulation_running = False
        self.root.destroy()
        
        # Generate and print performance report to the terminal
        report_card = self.evaluator.generate_report()
        print(report_card)

if __name__ == "__main__":
    # Start the application
    app = FlightSimulationRunner()
    app.root.mainloop()
