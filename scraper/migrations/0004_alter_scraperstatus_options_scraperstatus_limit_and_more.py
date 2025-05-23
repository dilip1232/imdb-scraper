# Generated by Django 5.2.1 on 2025-05-18 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0003_scraperstatus'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='scraperstatus',
            options={'verbose_name': 'New Scrape Job', 'verbose_name_plural': 'Scrape Jobs'},
        ),
        migrations.AddField(
            model_name='scraperstatus',
            name='limit',
            field=models.IntegerField(default=50),
        ),
        migrations.AddField(
            model_name='scraperstatus',
            name='search_type',
            field=models.CharField(choices=[('genre', 'Genre'), ('keyword', 'Keyword')], default='genre', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scraperstatus',
            name='search_value',
            field=models.CharField(default='action', max_length=255),
            preserve_default=False,
        ),
    ]
