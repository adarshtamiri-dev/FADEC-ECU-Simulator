# final_evaluation.py
import numpy as np

class EcuPerformanceEvaluator:
    def __init__(self):
        self.time_history = []
        self.throttle_history = []
        self.rpm_history = []
        self.egt_history = []
        self.fuel_history = []
        self.status_history = []
        self.loop_execution_times = []  # Tracks jitter/timing

    def log_tick(self, t, throttle, rpm, egt, fuel, status, exec_time_ms=0.02):
        """Collects telemetry state vectors including software execution frames."""
        self.time_history.append(t)
        self.throttle_history.append(throttle)
        self.rpm_history.append(rpm)
        self.egt_history.append(egt)
        self.fuel_history.append(fuel)
        self.status_history.append(status)
        self.loop_execution_times.append(exec_time_ms)

    def generate_report(self):
        """Compiles standard Collins-Aerospace/DO-178C grade software metrics."""
        if not self.rpm_history:
            return "No flight data available to process."
            
        t = np.array(self.time_history)
        th = np.array(self.throttle_history)
        rpm = np.array(self.rpm_history)
        egt = np.array(self.egt_history)
        fuel = np.array(self.fuel_history)
        exec_times = np.array(self.loop_execution_times)

        # ----------------------------------------------------
        # 1. CONTROL LOOP PRECISION (Steady State)
        # ----------------------------------------------------
        ss_window = t > (t[-1] - 3.0)  # Analyze last 3 seconds
        avg_ss_error = np.mean(np.abs(th[ss_window] - rpm[ss_window])) if np.any(ss_window) else 99.9

        # ----------------------------------------------------
        # 2. TRANSIENT CHARACTERISTICS
        # ----------------------------------------------------
        max_overshoot = 0.0
        rise_time = "N/A"
        for i in range(1, len(th)):
            if th[i] > th[i-1] + 20.0:  # Major step command detected
                start_t = t[i]
                target = th[i]
                window_rpm = rpm[i:i+250]
                window_t = t[i:i+250]
                if len(window_rpm) > 0:
                    max_overshoot = max(0.0, ((np.max(window_rpm) - target) / target) * 100.0)
                    # Find 90% rise time marker
                    idx_90 = np.where(window_rpm >= (target * 0.90))[0]
                    if len(idx_90) > 0:
                        rise_time = f"{window_t[idx_90[0]] - start_t:.2f} sec"
                break

        # ----------------------------------------------------
        # 3. INDUSTRY EFFICIENCY & PERFORMANCE PARAMETERS
        # ----------------------------------------------------
        # Specific Fuel Consumption (SFC) Efficiency Index
        # In industry: SFC = Fuel Burn Rate / Thrust Output (approximated here via RPM)
        active_flight = rpm > 15.0
        if np.any(active_flight):
            sfc_index = np.mean(fuel[active_flight] / (rpm[active_flight] + 1e-5)) * 10.0
        else:
            sfc_index = 0.0

        # Thermal Excursion Acceleration Stress Index
        # Measures how hard the thermal transients stress engine blades per second
        egt_derivatives = np.abs(np.diff(egt)) / (np.diff(t) + 1e-6)
        peak_thermal_stress = np.max(egt_derivatives) if len(egt_derivatives) > 0 else 0.0

        # ----------------------------------------------------
        # 4. EMBEDDED SOFTWARE REAL-TIME INTEGRITY (DO-178C Spirit)
        # ----------------------------------------------------
        # In a real 50Hz system, every frame must execute in under 20ms (0.02s)
        # Frame Jitter checks if our software ticks are dangerously irregular
        frame_intervals = np.diff(t)
        target_frame_dt = 0.02
        max_jitter_ms = np.max(np.abs(frame_intervals - target_frame_dt)) * 1000.0
        
        # Safety Margin Calculation
        thermal_safety_margin = ((800.0 - np.max(egt)) / 800.0) * 100.0
        overspeed_violations = int(np.sum(rpm > 100.5))
        fault_contained = "SUCCESS" if ("FAULT" in self.status_history and rpm[-1] <= 15.1) else "N/A"
        if "FAULT" in self.status_history and fault_contained != "SUCCESS":
            fault_contained = "CRITICAL FAIL (RUNAWAY)"

        # Formatted Avionics Engineering Profile Output
        report = (
            "\n" + "="*60 + "\n"
            "         COLLINS-GRADE AVIONICS ECU ENG EVALUATION REPORT     \n"
            "============================================================\n"
            " SYSTEM CONTROL PERFORMANCE:\n"
            f"  ▪ Steady-State Tracking Error: {avg_ss_error:.2f}%     [Target: <0.50%]  {'[PASS]' if avg_ss_error < 0.5 else '[FAIL]'}\n"
            f"  ▪ Transient Step Overshoot:    {max_overshoot:.2f}%     [Target: <5.00%]  {'[PASS]' if max_overshoot < 5.0 else '[FAIL]'}\n"
            f"  ▪ 90% Thrust Rise Time:         {rise_time}\n\n"
            " PROPULSION & THERMO EFFICIENCY PARAMETERS:\n"
            f"  ▪ Specific Fuel Burn Index (SFC): {sfc_index:.2f} lbs/hr/%N1\n"
            f"    (Lower is more efficient - optimized for range Cruise)\n"
            f"  ▪ Peak Thermal Stress Transient:  {peak_thermal_stress:.1f} °C/sec\n"
            f"    (High stress reduces blade life cycles)\n"
            f"  ▪ Operational Thermal Margin:    {thermal_safety_margin:.2f}%\n\n"
            " REAL-TIME EMBEDDED SOFTWARE INTEGRITY (DO-178C Framework):\n"
            f"  ▪ Worst-Case Frame Jitter:     {max_jitter_ms:.3f} ms   [Target: <2.0ms]  {'[PASS]' if max_jitter_ms < 2.0 else '[FAIL/REAL-TIME FAULT]'}\n"
            f"  ▪ Critical FADEC Safe-State:   {fault_contained}\n"
            f"  ▪ Rotor Structural Breaches:   {overspeed_violations} frames overspeed\n"
            "============================================================\n"
        )
        return report
