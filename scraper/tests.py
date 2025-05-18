from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from scraper.models import Movie, ScraperStatus
from scripts.management.commands.scraper import IMDBScraper


class MovieListAPITests(APITestCase):
    def setUp(self):
        Movie.objects.create(
            title="Inception",
            year=2010,
            rating=8.8,
            directors="Christopher Nolan",
            cast="Leonardo DiCaprio",
            plot="Dreams inside dreams."
        )
        Movie.objects.create(
            title="The Matrix",
            year=1999,
            rating=8.7,
            directors="The Wachowskis",
            cast="Keanu Reeves",
            plot="What is real?"
        )

    def test_movie_list_success(self):
        url = reverse('scraper-movie-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_movie_search_by_title(self):
        url = reverse('scraper-movie-list')
        response = self.client.get(url, {'search': 'Inception'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'Inception')

    def test_movie_search_by_director(self):
        url = reverse('scraper-movie-list')
        response = self.client.get(url, {'search': 'Nolan'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any("Nolan" in movie['directors'] for movie in response.data['results']))

    def test_movie_search_by_year(self):
        url = reverse('scraper-movie-list')
        response = self.client.get(url, {'search': '1999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(str(movie['year']) == "1999" for movie in response.data['results']))

    def test_pagination_custom_per_page(self):
        url = reverse('scraper-movie-list')
        response = self.client.get(url, {'per_page': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 1)


# ✅ Scraper Command Tests
class IMDBScraperTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.status = await ScraperStatus.objects.acreate(status='pending', total_movies=2)
        self.scraper = IMDBScraper(search_type='genre', search_value='comedy', limit=2, status=self.status)

    @patch('scripts.management.commands.scraper.IMDBScraper.fetch_movie_list_page', new_callable=AsyncMock)
    @patch('scripts.management.commands.scraper.IMDBScraper.scrape_details_concurrently', new_callable=AsyncMock)
    @patch('scripts.management.commands.scraper.IMDBScraper.update_status', new_callable=AsyncMock)
    async def test_run_success(self, mock_update_status, mock_scrape_concurrent, mock_fetch):
        mock_fetch.return_value = ['url1', 'url2']
        await self.scraper.run()
        mock_update_status.assert_called_with('completed', scraped_movies=2)

    @patch('scripts.management.commands.scraper.IMDBScraper.fetch_movie_list_page', new_callable=AsyncMock, side_effect=Exception("Fetch failed"))
    @patch('scripts.management.commands.scraper.IMDBScraper.update_status', new_callable=AsyncMock)
    async def test_run_fetch_failure(self, mock_update_status, mock_fetch):
        with self.assertRaises(Exception):
            await self.scraper.run()
        mock_update_status.assert_called_with('error', error_message='Fetch failed')
