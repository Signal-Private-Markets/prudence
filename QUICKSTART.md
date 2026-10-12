# Quick start

Requires Python 3.10 or later.

## 1. Install

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Validate the examples

```sh
python validate/prudence_validate.py examples/human-approved/procurement-award.json examples/automated/payment-release.json
```

Expected output, exit status 0:

```
VALID    examples/human-approved/procurement-award.json  (40 records)
VALID    examples/automated/payment-release.json  (38 records)
```

## 3. See a failure

```sh
python validate/prudence_validate.py examples/invalid/wrong-authorization-version.json
```

Expected output, exit status 1:

```
INVALID  examples/invalid/wrong-authorization-version.json  (1 error)
  [AUTH_VERSION] ACT-PAY-8841: cites version 1 of AUTH-AP-RELEASE-v2, but AUTH-AP-RELEASE-v2 is version 2
```

The action states it relied on version 1 of the payment authorization while pointing at the version-2 record. Every action must name the authorization version it actually relied on.

## 4. Run the tests

```sh
python -m unittest discover -s validate
```

Expected: `Ran 39 tests` and `OK`. Every error code in `LIMITATIONS.md` has at least one case that must trigger it, and one test fails if a documented code ever loses its case. One test feeds wrong-typed values into every field of every record type and requires the validator to report errors rather than fail. The valid cases include an action taken without a decision or authorization: it is valid when a linked Exception records what was missing, and invalid otherwise.

## 5. Write your own record set

1. Copy `examples/human-approved/procurement-award.json`.
2. Replace the records with your own. Every record needs at least a `created` Record Event.
3. Run the validator on your file. Each error names its code, the record, and the problem. Error codes are listed in `LIMITATIONS.md`. Exit status 3 means the validator itself failed; please report the input file.

Read `concepts.md` for the meaning of each concept and the record rules.
