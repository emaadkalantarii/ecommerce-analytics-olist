import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

st.set_page_config(
    page_title='Olist E-Commerce Analytics',
    page_icon='🛒',
    layout='wide'
)

BLUE  = '#2E86AB'
CORAL = '#E84855'
GREEN = '#3BB273'
GOLD  = '#F4A261'

sns.set_theme(style='whitegrid', palette='muted')

@st.cache_data
def load_data():
    base = Path(__file__).parent.parent
    df = pd.read_csv(base / 'data/processed/dashboard_data.csv',
                     parse_dates=['order_purchase_timestamp'])
    monthly = pd.read_csv(base / 'data/processed/monthly_summary.csv',
                          parse_dates=['month'])
    states  = pd.read_csv(base / 'data/processed/state_summary.csv')
    return df, monthly, states

df, monthly, states = load_data()

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
    col1.metric('Total Orders',    f"{df['order_id'].nunique():,}")
    col2.metric('Total Revenue',   f"R${df['price'].sum()/1e6:.2f}M")
    col3.metric('Avg Review Score',f"{df['review_score'].mean():.2f} / 5")
    col4.metric('Late Delivery Rate', f"{df['is_late'].mean()*100:.1f}%")
    col5.metric('Unique Customers', f"{df['customer_state'].count():,}")

    st.markdown('---')
    st.subheader('Monthly Revenue Trend')

    fig, ax1 = plt.subplots(figsize=(14, 4))
    ax2 = ax1.twinx()
    ax1.bar(monthly['month'], monthly['total_revenue'], width=20,
            color=BLUE, alpha=0.75, label='Revenue (BRL)')
    ax2.plot(monthly['month'], monthly['total_orders'], color=CORAL,
             linewidth=2.5, marker='o', markersize=4, label='Orders')
    ax1.set_ylabel('Total Revenue (BRL)', color=BLUE)
    ax2.set_ylabel('Order Count', color=CORAL)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e3:.0f}K'))
    ax1.tick_params(axis='x', rotation=45)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown('---')
    st.subheader('Key Findings')
    col_a, col_b = st.columns(2)
    with col_a:
        st.success('**Health & Beauty** is the top revenue category at R$1.26M')
        st.success('**Credit card** dominates payments at ~74% of all transactions')
        st.info('Peak shopping hours are between **10:00 and 21:00**')
    with col_b:
        st.error('Late deliveries score **2.57 avg stars** vs 4.29 for on-time — a 40% gap')
        st.error('**54% of late orders** receive a low score (1–2 stars)')
        st.warning('Customer repeat rate is only **3%** — retention is a major opportunity')

elif page == 'Revenue & Products':
    st.title('💰 Revenue & Product Analysis')
    st.markdown('---')

    st.subheader('Top 15 Product Categories by Revenue')
    cats = (
        df.groupby('category')['price']
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.barh(cats['category'][::-1], cats['price'][::-1], color=BLUE, alpha=0.85)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e3:.0f}K'))
    ax.set_xlabel('Total Revenue (BRL)')
    for i, (val, cat) in enumerate(zip(cats['price'][::-1], cats['category'][::-1])):
        ax.text(val + 1000, i, f'R${val/1e3:.0f}K', va='center', fontsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown('---')
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Revenue by Month')
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(monthly['month'].dt.strftime('%b %Y'), monthly['total_revenue'],
                color=BLUE, alpha=0.8)
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e3:.0f}K'))
        ax2.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    with col2:
        st.subheader('Payment Method Distribution')
        pay = df.groupby('payment_type')['price'].count().reset_index()
        pay.columns = ['payment_type', 'count']
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.pie(pay['count'], labels=pay['payment_type'], autopct='%1.1f%%',
                colors=[BLUE, GREEN, CORAL, GOLD], startangle=140)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()

    st.markdown('---')
    st.subheader('Order Volume by Hour of Day')
    hourly = df.groupby('hour_of_day')['order_id'].nunique().reset_index()
    fig4, ax4 = plt.subplots(figsize=(14, 4))
    colors = [CORAL if h in range(10, 22) else BLUE for h in hourly['hour_of_day']]
    ax4.bar(hourly['hour_of_day'], hourly['order_id'], color=colors, alpha=0.85)
    ax4.set_xlabel('Hour of Day (24h)')
    ax4.set_ylabel('Total Orders')
    ax4.set_xticks(range(0, 24))
    ax4.axvspan(9.5, 21.5, alpha=0.07, color=CORAL, label='Peak hours (10:00–21:00)')
    ax4.legend()
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

elif page == 'Delivery Performance':
    st.title('🚚 Delivery Performance Analysis')
    st.markdown('---')

    col1, col2, col3 = st.columns(3)
    col1.metric('Avg Delivery Time', f"{df['delivery_days'].mean():.1f} days")
    col2.metric('Late Orders', f"{df['is_late'].sum():,}")
    col3.metric('On-Time Rate', f"{(1 - df['is_late'].mean())*100:.1f}%")

    st.markdown('---')
    st.subheader('Late Delivery Rate by State')
    fig, ax = plt.subplots(figsize=(14, 5))
    state_sorted = states.sort_values('late_pct', ascending=False)
    colors = [CORAL if p > states['late_pct'].mean() else BLUE for p in state_sorted['late_pct']]
    ax.bar(state_sorted['customer_state'], state_sorted['late_pct'], color=colors, alpha=0.85)
    ax.axhline(states['late_pct'].mean(), color='black', linestyle='--', linewidth=1.2,
               label=f"Average: {states['late_pct'].mean():.1f}%")
    ax.set_xlabel('Customer State')
    ax.set_ylabel('Late Delivery Rate (%)')
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown('---')
    st.subheader('Impact of Late Delivery on Review Scores')
    col_a, col_b = st.columns(2)

    with col_a:
        late_summary = df.groupby('is_late')['review_score'].mean().reset_index()
        late_summary['label'] = late_summary['is_late'].map({True: 'Late', False: 'On Time'})
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        bars = ax2.bar(late_summary['label'], late_summary['review_score'],
                       color=[CORAL, GREEN], alpha=0.85, width=0.4)
        ax2.set_ylim(0, 5)
        ax2.set_ylabel('Average Review Score')
        ax2.set_title('Avg Review: Late vs On-Time')
        for bar, val in zip(bars, late_summary['review_score']):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                     f'{val:.2f}', ha='center', fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    with col_b:
        score_dist = df.groupby(['is_late', 'review_score']).size().reset_index(name='count')
        score_dist['label'] = score_dist['is_late'].map({True: 'Late', False: 'On Time'})
        pivot = score_dist.pivot(index='review_score', columns='label', values='count').fillna(0)
        pivot_pct = pivot.div(pivot.sum()) * 100
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        pivot_pct.plot(kind='bar', ax=ax3, color=[CORAL, GREEN], alpha=0.85, width=0.6)
        ax3.set_xlabel('Review Score')
        ax3.set_ylabel('Share of Orders (%)')
        ax3.set_title('Score Distribution by Delivery Status')
        ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()

    st.markdown('---')
    st.subheader('Average Delivery Days by State')
    fig4, ax4 = plt.subplots(figsize=(14, 5))
    state_days = states.sort_values('avg_delivery_days', ascending=False)
    ax4.bar(state_days['customer_state'], state_days['avg_delivery_days'], color=BLUE, alpha=0.8)
    ax4.axhline(states['avg_delivery_days'].mean(), color=CORAL, linestyle='--',
                linewidth=1.2, label=f"Average: {states['avg_delivery_days'].mean():.1f} days")
    ax4.set_xlabel('Customer State')
    ax4.set_ylabel('Avg Delivery Days')
    ax4.legend()
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

elif page == 'Customer Insights':
    st.title('👥 Customer Insights')
    st.markdown('---')

    col1, col2, col3 = st.columns(3)
    col1.metric('Unique States', df['customer_state'].nunique())
    col2.metric('Avg Review Score', f"{df['review_score'].mean():.2f}")
    col3.metric('Avg Items per Order',
                f"{df.groupby('order_id')['price'].count().mean():.2f}")

    st.markdown('---')
    st.subheader('Review Score Distribution')
    fig, ax = plt.subplots(figsize=(10, 4))
    score_counts = df['review_score'].value_counts().sort_index()
    colors = [GREEN if s >= 4 else CORAL if s <= 2 else GOLD for s in score_counts.index]
    ax.bar(score_counts.index, score_counts.values, color=colors, alpha=0.85)
    ax.set_xlabel('Review Score')
    ax.set_ylabel('Number of Orders')
    ax.set_title('Distribution of Customer Review Scores')
    for i, (score, count) in enumerate(zip(score_counts.index, score_counts.values)):
        ax.text(score, count + 100, f'{count:,}', ha='center', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown('---')
    st.subheader('Orders and Revenue by State')
    fig2, axes = plt.subplots(1, 2, figsize=(14, 5))
    top_states_orders = states.sort_values('total_orders', ascending=False).head(10)
    top_states_rev    = states.sort_values('total_revenue', ascending=False).head(10)

    axes[0].barh(top_states_orders['customer_state'][::-1],
                 top_states_orders['total_orders'][::-1], color=BLUE, alpha=0.85)
    axes[0].set_title('Top 10 States by Order Volume')
    axes[0].set_xlabel('Total Orders')

    axes[1].barh(top_states_rev['customer_state'][::-1],
                 top_states_rev['total_revenue'][::-1] / 1e6, color=GREEN, alpha=0.85)
    axes[1].set_title('Top 10 States by Revenue')
    axes[1].set_xlabel('Revenue (R$ Millions)')
    axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:.1f}M'))

    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

    st.markdown('---')
    st.subheader('Avg Review Score by State')
    fig3, ax3 = plt.subplots(figsize=(14, 4))
    state_review = states.sort_values('avg_review_score')
    colors = [GREEN if s >= 4 else CORAL if s < 3.5 else GOLD
              for s in state_review['avg_review_score']]
    ax3.bar(state_review['customer_state'], state_review['avg_review_score'],
            color=colors, alpha=0.85)
    ax3.axhline(states['avg_review_score'].mean(), color='black', linestyle='--',
                linewidth=1.2, label=f"Average: {states['avg_review_score'].mean():.2f}")
    ax3.set_ylim(0, 5)
    ax3.set_xlabel('Customer State')
    ax3.set_ylabel('Avg Review Score')
    ax3.legend()
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()