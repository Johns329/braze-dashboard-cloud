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
    page_title="Braze Governance Intelligence",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# Enhanced Custom CSS - Cyber Security Theme
st.markdown(
    """
    <style>
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0E1117 0%, #1a1f2e 100%);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161B22 0%, #0d1117 100%);
        border-right: 2px solid #1f6feb;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    /* Card Containers */
    .governance-card {
        background: linear-gradient(135deg, #1E2329 0%, #161b22 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #30363d;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .governance-card:hover {
        border-color: #1f6feb;
        box-shadow: 0 8px 24px rgba(31, 111, 235, 0.2);
    }
    
    /* Alert Boxes */
    .critical-alert {
        background: linear-gradient(135deg, #1a0f0f 0%, #2d1616 100%);
        border-left: 4px solid #f85149;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(248, 81, 73, 0.2);
    }
    
    .warning-alert {
        background: linear-gradient(135deg, #1a1510 0%, #2d2416 100%);
        border-left: 4px solid #f0883e;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(240, 136, 62, 0.2);
    }
    
    .success-alert {
        background: linear-gradient(135deg, #0f1a0f 0%, #162d16 100%);
        border-left: 4px solid #3fb950;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(63, 185, 80, 0.2);
    }
    
    .info-alert {
        background: linear-gradient(135deg, #0f1519 0%, #16212d 100%);
        border-left: 4px solid #1f6feb;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.2);
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E2329 0%, #161b22 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #1f6feb;
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.3);
    }
    
    div[data-testid="stMetric"] label {
        color: #8b949e !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1f6feb !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(31, 111, 235, 0.3);
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
    }
    
    /* Headers */
    h1 {
        color: #ffffff !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 20px rgba(31, 111, 235, 0.3);
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin-top: 2rem !important;
        border-bottom: 2px solid #1f6feb;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #c9d1d9 !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
    }
    
    /* DataFrames */
    .dataframe {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    thead tr th {
        background-color: #161b22 !important;
        color: #1f6feb !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.85rem !important;
        border-bottom: 2px solid #1f6feb !important;
    }
    
    tbody tr:hover {
        background-color: #1c2128 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161b22;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1c2128;
        color: #8b949e;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        border: 1px solid #30363d;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f6feb !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.4);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1f6feb 0%, #1158c7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.5);
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 2px;
    }
    
    .status-critical {
        background-color: #f851491a;
        color: #f85149;
        border: 1px solid #f85149;
    }
    
    .status-warning {
        background-color: #f0883e1a;
        color: #f0883e;
        border: 1px solid #f0883e;
    }
    
    .status-success {
        background-color: #3fb9501a;
        color: #3fb950;
        border: 1px solid #3fb950;
    }
    
    .status-info {
        background-color: #1f6feb1a;
        color: #1f6feb;
        border: 1px solid #1f6feb;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%);
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
            colorscale="Blues",
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
        plot_bgcolor="#161b22",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
    )

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
        "Critical (20+)": "#f85149",
        "High (10-19)": "#f0883e",
        "Medium (5-9)": "#58a6ff",
        "Low (1-4)": "#3fb950",
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
        plot_bgcolor="#161b22",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
    )

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
        color_continuous_scale="Blues",
        text="references",
    )

    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Number of References",
        yaxis_title="",
        height=500,
        showlegend=False,
        plot_bgcolor="#161b22",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
    )

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
        color_discrete_map={"Campaign": "#58a6ff", "Canvas": "#3fb950"},
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Active Assets",
        hovermode="x unified",
        height=400,
        plot_bgcolor="#161b22",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        legend=dict(title="Asset Type"),
    )

    return fig


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("🛡️ Braze Governance")
    st.markdown("**Intelligence Hub**")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Overview", "🔍 Field Intelligence", "🚨 Risk Center", "📊 Analytics"],
        label_visibility="collapsed",
    )

    st.markdown("---")

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

# --- PAGE 1: OVERVIEW ---
if page == "🏠 Overview":
    st.title("🛡️ Governance Overview")
    st.markdown("**Real-time catalog health monitoring and governance intelligence**")

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
            st.metric("Saturation", f"{saturation:.0f}%", help="Catalog utilization")
        else:
            st.metric("Saturation", "N/A")

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
                    <p style="margin: 0; color: #c9d1d9;">{insight["message"]}</p>
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
    st.title("🔍 Field Intelligence Center")
    st.markdown("**Deep dive into catalog field usage and dependencies**")

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

# --- PAGE 3: RISK CENTER ---
elif page == "🚨 Risk Center":
    st.title("🚨 Risk & Compliance Center")
    st.markdown("**Monitor and manage governance risks**")

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

# --- PAGE 4: ANALYTICS ---
elif page == "📊 Analytics":
    st.title("📊 Governance Analytics")
    st.markdown("**Advanced insights and trend analysis**")

    if refs_df.empty or assets_df.empty:
        st.warning("No analytics data available. Run ETL to populate analytics.")
    else:
        # Summary statistics
        st.header("📈 Key Statistics")

        col1, col2, col3, col4, col5 = st.columns(5)

        total_refs = len(refs_df[refs_df["is_risk"] == False])
        col1.metric("Total References", f"{total_refs:,}")

        unique_fields = refs_df[refs_df["is_risk"] == False]["field_name"].nunique()
        col2.metric("Unique Fields", unique_fields)

        if not catalog_df.empty:
            coverage = (
                (unique_fields / len(catalog_df) * 100) if len(catalog_df) > 0 else 0
            )
            col3.metric("Catalog Coverage", f"{coverage:.1f}%")

        avg_refs_per_field = total_refs / unique_fields if unique_fields > 0 else 0
        col4.metric("Avg Refs/Field", f"{avg_refs_per_field:.1f}")

        total_assets = len(assets_df)
        col5.metric("Total Assets", total_assets)

        st.markdown("---")

        # Detailed analytics tabs
        analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs(
            ["📊 Usage Patterns", "🔗 Dependencies", "📅 Trends"]
        )

        with analytics_tab1:
            col1, col2 = st.columns(2)

            with col1:
                dist_chart = create_usage_distribution_chart(refs_df)
                if dist_chart:
                    st.plotly_chart(dist_chart, use_container_width=True)

            with col2:
                # Field concentration
                if not refs_df[refs_df["is_risk"] == False].empty:
                    field_refs = refs_df[refs_df["is_risk"] == False][
                        "field_name"
                    ].value_counts()

                    # Calculate concentration
                    top_10_refs = field_refs.head(10).sum()
                    total_refs = field_refs.sum()
                    concentration = (
                        (top_10_refs / total_refs * 100) if total_refs > 0 else 0
                    )

                    st.markdown("### 🎯 Field Concentration")
                    st.metric(
                        "Top 10 Fields",
                        f"{concentration:.1f}%",
                        help="Percentage of total references from top 10 fields",
                    )

                    # Pareto chart
                    cumsum = (
                        field_refs.cumsum() / field_refs.sum() * 100
                    ).reset_index()
                    cumsum.columns = ["field_name", "cumulative_pct"]
                    cumsum["rank"] = range(1, len(cumsum) + 1)

                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=cumsum["rank"],
                            y=cumsum["cumulative_pct"],
                            mode="lines+markers",
                            name="Cumulative %",
                            line=dict(color="#1f6feb", width=2),
                        )
                    )
                    fig.add_hline(
                        y=80,
                        line_dash="dash",
                        line_color="#f0883e",
                        annotation_text="80% Rule",
                    )

                    fig.update_layout(
                        title="Cumulative Field Usage (Pareto)",
                        xaxis_title="Field Rank",
                        yaxis_title="Cumulative %",
                        height=400,
                        plot_bgcolor="#161b22",
                        paper_bgcolor="#0d1117",
                        font=dict(color="#c9d1d9"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with analytics_tab2:
            if not blocks_df.empty and not assets_df.empty:
                st.markdown("### 🔗 Field-Asset Dependency Network")

                # Build dependency matrix
                joined = refs_df[refs_df["is_risk"] == False].merge(
                    blocks_df[["block_id", "asset_id"]], on="block_id"
                )
                joined = joined.merge(
                    assets_df[["asset_id", "asset_name"]], on="asset_id"
                )

                # Create network visualization data
                dependency_matrix = (
                    joined.groupby(["field_name", "asset_name"])
                    .size()
                    .reset_index(name="weight")
                )

                # Show top dependencies
                top_deps = dependency_matrix.nlargest(20, "weight")

                fig = px.scatter(
                    top_deps,
                    x="field_name",
                    y="asset_name",
                    size="weight",
                    color="weight",
                    color_continuous_scale="Blues",
                    title="Top 20 Field-Asset Dependencies",
                )

                fig.update_layout(
                    height=600,
                    plot_bgcolor="#161b22",
                    paper_bgcolor="#0d1117",
                    font=dict(color="#c9d1d9"),
                    xaxis={"tickangle": 45},
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No dependency data available")

        with analytics_tab3:
            timeline = create_asset_timeline(assets_df)
            if timeline:
                st.plotly_chart(timeline, use_container_width=True)

            # Additional trend metrics
            if (
                "last_active" in assets_df.columns
                and not assets_df["last_active"].isna().all()
            ):
                st.markdown("### 📊 Activity Trends")

                assets_dated = assets_df.dropna(subset=["last_active"]).copy()
                assets_dated["week"] = (
                    assets_dated["last_active"].dt.to_period("W").dt.start_time
                )

                weekly_activity = (
                    assets_dated.groupby(["week", "asset_type"])
                    .size()
                    .reset_index(name="count")
                )

                fig = px.area(
                    weekly_activity,
                    x="week",
                    y="count",
                    color="asset_type",
                    title="Weekly Activity Trend",
                    color_discrete_map={"Campaign": "#58a6ff", "Canvas": "#3fb950"},
                )

                fig.update_layout(
                    height=400,
                    plot_bgcolor="#161b22",
                    paper_bgcolor="#0d1117",
                    font=dict(color="#c9d1d9"),
                    hovermode="x unified",
                )

                st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #8b949e; padding: 20px;'>
        <p>Braze Governance Intelligence Hub • Built with Streamlit</p>
        <p style='font-size: 0.8rem;'>Last ETL Run: Check data/tables for latest timestamps</p>
    </div>
""",
    unsafe_allow_html=True,
)
