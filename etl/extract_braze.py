"""Fetch raw data from Braze REST API and save JSON exports to data/raw_snapshots.

Usage:
  python etl/extract_braze.py

This script reads BRAZE_API_KEY and optional BRAZE_REST_ENDPOINT from environment.
For local development, you can put them in a project-local .env file.
"""

import argparse
import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tomllib
import requests
from dotenv import load_dotenv

# Project path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(BASE_DIR, "data", "raw_snapshots")


def _load_env(env_file: str | None) -> None:
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
        return

    project_env = os.path.join(BASE_DIR, ".env")
    if os.path.exists(project_env):
        load_dotenv(project_env)
        print(f"Loaded environment variables from {project_env}")
        return

    # Fall back to process environment.
    print("No .env file found; using process environment variables.")

    secrets_path = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
            for key in ("BRAZE_API_KEY", "BRAZE_REST_ENDPOINT"):
                if key not in os.environ and key in secrets:
                    os.environ[key] = str(secrets[key])
            print(f"Loaded secrets from {secrets_path}")
        except Exception as e:
            print(f"Warning: failed to load {secrets_path}: {e}")


def _request_with_backoff(session, url, headers=None, params=None, max_retries=5):
    delay = 1.0
    for attempt in range(max_retries):
        try:
            resp = session.get(url, headers=headers, params=params, timeout=30)
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue

        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {}

        if resp.status_code in (429,) or resp.status_code >= 500:
            if attempt == max_retries - 1:
                resp.raise_for_status()
            time.sleep(delay + (0.1 * attempt))
            delay = min(delay * 2, 60)
            continue

        resp.raise_for_status()


def paginate_list(session, url, headers, list_key, params=None):
    items = []
    page = 0
    while True:
        p = dict(params or {})
        p.update({"page": page})
        data = _request_with_backoff(session, url, headers=headers, params=p)
        if not isinstance(data, dict):
            break
        chunk = data.get(list_key, [])
        if not chunk:
            break
        items.extend(chunk)
        page += 1
    return items


def fetch_campaigns_list(session, rest_ep, headers):
    url = rest_ep.rstrip("/") + "/campaigns/list"
    return paginate_list(session, url, headers, "campaigns")


def fetch_canvases_list(session, rest_ep, headers):
    url = rest_ep.rstrip("/") + "/canvas/list"
    return paginate_list(session, url, headers, "canvases")


def fetch_details_concurrent(
    session, rest_ep, headers, ids, endpoint, id_param_name, max_workers=8
):
    results = []
    failures = []

    def _get_one(obj_id):
        url = rest_ep.rstrip("/") + endpoint
        params = {id_param_name: obj_id}
        try:
            return _request_with_backoff(session, url, headers=headers, params=params)
        except Exception as e:
            return {"__error__": str(e)}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_get_one, i): i for i in ids}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                res = fut.result()
                if isinstance(res, dict) and res.get("__error__"):
                    failures.append({"id": i, "error": res.get("__error__")})
                else:
                    if isinstance(res, dict):
                        res["id"] = i
                    results.append(res)
            except Exception as e:
                failures.append({"id": i, "error": str(e)})

    return results, failures


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--env-file",
        default=None,
        help="Path to a .env file (defaults to <project>/.env if present)",
    )
    p.add_argument(
        "--out-dir", default=DEFAULT_OUT_DIR, help="output directory for raw files"
    )
    p.add_argument(
        "--date", default=None, help="date suffix (YYYYMMDD). Defaults to today"
    )
    p.add_argument(
        "--concurrency",
        default=8,
        type=int,
        help="concurrent workers for details fetch",
    )
    args = p.parse_args()

    _load_env(args.env_file)

    api_key = os.environ.get("BRAZE_API_KEY")
    if not api_key:
        print("Error: BRAZE_API_KEY environment variable is not set.")
        print(
            "Please set it in your environment or creates a .env file (if using python-dotenv)."
        )
        return 1

    rest_ep = os.environ.get("BRAZE_REST_ENDPOINT", "https://rest.iad-05.braze.com")

    date_suffix = args.date or datetime.utcnow().strftime("%Y%m%d")
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    session = requests.Session()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    manifest = {
        "date": date_suffix,
        "fetched_at": datetime.utcnow().isoformat(),
        "counts": {},
        "failures": [],
    }

    # campaigns list
    print("Listing campaigns...")
    campaigns = fetch_campaigns_list(session, rest_ep, headers)
    campaigns_file = os.path.join(out_dir, f"campaigns_list_{date_suffix}.json")
    with open(campaigns_file, "w", encoding="utf-8") as f:
        json.dump(campaigns, f, indent=2)
    manifest["counts"]["campaigns_list"] = len(campaigns)
    print(f"Saved {len(campaigns)} campaigns to {campaigns_file}")

    # campaign details
    print("Fetching campaign details (concurrent)...")
    campaign_ids = [c.get("id") for c in campaigns if c.get("id")]
    camp_details, camp_failures = fetch_details_concurrent(
        session,
        rest_ep,
        headers,
        campaign_ids,
        "/campaigns/details",
        "campaign_id",
        max_workers=args.concurrency,
    )
    camp_details_file = os.path.join(out_dir, f"campaign_details_{date_suffix}.json")
    with open(camp_details_file, "w", encoding="utf-8") as f:
        json.dump(camp_details, f, indent=2)
    manifest["counts"]["campaign_details"] = len(camp_details)
    manifest["failures"].extend(camp_failures)
    print(
        f"Saved campaign details: {camp_details_file} (failures: {len(camp_failures)})"
    )

    # canvases list
    print("Listing canvases...")
    canvases = fetch_canvases_list(session, rest_ep, headers)
    canvases_file = os.path.join(out_dir, f"canvases_list_{date_suffix}.json")
    with open(canvases_file, "w", encoding="utf-8") as f:
        json.dump(canvases, f, indent=2)
    manifest["counts"]["canvases_list"] = len(canvases)
    print(f"Saved {len(canvases)} canvases to {canvases_file}")

    # canvas details
    print("Fetching canvas details (concurrent)...")
    canvas_ids = [c.get("id") for c in canvases if c.get("id")]
    canvas_details, canvas_failures = fetch_details_concurrent(
        session,
        rest_ep,
        headers,
        canvas_ids,
        "/canvas/details",
        "canvas_id",
        max_workers=args.concurrency,
    )
    canvas_details_file = os.path.join(out_dir, f"canvas_details_{date_suffix}.json")
    with open(canvas_details_file, "w", encoding="utf-8") as f:
        json.dump(canvas_details, f, indent=2)
    manifest["counts"]["canvas_details"] = len(canvas_details)
    manifest["failures"].extend(canvas_failures)
    print(
        f"Saved canvas details: {canvas_details_file} (failures: {len(canvas_failures)})"
    )

    # Catalog Items (Primary_Locations_Catalog)
    print("Fetching catalog items for Primary_Locations_Catalog...")
    # endpoint: /catalogs/{catalog_name}/items
    catalog_name = "Primary_Locations_Catalog"
    url = f"{rest_ep.rstrip('/')}/catalogs/{catalog_name}/items"

    try:
        cat_data = _request_with_backoff(session, url, headers=headers)
        if isinstance(cat_data, dict):
            cat_file = os.path.join(out_dir, f"catalog_items_{date_suffix}.json")
            with open(cat_file, "w", encoding="utf-8") as f:
                json.dump(cat_data, f, indent=2)
            item_count = len(cat_data.get("items", []))
            manifest["counts"]["catalog_items"] = item_count
            print(f"Saved {item_count} items from catalog {catalog_name}")
        else:
            print(f"Warning: Unexpected response format for catalog {catalog_name}")
    except Exception as e:
        print(f"Failed to fetch catalog {catalog_name}: {e}")
        manifest["failures"].append({"id": catalog_name, "error": str(e)})

    # manifest
    manifest_file = os.path.join(out_dir, f"manifest_{date_suffix}.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote manifest to {manifest_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
