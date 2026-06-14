# Railway Deployment Configuration

## Environment Variables to Set in Railway

Add these environment variables in the Railway dashboard:

### Required Variables
```
DJANGO_SETTINGS_MODULE=vasta_portfolio.prod
DJANGO_SECRET_KEY=<your-secret-key>
DJANGO_DEBUG=False
PYTHONUNBUFFERED=1
```

### Domain Configuration
```
DJANGO_ALLOWED_HOSTS=your-app.up.railway.app,www.yourdomain.com,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app,https://www.yourdomain.com
```

### Database (auto-set by Railway PostgreSQL plugin)
```
DATABASE_URL=<auto-populated by Railway PostgreSQL plugin>
```

### Cloudinary Setup (for media files)
```
CLOUDINARY_CLOUD_NAME=<your-cloud-name>
CLOUDINARY_API_KEY=<your-api-key>
CLOUDINARY_API_SECRET=<your-api-secret>
```

### Email (optional — only needed for contact form)
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=<app-password>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@vastarchitects.in
```

## Railway Setup Process

1. **Connect GitHub repository** to Railway
2. **Add PostgreSQL plugin** (Railway will auto-set `DATABASE_URL`)
3. **Set environment variables** (see above)
4. **Deploy** — Railway will:
   - Read Python version from `runtime.txt` (`python-3.12.3`)
   - Install dependencies from `vasta_portfolio/requirements.txt`
   - Run release tasks from `Procfile`:
     - Migrate database
     - Collect static files
   - Start web server with gunicorn

## What Happens on Each Deploy

```
Build Phase:
└── pip install -r vasta_portfolio/requirements.txt

Release Phase (runs once before traffic switches):
├── python manage.py migrate          → Updates database schema
└── python manage.py collectstatic    → Gathers static files to staticfiles/

Web Server:
└── gunicorn vasta_portfolio.wsgi:application  → Starts Django app on $PORT
```

## File Structure

```
VASTA/
├── Procfile              → Release + start commands
├── runtime.txt           → Python 3.12.3
├── railway.toml          → Build config (pip install path, health check)
├── railway_setup.md      → This file
└── vasta_portfolio/
    ├── requirements.txt  → Python dependencies
    └── vasta_portfolio/
        ├── settings.py   → Base settings (used locally)
        └── prod.py       → Production settings (imports settings.py, adds whitenoise + cloudinary)
```

## Generate a Secret Key

Run this locally to generate a secure `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Common Issues & Solutions

### "No directory at: /app/staticfiles/"
- **Cause**: collectstatic hasn't run yet
- **Solution**: Safe to ignore — collectstatic in the release phase creates it

### Database connection errors
- **Cause**: PostgreSQL plugin not added, or `DATABASE_URL` not set
- **Solution**: Add PostgreSQL plugin in Railway dashboard; it auto-sets `DATABASE_URL`

### Static files not loading (404s)
- **Cause**: WhiteNoise not in middleware or `collectstatic` not run
- **Solution**: WhiteNoise is already in `MIDDLEWARE` in `settings.py`; release phase runs `collectstatic`

### Media files not appearing
- **Cause**: Cloudinary variables not set
- **Solution**: Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

## Debugging

```bash
# View live logs
railway logs --follow

# Check deployment status
railway status

# Open a shell inside the running container
railway shell

# Inside shell — test database connection
python manage.py dbshell
```