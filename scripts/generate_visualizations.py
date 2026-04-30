import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

Path('docs/visualizations').mkdir(parents=True, exist_ok=True)

sns.set_theme(style='whitegrid', palette='muted')
BLUE = '#2E86AB'
CORAL = '#E84855'
GREEN = '#3BB273'

def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)

def plot_monthly_revenue(engine):
    df = pd.read_sql("""
        SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
               COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(i.price + i.freight_value)::numeric, 2) AS total_revenue
        FROM orders_clean o
        JOIN order_items_clean i ON o.order_id = i.order_id
        GROUP BY 1 ORDER BY 1
    """, engine, parse_dates=['month'])

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    ax1.bar(df['month'], df['total_revenue'], width=25, color=BLUE, alpha=0.75, label='Revenue (BRL)')
    ax2.plot(df['month'], df['total_orders'], color=CORAL, linewidth=2.5, marker='o', markersize=4, label='Orders')

    ax1.set_title('Monthly Revenue and Order Volume (2016–2018)', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('')
    ax1.set_ylabel('Total Revenue (BRL)', color=BLUE)
    ax2.set_ylabel('Order Count', color=CORAL)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
    ax1.tick_params(axis='x', rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig('docs/visualizations/01_monthly_revenue.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 01_monthly_revenue.png')

def plot_top_categories(engine):
    df = pd.read_sql("""
        SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
               ROUND(SUM(i.price)::numeric, 2) AS total_revenue
        FROM order_items_clean i
        JOIN products_clean p ON i.product_id = p.product_id
        LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
        GROUP BY 1 ORDER BY total_revenue DESC LIMIT 15
    """, engine)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(df['category'][::-1], df['total_revenue'][::-1], color=BLUE, alpha=0.85)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e6:.1f}M'))
    ax.set_title('Top 15 Product Categories by Revenue', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Total Revenue (BRL)')
    ax.set_ylabel('')

    for bar, val in zip(bars, df['total_revenue'][::-1]):
        ax.text(bar.get_width() + 5000, bar.get_y() + bar.get_height()/2,
                f'R${val/1e3:.0f}K', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig('docs/visualizations/02_top_categories.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 02_top_categories.png')

def plot_late_delivery_by_state(engine):
    df = pd.read_sql("""
        SELECT c.customer_state,
               COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS late_pct,
               ROUND(AVG(o.delivery_days)::numeric, 1) AS avg_days
        FROM orders_clean o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY 1
        HAVING COUNT(DISTINCT o.order_id) >= 100
        ORDER BY late_pct DESC
    """, engine)

    fig, ax = plt.subplots(figsize=(14, 6))
    colors = [CORAL if p > 15 else BLUE for p in df['late_pct']]
    bars = ax.bar(df['customer_state'], df['late_pct'], color=colors, alpha=0.85)
    ax.axhline(df['late_pct'].mean(), color='black', linestyle='--', linewidth=1.2, label=f"Average: {df['late_pct'].mean():.1f}%")
    ax.set_title('Late Delivery Rate by State (states with 100+ orders)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Customer State')
    ax.set_ylabel('Late Delivery Rate (%)')
    ax.legend()
    plt.tight_layout()
    plt.savefig('docs/visualizations/03_late_delivery_by_state.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 03_late_delivery_by_state.png')

def plot_review_vs_lateness(engine):
    df = pd.read_sql("""
        SELECT o.is_late,
               r.review_score,
               COUNT(*) AS count
        FROM orders_clean o
        JOIN order_reviews_clean r ON o.order_id = r.order_id
        GROUP BY 1, 2 ORDER BY 1, 2
    """, engine)

    df['delivery_status'] = df['is_late'].map({True: 'Late', False: 'On Time'})

    fig, ax = plt.subplots(figsize=(9, 5))
    pivot = df.pivot_table(index='review_score', columns='delivery_status', values='count', aggfunc='sum')
    pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100
    pivot_pct.plot(kind='bar', ax=ax, color=[CORAL, GREEN], alpha=0.85, width=0.6)
    ax.set_title('Review Score Distribution: Late vs On-Time Deliveries', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Review Score')
    ax.set_ylabel('Share of Orders (%)')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title='Delivery Status')
    plt.tight_layout()
    plt.savefig('docs/visualizations/04_review_vs_lateness.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 04_review_vs_lateness.png')

def plot_payment_methods(engine):
    df = pd.read_sql("""
        SELECT payment_type, COUNT(*) AS transactions,
               ROUND(SUM(payment_value)::numeric, 2) AS total_value
        FROM order_payments
        WHERE payment_type != 'not_defined'
        GROUP BY 1 ORDER BY transactions DESC
    """, engine)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].pie(df['transactions'], labels=df['payment_type'], autopct='%1.1f%%',
                colors=[BLUE, GREEN, CORAL, '#F4A261'], startangle=140)
    axes[0].set_title('Payment Method Share by Transaction Count', fontweight='bold')

    axes[1].bar(df['payment_type'], df['total_value'] / 1e6,
                color=[BLUE, GREEN, CORAL, '#F4A261'], alpha=0.85)
    axes[1].set_title('Total Value by Payment Method (R$ Millions)', fontweight='bold')
    axes[1].set_ylabel('Total Value (R$ M)')
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:.0f}M'))

    plt.suptitle('Payment Method Analysis', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('docs/visualizations/05_payment_methods.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 05_payment_methods.png')

def plot_hourly_orders(engine):
    df = pd.read_sql("""
        SELECT EXTRACT(HOUR FROM order_purchase_timestamp)::int AS hour_of_day,
               COUNT(DISTINCT order_id) AS total_orders
        FROM orders_clean
        GROUP BY 1 ORDER BY 1
    """, engine)

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = [CORAL if h in range(10, 22) else BLUE for h in df['hour_of_day']]
    ax.bar(df['hour_of_day'], df['total_orders'], color=colors, alpha=0.85)
    ax.set_title('Order Volume by Hour of Day', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Hour of Day (24h)')
    ax.set_ylabel('Total Orders')
    ax.set_xticks(range(0, 24))
    ax.axvspan(9.5, 21.5, alpha=0.07, color=CORAL, label='Peak hours (10:00–21:00)')
    ax.legend()
    plt.tight_layout()
    plt.savefig('docs/visualizations/06_hourly_orders.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 06_hourly_orders.png')

if __name__ == '__main__':
    engine = get_engine()
    print('Generating visualizations...\n')
    plot_monthly_revenue(engine)
    plot_top_categories(engine)
    plot_late_delivery_by_state(engine)
    plot_review_vs_lateness(engine)
    plot_payment_methods(engine)
    plot_hourly_orders(engine)
    print('\nAll visualizations saved to docs/visualizations/')