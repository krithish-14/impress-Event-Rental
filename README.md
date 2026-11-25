# Event Rental

Luxury event-rental website matching the Impress Signature Seating layout, built with HTML/CSS/JS templates on a Django backend.

## Run locally

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_catalog
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Admin: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)  
Username: `admin`  
Password: `admin123`

## Pages

- Home — hero slider, partner ribbon, welcome, collection cards
- Collections — Seating, Tables, Tents, Lighting
- Product detail — quote + WhatsApp
- Event Solutions
- Gallery — search, filters, lightbox
- Contact — inquiry form saved to Django admin
