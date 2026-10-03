# WAID Data Tensors Feature Store (`waid/data/tensors`)

This directory acts as the core **Feature Store** for the WAID machine learning pipeline. It stores preprocessed temporal data structured into **Sliding Windows** to feed deep learning models (such as LSTMs) efficiently, avoiding raw SQL overhead during training.

## Role of `waid_05_1_ml_tensors.py`

`waid_05_1_ml_tensors.py` is the data preparation script responsible for transforming raw SQLite database records into structured training tensors. 

### Key Responsibilities:
1. **Feature Engineering & Alignment:** Extracts raw weather data, computes cyclical temporal features, and aligns theoretical solar radiation.
2. **Sliding Window Generation:** Slices historical continuous series into fixed-size temporal lookbacks and forecast horizons.
3. **Delta Nowcasting Formulation:** Computes future target variables as deltas (variations) relative to the present moment rather than absolute values, stabilizing network convergence.
4. **Monthly Persistence:** Serializes processed arrays into a structured "trinity" of monthly Pickle (`.pkl`) files per month (from `2025_11` onward):
   - **`X_raw_YYYY_MM.pkl`**: Past 24-hour input matrix (Shape: `(Samples, 24, 11)`).
   - **`Y_raw_YYYY_MM.pkl`**: Next 6-hour target variation matrix (Shape: `(Samples, 6, 6)`).
   - **`timestamps_YYYY_MM.pkl`**: Reference timestamps for physical alignment and data lineage (Shape: `(Samples,)`).

By executing this preprocessing step once, subsequent model training (`waid_05_2_ml_train.py`) achieves high memory efficiency and lightning-fast I/O performance via `tf.data` pipelines.

# The `waid/data/tensors` Folder

This folder serves as the **Data Feature Store** heart of the Machine Learning pipeline.

To train a Deep Learning model (such as the LSTM network used by WAID) on temporal data, SQL tables cannot be passed as-is. Data must be restructured into **Sliding Windows**.

The files in the `data/tensors` folder are divided by **month** (from `2025_11` to `2026_09`). For each month, you will find a "trinity" of files (`X_raw`, `Y_raw`, `timestamps`). Below is the detailed role of each component:

---

### 1. `X_raw_YYYY_MM.pkl` (The Inputs / The Past)
Represents the **input** matrix that the model uses to understand recent weather conditions.
* **Content:** A time series sequence of the last **24 hours (Lookback)** for each time step $t$.
* **Shape:** `(Samples, 24, 11)`
  * *Samples:* Number of time steps in that month (approximately 720 hours/samples per month).
  * *24:* Past hours analyzed by the model to detect the trend (time window).
  * *11:* The 11 aligned features (6 weather + 4 cyclical temporal + 1 theoretical radiation).
* **Role:** Acts as the model's "rearview mirror." The LSTM reads these 24 hours of data to understand if pressure is dropping, temperature is rising, etc.

---

### 2. `Y_raw_YYYY_MM.pkl` (The Targets / The Future)
Represents the **labels** matrix, defining what the model must learn to predict.
* **Content:** Variations of the 6 weather variables over the **next 6 hours (Forecast Horizon)** relative to the current time step $t$.
* **Shape:** `(Samples, 6, 6)`
  * *Samples:* Exact same number of samples as $X$ (perfectly aligned).
  * *6:* Future hours to forecast ($t+1, t+2, ..., t+6$).
  * *6:* Target weather variables (Temperature, Humidity, Pressure, Wind, Solar Radiation, Rain).
* **The "Delta" Concept ($Y$):** The model does not predict absolute future values (e.g., "it will be 18°C in 3 hours"), but rather the **variation** compared to the current time step (e.g., "it will be $+1.2^\circ\text{C}$ compared to now"). This *Delta Nowcasting* approach makes the model infinitely more accurate and stable.

---

### 3. `timestamps_YYYY_MM.pkl` (The Timeline / The Anchor)
This file is not fed directly into the neural network, but it is essential for system management and data alignment.
* **Content:** A list of individual timestamps. Each timestamp represents the exact time $t$ (the present) referenced by each sample in $X$ and $Y$.
* **Shape:** `(Samples,)` (one-dimensional vector).
* **Role:** 
  1. **Physical Data Alignment:** Allows `waid_05_2` to know the exact hour corresponding to row `i` of the tensor, enabling millimetric precision when calculating theoretical solar radiation for that specific moment.
  2. **Data Lineage:** If the model makes a prediction error during testing, this file allows you to trace back to the exact day and hour of the failure.

---

### A Practical Example: How these 3 files cooperate

Imagine it is **November 15, 2025 at 12:00 PM** (our time step $t$):

1. **`X_raw_2025_11.pkl`** (at the corresponding row) provides the model with weather data recorded from **November 14 at 12:00 PM** to **November 15 at 11:00 AM** (the past 24 hours).
2. **`timestamps_2025_11.pkl`** contains the string `"2025-11-15 12:00:00"`.
3. **`Y_raw_2025_11.pkl`** contains the actual recorded differences from **November 15 at 1:00 PM** to **November 15 at 6:00 PM** (the next 6 future hours). The model trains by attempting to guess these differences based on the data from step 1.

---

### Why is this monthly `.pkl` (Pickle) file structure an excellent MLOps choice?

* **Memory Efficiency:** Allows `waid_05_2_ml_train.py` to load and process data one month at a time via `tf.data` pipelines. Loading the entire historical dataset directly into RAM on smaller machines could cause Out Of Memory (OOM) crashes.
* **Training Speed:** Extracting data from an SQLite database, calculating time windows, and running trigonometric calculations is slow. By performing this operation once with `waid_05_1` and saving tensors to disk in binary format (`.pkl`), model training (`waid_05_2`) becomes lightning-fast (up to 20 times faster than reading from the database every time).
* **Modularity:** If the Ecowitt sensors record new data for October 2026, you only need to generate the 3 files for October without touching or regenerating past months.