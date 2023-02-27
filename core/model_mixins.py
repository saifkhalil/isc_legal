class ExtraDataModelMixin:
    def __init__(self, *args, **kwargs):
        _instance_extra_data = kwargs.pop('_instance_extra_data', {})
        result = super().__init__(*args, **kwargs)
        for key, value in _instance_extra_data.items():
            setattr(self, key, value)

        return result


class HooksModelMixin:
    @classmethod
    def _execute_hooks(cls, hook_list, **kwargs):
        result = None

        for hook in hook_list:
            result = hook(**kwargs)
            if result:
                kwargs.update(result)

        return result

    @classmethod
    def _insert_hook_entry(cls, hook_list, func, order=None):
        order = order or len(hook_list)
        hook_list.insert(order, func)
