import argparse
import csv
import hashlib
import hmac
import json
from pathlib import Path

import numpy as np


DEFAULT_SECRET = b"regmonkey-demo-secret-not-for-production"


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sign_payload(payload, secret=DEFAULT_SECRET):
    return hmac.new(secret, canonical_json(payload), hashlib.sha256).hexdigest()


def read_csv_numeric(path, outcome, predictors):
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError("CSV has no data rows.")

    y = np.array([float(row[outcome]) for row in rows], dtype=float)

    X_cols = [np.ones(len(rows))]
    column_names = ["Intercept"]

    for pred in predictors:
        X_cols.append(np.array([float(row[pred]) for row in rows], dtype=float))
        column_names.append(pred)

    X = np.column_stack(X_cols)
    return X, y, column_names


def make_certificate(data_path, outcome, predictors, model_id):
    X, y, column_names = read_csv_numeric(data_path, outcome, predictors)

    xtx = X.T @ X
    xty = X.T @ y

    beta = np.linalg.solve(xtx, xty)
    residuals = y - X @ beta
    rss = float(residuals.T @ residuals)

    payload = {
        "certificate_type": "regmonkey_ols_v0_1",
        "model_id": model_id,
        "dataset_hash_sha256": sha256_file(data_path),
        "model_specification": {
            "model_type": "OLS",
            "outcome": outcome,
            "predictors": predictors,
            "intercept": True
        },
        "n_observations": int(X.shape[0]),
        "n_parameters": int(X.shape[1]),
        "coefficient_names": column_names,
        "reported_coefficients": {
            name: float(value) for name, value in zip(column_names, beta)
        },
        "sufficient_statistics": {
            "xtx": xtx.tolist(),
            "xty": xty.tolist(),
            "rss": rss
        },
        "verification_claim": {
            "coefficient_condition": "XTX_beta_equals_XTy",
            "tolerance": 1e-8
        },
        "generated_by": "regmonkey v0.1"
    }

    certificate = {
        "payload": payload,
        "signature": {
            "scheme": "HMAC-SHA256-demo",
            "value": sign_payload(payload)
        }
    }

    return certificate


def main():
    parser = argparse.ArgumentParser(description="Generate a RegMonkey OLS verification certificate.")
    parser.add_argument("--data", required=True, help="Path to analysis-ready CSV dataset.")
    parser.add_argument("--outcome", required=True, help="Outcome variable name.")
    parser.add_argument("--predictors", nargs="+", required=True, help="Predictor variable names.")
    parser.add_argument("--model-id", default="model_1", help="Model identifier.")
    parser.add_argument("--out", default="certificate.json", help="Output certificate path.")

    args = parser.parse_args()

    cert = make_certificate(
        data_path=Path(args.data),
        outcome=args.outcome,
        predictors=args.predictors,
        model_id=args.model_id
    )

    with open(args.out, "w") as f:
        json.dump(cert, f, indent=2)

    print(f"RegMonkey certificate written to {args.out}")


if __name__ == "__main__":
    main()
