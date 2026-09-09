# WAID Case Study: Integrating Solar-Radiation Physics into Edge Weather Nowcasting

## From Data-Driven Forecasting to Physics-Informed Inference

Machine learning models are increasingly used for local weather forecasting, but purely data-driven approaches can struggle when the available observations are sparse, irregular, or strongly dependent on deterministic environmental cycles.

This is particularly relevant for microclimate nowcasting. A local weather station can provide high-frequency measurements of temperature, humidity, pressure, wind, and solar radiation, but the model must still infer the temporal structure governing these variables.

One of the strongest deterministic signals available to a weather-forecasting system is the solar cycle.
Sunrise, solar elevation, and sunset are not predicted by the machine-learning model. They can be derived from astronomical geometry using the timestamp and the geographical coordinates of the observation site.

**WAID uses this property to introduce a physics-informed solar-radiation signal directly into the inference pipeline.**

The objective is not to replace atmospheric modelling with a simplified physical equation. Instead, the objective is to provide the LSTM with an explicit representation of a known physical structure that is available throughout the forecast horizon.

### The Architecture

The WAID inference pipeline combines observed telemetry, engineered temporal features, and a deterministic theoretical solar-radiation signal before passing the resulting tensor to the LSTM model.

Conceptually:

```text
Local telemetry
      |
      +-- Temperature
      +-- Humidity
      +-- Pressure
      +-- Wind
      +-- Other observations
      |
      v
Temporal feature engineering
      |
      +-- Cyclic time features
      +-- Theoretical solar radiation
      |
      v
Inference tensor
      |
      v
    LSTM
      |
      v
6-hour forecast
      |
      v
Live observation/reconciliation
```

The important architectural property is that the theoretical solar signal is generated at inference time.
It is not obtained from future sensor measurements.

---

### Why Solar Radiation Is a Useful Physical Signal
Many meteorological variables exhibit a strong relationship with the solar cycle. Temperature, for example, does not simply depend on the previous temperature value. Its evolution is influenced by the energy received from solar radiation, atmospheric conditions, surface characteristics, and other processes.

A purely temporal model can learn part of this relationship from historical observations. However, the model does not inherently know that the Sun will be below the horizon at a particular future timestamp. Providing a deterministic solar signal gives the model an additional source of information: **the temporal position of the atmosphere within the astronomical day/night cycle.**

This is particularly useful for a six-hour forecasting horizon because the forecast window can cross important transitions such as: **night → sunrise → daylight** or **daylight → sunset → night.**

The solar signal gives the model an explicit representation of these transitions. Computing the Theoretical Solar Signal WAID derives the solar signal from four main inputs:
- UTC-normalized timestamp 
- day of year 
- station latitude 
- station longitude 

The implementation first normalizes timestamps so that daylight-saving-time changes do not introduce artificial shifts into the astronomical calculation For each timestamp, the solar declination is estimated from the day of the year:

$$
δ=23.45^\circ \sin\left( \frac{360^\circ(284+n)}{365} \right)
$$

where *n* is the day of the year.

The station latitude and solar declination are then combined with the solar hour angle to estimate the solar elevation. The resulting relationship is based on:

$$
\sin(h) = \sin(\phi)\sin(\delta) + \cos(\phi)\cos(\delta)\cos(H)
$$

where:
- h is the solar elevation angle; 
- ϕ is the station latitude; 
- δ is the solar declination; 
- H is the solar hour angle.

The calculated elevation is then converted into a theoretical solar-radiation envelope.When the solar elevation is below the horizon, the theoretical radiation is set to zero. During daylight, the signal follows the solar elevation:

$$
R_{\mathrm{solar}} = 1000 \cdot \sin(h)
$$

with the value constrained to non-negative radiation.

This should be understood as a theoretical solar-radiation envelope, rather than a complete clear-sky radiative-transfer model. It does not attempt to model cloud attenuation, aerosol loading, atmospheric scattering, water vapour, or other atmospheric effects. Its purpose is different: **to encode the deterministic astronomical component of the day/night cycle.**

---

### Why compute it at inference time?

A particularly important property of this approach is that the solar signal can be calculated for future timestamps without accessing future observations. Suppose the model generates a six-hour forecast. For every future timestamp:
```
t + 1 hour
t + 2 hours
t + 3 hours
...
t + 6 hours
```
the theoretical solar radiation can already be calculated from: **timestamp + latitude + longitude**

No future sensor observation is required. This makes the signal available throughout the entire forecast horizon while avoiding future-observation leakage.

**Key Point
The theoretical solar-radiation signal is generated at inference time from astronomical geometry rather than observed future telemetry, providing the model with a deterministic representation of the day/night cycle over the forecast horizon.**

---

### Integrating the Signal into the LSTM Input

The solar calculation is performed while constructing the inference tensor. The WAID pipeline first generates the engineered temporal features and then computes the theoretical solar signal for the corresponding timestamps.

The resulting values are added to the engineered dataframe as:
```
df_engineered['theo_solar'] = theo_solar_vals
```
The final input tensor is then constructed from the configured model features:
```
input_data = df_engineered[env.input_features_match].values
```

Therefore, when *theo_solar* is part of the model's configured input feature set, the LSTM receives the deterministic solar signal alongside the observed and engineered variables. 

Conceptually, each timestep can be represented as:

$$
X_t =
\left[
X_t^{\mathrm{telemetry}},
X_t^{\mathrm{temporal}},
R_t^{\mathrm{solar,theoretical}}
\right]
$$

The LSTM can therefore learn relationships between local atmospheric conditions, temporal position, and the deterministic solar cycle.

---

### Physics-Informed Does Not Mean Physics-Complete
An important distinction is necessary.

The WAID model is not a numerical weather prediction system, nor does the solar-radiation function attempt to reproduce the complete physics of atmospheric radiative transfer.

The physical component is deliberately narrow. It encodes a known deterministic relationship: **the position of the Sun relative to the observation point over time.**

The LSTM remains responsible for learning the complex relationship between the available environmental variables and the forecast target. The solar component provides additional physical context. This makes the approach better described as physics-informed machine learning rather than a fully physics-based forecasting model.

**Why this is different from a simple Day/Night flag**. 
A binary feature such as: **day = 1**, **night = 0**, contains only categorical information.

The theoretical solar-radiation signal contains substantially more structure. It provides a continuous representation of the solar cycle:

```text
        night
            ↓
        sunrise
        ↓
        increasing solar elevation
            ↓
        maximum solar elevation
        ↓
        decreasing solar elevation
            ↓
        sunset
        ↓
        night

The shape of this signal changes with:
    - latitude; 
    - longitude; 
    - day of the year; 
    - timestamp.
```
This makes it a richer representation of the astronomical forcing than a simple day/night indicator.

---

### Time Zones and Daylight Saving Time

Time handling is particularly important when deriving astronomical features. Civil time can change because of daylight-saving rules, while the underlying solar geometry does not suddenly shift by one hour because a jurisdiction changes its clock.

WAID therefore normalizes timestamps to **UTC** before performing the solar calculation.
For timestamps without timezone information, the pipeline first localizes them using the configured station timezone and then converts them to **UTC**.

This separation between: *civil time* and *astronomical time* helps prevent artificial discontinuities in the solar feature caused by timezone or daylight-saving transitions.

---

### Physics Meets Edge Inference

The implementation is particularly relevant to the edge architecture of **WAID**.
The theoretical solar signal requires no external weather API, no future telemetry, and no additional network request.
Once the station coordinates are known, the signal can be generated locally.
This means the edge node can construct the complete inference tensor even when connectivity to external services is temporarily unavailable.

The physical feature is therefore:
- deterministic; 
- computationally inexpensive; 
- locally reproducible; 
- independent of future observations; 
- available across the entire forecast horizon. 

This is an important property for an edge-native forecasting architecture.

---

### From Prediction to Reconciliation

The physical solar signal is only one component of **WAID**'s broader forecasting architecture. The system does not assume that adding a physically meaningful feature automatically produces a better forecast.

Instead, **WAID** continuously compares predictions with incoming station telemetry.

This creates a feedback loop:
```text
        Physical context
            +
        Historical telemetry
            +
        Current observations
            ↓
           LSTM
            ↓
        6h forecast
            ↓
        Real-world observations
            ↓
        Reconciliation
            ↓
        MAE / bias / drift analysis
```

The distinction is important. The solar model provides a deterministic physical reference.

The LSTM provides the learned forecast. The live telemetry provides the real-world reference against which the forecast can be evaluated.

---

### Why this matters for microclimate forecasting

Global reanalysis products such as **ERA5** provide valuable atmospheric context, but they do not necessarily capture the full dynamics of a specific local environment.

A local station can observe conditions that differ from the broader-scale atmospheric representation.

**WAID** therefore combines:
```text
    Global-scale information
            +
    Local observations
            +
    Deterministic astronomical information
            ↓
    Local forecasting
```

The theoretical solar-radiation feature contributes a third dimension to this architecture. It is neither purely observational nor purely statistical. It represents a deterministic environmental process that can be computed independently of the sensor network.

---

### A Practical Physics-Informed Pattern

The approach used by **WAID** illustrates a broader pattern for machine-learning systems operating at the edge: **use machine learning for what must be learned, and deterministic knowledge for what can already be known.** The astronomical position of the Sun does not need to be learned from historical weather observations. It can be calculated.

The relationship between that solar forcing and local temperature, humidity, or other meteorological variables is considerably more complex. That relationship is where machine learning becomes useful. This separation can reduce the burden on the model while giving the forecasting pipeline explicit information about a deterministic component of the environment.

---

### Conclusion

**WAID integrates a theoretical solar-radiation signal directly into its LSTM inference tensor as a physics-informed feature.**

The signal is generated locally and deterministically from timestamp, day of year, latitude, and longitude. It represents the astronomical day/night cycle over the complete six-hour forecast horizon without relying on future observed telemetry. The approach does not attempt to replace atmospheric physics with machine learning, nor does it claim to provide a complete physical weather model.

Instead, it establishes a practical boundary between: **what can be calculated deterministically** and **what must be learned from data.**

For an edge-native weather forecasting system, this provides a lightweight way to inject known physical structure into a data-driven model while preserving the operational advantages of local inference.

The resulting architecture is therefore not simply: **telemetry → LSTM → forecast** but **telemetry + temporal structure + deterministic solar physics → LSTM → forecast → live reconciliation.**

That combination is the core idea behind the **physics-informed component of WAID**.
