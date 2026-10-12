# Changelog

## 0.1 — public draft (unreleased)

First public draft for implementation and feedback.

- Ten concepts: Mandate, Actor, Authorization, Decision, Evidence, Justification, Action, Result, Exception, Record Event.
- Nine record rules, including retention of unauthorized actions with linked Exceptions, and separation of stated justification from captured evidence.
- One structure for human, semi-automated, and automated actions, with separate execution attempts and observed results.
- JSON Schema for each concept and a record set.
- Structural validator with tests, including a check that every documented error code is exercised and that wrong-typed input is reported rather than causing a failure.
- Two synthetic examples (human-approved contract award; automated payment release with a retry), one invalid example, one extension example.

Credits: architecture and development by Signal Private Markets Infrastructure, Inc.; outside contributions credited to their respective contributors.

Release preparation: clarified Signal ownership and release authority, contributor rights, the open-core commitment and the canonical namespace (https://prudence.signalprivatemarkets.com/open/core/v0.1/). No concept, schema rule or validator behavior changed.
