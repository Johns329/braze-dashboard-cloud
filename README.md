# Braze Governance Dashboard (Streamlit Cloud)

This folder is a deployable copy of the Braze Governance dashboard + ETL, structured for Streamlit Community Cloud.

## Run locally

1) Install deps

```bash
python -m pip install -r requirements.txt
```

2) Run the app

```bash
streamlit run streamlit_app.py
```

## Refresh data (ETL)

The app reads CSV tables from `data/tables/`.

To regenerate those tables from the Braze API:

1) Set environment variables (or create a `.env` file in this folder):

- `BRAZE_API_KEY`
- `BRAZE_REST_ENDPOINT` (optional; defaults to `https://rest.iad-05.braze.com`)

You can also use `.streamlit/secrets.toml` (see `.streamlit/secrets.example.toml`).

2) Run:

```bash
python etl/run_etl.py
```

That will write raw snapshots to `data/raw_snapshots/` and refreshed tables to `data/tables/`.

## Deploy to Streamlit Community Cloud

1) Push this folder to a GitHub repo.
2) In Streamlit Community Cloud, set the app entrypoint to `streamlit_app.py`.
3) If you want the hosted app to show fresh data, commit the generated CSVs in `data/tables/` (recommended).

Notes:
- Do not commit secrets. Use Streamlit Cloud Secrets for API keys.
