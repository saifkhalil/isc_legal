from rest_framework_csv.renderers import CSVRenderer
import csv
from django.http import StreamingHttpResponse
from rest_framework.renderers import BaseRenderer


class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value
class LegalCSVRenderer(CSVRenderer):
    def __init__(self, header=None):
        self.header = header if header else []
        super().__init__()

    def flatten_data(self, data):
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        return [data]

    def render(self, data, accepted_media_type=None, renderer_context=None):
        print('start LegalCSVRenderer')
        if data is None:
            return ''

        data = self.flatten_data(data)
        # Set header dynamically if not provided
        if not self.header and data:
            self.header = list(data[0].keys())

        return super(LegalCSVRenderer, self).render(data, accepted_media_type, renderer_context)


class StreamingCSVRenderer(BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'
    charset = 'utf-8-sig'

    def render(self, data, media_type=None, renderer_context=None):
        print('start StreamingCSVRenderer - render')
        if data is None:
            data = []

        if not data:
            print('end StreamingCSVRenderer - render')
            return ''

        pseudo_buffer = Echo()
        writer = csv.DictWriter(pseudo_buffer, fieldnames=data[0].keys())

        def csv_generator():
            print('start StreamingCSVRenderer - csv_generator')
            # Add BOM
            yield '\ufeff'
            writer.writeheader()
            print('start StreamingCSVRenderer - csv_generator - start loop')
            for row in data:
                yield writer.writerow(row)

        response = StreamingHttpResponse(
            csv_generator(),
            content_type=self.media_type,
        )
        print('end StreamingCSVRenderer - render')
        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        return response