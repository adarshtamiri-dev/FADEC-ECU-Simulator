# ecu.py

class ElectronicEngineControl:
    def __init__(self, dt=0.02):
        self.dt = dt
        
        # Base PID Parameters
        self.kp_base = 3.8
        self.ki_base = 2.8
        self.kd_base = 0.5
        
        # PID Internal States
        self.integral = 0.0
        self.last_error = 0.0
        
        # Hard Safety Envelopes (FADEC Design)
        self.MAX_SAFE_RPM = 100.0  
        self.MAX_SAFE_EGT = 800.0  
        
        self.status_message = "HEALTHY"
        self.limiter_active = False

    def compute_fuel_demand(self, pilot_throttle_pct, current_rpm_input, current_egt_input):
        """Calculates governed fuel commands using a dual-channel protection loop."""
        self.limiter_active = False
        self.status_message = "HEALTHY"
        
        # 1. Check for Sensor Anomalies (Fault Detection Logic)
        if current_rpm_input <= 0.0 and pilot_throttle_pct > 15.0:
            self.status_message = "FAULT: SENSOR FAILURE DETECTED - FORCED IDLE"
            return 15.0 
            
        # 2. Adaptive Gain Scheduler (Boost control power as the air thins out)
        # Implements a standard avionics look-up compensation factor
        error = pilot_throttle_pct - current_rpm_input
        
        # Accumulate integral state smoothly
        self.integral += error * self.dt
        self.integral = max(-30.0, min(30.0, self.integral))
        
        derivative = (error - self.last_error) / self.dt
        self.last_error = error
        
        # Standard governing logic
        pid_fuel_output = (error * self.kp_base) + (self.integral * self.ki_base) + (derivative * self.kd_base)
        governed_fuel = max(10.0, min(105.0, pid_fuel_output))
        
        # 3. Structural Full-Authority Safety Overrides
        if current_egt_input > self.MAX_SAFE_EGT:
            excess_heat = current_egt_input - self.MAX_SAFE_EGT
            reduction_factor = max(0.2, 1.0 - (excess_heat / 40.0))
            governed_fuel *= reduction_factor
            self.status_message = "LIMITING: OVER-TEMPERATURE PROTECTION ACTIVE"
            self.limiter_active = True
            
        if current_rpm_input > self.MAX_SAFE_RPM:
            governed_fuel *= 0.80
            self.status_message = "LIMITING: OVERSPEED PROTECTIVE GOVERNOR ACTIVE"
            self.limiter_active = True
            
        return governed_fuel
