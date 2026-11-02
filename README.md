# National ID & Tax ID Validator MCP

An MCP server that lets an AI agent validate and decode ID numbers: national IDs, tax IDs, company and VAT numbers,
passport numbers and passport MRZ.

- **222 ID types from 108 countries and territories.**
- For every value it returns each ID type the value fits, whether the checksum is right, the number in its usual
  printed layout, and what the number itself encodes: date of birth, sex, region or place of birth, citizenship,
  taxpayer type.
- The validation is offline: no government registry is queried. "Valid" means the number is correctly built, not that
  the document exists or belongs to a particular person.
- The server is a thin client for the National ID & Tax ID Validator API, available
  [on RapidAPI](https://rapidapi.com/soxoj/api/national-id-tax-id-validator) and
  [as an Apify Actor](https://apify.com/soxoj/national-id-tax-id-validator). Use whichever account you have.

## Quick start

No install: add Apify's hosted MCP server to your client and sign in to Apify on the first connection.

```
https://mcp.apify.com?tools=soxoj/national-id-tax-id-validator
```

## Examples

All three numbers are made up for this README. The tool returns JSON (see [The tool](#the-tool)); here the answers
are shown as tables.

**`5010100A000PB1`**: Belarusian personal number (`blr_personal_number`), checksum verified

| Field | Value |
|---|---|
| Date of birth | 2000-01-01 |
| Sex | male |
| Region | Minsk |
| Status | citizen |
| Serial number | 000 |

**`50001010006`** with `country="EST"`: Estonian personal code (`est_personal_id`), checksum verified

| Field | Value |
|---|---|
| Date of birth | 2000-01-01 |
| Sex | male |
| E-mail | 50001010006@eesti.ee (the official address every Estonian ID card holder gets) |
| Serial number | 000 |

Without `country` the same string also passes the checksums of a Hungarian and a Lithuanian personal number and fits
four more formats; all seven matches are returned, checksum-verified first, and `valid` is `null`.

**`EATA000101MDFXSNA6`**: Mexican CURP (`mex_curp`) of a fictional Ana Example Test, checksum verified

| Field | Value |
|---|---|
| Initials | EATA: **E**x**a**mple, **T**est, **A**na |
| Inner consonants | XSN: e**x**ample, te**s**t, a**n**a |
| Date of birth | 2000-01-01 |
| Sex | female |
| State of birth | DF (Mexico City) |
| Homoclave | A |

## Use cases

- **Investigations.** An ID number turns up in a leak, a court record or a scanned document. Find out which country
  and document it belongs to and what it says about its holder: birth date, sex, region, citizenship. Then compare
  that with what you already know about the person.
- **KYC and anti-fraud.** Reject mistyped and invented numbers at sign-up, and compare the birth date and sex encoded
  in the number with the ones the customer entered. A mismatch is a reason to look closer.
- **Pivots.** Some numbers lead to other identifiers, such as the `@eesti.ee` address of an Estonian, or the PAN
  embedded in an Indian GSTIN.
- **Data cleaning.** Sort a column of unlabeled numbers by country and document type, drop the broken ones and
  print the rest in their usual layout.
- **Document workflows.** After an OCR tool has read a passport or an ID card, check the extracted number, or the
  passport's MRZ check digits, before anything is done with it.

## Setup

You need [uv](https://docs.astral.sh/uv/) and one of the two keys.

**RapidAPI**: subscribe to the [API on RapidAPI](https://rapidapi.com/soxoj/api/national-id-tax-id-validator)
(there is a free plan) and copy your `X-RapidAPI-Key`.

**Apify**: take your API token from [Apify Console → Settings → API & Integrations](https://console.apify.com/settings/integrations).
Runs of the [Actor](https://apify.com/soxoj/national-id-tax-id-validator) are billed to your Apify account per checked ID.

### Claude Code

```
claude mcp add national-id -e RAPIDAPI_KEY=your-key -- uvx --from git+https://github.com/soxoj/national-id-mcp national-id-mcp
```

(or `-e APIFY_TOKEN=your-token`)

### Claude Desktop, Cursor and other clients

```json
{
  "mcpServers": {
    "national-id": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/soxoj/national-id-mcp", "national-id-mcp"],
      "env": {"RAPIDAPI_KEY": "your-key"}
    }
  }
}
```

If both keys are set, RapidAPI is used.

### No install: Apify's hosted MCP server

Apify serves any Store Actor as an MCP tool. Point your client at

```
https://mcp.apify.com?tools=soxoj/national-id-tax-id-validator
```

and sign in to Apify in the browser on the first connection, or send `Authorization: Bearer <APIFY_TOKEN>`. That way
the tool comes from Apify's generic Actor wrapper rather than from this server.

## The tool

`validate_ids(values, country=None, type=None)`

- `values`: a list of ID numbers, MRZ strings or tax numbers. Spaces and hyphens are fine.
- `country`: optional ISO 3166 alpha-3 code, e.g. `POL`. Only this country's types are tried, and `valid` becomes
  `true` or `false`. Without it `valid` is `null`, since one string can be a valid number in several countries.
- `type`: optional exact type, e.g. `pol_pesel`, taken from an earlier result.

Through RapidAPI the result is one object per value: `{"value", "valid", "matches": [{"type", "checksum_verified",
"formatted", "fields"}]}`, checksum-verified matches first. Through Apify it is one row per matched type, with the
same fields.

## What it does not do

- No registry lookups: it cannot tell whether a person exists, a passport is still valid or a tax number is active.
- About a third of the types have no public checksum; for those only the format is checked.
- MRZ: passports (TD3) only, not ID cards (TD1, TD2).
- No OCR: the input is text.

## Development

```
uv run --with mcp python -m unittest
```

## License

MIT
