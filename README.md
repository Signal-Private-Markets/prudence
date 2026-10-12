# PRUDENCE™ v0.1

**Public draft for implementation and feedback.**

PRUDENCE™: architecture and development by Signal Private Markets Infrastructure, Inc. Signal owns its original PRUDENCE material and directs the project. Outside contributions remain owned by their respective copyright holders unless separately agreed.

PRUDENCE is a shared foundation for recording consequential decisions and the actions taken under them, so that their purpose, authority, evidence, reasoning, actions, and outcomes remain intelligible as people, systems, and institutions change.

It applies the same structure whether an action is carried out by a person, by a person assisted by a system, or by a system acting alone: **actor, decision, authorization, action**, with each attempt and its observed result recorded separately.

## What v0.1 contains

| Path | Contents |
| --- | --- |
| `concepts.md` | The ten concepts and the record rules |
| `schema/` | JSON Schema (draft 2020-12) for each concept and for a record set |
| `validate/` | A runnable structural validator and its tests |
| `examples/human-approved/` | A procurement committee awards a contract; an officer executes it |
| `examples/automated/` | A system releases a payment under standing authority; the first attempt fails and is retried |
| `examples/invalid/` | One deliberately invalid record set and the error it produces |
| `examples/extension/` | The human-approved example with a domain extension attached |
| `extending.md` | How domain requirements attach without changing the core |
| `LIMITATIONS.md` | What the validator checks, what it does not, and open questions |
| `GOVERNANCE.md` | How changes are proposed, reviewed, and approved |
| `tools/` | Scripts that regenerate the schemas and examples |
| `namespace.json` | The canonical namespace, the single place it is set |

Start with `QUICKSTART.md`.

## Community participation

Participation in official PRUDENCE project spaces is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). It includes a structured reporting and review process. Send concerns privately to admin@signalprivatemarkets.com. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution requirements and [GOVERNANCE.md](GOVERNANCE.md) for technical review and release authority.

## The release test

An outside developer can represent a consequential decision, connect it to an authorized action, and validate the resulting record without anyone's permission or infrastructure.

## What validation means

The validator checks structure: required fields, valid references, permitted status transitions, the record rules, and the consistency of the supplied Record Event sequence. A valid record set is well-formed and internally consistent. Validity does not establish that evidence is authentic, that an authorization was validly granted, or that a decision was sound.

The specification describes records. Implementers provide enforcement. Recording an authorization does not itself authorize an action.

## Implementation and endorsement

Anyone may implement PRUDENCE, including commercially, under the Apache License 2.0, and may state accurately which version they implement. Implementation does not imply endorsement or certification by Signal or by any other party.

## Ownership and attribution

PRUDENCE™: architecture and development by Signal Private Markets Infrastructure, Inc. Signal owns its original PRUDENCE material and directs the project. Outside contributions remain owned by their respective copyright holders unless separately agreed. See `NOTICE`.

## Commitments to participants

Signal commits to keeping the canonical public PRUDENCE core and accepted contributions under Apache 2.0. Published Apache rights continue independently of Signal. This project commitment does not require other implementers to publish proprietary extensions or derivatives.

Contributors retain ownership of their contributions unless they separately agree otherwise. Accepted contributions are available to everyone under Apache 2.0, including for commercial use. DCO sign-off certifies the right to contribute; it does not transfer copyright. Attribution is provided, but contributions create no automatic entitlement to payment, equity, royalties, or revenue participation. Paid work or revenue participation requires a separate agreement.

## Signal enterprise implementations

[Signal](https://signalprivatemarkets.com) provides enterprise capabilities for governed implementation, domain-specific ontologies, specialized intelligence, and integrations. These commercial capabilities are separate from the public foundation. Other organizations may independently implement PRUDENCE without using Signal.

## Canonical namespace

`https://prudence.signalprivatemarkets.com/open/core/v0.1/`

Schema identifiers are permanent: published identifiers are never moved or reused, and they remain stable if repository hosting changes. The `open/core` path holds the public core; any future public profiles or extensions receive their own paths. The validator loads schemas locally and does not require network access to the namespace. Hosting of the schema identifiers is not required for local validation; until files are served at those paths, identifiers may not resolve.

## License

Apache License 2.0. See `LICENSE`.
