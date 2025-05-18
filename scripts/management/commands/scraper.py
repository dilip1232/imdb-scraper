
import asyncio
import logging
import re
import sys
import requests
import math
import uuid

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from playwright.async_api import async_playwright, TimeoutError, Error as PlaywrightError
from asgiref.sync import sync_to_async
from tqdm.asyncio import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper.models import ScraperStatus, Movie

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log', mode='a')
    ]
)

HEADERS = {'User-Agent': 'Mozilla/5.0'}
IMDB_PAGE_SIZE = 50
SEARCH_CHOICES = ['genre', 'keyword']
BATCH_SIZE = 2


class IMDBScraper:
    def __init__(self, search_type, search_value, limit, status):
        self.search_type = search_type
        self.search_value = search_value.strip().replace(" ", "-")
        self.limit = limit
        self.status = status
        self.movie_instances = []

    async def run(self):
        url = self.get_search_url()
        try:
            movie_links = await self.fetch_movie_list_page(url)
        except Exception as e:
            logger.exception("Failed to fetch movie list")
            await self.update_status('error', error_message=str(e))
            raise

        logger.info(f"Total movies found: {len(movie_links)}")
        await self.scrape_details_concurrently(movie_links)

        if not movie_links:
            await self.update_status('error', error_message="No movies found")
        else:
            await self.update_status('completed', scraped_movies=len(movie_links))

    def get_search_url(self):
        base = "https://www.imdb.com/search/title/"
        return f"{base}?{'genres' if self.search_type == 'genre' else 'keywords'}={self.search_value}"

    async def update_status(self, new_status, **fields):
        fields['status'] = new_status
        for key, value in fields.items():
            setattr(self.status, key, value)
        await sync_to_async(self.status.save)(update_fields=list(fields.keys()))

    async def fetch_movie_list_page(self, url):
        try:
            all_links = []
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_extra_http_headers(HEADERS)
                await page.goto(url)

                previous_height = 0
                max_iterations = 0 if self.limit < 50 else math.ceil(self.limit / 50)
                current_iteration = 0

                while True:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
                    current_height = await page.evaluate("document.body.scrollHeight")
                    if current_height == previous_height:
                        if current_iteration == max_iterations:
                            break
                        current_iteration += 1
                        try:
                            await page.click(".ipc-see-more__text", timeout=3000)
                        except TimeoutError:
                            logger.info("See more button not found or not clickable.")
                    previous_height = current_height

                html = await page.content()
                await browser.close()

            soup = BeautifulSoup(html, 'html.parser')
            movie_containers = soup.select('ul.ipc-metadata-list')
            current_link_count = 1
            for ul in movie_containers:
                lis = ul.find_all('li', recursive=False)
                for li in lis:
                    link_tag = li.find('a', class_='ipc-title-link-wrapper')
                    if link_tag and 'href' in link_tag.attrs:
                        all_links.append("https://www.imdb.com" + link_tag['href'])
                        if current_link_count == self.limit:
                            break
                        current_link_count += 1
            return all_links
        except (TimeoutError, PlaywrightError):
            logger.exception(f"Error while navigating to {url}")
            return []

    async def scrape_details_concurrently(self, movie_links):
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(self.scrape_movie_details, link): link for link in movie_links}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping progress"):
                try:
                    movie_data = future.result()
                except Exception as e:
                    logger.warning(f"Error scraping {futures[future]}: {e}")
                    continue

                if not movie_data:
                    continue

                self.movie_instances.append(Movie(
                    title=movie_data['title'],
                    year=movie_data['year'],
                    rating=float(movie_data['rating']) if movie_data['rating'] else None,
                    directors=movie_data['directors'],
                    cast=movie_data['cast'],
                    plot=movie_data['plot'],
                ))

                if len(self.movie_instances) >= BATCH_SIZE:
                    await self.bulk_insert_movies()
                    self.movie_instances.clear()

        if self.movie_instances:
            await self.bulk_insert_movies()

    async def bulk_insert_movies(self):
        titles = [m.title for m in self.movie_instances]
        existing_titles = set(await sync_to_async(
            lambda: list(Movie.objects.filter(title__in=titles).values_list('title', flat=True))
        )())

        to_update = [m for m in self.movie_instances if m.title in existing_titles]
        to_create = [m for m in self.movie_instances if m.title not in existing_titles]

        if to_create:
            await sync_to_async(Movie.objects.bulk_create)(to_create, ignore_conflicts=True)

        if to_update:
            existing_movies = await sync_to_async(
                lambda: {m.title: m for m in Movie.objects.filter(title__in=[m.title for m in to_update])}
            )()
            for m in to_update:
                db_obj = existing_movies[m.title]
                db_obj.year = m.year
                db_obj.rating = m.rating
                db_obj.directors = m.directors
                db_obj.cast = m.cast
                db_obj.plot = m.plot

            await sync_to_async(Movie.objects.bulk_update)(
                existing_movies.values(), ['year', 'rating', 'directors', 'cast', 'plot']
            )

    def scrape_movie_details(self, movie_url):
        try:
            logger.debug(f"Scraping movie details for: {movie_url}")
            response = requests.get(movie_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.find('h1', {'data-testid': 'hero__pageTitle'})
            title = title.get_text(strip=True) if title else None

            year_element = soup.find('ul', {'class': 'ipc-inline-list ipc-inline-list--show-dividers'})
            li_tags = year_element.find_all('li') if year_element else []
            release_year = next((re.search(r'\d{4}', tag.text.strip()).group() for tag in li_tags if re.search(r'\d{4}', tag.text.strip())), None)

            rating_el = soup.find('div', {'data-testid': 'hero-rating-bar__aggregate-rating__score'})
            imdb_rating = rating_el.find('span').get_text(strip=True) if rating_el else None

            director_el = soup.find('span', string=lambda s: s in ['Director', 'Directors'] if s else False)
            directors = None
            if director_el:
                principal_li = director_el.find_parent('li')
                if principal_li:
                    a_tags = principal_li.select('ul li a')
                    names = [a.get_text(strip=True) for a in a_tags]
                    directors = ", ".join(names) if names else None

            plot_el = soup.find('span', {'data-testid': 'plot-xl'})
            plot_summary = plot_el.get_text(strip=True) if plot_el else None

            cast = self.get_credits_details(soup, 'Stars')
            if not directors:
                for i in ['Creator', 'Creators']:
                    directors = self.get_credits_details(soup, i)
                    if directors:
                        break

            return {
                'title': title,
                'year': release_year,
                'rating': imdb_rating,
                'directors': directors,
                'cast': cast,
                'plot': plot_summary,
                'url': movie_url
            }
        except requests.RequestException:
            logger.exception(f"Failed to scrape movie: {movie_url}")
            return {}

    def get_credits_details(self, soup, key):
        credits_section = soup.find('a', {'aria-label': 'See full cast and crew'}, href=True, string=key)
        credits_list = []
        if credits_section:
            credits_ul = credits_section.find_next('ul')
            if credits_ul:
                credits_list = [a.text for a in credits_ul.find_all('a')]
        return ", ".join(credits_list) if credits_list else None


class Command(BaseCommand):
    help = 'Scrapes IMDb movies based on genre or keyword'

    def add_arguments(self, parser):
        parser.add_argument('--type', type=str, choices=SEARCH_CHOICES, required=True)
        parser.add_argument('--value', type=str, required=True)
        parser.add_argument('--limit', type=int, default=IMDB_PAGE_SIZE)
        parser.add_argument('--job_id', type=str, required=False)

    def handle(self, *args, **options):
        search_type = options['type']
        search_value = options['value']
        limit = options['limit']
        job_id = options.get('job_id')

        if job_id:
            try:
                status = asyncio.run(sync_to_async(ScraperStatus.objects.get)(job_id=uuid.UUID(job_id)))
            except ScraperStatus.DoesNotExist:
                raise CommandError(f"Job with id {job_id} does not exist.")
        else:
            status = asyncio.run(sync_to_async(ScraperStatus.objects.create)())

        status.status = 'running'
        asyncio.run(sync_to_async(status.save)(update_fields=["status"]))
        logger.info(f"Scraping IMDb using {search_type}: '{search_value}', limit: {limit}")

        try:
            scraper = IMDBScraper(search_type, search_value, limit, status)
            asyncio.run(scraper.run())
        except Exception as e:
            logger.exception("Scraper failed")
            status.status = 'error'
            status.error_message = str(e)
            asyncio.run(sync_to_async(status.save)(update_fields=["status", "error_message"]))
            raise
