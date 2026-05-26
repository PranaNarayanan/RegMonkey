import argparse
import hashlib
import hmac
import json

import numpy as np


DEFAULT_SECRET = b"regmonkey-demo-secret-not-for-production"


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_payload(payload, secret=DEFAULT_SECRET):
    return hmac.new(secret, canonical_json(payload), hashlib.sha256).hexdigest()


def verify_certificate(path):
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

    passed = signature_valid and coefficient_check

    return {
        "passed": passed,
        "signature_valid": signature_valid,
        "coefficient_check": coefficient_check,
        "max_abs_diff": max_abs_diff,
        "tolerance": tolerance,
        "model_id": payload["model_id"]
    }


def main():
    parser = argparse.ArgumentParser(description="Verify a RegMonkey certificate.")
    parser.add_argument("certificate", help="Path to certificate JSON.")
    args = parser.parse_args()

    result = verify_certificate(args.certificate)

    print("REGMONKEY VERIFICATION")
    print("----------------------")
    print(f"Model ID: {result['model_id']}")
    print(f"Status: {'PASSED' if result['passed'] else 'FAILED'}")
    print(f"Signature valid: {'YES' if result['signature_valid'] else 'NO'}")
    print(f"Coefficient check: {'PASSED' if result['coefficient_check'] else 'FAILED'}")
    print(f"Max absolute difference: {result['max_abs_diff']}")
    print(f"Tolerance: {result['tolerance']}")


if __name__ == "__main__":
    main()
