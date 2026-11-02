"""python -m unittest: both backends against a local stub, through a real MCP client."""
import asyncio
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from mcp import Client

import national_id_mcp

SEEN = []


class Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        SEEN.append((self.path, self.headers, body))
        if self.path.startswith('/rapidapi'):
            out = [{'valid': None, 'matches': [{'type': 'est_personal_id'}]} for _ in body['values']]
        else:
            out = [{'value': v, 'type': 'est_personal_id'} for v in body['values']]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(out).encode())

    def log_message(self, *args):
        pass


def call(env, **arguments):
    async def run():
        async with Client(national_id_mcp.server) as client:
            return await client.call_tool('validate_ids', arguments)
    with mock.patch.dict(os.environ, env, clear=True):
        return asyncio.run(run())


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        httpd = HTTPServer(('127.0.0.1', 0), Stub)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{httpd.server_port}'
        cls.patches = [mock.patch.object(national_id_mcp, 'RAPIDAPI_URL', url + '/rapidapi'),
                       mock.patch.object(national_id_mcp, 'APIFY_URL', url + '/apify?memory=256')]
        for p in cls.patches:
            p.start()

    @classmethod
    def tearDownClass(cls):
        for p in cls.patches:
            p.stop()

    def setUp(self):
        SEEN.clear()

    def test_rapidapi_batches_by_100(self):
        r = call({'RAPIDAPI_KEY': 'k'}, values=[str(i) for i in range(150)], country='EST')
        self.assertFalse(r.is_error)
        out = r.structured_content['result']
        self.assertEqual((len(out), out[149]['value']), (150, '149'))
        self.assertEqual([len(body['values']) for *_, body in SEEN], [100, 50])
        path, headers, body = SEEN[0]
        self.assertEqual((headers['X-RapidAPI-Key'], body['country']), ('k', 'EST'))
        self.assertNotIn('type', body)

    def test_apify(self):
        r = call({'APIFY_TOKEN': 't'}, values=['37605030299'], type='est_personal_id')
        self.assertEqual(r.structured_content['result'], [{'value': '37605030299', 'type': 'est_personal_id'}])
        path, headers, body = SEEN[0]
        self.assertEqual((path, headers['Authorization']), ('/apify?memory=256', 'Bearer t'))
        self.assertEqual(body, {'values': ['37605030299'], 'type': 'est_personal_id'})

    def test_no_key(self):
        r = call({}, values=['1'])
        self.assertTrue(r.is_error)
        self.assertIn('RAPIDAPI_KEY', r.content[0].text)


if __name__ == '__main__':
    unittest.main()
