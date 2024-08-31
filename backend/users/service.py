import logging
import random
import string

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError


def generate_random_code(length=4) -> int:
    return int(''.join(random.sample('123456789', length)))


def generate_random_string(length: int) -> str:
    return ''.join(random.sample(string.ascii_letters, length))


logger = logging.getLogger()


def validate_response(phone, response: dict) -> None:
    if response.get('error') is None:
        logger.info(f'Сообщение отправлено на номер {phone}')
        return

    error_code = response.get('error_code', 0)
    if error_code == 7:
        logger.error(f'Неверный формат номера телефона: {phone}')
        raise ValidationError({'error': 'Неверный формат номера телефона'})
    elif error_code == 8:
        logger.error(f'Сообщение на номер {phone} не может быть доставлено')
        raise ValidationError({'error': 'Сообщение на указанный номер не может быть доставлено'})
    else:
        logger.error(f'Ошибка отправки сообщения на номер {phone}, код ошибки {error_code}.'
                     f' Ссылка для просмотра кода ошибки: https://smsc.ru/api/')
        raise ValidationError({'error': 'Сервис временно не доступен'})


def send_sms_to_phone(phone: str) -> str:
    code = generate_random_code()
    data = {
        'login': settings.SMSC_LOGIN,
        'psw': settings.SMSC_PASSWORD,
        'phones': phone,
        'freq': 1,
        'mes': f'{code}',
        'fmt': 3,
        # 'sender': 'mirahelps' # зарегать на сайте
    }
    response = requests.post(API_URL, json=data)
    data = response.json()
    logger.info(f'Отправка смс на номер {phone}: {data}')
    validate_response(phone, data)
    return code
