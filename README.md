# Config Precedence API

Render settings:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Set these Render environment variables:
- `APP_WORKERS=9`
- `APP_LOG_LEVEL=debug`

The app merges defaults -> `config.<APP_ENV>.yaml` (development by default) -> `.env` -> OS `APP_*` vars -> repeated `set=key=value` query overrides.
Example: `/effective-config?set=port=9000&set=debug=true`

The API enables CORS and always masks `api_key` as `****`.
