
from django.urls import path
from .views import MovieListAPIView


urlpatterns = [
    path('movies/', MovieListAPIView.as_view(), name='scraper-movie-list'),
]

