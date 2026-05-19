"""
E-Bike Acceleration Curve Simulator
Plots speed vs time with constraint region annotations for multiple bikes.
"""

import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches


def simulate_bike(params, dt=0.05, t_max=60.0):
    """
    Simulate e-bike acceleration from standstill.

    params: dict with keys:
        Kt        - torque constant (Nm/A)
        R         - phase-to-phase winding resistance (Ohm)
        Voc       - battery open circuit voltage (V)
        Rbat      - battery internal resistance (Ohm)
        I_bat_max - controller battery current limit (A)
        I_phase_max - controller phase current limit (A)
        G         - gear ratio (motor_rpm / wheel_rpm)
        Rw        - wheel radius (m)
        m         - total mass bike+rider (kg)
        CdA       - drag coefficient * frontal area (m^2)
        Cr        - rolling resistance coefficient

    Returns: t_arr, v_arr, constraint_arr
        constraint_arr: 0=phase limit, 1=battery limit, 2=voltage limit
    """
    Kt = params['Kt']
    Ke = Kt  # Kt = Ke in SI for ideal BLDC
    R = params['R']
    Voc = params['Voc']
    Rbat = params['Rbat']
    I_bat_max = params['I_bat_max']
    I_phase_max = params['I_phase_max']
    G = params['G']
    Rw = params['Rw']
    m = params['m']
    CdA = params['CdA']
    Cr = params['Cr']

    rho = 1.225  # air density kg/m^3
    g = 9.81

    steps = int(t_max / dt)
    t_arr = np.zeros(steps)
    v_arr = np.zeros(steps)
    constraint_arr = np.zeros(steps, dtype=int)

    v = 0.0
    t = 0.0

    for i in range(steps):
        t_arr[i] = t
        v_arr[i] = v

        # Motor angular velocity
        omega_motor = v * G / Rw
        E = Ke * omega_motor  # back-EMF

        # Constraint 1: Phase current limit
        I1 = I_phase_max

        # Constraint 2: Battery current limit
        # Power available from battery at max battery current
        V_bat_at_max = Voc - I_bat_max * Rbat
        P_bat = V_bat_at_max * I_bat_max
        # Solve: R*I^2 + E*I - P_bat = 0
        discriminant2 = E**2 + 4 * R * P_bat
        if discriminant2 > 0:
            I2 = (-E + np.sqrt(discriminant2)) / (2 * R)
        else:
            I2 = 0.0

        # Constraint 3: Voltage limit (D=1, full duty)
        # At full duty: I_bat = I_motor, V_bat = Voc - I_motor*Rbat = E + I_motor*R
        # => I_motor = (Voc - E) / (R + Rbat)
        I3 = (Voc - E) / (R + Rbat)

        # Active constraint is whichever gives lowest current
        I_candidates = [I1, I2, I3]
        # Filter out negative (motor can't regenerate here)
        I_candidates_clipped = [max(0.0, ic) for ic in I_candidates]
        I_actual = min(I_candidates_clipped)
        constraint = I_candidates_clipped.index(I_actual)
        constraint_arr[i] = constraint

        # Torque and force
        T_motor = Kt * I_actual
        T_wheel = T_motor * G
        F_tract = T_wheel / Rw

        # Resistive forces
        F_drag = 0.5 * rho * CdA * v**2
        F_roll = Cr * m * g

        # Net force and acceleration
        F_net = F_tract - F_drag - F_roll
        a = F_net / m
        if a < 0 and v <= 0:
            a = 0.0  # can't go backwards

        # Euler integration
        v = v + a * dt
        if v < 0:
            v = 0.0
        t = t + dt

        # Stop if acceleration is negligible and near top speed
        if i > 10 and abs(a) < 0.001 and v > 1.0:
            # Fill rest with steady state
            t_arr[i+1:] = np.linspace(t, t + dt * (steps - i - 1), steps - i - 1)
            v_arr[i+1:] = v
            constraint_arr[i+1:] = constraint
            break

    return t_arr, v_arr, constraint_arr


class EBikeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Bike Acceleration Simulator")
        self.root.geometry("1200x800")

        self.bikes = []  # list of (name, params, t, v, constraints)

        # Main layout: left panel for inputs, right for plot
        left_frame = ttk.Frame(root, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = ttk.Frame(root, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Input fields
        ttk.Label(left_frame, text="E-Bike Parameters", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 10))

        self.entries = {}
        fields = [
            ("name", "Bike Name", "Bike 1"),
            ("Kt", "Kt - Torque Constant (Nm/A)", "0.1"),
            ("R", "R - Winding Resistance (Ω)", "0.1"),
            ("Voc", "Voc - Battery Voltage OCV (V)", "72"),
            ("Rbat", "Rbat - Battery Int. Resistance (Ω)", "0.15"),
            ("I_bat_max", "I_bat_max - Battery Current Limit (A)", "80"),
            ("I_phase_max", "I_phase_max - Phase Current Limit (A)", "120"),
            ("G", "G - Gear Ratio (motor/wheel)", "5"),
            ("Rw", "Rw - Wheel Radius (m)", "0.33"),
            ("m", "m - Total Mass bike+rider (kg)", "140"),
            ("CdA", "CdA - Drag Coeff × Area (m²)", "0.5"),
            ("Cr", "Cr - Rolling Resistance Coeff", "0.01"),
            ("t_max", "Simulation Time (s)", "60"),
        ]

        for i, (key, label, default) in enumerate(fields):
            ttk.Label(left_frame, text=label).grid(row=i+1, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(left_frame, width=15)
            entry.insert(0, default)
            entry.grid(row=i+1, column=1, pady=2, padx=(5, 0))
            self.entries[key] = entry

        row_after = len(fields) + 1

        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=row_after, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Add Bike & Plot", command=self.add_bike).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Bike list
        ttk.Label(left_frame, text="Added Bikes:", font=("Arial", 10, "bold")).grid(
            row=row_after+1, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))

        self.bike_listbox = tk.Listbox(left_frame, height=8, width=30)
        self.bike_listbox.grid(row=row_after+2, column=0, columnspan=2, sticky=tk.W)

        ttk.Button(left_frame, text="Remove Selected", command=self.remove_bike).grid(
            row=row_after+3, column=0, columnspan=2, pady=5)

        # Matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax_v = self.fig.add_subplot(211)
        self.ax_a = self.fig.add_subplot(212)
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM)

        # Constraint colors
        self.constraint_colors = ['#2196F3', '#FF9800', '#F44336']  # blue, orange, red
        self.constraint_labels = ['Phase Current Limit', 'Battery Current Limit', 'Voltage Limit']

        # Bike line colors cycle
        self.line_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                           '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

    def get_params(self):
        try:
            params = {
                'Kt': float(self.entries['Kt'].get()),
                'R': float(self.entries['R'].get()),
                'Voc': float(self.entries['Voc'].get()),
                'Rbat': float(self.entries['Rbat'].get()),
                'I_bat_max': float(self.entries['I_bat_max'].get()),
                'I_phase_max': float(self.entries['I_phase_max'].get()),
                'G': float(self.entries['G'].get()),
                'Rw': float(self.entries['Rw'].get()),
                'm': float(self.entries['m'].get()),
                'CdA': float(self.entries['CdA'].get()),
                'Cr': float(self.entries['Cr'].get()),
            }
            t_max = float(self.entries['t_max'].get())
            name = self.entries['name'].get().strip()
            if not name:
                name = f"Bike {len(self.bikes) + 1}"
            return name, params, t_max
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return None, None, None

    def add_bike(self):
        name, params, t_max = self.get_params()
        if params is None:
            return

        t_arr, v_arr, constraint_arr = simulate_bike(params, dt=0.05, t_max=t_max)

        self.bikes.append((name, params, t_arr, v_arr, constraint_arr))
        self.bike_listbox.insert(tk.END, name)
        self.update_plot()

        # Auto-increment bike name
        try:
            num = int(name.split()[-1])
            self.entries['name'].delete(0, tk.END)
            base = ' '.join(name.split()[:-1])
            self.entries['name'].insert(0, f"{base} {num + 1}")
        except (ValueError, IndexError):
            pass

    def remove_bike(self):
        sel = self.bike_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.bikes.pop(idx)
        self.bike_listbox.delete(idx)
        self.update_plot()

    def clear_all(self):
        self.bikes.clear()
        self.bike_listbox.delete(0, tk.END)
        self.update_plot()

    def update_plot(self):
        self.ax_v.clear()
        self.ax_a.clear()

        if not self.bikes:
            self.ax_v.set_title("Speed vs Time")
            self.ax_v.set_xlabel("Time (s)")
            self.ax_v.set_ylabel("Speed (km/h)")
            self.ax_a.set_title("Acceleration vs Time")
            self.ax_a.set_xlabel("Time (s)")
            self.ax_a.set_ylabel("Acceleration (m/s²)")
            self.canvas.draw()
            return

        for idx, (name, params, t_arr, v_arr, constraint_arr) in enumerate(self.bikes):
            color = self.line_colors[idx % len(self.line_colors)]
            v_kmh = v_arr * 3.6  # m/s to km/h

            # Plot speed curve with constraint coloring
            # Break into segments by constraint
            self._plot_colored_line(self.ax_v, t_arr, v_kmh, constraint_arr, color, name)

            # Compute acceleration from velocity
            dt = t_arr[1] - t_arr[0] if len(t_arr) > 1 else 0.05
            a_arr = np.gradient(v_arr, dt)
            # Smooth acceleration for display
            kernel_size = max(1, int(0.5 / dt))
            if kernel_size > 1 and len(a_arr) > kernel_size:
                kernel = np.ones(kernel_size) / kernel_size
                a_arr_smooth = np.convolve(a_arr, kernel, mode='same')
            else:
                a_arr_smooth = a_arr

            self._plot_colored_line(self.ax_a, t_arr, a_arr_smooth, constraint_arr, color, name)

        # Legend for constraint colors
        constraint_patches = [
            mpatches.Patch(color=self.constraint_colors[i], alpha=0.3, label=self.constraint_labels[i])
            for i in range(3)
        ]
        self.ax_v.legend(loc='lower right', fontsize=8)
        self.ax_a.legend(loc='upper right', fontsize=8)

        # Add constraint color legend to top plot
        legend2 = self.ax_v.legend(
            handles=constraint_patches,
            loc='upper right', fontsize=7, title="Active Constraint")
        self.ax_v.add_artist(legend2)
        # Re-add line legend
        self.ax_v.legend(loc='lower right', fontsize=8)

        self.ax_v.set_title("Speed vs Time")
        self.ax_v.set_xlabel("Time (s)")
        self.ax_v.set_ylabel("Speed (km/h)")
        self.ax_v.grid(True, alpha=0.3)

        self.ax_a.set_title("Acceleration vs Time")
        self.ax_a.set_xlabel("Time (s)")
        self.ax_a.set_ylabel("Acceleration (m/s²)")
        self.ax_a.grid(True, alpha=0.3)

        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

    def _plot_colored_line(self, ax, t_arr, y_arr, constraint_arr, base_color, label):
        """Plot a line with background shading colored by active constraint."""
        # Plot the main line
        ax.plot(t_arr, y_arr, color=base_color, linewidth=1.5, label=label)

        # Add constraint shading
        # Find contiguous segments of same constraint
        segments = []
        if len(constraint_arr) == 0:
            return

        start = 0
        current = constraint_arr[0]
        for i in range(1, len(constraint_arr)):
            if constraint_arr[i] != current:
                segments.append((start, i - 1, current))
                start = i
                current = constraint_arr[i]
        segments.append((start, len(constraint_arr) - 1, current))

        y_min = np.min(y_arr)
        y_max = np.max(y_arr)
        if y_max == y_min:
            y_max = y_min + 1

        for seg_start, seg_end, constraint in segments:
            ax.axvspan(t_arr[seg_start], t_arr[seg_end],
                      alpha=0.08, color=self.constraint_colors[constraint])


def main():
    root = tk.Tk()
    app = EBikeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
