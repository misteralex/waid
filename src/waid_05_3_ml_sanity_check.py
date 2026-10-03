#!/usr/bin/env python3

"""
@file waid_05_3_ml_sanity_check.py
@brief Automated ML Validation Gate and Coherence Guardrail for WAID.
@details Inspects generated raw tensors on disk, trained scikit-learn scalers, 
         and the active Keras model to guarantee physical and structural alignment 
         (dimensions, features, and columns order) before deploying to inference.
@author AF
@date 2026
"""

import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TF verbosity

import sys
from pathlib import Path
import joblib
import numpy as np
from loguru import logger

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

# Detect libraries
HAS_KERAS = False
try:
    from tensorflow.keras.models import load_model
    HAS_KERAS = True
except ImportError:
    pass

HAS_H5PY = False
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    pass

# Map of accepted equivalent names between Training schema and Inference schema
SEMANTIC_EQUIVALENCES = {
    'temperature': 'ecowitt_temp',
    'humidity': 'ecowitt_rh',
    'pressure_hpa': 'ecowitt_pres',
    'wind_speed': 'ecowitt_wind',
    'solar_radiation': 'ecowitt_solar',
    'hourly_rain': 'ecowitt_rain',
    'hour_sin': 'hour_sin',
    'hour_cos': 'hour_cos',
    'doy_sin': 'doy_sin',
    'doy_cos': 'doy_cos',
    'theo_solar': 'theo_solar'
}


def validate_pipeline_alignment(env: WaidBoot) -> int:
    """Validates dimensional and structural alignment across the ML pipeline.

    @param env Initialized framework environment context (WaidBoot).
    @return Integer status code matching WaidExit enum (WaidExit.SUCCESS or WaidExit.DATA_FAIL).
    """
    logger.info("Initializing Automated ML Validation Gate [Step 05_3]...")
    
    tensors_dir = env.ml_tensors_dir
    models_dir = env.ml_models_dir
    
    # Use a local flag to manage keras status and avoid UnboundLocalError
    keras_available = HAS_KERAS
    
    # --------------------------------------------------------------------------
    # 1. TENSOR INSPECTION
    # --------------------------------------------------------------------------
    x_files = sorted(list(Path(tensors_dir).glob("X_raw_*.pkl")))
    if not x_files:
        logger.error(f"Validation failed: No X_raw_*.pkl tensor files found in {tensors_dir}")
        return WaidExit.DATA_FAIL
        
    # Inspect EVERY monthly period: X shape, and X/Y/timestamps consistency
    tensor_features_by_period = {}
    tensor_issues = 0

    logger.info(f"Inspecting {len(x_files)} monthly tensor periods...")
    for x_path in x_files:
        period = x_path.stem.replace("X_raw_", "")

        try:
            X = joblib.load(x_path)
        except Exception as e:
            logger.error(f"Failed to load tensor {x_path.name}: {e}")
            return WaidExit.DATA_FAIL

        if getattr(X, "ndim", 0) != 3:
            logger.error(
                f"[{period}] X tensor must be 3D (samples, timesteps, features), "
                f"got shape {getattr(X, 'shape', None)}"
            )
            tensor_issues += 1
            continue

        n_samples, n_timesteps, n_feat = X.shape
        tensor_features_by_period[period] = n_feat
        del X  # Free memory before loading the next period

        # Companion files must exist and have the same number of samples as X
        for prefix in ("Y_raw", "timestamps"):
            companion = x_path.with_name(f"{prefix}_{period}.pkl")
            if not companion.exists():
                logger.error(f"[{period}] Missing companion file: {companion.name}")
                tensor_issues += 1
                continue
            try:
                companion_len = len(joblib.load(companion))
            except Exception as e:
                logger.error(f"[{period}] Failed to load {companion.name}: {e}")
                return WaidExit.DATA_FAIL
            if companion_len != n_samples:
                logger.error(
                    f"[{period}] Sample count mismatch: X has {n_samples}, "
                    f"{companion.name} has {companion_len}"
                )
                tensor_issues += 1

        logger.info(f"[{period}] X shape=({n_samples}, {n_timesteps}, {n_feat})")

    # All periods must agree on the number of features
    distinct_features = sorted(set(tensor_features_by_period.values()))
    if len(distinct_features) > 1:
        logger.error("Feature count differs across periods")
        tensor_issues += 1

    # --------------------------------------------------------------------------
    # 2. FEATURE ORDER & SCHEME ALIGNMENT
    # --------------------------------------------------------------------------
    logger.info("Analyzing feature ordering compatibility (Training vs Inference Scheme)...")
    
    # 2a. Reconstruct implicit Training feature order
    standard_features = [feature["standard"] for feature in env.output_features]
    cyclical_features = ['hour_sin', 'hour_cos', 'doy_sin', 'doy_cos']
    training_order = standard_features + cyclical_features + ['theo_solar']
    
    # 2b. Retrieve configured Inference order
    inference_order = getattr(env, 'input_features_match', [])
    
    order_mismatches = 0
    max_len = max(len(training_order), len(inference_order))
    
    logger.info("-" * 80)
    logger.info(f"{'Index':<6} | {'Implicit Training Column':<25} | {'Inference Match Column':<25} | {'Status'}")
    logger.info("-" * 80)
    
    for i in range(max_len):
        tr_col = training_order[i] if i < len(training_order) else "[MISSING]"
        inf_col = inference_order[i] if i < len(inference_order) else "[MISSING]"
        
        # Check direct match or semantic equivalence
        is_match = (tr_col == inf_col) or (SEMANTIC_EQUIVALENCES.get(tr_col) == inf_col)
        
        if is_match:
            status = "🟢 MATCH"
        else:
            status = "🔴 MISMATCH"
            order_mismatches += 1
            
        logger.info(f"{i:<6} | {tr_col:<25} | {inf_col:<25} | {status}")
    logger.info("-" * 80)

    # --------------------------------------------------------------------------
    # 3. SCALER & DEEP LEARNING MODEL METADATA INSPECTION
    # --------------------------------------------------------------------------
    x_scaler_path = models_dir / env.ml_input_scaler_pkl_file
    scaler_x_features = None
    
    if x_scaler_path.exists():
        try:
            scaler_x = joblib.load(x_scaler_path)
            if hasattr(scaler_x, "n_features_in_"):
                scaler_x_features = scaler_x.n_features_in_
            elif hasattr(scaler_x, "mean_"):
                scaler_x_features = len(scaler_x.mean_)
            logger.info(f"Input Scaler loaded. Expects input features = {scaler_x_features}")
        except Exception as e:
            logger.error(f"Failed to read input scaler metadata: {e}")
            return WaidExit.DATA_FAIL
    else:
        logger.error(f"Input Scaler file missing at: {x_scaler_path}")
        return WaidExit.DATA_FAIL

    model_path = models_dir / env.ml_model_h5_file
    model_input_features = None
    
    if model_path.exists():
        if keras_available:
            try:
                model = load_model(model_path, compile=False)
                input_shape = model.input_shape
                if input_shape and len(input_shape) >= 3:
                    model_input_features = input_shape[-1]
                logger.info(f"Keras Model loaded. Expects input features = {model_input_features}")
            except Exception as e:
                logger.warning(f"Keras loading failed: {e}. Falling back to metadata-only check.")
                keras_available = False
                
        if not keras_available and HAS_H5PY:
            try:
                with h5py.File(model_path, 'r') as f:
                    if 'model_config' in f.attrs:
                        import json
                        config = json.loads(f.attrs['model_config'])
                        layers = config.get('config', {}).get('layers', [])
                        if layers:
                            first_layer = layers[0]
                            batch_input_shape = first_layer.get('config', {}).get('batch_input_shape', None)
                            if batch_input_shape:
                                model_input_features = batch_input_shape[-1]
                                logger.info(
                                    f"Model metadata extracted via H5Py. Expects input features = {model_input_features}"
                                )
            except Exception as e:
                logger.error(f"H5Py metadata extraction failed: {e}")
    else:
        logger.error(f"Keras Model file missing at: {model_path}")
        return WaidExit.DATA_FAIL

    # --------------------------------------------------------------------------
    # 4. FINAL CONGRUENCE DECISION (GUARDRAIL GATE)
    # --------------------------------------------------------------------------
    validation_passed = True
    
    logger.info("Evaluating validation gate rules...")
    
    # Rule 0: Tensor integrity across all periods (shape, companions, consistency)
    if tensor_issues > 0:
        logger.error(f"Rule Violation [Tensor Integrity]: {tensor_issues} issue(s) found across monthly tensors!")
        validation_passed = False

    # Rule 1: Every tensor period vs Scaler
    if scaler_x_features is not None:
        bad_periods = {
            period: n_feat
            for period, n_feat in tensor_features_by_period.items()
            if n_feat != scaler_x_features
        }
        if bad_periods:
            logger.error(
                f"Rule Violation [Tensor vs Scaler]: "
                f"Scaler demands {scaler_x_features} features, but {len(bad_periods)} "
                f"of {len(tensor_features_by_period)} periods differ: {bad_periods}!"
            )
            validation_passed = False
            
    # Rule 2: Scaler vs Keras Model
    if scaler_x_features is not None and model_input_features is not None:
        if scaler_x_features != model_input_features:
            logger.error(
                f"Rule Violation [Scaler vs Model]: "
                f"Scaler is fit on {scaler_x_features} features, "
                f"but Keras Model requires {model_input_features}!"
            )
            validation_passed = False
            
    # Rule 3: Column Ordering & Schema Match
    if order_mismatches > 0:
        logger.error(
            f"Rule Violation [Schema Order]: "
            f"Detected {order_mismatches} column ordering mismatches "
            f"between Training composition and Inference mapping!"
        )
        validation_passed = False

    if validation_passed:
        logger.success(
            "VALIDATION SUCCESSFUL: All components (Tensor, Scaler, Model) are aligned and synchronized."
        )
        return WaidExit.SUCCESS
    else:
        logger.critical(
            "VALIDATION CRITICAL FAILURE: Structural mismatch detected. Aborting pipeline deployment."
        )
        return WaidExit.DATA_FAIL


def main() -> int:
    """Main entry point for pipeline validation gate execution.

    @return Exit status code matching WaidExit enum.
    """
    try:
        env = WaidBoot()
        return validate_pipeline_alignment(env)
    except WError as e:
        logger.error(f"Validation framework error: {e}")
        return e.code
    except Exception:
        logger.exception("Unexpected error during pipeline validation gate run")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())