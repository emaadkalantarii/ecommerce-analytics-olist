import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

Path('docs/visualizations').mkdir(parents=True, exist_ok=True)

sns.set_theme(style='whitegrid', palette='muted')
BLUE  = '#2E86AB'
CORAL = '#E84855'
GREEN = '#3BB273'
GOLD  = '#F4A261'

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

    df = df[df['total_orders'] > 10]

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    ax1.bar(df['month'], df['total_revenue'], width=20, color=BLUE, alpha=0.75, label='Revenue (BRL)')
    ax2.plot(df['month'], df['total_orders'], color=CORAL, linewidth=2.5,
             marker='o', markersize=4, label='Order Count')

    ax1.set_title('Monthly Revenue and Order Volume (2016–2018)', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel('Total Revenue (BRL)', color=BLUE, fontsize=11)
    ax2.set_ylabel('Order Count', color=CORAL, fontsize=11)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e3:.0f}K'))
    ax1.tick_params(axis='x', rotation=45)
    ax1.tick_params(axis='y', labelcolor=BLUE)
    ax2.tick_params(axis='y', labelcolor=CORAL)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

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
    ax.set_xlabel('Total Revenue (BRL)', fontsize=11)

    for bar, val in zip(bars, df['total_revenue'][::-1]):
        ax.text(bar.get_width() + 3000, bar.get_y() + bar.get_height() / 2,
                f'R${val/1e3:.0f}K', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig('docs/visualizations/02_top_categories.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 02_top_categories.png')

def plot_late_delivery_by_state(engine):
    df = pd.read_sql("""
        SELECT c.customer_state,
               COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS late_pct
        FROM orders_clean o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY 1
        HAVING COUNT(DISTINCT o.order_id) >= 100
        ORDER BY late_pct DESC
    """, engine)

    avg = df['late_pct'].mean()
    colors = [CORAL if p > avg else BLUE for p in df['late_pct']]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(df['customer_state'], df['late_pct'], color=colors, alpha=0.85)
    ax.axhline(avg, color='black', linestyle='--', linewidth=1.2)

    above_patch = mpatches.Patch(color=CORAL, alpha=0.85, label=f'Above average (>{avg:.1f}%)')
    below_patch = mpatches.Patch(color=BLUE,  alpha=0.85, label=f'Below average (<{avg:.1f}%)')
    avg_line    = plt.Line2D([0], [0], color='black', linestyle='--', linewidth=1.2,
                             label=f'National average: {avg:.1f}%')
    ax.legend(handles=[above_patch, below_patch, avg_line], loc='upper right', framealpha=0.9)

    ax.set_title('Late Delivery Rate by State (states with 100+ orders)',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Customer State', fontsize=11)
    ax.set_ylabel('Late Delivery Rate (%)', fontsize=11)
    plt.tight_layout()
    plt.savefig('docs/visualizations/03_late_delivery_by_state.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 03_late_delivery_by_state.png')

def plot_review_vs_lateness(engine):
    df = pd.read_sql("""
        SELECT o.is_late, r.review_score, COUNT(*) AS count
        FROM orders_clean o
        JOIN order_reviews_clean r ON o.order_id = r.order_id
        GROUP BY 1, 2 ORDER BY 1, 2
    """, engine)

    df['delivery_status'] = df['is_late'].map({True: 'Late', False: 'On Time'})

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    avg_scores = df.groupby('delivery_status').apply(
        lambda x: (x['review_score'] * x['count']).sum() / x['count'].sum()
    ).reset_index()
    avg_scores.columns = ['delivery_status', 'avg_score']
    avg_scores['color'] = avg_scores['delivery_status'].map({'On Time': GREEN, 'Late': CORAL})

    bars = axes[0].bar(avg_scores['delivery_status'], avg_scores['avg_score'],
                       color=avg_scores['color'], alpha=0.85, width=0.4)
    axes[0].set_ylim(0, 5)
    axes[0].set_ylabel('Average Review Score', fontsize=11)
    axes[0].set_title('Avg Review Score: Late vs On-Time', fontsize=12, fontweight='bold')

    on_time_patch = mpatches.Patch(color=GREEN, alpha=0.85, label='On Time')
    late_patch    = mpatches.Patch(color=CORAL, alpha=0.85, label='Late')
    axes[0].legend(handles=[on_time_patch, late_patch], framealpha=0.9)

    for bar, val in zip(bars, avg_scores['avg_score']):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                     f'{val:.2f}', ha='center', fontweight='bold', fontsize=11)

    pivot = df.pivot_table(index='review_score', columns='delivery_status',
                           values='count', aggfunc='sum').fillna(0)
    pivot_pct = pivot.div(pivot.sum()) * 100

    pivot_pct[['On Time', 'Late']].plot(
        kind='bar', ax=axes[1],
        color=[GREEN, CORAL],
        alpha=0.85, width=0.6
    )
    axes[1].set_xlabel('Review Score', fontsize=11)
    axes[1].set_ylabel('Share of Orders (%)', fontsize=11)
    axes[1].set_title('Score Distribution: Late vs On-Time', fontsize=12, fontweight='bold')
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=0)
    axes[1].legend(title='Delivery Status', framealpha=0.9)

    plt.suptitle('Impact of Late Delivery on Customer Review Scores',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('docs/visualizations/04_review_vs_lateness.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 04_review_vs_lateness.png')

def plot_payment_methods(engine):
    df = pd.read_sql("""
        SELECT payment_type, COUNT(*) AS transactions,
               ROUND(SUM(payment_value)::numeric, 2) AS total_value
        FROM order_payments_clean
        GROUP BY 1 ORDER BY transactions DESC
    """, engine)

    label_map = {
        'credit_card': 'Credit Card',
        'boleto':      'Boleto',
        'voucher':     'Voucher',
        'debit_card':  'Debit Card'
    }
    df['label'] = df['payment_type'].map(label_map).fillna(df['payment_type'])

    colors = [BLUE, GREEN, GOLD, CORAL]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    wedges, texts, autotexts = axes[0].pie(
        df['transactions'],
        labels=None,
        autopct='%1.1f%%',
        colors=colors,
        startangle=140,
        pctdistance=0.75,
        wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'}
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')

    axes[0].legend(wedges, df['label'], title='Payment Method',
                   loc='lower left', bbox_to_anchor=(-0.15, -0.1), framealpha=0.9)
    axes[0].set_title('Transaction Share by Payment Method', fontsize=12, fontweight='bold')

    bars = axes[1].bar(df['label'], df['total_value'] / 1e6, color=colors, alpha=0.85)
    axes[1].set_title('Total Revenue by Payment Method', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Total Value (R$ Millions)', fontsize=11)
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:.0f}M'))
    axes[1].tick_params(axis='x', rotation=15)

    for bar, val in zip(bars, df['total_value'] / 1e6):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                     f'R${val:.1f}M', ha='center', fontsize=9, fontweight='bold')

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

    peak_hours = list(range(10, 22))
    colors = [CORAL if h in peak_hours else BLUE for h in df['hour_of_day']]

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.bar(df['hour_of_day'], df['total_orders'], color=colors, alpha=0.85)
    ax.axvspan(9.5, 21.5, alpha=0.07, color=CORAL)
    ax.set_title('Order Volume by Hour of Day', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Hour of Day (24h)', fontsize=11)
    ax.set_ylabel('Total Orders', fontsize=11)
    ax.set_xticks(range(0, 24))

    peak_patch = mpatches.Patch(color=CORAL, alpha=0.85, label='Peak hours (10:00–21:00)')
    off_patch  = mpatches.Patch(color=BLUE,  alpha=0.85, label='Off-peak hours')
    ax.legend(handles=[peak_patch, off_patch], framealpha=0.9)

    plt.tight_layout()
    plt.savefig('docs/visualizations/06_hourly_orders.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 06_hourly_orders.png')

def plot_review_score_distribution(engine):
    df = pd.read_sql("""
        SELECT review_score, COUNT(*) AS count
        FROM order_reviews_clean
        GROUP BY 1 ORDER BY 1
    """, engine)

    colors = [GREEN if s >= 4 else CORAL if s <= 2 else GOLD for s in df['review_score']]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(df['review_score'], df['count'], color=colors, alpha=0.85, width=0.6)
    ax.set_title('Customer Review Score Distribution', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Review Score', fontsize=11)
    ax.set_ylabel('Number of Reviews', fontsize=11)
    ax.set_xticks([1, 2, 3, 4, 5])

    for bar, val in zip(bars, df['count']):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
                f'{val:,}', ha='center', fontsize=9, fontweight='bold')

    positive_patch = mpatches.Patch(color=GREEN, alpha=0.85, label='Positive (4–5 stars)')
    neutral_patch  = mpatches.Patch(color=GOLD,  alpha=0.85, label='Neutral (3 stars)')
    negative_patch = mpatches.Patch(color=CORAL, alpha=0.85, label='Negative (1–2 stars)')
    ax.legend(handles=[positive_patch, neutral_patch, negative_patch], framealpha=0.9)

    plt.tight_layout()
    plt.savefig('docs/visualizations/07_review_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved: 07_review_distribution.png')

if __name__ == '__main__':
    engine = get_engine()
    print('Generating visualizations...\n')
    plot_monthly_revenue(engine)
    plot_top_categories(engine)
    plot_late_delivery_by_state(engine)
    plot_review_vs_lateness(engine)
    plot_payment_methods(engine)
    plot_hourly_orders(engine)
    plot_review_score_distribution(engine)
    print('\nAll visualizations saved to docs/visualizations/')