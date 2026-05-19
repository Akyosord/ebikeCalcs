# E-Bike Acceleration Simulator

A browser-based tool to compare acceleration curves of different electric bikes based on their motor/battery/controller specs.

## Features

- **Speed vs Time** and **Acceleration (g's) vs Time** charts for multiple bikes
- **Constraint visualization**: line style shows which physical limit is active (phase current, battery current, or voltage)
- **Excel-like grid** for entering/editing bike parameters
- **Voltage slider** to simulate state-of-charge effects (+15% to -20%)
- **Auto-save/load** bike data to JSON
- **Full equation derivation** section explaining the physics

## Quick Start

```bash
python server.py
```

Opens `http://localhost:8080` in your browser.

## Parameters

| Type | Fields |
|------|--------|
| **Input** | Top Speed (mph), Motor Peak Power (W), Battery Max Current (A), Controller Phase Current (A) |
| **Assumption** | Battery Voltage, Internal Resistances, Gear Ratio, Wheel Size, Mass, Aero Drag, Rolling Resistance |
| **Calculated** | Kt (torque constant), Ke (back-EMF constant) |

## Tech Stack

- Single HTML file with vanilla JS
- Plotly.js for interactive charts
- KaTeX for LaTeX equation rendering
- Python `http.server` for save/load API
- No build step, no frameworks

---

## Full Derivation

### 1. The Motor — Converting Electricity to Spinning

A BLDC hub motor uses permanent magnets and copper coils. Two constants define it:

**Torque constant** — torque produced per ampere:

$$T = K_t \cdot I$$

**Back-EMF constant** — voltage generated per unit of angular velocity:

$$E = K_e \cdot \omega$$

For any BLDC motor (from energy conservation):

$$K_t = K_e \quad \text{(in SI units: Nm/A = V·s/rad)}$$

### 2. The Electrical Equation — Voltage Budget

The battery voltage must be divided among three consumers:

$$V_{oc} = \underbrace{K_e \cdot \omega}_{\text{back-EMF}} + \underbrace{I \cdot R_{\text{wind}}}_{\text{motor heat}} + \underbrace{I_{\text{bat}} \cdot R_{\text{bat}}}_{\text{battery sag}}$$

As speed $\omega$ increases, back-EMF grows, leaving less voltage to push current. At top speed, nearly all voltage is consumed by back-EMF.

### 3. Deriving $K_t$ from Top Speed

At top speed (steady state), the motor only overcomes drag and rolling resistance:

$$F_{\text{drag}} = \frac{1}{2} \rho \cdot C_d A \cdot v_{\text{top}}^2$$

$$F_{\text{roll}} = C_r \cdot m \cdot g$$

$$P_{\text{cruise}} = (F_{\text{drag}} + F_{\text{roll}}) \cdot v_{\text{top}}$$

Cruise current:

$$I_{\text{cruise}} \approx \frac{P_{\text{cruise}}}{V_{oc}}$$

Motor angular velocity (hub motor, $G=1$):

$$\omega_{\text{top}} = \frac{v_{\text{top}}}{R_{\text{wheel}}}$$

Solving the voltage equation for $K_e$:

$$\boxed{K_t = K_e = \frac{V_{oc} - I_{\text{cruise}} \cdot (R_{\text{wind}} + R_{\text{bat}})}{\omega_{\text{top}}}}$$

### 4. Three Constraint Zones & Transitions

At any speed, three limits cap the motor current. The **lowest wins**:

#### Zone 1: Phase Current Limit (constant torque)

$$I_1 = I_{\text{phase,max}} \quad \Rightarrow \quad T_1 = K_t \cdot I_{\text{phase,max}}$$

At low speed, back-EMF is small and the controller can push max current. Torque is constant — this is your hardest launch.

#### Zone 2: Battery Current Limit (constant power)

$$P_{\text{bat}} = (V_{oc} - I_{\text{bat,max}} \cdot R_{\text{bat}}) \cdot I_{\text{bat,max}}$$

$$I_2 = \frac{-E + \sqrt{E^2 + 4 R_{\text{wind}} \cdot P_{\text{bat}}}}{2 R_{\text{wind}}}$$

As speed rises, maintaining phase current requires more power. When battery power hits its limit, the controller reduces phase current. Torque falls as ~$1/\omega$.

#### Zone 3: Voltage Limit (back-EMF dominated)

$$I_3 = \frac{V_{oc} - K_e \cdot \omega}{R_{\text{wind}} + R_{\text{bat}}}$$

At very high speed, back-EMF approaches battery voltage. Current drops linearly to zero.

#### Transition Points

**Zone 1 → Zone 2** occurs when battery power needed to sustain full phase current exceeds the battery's max:

$$v_{1 \to 2} \approx \frac{P_{\text{bat,max}} \cdot R_w}{K_t \cdot I_{\text{phase,max}}}$$

**Zone 2 → Zone 3** occurs when voltage-limited current drops below battery-limited current:

$$\frac{V_{oc} - K_e \omega}{R_{\text{wind}} + R_{\text{bat}}} < I_2(\omega)$$

**Physical intuition:**
- **Zone 1→2:** "The battery can't keep up." Power demand exceeds supply.
- **Zone 2→3:** "The motor is fighting itself." Back-EMF is so large that Ohm's law limits current regardless of available power.

### 5. From Torque to Acceleration

Actual current at any speed:

$$I_{\text{actual}}(\omega) = \min(I_1,\; I_2,\; I_3)$$

Force at wheel (hub motor):

$$F_{\text{traction}} = \frac{K_t \cdot I_{\text{actual}}}{R_{\text{wheel}}}$$

Net force:

$$F_{\text{net}} = F_{\text{traction}} - \frac{1}{2}\rho \, C_dA \, v^2 - C_r \, m \, g$$

Newton's second law:

$$\boxed{a = \frac{F_{\text{net}}}{m}}$$

Integrated via Euler's method:

$$v(t + \Delta t) = v(t) + a(t) \cdot \Delta t$$

### 6. Why Higher Wattage ≠ Faster Launch

For a hub motor on the same voltage:

$$\boxed{F_{\text{launch}} \approx \frac{V_{oc} \cdot I_{\text{phase}}}{v_{\text{top}}}}$$

Wheel radius cancels out! A "9000W" motor with higher top speed has lower $K_t$, producing **less** launch force at the same current than a "6000W" motor with lower top speed.

$\text{Power} = \text{Torque} \times \text{Speed}$. High watts can come from modest torque at high RPM.

### 7. Voltage & State of Charge

$$V_{\text{actual}} = V_{\text{nominal}} \times (1 + \text{slider\%})$$

| State | Voltage |
|-------|---------|
| Fully charged (100% SOC) | ≈ +15% above nominal |
| Mid charge (50% SOC) | 0% — nominal |
| Nearly empty (20% SOC) | ≈ −14% below nominal |
| Under heavy load | Additional sag: $\Delta V = I_{\text{bat}} \cdot R_{\text{bat}}$ |

Higher voltage → more headroom above back-EMF → more current → more torque → faster acceleration.
