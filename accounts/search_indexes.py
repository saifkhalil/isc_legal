# from haystack import indexes
# from .models import Employees
#
# class EmployeesIndex(indexes.SearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=True)
#     full_name = indexes.CharField(model_attr='full_name')
#     email = indexes.CharField(model_attr='email')
#     suggestions = indexes.FacetCharField()
#
#     def get_model(self):
#         return Employees
#
#     def index_queryset(self, using=None):
#         return self.get_model().objects.all()
#
#     def prepare(self, obj):
#         prepared_data = super().prepare(obj)
#         prepared_data['suggestions'] = prepared_data['text']
#         return prepared_data
#
#     class Meta:
#         index = 'employees'
#         settings = {
#             'number_of_shards': 1,
#             'number_of_replicas': 0,
#         }