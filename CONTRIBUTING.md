# Contributing

Participants must follow the [Code of Conduct](CODE_OF_CONDUCT.md). It defines community standards and a structured process for reporting and reviewing concerns. Send concerns privately to admin@signalprivatemarkets.com.

Contributions are accepted under the Apache License 2.0 and the [Developer Certificate of Origin](https://developercertificate.org/) (DCO).

## Sign-off

Each commit must include a sign-off line certifying that you have the right to submit the contribution under the project's license:

```
Signed-off-by: Your Name <you@example.com>
```

`git commit -s` adds it. Pull requests with unsigned commits are not merged.

## Before submitting

1. Run the tests: `python -m unittest discover -s validate`.
2. Validate any example you add or change: `python validate/prudence_validate.py <file>`.
3. Use synthetic data only. Do not include real institutional records, personal data, or third-party material you cannot license under Apache 2.0.
4. Add an entry to `CHANGELOG.md`.

The process for review and approval is in `GOVERNANCE.md`. Contributors are credited in `CHANGELOG.md` and in the project's contributor record. Recognition is non-financial.

Contributors retain copyright unless separately agreed. DCO sign-off is a certification of the right to submit, not an assignment. Accepted contributions are licensed under Apache 2.0 to everyone, including competing commercial implementers. Signal may use contributions in its commercial implementations under that license. Contributions create no automatic right to payment, equity, royalties or revenue participation; any such arrangement must be agreed separately.
