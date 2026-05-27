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


def parse_model(model):
    if "~" not in model:
        raise ValueError('Model must look like: "y ~ x1 + x2"')

    lhs, rhs = model.split("~", 1)
    outcome = lhs.strip()
    raw_terms = [x.strip() for x in rhs.split("+") if x.strip()]

    if not outcome:
        raise ValueError("Missing outcome before ~")
    if not raw_terms:
        raise ValueError("Missing predictors after ~")

    terms = []
    for term in raw_terms:
        if "*" in term:
            parts = [p.strip() for p in term.split("*") if p.strip()]
            if len(parts) != 2:
                raise ValueError("Only two-way interactions like x1*x2 are supported.")
            for p in parts:
                if p not in terms:
                    terms.append(p)
            interaction = f"{parts[0]}*{parts[1]}"
            if interaction not in terms:
                terms.append(interaction)
        else:
            if term not in terms:
                terms.append(term)

    return outcome, terms


def read_csv_rows(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("CSV has no data rows.")

    return rows


def get_numeric_column(rows, name):
    return np.array([float(row[name]) for row in rows], dtype=float)


def build_term(rows, term):
    if "*" in term:
        left, right = [x.strip() for x in term.split("*")]
        return get_numeric_column(rows, left) * get_numeric_column(rows, right)
    return get_numeric_column(rows, term)


def within_demean(X, y, groups):
    X_dm = X.copy()
    y_dm = y.copy()

    for g in sorted(set(groups)):
        idx = np.array([group == g for group in groups])
        y_dm[idx] = y[idx] - y[idx].mean()
        X_dm[idx, :] = X[idx, :] - X[idx, :].mean(axis=0)

    return X_dm, y_dm


def build_arrays(rows, outcome, terms, fe=None):
    y = get_numeric_column(rows, outcome)

    X_cols = []
    column_names = []

    if fe is None:
        X_cols.append(np.ones(len(rows)))
        column_names.append("Intercept")

    for term in terms:
        X_cols.append(build_term(rows, term))
        column_names.append(term)

    X = np.column_stack(X_cols)

    if fe is not None:
        groups = [row[fe] for row in rows]
        X, y = within_demean(X, y, groups)

    return X, y, column_names


def make_certificate(data_path, model, model_id, fe=None):
    outcome, terms = parse_model(model)
    rows = read_csv_rows(data_path)
    X, y, column_names = build_arrays(rows, outcome, terms, fe=fe)

    xtx = X.T @ X
    xty = X.T @ y

    beta = np.linalg.lstsq(xtx, xty, rcond=None)[0]
    residuals = y - X @ beta
    rss = float(residuals.T @ residuals)

    payload = {
        "certificate_type": "regmonkey_ols_v0_2",
        "model_id": model_id,
        "dataset_hash_sha256": sha256_file(data_path),
        "model_specification": {
            "model_type": "OLS",
            "formula": model,
            "outcome": outcome,
            "terms": terms,
            "intercept": fe is None,
            "fixed_effect": fe,
            "transformation": "within_demeaning" if fe else "none"
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
        "generated_by": "regmonkey v0.2"
    }

    return {
        "payload": payload,
        "signature": {
            "scheme": "HMAC-SHA256-demo",
            "value": sign_payload(payload)
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a RegMonkey OLS verification certificate."
    )
    parser.add_argument("--data", required=True, help="Path to analysis-ready CSV dataset.")
    parser.add_argument("--model", required=True, help='Formula, e.g. "y ~ x1 + x2 + x1*x2"')
    parser.add_argument("--fe", default=None, help="Optional one-way fixed effect column, e.g. subject")
    parser.add_argument("--model-id", default="model_1", help="Model identifier.")
    parser.add_argument("--out", default="certificate.json", help="Output certificate path.")

    args = parser.parse_args()

    cert = make_certificate(
        data_path=Path(args.data),
        model=args.model,
        model_id=args.model_id,
        fe=args.fe
    )

    with open(args.out, "w") as f:
        json.dump(cert, f, indent=2)

    print(f"RegMonkey certificate written to {args.out}")


if __name__ == "__main__":
    main()