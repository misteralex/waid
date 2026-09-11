# Hardware-Aware Physics Guardrails: Combining Dynamic Telemetry Profiling and Defensive Hardware Specs for Edge ML Nowcasting

### Abstract

Deploying Machine Learning (ML) predictions to Edge AI systems for local weather nowcasting presents a fundamental challenge: standard deep learning architectures (such as LSTMs) yield continuous floating-point values that frequently violate physical reality and hardware boundaries. Predictions like $-0.04 \text{ m/s}$ wind speed, $0.03 \text{ mm}$ rainfall on a $0.2 \text{ mm}$ mechanical tipping bucket, or nighttime solar irradiance introduce model noise, degrade trust, and waste database bandwidth.

To bridge the gap between continuous ML outputs and physical edge capabilities, the **WAID** (Weather AI Direct) framework implements a hybrid pipeline: **dynamic empirical profiling**, **centralized nominal fallback specs**, and **astronomical physics guardrails**.

---

## 1. System Architecture: Centralized & Dynamic Metadata Pipeline

The metadata architecture centers around two complementary mechanisms: a single source of truth for nominal hardware capabilities (`NOMINAL_SENSOR_SPECS` in `waid_shared.py`) and a profiling script (`waid_04_1_setup_specs.py`) that analyzes operational telemetry.

```
       +------------------------------------+
       |   NOMINAL_SENSOR_SPECS (Shared)    |
       |  Defines theoretical factory specs |
       +-----------------+------------------+
                         |
                         v
       +-----------------+------------------+
       |      get_station_metadata (DB)     |
       |           Reads DB specs           |
       |      with nominal fallbacks        |
       +-----------------+------------------+
                         |
                         v
       +-----------------+------------------+
       | Empirical Profiling (14-Day Window)|
       | Evaluates deltas & mode resolution |
       +-----------------+------------------+
                         |
                         v
       +-----------------+------------------+
       |     Physics Guardrails Engine      | 
       |           (Inference)              |
       |  Clipping, Quantization, Low-Pass  |
       +------------------------------------+

```

1. **Centralized Baseline Defaults:** System-wide fallback parameters are declared in a shared constant `NOMINAL_SENSOR_SPECS` and delivered via `get_station_metadata`, ensuring robust execution even when database tables are empty or uninitialized.
2. **Empirical Diagnostics (`profile_or_default_specs`):** Evaluates rolling telemetry (e.g., 14-day history across 430,000+ records) to compute effective data granularity and identify operational cut-in thresholds (e.g., anemometer deadbands).
3. **Persisted Hardware Awareness:** Empirical results are serialized into the SQLite `station_metadata` table per `station_id`, creating an adaptive hardware profile.

---

## 2. Dynamic Diagnostics & Key Empirical Findings

Running the empirical diagnostic suite over **433,456 historical records** revealed critical insights into the relationship between physical hardware, firmware transformations, and database representations:

| Feature | Nominal Spec | Profiled Empirical | System Status | Hardware vs. Firmware Insight |
| --- | --- | --- | --- | --- |
| **Temperature** | $0.1\text{ }^\circ\text{C}$ | $0.10\text{ }^\circ\text{C}$ | **✅ Match** | Strict adherence to physical sensor specifications. |
| **Humidity** | $1.0\text{ }\%$ | $1.00\text{ }\%$ | **✅ Match** | Strict adherence to physical sensor specifications. |
| **Pressure** | $0.1\text{ hPa}$ | $0.10\text{ hPa}$ | **✅ Match** | Strict adherence to physical sensor specifications. |
| **Wind Speed** | $0.1\text{ m/s}$ | $0.10\text{ m/s}$ | **✅ Match** | Strict adherence to physical sensor specifications. |
| **Solar Irradiance** | $0.1\text{ W/m}^2$ | $0.01\text{ W/m}^2$ | **⚠️ Low-Pass Filtered** | Firmware converts Lux to $\text{W/m}^2$ ($\times 0.0079$), introducing artificial sub-grid steps. |
| **Hourly Rain** | $0.2\text{ mm}$ | $0.10\text{ mm}$ | **🛡️ Defensive Nominal** | Physical bucket capacity is $0.2\text{ mm}$; time-window averaging produces artificial $0.1\text{ mm}$ steps. |

---

## 3. The Inference Guardrail Execution Sequence (`apply_physics_guardrails`)

During post-processing, raw continuous predictions pass through three sequential filtering stages:

### A. Physical & Astronomical Boundary Enforcement

* **Non-Negativity Clipping:** Enforces strict non-negativity ($x \ge 0$) for wind, rain, solar irradiance, and humidity, while preserving sub-zero dynamics strictly for temperature.
* **Deterministic Solar Capping:** Integrates solar geometry equations (Clear-Sky models). When theoretical astronomical irradiance is zero ($\text{theo}\_\text{solar} \le 0.0$), predicted solar values are immediately hard-clipped to zero, eliminating nighttime model hallucinations.

### B. Hardware-Aware Discretization & Noise Suppression

* **Sensitivity Thresholding (Deadband Filtering):** Signal values falling below half the target resolution ($\text{res} / 2.0$) or below mechanical activation thresholds (e.g., anemometer cut-in speed) are suppressed to zero:

$$x_{\text{filtered}} = \begin{cases} 0 & \text{if } x < \frac{\text{res}}{2.0} \\ x & \text{otherwise} \end{cases}$$

* **Hardware Quantization:** Discretizes model outputs to match exact hardware grid steps:

$$\text{Output} = \text{round}\left(\frac{x}{\text{res}}\right) \times \text{res}$$

---

## 4. Architectural Trade-Offs & Defensive Strategy

### Hardware Reality vs. Firmware Noise Filtering

Empirical profiling can detect artificial granularity introduced by firmware multipliers or gateway windowing. The WAID architecture balances these empirical findings against physical realities:

* **Low-Pass Filtering for Solar Irradiance:** While firmware Lux conversions yield a $0.01\text{ W/m}^2$ grid, forcing an LSTM to predict at this precision causes it to learn high-frequency noise. Setting the guardrail resolution to $0.1\text{ W/m}^2$ acts as a natural low-pass filter.
* **Defensive Baseline for Rain Gauges:** Mechanical tipping buckets operate at discrete steps ($0.2\text{ mm}$). Even if gateway temporal averaging introduces intermediate $0.1\text{ mm}$ steps, maintaining $0.2\text{ mm}$ as the baseline guardrail protects the ML model from false activations caused by floating-point conversion artifacts.

---

## 5. Summary Parameters

```python
# System Nominal Sensor Specifications (waid_shared.py)
NOMINAL_SENSOR_SPECS = {
    "ecowitt_temp": {"resolution": 0.1, "deadband": 0.0},
    "ecowitt_rh": {"resolution": 1.0, "deadband": 0.0},
    "ecowitt_pres": {"resolution": 0.1, "deadband": 0.0},
    "ecowitt_wind": {"resolution": 0.1, "deadband": 0.2},
    "ecowitt_solar": {"resolution": 0.1, "deadband": 0.0},  # Low-pass filter target
    "ecowitt_rain": {"resolution": 0.2, "deadband": 0.2},  # Defensive mechanical threshold
}

```

By pairing dynamic telemetry profiling with centralized defensive guardrails, **WAID** ensures edge nowcasting models remain physically consistent, resilient to sensor drift, and aligned with operational hardware.