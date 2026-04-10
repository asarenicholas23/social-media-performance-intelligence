import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import io

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Social Media Performance Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 18px 20px;
        border-left: 4px solid #4C72B0;
    }
    .metric-label {
        color: #9ca3af;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        margin-top: 6px;
    }
    .metric-sub {
        color: #6b7280;
        font-size: 11px;
        margin-top: 4px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #e5e7eb;
        margin-top: 8px;
        margin-bottom: 2px;
    }
    .section-subtitle {
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 16px;
    }
    .insight-box {
        background: #1a2035;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13px;
        color: #9ca3af;
        margin-top: 8px;
    }
    .insight-box b { color: #e5e7eb; }
    .warning-box {
        background: #2d1f1f;
        border: 1px solid #7f3f3f;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 12px;
        color: #f87171;
        margin-top: 6px;
    }
    div[data-testid="stSidebar"] { background-color: #1a1d2e; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
PLATFORM_COLORS = {
    "Instagram": "#E1306C",
    "TikTok":    "#69C9D0",
    "Facebook":  "#1877F2",
    "Linkedin":  "#0A66C2",
}

POST_TYPE_MAP = {
    "reel": "Reel", "reels": "Reel",
    "video": "Video", "videos": "Video",
    "photo": "Photo", "photos": "Photo", "image": "Photo",
    "carousel": "Carousel", "text": "Text",
}

RANK_METRICS = {
    "Engagement Rate":        ("engagement_rate",        ".2%",  "Rate at which people interact relative to impressions"),
    "Total Engagement":       ("total_engagement",       ",.0f", "Sum of likes, comments, shares and saves"),
    "Impressions":            ("impressions",            ",.0f", "Total times the post was seen"),
    "Reach":                  ("reach",                  ",.0f", "Unique accounts that saw the post (not available on TikTok)"),
    "Likes":                  ("likes",                  ",.0f", "Total likes"),
    "Comments":               ("comments",               ",.0f", "Total comments"),
    "Shares":                 ("shares",                 ",.0f", "Total shares"),
    "Saves":                  ("saves",                  ",.0f", "Total saves (Instagram & TikTok only)"),
    "Profile Visits":         ("profile_visits",         ",.0f", "Profile visits driven by the post"),
    "Follow Conversion Rate": ("follow_conversion_rate", ".4f",  "⚠ Sparse — only 15 posts drove follows"),
}

DOW_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

CHART_LAYOUT = dict(
    plot_bgcolor="#1e2130",
    paper_bgcolor="#1e2130",
    font_color="#e5e7eb",
    title_font_size=13,
    margin=dict(l=10, r=20, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font_size=11),
)
AXIS_STYLE = dict(gridcolor="#2d3748", zerolinecolor="#2d3748")


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data(source):
    df = pd.read_csv(source)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")

    df["post_type"] = (
        df["post_type"].str.strip().str.lower()
        .map(POST_TYPE_MAP)
        .fillna(df["post_type"].str.strip().str.title())
    )

    num_cols = ["impressions","reach","likes","comments","shares","saves",
                "follows","profile_visits","total_engagement",
                "engagement_rate","save_rate","follow_conversion_rate"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "total_engagement" not in df.columns:
        df["total_engagement"] = (
            df.get("likes", pd.Series(0, index=df.index)).fillna(0)
            + df.get("comments", pd.Series(0, index=df.index)).fillna(0)
            + df.get("shares", pd.Series(0, index=df.index)).fillna(0)
            + df.get("saves", pd.Series(0, index=df.index)).fillna(0)
        )
    if "engagement_rate" not in df.columns:
        df["engagement_rate"] = df["total_engagement"] / df["impressions"].replace(0, np.nan)

    df = df[df["impressions"] > 0].copy()
    df["month_dt"] = df["date_posted"].dt.to_period("M").dt.to_timestamp()
    df["month_str"] = df["date_posted"].dt.strftime("%b %Y")
    df["caption_short"] = (
        df["caption"].fillna("").str.strip().str[:60]
        .apply(lambda x: x + "…" if len(x) == 60 else x)
    )
    return df


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 SM Intelligence")
    st.markdown("---")

    uploaded = st.file_uploader("Upload metrics CSV", type=["csv"])
    df = load_data(uploaded if uploaded else "data/processed/metrics_SM_data.csv")
    if uploaded:
        st.success(f"✓ {len(df)} posts loaded")

    st.markdown("---")
    st.markdown("### Filters")

    all_platforms = sorted(df["platform"].dropna().unique())
    sel_platforms = st.multiselect("Platform", all_platforms, default=all_platforms)

    all_types = sorted(df["post_type"].dropna().unique())
    sel_types = st.multiselect("Post Type", all_types, default=all_types)

    date_min = df["date_posted"].min().date()
    date_max = df["date_posted"].max().date()
    sel_dates = st.date_input("Date Range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)

    st.markdown("---")
    st.caption("Social Media Performance Intelligence · v1.0")

# ── Figure registry — collects all charts for HTML report ─────────────────────
_figures = {}  # {label: fig}

def register(label, fig):
    """Register a figure and return it (so calls can be chained inline)."""
    _figures[label] = fig
    return fig


# ── Download helpers ───────────────────────────────────────────────────────────
def df_to_csv_bytes(dataframe):
    """Return a dataframe as UTF-8 CSV bytes for st.download_button."""
    return dataframe.to_csv(index=False).encode("utf-8")


def build_html_report(dataframe, figures_dict):
    """
    Build a self-contained HTML report with:
    - key summary stats
    - all Plotly charts embedded as interactive HTML divs
    - full filtered data table
    """
    rows = []
    rows.append("""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>Social Media Performance Intelligence Report</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f1117; color: #e5e7eb; margin: 0; padding: 32px; }
  h1   { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
  h2   { font-size: 16px; font-weight: 600; color: #9ca3af;
         border-bottom: 1px solid #2d3748; padding-bottom: 8px; margin-top: 40px; }
  .meta { font-size: 13px; color: #6b7280; margin-bottom: 32px; }
  .kpi-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 32px; }
  .kpi  { background: #1e2130; border-left: 4px solid #4C72B0; border-radius: 10px;
          padding: 16px 20px; min-width: 160px; }
  .kpi-label { font-size: 11px; color: #9ca3af; text-transform: uppercase;
               letter-spacing: 0.06em; }
  .kpi-value { font-size: 24px; font-weight: 700; margin-top: 4px; }
  .chart-wrap { background: #1e2130; border-radius: 10px; padding: 16px;
                margin-bottom: 24px; }
  table { width: 100%; border-collapse: collapse; font-size: 12px;
          background: #1e2130; border-radius: 8px; overflow: hidden; }
  th    { background: #2d3748; padding: 10px 12px; text-align: left;
          color: #9ca3af; font-weight: 600; }
  td    { padding: 8px 12px; border-bottom: 1px solid #2d3748; }
  tr:last-child td { border-bottom: none; }
  .warn { background: #2d1f1f; border: 1px solid #7f3f3f; border-radius: 6px;
          padding: 8px 12px; font-size: 12px; color: #f87171; margin-bottom: 16px; }
  .footer { margin-top: 48px; font-size: 11px; color: #4b5563; text-align: center; }
</style>
</head>
<body>
""")

    # Header
    from datetime import datetime
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_range = f"{dataframe['date_posted'].min().strftime('%b %Y')} – {dataframe['date_posted'].max().strftime('%b %Y')}"
    rows.append(f"<h1>📊 Social Media Performance Intelligence</h1>")
    rows.append(f"<p class='meta'>Generated: {generated} &nbsp;·&nbsp; {len(dataframe)} posts &nbsp;·&nbsp; {date_range}</p>")

    # KPI strip
    best_platform = dataframe.groupby("platform")["engagement_rate"].median().idxmax()
    rows.append("<div class='kpi-row'>")
    for label, value in [
        ("Total Posts",       f"{len(dataframe):,}"),
        ("Total Impressions", f"{dataframe['impressions'].sum():,.0f}"),
        ("Total Engagement",  f"{dataframe['total_engagement'].sum():,.0f}"),
        ("Median Eng. Rate",  f"{dataframe['engagement_rate'].median():.2%}"),
        ("Best Platform",     best_platform),
    ]:
        rows.append(f"<div class='kpi'><div class='kpi-label'>{label}</div>"
                    f"<div class='kpi-value'>{value}</div></div>")
    rows.append("</div>")

    # Charts
    rows.append("<h2>Charts</h2>")
    rows.append("<p style='font-size:12px;color:#6b7280;margin-bottom:16px;'>"
                "All charts are fully interactive — hover, zoom, and click to explore.</p>")
    for title, fig in figures_dict.items():
        html_div = pio.to_html(fig, full_html=False, include_plotlyjs="cdn",
                               config={"displayModeBar": True, "displaylogo": False})
        rows.append(f"<div class='chart-wrap'>{html_div}</div>")

    # Full data table
    rows.append("<h2>Full Filtered Dataset</h2>")
    display_df = dataframe[[
        "date_posted","platform","post_type","impressions","reach",
        "likes","comments","shares","saves","total_engagement",
        "engagement_rate","save_rate","follow_conversion_rate","caption_short"
    ]].copy()
    display_df["date_posted"] = display_df["date_posted"].dt.strftime("%Y-%m-%d")
    display_df["engagement_rate"] = display_df["engagement_rate"].map(
        lambda x: f"{x:.2%}" if pd.notna(x) else "")
    display_df.columns = [
        "Date","Platform","Type","Impressions","Reach",
        "Likes","Comments","Shares","Saves","Total Eng.",
        "Eng. Rate","Save Rate","Follow Conv.","Caption"
    ]

    rows.append("<table><thead><tr>")
    for col in display_df.columns:
        rows.append(f"<th>{col}</th>")
    rows.append("</tr></thead><tbody>")
    for _, row in display_df.iterrows():
        rows.append("<tr>")
        for val in row:
            v = "" if pd.isna(val) else str(val)
            rows.append(f"<td>{v}</td>")
        rows.append("</tr>")
    rows.append("</tbody></table>")

    rows.append("<div class='footer'>Social Media Performance Intelligence · auto-generated report</div>")
    rows.append("</body></html>")

    return "\n".join(rows).encode("utf-8")


# ── Apply filters ──────────────────────────────────────────────────────────────
dff = df[df["platform"].isin(sel_platforms) & df["post_type"].isin(sel_types)].copy()
if len(sel_dates) == 2:
    dff = dff[
        (dff["date_posted"].dt.date >= sel_dates[0]) &
        (dff["date_posted"].dt.date <= sel_dates[1])
    ]

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# Social Media Performance Intelligence")
st.markdown(
    f"**{len(dff)} posts** · **{dff['platform'].nunique()} platforms** · "
    f"{dff['date_posted'].min().strftime('%b %Y')} – {dff['date_posted'].max().strftime('%b %Y')}"
)
st.markdown("---")

if dff.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# ── KPI strip ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
for col, label, value, sub in [
    (k1, "Total Posts",       f"{len(dff):,}",                         "All platforms combined"),
    (k2, "Total Impressions", f"{dff['impressions'].sum():,.0f}",       "Times content was seen"),
    (k3, "Total Engagement",  f"{dff['total_engagement'].sum():,.0f}",  "Likes + comments + shares + saves"),
    (k4, "Median Eng. Rate",  f"{dff['engagement_rate'].median():.2%}", "Cross-platform benchmark"),
    (k5, "Best Platform",     dff.groupby("platform")["engagement_rate"].median().idxmax(), "By median engagement rate"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡  Q1 · Platform Performance",
    "🎨  Q2 · Content by Platform",
    "📅  Q3 · Best Days to Post",
    "📈  Q4 · Additional Metrics",
    "🏆  Top Posts",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Platform Performance
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-title">Which platform gives us the most?</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Broken down by Awareness, Engagement, and Sales/Conversion</p>', unsafe_allow_html=True)

    # 1a. Awareness
    st.markdown("#### 📡 Awareness — How many people are we reaching?")
    c1, c2 = st.columns(2)

    with c1:
        imp_data = (
            dff.groupby("platform")["impressions"]
            .median().reset_index()
            .sort_values("impressions", ascending=True)
        )
        fig = px.bar(imp_data, x="impressions", y="platform", orientation="h",
                     color="platform", color_discrete_map=PLATFORM_COLORS,
                     title="Median Impressions per Post",
                     labels={"impressions": "Median Impressions", "platform": ""},
                     text="impressions")
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        fig.update_xaxes(**AXIS_STYLE)
        fig.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_01_fig", fig), use_container_width=True)

    with c2:
        reach_data = (
            dff[dff["reach"].notna()]
            .groupby("platform")["reach"]
            .median().reset_index()
            .sort_values("reach", ascending=True)
        )
        fig2 = px.bar(reach_data, x="reach", y="platform", orientation="h",
                      color="platform", color_discrete_map=PLATFORM_COLORS,
                      title="Median Reach per Post",
                      labels={"reach": "Median Reach", "platform": ""},
                      text="reach")
        fig2.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig2.update_layout(showlegend=False, **CHART_LAYOUT)
        fig2.update_xaxes(**AXIS_STYLE)
        fig2.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_02_fig2", fig2), use_container_width=True)
        st.markdown('<div class="warning-box">⚠ TikTok does not report Reach separately — excluded from this chart</div>', unsafe_allow_html=True)

    # 1b. Engagement
    st.markdown("#### 💬 Engagement — Which platform drives the most interaction?")
    c3, c4 = st.columns(2)

    with c3:
        er_data = (
            dff.groupby("platform")["engagement_rate"]
            .median().reset_index()
            .sort_values("engagement_rate", ascending=True)
        )
        fig3 = px.bar(er_data, x="engagement_rate", y="platform", orientation="h",
                      color="platform", color_discrete_map=PLATFORM_COLORS,
                      title="Median Engagement Rate by Platform",
                      labels={"engagement_rate": "Median Engagement Rate", "platform": ""},
                      text="engagement_rate")
        fig3.update_traces(texttemplate="%{text:.2%}", textposition="outside")
        fig3.update_layout(showlegend=False, **CHART_LAYOUT)
        fig3.update_xaxes(tickformat=".0%", **AXIS_STYLE)
        fig3.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_03_fig3", fig3), use_container_width=True)

    with c4:
        eng_comp = (
            dff.groupby("platform")[["likes","comments","shares","saves"]]
            .median().fillna(0).reset_index()
            .melt(id_vars="platform", var_name="component", value_name="median")
        )
        fig4 = px.bar(eng_comp, x="platform", y="median", color="component",
                      barmode="stack", title="Median Engagement Components",
                      labels={"median": "Median Count", "platform": "", "component": ""},
                      color_discrete_sequence=["#4C72B0","#DD8452","#55A868","#C44E52"])
        fig4.update_layout(**CHART_LAYOUT)
        fig4.update_xaxes(**AXIS_STYLE)
        fig4.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_04_fig4", fig4), use_container_width=True)

    # 1c. Sales / Conversion
    st.markdown("#### 💰 Sales / Conversion — Which platform drives the most follows?")
    st.markdown('<div class="warning-box">⚠ Follow data is only available for Instagram (108 posts, 15 with actual follows). This is the closest proxy to conversion in the current dataset. Link clicks or DMs would be stronger signals if captured in future.</div>', unsafe_allow_html=True)

    ig_follows = dff[(dff["platform"] == "Instagram") & dff["follow_conversion_rate"].notna()].copy()
    if not ig_follows.empty:
        c5, c6 = st.columns(2)
        with c5:
            fig5 = px.histogram(ig_follows, x="follow_conversion_rate", nbins=30,
                                title="Follow Conversion Rate Distribution (Instagram)",
                                labels={"follow_conversion_rate": "Follow Conversion Rate"},
                                color_discrete_sequence=["#E1306C"])
            fig5.update_layout(**CHART_LAYOUT)
            fig5.update_xaxes(tickformat=".2%", **AXIS_STYLE)
            fig5.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(register(f"chart_05_fig5", fig5), use_container_width=True)

        with c6:
            top_follow = ig_follows.nlargest(10, "follow_conversion_rate")[
                ["date_posted","post_type","impressions","follows","follow_conversion_rate","caption_short"]
            ].copy()
            top_follow["date_posted"] = top_follow["date_posted"].dt.strftime("%Y-%m-%d")
            top_follow["follow_conversion_rate"] = top_follow["follow_conversion_rate"].map("{:.4f}".format)
            top_follow.columns = ["Date","Type","Impressions","Follows","Conv. Rate","Caption"]
            top_follow = top_follow.reset_index(drop=True)
            top_follow.index += 1
            st.markdown("**Top 10 posts by follow conversion**")
            st.dataframe(top_follow, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # Platform summary CSV
    plat_summary = dff.groupby("platform").agg(
        posts=("post_id","count") if "post_id" in dff.columns else ("impressions","count"),
        median_impressions=("impressions","median"),
        median_engagement_rate=("engagement_rate","median"),
        total_engagement=("total_engagement","sum"),
        median_likes=("likes","median"),
        median_comments=("comments","median"),
        median_shares=("shares","median"),
    ).round(4).reset_index()
    st.download_button(
        label="⬇ Download Platform Summary (CSV)",
        data=df_to_csv_bytes(plat_summary),
        file_name="platform_summary.csv",
        mime="text/csv",
        use_container_width=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Content by Platform
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-title">Which post type works best on each platform?</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Toggle between Awareness and Engagement to see what each format delivers</p>', unsafe_allow_html=True)

    view = st.radio("View by:", ["Awareness (Impressions)", "Engagement (Rate)"],
                    horizontal=True, key="content_view")

    metric_col = "impressions" if "Awareness" in view else "engagement_rate"
    label      = "Median Impressions" if "Awareness" in view else "Median Engagement Rate"

    # Per-platform charts
    platforms_in_data = sorted(dff["platform"].unique())
    p_cols = st.columns(len(platforms_in_data))

    for col, platform in zip(p_cols, platforms_in_data):
        sub = dff[dff["platform"] == platform]
        pt_data = (
            sub.groupby("post_type")[metric_col]
            .median().reset_index()
            .sort_values(metric_col, ascending=True)
            .dropna()
        )
        color = PLATFORM_COLORS.get(platform, "#888")
        fig = px.bar(pt_data, x=metric_col, y="post_type", orientation="h",
                     title=platform,
                     labels={metric_col: label, "post_type": ""},
                     text=metric_col,
                     color_discrete_sequence=[color])
        if "Rate" in view:
            fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
            fig.update_xaxes(tickformat=".0%", **AXIS_STYLE)
        else:
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            fig.update_xaxes(**AXIS_STYLE)
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        fig.update_yaxes(**AXIS_STYLE)
        col.plotly_chart(fig, use_container_width=True)

    # Heatmap
    st.markdown("#### Full Heatmap: Platform × Post Type")
    pivot = dff.groupby(["platform","post_type"])[metric_col].median().unstack("post_type").round(4)
    text_fmt = ".0f" if "Awareness" in view else ".2%"
    fig_heat = px.imshow(pivot, text_auto=text_fmt, color_continuous_scale="YlOrRd",
                         title=f"{label}: Platform × Post Type",
                         labels=dict(x="Post Type", y="Platform", color=label),
                         aspect="auto")
    fig_heat.update_layout(**CHART_LAYOUT)
    st.plotly_chart(register(f"chart_06_fig_heat", fig_heat), use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>Important:</b> Each platform only uses certain post types — TikTok is 100% Video,
    Instagram has no Video or Text, LinkedIn has no Reels. Comparisons are only valid
    <i>within</i> each platform, not across them.
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    content_summary = (
        dff.groupby(["platform","post_type"])
        .agg(posts=("impressions","count"),
             median_impressions=("impressions","median"),
             median_engagement_rate=("engagement_rate","median"))
        .round(4).reset_index()
    )
    st.download_button(
        label="⬇ Download Content Summary (CSV)",
        data=df_to_csv_bytes(content_summary),
        file_name="content_by_platform.csv",
        mime="text/csv",
        use_container_width=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Best Days to Post
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-title">Which day is best to post?</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Based on median engagement rate by day of week, per platform</p>', unsafe_allow_html=True)

    st.markdown('<div class="warning-box">⚠ Time of day is not recorded in the current dataset — only the date is captured. To unlock best-time-of-day analysis, start logging the hour of posting going forward.</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Overall
    dow_overall = (
        dff.groupby("day_of_week")["engagement_rate"]
        .agg(["median","count"]).reindex(DOW_ORDER).reset_index()
        .rename(columns={"median":"median_er","count":"n_posts"})
    )
    fig_dow = px.bar(dow_overall, x="day_of_week", y="median_er",
                     title="Overall: Median Engagement Rate by Day of Week",
                     labels={"median_er": "Median Engagement Rate", "day_of_week": ""},
                     text="median_er", color="median_er",
                     color_continuous_scale="Blues")
    fig_dow.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig_dow.update_layout(showlegend=False, coloraxis_showscale=False, **CHART_LAYOUT)
    fig_dow.update_xaxes(**AXIS_STYLE)
    fig_dow.update_yaxes(tickformat=".0%", **AXIS_STYLE)
    st.plotly_chart(register(f"chart_07_fig_dow", fig_dow), use_container_width=True)

    # Per platform
    st.markdown("#### By Platform")
    p_cols2 = st.columns(len(platforms_in_data))
    for col, platform in zip(p_cols2, sorted(dff["platform"].unique())):
        sub = dff[dff["platform"] == platform]
        dow_p = (
            sub.groupby("day_of_week")["engagement_rate"]
            .median().reindex(DOW_ORDER).reset_index()
        )
        color = PLATFORM_COLORS.get(platform, "#888")
        fig_p = px.bar(dow_p, x="day_of_week", y="engagement_rate",
                       title=platform,
                       labels={"engagement_rate": "Median ER", "day_of_week": ""},
                       color_discrete_sequence=[color])
        fig_p.update_layout(showlegend=False, **CHART_LAYOUT)
        fig_p.update_xaxes(tickangle=45, **AXIS_STYLE)
        fig_p.update_yaxes(tickformat=".0%", **AXIS_STYLE)
        col.plotly_chart(fig_p, use_container_width=True)

    # Monthly trend
    st.markdown("#### Performance Over Time")
    monthly = (
        dff.groupby(["month_dt","platform"])["engagement_rate"]
        .median().reset_index().sort_values("month_dt")
    )
    monthly["month_label"] = monthly["month_dt"].dt.strftime("%b %Y")
    fig_trend = px.line(monthly, x="month_label", y="engagement_rate", color="platform",
                        color_discrete_map=PLATFORM_COLORS, markers=True,
                        title="Monthly Median Engagement Rate by Platform",
                        labels={"engagement_rate": "Median ER", "month_label": "", "platform": ""})
    fig_trend.update_layout(**CHART_LAYOUT)
    fig_trend.update_xaxes(**AXIS_STYLE)
    fig_trend.update_yaxes(tickformat=".0%", **AXIS_STYLE)
    st.plotly_chart(register(f"chart_08_fig_trend", fig_trend), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    dow_summary = (
        dff.groupby(["platform","day_of_week"])["engagement_rate"]
        .agg(["median","count"]).round(4).reset_index()
        .rename(columns={"median":"median_er","count":"n_posts"})
    )
    st.download_button(
        label="⬇ Download Day-of-Week Summary (CSV)",
        data=df_to_csv_bytes(dow_summary),
        file_name="best_days_to_post.csv",
        mime="text/csv",
        use_container_width=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Additional Metrics
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-title">Additional performance metrics</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Save rate, profile visits, impressions spread, and posting consistency</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        save_data = (
            dff[dff["save_rate"].notna() & (dff["save_rate"] > 0)]
            .groupby("platform")["save_rate"]
            .median().reset_index()
            .sort_values("save_rate", ascending=True)
        )
        fig_save = px.bar(save_data, x="save_rate", y="platform", orientation="h",
                          color="platform", color_discrete_map=PLATFORM_COLORS,
                          title="Median Save Rate by Platform",
                          labels={"save_rate": "Save Rate", "platform": ""},
                          text="save_rate")
        fig_save.update_traces(texttemplate="%{text:.4f}", textposition="outside")
        fig_save.update_layout(showlegend=False, **CHART_LAYOUT)
        fig_save.update_xaxes(**AXIS_STYLE)
        fig_save.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_09_fig_save", fig_save), use_container_width=True)
        st.markdown('<div class="insight-box"><b>Save Rate</b> = saves ÷ impressions. Only available on Instagram and TikTok. A high save rate means content people bookmark to return to — a strong quality signal.</div>', unsafe_allow_html=True)

    with c2:
        visit_data = (
            dff[dff["profile_visits"].notna()]
            .groupby("platform")["profile_visits"]
            .median().reset_index()
            .sort_values("profile_visits", ascending=True)
        )
        fig_visits = px.bar(visit_data, x="profile_visits", y="platform", orientation="h",
                            color="platform", color_discrete_map=PLATFORM_COLORS,
                            title="Median Profile Visits per Post",
                            labels={"profile_visits": "Median Profile Visits", "platform": ""},
                            text="profile_visits")
        fig_visits.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_visits.update_layout(showlegend=False, **CHART_LAYOUT)
        fig_visits.update_xaxes(**AXIS_STYLE)
        fig_visits.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_10_fig_visits", fig_visits), use_container_width=True)
        st.markdown('<div class="insight-box"><b>Profile Visits</b> signals discovery intent — people who saw your post and wanted to know more. A leading indicator of follower growth.</div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        fig_box = px.box(dff, x="platform", y="impressions",
                         color="platform", color_discrete_map=PLATFORM_COLORS,
                         title="Impressions Spread by Platform",
                         labels={"impressions": "Impressions", "platform": ""},
                         points="outliers")
        fig_box.update_layout(showlegend=False, **CHART_LAYOUT)
        fig_box.update_xaxes(**AXIS_STYLE)
        fig_box.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_11_fig_box", fig_box), use_container_width=True)
        st.markdown('<div class="insight-box">Wide boxes = inconsistent reach. Outlier dots = occasional viral posts. A narrow box means more predictable performance.</div>', unsafe_allow_html=True)

    with c4:
        freq = (
            dff.groupby(["month_dt","platform"]).size()
            .reset_index(name="posts").sort_values("month_dt")
        )
        freq["month_label"] = freq["month_dt"].dt.strftime("%b %Y")
        fig_freq = px.bar(freq, x="month_label", y="posts", color="platform",
                          color_discrete_map=PLATFORM_COLORS, barmode="stack",
                          title="Posting Frequency by Month",
                          labels={"posts": "Number of Posts", "month_label": "", "platform": ""})
        fig_freq.update_layout(**CHART_LAYOUT)
        fig_freq.update_xaxes(**AXIS_STYLE)
        fig_freq.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(register(f"chart_12_fig_freq", fig_freq), use_container_width=True)
        st.markdown('<div class="insight-box">Consistency in posting volume often correlates with sustained reach. Gaps here are worth investigating against engagement dips in Q3.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Top Posts
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<p class="section-title">Top performing posts</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Rank by any metric. Caption included so you can identify the exact post.</p>', unsafe_allow_html=True)

    ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
    with ctrl1:
        rank_by = st.selectbox("Rank by", options=list(RANK_METRICS.keys()), index=0)
    with ctrl2:
        n_posts = st.selectbox("Show top", [5, 10, 20, 50], index=1)
    with ctrl3:
        min_imp = st.number_input("Min. impressions", min_value=0, value=50, step=10)

    rank_col, fmt_str, metric_note = RANK_METRICS[rank_by]
    st.markdown(f'<div class="insight-box"><b>{rank_by}:</b> {metric_note}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    rank_df = dff[
        (dff["impressions"] >= min_imp) & dff[rank_col].notna()
    ].nlargest(n_posts, rank_col)

    # Bar chart
    fig_top = px.bar(
        rank_df.sort_values(rank_col),
        x=rank_col,
        y=rank_df.sort_values(rank_col)["caption_short"],
        orientation="h",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        title=f"Top {n_posts} Posts by {rank_by}",
        labels={rank_col: rank_by, "y": ""},
        hover_data=["date_posted","post_type","platform"]
    )
    fig_top.update_layout(
        showlegend=True,
        height=max(350, n_posts * 38),
        **CHART_LAYOUT
    )
    fig_top.update_xaxes(**AXIS_STYLE)
    fig_top.update_yaxes(**AXIS_STYLE)
    st.plotly_chart(register(f"chart_13_fig_top", fig_top), use_container_width=True)

    # Table
    table_df = rank_df[[
        "date_posted","platform","post_type",rank_col,
        "impressions","total_engagement","caption_short"
    ]].copy()
    table_df["date_posted"] = table_df["date_posted"].dt.strftime("%Y-%m-%d")
    table_df[rank_col] = table_df[rank_col].apply(lambda x: format(x, fmt_str))
    table_df["impressions"] = table_df["impressions"].apply(lambda x: f"{x:,.0f}")
    table_df["total_engagement"] = table_df["total_engagement"].apply(lambda x: f"{x:,.0f}")
    table_df.columns = ["Date","Platform","Type", rank_by,"Impressions","Engagement","Caption"]
    table_df = table_df.reset_index(drop=True)
    table_df.index += 1
    st.dataframe(table_df, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="⬇ Download Top Posts as CSV",
        data=df_to_csv_bytes(rank_df[[
            "date_posted","platform","post_type",rank_col,
            "impressions","total_engagement","caption"
        ]].assign(date_posted=rank_df["date_posted"].dt.strftime("%Y-%m-%d"))),
        file_name="top_posts.csv",
        mime="text/csv",
        use_container_width=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR EXPORT — rendered after all tabs so _figures is fully populated
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("---")
    st.markdown("### Export")

    # Full filtered data CSV
    st.download_button(
        label="⬇ Download Filtered Data (CSV)",
        data=df_to_csv_bytes(dff.drop(columns=["caption_short","month_dt"], errors="ignore")),
        file_name="sm_filtered_data.csv",
        mime="text/csv",
        use_container_width=True,
        help="All posts matching the current sidebar filters"
    )

    # Full HTML report
    if _figures:
        html_bytes = build_html_report(dff, _figures)
        st.download_button(
            label="⬇ Download Full Report (HTML)",
            data=html_bytes,
            file_name="sm_performance_report.html",
            mime="text/html",
            use_container_width=True,
            help="Interactive report with all charts + full data table. Opens in any browser."
        )

    st.markdown("""
    <div style='font-size:11px;color:#4b5563;margin-top:8px;'>
    💡 To save individual charts as PNG, hover over any chart and click the
    <b>camera icon</b> (📷) in the top-right toolbar.
    </div>
    """, unsafe_allow_html=True)