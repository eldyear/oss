# middleware.py
from django.conf import settings

class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем, если пользователь находится в админке
        if request.path.startswith('/admin/'):
            settings.SESSION_COOKIE_NAME = 'admin_sessionid'
            settings.CSRF_COOKIE_NAME = 'admin_csrftoken'
        else:
            settings.SESSION_COOKIE_NAME = 'user_sessionid'
            settings.CSRF_COOKIE_NAME = 'user_csrftoken'
        return self.get_response(request)
