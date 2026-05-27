import argparse
import hashlib
import hmac
import json
from pathlib import Path

import numpy as np


DEFAULT_SECRET = b"regmonkey-demo-secret-not-for-production"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_payload(payload, secret=DEFAULT_SECRET):
    return hmac.new(secret, canonical_json(payload), hashlib.sha256).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mark(passed):
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"


def verify_certificate(path, expected_data_hash=None, data_path=None):
    with open(path) as f:
        cert = json.load(f)

    payload = cert["payload"]
    signature = cert["signature"]["value"]

    expected_signature = sign_payload(payload)
    signature_valid = hmac.compare_digest(signature, expected_signature)

    xtx = np.array(payload["sufficient_statistics"]["xtx"], dtype=float)
    xty = np.array(payload["sufficient_statistics"]["xty"], dtype=float)

    names = payload["coefficient_names"]
    beta_reported = np.array(
        [payload["reported_coefficients"][name] for name in names],
        dtype=float
    )

    lhs = xtx @ beta_reported
    rhs = xty

    tolerance = payload["verification_claim"]["tolerance"]
    max_abs_diff = float(np.max(np.abs(lhs - rhs)))
    coefficient_check = max_abs_diff <= tolerance

    certificate_data_hash = payload.get("dataset_hash_sha256")
    dataset_commitment = certificate_data_hash is not None

    data_hash_check_requested = expected_data_hash is not None or data_path is not None
    recomputed_data_hash = None
    data_hash_match = None

    if data_path is not None:
        recomputed_data_hash = sha256_file(data_path)
        expected_data_hash = recomputed_data_hash

    if expected_data_hash is not None:
        data_hash_match = (
            certificate_data_hash is not None
            and hmac.compare_digest(certificate_data_hash, expected_data_hash)
        )

    passed = signature_valid and coefficient_check and dataset_commitment

    if data_hash_check_requested:
        passed = passed and bool(data_hash_match)

    return {
        "passed": passed,
        "signature_valid": signature_valid,
        "coefficient_check": coefficient_check,
        "dataset_commitment": dataset_commitment,
        "data_hash_check_requested": data_hash_check_requested,
        "data_hash_match": data_hash_match,
        "certificate_data_hash": certificate_data_hash,
        "recomputed_data_hash": recomputed_data_hash,
        "max_abs_diff": max_abs_diff,
        "tolerance": tolerance,
        "model_id": payload["model_id"],
        "n_observations": payload["n_observations"],
        "n_parameters": payload["n_parameters"]
    }


def main():
    parser = argparse.ArgumentParser(description="Verify a RegMonkey certificate.")
    parser.add_argument("certificate", help="Path to certificate JSON.")

    parser.add_argument(
        "--expected-data-hash",
        default=None,
        help="Optional expected SHA256 dataset hash recorded at submission."
    )

    parser.add_argument(
        "--data",
        default=None,
        help="Optional dataset path for auditor mode. Recomputes SHA256 and compares to certificate."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print technical verification details."
    )

    args = parser.parse_args()

    result = verify_certificate(
        args.certificate,
        expected_data_hash=args.expected_data_hash,
        data_path=Path(args.data) if args.data else None
    )

    print("REGMONKEY VERIFICATION")
    print("----------------------")

    if result["passed"]:
        print(f"{GREEN}STATUS: PASSED{RESET}")
    else:
        print(f"{RED}STATUS: FAILED{RESET}")

    print()
    print(f"{mark(result['signature_valid'])} Signature valid")
    print(f"{mark(result['coefficient_check'])} Coefficient consistency")

    if result["data_hash_check_requested"]:
        print(f"{mark(result['data_hash_match'])} Dataset consistency")
    else:
        print(f"{mark(result['dataset_commitment'])} Dataset commitment")
    
    print()

    
    if args.verbose:
        print()
        print("DETAILS")
        print("-------")
        print(f"Model ID: {result['model_id']}")
        print(f"Max absolute difference: {result['max_abs_diff']}")
        print(f"Tolerance: {result['tolerance']}")
        print(f"Certificate dataset hash: {result['certificate_data_hash']}")
        print(f"Observations (N): {result['n_observations']}")
        print(f"Parameters (K): {result['n_parameters']}")
        if result["recomputed_data_hash"] is not None:
            print(f"Recomputed dataset hash: {result['recomputed_data_hash']}")


if __name__ == "__main__":
    main()