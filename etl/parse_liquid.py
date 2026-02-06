import json
import csv
import os
import re
import hashlib
import pandas as pd
from datetime import datetime
import glob

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw_snapshots")
TABLES_DIR = os.path.join(BASE_DIR, "data", "tables")

# --- REGEX PATTERNS ---
# 1. Direct Catalog Access: catalog_items['CatalogName'][index].fieldName
# Captures: 1=CatalogName, 2=FieldName
REGEX_DIRECT_ACCESS = r"catalog_items\s*\[['\"](.*?)['\"]\].*?\.([a-zA-Z0-9_]+)\b"

# 2. Assign/Where lookups: where: 'fieldName', value
# Captures: 1=FieldName
REGEX_WHERE_LOOKUP = r"where:\s*['\"]([a-zA-Z0-9_]+)['\"]"

# 3. New Catalog Pattern: {% catalog_items Primary_Locations_Catalog ... %}
# Captures: 1=CatalogName
REGEX_CATALOG_BLOCK = r"{%\s*catalog_items\s+([a-zA-Z0-9_]+)"

# 4. Assigning items to a variable: {% assign var = items... %}
# Captures: 1=VarName
REGEX_ASSIGN_ITEMS = r"{%\s*assign\s+([a-zA-Z0-9_]+)\s*=\s*items"

# 5. Variable Usage: var.field
REGEX_VAR_ACCESS = r"\b([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\b"


def get_hash(text):
    return hashlib.md5(str(text).encode("utf-8")).hexdigest()


def ensure_tables_dir():
    if not os.path.exists(TABLES_DIR):
        os.makedirs(TABLES_DIR)


def get_latest_file(pattern):
    files = glob.glob(os.path.join(RAW_DIR, pattern))
    if not files:
        return None
    return max(files, key=os.path.getctime)


def parse_catalog_schema():
    """Reads local catalog JSON (items) and infers schema from keys"""
    # Look for catalog_items_*.json (produced by fetch_braze.py)
    schema_path = get_latest_file("catalog_items_*.json")

    # Fallback to sample if no real data found
    if not schema_path:
        schema_path = os.path.join(RAW_DIR, "sample_catalogs.json")
        if not os.path.exists(schema_path):
            print(
                "No catalog data found (checked catalog_items_*.json and sample_catalogs.json)."
            )
            return set()

    print(f"Reading catalog data from: {os.path.basename(schema_path)}")

    with open(schema_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # transform.py logic: data might be a dict with 'items' key or just the items
    items = data.get("items", []) if isinstance(data, dict) else data

    # Infer schema from all keys in all items
    known_fields = set()
    for item in items:
        if isinstance(item, dict):
            known_fields.update(item.keys())

    # Remove internal id if present, or keep it. Let's keep it but mark as system.

    rows = []
    for field in known_fields:
        rows.append(
            {
                "field_name": field,
                "field_type": "String",  # Inferred, could be improved
                "is_custom": field not in ["id", "updated_at", "created_at"],
                "last_seen": datetime.now().strftime("%Y-%m-%d"),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(TABLES_DIR, "catalog_schema.csv"), index=False)
    print(f"Parsed {len(df)} catalog fields.")
    return known_fields


def parse_assets(known_fields):
    """Parses campaigns/canvases for liquid and references"""

    # 1. Campaigns
    camp_path = get_latest_file("campaign_details_*.json")
    if not camp_path:
        camp_path = os.path.join(RAW_DIR, "sample_campaigns.json")

    # 2. Canvases
    canvas_path = get_latest_file("canvas_details_*.json")
    # If sample_campaigns contains mixed data (as in my mock), we handled it.
    # But usually real exports are separate.

    assets_to_process = []

    # Load Campaigns
    if camp_path and os.path.exists(camp_path):
        print(f"Reading campaigns from: {os.path.basename(camp_path)}")
        with open(camp_path, "r", encoding="utf-8") as f:
            camps = json.load(f)
            # transform.py handles: item.get("campaign", {}) or item
            for item in camps:
                actual_item = item.get("campaign", item)
                assets_to_process.append({"data": actual_item, "type": "Campaign"})

    # Load Canvases
    if canvas_path and os.path.exists(canvas_path):
        print(f"Reading canvases from: {os.path.basename(canvas_path)}")
        with open(canvas_path, "r", encoding="utf-8") as f:
            canvs = json.load(f)
            for item in canvs:
                # transform.py handles: item.get("canvas", {}) or item
                actual_item = item.get("canvas", item)
                assets_to_process.append({"data": actual_item, "type": "Canvas"})

    if not assets_to_process:
        print("No assets found to process.")
        return

    asset_rows = []
    block_rows = []
    ref_rows = []

    for entry in assets_to_process:
        asset = entry["data"]
        a_type = entry["type"]

        asset_id = asset.get("id", "unknown")
        asset_name = asset.get("name", "Unnamed")

        # Determine "Last Active" date
        last_active = None
        if a_type == "Campaign":
            last_active = asset.get("last_sent") or asset.get("stats", {}).get(
                "last_sent"
            )
        elif a_type == "Canvas":
            last_active = asset.get("last_entry") or asset.get(
                "canvas_summary", {}
            ).get("last_entry")

        # Fallback to edited if never sent
        if not last_active:
            last_active = asset.get("last_edited_at", asset.get("updated_at"))

        asset_rows.append(
            {
                "asset_id": asset_id,
                "asset_name": asset_name,
                "asset_type": a_type,
                "subtype": "Standard",
                "status": "Active" if asset.get("status") != "Archived" else "Archived",
                "last_edited": asset.get("last_edited_at", asset.get("updated_at")),
                "last_active": last_active,
                "tags": ",".join(asset.get("tags", [])),
            }
        )

        # Helper to process a text string
        def process_content(text, step_name, channel):
            if not isinstance(text, str) or "{" not in text:
                return

            content_hash = get_hash(text)
            block_id = get_hash(f"{asset_id}_{step_name}_{content_hash}")

            block_rows.append(
                {
                    "block_id": block_id,
                    "asset_id": asset_id,
                    "step_name": step_name,
                    "channel": channel,
                    "location": "body",
                    "liquid_content": text,  # In prod, might truncate if massive
                    "content_hash": content_hash,
                }
            )

            # 3. Find References (The Governance Logic)

            # Strategy: Linear Scan for Context
            # We track which variable maps to which catalog within this block
            # Map: { "items": "Primary_Locations_Catalog", "my_item": "Primary_Locations_Catalog" }
            var_catalog_map = {}

            # Identify catalog blocks first (naive scope: assuming one main catalog per block for now, or last seen)
            # Find all catalog declarations
            for match in re.finditer(REGEX_CATALOG_BLOCK, text):
                cat_name = match.group(1)
                if cat_name == "Primary_Locations_Catalog":
                    var_catalog_map["items"] = cat_name  # 'items' is the default

            # Find assignments (aliases)
            # {% assign catalog_item = items[0] %}
            for match in re.finditer(REGEX_ASSIGN_ITEMS, text):
                var_name = match.group(1)
                # If 'items' is already mapped, map this new var too
                if "items" in var_catalog_map:
                    var_catalog_map[var_name] = var_catalog_map["items"]

            # Check A: Direct Access (Old Regex)
            for match in re.finditer(REGEX_DIRECT_ACCESS, text):
                catalog_name, field_name = match.groups()
                if catalog_name == "Primary_Locations_Catalog":
                    ref_rows.append(
                        {
                            "ref_id": get_hash(f"{block_id}_{field_name}"),
                            "block_id": block_id,
                            "field_name": field_name,
                            "match_type": "direct_access",
                            "context_snippet": match.group(0),
                            "is_risk": field_name not in known_fields,
                        }
                    )

            # Check B: 'Where' Lookups
            for match in re.finditer(REGEX_WHERE_LOOKUP, text):
                field_name = match.group(1)
                ref_rows.append(
                    {
                        "ref_id": get_hash(f"{block_id}_{field_name}_where"),
                        "block_id": block_id,
                        "field_name": field_name,
                        "match_type": "where_clause",
                        "context_snippet": match.group(0),
                        "is_risk": field_name not in known_fields,
                    }
                )

            # Check C: Variable Access (New Logic)
            if var_catalog_map:
                for match in re.finditer(REGEX_VAR_ACCESS, text):
                    var_name, field_name = match.groups()
                    if var_name in var_catalog_map:
                        # Ensure we don't duplicate existing direct_access finds
                        # (A hash collision check handles this naturally, or we can just append)
                        ref_rows.append(
                            {
                                "ref_id": get_hash(
                                    f"{block_id}_{var_name}_{field_name}"
                                ),
                                "block_id": block_id,
                                "field_name": field_name,
                                "match_type": f"var_alias ({var_name})",
                                "context_snippet": match.group(0),
                                "is_risk": field_name not in known_fields,
                            }
                        )

        # Walk the JSON structure
        # Campaigns
        if "messages" in asset:
            msgs = asset["messages"]
            # messages can be dict (channel -> msg) or list of dicts
            if isinstance(msgs, dict):
                for channel, msg in msgs.items():
                    if isinstance(msg, dict) and "body" in msg:
                        process_content(msg["body"], "Campaign Message", channel)
            elif isinstance(msgs, list):
                for msg in msgs:
                    if isinstance(msg, dict) and "body" in msg:
                        process_content(
                            msg["body"],
                            "Campaign Message",
                            msg.get("channel", "unknown"),
                        )

        # Canvases
        if "steps" in asset:
            for step in asset["steps"]:
                step_name = step.get("name", "Unknown Step")
                if "messages" in step:
                    msgs = step["messages"]
                    if isinstance(msgs, dict):
                        for channel, msg in msgs.items():
                            if isinstance(msg, dict):
                                # Check common body fields
                                body = (
                                    msg.get("body")
                                    or msg.get("alert")
                                    or msg.get("email_body")
                                )
                                if body:
                                    process_content(body, step_name, channel)
                    elif isinstance(msgs, list):
                        for msg in msgs:
                            if isinstance(msg, dict):
                                body = (
                                    msg.get("body")
                                    or msg.get("alert")
                                    or msg.get("email_body")
                                )
                                if body:
                                    process_content(
                                        body, step_name, msg.get("channel", "unknown")
                                    )

    # Write Outputs
    pd.DataFrame(asset_rows).to_csv(
        os.path.join(TABLES_DIR, "asset_inventory.csv"), index=False
    )
    pd.DataFrame(block_rows).to_csv(
        os.path.join(TABLES_DIR, "content_blocks.csv"), index=False
    )
    pd.DataFrame(ref_rows).to_csv(
        os.path.join(TABLES_DIR, "field_references.csv"), index=False
    )

    # Create empty dependencies if not exists
    if not os.path.exists(os.path.join(TABLES_DIR, "dependencies.csv")):
        pd.DataFrame(
            {"source_asset_id": [], "target_asset_id": [], "dependency_type": []}
        ).to_csv(os.path.join(TABLES_DIR, "dependencies.csv"), index=False)

    print(f"Processed {len(assets_to_process)} assets.")
    print(f"Extracted {len(block_rows)} liquid blocks.")
    print(f"Found {len(ref_rows)} field references.")


if __name__ == "__main__":
    ensure_tables_dir()
    print("Starting Local ETL...")
    fields = parse_catalog_schema()
    parse_assets(fields)
    print("Done.")
