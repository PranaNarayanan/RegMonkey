# RegMonkey
<<<<<<< HEAD

RegMonkey is an early-stage research prototype for lightweight verification of regression outputs under disclosure constraints.

The core idea is to generate tamper-evident regression certificates that allow a journal, reviewer, or verifier to check that reported OLS coefficients are algebraically consistent with compact sufficient statistics, without rerunning a full statistical software environment.

## Current Scope

RegMonkey v0.1 supports:

- OLS models
- CSV analysis-ready datasets
- one outcome variable
- one or more numeric predictors
- intercept by default
- JSON certificates
- signature-based tamper detection

## Example

Generate a certificate:

```bash
python certify.py --data examples/toy_data.csv --outcome y --predictors x --model-id toy_model --out certificate.json
```

Verify the certificate:

```bash
python verify.py certificate.json
```

Expected output:

```text
REGMONKEY VERIFICATION
Status: PASSED
Signature valid: YES
Coefficient check: PASSED
```

## What RegMonkey Verifies

RegMonkey verifies that the reported coefficients are algebraically consistent with the sufficient statistics stored in the certificate:

```text
X'X beta = X'y
```

## What RegMonkey Does Not Verify

RegMonkey does not verify:

- whether the underlying data are truthful
- whether preprocessing was correct
- whether the analysis-ready dataset was constructed appropriately
- whether the author executed the tool honestly

This prototype is intended as a lightweight attestation layer between blind trust and full computational replication.

## License

MIT
=======
RegMonkey is a prototype framework for lightweight verification of empirical regression models under data disclosure constraints.
>>>>>>> d8a14036502eb57ff4b3c584f4717677478c4076
