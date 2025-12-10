import math

def determine_bucket(n_samples):
    """
    Assigns a node to a compute resource pool (Small/Mid/Large) based on sample size.
    """
    # Define thresholds
    SMALL_MAX = 80
    MID_MAX = 500
    
    # --- Robustness handling ---
    if n_samples is None:
        return "small"
    
    try:
        n = int(n_samples)
    except (ValueError, TypeError):
        return "small"

    if n < 0:
        return "small"
        
    # --- Core bucketing logic ---
    if n < SMALL_MAX:
        return "small"
    elif n < MID_MAX:
        return "mid"
    else:
        return "large"

def make_task_key(prefix, idx):
    """
    Generates a unique key for a Databricks Job Task.
    """
    return f"{prefix}_{idx:03d}"