import uuid
from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=255,unique=True)
    year = models.IntegerField(null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    directors = models.TextField(null=True)
    cast = models.TextField(null=True)
    plot = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.year})"


class ScraperStatus(models.Model):
    job_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_movies = models.IntegerField(default=0)
    scraped_movies = models.IntegerField(default=0)

    SEARCH_TYPE_CHOICES = [
        ('genre', 'Genre'),
        ('keyword', 'Keyword'),
    ]
    search_type = models.CharField(max_length=10, choices=SEARCH_TYPE_CHOICES)
    search_value = models.CharField(max_length=255)
    limit = models.IntegerField(default=50)

    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("error", "Error")
    ], default="pending")
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "New Scrape Job"
        verbose_name_plural = "Scrape Jobs"
