"""WasteWise Streamlit interface. Run with: streamlit run app.py"""
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from database import (init_db, list_bins, add_bin, update_bin, change_status,
                      report_overflow, delete_bin, AREAS, WASTE_TYPES, STATUSES)
from analytics import frame, summary, spark_analytics

st.set_page_config(page_title='WasteWise | Smart Waste Management', page_icon='♻️',
                   layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.stApp {background: #0b1220; color: #e6eef8;}
[data-testid="stSidebar"] {background: #101c30;}
[data-testid="stMetric"] {background: #15243a; border: 1px solid #253e55;
 border-radius: 14px; padding: 17px;}
h1,h2,h3 {color:#ecf8f4!important;}
div.stButton>button[kind="primary"] {background:#078c74; border-color:#078c74;}
</style>''', unsafe_allow_html=True)

try:
    init_db()
except sqlite3.Error as exc:
    st.error(f'Could not initialize the local database: {exc}')
    st.stop()

st.sidebar.title('♻️ WasteWise')
st.sidebar.caption('Smart waste collection analytics')
page = st.sidebar.radio('Navigation', ['Dashboard', 'Manage Bins', 'Collection Queue', 'Analytics & Reports'])
st.sidebar.divider()
st.sidebar.info('Demo system • Simulated data • SQLite + Pandas + PySpark')

try:
    df = frame(list_bins())
except sqlite3.Error as exc:
    st.error(f'Could not read waste-bin records: {exc}')
    st.stop()


def action(callback, *args):
    try:
        callback(*args)
        st.success('Saved successfully.')
        st.rerun()
    except (ValueError, sqlite3.Error) as exc:
        st.error(f'Unable to save: {exc}')


def show_table(data):
    cols = ['bin_code', 'area', 'location', 'waste_type', 'fill_level',
            'capacity_liters', 'priority', 'status', 'estimated_waste_liters']
    st.dataframe(data[cols].rename(columns={
        'bin_code':'Bin ID','area':'Area','location':'Location','waste_type':'Waste Type',
        'fill_level':'Fill %','capacity_liters':'Capacity (L)','priority':'Priority',
        'status':'Status','estimated_waste_liters':'Estimated Waste (L)'}),
        use_container_width=True, hide_index=True)


def filtered(data, key):
    a, b, c = st.columns([2, 1, 1])
    query = a.text_input('Search bin, area or location', key=f'{key}_search')
    area = b.selectbox('Area', ['All'] + sorted(data['area'].dropna().unique().tolist()), key=f'{key}_area')
    status = c.selectbox('Status', ['All'] + STATUSES, key=f'{key}_status')
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


if page == 'Dashboard':
    st.title('WasteWise | Operations Dashboard')
    st.caption('Prioritize overflowing bins and monitor waste collection across city areas.')
    stats = summary(df)
    cols = st.columns(4)
    for col, title, value in zip(cols,
        ['Total Bins', 'Full / Overflowing', 'Pending Collections', 'Collected Waste (estimated)'],
        [stats['total'], stats['full'], stats['pending'], f"{stats['collected_liters']:,.1f} L"]):
        col.metric(title, value)
    st.subheader('Collection overview')
    if df.empty:
        st.info('No bins yet. Add a record in Manage Bins.')
    else:
        left, right = st.columns(2)
        area_df = df.groupby('area', as_index=False)['estimated_waste_liters'].sum()
        left.plotly_chart(px.bar(area_df, x='area', y='estimated_waste_liters',
                                 title='Estimated waste by area', color='estimated_waste_liters',
                                 labels={'estimated_waste_liters':'Estimated liters', 'area':'Area'},
                                 color_continuous_scale='Teal'), use_container_width=True)
        status_df = df.groupby('status', as_index=False).size()
        right.plotly_chart(px.pie(status_df, names='status', values='size', hole=.55,
                                  title='Collection status distribution'), use_container_width=True)
        st.subheader('Urgent collection queue')
        urgent = df[(df.priority == 'High') & (df.status != 'Collected')].sort_values('fill_level', ascending=False)
        if urgent.empty:
            st.success('No high-priority bins currently need collection.')
        else:
            show_table(urgent.head(10))

elif page == 'Manage Bins':
    st.title('Manage Waste Bins')
    with st.expander('➕ Add a new waste bin', expanded=True):
        with st.form('add_form', clear_on_submit=True):
            x, y = st.columns(2)
            code = x.text_input('Unique bin code (example: BIN-101)')
            area = y.selectbox('Area', AREAS)
            location = x.text_input('Location / landmark')
            waste_type = y.selectbox('Waste type', WASTE_TYPES)
            fill = x.slider('Fill level (%)', 0, 100, 50)
            capacity = y.number_input('Bin capacity (liters)', 1, 10000, 240, step=10)
            if st.form_submit_button('Add Bin', type='primary'):
                action(add_bin, code, area, location, waste_type, fill, capacity)
    st.subheader('Search and filter records')
    view = filtered(df, 'manage')
    st.caption(f'{len(view)} matching bins')
    show_table(view)
    st.download_button('⬇️ Download filtered records (CSV)',
                       data=view.to_csv(index=False).encode('utf-8-sig'),
                       file_name='wastewise_filtered_bins.csv', mime='text/csv')
    if not df.empty:
        st.subheader('Edit or delete a record')
        ids = df['id'].astype(int).tolist()
        labels = {int(r.id): f'{r.bin_code} — {r.area}' for r in df.itertuples()}
        selected = st.selectbox('Choose bin', ids, format_func=lambda v: labels[v])
        rec = df[df.id == selected].iloc[0]
        with st.form('edit_form'):
            ea, eb = st.columns(2)
            new_area = ea.selectbox('Area', AREAS, index=AREAS.index(rec.area) if rec.area in AREAS else 0)
            new_location = eb.text_input('Location', value=str(rec.location))
            new_type = ea.selectbox('Waste type', WASTE_TYPES, index=WASTE_TYPES.index(rec.waste_type))
            new_fill = eb.slider('Fill level (%)', 0, 100, int(rec.fill_level))
            new_capacity = ea.number_input('Capacity (liters)', 1, 10000, int(rec.capacity_liters))
            if st.form_submit_button('Save Changes', type='primary'):
                action(update_bin, selected, new_area, new_location, new_type, new_fill, new_capacity)
        confirm = st.checkbox('I confirm I want to delete this record', key=f'del_{selected}')
        if st.button('Delete Selected Bin', disabled=not confirm):
            action(delete_bin, selected)

elif page == 'Collection Queue':
    st.title('Collection Prioritization')
    st.caption('High: reported overflow or ≥90% full. Medium: ≥70%. Low: below 70%. Collected bins are completed.')
    active = df[df.status != 'Collected'].copy()
    order = {'High':0, 'Medium':1, 'Low':2}
    if not active.empty:
        active['sort_priority'] = active.priority.map(order)
        active = active.sort_values(['sort_priority', 'fill_level'], ascending=[True, False])
    show_table(active)
    if df.empty:
        st.info('Add a bin first.')
    else:
        st.subheader('Report an overflow')
        choices = {int(r.id): f'{r.bin_code} — {r.location} ({r.fill_level}%)' for r in df.itertuples()}
        selected_report = st.selectbox('Select bin to report', list(choices), format_func=lambda v: choices[v], key='report')
        if st.button('🚨 Report Overflow', type='primary'):
            action(report_overflow, selected_report)
        st.subheader('Update collection status')
        selected_status = st.selectbox('Select bin', list(choices), format_func=lambda v: choices[v], key='status_bin')
        current = df[df.id == selected_status].iloc[0].status
        new_status = st.selectbox('New status', STATUSES, index=STATUSES.index(current))
        if st.button('Update Status', type='primary'):
            action(change_status, selected_status, new_status)

else:
    st.title('Analytics & Reports')
    st.caption('Interactive charts and downloadable records. PySpark runs locally on demand.')
    if df.empty:
        st.info('Add bins to generate analytics.')
    else:
        left, right = st.columns(2)
        by_type = df.groupby('waste_type', as_index=False)['estimated_waste_liters'].sum()
        left.plotly_chart(px.bar(by_type, x='waste_type', y='estimated_waste_liters',
                                 title='Estimated waste by type', color='waste_type'), use_container_width=True)
        trend = df.copy()
        trend['date'] = pd.to_datetime(trend['collected_at'], errors='coerce').dt.date
        trend = trend[trend.status == 'Collected'].dropna(subset=['date'])
        if not trend.empty:
            daily = trend.groupby('date', as_index=False)['estimated_waste_liters'].sum()
            right.plotly_chart(px.line(daily, x='date', y='estimated_waste_liters', markers=True,
                                       title='Estimated collected waste by date'), use_container_width=True)
        else:
            right.info('Mark some bins Collected to see collection trends.')
        st.subheader('PySpark Big Data Analysis')
        st.caption('Runs real Spark DataFrame groupBy, count and sum operations in local[1] mode. '
                   'The included sample data is small; this demonstrates Spark concepts, not large-scale distributed processing.')
        if st.button('▶ Run PySpark Analytics', type='primary'):
            with st.spinner('Starting local Spark and analyzing waste records...'):
                try:
                    results = spark_analytics(df)
                    st.session_state['spark_results'] = results
                    st.success(f"Spark processed {results['processed']} records successfully.")
                except Exception as exc:
                    st.error(f'PySpark could not start: {exc}. Check Java 17, Python compatibility and installation.')
        if 'spark_results' in st.session_state:
            results = st.session_state['spark_results']
            a, b = st.columns(2)
            a.markdown('**Spark: area-wise analysis**')
            a.dataframe(pd.DataFrame(results['area']), use_container_width=True, hide_index=True)
            b.markdown('**Spark: waste-type analysis**')
            b.dataframe(pd.DataFrame(results['type']), use_container_width=True, hide_index=True)
            st.markdown('**Spark: collection statuses**')
            st.dataframe(pd.DataFrame(results['status']), use_container_width=True, hide_index=True)
            st.download_button('⬇️ Export Spark area analytics',
                pd.DataFrame(results['area']).to_csv(index=False).encode('utf-8-sig'),
                file_name='wastewise_spark_area.csv', mime='text/csv')
        st.subheader('Export data')
        st.download_button('⬇️ Download all bin records (CSV)',
                           df.to_csv(index=False).encode('utf-8-sig'),
                           file_name='wastewise_all_bins.csv', mime='text/csv')
