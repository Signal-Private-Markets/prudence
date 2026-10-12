"""Tests for the PRUDENCE v0.1 validator.

Run from the repository root: python -m unittest discover -s validate

Every error code documented in LIMITATIONS.md has at least one case in FAILING_CASES
that must produce it; test_every_documented_code_has_a_case enforces this.
"""
import copy
import json
import re
import unittest
from pathlib import Path

from prudence_validate import load_schemas, validate_file

ROOT = Path(__file__).resolve().parent.parent
HUMAN = ROOT / "examples" / "human-approved" / "procurement-award.json"
AUTOMATED = ROOT / "examples" / "automated" / "payment-release.json"
INVALID = ROOT / "examples" / "invalid" / "wrong-authorization-version.json"
EXTENDED = ROOT / "examples" / "extension" / "procurement-award-extended.json"
SCHEMAS = load_schemas()
TMP = ROOT / "validate" / ".test-tmp.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find(doc, rid):
    return next(r for r in doc["records"] if r["id"] == rid)


def run(doc):
    TMP.write_text(json.dumps(doc), encoding="utf-8")
    try:
        return [code for code, _, _ in validate_file(TMP, SCHEMAS).errors]
    finally:
        TMP.unlink(missing_ok=True)


def add_record(doc, record, actor, at):
    """Append a record together with its created Record Event."""
    doc["records"].append(record)
    doc["records"].append({"id": f"EVT-{record['id']}-01", "type": "RecordEvent", "subject": record["id"],
                           "actor": actor, "at": at, "change": {"kind": "created"}, "prior": None})


def add_status_event(doc, subject, actor, at, frm, to):
    prior = [r for r in doc["records"] if r["type"] == "RecordEvent" and r["subject"] == subject][-1]["id"]
    doc["records"].append({"id": f"EVT-{subject}-{frm}-{to}-{at}", "type": "RecordEvent", "subject": subject,
                           "actor": actor, "at": at, "prior": prior,
                           "change": {"kind": "status_changed", "field": "status", "from": frm, "to": to}})


# ---------------------------------------------------------------- scenario builders

def unauthorized_action(with_exceptions):
    """A payment sent with no decision and no authorization."""
    doc = load(AUTOMATED)
    svc = "ACT-ap-service"
    add_record(doc, {"id": "ACT-UNAUTH", "type": "Action", "decision": None, "performer": svc,
                     "mode": "automated", "authorization": None, "authorizationVersion": None,
                     "description": "Duplicate payment submitted without a decision or authorization.",
                     "status": "completed",
                     "attempts": [{"attemptId": "A1", "startedAt": "2026-10-03T09:00:00Z", "status": "completed"}]},
               svc, "2026-10-03T09:00:00Z")
    add_status_event(doc, "ACT-UNAUTH", svc, "2026-10-03T09:00:00Z", "proposed", "attempted")
    add_status_event(doc, "ACT-UNAUTH", svc, "2026-10-03T09:01:00Z", "attempted", "completed")
    if with_exceptions:
        for kind in ("missing_decision", "missing_authorization"):
            add_record(doc, {"id": f"EXC-UNAUTH-{kind}", "type": "Exception", "exceptionType": kind,
                             "raisedOn": "ACT-UNAUTH", "raisedBy": "ACT-finance-director",
                             "raisedAt": "2026-10-03T11:00:00Z",
                             "description": "Payment was released with no decision or authorization."},
                       "ACT-finance-director", "2026-10-03T11:00:00Z")
    return doc


def expired_authority(with_exception):
    """The officer executes the contract a day after the execution authority lapsed."""
    doc = load(HUMAN)
    find(doc, "AUTH-OFFICER-EXECUTE-v1")["validTo"] = "2026-09-28T23:59:59Z"
    if with_exception:
        add_record(doc, {"id": "EXC-EXECUTE-EXPIRED", "type": "Exception", "exceptionType": "expired_authority",
                         "raisedOn": "ACT-EXECUTE-014", "raisedBy": "ACT-clerk",
                         "raisedAt": "2026-09-30T09:00:00Z",
                         "description": "Contract executed one day after AUTH-OFFICER-EXECUTE-v1 expired."},
                   "ACT-clerk", "2026-09-30T09:00:00Z")
    return doc


def rejected_decision(with_exception):
    """The payment decision is rejected, but the payment was still sent."""
    doc = load(AUTOMATED)
    dec = find(doc, "DEC-PAY-8841")
    dec["status"], dec["approval"] = "rejected", {"status": "rejected"}
    find(doc, "EVT-DEC-PAY-8841-02")["change"]["to"] = "rejected"
    if with_exception:
        add_record(doc, {"id": "EXC-PAY-8841-REJECTED", "type": "Exception", "exceptionType": "missing_decision",
                         "raisedOn": "ACT-PAY-8841", "raisedBy": "ACT-finance-director",
                         "raisedAt": "2026-10-02T15:00:00Z",
                         "description": "Payment released although DEC-PAY-8841 was rejected."},
                   "ACT-finance-director", "2026-10-02T15:00:00Z")
    return doc


def mutate(path, fn):
    def build():
        doc = load(path)
        fn(doc)
        return doc
    return build


def set_field(rid, field, value):
    return lambda doc: find(doc, rid).__setitem__(field, value)


def drop_events_for(subject):
    def fn(doc):
        doc["records"] = [r for r in doc["records"] if not (r["type"] == "RecordEvent" and r["subject"] == subject)]
    return fn


def duplicate(rid):
    return lambda doc: doc["records"].append(copy.deepcopy(find(doc, rid)))


# ---------------------------------------------------------------- cases

# (name, expected code, builder). Each builder returns a record set that must fail with the code.
FAILING_CASES = [
    ("envelope: empty records", "ENVELOPE", mutate(HUMAN, lambda d: d.__setitem__("records", []))),
    ("envelope: undeclared top-level field", "ENVELOPE", mutate(HUMAN, lambda d: d.__setitem__("notes", "x"))),
    ("envelope: wrong version", "ENVELOPE", mutate(HUMAN, lambda d: d.__setitem__("prudence", "0.2"))),
    ("schema: system actor without version", "SCHEMA",
     mutate(AUTOMATED, lambda d: find(d, "ACT-ap-service").pop("systemVersion"))),
    ("schema: unknown record type", "SCHEMA", mutate(HUMAN, set_field("MAN-PW-PROC", "type", "Policy"))),
    ("duplicate id", "DUPLICATE_ID", mutate(HUMAN, duplicate("MAN-PW-PROC"))),
    ("reference to a missing record", "REF", mutate(HUMAN, set_field("DEC-AWARD-014", "mandate", "MAN-NONE"))),
    ("reference to the wrong type", "REF", mutate(HUMAN, set_field("ACT-EXECUTE-014", "decision", "ACT-chair"))),
    ("authorization version mismatch", "AUTH_VERSION", lambda: load(INVALID)),
    ("supersedes a different grant", "AUTH_VERSION",
     mutate(AUTOMATED, set_field("AUTH-AP-RELEASE-v1", "authorizationId", "AUTH-OTHER"))),
    ("performer is not the grantee", "AUTH_GRANTEE", mutate(HUMAN, set_field("ACT-EXECUTE-014", "performer", "ACT-clerk"))),
    ("deciders exclude the grantee", "AUTH_GRANTEE", mutate(HUMAN, set_field("DEC-AWARD-014", "decidedBy", ["ACT-chair"]))),
    ("attempt outside authorization validity", "AUTH_VALIDITY", lambda: expired_authority(False)),
    ("unauthorized action without exception", "MISSING_LINK", lambda: unauthorized_action(False)),
    ("standing authority claimed where human approval is required", "APPROVAL",
     mutate(HUMAN, set_field("DEC-AWARD-014", "approval", {"status": "not_required_standing_authority"}))),
    ("human approval required but no human approver", "APPROVAL",
     mutate(HUMAN, set_field("DEC-AWARD-014", "approval", {"status": "approved", "approvedBy": ["ACT-committee"]}))),
    ("result names an unknown attempt", "ATTEMPT", mutate(AUTOMATED, set_field("RES-PAY-8841-A2", "attemptId", "A9"))),
    ("status disagrees with latest attempt", "ATTEMPT",
     mutate(AUTOMATED, lambda d: find(d, "ACT-PAY-8841")["attempts"][1].__setitem__("status", "failed"))),
    ("execution failure without attempt", "ATTEMPT", mutate(AUTOMATED, lambda d: find(d, "EXC-PAY-8841-A1").pop("attemptId"))),
    ("illegal status transition", "TRANSITION",
     mutate(HUMAN, lambda d: next(r for r in d["records"] if r["type"] == "RecordEvent"
                                  and r["subject"] == "ACT-EXECUTE-014"
                                  and r["change"].get("to") == "authorized")["change"].__setitem__("to", "completed"))),
    ("status disagrees with last status event", "TRANSITION",
     mutate(HUMAN, set_field("DEC-AWARD-014", "status", "rejected"))),
    ("record with no events", "EVENTS", mutate(HUMAN, drop_events_for("MAN-PW-PROC"))),
    ("forked event sequence", "EVENTS",
     mutate(HUMAN, lambda d: d["records"].append({"id": "EVT-FORK", "type": "RecordEvent", "subject": "DEC-AWARD-014",
                                                   "actor": "ACT-officer", "at": "2026-09-20T10:00:00Z",
                                                   "change": {"kind": "amended", "field": "summary"},
                                                   "prior": "EVT-DEC-AWARD-014-01"}))),
    ("event earlier than its predecessor", "EVENTS",
     mutate(HUMAN, set_field("EVT-DEC-AWARD-014-02", "at", "2026-09-01T00:00:00Z"))),
    ("record type is not a string", "SCHEMA", mutate(HUMAN, set_field("MAN-PW-PROC", "type", []))),
    ("status event value is not a string", "SCHEMA",
     mutate(HUMAN, lambda d: find(d, "EVT-DEC-AWARD-014-02")["change"].__setitem__("to", {}))),
    ("action executed under a rejected decision without exception", "MISSING_LINK", lambda: rejected_decision(False)),
    ("execution failure names a completed attempt", "ATTEMPT",
     mutate(AUTOMATED, set_field("EXC-PAY-8841-A1", "attemptId", "A2"))),
    ("result observed before its attempt started", "ATTEMPT",
     mutate(AUTOMATED, set_field("RES-PAY-8841-A2", "observedAt", "2026-10-02T13:30:00Z"))),
]

VALID_CASES = [
    ("human-approved example", lambda: load(HUMAN)),
    ("automated example", lambda: load(AUTOMATED)),
    ("extension example", lambda: load(EXTENDED)),
    ("unauthorized action kept with linked exceptions", lambda: unauthorized_action(True)),
    ("expired authority recorded by an exception", lambda: expired_authority(True)),
    ("action under a rejected decision kept with an exception", lambda: rejected_decision(True)),
]


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


class ValidatorTests(unittest.TestCase):
    def test_unreadable_file(self):
        TMP.write_text("{not json", encoding="utf-8")
        try:
            self.assertEqual([c for c, _, _ in validate_file(TMP, SCHEMAS).errors], ["FILE"])
        finally:
            TMP.unlink(missing_ok=True)

    def test_invalid_example_reports_exactly_one_error(self):
        errors = validate_file(INVALID, SCHEMAS).errors
        self.assertEqual([c for c, _, _ in errors], ["AUTH_VERSION"])

    def test_wrong_typed_values_are_reported_not_raised(self):
        """Replace every field of one record of each type with wrong-typed values.

        The validator must return errors for each, never raise.
        """
        samples = {}
        for path in (HUMAN, AUTOMATED):
            for r in load(path)["records"]:
                samples.setdefault(r["type"], (path, r["id"]))
        self.assertEqual(len(samples), 10)
        for rtype, (path, rid) in samples.items():
            for field in list(find(load(path), rid)):
                for bad in ([], {}, None, 7, "x"):
                    if field == "id" and bad == "x":
                        continue
                    doc = load(path)
                    find(doc, rid)[field] = bad
                    TMP.write_text(json.dumps(doc), encoding="utf-8")
                    try:
                        validate_file(TMP, SCHEMAS)
                    except Exception as exc:  # pragma: no cover - failure path
                        self.fail(f"{rtype}.{field} = {bad!r} raised {type(exc).__name__}: {exc}")
                    finally:
                        TMP.unlink(missing_ok=True)

    def test_every_documented_code_has_a_case(self):
        documented = set(re.findall(r"^\| `([A-Z_]+)` \|", (ROOT / "LIMITATIONS.md").read_text(encoding="utf-8"), re.M))
        covered = {code for _, code, _ in FAILING_CASES} | {"FILE"}
        self.assertTrue(documented, "no codes found in LIMITATIONS.md")
        self.assertEqual(documented - covered, set(), "documented codes with no failing case")
        self.assertEqual(covered - documented, set(), "tested codes missing from LIMITATIONS.md")


# One named test per case, so each appears in the test output on its own.
for _name, _build in VALID_CASES:
    setattr(ValidatorTests, f"test_valid__{slug(_name)}",
            lambda self, b=_build: self.assertEqual(run(b()), []))
for _name, _code, _build in FAILING_CASES:
    setattr(ValidatorTests, f"test_fails_{_code.lower()}__{slug(_name)}",
            lambda self, c=_code, b=_build: self.assertIn(c, run(b())))


if __name__ == "__main__":
    unittest.main()
