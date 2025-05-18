from django.contrib import admin
from .models import Movie, ScraperStatus
from django.core.management import call_command
import threading
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import DropdownFilter


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'short_directors', 'short_cast')
    list_filter = (('year', DropdownFilter),
                   ('rating', DropdownFilter))
    search_fields = ('title', 'directors', 'cast', 'plot')
    ordering = ('-year', '-rating')
    list_per_page = 25

    def short_directors(self, obj):
        if obj.directors:
            return ", ".join(obj.directors.split(",")[:2]) + ("..." if obj.directors.count(",") > 1 else "")
        return "-"
    short_directors.short_description = "Directors"

    def short_cast(self, obj):
        if obj.cast:
            return ", ".join(obj.cast.split(",")[:2]) + ("..." if obj.cast.count(",") > 1 else "")
        return "-"
    short_cast.short_description = "Cast"


@admin.register(ScraperStatus)
class ScraperStatusAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'status', 'scraped_movies', 'error_message', 'run_now_link')
    readonly_fields = ('job_id', 'started_at', 'updated_at', 'scraped_movies', 'status', 'error_message')

    fields = ('job_id', 'search_type', 'search_value', 'limit', 'status', 'scraped_movies', 'error_message', 'started_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-started_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        def run_scraper():
            try:
                call_command(
                    'scraper',
                    type=obj.search_type,
                    value=obj.search_value,
                    limit=obj.limit,
                    job_id=str(obj.job_id)
                )
            except Exception as e:
                obj.status = 'error'
                obj.error_message = str(e)
                obj.save(update_fields=["status", "error_message"])

        threading.Thread(target=run_scraper).start()

    def run_now_link(self, obj):
        return format_html('<a class="button" href="/admin/scraper/scraperstatus/{}/change/">View</a>', obj.pk)
    run_now_link.short_description = 'Manage'
