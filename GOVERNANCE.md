# Governance

## Roles

- **Project owner and sponsor: Signal Private Markets Infrastructure, Inc.** Signal architected and developed PRUDENCE, owns its original material and project name, and directs releases. Ownership of outside contributions stays with the respective copyright holders unless separately agreed.
- **Maintainers.** Signal appoints maintainers to administer the repository, review contributions and prepare releases. Signal retains final release authority.
- **Contributors.** Anyone may propose changes. Contributions receive attribution in the project history and contributor record. Recognition is non-financial unless a separate agreement provides otherwise.

## Open core and continuity

Signal commits to keeping the canonical public core and accepted contributions under Apache 2.0. The rights granted in published versions continue independently of the sponsor or maintainer. Other implementers may build commercial and proprietary implementations consistent with Apache 2.0.

If Signal ceases operating or permanently withdraws maintenance, project administration may pass to a continuity maintainer under arrangements made by Signal. Any change in release authority will be publicly documented. It does not revoke published licenses, transfer contributors' copyright, or open Signal's proprietary assets.

## Proposing a change

1. **Open an issue** describing the problem and the proposed change. For changes to concepts, fields, or record rules, include an example record set that the change makes representable or invalid.
2. **Discuss.** The maintainer labels the issue: `editorial` (wording, examples, documentation), `compatible` (adds an optional field or concept), or `breaking` (removes or changes the meaning of a field, a rule, or a transition).
3. **Submit a pull request** with the change, updated schemas, examples, and tests, and a `CHANGELOG.md` entry. Every commit carries a DCO sign-off (see `CONTRIBUTING.md`).
4. **Review.** The maintainer reviews for consistency with the record rules and runs the validator and tests. `breaking` changes stay open for comment for at least 14 days.
5. **Merge.** The maintainer merges approved pull requests into the next draft version.

## Releasing a version

1. The maintainer proposes a release: version number, change list, and validation results.
2. Signal's authorized representative approves it in writing. No version is published without that approval.
3. The release is tagged and published under the canonical namespace.

## Versioning

- Versions are `MAJOR.MINOR`. While `MAJOR` is 0, any release may contain breaking changes, recorded in `CHANGELOG.md`.
- Published versions are never modified. Changes are made only by publishing a successor version. Superseded versions remain available.
- A record set declares the version it follows in its `prudence` field.

## Implementation claims

Any implementer may state accurately which version it implements. No implementer may claim endorsement or certification by Signal without a separate written agreement with Signal.
