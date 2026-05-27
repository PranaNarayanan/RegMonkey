# RegMonkey

RegMonkey is an early-stage research prototype for lightweight verification of empirical regression models under disclosure constraints.

Instead of requiring reviewers to rerun full statistical pipelines or access confidential raw datasets, RegMonkey verifies whether reported regression coefficients are algebraically consistent with compact sufficient statistics derived from the original analysis dataset.

The current prototype supports:
- Ordinary Least Squares (OLS)
- interaction terms
- one-way fixed effects
- lightweight verification certificates
- optional dataset consistency checks

---

# Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/regmonkey.git
cd regmonkey
```

Install dependencies:

```bash
pip install numpy
```

---

# Basic Usage

Generate a certificate:

```bash
python certify.py \
  --data examples/toy_data.csv \
  --model "y ~ x" \
  --model-id toy_model \
  --out certificate.json
```

Verify certificate:

```bash
python verify.py certificate.json
```

Expected output:

```text
REGMONKEY VERIFICATION
----------------------
STATUS: PASSED

✓ Signature valid
✓ Coefficient consistency
✓ Dataset commitment
```

---

# Formula Syntax

RegMonkey currently supports:
- additive models
- two-way interaction terms
- optional one-way fixed effects

Examples:

```bash
--model "y ~ x"
```

```bash
--model "y ~ x1 + x2"
```

```bash
--model "y ~ x1 + x2 + x1*x2"
```

---

# Interaction Example

Dataset:

`examples/interaction_data.csv`

```csv
x1,x2,y
1,0,2
2,0,4
3,0,6
1,1,5
2,1,8
3,1,11
```

Generate certificate:

```bash
python certify.py \
  --data examples/interaction_data.csv \
  --model "y ~ x1 + x2 + x1*x2" \
  --model-id interaction_demo \
  --out interaction_certificate.json
```

Verify:

```bash
python verify.py interaction_certificate.json
```

---

# Fixed Effects Example

Dataset:

`examples/fe_data.csv`

```csv
subject,x,y
A,1,12
A,2,14
A,3,16
B,1,22
B,2,24
B,3,26
C,1,32
C,2,34
C,3,36
```

Generate certificate:

```bash
python certify.py \
  --data examples/fe_data.csv \
  --model "y ~ x" \
  --fe subject \
  --model-id fe_demo \
  --out fe_certificate.json
```

Verify:

```bash
python verify.py fe_certificate.json
```

---

# Auditor Mode

RegMonkey supports optional dataset consistency verification.

Verify against expected dataset hash:

```bash
python verify.py certificate.json \
  --expected-data-hash abc123...
```

Or recompute hash directly from dataset:

```bash
python verify.py certificate.json \
  --data confidential_dataset.csv
```

This mode is intended for:
- journal auditors
- confidential-data stewards
- replication teams
- trusted third-party verification

Typical reviewers do not require access to raw data.

---

# What RegMonkey Verifies

RegMonkey verifies:
- certificate integrity
- algebraic consistency of reported coefficients
- optional dataset consistency

For OLS-family estimators, coefficients satisfy:

```text
X'X beta = X'y
```

The verifier checks whether the reported coefficients satisfy these estimating equations using compact sufficient statistics stored in the certificate.

---

# What RegMonkey Does Not Verify

RegMonkey does not verify:
- whether the underlying data are truthful
- whether preprocessing was correct
- whether the analysis-ready dataset was constructed appropriately
- whether the author executed the tool honestly

This prototype is intended as a lightweight attestation layer between blind trust and full computational replication.

---

# Current Scope

Current prototype supports:
- OLS
- interaction terms
- one-way fixed effects

Current prototype does NOT yet support:
- clustered standard errors
- instrumental variables
- generalized method of moments
- nonlinear estimators
- two-way fixed effects
- zero-knowledge proofs

---

# Motivation

Computational reproducibility is increasingly difficult to scale across peer review due to:
- inconsistent verification practices
- reviewer workload
- confidential datasets
- growing volumes of AI-generated empirical analyses

RegMonkey explores a lightweight intermediate layer between:
- unverifiable empirical reporting
- full computational replication

---

# License

MIT