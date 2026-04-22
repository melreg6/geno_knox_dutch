# knox_proxy.py
import urllib.request
from config import KNOX_URL

def proxy_request(method, path, body=None, headers=None):
    url = KNOX_URL + path

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers or {},
        method=method
    )

    with urllib.request.urlopen(req) as resp:
        return resp.read(), resp.status, dict(resp.headers)