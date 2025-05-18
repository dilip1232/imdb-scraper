from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Movie
from .serializers import MovieSerializer

class MovieListAPIView(ListAPIView):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all().order_by('-id')

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'directors', 'cast', 'plot']
    filterset_fields = ['year', 'rating']
    ordering_fields = ['title', 'year', 'rating', 'created']
    ordering = ['-id']
    def get_paginate_by(self):
        return int(self.request.query_params.get('per_page', 10))
