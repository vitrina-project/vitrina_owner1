import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

User = get_user_model()
logger = logging.getLogger()


class BaseAPIResponseMiddleware:
    def get_response_data(self, status_code):
        return {
            'status': status_code,
            'success': False,
            'errors': '',
            'message': '',
            'data': ''
        }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.META.get('HTTP_REFERER', '').endswith('/api/docs/'):
            return response
        if (settings.BASE_DIR.parent / 'infra' / 'local' / '.env').exists():
            return response
        if '/api/v1' not in request.path:
            return response

        response_data = self.get_response_data(status_code=response.status_code)

        if response.status_code > 405:
            response_data['errors'] = response.content.decode('utf-8')
            if response.status_code != 500:
                logger.error(str(response.content.decode('utf-8')))

        elif 400 <= response.status_code <= 405:
            logger.error(str(response.content.decode('utf-8')))
            if not hasattr(response, 'data'):
                response_data['errors'] = str(response.content.decode('utf-8'))

            elif isinstance(response.data, dict):
                for key, value in response.data.items():
                    if isinstance(value, list):
                        if isinstance(value[0], dict):
                            for item in value:
                                for v in item.values():
                                    response_data['errors'] += f'{". ".join(v)}. '
                        else:
                            response_data['errors'] += f'{". ".join(value)}. '

                    else:
                        response_data['errors'] += f' {value}. '
            else:
                response_data['errors'] = str(response.data)

        elif response.status_code >= 100:
            response_data['success'] = True
            response_data['data'] = response.data

        response = Response(response_data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        response.render()

        return response
