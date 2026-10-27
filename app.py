"""WasteWise — Smart City Waste Management Command Center.
Run with: streamlit run app.py
"""
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from database import (init_db, list_bins, add_bin, update_bin, change_status,
                      report_overflow, delete_bin, AREAS, WASTE_TYPES, STATUSES)
from analytics import frame, summary, spark_analytics

st.set_page_config(
    page_title='WasteWise | Command Center',
    page_icon='♻️',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Custom Command Center Theme & High-Contrast Styling
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #070d18;
    color: #f1f5f9;
}

/* Fix header clipping, laptop responsiveness, and top container spacing */
header[data-testid="stHeader"] {
    background: rgba(7, 13, 24, 0.75) !important;
    backdrop-filter: blur(10px) !important;
    height: 3.25rem !important;
    z-index: 100 !important;
}
.block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: clamp(1rem, 2.5vw, 2.5rem) !important;
    padding-right: clamp(1rem, 2.5vw, 2.5rem) !important;
    max-width: 100% !important;
}

[data-testid="stVerticalBlock"] {
    gap: 0.85rem !important;
}

/* Background Atmosphere */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgba(0, 230, 153, 0.04) 0%, transparent 35%),
                radial-gradient(circle at 90% 80%, rgba(14, 165, 233, 0.04) 0%, transparent 40%),
                #070d18;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: #0a1324 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

/* Typography Enhancements */
h1 {
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    color: #f8fafc !important;
    margin-bottom: 0.25rem !important;
}
h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #f1f5f9 !important;
}
h4, h5, h6 {
    color: #94a3b8 !important;
}
.stCaption, [data-testid="stCaptionContainer"] {
    color: #94a3b8 !important;
    font-size: 0.88rem !important;
}

/* Command Center Header Banner */
.ww-header-box {
    background: linear-gradient(135deg, rgba(13, 24, 43, 0.9) 0%, rgba(15, 29, 53, 0.7) 100%);
    border: 1px solid rgba(0, 230, 153, 0.2);
    border-radius: 16px;
    padding: clamp(16px, 2.2vw, 24px) clamp(18px, 2.5vw, 28px);
    margin-top: 0.25rem;
    margin-bottom: 18px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    position: relative;
    overflow: hidden;
}
.ww-header-box::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #00e699, #0ea5e9, #8b5cf6);
}
.ww-header-box h1 {
    font-size: clamp(1.4rem, 2.2vw, 1.85rem) !important;
    margin: 0 !important;
    line-height: 1.25 !important;
}
.ww-tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(0, 230, 153, 0.15);
    color: #00e699;
    border: 1px solid rgba(0, 230, 153, 0.3);
    margin-bottom: 6px;
}
.ww-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

/* Polished KPI Cards */
.ww-kpi-card {
    background: linear-gradient(145deg, #0e192d 0%, #0a1324 100%);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: clamp(14px, 1.8vw, 18px);
    position: relative;
    box-shadow: 0 6px 20px -4px rgba(0, 0, 0, 0.4);
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.ww-kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 230, 153, 0.35);
    box-shadow: 0 10px 24px -4px rgba(0, 230, 153, 0.15);
}
.ww-kpi-card.urgent {
    border-left: 4px solid #f43f5e;
}
.ww-kpi-card.urgent:hover {
    border-color: rgba(244, 63, 94, 0.4);
    box-shadow: 0 10px 24px -4px rgba(244, 63, 94, 0.18);
}
.ww-kpi-card.pending {
    border-left: 4px solid #f59e0b;
}
.ww-kpi-card.collected {
    border-left: 4px solid #0ea5e9;
}
.ww-kpi-card.total {
    border-left: 4px solid #00e699;
}
.ww-kpi-icon {
    font-size: 1.35rem;
    line-height: 1;
    margin-bottom: 8px;
}
.ww-kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    margin-bottom: 4px;
}
.ww-kpi-value {
    font-size: clamp(1.4rem, 2vw, 1.8rem);
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.02em;
    line-height: 1.15;
}
.ww-kpi-sub {
    font-size: 0.72rem;
    color: #64748b;
    margin-top: 4px;
}

/* Plotly Visual Card Container */
.js-plotly-plot {
    background: linear-gradient(145deg, rgba(13, 24, 43, 0.65) 0%, rgba(10, 19, 36, 0.75) 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 14px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
    overflow: hidden !important;
}

/* Streamlit Native Widget Polishing */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #0e192d 0%, #0a1324 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}
div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-weight: 800 !important;
    font-size: 1.8rem !important;
}

/* Buttons */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00c885 0%, #059669 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 4px 14px rgba(0, 200, 133, 0.3) !important;
    transition: all 0.2s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #00e699 0%, #10b981 100%) !important;
    box-shadow: 0 6px 20px rgba(0, 230, 153, 0.45) !important;
    transform: translateY(-1px) !important;
}
div.stButton > button[kind="secondary"] {
    background: #0f1d35 !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: #152747 !important;
    border-color: rgba(0, 230, 153, 0.4) !important;
    color: #ffffff !important;
}

/* Download Buttons */
div.stDownloadButton > button {
    background: #0d1b32 !important;
    color: #38bdf8 !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div.stDownloadButton > button:hover {
    background: rgba(56, 189, 248, 0.12) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
}

/* Form Inputs & Selects */
div[data-baseweb="input"], div[data-baseweb="select"] {
    border-radius: 10px !important;
}
div[data-baseweb="input"] input {
    color: #f8fafc !important;
}

/* Expander Styling */
div[data-testid="stExpander"] {
    background: rgba(13, 24, 43, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    margin-bottom: 16px !important;
}

/* Table Card Enhancements */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Radio Navigation in Sidebar */
div[data-testid="stRadio"] > label {
    display: none !important;
}
div[data-testid="stRadio"] [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    width: 100% !important;
}
[data-testid="stRadioOption"],
div[data-testid="stRadio"] [role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin: 0 !important;
    cursor: pointer !important;
    width: 100% !important;
    box-sizing: border-box !important;
    transition: all 0.2s ease !important;
}
[data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p,
[data-testid="stRadioOption"] p,
div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    color: #94a3b8 !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    margin: 0 !important;
    line-height: 1.3 !important;
    transition: color 0.2s ease !important;
}
[data-testid="stRadioOption"]:hover,
div[data-testid="stRadio"] [role="radiogroup"] label:hover {
    background: rgba(0, 230, 153, 0.06) !important;
    border-color: rgba(0, 230, 153, 0.25) !important;
}
[data-testid="stRadioOption"]:hover [data-testid="stMarkdownContainer"] p,
[data-testid="stRadioOption"]:hover p,
div[data-testid="stRadio"] [role="radiogroup"] label:hover div[data-testid="stMarkdownContainer"] p {
    color: #f1f5f9 !important;
}
/* Selected active state */
[data-testid="stRadioOption"][data-selected="true"],
[data-testid="stRadioOption"]:has(input:checked),
div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked),
div[data-testid="stRadio"] [role="radiogroup"] label[data-checked="true"] {
    background: linear-gradient(90deg, rgba(0, 230, 153, 0.16) 0%, rgba(14, 165, 233, 0.08) 100%) !important;
    border: 1px solid #00e699 !important;
    box-shadow: 0 2px 10px rgba(0, 230, 153, 0.15) !important;
}
[data-testid="stRadioOption"][data-selected="true"] [data-testid="stMarkdownContainer"] p,
[data-testid="stRadioOption"][data-selected="true"] p,
[data-testid="stRadioOption"]:has(input:checked) [data-testid="stMarkdownContainer"] p,
[data-testid="stRadioOption"]:has(input:checked) p,
div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p,
div[data-testid="stRadio"] [role="radiogroup"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] p {
    color: #00e699 !important;
    font-weight: 700 !important;
}

/* System Pills & Legend */
.ww-legend-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 8px;
}
.ww-pill-high { background: rgba(244, 63, 94, 0.12); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
.ww-pill-medium { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.ww-pill-low { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.ww-pill-completed { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
</style>
''', unsafe_allow_html=True)

# Database Initialization
try:
    init_db()
except sqlite3.Error as exc:
    st.error(f'Could not initialize the local database: {exc}')
    st.stop()

# Sidebar: Brand, Navigation & Telemetry Diagnostics
st.sidebar.markdown('''
<div style="padding: 10px 0 20px 0;">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <span style="font-size: 2rem; background: rgba(0,230,153,0.12); padding: 8px; border-radius: 12px; border: 1px solid rgba(0,230,153,0.3);">♻️</span>
        <div>
            <div style="font-weight: 800; font-size: 1.25rem; letter-spacing: -0.02em; color: #f8fafc;">WasteWise</div>
            <div style="font-size: 0.75rem; font-weight: 600; color: #00e699; letter-spacing: 0.05em; text-transform: uppercase;">Command Center</div>
        </div>
    </div>
    <div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.4;">Smart Municipal Waste Management & Prioritization</div>
</div>
''', unsafe_allow_html=True)

page = st.sidebar.radio(
    'Navigation',
    ['Dashboard', 'Manage Bins', 'Collection Queue', 'Analytics & Reports']
)

st.sidebar.divider()

# Load Data from Database
try:
    df = frame(list_bins())
except sqlite3.Error as exc:
    st.error(f'Could not read waste-bin records: {exc}')
    st.stop()

# Sidebar Diagnostics Pill
stats = summary(df)
urgent_sidebar_count = int(((df.fill_level >= 90) | (df.reported_overflow == 1)).sum()) if not df.empty else 0

st.sidebar.markdown(f'''
<div style="background: rgba(13, 24, 43, 0.7); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
    <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em; color: #94a3b8; margin-bottom: 8px;">System Diagnostics</div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="font-size: 0.8rem; color: #cbd5e1;">High Priority Bins</span>
        <span style="font-size: 0.8rem; font-weight: 700; color: {'#f43f5e' if urgent_sidebar_count > 0 else '#10b981'};">{urgent_sidebar_count}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="font-size: 0.8rem; color: #cbd5e1;">Pending Collection</span>
        <span style="font-size: 0.8rem; font-weight: 700; color: #f59e0b;">{stats['pending']}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 0.8rem; color: #cbd5e1;">Database Records</span>
        <span style="font-size: 0.8rem; font-weight: 700; color: #00e699;">{stats['total']}</span>
    </div>
</div>
<div style="font-size: 0.72rem; color: #64748b; text-align: center;">
    Engine: SQLite • Pandas • Apache Spark local[1]
</div>
''', unsafe_allow_html=True)


def action(callback, *args):
    try:
        callback(*args)
        st.success('Operation saved successfully.')
        st.rerun()
    except (ValueError, sqlite3.Error) as exc:
        st.error(f'Unable to save operation: {exc}')


def apply_plotly_theme(fig, height=350, show_legend=True, legend_orientation='h'):
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(family='Plus Jakarta Sans, sans-serif', color='#e2e8f0', size=11),
        margin=dict(l=55, r=25, t=65, b=45),
        height=height,
        title=dict(
            font=dict(size=14, color='#f8fafc', family='Plus Jakarta Sans, sans-serif'),
            x=0.03,
            y=0.96,
            xanchor='left',
            yanchor='top'
        ),
        showlegend=show_legend,
        legend=dict(
            orientation=legend_orientation,
            yanchor='bottom',
            y=1.04,
            xanchor='right',
            x=0.98,
            font=dict(size=11, color='#94a3b8')
        ),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.05)',
            zerolinecolor='rgba(255, 255, 255, 0.08)',
            tickfont=dict(color='#94a3b8', size=11),
            title_standoff=10
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.05)',
            zerolinecolor='rgba(255, 255, 255, 0.08)',
            tickfont=dict(color='#94a3b8', size=11),
            title_standoff=12
        )
    )
    return fig


def show_table(data):
    cols = ['bin_code', 'area', 'location', 'waste_type', 'fill_level',
            'capacity_liters', 'priority', 'status', 'estimated_waste_liters']
    renamed = data[cols].rename(columns={
        'bin_code': 'Bin ID',
        'area': 'Area',
        'location': 'Location',
        'waste_type': 'Waste Type',
        'fill_level': 'Fill %',
        'capacity_liters': 'Capacity (L)',
        'priority': 'Priority',
        'status': 'Status',
        'estimated_waste_liters': 'Estimated Waste (L)'
    })
    st.dataframe(
        renamed,
        column_config={
            'Fill %': st.column_config.ProgressColumn(
                'Fill %',
                help='Current container fill percentage',
                format='%d%%',
                min_value=0,
                max_value=100
            ),
            'Capacity (L)': st.column_config.NumberColumn(
                'Capacity (L)',
                format='%d L'
            ),
            'Estimated Waste (L)': st.column_config.NumberColumn(
                'Estimated Waste (L)',
                format='%.1f L'
            ),
            'Priority': st.column_config.TextColumn(
                'Priority',
                help='High: overflow or ≥90% | Medium: ≥70% | Low: <70% | Completed'
            ),
            'Status': st.column_config.TextColumn('Status')
        },
        use_container_width=True,
        hide_index=True
    )


def filtered(data, key):
    a, b, c = st.columns([2, 1, 1])
    query = a.text_input('Search by Bin ID, Area, or Location', key=f'{key}_search', placeholder='e.g., BIN-001, Andheri, Market...')
    area = b.selectbox('Filter Area', ['All'] + sorted(data['area'].dropna().unique().tolist()), key=f'{key}_area')
    status = c.selectbox('Filter Status', ['All'] + STATUSES, key=f'{key}_status')
    result = data.copy()
    if query:
        mask = (result['bin_code'].astype(str).str.contains(query, case=False, regex=False) |
                result['area'].astype(str).str.contains(query, case=False, regex=False) |
                result['location'].astype(str).str.contains(query, case=False, regex=False))
        result = result[mask]
    if area != 'All':
        result = result[result.area == area]
    if status != 'All':
        result = result[result.status == status]
    return result


# ==============================================================================
# PAGE 1: DASHBOARD
# ==============================================================================
if page == 'Dashboard':
    st.markdown('''
    <div class="ww-header-box">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <span class="ww-tag">Executive Overview</span>
                <h1 style="font-size: 2rem; margin: 0;">Municipal Waste Operations Command Center</h1>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px; margin-bottom: 0;">
                    Real-time container telemetry, automated dispatch prioritization, and urban waste load analytics.
                </p>
            </div>
            <div class="ww-status-badge">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981;"></span>
                Live Telemetry Active
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # 4 Command Center KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'''
        <div class="ww-kpi-card total">
            <div class="ww-kpi-icon">🏢</div>
            <div class="ww-kpi-label">Total Monitored Bins</div>
            <div class="ww-kpi-value">{stats['total']}</div>
            <div class="ww-kpi-sub">Across 6 municipal zones</div>
        </div>
        ''', unsafe_allow_html=True)

    with k2:
        st.markdown(f'''
        <div class="ww-kpi-card urgent">
            <div class="ww-kpi-icon">🚨</div>
            <div class="ww-kpi-label">Urgent / Overflowing</div>
            <div class="ww-kpi-value" style="color: #fb7185;">{stats['full']}</div>
            <div class="ww-kpi-sub">Fill ≥ 90% or reported overflow</div>
        </div>
        ''', unsafe_allow_html=True)

    with k3:
        st.markdown(f'''
        <div class="ww-kpi-card pending">
            <div class="ww-kpi-icon">⏳</div>
            <div class="ww-kpi-label">Pending Collections</div>
            <div class="ww-kpi-value" style="color: #fbbf24;">{stats['pending']}</div>
            <div class="ww-kpi-sub">Awaiting truck dispatch</div>
        </div>
        ''', unsafe_allow_html=True)

    with k4:
        st.markdown(f'''
        <div class="ww-kpi-card collected">
            <div class="ww-kpi-icon">♻️</div>
            <div class="ww-kpi-label">Collected Waste</div>
            <div class="ww-kpi-value" style="color: #38bdf8;">{stats['collected_liters']:,.1f} <span style="font-size: 1.1rem; font-weight: 600;">L</span></div>
            <div class="ww-kpi-sub">Estimated volume cleared</div>
        </div>
        ''', unsafe_allow_html=True)

    if df.empty:
        st.info('No bin records found in database. Use Manage Bins to register initial bins.')
    else:
        left, right = st.columns([1.1, 0.9])
        with left:
            area_df = df.groupby('area', as_index=False)['estimated_waste_liters'].sum().sort_values('estimated_waste_liters', ascending=False)
            fig_area = px.bar(
                area_df,
                x='area',
                y='estimated_waste_liters',
                title='Estimated Waste Load by Municipal Zone',
                labels={'estimated_waste_liters': 'Estimated Waste (Liters)', 'area': 'Municipal Zone'},
                color='estimated_waste_liters',
                color_continuous_scale=[[0, '#059669'], [0.5, '#10b981'], [1, '#00e699']]
            )
            fig_area.update_coloraxes(showscale=False)
            apply_plotly_theme(fig_area, height=350, show_legend=False)
            st.plotly_chart(fig_area, use_container_width=True)

        with right:
            status_df = df.groupby('status', as_index=False).size()
            fig_status = px.pie(
                status_df,
                names='status',
                values='size',
                hole=0.6,
                title='Operational Status Breakdown',
                color='status',
                color_discrete_map={
                    'Pending': '#f59e0b',
                    'In Progress': '#0ea5e9',
                    'Collected': '#10b981'
                }
            )
            apply_plotly_theme(fig_status, height=350)
            fig_status.update_layout(
                legend=dict(orientation='h', yanchor='top', y=-0.08, xanchor='center', x=0.5),
                margin=dict(l=20, r=20, t=55, b=45)
            )
            st.plotly_chart(fig_status, use_container_width=True)

        # Urgent Collection Queue Section
        st.markdown('''
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 12px;">
            <div>
                <h3 style="margin: 0; display: inline-flex; align-items: center; gap: 8px;">
                    <span style="color: #f43f5e;">⚡</span> Urgent Priority Queue
                </h3>
                <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 2px;">
                    Containers requiring critical dispatch (Fill ≥ 90% or actively reported overflow)
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        urgent = df[(df.priority == 'High') & (df.status != 'Collected')].sort_values('fill_level', ascending=False)
        if urgent.empty:
            st.success('✅ All high-priority municipal bins have been addressed. No urgent collections pending.')
        else:
            show_table(urgent.head(10))


# ==============================================================================
# PAGE 2: MANAGE BINS
# ==============================================================================
elif page == 'Manage Bins':
    st.markdown('''
    <div class="ww-header-box">
        <span class="ww-tag">Infrastructure Registry</span>
        <h1 style="font-size: 2rem; margin: 0;">Smart Waste Bin Registry & Management</h1>
        <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px; margin-bottom: 0;">
            Provision new municipal waste units, maintain spatial metadata, and review container fleet records.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander('➕ Provision New Waste Bin Container', expanded=True):
        with st.form('add_form', clear_on_submit=True):
            x, y = st.columns(2)
            code = x.text_input('Unique Bin Identifier', placeholder='e.g., BIN-101')
            area = y.selectbox('Designated Municipal Zone', AREAS)
            location = x.text_input('Street Address / Sector Landmark', placeholder='e.g., Andheri Station West, Gate 2')
            waste_type = y.selectbox('Waste Category', WASTE_TYPES)
            fill = x.slider('Initial Fill Level (%)', 0, 100, 50)
            capacity = y.number_input('Container Capacity (Liters)', 1, 10000, 240, step=10)
            if st.form_submit_button('➕ Register Container to Fleet', type='primary', use_container_width=True):
                action(add_bin, code, area, location, waste_type, fill, capacity)

    st.subheader('Container Fleet Explorer')
    st.caption('Filter fleet records dynamically by keyword, municipal zone, or collection status.')
    view = filtered(df, 'manage')

    st.markdown(f'''
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">Displaying {len(view)} matching container(s)</span>
    </div>
    ''', unsafe_allow_html=True)

    show_table(view)

    st.download_button(
        '⬇️ Export Filtered Fleet Records (CSV)',
        data=view.to_csv(index=False).encode('utf-8-sig'),
        file_name='wastewise_filtered_bins.csv',
        mime='text/csv'
    )

    if not df.empty:
        st.markdown('''
        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px; margin-top: 14px;">
            <h3>Update Container Telemetry or Decommission</h3>
            <p style="color: #94a3b8; font-size: 0.88rem;">Select an existing container record to update its operational parameters or retire it from the active database.</p>
        </div>
        ''', unsafe_allow_html=True)

        ids = df['id'].astype(int).tolist()
        labels = {int(r.id): f'{r.bin_code} — {r.area} ({r.location})' for r in df.itertuples()}
        selected = st.selectbox('Choose Container to Edit', ids, format_func=lambda v: labels[v])
        rec = df[df.id == selected].iloc[0]

        with st.form('edit_form'):
            ea, eb = st.columns(2)
            new_area = ea.selectbox('Municipal Area', AREAS, index=AREAS.index(rec.area) if rec.area in AREAS else 0)
            new_location = eb.text_input('Location Landmark', value=str(rec.location))
            new_type = ea.selectbox('Waste Category', WASTE_TYPES, index=WASTE_TYPES.index(rec.waste_type))
            new_fill = eb.slider('Updated Fill Level (%)', 0, 100, int(rec.fill_level))
            new_capacity = ea.number_input('Container Capacity (Liters)', 1, 10000, int(rec.capacity_liters))
            if st.form_submit_button('💾 Save Operational Updates', type='primary', use_container_width=True):
                action(update_bin, selected, new_area, new_location, new_type, new_fill, new_capacity)

        with st.container():
            st.markdown('<div style="background: rgba(244,63,94,0.06); border: 1px solid rgba(244,63,94,0.25); border-radius: 12px; padding: 16px; margin-top: 14px;">', unsafe_allow_html=True)
            confirm = st.checkbox('Confirm permanent decommissioning of this record', key=f'del_{selected}')
            if st.button('🗑️ Decommission Selected Bin', disabled=not confirm):
                action(delete_bin, selected)
            st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# PAGE 3: COLLECTION QUEUE
# ==============================================================================
elif page == 'Collection Queue':
    st.markdown('''
    <div class="ww-header-box">
        <span class="ww-tag">Sanitation Dispatch</span>
        <h1 style="font-size: 2rem; margin: 0;">Collection Prioritization & Dispatch Queue</h1>
        <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px; margin-bottom: 0;">
            Deterministic priority engine ranking active containers by overflow risk and volume threshold.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # Priority Engine Rules Legend
    st.markdown('''
    <div style="margin-bottom: 16px;">
        <span class="ww-legend-pill ww-pill-high">🔴 High: Overflow Reported OR Fill ≥ 90%</span>
        <span class="ww-legend-pill ww-pill-medium">🟡 Medium: Fill ≥ 70%</span>
        <span class="ww-legend-pill ww-pill-low">🟢 Low: Fill &lt; 70%</span>
        <span class="ww-legend-pill ww-pill-completed">🔵 Completed: Successfully Collected</span>
    </div>
    ''', unsafe_allow_html=True)

    active = df[df.status != 'Collected'].copy()
    order = {'High': 0, 'Medium': 1, 'Low': 2}
    if not active.empty:
        active['sort_priority'] = active.priority.map(order)
        active = active.sort_values(['sort_priority', 'fill_level'], ascending=[True, False])

    st.subheader('Active Dispatch Manifest')
    show_table(active)

    if df.empty:
        st.info('No containers currently registered in the database.')
        st.markdown('### Operational Dispatch Hub')
        q_left, q_right = st.columns(2)

        choices = {int(r.id): f'{r.bin_code} — {r.location} ({r.fill_level}%)' for r in df.itertuples()}

        with q_left:
            st.markdown('''
            <div style="border-top: 3px solid #f43f5e; padding: 14px 18px; background: rgba(13, 24, 43, 0.65); border-radius: 12px; border-left: 1px solid rgba(255,255,255,0.06); border-right: 1px solid rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
                <h4 style="color: #f8fafc; margin: 0 0 4px 0; display: flex; align-items: center; gap: 8px;">
                    <span>🚨</span> Citizen / Field Overflow Report
                </h4>
                <p style="color: #94a3b8; font-size: 0.82rem; margin: 0;">
                    Escalates container priority directly to <b>HIGH</b> and flags for urgent sanitation dispatch.
                </p>
            </div>
            ''', unsafe_allow_html=True)
            selected_report = st.selectbox('Select Container to Flag', list(choices), format_func=lambda v: choices[v], key='report')
            if st.button('🚨 Submit Overflow Escalation', type='primary', use_container_width=True):
                action(report_overflow, selected_report)

        with q_right:
            st.markdown('''
            <div style="border-top: 3px solid #00e699; padding: 14px 18px; background: rgba(13, 24, 43, 0.65); border-radius: 12px; border-left: 1px solid rgba(255,255,255,0.06); border-right: 1px solid rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
                <h4 style="color: #f8fafc; margin: 0 0 4px 0; display: flex; align-items: center; gap: 8px;">
                    <span>🚚</span> Update Collection Workflow
                </h4>
                <p style="color: #94a3b8; font-size: 0.82rem; margin: 0;">
                    Advance container cycle: <i>Pending → In Progress → Collected</i>.
                </p>
            </div>
            ''', unsafe_allow_html=True)
            selected_status = st.selectbox('Select Target Container', list(choices), format_func=lambda v: choices[v], key='status_bin')
            current = df[df.id == selected_status].iloc[0].status
            new_status = st.selectbox('New Lifecycle Status', STATUSES, index=STATUSES.index(current))
            if st.button('✅ Confirm Status Transition', type='primary', use_container_width=True):
                action(change_status, selected_status, new_status)


# ==============================================================================
# PAGE 4: ANALYTICS & REPORTS
# ==============================================================================
else:
    st.markdown('''
    <div class="ww-header-box">
        <span class="ww-tag">Big Data & Insights</span>
        <h1 style="font-size: 2rem; margin: 0;">Sanitation Analytics & Big Data Engine</h1>
        <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px; margin-bottom: 0;">
            Multi-dimensional analytical visualizations and on-demand local Apache PySpark distributed aggregations.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    if df.empty:
        st.info('Add containers in Manage Bins to view operational reports.')
    else:
        left, right = st.columns(2)
        with left:
            by_type = df.groupby('waste_type', as_index=False)['estimated_waste_liters'].sum().sort_values('estimated_waste_liters', ascending=False)
            fig_type = px.bar(
                by_type,
                x='waste_type',
                y='estimated_waste_liters',
                title='Estimated Waste Volume by Category',
                labels={'estimated_waste_liters': 'Estimated Waste (Liters)', 'waste_type': 'Waste Type'},
                color='waste_type',
                color_discrete_sequence=['#00e699', '#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#64748b']
            )
            apply_plotly_theme(fig_type, height=350, show_legend=False)
            st.plotly_chart(fig_type, use_container_width=True)

        with right:
            trend = df.copy()
            trend['date'] = pd.to_datetime(trend['collected_at'], errors='coerce').dt.date
            trend = trend[trend.status == 'Collected'].dropna(subset=['date'])
            if not trend.empty:
                daily = trend.groupby('date', as_index=False)['estimated_waste_liters'].sum()
                fig_trend = px.line(
                    daily,
                    x='date',
                    y='estimated_waste_liters',
                    markers=True,
                    title='Daily Collection Trend (Liters Cleared)',
                    labels={'estimated_waste_liters': 'Collected Volume (Liters)', 'date': 'Collection Date'}
                )
                fig_trend.update_traces(line_color='#00e699', line_width=3, marker=dict(size=8, color='#38bdf8'))
                apply_plotly_theme(fig_trend, height=350, show_legend=False)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info('ℹ️ Mark containers as "Collected" to populate daily collection trend series.')

        # PySpark Big Data Analytics Engine Deck
        st.markdown('''
        <div style="border: 1px solid rgba(0, 230, 153, 0.25); background: linear-gradient(135deg, rgba(13, 24, 43, 0.8) 0%, rgba(10, 20, 38, 0.9) 100%); border-radius: 14px; padding: 18px 22px; margin-top: 10px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
                <div>
                    <span class="ww-tag" style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border-color: rgba(14, 165, 233, 0.3);">
                        Engine: Apache Spark 3.5.x local[1]
                    </span>
                    <h3 style="margin: 6px 0 0 0; color: #f8fafc;">PySpark Big Data Analytics Execution</h3>
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                Executes true PySpark DataFrame transformations (<code>groupBy</code>, <code>agg</code>, <code>sum</code>, <code>count</code>, and conditional high-priority filters) over strongly typed schemas. This demonstrates Big Data distributed computing concepts natively within the local Python runtime.
            </p>
        </div>
        ''', unsafe_allow_html=True)

        if st.button('⚡ Launch PySpark Analytics Engine', type='primary'):
            with st.spinner('Initializing SparkSession local[1] and executing schema transformations...'):
                try:
                    results = spark_analytics(df)
                    st.session_state['spark_results'] = results
                    st.success(f"Spark Engine successfully processed {results['processed']} container records in local[1] mode.")
                except Exception as exc:
                    st.error(f'PySpark execution failed: {exc}. Verify Java 17 and Python environment configurations.')

        if 'spark_results' in st.session_state:
            results = st.session_state['spark_results']
            a, b = st.columns(2)
            with a:
                st.markdown('**Spark: Area-Wise Aggregation**')
                st.dataframe(pd.DataFrame(results['area']), use_container_width=True, hide_index=True)
            with b:
                st.markdown('**Spark: Waste Category Breakdown**')
                st.dataframe(pd.DataFrame(results['type']), use_container_width=True, hide_index=True)

            st.markdown('**Spark: Lifecycle Status Manifest**')
            st.dataframe(pd.DataFrame(results['status']), use_container_width=True, hide_index=True)

            st.download_button(
                '⬇️ Download Spark Area Analytics Report (CSV)',
                pd.DataFrame(results['area']).to_csv(index=False).encode('utf-8-sig'),
                file_name='wastewise_spark_area.csv',
                mime='text/csv'
            )

        # Full Data Export Section
        st.markdown('''
        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px; margin-top: 16px;">
            <h4>Raw Operational Telemetry Export</h4>
            <p style="color: #94a3b8; font-size: 0.85rem;">Export complete municipal fleet database records for offline audit and reporting.</p>
        </div>
        ''', unsafe_allow_html=True)

        st.download_button(
            '⬇️ Download Complete Fleet Registry (CSV)',
            df.to_csv(index=False).encode('utf-8-sig'),
            file_name='wastewise_all_bins.csv',
            mime='text/csv'
        )
