from rest_framework.pagination import BasePagination


class SubscribersPagination(BasePagination):

    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)
