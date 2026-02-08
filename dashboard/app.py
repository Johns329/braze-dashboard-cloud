import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import os
from datetime import datetime, timedelta

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="Toast Audience Studio | Governance",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# Custom CSS - Toast Audience Studio theme (for a seamless iframe embed)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
      --primary: #ff6a00;
      --primary-hover: #e55f00;
      --dark-slate: #0f172a;
      --slate-800: #1e293b;
      --slate-600: #475569;
      --slate-400: #94a3b8;
      --slate-200: #e2e8f0;
      --surface: #ffffff;
      --background: #f8fafc;
      --danger: #ef4444;
      --success: #10b981;
      --warning: #f59e0b;
      --radius-lg: 16px;
      --radius-md: 10px;
      --radius-full: 9999px;
      --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
    }

    html, body, [class*="css"] {
      font-family: 'Inter', system-ui, sans-serif;
    }

    /* Hide Streamlit chrome (especially noticeable in an iframe). */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    div[data-testid="stToolbar"] { visibility: hidden; height: 0; }

    .stApp {
      background: var(--surface);
      color: var(--dark-slate);
    }

    /* Layout */
    .main .block-container {
      padding-top: 1.25rem;
      padding-bottom: 2.5rem;
      max-width: 1400px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
      background: var(--surface);
      border-right: 1px solid var(--slate-200);
    }

    section[data-testid="stSidebar"] .block-container {
      padding-top: 1.25rem;
    }

    /* Headings */
    h1, h2, h3 {
      color: var(--dark-slate) !important;
      letter-spacing: -0.02em;
    }

    h1 {
      font-weight: 800 !important;
      margin-bottom: 0.25rem !important;
    }

    h2 {
      font-weight: 800 !important;
      border-bottom: 1px solid var(--slate-200);
      padding-bottom: 10px;
    }

    h3 {
      font-weight: 700 !important;
    }

    /* Card Containers */
    .governance-card {
      background: var(--surface);
      padding: 20px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--slate-200);
      box-shadow: var(--shadow);
      margin-bottom: 16px;
      transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }

    .governance-card:hover {
      border-color: rgba(255, 106, 0, 0.35);
      box-shadow: 0 10px 18px -10px rgba(0, 0, 0, 0.12);
      transform: translateY(-1px);
    }

    /* Alert Boxes */
    .critical-alert,
    .warning-alert,
    .success-alert,
    .info-alert {
      background: var(--background);
      border: 1px solid var(--slate-200);
      border-left-width: 4px;
      padding: 16px 18px;
      border-radius: var(--radius-lg);
      margin: 14px 0;
      box-shadow: var(--shadow);
    }

    .critical-alert { border-left-color: var(--danger); }
    .warning-alert { border-left-color: var(--warning); }
    .success-alert { border-left-color: var(--success); }
    .info-alert { border-left-color: var(--primary); }

    /* Metric Cards */
    div[data-testid="stMetric"] {
      background: var(--surface);
      padding: 18px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--slate-200);
      box-shadow: var(--shadow);
      transition: border-color 0.2s ease, transform 0.2s ease;
    }

    div[data-testid="stMetric"]:hover {
      transform: translateY(-1px);
      border-color: rgba(255, 106, 0, 0.35);
    }

    div[data-testid="stMetric"] label {
      color: var(--slate-600) !important;
      font-size: 0.8rem !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
      color: var(--primary) !important;
      font-size: 2.0rem !important;
      font-weight: 800 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
      gap: 8px;
      background: var(--background);
      padding: 8px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--slate-200);
    }

    .stTabs [data-baseweb="tab"] {
      background: transparent;
      color: var(--slate-600);
      border-radius: 12px;
      padding: 10px 14px;
      font-weight: 600;
      border: 1px solid transparent;
    }

    .stTabs [aria-selected="true"] {
      background: rgba(255, 106, 0, 0.12) !important;
      color: var(--dark-slate) !important;
      border-color: rgba(255, 106, 0, 0.25) !important;
    }

    /* Buttons */
    .stButton > button {
      background: linear-gradient(135deg, var(--primary) 0%, #ff9e42 100%);
      color: white;
      border: none;
      border-radius: 12px;
      padding: 10px 18px;
      font-weight: 700;
      transition: background 0.2s ease, transform 0.2s ease;
      box-shadow: 0 8px 16px -10px rgba(255, 106, 0, 0.6);
    }

    .stButton > button:hover {
      transform: translateY(-1px);
      background: linear-gradient(135deg, var(--primary-hover) 0%, #ff8f2a 100%);
    }

    /* Status Badges */
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: var(--radius-full);
      font-size: 0.8rem;
      font-weight: 700;
      margin: 2px;
    }

    .status-critical {
      background: rgba(239, 68, 68, 0.12);
      color: var(--danger);
      border: 1px solid rgba(239, 68, 68, 0.35);
    }

    .status-warning {
      background: rgba(245, 158, 11, 0.14);
      color: var(--warning);
      border: 1px solid rgba(245, 158, 11, 0.35);
    }

    .status-success {
      background: rgba(16, 185, 129, 0.12);
      color: var(--success);
      border: 1px solid rgba(16, 185, 129, 0.35);
    }

    .status-info {
      background: rgba(255, 106, 0, 0.12);
      color: var(--primary);
      border: 1px solid rgba(255, 106, 0, 0.35);
    }

    /* Progress bars */
    .stProgress > div > div > div {
      background: linear-gradient(90deg, var(--primary) 0%, #ff9e42 100%);
    }

    /* Navigation pills (Streamlit st.pills) */
    div[data-testid="stPills"] [role="listbox"] {
      gap: 10px;
    }

    div[data-testid="stPills"] [role="option"] {
      border-radius: var(--radius-full);
      border: 1px solid var(--slate-200);
      padding: 10px 14px;
      font-weight: 650;
      color: var(--slate-600);
      background: var(--surface);
      transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
    }

    div[data-testid="stPills"] [role="option"][aria-selected="true"] {
      background: rgba(255, 106, 0, 0.12);
      border-color: rgba(255, 106, 0, 0.35);
      color: var(--dark-slate);
    }

    div[data-testid="stPills"] [role="option"]:hover {
      border-color: rgba(255, 106, 0, 0.35);
      transform: translateY(-1px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# DATA LOADING
# ============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES_DIR = os.path.join(BASE_DIR, "data", "tables")


@st.cache_data
def load_data():
    """Load all governance data tables."""
    try:
        catalog = pd.read_csv(os.path.join(TABLES_DIR, "catalog_schema.csv"))
        assets = pd.read_csv(os.path.join(TABLES_DIR, "asset_inventory.csv"))
        blocks = pd.read_csv(os.path.join(TABLES_DIR, "content_blocks.csv"))
        refs = pd.read_csv(os.path.join(TABLES_DIR, "field_references.csv"))
        deps = pd.read_csv(os.path.join(TABLES_DIR, "dependencies.csv"))

        # Parse dates
        # Normalize to tz-naive UTC so downstream comparisons/grouping work consistently.
        if "last_active" in assets.columns:
            assets["last_active"] = pd.to_datetime(
                assets["last_active"], errors="coerce", utc=True
            ).dt.tz_convert(None)

        return catalog, assets, blocks, refs, deps
    except FileNotFoundError as e:
        st.error(f"⚠️ Data tables not found: {e}")
        st.info("Please run the ETL script first to generate the required data tables.")
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )


# Load data
catalog_df, assets_df, blocks_df, refs_df, deps_df = load_data()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def calculate_governance_score(catalog_df, refs_df, assets_df):
    """Calculate overall governance health score."""
    if catalog_df.empty or refs_df.empty:
        return 0, "No Data"

    # Metrics for scoring
    total_fields = len(catalog_df)
    used_fields = refs_df[refs_df["is_risk"] == False]["field_name"].nunique()
    ghost_fields = len(
        refs_df[
            (refs_df["is_risk"] == True) & (refs_df["field_name"] != "location_guid")
        ]
    )
    total_assets = len(assets_df)

    # Calculate components
    utilization_score = (used_fields / total_fields * 100) if total_fields > 0 else 0
    ghost_penalty = min(ghost_fields * 5, 40)  # Max 40 point penalty

    # Final score
    score = max(0, min(100, utilization_score - ghost_penalty))

    if score >= 85:
        return score, "Excellent"
    elif score >= 70:
        return score, "Good"
    elif score >= 50:
        return score, "Fair"
    else:
        return score, "Critical"


def generate_governance_insights(catalog_df, refs_df, assets_df):
    """Generate actionable governance insights."""
    insights = []

    if refs_df.empty:
        return ["No reference data available for analysis."]

    # Ghost fields (critical)
    ghost_fields = refs_df[
        (refs_df["is_risk"] == True) & (refs_df["field_name"] != "location_guid")
    ]
    if len(ghost_fields) > 0:
        unique_ghosts = ghost_fields["field_name"].nunique()
        insights.append(
            {
                "type": "critical",
                "icon": "🚨",
                "title": "Ghost Fields Detected",
                "message": f"{unique_ghosts} fields are referenced but not in catalog. This can cause runtime errors.",
                "count": unique_ghosts,
            }
        )

    # Catalog saturation
    if not catalog_df.empty:
        total_fields = len(catalog_df)
        used_fields = refs_df[refs_df["is_risk"] == False]["field_name"].nunique()
        saturation = (used_fields / total_fields * 100) if total_fields > 0 else 0

        if saturation < 30:
            insights.append(
                {
                    "type": "warning",
                    "icon": "⚠️",
                    "title": "Low Catalog Utilization",
                    "message": f"Only {saturation:.1f}% of catalog fields are in use. Consider cleaning unused fields.",
                    "count": total_fields - used_fields,
                }
            )
        elif saturation > 85:
            insights.append(
                {
                    "type": "success",
                    "icon": "✅",
                    "title": "High Catalog Utilization",
                    "message": f"{saturation:.1f}% of catalog fields are actively used. Great efficiency!",
                    "count": used_fields,
                }
            )

    # High-impact fields
    if not refs_df[refs_df["is_risk"] == False].empty:
        field_usage = refs_df[refs_df["is_risk"] == False]["field_name"].value_counts()
        if len(field_usage) > 0:
            top_field = field_usage.index[0]
            top_count = field_usage.iloc[0]
            insights.append(
                {
                    "type": "info",
                    "icon": "⭐",
                    "title": "Critical Dependency",
                    "message": f"Field '{top_field}' is used in {top_count} locations. Changes require careful review.",
                    "count": top_count,
                }
            )

    # Stale assets
    if "last_active" in assets_df.columns and not assets_df["last_active"].isna().all():
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
        stale = assets_df[assets_df["last_active"] < cutoff]
        if len(stale) > 0:
            insights.append(
                {
                    "type": "warning",
                    "icon": "⏰",
                    "title": "Stale Assets",
                    "message": f"{len(stale)} assets haven't been active in 90+ days. Review for deprecation.",
                    "count": len(stale),
                }
            )

    return (
        insights
        if insights
        else [
            {
                "type": "success",
                "icon": "✅",
                "title": "All Systems Operational",
                "message": "No critical governance issues detected.",
                "count": 0,
            }
        ]
    )


def create_field_usage_heatmap(refs_df, assets_df, blocks_df):
    """Create field usage heatmap by asset type."""
    if refs_df.empty or assets_df.empty:
        return None

    # Join to get asset types
    joined = refs_df.merge(
        blocks_df[["block_id", "asset_id"]], on="block_id", how="left"
    )
    joined = joined.merge(
        assets_df[["asset_id", "asset_type"]], on="asset_id", how="left"
    )

    # Filter valid usage
    valid = joined[joined["is_risk"] == False]

    if valid.empty:
        return None

    # Aggregate
    heatmap_data = (
        valid.groupby(["field_name", "asset_type"]).size().reset_index(name="count")
    )

    # Pivot for heatmap
    pivot = heatmap_data.pivot(
        index="field_name", columns="asset_type", values="count"
    ).fillna(0)

    # Get top 20 fields by total usage
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.nlargest(20, "total").drop("total", axis=1)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Oranges",
            text=pivot.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="References"),
        )
    )

    fig.update_layout(
        title="Field Usage Heatmap (Top 20 Fields)",
        xaxis_title="Asset Type",
        yaxis_title="Field Name",
        height=600,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0f172a"),
    )

    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)

    return fig


def create_usage_distribution_chart(refs_df):
    """Create distribution chart showing field usage patterns."""
    if refs_df.empty or refs_df[refs_df["is_risk"] == False].empty:
        return None

    valid_refs = refs_df[refs_df["is_risk"] == False]
    usage_counts = valid_refs["field_name"].value_counts().reset_index()
    usage_counts.columns = ["field_name", "count"]

    # Categorize
    def categorize(count):
        if count >= 20:
            return "Critical (20+)"
        elif count >= 10:
            return "High (10-19)"
        elif count >= 5:
            return "Medium (5-9)"
        else:
            return "Low (1-4)"

    usage_counts["category"] = usage_counts["count"].apply(categorize)

    category_counts = usage_counts["category"].value_counts().reset_index()
    category_counts.columns = ["category", "fields"]

    # Define order
    order = ["Critical (20+)", "High (10-19)", "Medium (5-9)", "Low (1-4)"]
    category_counts["category"] = pd.Categorical(
        category_counts["category"], categories=order, ordered=True
    )
    category_counts = category_counts.sort_values("category")

    color_map = {
        "Critical (20+)": "#ef4444",
        "High (10-19)": "#ff6a00",
        "Medium (5-9)": "#f59e0b",
        "Low (1-4)": "#10b981",
    }

    fig = px.bar(
        category_counts,
        x="category",
        y="fields",
        color="category",
        color_discrete_map=color_map,
        title="Field Usage Distribution",
        text="fields",
    )

    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(
        showlegend=False,
        xaxis_title="Usage Category",
        yaxis_title="Number of Fields",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0f172a"),
    )

    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)

    return fig


def create_top_fields_chart(refs_df, top_n=15):
    """Create horizontal bar chart of most-used fields."""
    if refs_df.empty or refs_df[refs_df["is_risk"] == False].empty:
        return None

    valid_refs = refs_df[refs_df["is_risk"] == False]
    top_fields = valid_refs["field_name"].value_counts().head(top_n).reset_index()
    top_fields.columns = ["field_name", "references"]

    fig = px.bar(
        top_fields,
        y="field_name",
        x="references",
        orientation="h",
        title=f"Top {top_n} Most Referenced Fields",
        color="references",
        color_continuous_scale="Oranges",
        text="references",
    )

    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Number of References",
        yaxis_title="",
        height=500,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0f172a"),
    )

    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)

    return fig


def create_asset_timeline(assets_df):
    """Create timeline of asset activity."""
    if assets_df.empty or "last_active" not in assets_df.columns:
        return None

    assets_clean = assets_df.dropna(subset=["last_active"]).copy()

    if assets_clean.empty:
        return None

    assets_clean["month"] = (
        assets_clean["last_active"].dt.to_period("M").dt.to_timestamp()
    )
    timeline = (
        assets_clean.groupby(["month", "asset_type"]).size().reset_index(name="count")
    )

    fig = px.line(
        timeline,
        x="month",
        y="count",
        color="asset_type",
        title="Asset Activity Over Time",
        markers=True,
        color_discrete_map={"Campaign": "#ff6a00", "Canvas": "#1e293b"},
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Active Assets",
        hovermode="x unified",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0f172a"),
        legend=dict(title="Asset Type"),
    )

    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)

    return fig


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    # Date Filter
    st.markdown("### 📅 Activity Period")

    if "last_active" in assets_df.columns and not assets_df["last_active"].isna().all():
        min_date = assets_df["last_active"].min()
        max_date = assets_df["last_active"].max()

        if pd.notnull(min_date) and pd.notnull(max_date):
            period_options = [
                "Current Week (Mon–Today)",
                "Last Week (Mon–Sun)",
                "Last 30 Days",
                "Last 60 Days",
                "Last 90 Days",
                "Last 180 Days",
                "Year to Date (YTD)",
                "Last 12 Months",
                "All Time",
            ]

            selected_period = st.selectbox(
                "Filter by activity period:",
                options=period_options,
                index=period_options.index("All Time"),
            )

            today_ts = pd.Timestamp.now().normalize()
            this_monday_ts = today_ts - pd.Timedelta(days=today_ts.weekday())
            min_ts = pd.Timestamp(min_date).normalize()
            max_ts = pd.Timestamp(max_date).normalize()

            if selected_period == "Current Week (Mon–Today)":
                start_ts = this_monday_ts
                end_ts = today_ts
            elif selected_period == "Last Week (Mon–Sun)":
                start_ts = this_monday_ts - pd.Timedelta(days=7)
                end_ts = start_ts + pd.Timedelta(days=6)
            elif selected_period == "Last 30 Days":
                start_ts = today_ts - pd.Timedelta(days=29)
                end_ts = today_ts
            elif selected_period == "Last 60 Days":
                start_ts = today_ts - pd.Timedelta(days=59)
                end_ts = today_ts
            elif selected_period == "Last 90 Days":
                start_ts = today_ts - pd.Timedelta(days=89)
                end_ts = today_ts
            elif selected_period == "Last 180 Days":
                start_ts = today_ts - pd.Timedelta(days=179)
                end_ts = today_ts
            elif selected_period == "Year to Date (YTD)":
                start_ts = pd.Timestamp(year=today_ts.year, month=1, day=1)
                end_ts = today_ts
            elif selected_period == "Last 12 Months":
                start_ts = today_ts - pd.DateOffset(months=12)
                end_ts = today_ts
            else:  # All Time
                start_ts = min_ts
                end_ts = max_ts

            start_date = start_ts.date()
            end_date = end_ts.date()

            assets_df = assets_df[
                (assets_df["last_active"].dt.date >= start_date)
                & (assets_df["last_active"].dt.date <= end_date)
            ]

            st.caption(f"{start_date:%Y/%m/%d} - {end_date:%Y/%m/%d}")
            st.success(f"✓ {len(assets_df)} assets in range")
        else:
            st.info("No date data available")
    else:
        st.warning("Run ETL to enable filtering")

    st.markdown("---")

    # Quick Stats
    st.markdown("### ⚡ Quick Stats")
    st.metric("Total Assets", len(assets_df), help="Campaigns + Canvases")

    if not refs_df.empty:
        ghost_count = len(
            refs_df[
                (refs_df["is_risk"] == True)
                & (refs_df["field_name"] != "location_guid")
            ]
        )
        st.metric(
            "Ghost References",
            ghost_count,
            delta="-" if ghost_count > 0 else None,
            help="Fields used but not in catalog",
        )

    st.markdown("---")
    st.markdown("**Last Updated:** " + datetime.now().strftime("%Y-%m-%d %H:%M"))

# ============================================================================
# MAIN CONTENT
# ============================================================================

PAGES = [
    "🏠 Overview",
    "🔍 Field Intelligence",
    "👨‍🍳 Catalog Fields",
    "🚨 Risk Center",
]
current_page = st.session_state.get("tas_page", PAGES[0])
if current_page not in PAGES:
    current_page = PAGES[0]

page = st.pills(
    "Navigation",
    PAGES,
    selection_mode="single",
    default=current_page,
    label_visibility="collapsed",
    key="tas_page",
)

if page is None:
    page = current_page

# --- PAGE 1: OVERVIEW ---
if page == "🏠 Overview":
    # Calculate governance score (used for internal context; not shown as a card)
    score, status = calculate_governance_score(catalog_df, refs_df, assets_df)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_campaigns = len(assets_df[assets_df["asset_type"] == "Campaign"])
        st.metric("Campaigns", total_campaigns, help="Active campaigns")

    with col2:
        total_canvases = len(assets_df[assets_df["asset_type"] == "Canvas"])
        st.metric("Canvases", total_canvases, help="Active canvases")

    with col3:
        if not catalog_df.empty and not refs_df.empty:
            used_fields = refs_df[refs_df["is_risk"] == False]["field_name"].nunique()
            saturation = (
                (used_fields / len(catalog_df) * 100) if len(catalog_df) > 0 else 0
            )
            st.metric("Utilization", f"{saturation:.0f}%", help="Catalog utilization")
        else:
            st.metric("Utilization", "N/A")

    with col4:
        st.metric("Catalog Fields", len(catalog_df), help="Total defined fields")

    st.markdown("---")

    # Key Insights
    st.header("💡 Governance Insights")

    insights = generate_governance_insights(catalog_df, refs_df, assets_df)

    cols = st.columns(len(insights))
    for idx, insight in enumerate(insights):
        with cols[idx]:
            alert_class = f"{insight['type']}-alert"
            st.markdown(
                f"""
                <div class="{alert_class}">
                    <h3 style="margin: 0 0 10px 0; font-size: 1.1rem;">{insight["icon"]} {insight["title"]}</h3>
                    <p style="margin: 0; color: var(--slate-600);">{insight["message"]}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Visual Analytics
    st.header("📊 Usage Intelligence")

    tab1, tab2, tab3 = st.tabs(["🔥 Top Fields", "📈 Distribution", "🗓️ Timeline"])

    with tab1:
        top_chart = create_top_fields_chart(refs_df, top_n=15)
        if top_chart:
            st.plotly_chart(top_chart, use_container_width=True)
        else:
            st.info("No field usage data available")

        st.markdown("### 📋 Field Impact Analysis")

        if not refs_df.empty and not blocks_df.empty and not assets_df.empty:
            # Join to get asset types
            joined = refs_df[refs_df["is_risk"] == False].merge(
                blocks_df[["block_id", "asset_id"]], on="block_id", how="left"
            )
            joined = joined.merge(
                assets_df[["asset_id", "asset_type"]], on="asset_id", how="left"
            )

            # Aggregate by field and asset type
            agg = (
                joined.groupby(["field_name", "asset_type"])["asset_id"]
                .nunique()
                .unstack(fill_value=0)
            )

            # Ensure columns exist
            for col in ["Campaign", "Canvas"]:
                if col not in agg.columns:
                    agg[col] = 0

            agg = agg.reset_index()
            agg["Total"] = agg["Campaign"] + agg["Canvas"]
            agg = agg.sort_values("Total", ascending=False).head(15)

            st.dataframe(
                agg[["field_name", "Campaign", "Canvas", "Total"]],
                use_container_width=True,
                column_config={
                    "field_name": "Field",
                    "Campaign": st.column_config.NumberColumn("Camps", format="%d"),
                    "Canvas": st.column_config.NumberColumn("Canvas", format="%d"),
                    "Total": st.column_config.ProgressColumn(
                        "Impact",
                        format="%d",
                        min_value=0,
                        max_value=int(agg["Total"].max()) if not agg.empty else 100,
                    ),
                },
                hide_index=True,
                height=500,
            )
        else:
            st.info("No data available for impact analysis")

    with tab2:
        heatmap = create_field_usage_heatmap(refs_df, assets_df, blocks_df)
        if heatmap:
            st.plotly_chart(heatmap, use_container_width=True)
        else:
            st.info("No heatmap data available")

    with tab3:
        timeline = create_asset_timeline(assets_df)
        if timeline:
            st.plotly_chart(timeline, use_container_width=True)
        else:
            st.info("No timeline data available")

        # Activity breakdown
        if not assets_df.empty and "last_active" in assets_df.columns:
            st.markdown("### 📅 Activity Breakdown")

            assets_dated = assets_df.dropna(subset=["last_active"])

            if not assets_dated.empty:
                now = pd.Timestamp.now()
                last_7d = assets_dated[
                    assets_dated["last_active"] > (now - pd.Timedelta(days=7))
                ]
                last_30d = assets_dated[
                    assets_dated["last_active"] > (now - pd.Timedelta(days=30))
                ]
                last_90d = assets_dated[
                    assets_dated["last_active"] > (now - pd.Timedelta(days=90))
                ]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Last 7 Days", len(last_7d))
                col2.metric("Last 30 Days", len(last_30d))
                col3.metric("Last 90 Days", len(last_90d))
                col4.metric("Total", len(assets_dated))

# --- PAGE 2: FIELD INTELLIGENCE ---
elif page == "🔍 Field Intelligence":
    if refs_df.empty or catalog_df.empty:
        st.warning(
            "No reference data available. Run ETL to populate field intelligence."
        )
    else:
        # Search and filter
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            search = st.text_input("🔍 Search fields", placeholder="Type to search...")

        with col2:
            risk_filter = st.selectbox("Risk Status", ["All", "Valid", "Ghost"])

        with col3:
            sort_by = st.selectbox("Sort By", ["Usage", "Name", "Risk"])

        # Process data
        field_analysis = (
            refs_df.groupby(["field_name", "is_risk"])
            .size()
            .reset_index(name="references")
        )

        # Merge with catalog
        field_analysis["in_catalog"] = field_analysis["field_name"].isin(
            catalog_df["field_name"] if "field_name" in catalog_df.columns else []
        )

        # Apply filters
        if search:
            field_analysis = field_analysis[
                field_analysis["field_name"].str.contains(search, case=False, na=False)
            ]

        if risk_filter == "Valid":
            field_analysis = field_analysis[field_analysis["is_risk"] == False]
        elif risk_filter == "Ghost":
            field_analysis = field_analysis[field_analysis["is_risk"] == True]

        # Sort
        if sort_by == "Usage":
            field_analysis = field_analysis.sort_values("references", ascending=False)
        elif sort_by == "Name":
            field_analysis = field_analysis.sort_values("field_name")
        elif sort_by == "Risk":
            field_analysis = field_analysis.sort_values(
                ["is_risk", "references"], ascending=[False, False]
            )

        # Display
        st.markdown("### 📊 Field Usage Matrix")

        # Add risk badges
        def format_risk(row):
            if row["is_risk"]:
                return '<span class="status-badge status-critical">GHOST</span>'
            else:
                return '<span class="status-badge status-success">VALID</span>'

        st.dataframe(
            field_analysis,
            use_container_width=True,
            column_config={
                "field_name": "Field Name",
                "references": st.column_config.ProgressColumn(
                    "References",
                    format="%d",
                    min_value=0,
                    max_value=int(field_analysis["references"].max())
                    if not field_analysis.empty
                    else 100,
                ),
                "is_risk": st.column_config.CheckboxColumn("Ghost"),
                "in_catalog": st.column_config.CheckboxColumn("In Catalog"),
            },
            hide_index=True,
            height=600,
        )

        # Field details section
        st.markdown("---")
        st.markdown("### 🔬 Field Details")

        selected_field = st.selectbox(
            "Select a field to analyze:", options=field_analysis["field_name"].unique()
        )

        if selected_field:
            field_refs = refs_df[refs_df["field_name"] == selected_field]

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total References", len(field_refs))
            col2.metric("Is Ghost", "Yes" if field_refs["is_risk"].iloc[0] else "No")

            # Get asset count
            if not blocks_df.empty and not assets_df.empty:
                field_blocks = field_refs.merge(
                    blocks_df[["block_id", "asset_id"]], on="block_id"
                )
                asset_count = field_blocks["asset_id"].nunique()
                col3.metric("Assets Using", asset_count)

                # Get asset types
                field_assets = field_blocks.merge(
                    assets_df[["asset_id", "asset_type"]], on="asset_id"
                )
                campaign_count = len(
                    field_assets[field_assets["asset_type"] == "Campaign"]
                )
                canvas_count = len(field_assets[field_assets["asset_type"] == "Canvas"])
                col4.metric("Campaigns/Canvases", f"{campaign_count}/{canvas_count}")

            # Show context snippets
            st.markdown("#### 📝 Usage Examples")
            if "context_snippet" in field_refs.columns:
                samples = field_refs["context_snippet"].dropna().head(5)
                for idx, snippet in enumerate(samples, 1):
                    with st.expander(f"Example {idx}"):
                        st.code(snippet, language="liquid")

# --- PAGE 3: CATALOG FIELDS ---
elif page == "👨‍🍳 Catalog Fields":
    if catalog_df.empty or "field_name" not in catalog_df.columns:
        st.warning("No catalog schema available. Run ETL to populate catalog fields.")
    else:
        raw_fields = catalog_df["field_name"].dropna().astype(str).str.strip()
        fields = (
            raw_fields[raw_fields.str.lower() != "id"]
            .drop_duplicates()
            .sort_values(kind="mergesort")
        )
        fields_df = pd.DataFrame({"Field": fields.values})

        search = st.text_input(
            "Search catalog fields",
            placeholder="Type to filter fields...",
        )

        if search:
            fields_df = fields_df[
                fields_df["Field"].str.contains(search, case=False, na=False)
            ]

        st.caption(f"{len(fields_df):,} fields")
        st.dataframe(
            fields_df,
            use_container_width=True,
            hide_index=True,
        )

# --- PAGE 3: RISK CENTER ---
elif page == "🚨 Risk Center":
    # Risk Overview
    st.header("⚠️ Active Risks")

    if refs_df.empty:
        st.info("No risk data available. Run ETL to populate risk center.")
    else:
        # Calculate risks
        ghost_fields = refs_df[
            (refs_df["is_risk"] == True) & (refs_df["field_name"] != "location_guid")
        ]
        unique_ghosts = ghost_fields["field_name"].nunique()
        total_ghost_refs = len(ghost_fields)

        # Risk metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Ghost Fields",
                unique_ghosts,
                delta=f"-{unique_ghosts}" if unique_ghosts > 0 else None,
                delta_color="inverse",
                help="Fields used but not in catalog",
            )

        with col2:
            st.metric(
                "Ghost References",
                total_ghost_refs,
                delta=f"-{total_ghost_refs}" if total_ghost_refs > 0 else None,
                delta_color="inverse",
                help="Total occurrences of ghost fields",
            )

        with col3:
            if not assets_df.empty:
                affected_assets = (
                    ghost_fields.merge(
                        blocks_df[["block_id", "asset_id"]], on="block_id"
                    )["asset_id"].nunique()
                    if not blocks_df.empty
                    else 0
                )
                st.metric(
                    "Affected Assets",
                    affected_assets,
                    delta=f"-{affected_assets}" if affected_assets > 0 else None,
                    delta_color="inverse",
                    help="Assets with ghost field references",
                )

        with col4:
            risk_level = (
                "🔴 Critical"
                if unique_ghosts > 10
                else "🟡 Warning"
                if unique_ghosts > 0
                else "🟢 Good"
            )
            st.metric("Risk Level", risk_level, help="Overall risk assessment")

        st.markdown("---")

        # Ghost Fields Detail
        if unique_ghosts > 0:
            st.header("👻 Ghost Fields Detail")

            st.markdown(
                """
                <div class="critical-alert">
                    <h3>⚠️ Critical: Ghost Fields Detected</h3>
                    <p>These fields are referenced in your assets but not defined in your catalog. 
                    This can cause runtime errors, data inconsistencies, and template failures.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Aggregate ghost field data
            ghost_agg = (
                ghost_fields.groupby("field_name")
                .agg({"field_name": "size", "context_snippet": "first"})
                .rename(columns={"field_name": "occurrences"})
                .reset_index()
            )

            # Get affected assets per ghost field
            if not blocks_df.empty and not assets_df.empty:
                ghost_assets = ghost_fields.merge(
                    blocks_df[["block_id", "asset_id"]], on="block_id"
                )
                ghost_assets = ghost_assets.merge(
                    assets_df[["asset_id", "asset_name", "asset_type"]], on="asset_id"
                )

                asset_counts = (
                    ghost_assets.groupby("field_name")["asset_id"]
                    .nunique()
                    .reset_index()
                )
                asset_counts.columns = ["field_name", "affected_assets"]

                ghost_agg = ghost_agg.merge(asset_counts, on="field_name")

            ghost_agg = ghost_agg.sort_values("occurrences", ascending=False)

            st.dataframe(
                ghost_agg[
                    ["field_name", "occurrences", "affected_assets", "context_snippet"]
                ],
                use_container_width=True,
                column_config={
                    "field_name": st.column_config.TextColumn(
                        "Ghost Field", width="medium"
                    ),
                    "occurrences": st.column_config.ProgressColumn(
                        "References",
                        format="%d",
                        min_value=0,
                        max_value=int(ghost_agg["occurrences"].max())
                        if not ghost_agg.empty
                        else 100,
                    ),
                    "affected_assets": st.column_config.NumberColumn(
                        "Assets", format="%d"
                    ),
                    "context_snippet": st.column_config.TextColumn(
                        "Example Usage", width="large"
                    ),
                },
                hide_index=True,
                height=500,
            )

            # Remediation recommendations
            st.markdown("---")
            st.header("🔧 Recommended Actions")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    """
                    <div class="info-alert">
                        <h3>📋 Immediate Actions</h3>
                        <ol>
                            <li>Add missing fields to catalog</li>
                            <li>Update asset templates with correct field names</li>
                            <li>Run validation tests before deployment</li>
                            <li>Set up automated drift detection</li>
                        </ol>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    """
                    <div class="warning-alert">
                        <h3>⚡ Prevention</h3>
                        <ul>
                            <li>Enforce catalog-first development</li>
                            <li>Use Content Blocks for reusability</li>
                            <li>Implement pre-deployment validation</li>
                            <li>Schedule regular governance audits</li>
                        </ul>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.success(
                "✅ No ghost fields detected. Your catalog governance is excellent!"
            )

        st.markdown("---")

        # Other risks
        st.header("📊 Additional Risk Factors")

        tab1, tab2, tab3 = st.tabs(["Stale Assets", "Low Utilization", "High Coupling"])

        with tab1:
            if (
                "last_active" in assets_df.columns
                and not assets_df["last_active"].isna().all()
            ):
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
                stale = assets_df[assets_df["last_active"] < cutoff]

                if not stale.empty:
                    st.warning(f"Found {len(stale)} assets inactive for 90+ days")
                    st.dataframe(
                        stale[["asset_name", "asset_type", "last_active"]].head(20),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.success("All assets have recent activity")
            else:
                st.info("No activity data available")

        with tab2:
            if not catalog_df.empty and not refs_df.empty:
                used_fields = set(
                    refs_df[refs_df["is_risk"] == False]["field_name"].unique()
                )
                all_fields = set(
                    catalog_df["field_name"].unique()
                    if "field_name" in catalog_df.columns
                    else []
                )
                unused = all_fields - used_fields

                if unused:
                    st.warning(f"{len(unused)} catalog fields are not being used")
                    unused_df = pd.DataFrame({"field_name": list(unused)})
                    st.dataframe(unused_df, use_container_width=True, hide_index=True)
                else:
                    st.success("All catalog fields are in use")
            else:
                st.info("No catalog data available")

        with tab3:
            if not refs_df.empty:
                high_usage = (
                    refs_df[refs_df["is_risk"] == False]["field_name"]
                    .value_counts()
                    .head(10)
                )

                if not high_usage.empty:
                    st.info("Fields with highest coupling (most references)")
                    coupling_df = high_usage.reset_index()
                    coupling_df.columns = ["field_name", "references"]

                    st.dataframe(
                        coupling_df,
                        use_container_width=True,
                        column_config={
                            "field_name": "Field Name",
                            "references": st.column_config.ProgressColumn(
                                "References",
                                format="%d",
                                min_value=0,
                                max_value=int(coupling_df["references"].max()),
                            ),
                        },
                        hide_index=True,
                    )
                    st.caption(
                        "⚠️ High coupling means changes to these fields require extensive testing"
                    )

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #94a3b8; padding: 20px;'>
        <p>Toast Audience Studio • Built with Streamlit</p>
        <p style='font-size: 0.8rem;'>Last ETL Run: Check data/tables for latest timestamps</p>
    </div>
""",
    unsafe_allow_html=True,
)
