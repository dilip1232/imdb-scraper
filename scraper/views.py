from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Movie
from .serializers import MovieSerializer
from rest_framework.pagination import PageNumberPagination

class CustomPageSizePagination(PageNumberPagination):
    page_size = 10  # default
    page_size_query_param = 'per_page'
    max_page_size = 100

class MovieListAPIView(ListAPIView):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all().order_by('-id')
    pagination_class = CustomPageSizePagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'directors', 'cast', 'plot', 'year']
    filterset_fields = ['year', 'rating']
    ordering_fields = ['title', 'year', 'rating', 'created']
    ordering = ['-id']
