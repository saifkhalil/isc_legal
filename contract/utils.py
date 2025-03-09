from core.models import Duration

def get_duration(key, default=None):
    try:
        duration = Duration.objects.get(key=key)
        return Duration.no_of_days
    except Duration.DoesNotExist:
        return default

def set_setting(key, value):
    setting, created = Duration.objects.get_or_create(key=key)
    setting.no_of_days = value
    setting.save()
