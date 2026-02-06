import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES_DIR = os.path.join(BASE_DIR, "data", "tables")


def get_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def generate_csvs():
    print(f"Generating seed data in {TABLES_DIR}...")

    # 1. Catalog Schema (Primary_Locations_Catalog)
    # The 'Source of Truth' for what fields exist
    catalog_data = [
        {
            "field_name": "location_id",
            "field_type": "String",
            "is_custom": False,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "city",
            "field_type": "String",
            "is_custom": False,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "state",
            "field_type": "String",
            "is_custom": False,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "region",
            "field_type": "String",
            "is_custom": True,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "manager_email",
            "field_type": "String",
            "is_custom": True,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "store_hours",
            "field_type": "Object",
            "is_custom": True,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "is_open",
            "field_type": "Boolean",
            "is_custom": True,
            "last_seen": "2023-10-25",
        },
        {
            "field_name": "legacy_code",
            "field_type": "String",
            "is_custom": True,
            "last_seen": "2023-01-01",
        },  # Old field
    ]
    pd.DataFrame(catalog_data).to_csv(
        os.path.join(TABLES_DIR, "catalog_schema.csv"), index=False
    )

    # 2. Asset Inventory (Campaigns & Canvases)
    assets_data = [
        # The "Blank Webhook" Campaign
        {
            "asset_id": "cmp_eligibility_engine",
            "asset_name": "Global Eligibility Calculator",
            "asset_type": "Campaign",
            "subtype": "Webhook",
            "status": "Active",
            "last_edited": "2023-10-26",
        },
        # Downstream Canvas
        {
            "asset_id": "cnv_welcome_series",
            "asset_name": "Welcome Series V2",
            "asset_type": "Canvas",
            "subtype": "Push",
            "status": "Active",
            "last_edited": "2023-10-27",
        },
        # Another Canvas
        {
            "asset_id": "cnv_winback",
            "asset_name": "Winback - 90 Days",
            "asset_type": "Canvas",
            "subtype": "Email",
            "status": "Draft",
            "last_edited": "2023-09-15",
        },
    ]
    pd.DataFrame(assets_data).to_csv(
        os.path.join(TABLES_DIR, "asset_inventory.csv"), index=False
    )

    # 3. Content Blocks (Extracted Liquid)
    # Simulating what we parsed from the API JSONs

    # Liquid for the Eligibility Engine
    liquid_eligibility = """{% assign location = catalog_items['Primary_Locations_Catalog'] | where: 'location_id', custom_attribute.${preferred_store_id} | first %}
{% if location.is_open == true %}
  {% assign eligible = true %}
{% else %}
  {% abort_message('Store closed') %}
{% endif %}"""

    # Liquid for Welcome Series (Direct Usage)
    liquid_welcome = """Hi {{ first_name }}, visit us at {{ catalog_items['Primary_Locations_Catalog'][0].city }}!
Manager: {{ catalog_items['Primary_Locations_Catalog'][0].manager_email }}"""

    # Liquid for Winback (Has a 'Ghost Field' - 'old_offer_code' not in schema)
    liquid_winback = """We miss you! Use code {{ catalog_items['Primary_Locations_Catalog'][0].legacy_code }}."""

    blocks_data = [
        {
            "block_id": get_hash("cmp_eligibility_engine" + "step1"),
            "asset_id": "cmp_eligibility_engine",
            "step_name": "Webhook Body",
            "channel": "webhook",
            "location": "body",
            "liquid_content": liquid_eligibility,
            "content_hash": get_hash(liquid_eligibility),
        },
        {
            "block_id": get_hash("cnv_welcome_series" + "var1"),
            "asset_id": "cnv_welcome_series",
            "step_name": "Message 1",
            "channel": "push",
            "location": "body",
            "liquid_content": liquid_welcome,
            "content_hash": get_hash(liquid_welcome),
        },
        {
            "block_id": get_hash("cnv_winback" + "email1"),
            "asset_id": "cnv_winback",
            "step_name": "Winback Email",
            "channel": "email",
            "location": "body",
            "liquid_content": liquid_winback,
            "content_hash": get_hash(liquid_winback),
        },
    ]
    pd.DataFrame(blocks_data).to_csv(
        os.path.join(TABLES_DIR, "content_blocks.csv"), index=False
    )

    # 4. Field References (The Parse Results)
    # Mapping Block -> Catalog Field
    refs_data = [
        # Eligibility Engine Refs
        {
            "ref_id": "r1",
            "block_id": get_hash("cmp_eligibility_engine" + "step1"),
            "field_name": "location_id",
            "match_type": "lookup_key",
            "context_snippet": "where: 'location_id'",
            "is_risk": False,
        },
        {
            "ref_id": "r2",
            "block_id": get_hash("cmp_eligibility_engine" + "step1"),
            "field_name": "is_open",
            "match_type": "dot_access",
            "context_snippet": "location.is_open",
            "is_risk": False,
        },
        # Welcome Series Refs
        {
            "ref_id": "r3",
            "block_id": get_hash("cnv_welcome_series" + "var1"),
            "field_name": "city",
            "match_type": "direct_lookup",
            "context_snippet": "items...[0].city",
            "is_risk": False,
        },
        {
            "ref_id": "r4",
            "block_id": get_hash("cnv_welcome_series" + "var1"),
            "field_name": "manager_email",
            "match_type": "direct_lookup",
            "context_snippet": "items...[0].manager_email",
            "is_risk": False,
        },
        # Winback Refs (Ghost Field)
        {
            "ref_id": "r5",
            "block_id": get_hash("cnv_winback" + "email1"),
            "field_name": "legacy_code",
            "match_type": "direct_lookup",
            "context_snippet": "items...[0].legacy_code",
            "is_risk": True,
        },  # marked risk just for demo, though it exists in legacy schema
        {
            "ref_id": "r6",
            "block_id": get_hash("cnv_winback" + "email1"),
            "field_name": "ghost_promo",
            "match_type": "direct_lookup",
            "context_snippet": "items...[0].ghost_promo",
            "is_risk": True,
        },  # Totally missing field
    ]
    pd.DataFrame(refs_data).to_csv(
        os.path.join(TABLES_DIR, "field_references.csv"), index=False
    )

    # 5. Dependencies
    deps_data = [
        {
            "source_asset_id": "cmp_eligibility_engine",
            "target_asset_id": "cnv_welcome_series",
            "dependency_type": "segment_inclusion",
        },
    ]
    pd.DataFrame(deps_data).to_csv(
        os.path.join(TABLES_DIR, "dependencies.csv"), index=False
    )

    print("Seed data generated successfully.")


if __name__ == "__main__":
    generate_csvs()
