# Extending PRUDENCE

Domains attach their own requirements without changing the core. A healthcare formulary, a public procurement office, or an investment committee each needs fields the core does not define.

## How an extension attaches

Every record may carry an `extensions` object. Its keys are the extension's namespace URI; its values hold that extension's fields:

```json
{
  "id": "DEC-AWARD-014",
  "type": "Decision",
  "...": "core fields",
  "extensions": {
    "https://example.org/prudence-ext/public-procurement/v1": {
      "solicitationNumber": "RFB-2027-014",
      "procurementMethod": "competitive_sealed_bid",
      "bidsReceived": 3,
      "awardedAmount": {"value": 412000, "currency": "USD"}
    }
  }
}
```

The full example is `examples/extension/procurement-award-extended.json`. It is the human-approved example with these fields added to its Decision and Action.

## Rules for extensions

1. **Use a namespace you control.** The key must be an `http` or `https` URI. Version it in the path.
2. **Add; do not redefine.** An extension may add fields. It may not change the meaning of a core field or relax a record rule.
3. **Validate your own fields.** The core validator checks only that each extension value is an object. Publish a JSON Schema for your fields and validate them yourself.
4. **Core validity comes first.** A record set must pass the core validator with its extensions present.

## Validating extension fields

`examples/extension/public-procurement.schema.json` defines the synthetic extension. To check it:

```sh
python - <<'EOF'
import json
from jsonschema import Draft202012Validator
ns = "https://example.org/prudence-ext/public-procurement/v1"
schema = json.load(open("examples/extension/public-procurement.schema.json"))
records = json.load(open("examples/extension/procurement-award-extended.json"))["records"]
for r in records:
    if ns in r.get("extensions", {}):
        part = schema["$defs"][r["type"].lower()]
        Draft202012Validator(part).validate(r["extensions"][ns])
        print("extension fields valid:", r["id"])
EOF
```

Expected output:

```
extension fields valid: DEC-AWARD-014
extension fields valid: ACT-EXECUTE-014
```

The extension shown is synthetic and illustrative. It is not a published PRUDENCE extension.
