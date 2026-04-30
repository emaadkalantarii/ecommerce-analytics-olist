import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

Path('data/processed').mkdir(parents=True, exist_ok=True)

def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)

def export_main_dataset(engine):
    df = pd.read_sql("""
        SELECT
            o.order_id,
            o.order_purchase_timestamp,
            EXTRACT(YEAR FROM o.order_purchase_timestamp)::int  AS year,
            EXTRACT(MONTH FROM o.order_purchase_timestamp)::int AS month,
            EXTRACT(DOW FROM o.order_purchase_timestamp)::int   AS day_of_week,
            EXTRACT(HOUR FROM o.order_purchase_timestamp)::int  AS hour_of_day,
            o.delivery_days,
            o.is_late,
            c.customer_state,
            c.customer_city,
            COALESCE(t.product_category_name_english,
                     p.product_category_name, 'unknown')        AS category,
            i.price,
            i.freight_value,
            i.price + i.freight_value                           AS total_item_value,
            i.seller_id,
            r.review_score,
            pay.payment_type,
            pay.payment_value,
            pay.payment_installments,
            g.geolocation_lat                                   AS customer_lat,
            g.geolocation_lng                                   AS customer_lng
        FROM orders_clean o
        JOIN customers c              ON o.customer_id = c.customer_id
        JOIN order_items_clean i      ON o.order_id = i.order_id
        JOIN products_clean p         ON i.product_id = p.product_id
        LEFT JOIN category_translation t   ON p.product_category_name = t.product_category_name
        LEFT JOIN order_reviews_clean r    ON o.order_id = r.order_id
        LEFT JOIN order_payments pay       ON o.order_id = pay.order_id
                                        AND pay.payment_sequential = 1
        LEFT JOIN geolocation_clean g      ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
    """, engine, parse_dates=['order_purchase_timestamp'])

    df.to_csv('data/processed/dashboard_data.csv', index=False)
    print(f'Exported dashboard_data.csv: {len(df):,} rows, {len(df.columns)} columns')

def export_monthly_summary(engine):
    df = pd.read_sql("""
        SELECT
            DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
            COUNT(DISTINCT o.order_id)                       AS total_orders,
            ROUND(SUM(i.price)::numeric, 2)                  AS product_revenue,
            ROUND(SUM(i.freight_value)::numeric, 2)          AS freight_revenue,
            ROUND(SUM(i.price + i.freight_value)::numeric, 2) AS total_revenue,
            ROUND(AVG(o.delivery_days)::numeric, 1)          AS avg_delivery_days,
            ROUND(SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS late_pct,
            ROUND(AVG(r.review_score)::numeric, 2)           AS avg_review_score
        FROM orders_clean o
        JOIN order_items_clean i      ON o.order_id = i.order_id
        LEFT JOIN order_reviews_clean r ON o.order_id = r.order_id
        GROUP BY 1 ORDER BY 1
    """, engine)

    df.to_csv('data/processed/monthly_summary.csv', index=False)
    print(f'Exported monthly_summary.csv: {len(df):,} rows')

def export_state_summary(engine):
    df = pd.read_sql("""
        SELECT
            c.customer_state,
            COUNT(DISTINCT o.order_id)                        AS total_orders,
            ROUND(SUM(i.price)::numeric, 2)                   AS total_revenue,
            ROUND(AVG(o.delivery_days)::numeric, 1)           AS avg_delivery_days,
            ROUND(SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS late_pct,
            ROUND(AVG(r.review_score)::numeric, 2)            AS avg_review_score
        FROM orders_clean o
        JOIN customers c              ON o.customer_id = c.customer_id
        JOIN order_items_clean i      ON o.order_id = i.order_id
        LEFT JOIN order_reviews_clean r ON o.order_id = r.order_id
        GROUP BY 1 ORDER BY total_revenue DESC
    """, engine)

    df.to_csv('data/processed/state_summary.csv', index=False)
    print(f'Exported state_summary.csv: {len(df):,} rows')

if __name__ == '__main__':
    engine = get_engine()
    print('Exporting dashboard data...\n')
    export_main_dataset(engine)
    export_monthly_summary(engine)
    export_state_summary(engine)
    print('\nAll exports complete.')