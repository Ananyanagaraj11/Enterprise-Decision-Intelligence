"""
Network intrusion detection dataset loader.
Supports UNSW-NB15 and CICIDS2017 (single or multiple CSV) formats.
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight


# Common non-informative / identifier columns across datasets
ID_COLUMNS = {"id", "srcip", "dstip", "sport", "dsport", "stime", "ltime"}

# CICIDS2017 typical label column
CICIDS_LABEL_COLUMN = "Label"


def _infer_label_column(df: pd.DataFrame) -> str:
    """Infer label column name from known dataset schemas."""
    candidates = ["label", "Label", "attack_cat", "attack", "Attack"]
    for c in candidates:
        if c in df.columns:
            return c
    # Last column is often the label in IDS datasets
    return df.columns[-1]


def _infer_dataset_type(df: pd.DataFrame, label_col: str) -> str:
    """Infer whether data is UNSW-NB15 or CICIDS2017 style."""
    sample = df[label_col].dropna().astype(str).iloc[0].lower()
    if "normal" in sample or sample in ("0", "1") or df[label_col].nunique() <= 15:
        return "cicids"
    return "unsw"


def load_csv(
    path: str,
    label_column: Optional[str] = None,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load network intrusion CSV. Handles UNSW-NB15 and CICIDS2017.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    kwargs = {"low_memory": False}
    if max_rows is not None:
        kwargs["nrows"] = max_rows

    df = pd.read_csv(path, **kwargs)

    label_col = label_column or _infer_label_column(df)
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not in {list(df.columns)}")

    return df, label_col


def load_cicids2017(
    dir_path: str,
    label_column: Optional[str] = None,
    max_rows_per_file: Optional[int] = None,
    max_rows_total: Optional[int] = None,
    pattern: str = "*.csv",
) -> Tuple[pd.DataFrame, str]:
    """
    Load CICIDS2017 from a directory of CSV files (e.g. Monday-WorkingHours.csv, etc.).
    Concatenates all matching CSVs and returns (df, label_col).
    Label column defaults to 'Label' for CICIDS2017.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"CICIDS2017 directory not found: {dir_path}")

    label_col = label_column or CICIDS_LABEL_COLUMN
    frames = []
    total_rows = 0

    for path in sorted(dir_path.glob(pattern)):
        if not path.is_file():
            continue
        kwargs = {"low_memory": False}
        if max_rows_per_file is not None:
            kwargs["nrows"] = max_rows_per_file
        try:
            df = pd.read_csv(path, **kwargs)
        except Exception as e:
            continue
        if label_col not in df.columns:
            label_col = _infer_label_column(df)
        frames.append(df)
        total_rows += len(df)
        if max_rows_total is not None and total_rows >= max_rows_total:
            break

    if not frames:
        raise FileNotFoundError(f"No CSV files found in {dir_path} with pattern {pattern}")

    df = pd.concat(frames, axis=0, ignore_index=True)
    if max_rows_total is not None and len(df) > max_rows_total:
        df = df.iloc[:max_rows_total]
    return df, label_col


def drop_non_informative(df: pd.DataFrame) -> pd.DataFrame:
    """Remove identifier and non-informative columns."""
    drop = [c for c in df.columns if c.lower() in {x.lower() for x in ID_COLUMNS}]
    return df.drop(columns=[c for c in drop if c in df.columns], errors="ignore")


def encode_labels(y: pd.Series) -> Tuple[np.ndarray, LabelEncoder]:
    """Encode string/categorical labels to integers."""
    le = LabelEncoder()
    y_clean = y.astype(str).str.strip().replace("", np.nan)
    y_clean = y_clean.dropna()
    le.fit(y_clean)
    y_encoded = le.transform(y.astype(str).str.strip())
    return np.asarray(y_encoded, dtype=np.int64), le


def get_class_weights(y: np.ndarray) -> np.ndarray:
    """Compute class weights for imbalanced classification."""
    classes = np.unique(y)
    weights = compute_class_weight(
        "balanced", classes=classes, y=y
    )
    return np.asarray(weights, dtype=np.float32)


def prepare_for_training(
    csv_path: str,
    label_column: Optional[str] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    max_rows: Optional[int] = None,
    drop_ids: bool = True,
    use_cicids2017_dir: bool = False,
    max_rows_total: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler, LabelEncoder, list]:
    """
    Load CSV (or CICIDS2017 directory), preprocess, and split into train/validation.
    Returns X_train, X_val, y_train, y_val, scaler, label_encoder, feature_names.

    If use_cicids2017_dir is True, csv_path must be a directory containing CICIDS2017 CSV files.
    Use max_rows_total to cap total rows when loading multiple files.
    """
    path = Path(csv_path)
    if use_cicids2017_dir:
        df, label_col = load_cicids2017(
            csv_path,
            label_column=label_column,
            max_rows_per_file=max_rows,
            max_rows_total=max_rows_total or max_rows,
        )
    else:
        df, label_col = load_csv(csv_path, label_column=label_column, max_rows=max_rows)

    if drop_ids:
        df = drop_non_informative(df)

    # Separate features and label
    y_series = df[label_col]
    X_df = df.drop(columns=[label_col])

    # Numeric only
    X_df = X_df.select_dtypes(include=[np.number])
    if X_df.empty:
        raise ValueError("No numeric features found after dropping non-informative columns.")

    # Drop rows with missing label or all-NaN features
    valid = y_series.notna() & (~X_df.isna().all(axis=1))
    X_df = X_df.loc[valid].copy()
    y_series = y_series.loc[valid]

    # Encode labels
    y, label_encoder = encode_labels(y_series)

    # 1) Replace +/- inf with NaN (CICIDS2017 can have inf in raw features)
    X_df = X_df.replace([np.inf, -np.inf], np.nan)

    # 2) Drop columns that are entirely NaN
    all_nan_cols = X_df.columns[X_df.isna().all(axis=0)]
    X_df = X_df.drop(columns=all_nan_cols)
    if X_df.empty:
        raise ValueError("All feature columns became NaN after cleaning.")

    feature_names = list(X_df.columns)
    X = X_df.values.astype(np.float64)

    # Train/validation split (stratify when possible)
    try:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
    except ValueError:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

    # 3) Impute remaining NaNs using column means from training data only
    col_means = np.nanmean(X_train, axis=0)
    col_means = np.where(np.isnan(col_means), 0.0, col_means)

    for arr in (X_train, X_val):
        nan_mask = np.isnan(arr)
        if nan_mask.any():
            arr[nan_mask] = np.take(col_means, np.where(nan_mask)[1])

    # 4) Clip any remaining extreme values that could overflow float64
    X_train = np.clip(X_train, -1e30, 1e30)
    X_val = np.clip(X_val, -1e30, 1e30)

    # Normalize
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    return X_train, X_val, y_train, y_val, scaler, label_encoder, feature_names
