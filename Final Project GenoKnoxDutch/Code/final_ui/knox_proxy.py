# knox_proxy.py

import urllib.request
import urllib.error
from config import KNOX_URL

def proxy_request(method, path, body=None, headers=None):
    url = KNOX_URL + path

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers or {},
        method=method
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read(), resp.status, dict(resp.headers)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print("Knox returned error:")
        print(error_body)

        return error_body, e.code, dict(e.headers)