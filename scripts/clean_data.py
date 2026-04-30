import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)

def clean_orders(engine):
    df = pd.read_sql('SELECT * FROM orders', engine)

    timestamp_cols = [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df = df[df['order_status'] == 'delivered'].copy()
    df = df.dropna(subset=['order_delivered_customer_date', 'order_purchase_timestamp'])

    df['delivery_days'] = (
        df['order_delivered_customer_date'] - df['order_purchase_timestamp']
    ).dt.days

    df['is_late'] = (
        df['order_delivered_customer_date'] > df['order_estimated_delivery_date']
    )

    df = df[df['delivery_days'] > 0]

    df.to_sql('orders_clean', engine, if_exists='replace', index=False)
    print(f'orders_clean: {len(df):,} rows')

def clean_products(engine):
    df = pd.read_sql('SELECT * FROM products', engine)

    df = df.rename(columns={
        'product_name_lenght': 'product_name_length',
        'product_description_lenght': 'product_description_length'
    })

    df['product_category_name'] = df['product_category_name'].fillna('unknown')

    df.to_sql('products_clean', engine, if_exists='replace', index=False)
    print(f'products_clean: {len(df):,} rows')

def clean_order_items(engine):
    df = pd.read_sql('SELECT * FROM order_items', engine)

    df = df[df['price'] > 0].copy()
    df = df[df['freight_value'] >= 0].copy()

    df.to_sql('order_items_clean', engine, if_exists='replace', index=False)
    print(f'order_items_clean: {len(df):,} rows')

def clean_reviews(engine):
    df = pd.read_sql('SELECT * FROM order_reviews', engine)

    df = df.dropna(subset=['review_score']).copy()
    df['review_score'] = df['review_score'].astype(int)

    df.to_sql('order_reviews_clean', engine, if_exists='replace', index=False)
    print(f'order_reviews_clean: {len(df):,} rows')

def clean_geolocation(engine):
    df = pd.read_sql('SELECT * FROM geolocation', engine)

    df = df.drop_duplicates(subset=['geolocation_zip_code_prefix'])

    df.to_sql('geolocation_clean', engine, if_exists='replace', index=False)
    print(f'geolocation_clean: {len(df):,} rows')

if __name__ == '__main__':
    engine = get_engine()
    print('Starting data cleaning...\n')
    clean_orders(engine)
    clean_products(engine)
    clean_order_items(engine)
    clean_reviews(engine)
    clean_geolocation(engine)
    print('\nAll cleaning complete.')