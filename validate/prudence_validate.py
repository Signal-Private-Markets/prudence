#!/usr/bin/env python3
"""PRUDENCE v0.1 structural validator.

Checks that a record set is well-formed and internally consistent:
required fields, valid references, permitted status transitions,
the record rules in concepts.md, and the supplied Record Event sequence.

It does not check whether evidence is authentic, whether an authorization
was validly granted, or whether a decision was sound. See LIMITATIONS.md.

Usage:
    python validate/prudence_validate.py FILE [FILE ...]

Exit status: 0 if every file is valid, 1 if any file has errors, 2 on usage errors,
3 if the validator itself fails (a defect to report, not a verdict on the file).
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"

TYPE_SCHEMA = {
    "Mandate": "mandate", "Actor": "actor", "Authorization": "authorization",
    "Decision": "decision", "Evidence": "evidence", "Justification": "justification",
    "Action": "action", "Result": "result", "Exception": "exception",
    "RecordEvent": "recordEvent",
}

# (record type, field) -> allowed target types. "*" = any record except RecordEvent.
REFERENCES = {
    ("Authorization", "grantor"): {"Actor"},
    ("Authorization", "grantee"): {"Actor"},
    ("Authorization", "mandate"): {"Mandate"},
    ("Authorization", "supersedes"): {"Authorization"},
    ("Decision", "mandate"): {"Mandate"},
    ("Decision", "decidedBy"): {"Actor"},
    ("Decision", "authorization"): {"Authorization"},
    ("Decision", "evidence"): {"Evidence"},
    ("Decision", "supersededBy"): {"Decision"},
    ("Evidence", "capturedBy"): {"Actor"},
    ("Evidence", "sourceActor"): {"Actor"},
    ("Justification", "about"): {"Decision", "Action"},
    ("Justification", "statedBy"): {"Actor"},
    ("Justification", "citesEvidence"): {"Evidence"},
    ("Action", "decision"): {"Decision"},
    ("Action", "performer"): {"Actor"},
    ("Action", "authorization"): {"Authorization"},
    ("Result", "action"): {"Action"},
    ("Result", "observedBy"): {"Actor"},
    ("Result", "evidence"): {"Evidence"},
    ("Exception", "raisedOn"): {"Decision", "Action"},
    ("Exception", "raisedBy"): {"Actor"},
    ("RecordEvent", "subject"): {"*"},
    ("RecordEvent", "actor"): {"Actor"},
    ("RecordEvent", "prior"): {"RecordEvent"},
}

INITIAL_STATUS = {"Decision": "proposed", "Action": "proposed"}
TRANSITIONS = {
    "Decision": {
        "proposed": {"approved", "rejected"},
        "approved": {"superseded"},
    },
    "Action": {
        "proposed": {"authorized", "rejected", "cancelled"},
        "authorized": {"attempted", "cancelled"},
        "attempted": {"completed", "failed"},
        "failed": {"attempted", "cancelled"},
    },
}
# Allowed only when the action carries an Exception recording the missing link.
UNAUTHORIZED_TRANSITION = ("proposed", "attempted")


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class Schemas:
    """The schemas in schema/, looked up by file name.

    Each schema's canonical id comes from its own "$id", so the namespace is
    defined only in namespace.json (via tools/gen_schemas.py), never here.
    """

    def __init__(self, schema_dir: Path = SCHEMA_DIR) -> None:
        self.by_name: dict[str, dict] = {}
        self._validators: dict[str, Draft202012Validator] = {}
        resources = []
        for path in sorted(schema_dir.glob("*.schema.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.by_name[path.name] = doc
            resources.append((doc["$id"], Resource.from_contents(doc)))
        self.registry = Registry().with_resources(resources)

    def validator(self, name: str) -> Draft202012Validator:
        if name not in self._validators:
            self._validators[name] = Draft202012Validator(
                self.by_name[name], registry=self.registry, format_checker=FormatChecker())
        return self._validators[name]

    def envelope_validator(self) -> Draft202012Validator:
        """recordset.schema.json with its per-record "items" rule removed.

        Every other envelope constraint applies unchanged. The removed rule says each record
        must match one concept schema; check_schema enforces exactly that, record by record,
        against the same schemas, with messages that name the record.
        """
        if "_envelope" not in self._validators:
            env = copy.deepcopy(self.by_name["recordset.schema.json"])
            del env["properties"]["records"]["items"]
            self._validators["_envelope"] = Draft202012Validator(env, registry=self.registry,
                                                                 format_checker=FormatChecker())
        return self._validators["_envelope"]


def load_schemas() -> Schemas:
    return Schemas()


class Report:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str, str]] = []

    def add(self, code: str, record_id: str, message: str) -> None:
        self.errors.append((code, record_id, message))


def check_schema(data, schemas: Schemas, report: Report) -> list[dict]:
    """Validate the envelope against recordset.schema.json and each record against its concept schema.

    Envelope errors that sit inside an individual record are left to the per-record
    check, which reports them against the record's id with a clearer message.
    """
    envelope_errors = list(schemas.envelope_validator().iter_errors(data))
    for e in sorted(envelope_errors, key=lambda e: list(map(str, e.path))):
        where = "/".join(str(p) for p in e.path) or "(record set)"
        report.add("ENVELOPE", "-", f"{where}: {e.message}")
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        return []
    valid = []
    for i, record in enumerate(data["records"]):
        rid = record.get("id") if isinstance(record, dict) else None
        rid = rid if isinstance(rid, str) else f"records[{i}]"
        rtype = record.get("type") if isinstance(record, dict) else None
        if not isinstance(rtype, str) or rtype not in TYPE_SCHEMA:
            report.add("SCHEMA", rid, f"unknown or missing type {rtype!r}")
            continue
        validator = schemas.validator(f"{TYPE_SCHEMA[rtype]}.schema.json")
        errs = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
        for e in errs:
            where = "/".join(str(p) for p in e.path) or "(record)"
            report.add("SCHEMA", rid, f"{where}: {e.message}")
        if not errs:
            valid.append(record)
    return valid


def iter_refs(record):
    rtype = record["type"]
    for (t, field), targets in REFERENCES.items():
        if t != rtype or field not in record:
            continue
        value = record[field]
        values = value if isinstance(value, list) else [value]
        for v in values:
            if v is not None:
                yield field, v, targets
    if rtype == "Decision":
        for v in record.get("approval", {}).get("approvedBy", []):
            yield "approval.approvedBy", v, {"Actor"}


def check_references(records, by_id, report):
    for r in records:
        for field, target, allowed in iter_refs(r):
            if target not in by_id:
                report.add("REF", r["id"], f"{field} refers to {target!r}, which is not in the record set")
                continue
            ttype = by_id[target]["type"]
            if "*" in allowed:
                if ttype == "RecordEvent":
                    report.add("REF", r["id"], f"{field} may not refer to a Record Event")
            elif ttype not in allowed:
                report.add("REF", r["id"], f"{field} refers to {target!r} ({ttype}); expected {' or '.join(sorted(allowed))}")


def exceptions_on(records, rid, kind=None):
    return [r for r in records if r["type"] == "Exception" and r["raisedOn"] == rid
            and (kind is None or r["exceptionType"] == kind)]


def check_authorization_links(records, by_id, report):
    for r in records:
        if r["type"] == "Authorization" and "supersedes" in r:
            prev = by_id.get(r["supersedes"])
            if prev and prev["type"] == "Authorization":
                if prev["authorizationId"] != r["authorizationId"] or prev["version"] >= r["version"]:
                    report.add("AUTH_VERSION", r["id"], "supersedes must name an earlier version of the same authorizationId")
        if r["type"] not in ("Decision", "Action"):
            continue
        auth_id, version = r.get("authorization"), r.get("authorizationVersion")
        if (auth_id is None) != (version is None):
            report.add("AUTH_VERSION", r["id"], "authorization and authorizationVersion must both be set or both be null")
            continue
        if auth_id is None:
            continue
        auth = by_id.get(auth_id)
        if not auth or auth["type"] != "Authorization":
            continue
        if auth["version"] != version:
            report.add("AUTH_VERSION", r["id"],
                       f"cites version {version} of {auth_id}, but {auth_id} is version {auth['version']}")
        grantee = auth["grantee"]
        if r["type"] == "Action" and r["performer"] != grantee:
            report.add("AUTH_GRANTEE", r["id"], f"performer {r['performer']} is not the grantee ({grantee}) of {auth_id}")
        if r["type"] == "Decision" and grantee not in r["decidedBy"]:
            report.add("AUTH_GRANTEE", r["id"], f"grantee {grantee} of {auth_id} is not among decidedBy")


def check_missing_links(records, by_id, report):
    for r in records:
        if r["type"] != "Action":
            continue
        if r["decision"] is None and not exceptions_on(records, r["id"], "missing_decision"):
            report.add("MISSING_LINK", r["id"], "action has no decision and no linked missing_decision Exception")
        decision = by_id.get(r["decision"]) if r["decision"] else None
        # An action that was attempted under a decision that was never approved (proposed or
        # rejected) is kept as a record of what happened, but must carry a missing_decision Exception.
        # Superseded decisions were approved when acted on, so they do not trigger this.
        if (decision and decision["type"] == "Decision" and decision["status"] in ("proposed", "rejected")
                and r["attempts"] and not exceptions_on(records, r["id"], "missing_decision")):
            report.add("MISSING_LINK", r["id"],
                       f"action was attempted under {decision['id']}, whose status is {decision['status']}, "
                       "and no missing_decision Exception is linked")
        if r["authorization"] is None and not exceptions_on(records, r["id"], "missing_authorization"):
            report.add("MISSING_LINK", r["id"], "action has no authorization and no linked missing_authorization Exception")


def check_approval(records, by_id, report):
    for r in records:
        if r["type"] != "Decision":
            continue
        approval = r["approval"]
        auth = by_id.get(r["authorization"])
        if not auth or auth["type"] != "Authorization":
            continue
        if approval["status"] == "not_required_standing_authority" and auth["humanApprovalRequired"]:
            report.add("APPROVAL", r["id"], f"approval marked not required, but {auth['id']} requires human approval")
        if r["status"] == "approved":
            if approval["status"] not in ("approved", "not_required_standing_authority"):
                report.add("APPROVAL", r["id"], f"decision is approved but approval status is {approval['status']}")
            if approval["status"] == "approved":
                approvers = approval.get("approvedBy", [])
                if not approvers:
                    report.add("APPROVAL", r["id"], "approval status is approved but approvedBy is empty")
                if auth["humanApprovalRequired"] and not any(
                        by_id.get(a, {}).get("actorKind") == "human" for a in approvers):
                    report.add("APPROVAL", r["id"], f"{auth['id']} requires human approval; no human actor is in approvedBy")
        if r["status"] == "superseded" and "supersededBy" not in r:
            report.add("APPROVAL", r["id"], "superseded decision must name supersededBy")


def check_attempts(records, by_id, report):
    for r in records:
        if r["type"] == "Action":
            attempts = r["attempts"]
            ids = [a["attemptId"] for a in attempts]
            if len(ids) != len(set(ids)):
                report.add("ATTEMPT", r["id"], "attemptId values must be unique within an action")
            last = attempts[-1]["status"] if attempts else None
            status = r["status"]
            if status in ("proposed", "authorized", "rejected") and attempts:
                report.add("ATTEMPT", r["id"], f"status {status} cannot have execution attempts")
            if status in ("attempted", "completed", "failed") and last != status:
                report.add("ATTEMPT", r["id"], f"status is {status} but the latest attempt is {last}")
            for a in attempts[:-1]:
                if a["status"] != "failed":
                    report.add("ATTEMPT", r["id"], f"attempt {a['attemptId']} is followed by another attempt, so it must be failed")
            auth = by_id.get(r["authorization"]) if r["authorization"] else None
            if auth and auth["type"] == "Authorization":
                for a in attempts:
                    start = ts(a["startedAt"])
                    outside = start < ts(auth["validFrom"]) or ("validTo" in auth and start > ts(auth["validTo"]))
                    if outside and not exceptions_on(records, r["id"], "expired_authority"):
                        report.add("AUTH_VALIDITY", r["id"],
                                   f"attempt {a['attemptId']} is outside the validity of {auth['id']} and no expired_authority Exception is linked")
        if r["type"] in ("Result", "Exception") and r.get("attemptId"):
            target = by_id.get(r["action"] if r["type"] == "Result" else r["raisedOn"])
            if target and target["type"] == "Action":
                attempt = next((a for a in target["attempts"] if a["attemptId"] == r["attemptId"]), None)
                if attempt is None:
                    report.add("ATTEMPT", r["id"], f"attemptId {r['attemptId']} does not exist on {target['id']}")
                else:
                    if r["type"] == "Result" and ts(r["observedAt"]) < ts(attempt["startedAt"]):
                        report.add("ATTEMPT", r["id"],
                                   f"observedAt {r['observedAt']} is earlier than attempt {attempt['attemptId']} started ({attempt['startedAt']})")
                    if r["type"] == "Exception" and r["exceptionType"] == "execution_failure" and attempt["status"] != "failed":
                        report.add("ATTEMPT", r["id"],
                                   f"execution_failure names attempt {attempt['attemptId']}, whose status is {attempt['status']}, not failed")
            elif target:
                report.add("ATTEMPT", r["id"], "attemptId may only be used on an Action")
        if r["type"] == "Exception" and r["exceptionType"] == "execution_failure" and not r.get("attemptId"):
            report.add("ATTEMPT", r["id"], "execution_failure Exception must name the failed attemptId")


def check_events(records, by_id, report):
    events = [r for r in records if r["type"] == "RecordEvent"]
    by_subject: dict[str, list[dict]] = {}
    for e in events:
        by_subject.setdefault(e["subject"], []).append(e)

    for r in records:
        if r["type"] == "RecordEvent":
            continue
        chain = by_subject.get(r["id"], [])
        if not chain:
            report.add("EVENTS", r["id"], "record has no Record Events; at least a created event is required")
            continue
        roots = [e for e in chain if e["prior"] is None]
        if len(roots) != 1:
            report.add("EVENTS", r["id"], f"expected exactly one first event (prior: null), found {len(roots)}")
            continue
        if roots[0]["change"]["kind"] != "created":
            report.add("EVENTS", r["id"], "first event must have change.kind created")
        nxt: dict[str, list[dict]] = {}
        for e in chain:
            if e["prior"] is not None:
                prior = by_id.get(e["prior"])
                if prior and prior.get("subject") != r["id"]:
                    report.add("EVENTS", e["id"], f"prior {e['prior']} belongs to a different subject")
                nxt.setdefault(e["prior"], []).append(e)
        ordered, cur = [roots[0]], roots[0]
        while True:
            following = nxt.get(cur["id"], [])
            if len(following) > 1:
                report.add("EVENTS", r["id"], f"sequence forks after {cur['id']}: {', '.join(f['id'] for f in following)}")
                break
            if not following:
                break
            cur = following[0]
            if cur in ordered:
                report.add("EVENTS", r["id"], "sequence contains a cycle")
                break
            ordered.append(cur)
        if len(ordered) != len(chain):
            missing = sorted({e["id"] for e in chain} - {e["id"] for e in ordered})
            report.add("EVENTS", r["id"], f"events not connected to the sequence: {', '.join(missing)}")
        for a, b in zip(ordered, ordered[1:]):
            if ts(b["at"]) < ts(a["at"]):
                report.add("EVENTS", b["id"], f"timestamp is earlier than the preceding event {a['id']}")
        check_transitions(r, ordered, records, report)


def check_transitions(record, ordered, records, report):
    rtype = record["type"]
    if rtype not in TRANSITIONS:
        return
    status = INITIAL_STATUS[rtype]
    for e in ordered:
        change = e["change"]
        if change["kind"] != "status_changed" or change.get("field") != "status":
            continue
        if change["from"] != status:
            report.add("TRANSITION", e["id"], f"from {change['from']!r} does not match the current status {status!r}")
        allowed = TRANSITIONS[rtype].get(change["from"], set())
        ok = change["to"] in allowed
        if not ok and rtype == "Action" and (change["from"], change["to"]) == UNAUTHORIZED_TRANSITION:
            ok = bool(exceptions_on(records, record["id"], "missing_authorization")
                      or exceptions_on(records, record["id"], "missing_decision"))
        if not ok:
            report.add("TRANSITION", e["id"], f"{rtype} status may not change from {change['from']!r} to {change['to']!r}")
        status = change["to"]
    if record["status"] != status:
        report.add("TRANSITION", record["id"], f"status is {record['status']!r} but its Record Events end at {status!r}")


def validate_file(path: Path, schemas: Schemas) -> Report:
    report = Report()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.add("FILE", "-", str(exc))
        return report
    records = check_schema(data, schemas, report)
    by_id: dict[str, dict] = {}
    for r in records:
        if r["id"] in by_id:
            report.add("DUPLICATE_ID", r["id"], "id is used by more than one record")
        by_id[r["id"]] = r
    if report.errors:
        return report  # rule checks assume schema-valid records
    check_references(records, by_id, report)
    if report.errors:
        return report
    check_authorization_links(records, by_id, report)
    check_missing_links(records, by_id, report)
    check_approval(records, by_id, report)
    check_attempts(records, by_id, report)
    check_events(records, by_id, report)
    return report


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    schemas = load_schemas()
    failed = False
    for arg in argv:
        path = Path(arg)
        try:
            report = validate_file(path, schemas)
        except Exception as exc:  # a defect in the validator, never a verdict on the file
            print(f"ERROR    {path}  validator fault: {type(exc).__name__}: {exc}", file=sys.stderr)
            print("         Please report this with the input file; see GOVERNANCE.md.", file=sys.stderr)
            return 3
        if report.errors:
            failed = True
            print(f"INVALID  {path}  ({len(report.errors)} error{'s' if len(report.errors) != 1 else ''})")
            for code, rid, msg in report.errors:
                print(f"  [{code}] {rid}: {msg}")
        else:
            count = len(json.loads(path.read_text(encoding="utf-8"))["records"])
            print(f"VALID    {path}  ({count} records)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
