import random
import string

from curl_cffi import requests


def generate_random_code(length=4) -> int:
    return int(''.join(random.sample('123456789', length)))


def generate_random_string(length: int) -> str:
    return ''.join(random.sample(string.ascii_letters, length))


def request(url, method='GET', **kwargs):
    headers = kwargs.pop('headers', {})
    headers[
        'User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    headers['Content-Type'] = 'application/json'

    return requests.request(
        method, url, **kwargs,
        # proxy_auth=('SUKu17', '2NH0Vx'),
        # proxy='https://SUKu17:2NH0Vx@147.45.89.28:8000',
        impersonate="chrome", headers=headers
    )
    # 'http': "https://SUKu17:2NH0Vx@147.45.89.28:8000",
