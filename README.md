
# 🎬 IMDb Scraper Project (Django + Admin + API)

This Django project allows you to scrape movie data from IMDb based on `genre` or `keyword`, and manage everything via the Django admin interface.

---

## ⚙️ Setup Instructions

### 1. 🔁 Clone the Repository

```bash
git clone https://github.com/dilip1232/imdb-scraper.git
cd imdb-scraper
```

### 2. 📦 Install Requirements

```bash
pip install -r requirements.txt
```

> Make sure you have Python 3.9+ and `playwright` dependencies set up correctly.

### 3. 🧱 Set Up the Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 🧪 Run Tests (optional)

```bash
python manage.py test
```

### 5. 🧑‍💻 Create Superuser

```bash
python manage.py createsuperuser
```

### 6. 🚀 Run the Server

```bash
python manage.py runserver
```

---

## 🛠 Starting a Scraper Job (via Admin Panel)

You can trigger and monitor scrapers directly from Django Admin:

1. Go to [http://localhost:8000/admin/](http://localhost:8000/admin/)
2. Navigate to **"Scrape Jobs"**
3. Click **"Add New Scrape Job"**
4. Select `search_type`, provide `search_value` (e.g. "action" or "sci-fi"), and a `limit`
5. Hit **Save** — the scraper runs in the background, and status will update automatically

### 🖼️ Admin Screenshot

> _(Replace this with actual screenshot)_

```
📷 ![Admin Scraper Panel](screenshots/admin-scraper-job.png)
```

---

## 📡 API: Get Scraped Movies

### 📥 Endpoint

```
GET /api/movies/
```

### 🔎 Query Parameters

| Param       | Type   | Description                         |
|-------------|--------|-------------------------------------|
| `search`    | string | Full-text search in title/cast/etc |
| `year`      | int    | Filter by year                      |
| `rating`    | float  | Filter by exact rating              |
| `ordering`  | string | Field to order by (`-rating`, `year`) |
| `per_page`  | int    | Number of results per page          |

### 📤 Sample Request

```
GET /api/movies/?search=action&year=2023&ordering=-rating&per_page=5
```

### 📥 Sample Response

```json
{
  "count": 120,
  "next": "http://localhost:8000/api/movies/?page=2",
  "previous": null,
  "results": [
    {
      "title": "The Action Hero",
      "year": 2023,
      "rating": 8.2,
      "directors": "John Smith",
      "cast": "Jane Doe, Alan Walker",
      "plot": "A thrilling journey of a rogue agent."
    }
  ]
}
```

---

## 💡 Future Improvements

- ✅ **API-based scraper trigger endpoint**
- ⏳ **Real-time admin scraper progress** (via polling or Django Channels)
- 🎛 **More robust filtering**:
  - Range filter: `rating__gte=6&rating__lte=9`
  - Genre multi-select
- 🧠 **Intelligent duplicate detection and merge logic**
- ⏱ **Schedule recurring scrapes** (CRON or Celery Beat)
- 🌐 **Web frontend dashboard** (React/Vue/HTMX)

---

## 📂 Project Structure

```bash
scraper/
│
├── models.py         # Movie and ScraperStatus models
├── admin.py          # Admin logic + scraper trigger
├── views.py          # Admin panel views + API
├── serializers.py    # Movie API serializer
├── urls.py           # Route definitions
├── management/
│   └── commands/
│       └── scrapper.py   # Main scraping logic using Playwright
```

---

## ✅ Technologies Used

- Django + Django Admin
- Django REST Framework
- Playwright + BeautifulSoup
- PostgreSQL / SQLite
- Async + Threaded scraping
- DRF filters, pagination, ordering
