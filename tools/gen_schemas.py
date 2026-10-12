"""Generate PRUDENCE v0.1 JSON Schemas.

Usage: python tools/gen_schemas.py schema

The namespace comes only from namespace.json at the repository root.
"""
import json, os, sys
from pathlib import Path

OUT = sys.argv[1]
NAMESPACE = json.loads((Path(__file__).resolve().parent.parent / "namespace.json").read_text(encoding="utf-8"))["base"]
BASE = NAMESPACE.rstrip("/") + "/schema/"

def ref(defn): return {"$ref": f"common.schema.json#/$defs/{defn}"}
REF = ref("recordRef")
TS = ref("timestamp")
NULLREF = {"oneOf": [REF, {"type": "null"}]}

def concept(name, title, description, props, required):
    p = {"id": ref("recordId"), "type": {"const": name}, "extensions": ref("extensions")}
    p.update(props)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + f"{name[0].lower() + name[1:]}.schema.json",
        "title": title,
        "description": description,
        "type": "object",
        "properties": p,
        "required": ["id", "type"] + required,
        "additionalProperties": False,
    }

common = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": BASE + "common.schema.json",
    "title": "PRUDENCE v0.1 common definitions",
    "$defs": {
        "recordId": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
                     "description": "Identifier unique within a record set."},
        "recordRef": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
                      "description": "Identifier of another record in the same record set."},
        "timestamp": {"type": "string", "format": "date-time",
                      "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"},
        "extensions": {"type": "object",
                       "description": "Extension data keyed by the extension's namespace URI.",
                       "propertyNames": {"pattern": "^https?://"},
                       "additionalProperties": {"type": "object"}},
    },
}

schemas = {}
schemas["mandate"] = concept("Mandate", "Mandate", "The standing charge that decisions serve.", {
    "name": {"type": "string", "minLength": 1},
    "purpose": {"type": "string", "minLength": 1},
    "constraints": {"type": "array", "items": {"type": "string", "minLength": 1}},
    "scope": {"type": "string"},
    "governingInstrument": {"type": "string"},
    "version": {"type": "integer", "minimum": 1},
}, ["name", "purpose", "version"])

schemas["actor"] = concept("Actor", "Actor", "A person, organization, or system that decides, approves, or acts.", {
    "actorKind": {"enum": ["human", "organization", "system"]},
    "name": {"type": "string", "minLength": 1},
    "role": {"type": "string"},
    "systemVersion": {"type": "string", "minLength": 1},
}, ["actorKind", "name"])
schemas["actor"]["allOf"] = [{"if": {"properties": {"actorKind": {"const": "system"}}},
                              "then": {"required": ["systemVersion"]}}]

schemas["authorization"] = concept("Authorization", "Authorization",
    "A versioned grant permitting an actor to decide or act. Recording it does not itself authorize anything.", {
    "authorizationId": {"type": "string", "minLength": 1,
                        "description": "Stable identifier shared by every version of the grant."},
    "version": {"type": "integer", "minimum": 1},
    "grantor": REF,
    "grantee": REF,
    "mandate": REF,
    "scope": {"type": "string", "minLength": 1},
    "limits": {"type": "array", "items": {"type": "string", "minLength": 1}},
    "humanApprovalRequired": {"type": "boolean"},
    "validFrom": TS,
    "validTo": TS,
    "supersedes": REF,
}, ["authorizationId", "version", "grantor", "grantee", "scope", "humanApprovalRequired", "validFrom"])

schemas["decision"] = concept("Decision", "Decision", "A choice made under a mandate.", {
    "mandate": REF,
    "summary": {"type": "string", "minLength": 1},
    "decidedBy": {"type": "array", "items": REF, "minItems": 1},
    "authorization": REF,
    "authorizationVersion": {"type": "integer", "minimum": 1},
    "status": {"enum": ["proposed", "approved", "rejected", "superseded"]},
    "approval": {
        "type": "object",
        "properties": {
            "status": {"enum": ["pending", "approved", "rejected", "not_required_standing_authority"]},
            "approvedBy": {"type": "array", "items": REF},
        },
        "required": ["status"],
        "additionalProperties": False,
    },
    "decidedAt": TS,
    "effectiveAt": TS,
    "knowledgeAsOf": TS,
    "alternatives": {"type": "array", "items": {
        "type": "object",
        "properties": {"description": {"type": "string", "minLength": 1}, "chosen": {"type": "boolean"}},
        "required": ["description", "chosen"], "additionalProperties": False}},
    "evidence": {"type": "array", "items": REF},
    "supersededBy": REF,
}, ["mandate", "summary", "decidedBy", "authorization", "authorizationVersion", "status", "approval", "knowledgeAsOf"])

schemas["evidence"] = concept("Evidence", "Evidence", "Material captured from a source.", {
    "description": {"type": "string", "minLength": 1},
    "source": {"type": "string", "minLength": 1},
    "sourceActor": REF,
    "capturedAt": TS,
    "capturedBy": REF,
    "contentRef": {"type": "string", "minLength": 1},
    "contentHash": {"type": "string", "pattern": "^[a-z0-9]+:[A-Fa-f0-9]+$"},
}, ["description", "source", "capturedAt", "capturedBy", "contentRef"])

schemas["justification"] = concept("Justification", "Justification",
    "Reasoning stated by an actor. It is evidence of what was stated, not that the statement is true.", {
    "about": REF,
    "statedBy": REF,
    "statedAt": TS,
    "statement": {"type": "string", "minLength": 1},
    "citesEvidence": {"type": "array", "items": REF},
    "alternativesRejected": {"type": "array", "items": {
        "type": "object",
        "properties": {"alternative": {"type": "string", "minLength": 1}, "reason": {"type": "string", "minLength": 1}},
        "required": ["alternative", "reason"], "additionalProperties": False}},
}, ["about", "statedBy", "statedAt", "statement"])

schemas["action"] = concept("Action", "Action",
    "An intended or performed act implementing a decision, with zero or more execution attempts.", {
    "decision": NULLREF,
    "performer": REF,
    "mode": {"enum": ["human", "semi_automated", "automated"]},
    "authorization": NULLREF,
    "authorizationVersion": {"oneOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
    "description": {"type": "string", "minLength": 1},
    "status": {"enum": ["proposed", "authorized", "rejected", "attempted", "completed", "failed", "cancelled"]},
    "attempts": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "attemptId": {"type": "string", "minLength": 1},
            "startedAt": TS,
            "status": {"enum": ["attempted", "completed", "failed"]},
        },
        "required": ["attemptId", "startedAt", "status"], "additionalProperties": False}},
}, ["decision", "performer", "mode", "authorization", "authorizationVersion", "description", "status", "attempts"])

schemas["result"] = concept("Result", "Result", "The observed outcome of one execution attempt.", {
    "action": REF,
    "attemptId": {"type": "string", "minLength": 1},
    "observedBy": REF,
    "observedAt": TS,
    "outcome": {"type": "string", "minLength": 1},
    "evidence": {"type": "array", "items": REF},
}, ["action", "attemptId", "observedBy", "observedAt", "outcome"])

schemas["exception"] = concept("Exception", "Exception", "A condition that stops normal completion.", {
    "exceptionType": {"enum": ["missing_decision", "missing_authorization", "missing_evidence",
                               "expired_authority", "conflicting_instructions", "execution_failure", "escalation"]},
    "raisedOn": REF,
    "attemptId": {"type": "string", "minLength": 1},
    "raisedBy": REF,
    "raisedAt": TS,
    "description": {"type": "string", "minLength": 1},
    "resolution": {"type": "string"},
}, ["exceptionType", "raisedOn", "raisedBy", "raisedAt", "description"])

schemas["recordEvent"] = concept("RecordEvent", "Record Event", "An append-only entry for each creation or change of a record.", {
    "subject": REF,
    "actor": REF,
    "at": TS,
    "change": {
        "type": "object",
        "properties": {
            "kind": {"enum": ["created", "status_changed", "amended"]},
            "field": {"type": "string"},
            "from": {},
            "to": {},
        },
        "required": ["kind"],
        "additionalProperties": False,
        "allOf": [{"if": {"properties": {"kind": {"const": "status_changed"}}},
                   "then": {"required": ["field", "from", "to"],
                            "properties": {"field": {"type": "string"},
                                           "from": {"type": "string"},
                                           "to": {"type": "string"}}}}],
    },
    "prior": {"oneOf": [REF, {"type": "null"}]},
}, ["subject", "actor", "at", "change", "prior"])

names = list(schemas)
recordset = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": BASE + "recordset.schema.json",
    "title": "PRUDENCE v0.1 record set",
    "description": "A set of PRUDENCE records validated together.",
    "type": "object",
    "properties": {
        "prudence": {"const": "0.1"},
        "description": {"type": "string"},
        "records": {"type": "array", "minItems": 1, "items": {"oneOf": [
            {"$ref": f"{n}.schema.json"} for n in names]}},
    },
    "required": ["prudence", "records"],
    "additionalProperties": False,
}

os.makedirs(OUT, exist_ok=True)
for fname, doc in [("common", common), ("recordset", recordset)] + list(schemas.items()):
    with open(os.path.join(OUT, f"{fname}.schema.json"), "w") as f:
        doc["$comment"] = 'PRUDENCE™: architecture and development by Signal Private Markets Infrastructure, Inc. Signal owns its original PRUDENCE material and directs the project. Outside contributions remain owned by their respective copyright holders unless separately agreed.'
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
print("wrote", len(schemas) + 2, "schemas")
