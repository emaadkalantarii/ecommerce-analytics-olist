import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title='Olist E-Commerce Analytics',
    page_icon='🛒',
    layout='wide'
)

@st.cache_data
def load_data():
    base = Path(__file__).parent.parent
    df      = pd.read_csv(base / 'data/processed/dashboard_data.csv',
                          parse_dates=['order_purchase_timestamp'])
    monthly = pd.read_csv(base / 'data/processed/monthly_summary.csv',
                          parse_dates=['month'])
    states  = pd.read_csv(base / 'data/processed/state_summary.csv')
    return df, monthly, states

df, monthly, states = load_data()
VIZ = Path(__file__).parent.parent / 'docs/visualizations'

def show_chart(filename, width=900):
    col_l, col_c, col_r = st.columns([1, 6, 1])
    with col_c:
        st.image(str(VIZ / filename), width=width)

st.sidebar.title('Olist Analytics')
page = st.sidebar.radio(
    'Navigate',
    ['Overview', 'Revenue & Products', 'Delivery Performance', 'Customer Insights']
)
st.sidebar.markdown('---')
st.sidebar.caption('Brazilian e-commerce data · 2016–2018')
st.sidebar.caption('Source: Olist / Kaggle')

if page == 'Overview':
    st.title('🛒 Olist E-Commerce Analytics')
    st.markdown('End-to-end analysis of **96,457 delivered orders** across Brazil (2016–2018).')
    st.markdown('---')

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Total Orders',       f"{df['order_id'].nunique():,}")
    col2.metric('Total Revenue',      f"R${df['price'].sum()/1e6:.2f}M")
    col3.metric('Avg Review Score',   f"{df['review_score'].mean():.2f} / 5")
    col4.metric('Late Delivery Rate', f"{df['is_late'].mean()*100:.1f}%")
    col5.metric('Repeat Rate',        '3.0%')

    st.markdown('---')
    st.subheader('Monthly Revenue Trend')
    show_chart('01_monthly_revenue.png')

    st.markdown('---')
    st.subheader('Key Findings')
    col_a, col_b = st.columns(2)
    with col_a:
        st.success('**Health & Beauty** is the top revenue category at R$1.23M')
        st.success('**Credit card** dominates payments at ~74% of all transactions')
        st.info('Peak shopping hours are between **10:00 and 21:00**')
    with col_b:
        st.error('Late deliveries score **2.57 avg stars** vs 4.29 for on-time — a 40% gap')
        st.error('**46% of late orders** receive a 1-star review')
        st.warning('Customer repeat rate is only **3%** — retention is a major opportunity')

elif page == 'Revenue & Products':
    st.title('💰 Revenue & Product Analysis')
    st.markdown('---')

    st.subheader('Top 15 Product Categories by Revenue')
    show_chart('02_top_categories.png')

    st.markdown('---')
    st.subheader('Payment Method Analysis')
    show_chart('05_payment_methods.png')

    st.markdown('---')
    st.subheader('Order Volume by Hour of Day')
    show_chart('06_hourly_orders.png')

elif page == 'Delivery Performance':
    st.title('🚚 Delivery Performance Analysis')
    st.markdown('---')

    col1, col2, col3 = st.columns(3)
    col1.metric('Avg Delivery Time', f"{df['delivery_days'].mean():.1f} days")
    col2.metric('Late Orders',       f"{df['is_late'].sum():,}")
    col3.metric('On-Time Rate',      f"{(1 - df['is_late'].mean())*100:.1f}%")

    st.markdown('---')
    st.subheader('Late Delivery Rate by State')
    show_chart('03_late_delivery_by_state.png')

    st.markdown('---')
    st.subheader('Impact of Late Delivery on Review Scores')
    show_chart('04_review_vs_lateness.png')

elif page == 'Customer Insights':
    st.title('👥 Customer Insights')
    st.markdown('---')

    col1, col2, col3 = st.columns(3)
    col1.metric('Unique States',      df['customer_state'].nunique())
    col2.metric('Avg Review Score',   f"{df['review_score'].mean():.2f}")
    col3.metric('5-Star Review Rate', f"{(df['review_score']==5).mean()*100:.1f}%")

    st.markdown('---')
    st.subheader('Customer Review Score Distribution')
    show_chart('07_review_distribution.png', width=750)