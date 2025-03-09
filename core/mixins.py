from rest_framework import renderers

from core.renderers import LegalCSVRenderer, StreamingCSVRenderer


class CSVRendererMixin:
    def get_renderers(self):
        print('start CSVRendererMixin')
        renderers = super().get_renderers()

        if 'format' in self.request.query_params and self.request.query_params['format'] == 'csv':
            queryset = self.filter_queryset(self.get_queryset())
            if queryset.exists():
                # Get the model fields from the queryset
                fields = queryset.model._meta.get_fields()
                header = [field.name for field in fields if not field.is_relation]
                csv_renderer = LegalCSVRenderer(header=header)
                renderers = [csv_renderer] + renderers

        return renderers

    def paginate_queryset(self, queryset):
        if 'format' in self.request.query_params and self.request.query_params['format'] == 'csv':
            return None
        return super().paginate_queryset(queryset)


class CSVRendererMixin2:
    def get_renderers(self):
        print('start CSVRendererMixin2 - get_renderers')
        renderers = super().get_renderers()

        if 'format' in self.request.query_params and self.request.query_params['format'] == 'csv':
            queryset = self.filter_queryset(self.get_queryset())
            if queryset.exists():
                print('start CSVRendererMixin2 - get_renderers - if queryset.exists()')
                csv_renderer = StreamingCSVRenderer()
                print('end CSVRendererMixin2 - get_renderers - if queryset.exists()')
                renderers = [csv_renderer] + renderers
        print('end CSVRendererMixin2 - get_renderers')
        return renderers

    def get_queryset(self):
        print('start CSVRendererMixin2 - get_queryset')
        queryset = super().get_queryset()
        if 'format' in self.request.query_params and self.request.query_params['format'] == 'csv':
            queryset = queryset.all()
        print('end CSVRendererMixin2 - get_queryset')
        return queryset

    def paginate_queryset(self, queryset):
        print('start CSVRendererMixin2 - paginate_queryset')
        if 'format' in self.request.query_params and self.request.query_params['format'] == 'csv':
            print('end CSVRendererMixin2 - paginate_queryset')
            return None
        print('end CSVRendererMixin2 - paginate_queryset')
        print('start CSVRendererMixin2 - response')
        response = super().paginate_queryset(queryset)
        print('end CSVRendererMixin2 - response')
        return response