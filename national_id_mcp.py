"""MCP server for the National ID & Tax ID Validator: validate and decode national IDs, tax IDs and passport MRZ.

Calls the API through RapidAPI (RAPIDAPI_KEY) or through the Apify Actor (APIFY_TOKEN), whichever key is set.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

RAPIDAPI_URL = 'https://national-id-tax-id-validator.p.rapidapi.com/v1/parse/batch'
APIFY_URL = 'https://api.apify.com/v2/acts/soxoj~national-id-tax-id-validator/run-sync-get-dataset-items?memory=256'
BATCH = 100  # values per RapidAPI request

server = MCPServer('national-id', instructions=(
    'Validates national ID numbers, tax IDs, company registration numbers, VAT numbers and passport MRZ of 108 '
    'countries and territories offline, and decodes what the number itself encodes: date of birth, sex, region or '
    'place of birth, citizenship. It does not query any government registry: valid means correctly built, not that '
    'the document exists or belongs to a particular person.'))


def post(url, payload, headers):
    request = urllib.request.Request(url, json.dumps(payload).encode(),
                                     {'Content-Type': 'application/json', **headers})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:  # the API's message (a 422 says what is wrong) goes to the model
        raise ToolError(f'HTTP {e.code}: {e.read().decode(errors="replace")[:500]}') from None


@server.tool()
def validate_ids(values: list[str], country: Optional[str] = None, type: Optional[str] = None) -> list[dict]:
    """Validate and decode ID numbers: national IDs, tax IDs, company and VAT numbers, passport numbers or MRZ.

    Every ID type a value fits is returned, checksum-verified ones first, with the number's formatted layout and the
    fields it encodes (birth date, sex, region...). Without a hint, valid is null: one string can be a valid number in
    several countries. With country (ISO alpha-3, e.g. "POL") or an exact type (e.g. "pol_pesel", from an earlier
    result) only those types are tried and valid is true or false (null where the country's IDs have no checksum).
    Offline validation only: valid means correctly built, not that the document exists.
    """
    hints = {k: v for k, v in (('country', country), ('type', type)) if v}
    if key := os.environ.get('RAPIDAPI_KEY'):
        headers = {'X-RapidAPI-Key': key, 'X-RapidAPI-Host': urllib.parse.urlsplit(RAPIDAPI_URL).netloc}
        results = []
        for i in range(0, len(values), BATCH):
            results += post(RAPIDAPI_URL, {'values': values[i:i + BATCH], **hints}, headers)
        return [{'value': v, **r} for v, r in zip(values, results)]
    if token := os.environ.get('APIFY_TOKEN'):  # one row per matched type
        return post(APIFY_URL, {'values': values, **hints}, {'Authorization': f'Bearer {token}'})
    raise ToolError('Set RAPIDAPI_KEY (https://rapidapi.com/soxoj/api/national-id-tax-id-validator) or APIFY_TOKEN '
                    '(https://console.apify.com/settings/integrations) in the MCP server environment')


def main():
    server.run()


if __name__ == '__main__':
    main()
