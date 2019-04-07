from django.core.cache import caches
from rest_framework.authentication import BaseAuthentication

from .models import ShangmiUser

user_cache = caches['user']

class LoginAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.data.get("token")
        if not token:
            token = request.query_params.get("token")
        user_id = user_cache.get(token)
        if user_id:
            user = ShangmiUser.objects.get(pk=user_id)
            return (user, token)
        else:
            return None, None