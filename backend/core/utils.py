import random
import string

from curl_cffi import requests
from django.template.defaultfilters import slugify as django_slugify


def generate_random_code(length=4) -> int:
    return int(''.join(random.sample('123456789', length)))


alphabet = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
            'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
            'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ы': 'i', 'э': 'e', 'ю': 'yu',
            'я': 'ya'}


def slugify(s):
    return django_slugify(''.join(alphabet.get(w, w) for w in s.lower()))


def get_random_string(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


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
