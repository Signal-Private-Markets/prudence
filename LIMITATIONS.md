# Limitations and open questions

## What the validator checks

| Code | Check |
| --- | --- |
| `FILE` | The file can be read and parsed as JSON |
| `ENVELOPE` | The record set matches `recordset.schema.json`: the `prudence` version, at least one record, no undeclared top-level fields |
| `SCHEMA` | Each record matches its concept schema: required fields, types, allowed values |
| `DUPLICATE_ID` | Record ids are unique within the record set |
| `REF` | Every reference points to a record in the set, of the expected type |
| `AUTH_VERSION` | The cited authorization version matches the Authorization record; superseding versions share an `authorizationId` |
| `AUTH_GRANTEE` | An Action's performer is the grantee of the cited Authorization; a Decision's deciders include the grantee |
| `AUTH_VALIDITY` | Each attempt falls within the Authorization's validity period, or an `expired_authority` Exception is linked |
| `MISSING_LINK` | An Action with no decision or no authorization, or attempted under a decision that was never approved, has a linked Exception recording what was missing |
| `APPROVAL` | Approval status is consistent with the Authorization's `humanApprovalRequired` and with the Decision's status |
| `ATTEMPT` | Attempts are consistent with Action status; Results and execution-failure Exceptions name an existing attempt; a Result is not observed before its attempt started; an execution failure names a failed attempt |
| `TRANSITION` | Status changes follow the permitted transitions, and each record's status matches its last status event |
| `EVENTS` | Each record has one unbroken Record Event sequence starting with `created`, in non-decreasing time |

## What the validator does not check

- **Truth of evidence.** Whether captured material is authentic, complete, or accurately described.
- **Validity of authority.** Whether the grantor had power to grant an Authorization, or whether its limits were respected in substance (for example, whether an amount exceeded a stated limit).
- **Soundness of judgment.** Whether a decision was prudent, lawful, or adequate for its domain.
- **Completeness of history.** The validator checks the consistency of the Record Events supplied. It cannot establish that no events were omitted or that earlier records were not altered outside the supplied sequence. Tamper evidence, signing, and attestation are left to implementers.
- **Extension fields.** Only that each extension value is an object. See `extending.md`.
- **Presence of reasoning.** A record set is structurally valid without any Justification, and a Decision is valid without Evidence links. v0.1 checks that stated reasoning, when present, is well-formed and kept distinct from evidence; it does not require that reasoning be stated. This is weaker than requiring every decision, including one made by an automated agent, to carry its reasons. That stronger requirement belongs in a decision-documentation profile (see open questions), so that it can be required where it applies without making every record carry it.

## Known limitations of v0.1

- One record set per file. References across record sets are not defined.
- Limits in an Authorization are free text. They are not machine-evaluable.
- Schema identifiers use the canonical namespace `https://prudence.signalprivatemarkets.com/open/core/v0.1/`. The validator loads schemas locally. The namespace is set only in `namespace.json`; after changing it, run `python tools/gen_schemas.py schema`. The validator reads each schema's own identifier, so it needs no change.
- The JSON format is the only supported serialization.

## Open questions for v0.2

1. Should v0.2 define a decision-documentation profile: an additional set of checks under which every Decision must have at least one Justification and cite Evidence, and every automated Action must link the system's stated reasoning?
2. Should Authorization limits gain a structured, machine-evaluable form?
3. How should chains of delegation (a grantee delegating onward) be represented?
4. Should Decision gain states such as `withdrawn` or `deferred`?
5. What is the minimal format for sharing part of a record set while proving it belongs to a larger one?
6. Should Assessment, Review, and Classification Facet join the core?

Comments on these questions are welcome; see `GOVERNANCE.md`.
