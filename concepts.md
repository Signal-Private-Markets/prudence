# PRUDENCE v0.1 concepts and record rules

A **record set** is one JSON document: `{"prudence": "0.1", "records": [ ... ]}`. Each record has an `id`, unique within the set, and a `type`. Records refer to one another by `id`. Any record may carry an `extensions` object (see `extending.md`). Schemas are in `schema/`.

## Concepts

| Concept | What it records | Required fields |
| --- | --- | --- |
| **Mandate** | The standing charge that decisions serve: its purpose, constraints, and scope | `name`, `purpose`, `version` |
| **Actor** | A person, organization, or system that decides, approves, or acts | `actorKind` (`human`, `organization`, `system`), `name`; `systemVersion` for systems |
| **Authorization** | A versioned grant permitting an actor to decide or act, within stated limits | `authorizationId`, `version`, `grantor`, `grantee`, `scope`, `humanApprovalRequired`, `validFrom` |
| **Decision** | A choice made under a mandate | `mandate`, `summary`, `decidedBy`, `authorization`, `authorizationVersion`, `status`, `approval`, `knowledgeAsOf` |
| **Evidence** | Material captured from a source, including documents, data, and system outputs | `description`, `source`, `capturedAt`, `capturedBy`, `contentRef` |
| **Justification** | Reasoning stated by an actor about a decision or action | `about`, `statedBy`, `statedAt`, `statement` |
| **Action** | An intended or performed act implementing a decision, with zero or more execution attempts | `decision`, `performer`, `mode`, `authorization`, `authorizationVersion`, `description`, `status`, `attempts` |
| **Result** | The observed outcome of one execution attempt | `action`, `attemptId`, `observedBy`, `observedAt`, `outcome` |
| **Exception** | A condition that stops normal completion | `exceptionType`, `raisedOn`, `raisedBy`, `raisedAt`, `description` |
| **Record Event** | An append-only entry for each creation or change of a record | `subject`, `actor`, `at`, `change`, `prior` |

Notes on specific fields:

- **Authorization versions.** Each version of a grant is its own record, sharing an `authorizationId`. A later version names the earlier one in `supersedes`.
- **Decision times.** `decidedAt` is when the choice was made, `effectiveAt` when it takes effect, and `knowledgeAsOf` the point in time the decision-makers' information reflects.
- **Action mode.** `human`, `semi_automated`, or `automated`. A system that acts is an Actor with `actorKind: system`; its outputs are Evidence and its stated explanation is a Justification.
- **Justification is optional in v0.1.** The record rules govern stated reasoning when it is recorded; they do not require it. See `LIMITATIONS.md`.
- **Exception types.** `missing_decision`, `missing_authorization`, `missing_evidence`, `expired_authority`, `conflicting_instructions`, `execution_failure`, `escalation`.

## Status transitions

Decision `status` starts at `proposed`.

| From | May change to |
| --- | --- |
| proposed | approved, rejected |
| approved | superseded |

Decision `approval.status` is one of `pending`, `approved`, `rejected`, or `not_required_standing_authority`. The last applies when the cited Authorization does not require human approval, so automated decisions carry no invented human approval.

Action `status` starts at `proposed`.

| From | May change to |
| --- | --- |
| proposed | authorized, rejected, cancelled; attempted only when an Exception records a missing decision or authorization |
| authorized | attempted, cancelled |
| attempted | completed, failed |
| failed | attempted (retry), cancelled |

Each status change is recorded as a Record Event with `change.kind: status_changed`, `field: status`, `from`, and `to`.

## Record rules

1. **Recording is not authorizing.** An Authorization record describes a grant. It does not itself permit any action. Implementers provide enforcement.
2. **Every Action names its Authorization and version, or records that none was relied on.** The cited version must match the Authorization record. The performer must be the grantee.
3. **Unauthorized and undecided actions are kept.** An action taken without a decision or without authorization, or carried out under a decision that was never approved (proposed or rejected), is still recorded as an Action, with a linked Exception identifying what was missing (`missing_decision` or `missing_authorization`). The record preserves what actually happened.
4. **Status follows the transitions above.** A Decision's cited Authorization grantee must be among its deciders. A Decision that requires human approval must name at least one human approver.
5. **Results are observed, not asserted.** A Result is separate from Action status, names one attempt, names who or what observed it, and is not observed before that attempt started. An Action may have several attempts; each earlier attempt must have failed.
6. **Justification and Evidence stay distinct.** Reasoning an actor states, including an automated agent's explanation, is a Justification linked to its actor. Captured sources and system outputs are Evidence. A Justification is evidence of what the actor stated, not independent evidence that the statement is true.
7. **Exceptions are first-class.** They are recorded against the Decision or Action they affect. An execution failure names an attempt whose status is failed. An attempt outside its authorization's validity period requires an `expired_authority` Exception.
8. **Every creation and change produces a Record Event.** Each record's events form one unbroken sequence, starting with `created`, each naming its `prior`, in non-decreasing time. Earlier states are not overwritten.
9. **Records can be private.** The specification defines record structure. Publishing the specification publishes no institutional data, and record sets can be shared selectively.
