# FF GUILD GOLORY BOT — Render Ready

This package serves the Telegram Mini App and runs the Telegram bot in the same Render Web Service.

## Render settings
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --workers 1 --threads 2 --bind 0.0.0.0:$PORT`
- Environment variable: `BOT_TOKEN` = your current/new BotFather token
- Environment variable: `WEB_APP_URL` = your Render HTTPS URL, e.g. `https://your-service.onrender.com`

If `WEB_APP_URL` is left blank, the app attempts to use Render's `RENDER_EXTERNAL_URL` automatically.

Do not commit your bot token to GitHub. Store it only in Render Environment Variables.

# SECURITY: Keep this value out of GitHub. Set BOT_TOKEN in Render Dashboard -> Environment.
