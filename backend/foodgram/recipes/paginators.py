from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    # page_size = 3
    page_size_query_param = 'limit'
