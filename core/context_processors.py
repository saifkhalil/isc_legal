import json
from accounts.models import User
from django.core.cache import cache


def users_json_context(request):
    users_list = cache.get('users')

    if not users_list:
        users_list = User.objects.filter(is_active=True)
        cache.set('users', users_list, 60 * 5)  # Cache for 5 minutes
    return {
        'mention_users':users_list
    }
