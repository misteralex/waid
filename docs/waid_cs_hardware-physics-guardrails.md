### Hardware-Aware Edge ML: Adapting Physics Guardrails via Empirically Computed Sensor Resolution

A major friction point in deployment-ready Edge AI for weather nowcasting is the disconnect between continuous model outputs and physical hardware realities. Standard Machine Learning models often generate floating-point predictions that violate hardware capabilities—such as predicting $0.03 \text{ mm}$ of rainfall when the physical tipping bucket has a minimum mechanical threshold of $0.1 \text{ mm}$ or $0.2 \text{ mm}$.

To overcome this, **WAID** introduces an end-to-end pipeline that first **empirically profiles** the physical telemetry to calculate real-world sensor resolutions, and then applies these specs as **physics-informed guardrails** during edge inference.

---

### 1. Dynamic Sensor Profiling: Empirically Computing Hardware Specs

Rather than relying purely on static datasheet assumptions, **WAID** executes an empirical profiling module (`waid_04_1_setup_specs.py`) that learns the operational characteristics directly from recent field telemetry (e.g., a 14-day rolling window of `ecowitt_records`):

* **Empirical Resolution Extraction:** The system evaluates consecutive telemetry deltas using non-zero differences (`np.diff`). By taking the 25th percentile of these deltas, it dynamically computes the actual reporting resolution ($\text{res}$) for temperature, pressure, humidity, and solar irradiance.
* **Deadband & Cut-In Speed Identification:**
* **Anemometer Cut-In Threshold:** Computes the lower 10th percentile of non-zero wind readings to identify the mechanical starting threshold of the anemometer.
* **Rain Gauge Bucket Capacity:** Pinpoints the precise tipping bucket volume by extracting the minimum non-zero value (`non_zero.min()`) directly from raw precipitation logs.


* **Metadata Persistence:** The computed specifications are serialized into JSON and stored within the local SQLite `station_metadata` store per `station_id`. This creates a hardware-aware profile that automatically adjusts if sensors age, degrade, or get replaced.

---

### 2. Downstream Inference Guardrails (`apply_physics_guardrails`)

Once the real-world resolution and deadbands are computed, the edge inference pipeline utilizes these empirical metrics to constrain model predictions:

* **Hardware-Aware Quantization & Denoising:** Raw floating-point ML outputs are quantized directly to match the computed sensor resolution ($\text{res}$):

$$\text{Output} = \text{round}\left(\frac{\text{Prediction}}{\text{res}}\right) \times \text{res}$$



Signal values falling below half the computed resolution threshold ($\text{res} / 2.0$) are treated as physical noise and suppressed to zero.

* **Astronomical Solar Capping:** Integrates deterministic solar geometry equations to enforce a strict upper boundary on predicted solar radiation, automatically zeroing out irradiance during astronomical night ($\text{theo}\_\text{solar} \le 0.0$).                                                  
* **Physical Boundary Enforcement:** Enforces strict non-negativity for physical parameters (wind, rain, solar, humidity) while preserving sub-zero dynamics strictly for ambient temperature.

---

### Why This Matters for Ecowitt Integration

This empirical feedback loop transforms raw ML inference into **hardware-aligned edge intelligence**. By deriving sensor capabilities dynamically from actual measurement streams rather than theoretical defaults, **WAID** ensures that edge predictions strictly conform to Ecowitt hardware behavior, eliminate model hallucinations, and remain resilient to real-world sensor drift.