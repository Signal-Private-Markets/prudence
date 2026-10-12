"""Build the PRUDENCE v0.1 example record sets (synthetic data)."""
import copy, hashlib, json, sys
from pathlib import Path

OUT = Path(sys.argv[1])
EXT_NS = "https://example.org/prudence-ext/public-procurement/v1"


def h(text):
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


class Builder:
    def __init__(self):
        self.records, self.events, self.last = [], [], {}

    def add(self, record, at, by):
        self.records.append(record)
        self._event(record["id"], by, at, {"kind": "created"})
        return record

    def status(self, rid, by, at, frm, to):
        self._event(rid, by, at, {"kind": "status_changed", "field": "status", "from": frm, "to": to})

    def _event(self, subject, actor, at, change):
        n = sum(1 for e in self.events if e["subject"] == subject) + 1
        eid = f"EVT-{subject}-{n:02d}"
        self.events.append({"id": eid, "type": "RecordEvent", "subject": subject, "actor": actor,
                            "at": at, "change": change, "prior": self.last.get(subject)})
        self.last[subject] = eid

    def doc(self, description):
        return {"prudence": "0.1", "description": description, "records": self.records + self.events}


def actor(rid, kind, name, role, version=None):
    a = {"id": rid, "type": "Actor", "actorKind": kind, "name": name, "role": role}
    if version:
        a["systemVersion"] = version
    return a


# ---------------------------------------------------------------- human-approved
def human_approved():
    b = Builder()
    t0 = "2026-07-01T09:00:00Z"
    officer = "ACT-officer"
    b.add(actor("ACT-council", "organization", "Riverton City Council", "Governing body"), t0, "ACT-council")
    b.add(actor("ACT-committee", "organization", "Riverton Procurement Committee", "Award authority"), t0, "ACT-council")
    b.add(actor("ACT-chair", "human", "Dana Reyes", "Procurement Committee chair"), t0, "ACT-council")
    b.add(actor("ACT-member-1", "human", "Malik Chen", "Procurement Committee member"), t0, "ACT-council")
    b.add(actor("ACT-member-2", "human", "Priya Nair", "Procurement Committee member"), t0, "ACT-council")
    b.add(actor(officer, "human", "Owen Hart", "Procurement officer"), t0, "ACT-council")
    b.add(actor("ACT-clerk", "human", "Ruth Alvarez", "City clerk"), t0, "ACT-council")

    b.add({"id": "MAN-PW-PROC", "type": "Mandate", "name": "Public Works procurement",
           "purpose": "Obtain goods, services, and construction for the Public Works Department at the best value to the public, through fair and open competition.",
           "constraints": ["Competitive sealed bidding is required above $50,000.",
                           "Award goes to the lowest responsive and responsible bidder.",
                           "Construction bids must include a bid bond of 5% of the bid amount."],
           "scope": "Public Works Department, fiscal year 2027",
           "governingInstrument": "Riverton Procurement Ordinance, section 4 (synthetic)",
           "version": 1}, t0, "ACT-council")

    b.add({"id": "AUTH-COMMITTEE-AWARD-v1", "type": "Authorization", "authorizationId": "AUTH-COMMITTEE-AWARD",
           "version": 1, "grantor": "ACT-council", "grantee": "ACT-committee", "mandate": "MAN-PW-PROC",
           "scope": "Award construction contracts under the Public Works procurement mandate.",
           "limits": ["Contract value up to $500,000.", "Award requires the recorded approval of at least two committee members."],
           "humanApprovalRequired": True, "validFrom": "2026-07-01T00:00:00Z", "validTo": "2027-06-30T23:59:59Z"},
          t0, "ACT-council")
    b.add({"id": "AUTH-OFFICER-EXECUTE-v1", "type": "Authorization", "authorizationId": "AUTH-OFFICER-EXECUTE",
           "version": 1, "grantor": "ACT-council", "grantee": officer, "mandate": "MAN-PW-PROC",
           "scope": "Execute contracts the Procurement Committee has awarded.",
           "limits": ["Only contracts with a recorded award decision.", "No change to the awarded price or scope."],
           "humanApprovalRequired": False, "validFrom": "2026-07-01T00:00:00Z", "validTo": "2027-06-30T23:59:59Z"},
          t0, "ACT-council")

    ev = [("EV-BID-TAB", "Bid tabulation for Elm Street resurfacing, solicitation RFB-2027-014: Bidder A $389,500; Bidder B $412,000; Bidder C $447,800.",
           "records://riverton/rfb-2027-014/bid-tabulation.pdf", "2026-09-15T15:10:00Z"),
          ("EV-BOND-CHECK", "Bid bond verification: Bidders B and C submitted 5% bid bonds; Bidder A submitted none.",
           "records://riverton/rfb-2027-014/bond-verification.pdf", "2026-09-16T11:30:00Z"),
          ("EV-RESPONSIBILITY", "Responsibility review of Bidder B: state contractor license active, three references confirmed.",
           "records://riverton/rfb-2027-014/responsibility-review.pdf", "2026-09-18T14:00:00Z")]
    for rid, desc, ref, at in ev:
        b.add({"id": rid, "type": "Evidence", "description": desc, "source": "Riverton procurement records",
               "capturedAt": at, "capturedBy": officer, "contentRef": ref, "contentHash": h(rid)}, at, officer)

    dec = "DEC-AWARD-014"
    b.add({"id": dec, "type": "Decision", "mandate": "MAN-PW-PROC",
           "summary": "Award the Elm Street resurfacing contract (RFB-2027-014) to Bidder B for $412,000.",
           "decidedBy": ["ACT-committee"], "authorization": "AUTH-COMMITTEE-AWARD-v1", "authorizationVersion": 1,
           "status": "approved",
           "approval": {"status": "approved", "approvedBy": ["ACT-chair", "ACT-member-1", "ACT-member-2"]},
           "decidedAt": "2026-09-22T18:30:00Z", "effectiveAt": "2026-09-23T00:00:00Z",
           "knowledgeAsOf": "2026-09-22T17:00:00Z",
           "alternatives": [{"description": "Award to Bidder A at $389,500", "chosen": False},
                            {"description": "Award to Bidder B at $412,000", "chosen": True},
                            {"description": "Award to Bidder C at $447,800", "chosen": False},
                            {"description": "Reject all bids and re-bid", "chosen": False}],
           "evidence": ["EV-BID-TAB", "EV-BOND-CHECK", "EV-RESPONSIBILITY"]},
          "2026-09-19T10:00:00Z", officer)
    b.status(dec, "ACT-chair", "2026-09-22T18:30:00Z", "proposed", "approved")

    b.add({"id": "JUS-AWARD-014", "type": "Justification", "about": dec, "statedBy": "ACT-chair",
           "statedAt": "2026-09-22T18:30:00Z",
           "statement": "Bidder B is the lowest responsive and responsible bidder. Bidder A offered the lowest price but submitted no bid bond, so its bid is non-responsive under the mandate's constraints.",
           "citesEvidence": ["EV-BID-TAB", "EV-BOND-CHECK", "EV-RESPONSIBILITY"],
           "alternativesRejected": [
               {"alternative": "Award to Bidder A", "reason": "Non-responsive: required bid bond missing."},
               {"alternative": "Award to Bidder C", "reason": "Higher price than a responsive, responsible bid."},
               {"alternative": "Reject all bids and re-bid", "reason": "A responsive bid within budget was received."}]},
          "2026-09-22T18:30:00Z", "ACT-chair")

    act = "ACT-EXECUTE-014"
    b.add({"id": act, "type": "Action", "decision": dec, "performer": officer, "mode": "human",
           "authorization": "AUTH-OFFICER-EXECUTE-v1", "authorizationVersion": 1,
           "description": "Execute construction contract C-2027-031 with Bidder B.",
           "status": "completed",
           "attempts": [{"attemptId": "A1", "startedAt": "2026-09-29T14:00:00Z", "status": "completed"}]},
          "2026-09-23T09:00:00Z", officer)
    b.status(act, officer, "2026-09-23T09:05:00Z", "proposed", "authorized")
    b.status(act, officer, "2026-09-29T14:00:00Z", "authorized", "attempted")
    b.status(act, officer, "2026-09-29T16:00:00Z", "attempted", "completed")

    b.add({"id": "EV-CONTRACT", "type": "Evidence",
           "description": "Executed contract C-2027-031, signed by Bidder B and the procurement officer.",
           "source": "Office of the City Clerk", "capturedAt": "2026-09-29T16:20:00Z", "capturedBy": "ACT-clerk",
           "contentRef": "records://riverton/contracts/C-2027-031.pdf", "contentHash": h("EV-CONTRACT")},
          "2026-09-29T16:20:00Z", "ACT-clerk")
    b.add({"id": "RES-EXECUTE-014-A1", "type": "Result", "action": act, "attemptId": "A1",
           "observedBy": "ACT-clerk", "observedAt": "2026-09-29T16:20:00Z",
           "outcome": "Contract C-2027-031 executed by both parties and filed with the City Clerk.",
           "evidence": ["EV-CONTRACT"]},
          "2026-09-29T16:20:00Z", "ACT-clerk")

    return b.doc("Synthetic example: a procurement committee awards a construction contract; "
                 "a procurement officer executes it. Human approval required. All names and figures are fictional.")


# ---------------------------------------------------------------- automated
def automated():
    b = Builder()
    t0 = "2026-01-02T09:00:00Z"
    svc, gw, fd = "ACT-ap-service", "ACT-payment-gateway", "ACT-finance-director"
    b.add(actor(fd, "human", "Lena Ortiz", "Finance director"), t0, fd)
    b.add(actor(svc, "system", "Riverton accounts payable matching service", "Invoice matching and payment release", "3.2.0"), t0, fd)
    b.add(actor(gw, "system", "Riverton payment gateway", "Bank payment submission and confirmation", "1.8.4"), t0, fd)

    b.add({"id": "MAN-AP", "type": "Mandate", "name": "Accounts payable",
           "purpose": "Pay the City's valid obligations accurately and on time.",
           "constraints": ["Pay only invoices matched to a purchase order and a receiving record.",
                           "Hold any invoice outside matching tolerance for human review."],
           "scope": "All City departments",
           "governingInstrument": "Riverton Finance Policy FP-12 (synthetic)", "version": 1}, t0, fd)

    b.add({"id": "AUTH-AP-RELEASE-v1", "type": "Authorization", "authorizationId": "AUTH-AP-RELEASE",
           "version": 1, "grantor": fd, "grantee": svc, "mandate": "MAN-AP",
           "scope": "Release payment on matched invoices without individual human approval.",
           "limits": ["Invoice amount up to $10,000.", "Three-way match within 2% price tolerance and exact quantity.",
                      "Vendor on the approved vendor list."],
           "humanApprovalRequired": False, "validFrom": "2026-01-01T00:00:00Z", "validTo": "2026-07-31T23:59:59Z"},
          t0, fd)
    b.add({"id": "AUTH-AP-RELEASE-v2", "type": "Authorization", "authorizationId": "AUTH-AP-RELEASE",
           "version": 2, "grantor": fd, "grantee": svc, "mandate": "MAN-AP",
           "scope": "Release payment on matched invoices without individual human approval.",
           "limits": ["Invoice amount up to $25,000.", "Three-way match within 2% price tolerance and exact quantity.",
                      "Vendor on the approved vendor list."],
           "humanApprovalRequired": False, "validFrom": "2026-08-01T00:00:00Z", "validTo": "2027-07-31T23:59:59Z",
           "supersedes": "AUTH-AP-RELEASE-v1"}, "2026-07-28T10:00:00Z", fd)

    ev = [("EV-PO", "Purchase order PO-2027-0877: 900 tons asphalt binder at $20.50 per ton, $18,450.00.",
           "Riverton purchasing records", "records://riverton/po/PO-2027-0877.json", "2026-09-04T12:00:00Z", svc, None),
          ("EV-RECEIPT", "Receiving record RR-5521: 900 tons asphalt binder received at Public Works yard.",
           "Riverton receiving records", "records://riverton/receiving/RR-5521.json", "2026-09-30T08:15:00Z", svc, None),
          ("EV-INVOICE", "Invoice INV-8841 from Northgate Asphalt Supply: 900 tons at $20.50, $18,450.00.",
           "Vendor invoice intake", "records://riverton/invoices/INV-8841.pdf", "2026-10-01T09:40:00Z", svc, None),
          ("EV-MATCH", "Three-way match output for INV-8841: price variance 0.0%, quantity variance 0, vendor approved.",
           "Accounts payable matching service output", "records://riverton/ap/match/INV-8841.json",
           "2026-10-02T12:58:00Z", svc, svc)]
    for rid, desc, source, ref, at, by, src_actor in ev:
        rec = {"id": rid, "type": "Evidence", "description": desc, "source": source,
               "capturedAt": at, "capturedBy": by, "contentRef": ref, "contentHash": h(rid)}
        if src_actor:
            rec["sourceActor"] = src_actor
        b.add(rec, at, by)

    dec = "DEC-PAY-8841"
    b.add({"id": dec, "type": "Decision", "mandate": "MAN-AP",
           "summary": "Release payment of $18,450.00 on invoice INV-8841 from Northgate Asphalt Supply.",
           "decidedBy": [svc], "authorization": "AUTH-AP-RELEASE-v2", "authorizationVersion": 2,
           "status": "approved", "approval": {"status": "not_required_standing_authority"},
           "decidedAt": "2026-10-02T12:59:00Z", "effectiveAt": "2026-10-02T12:59:00Z",
           "knowledgeAsOf": "2026-10-02T12:58:00Z",
           "alternatives": [{"description": "Release payment", "chosen": True},
                            {"description": "Hold for human review", "chosen": False}],
           "evidence": ["EV-PO", "EV-RECEIPT", "EV-INVOICE", "EV-MATCH"]},
          "2026-10-02T12:58:30Z", svc)
    b.status(dec, svc, "2026-10-02T12:59:00Z", "proposed", "approved")

    b.add({"id": "JUS-PAY-8841", "type": "Justification", "about": dec, "statedBy": svc,
           "statedAt": "2026-10-02T12:59:00Z",
           "statement": "INV-8841 matches PO-2027-0877 and RR-5521 within tolerance (price variance 0.0%, quantities equal). The amount is within the $25,000 limit of AUTH-AP-RELEASE version 2.",
           "citesEvidence": ["EV-MATCH", "EV-PO", "EV-RECEIPT", "EV-INVOICE"],
           "alternativesRejected": [{"alternative": "Hold for human review",
                                     "reason": "No tolerance breach or vendor flag was found."}]},
          "2026-10-02T12:59:00Z", svc)

    act = "ACT-PAY-8841"
    b.add({"id": act, "type": "Action", "decision": dec, "performer": svc, "mode": "automated",
           "authorization": "AUTH-AP-RELEASE-v2", "authorizationVersion": 2,
           "description": "Submit payment of $18,450.00 to Northgate Asphalt Supply through the payment gateway.",
           "status": "completed",
           "attempts": [{"attemptId": "A1", "startedAt": "2026-10-02T13:00:00Z", "status": "failed"},
                        {"attemptId": "A2", "startedAt": "2026-10-02T13:45:00Z", "status": "completed"}]},
          "2026-10-02T12:59:30Z", svc)
    b.status(act, svc, "2026-10-02T12:59:40Z", "proposed", "authorized")
    b.status(act, svc, "2026-10-02T13:00:00Z", "authorized", "attempted")
    b.status(act, svc, "2026-10-02T13:02:00Z", "attempted", "failed")
    b.status(act, svc, "2026-10-02T13:45:00Z", "failed", "attempted")
    b.status(act, svc, "2026-10-02T13:47:00Z", "attempted", "completed")

    b.add({"id": "RES-PAY-8841-A1", "type": "Result", "action": act, "attemptId": "A1", "observedBy": gw,
           "observedAt": "2026-10-02T13:02:00Z",
           "outcome": "Payment file rejected: the bank endpoint timed out before acknowledgment. No funds moved."},
          "2026-10-02T13:02:00Z", gw)
    b.add({"id": "EXC-PAY-8841-A1", "type": "Exception", "exceptionType": "execution_failure", "raisedOn": act,
           "attemptId": "A1", "raisedBy": svc, "raisedAt": "2026-10-02T13:02:10Z",
           "description": "Attempt A1 failed: bank endpoint timeout.",
           "resolution": "Retried after 43 minutes under the same authorization version; attempt A2 settled."},
          "2026-10-02T13:02:10Z", svc)
    b.add({"id": "RES-PAY-8841-A2", "type": "Result", "action": act, "attemptId": "A2", "observedBy": gw,
           "observedAt": "2026-10-02T13:47:00Z",
           "outcome": "Payment of $18,450.00 settled; bank reference 7Q2-118844."},
          "2026-10-02T13:47:00Z", gw)

    return b.doc("Synthetic example: an accounts payable system releases a matched invoice payment under standing "
                 "authority, with no individual human approval. The first attempt fails and is retried. "
                 "All names and figures are fictional.")


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


ha = human_approved()
au = automated()
write(OUT / "human-approved" / "procurement-award.json", ha)
write(OUT / "automated" / "payment-release.json", au)

# Invalid: the payment action cites version 1 of a version-2 authorization record.
bad = copy.deepcopy(au)
bad["description"] = ("Deliberately invalid copy of automated/payment-release.json. ACT-PAY-8841 cites "
                      "authorizationVersion 1 while referencing the version-2 authorization record.")
for r in bad["records"]:
    if r["id"] == "ACT-PAY-8841":
        r["authorizationVersion"] = 1
write(OUT / "invalid" / "wrong-authorization-version.json", bad)

# Extension: the human-approved example with public-procurement fields attached.
ext = copy.deepcopy(ha)
ext["description"] = ("The human-approved example with a synthetic public-procurement extension attached to the "
                      "Decision and Action records. See extending.md.")
for r in ext["records"]:
    if r["id"] == "DEC-AWARD-014":
        r["extensions"] = {EXT_NS: {"solicitationNumber": "RFB-2027-014",
                                    "procurementMethod": "competitive_sealed_bid",
                                    "bidsReceived": 3, "awardedAmount": {"value": 412000, "currency": "USD"}}}
    if r["id"] == "ACT-EXECUTE-014":
        r["extensions"] = {EXT_NS: {"contractNumber": "C-2027-031"}}
write(OUT / "extension" / "procurement-award-extended.json", ext)
print("examples written")
