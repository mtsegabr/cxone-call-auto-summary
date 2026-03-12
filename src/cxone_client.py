import json
import os
import time
import urllib.request
import urllib.parse

class CxoneClient:
    """
    CXone API helper for:
    - Access Token retrieval
    - GET contact details
    - GET playback metadata (fileToPlayUrl)
    - Listing completed contacts (requires your tenant's reporting endpoint)
    """

    def __init__(self, access_key_id, access_key_secret, base_url, auth_url):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.base_url = base_url.rstrip("/")
        self.auth_url = auth_url.rstrip("/")
        self._token = None
        self._token_exp = 0

    def _http(self, method, url, headers=None, data=None, timeout=30):
        req = urllib.request.Request(url, method=method, data=data)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            if not body:
                return {}
            return json.loads(body.decode("utf-8"))

    def _get_token(self):
        now = int(time.time())
        if self._token and now < self._token_exp - 60:
            return self._token

        payload = json.dumps({
            "accessKeyId": self.access_key_id,
            "accessKeySecret": self.access_key_secret
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        token_resp = self._http("POST", f"{self.auth_url}/token", headers, payload)

        self._token = token_resp["accessToken"]
        self._token_exp = now + int(token_resp.get("expiresIn", 3600))
        return self._token

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get_contact_details(self, acd_call_id):
        url = f"{self.base_url}/services/v22.0/contacts/{urllib.parse.quote(acd_call_id)}"
        return self._http("GET", url, self._auth_headers())

    def get_playback_metadata(self, acd_call_id):
        url = f"{self.base_url}/services/v22.0/recording/playback/{urllib.parse.quote(acd_call_id)}"
        return self._http("GET", url, self._auth_headers())

    def list_completed_contacts(self, start_iso, end_iso, page=1, page_size=200):
        url = (
            f"{self.base_url}/services/v22.0/reporting/contacts?"
            f"from={urllib.parse.quote(start_iso)}&to={urllib.parse.quote(end_iso)}"
            f"&page={page}&pageSize={page_size}"
        )
        return self._http("GET", url, self._auth_headers())