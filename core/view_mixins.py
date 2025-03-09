


class ExtraContextViewMixin:
    """
    Mixin that allows views to pass extra context to the template much easier
    than overloading .get_context_data().
    """
    extra_context = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            self.get_extra_context()
        )
        return context

    def get_extra_context(self):
        return self.extra_context
