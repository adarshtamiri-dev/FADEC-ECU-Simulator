# engine.py

class JetEngineSimulator:
    def __init__(self, dt=0.02):
        self.dt = dt  # Time step in seconds (50 Hz)
        
        # Engine State Variables
        self.rpm_pct = 0.0      # Current Engine Core Speed (0% to 100%+)
        self.egt_degc = 15.0     # Exhaust Gas Temperature in Celsius
        self.fuel_flow_pct = 0.0 # Actual fuel delivery rate
        
        # Environment Defaults
        self.altitude_ft = 0.0
        self.ambient_temp = 15.0
        
        # Physics Constants
        self.inertia_factor = 2.5  
        self.thermal_inertia = 0.8  # NEW: Prevents instantaneous temperature spikes

    def update_environment(self, altitude_ft):
        """Simulates atmospheric changes as the aircraft climbs."""
        self.altitude_ft = altitude_ft
        self.ambient_temp = max(-56.5, 15.0 - (altitude_ft * 0.00198))

    def step(self, commanded_fuel_pct, inject_fault=False):
        """Updates the physical state of the engine for one clock tick."""
        # 1. Simulate Actuator Delay
        self.fuel_flow_pct += (commanded_fuel_pct - self.fuel_flow_pct) * (self.dt * 8.0)
        
        # 2. Balanced Environmental Power Loss (Realistic high-altitude baseline air density)
        altitude_loss_factor = max(0.55, 1.0 - (self.altitude_ft / 65000.0))
        effective_fuel = self.fuel_flow_pct * altitude_loss_factor
        
        # 3. Calculate Core RPM Physics
        target_rpm_physics = effective_fuel * 1.05
        rpm_acceleration = (target_rpm_physics - self.rpm_pct) / self.inertia_factor
        self.rpm_pct += rpm_acceleration * self.dt
        
        if self.rpm_pct < 0: 
            self.rpm_pct = 0.0

        # 4. Thermal Model with Inertia Lag (Fixes the 4000°C/sec bug)
        combustion_heat = effective_fuel * 9.5
        
        if effective_fuel > 5.0:
            target_egt = max(350.0, self.ambient_temp + combustion_heat)
        else:
            target_egt = self.ambient_temp + combustion_heat
            
        # Smooth thermal change over time instead of instantaneous jumps
        egt_rate_of_change = (target_egt - self.egt_degc) / self.thermal_inertia
        self.egt_degc += egt_rate_of_change * self.dt
        
        # 5. Fault Injection
        if inject_fault:
            return 0.0, self.egt_degc, self.fuel_flow_pct
            
        return self.rpm_pct, self.egt_degc, self.fuel_flow_pct
