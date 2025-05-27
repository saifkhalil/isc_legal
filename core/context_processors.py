import json
from accounts.models import User
from django.core.cache import cache


def users_json_context(request):
    users_list = cache.get('users_json_list')
    users = cache.get('users')

    if not users_list or not users:
        users = User.objects.filter(is_active=True)
        users_values = users.values('username', 'email','photo')
        users_list = [{'key': u['username'], 'value': u['email'] or u['username'], 'photo': u['photo']} for u in users_values]
        cache.set('users_json_list', users_list, 60 * 5)  # Cache for 5 minutes
        cache.set('users', users, 60 * 5)  # Cache for 5 minutes
    return {
        'users_json': json.dumps(users_list),
        'mention_users':users
    }
