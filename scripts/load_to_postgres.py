import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)

def drop_all_tables(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS order_reviews CASCADE;
            DROP TABLE IF EXISTS order_payments CASCADE;
            DROP TABLE IF EXISTS order_items CASCADE;
            DROP TABLE IF EXISTS orders CASCADE;
            DROP TABLE IF EXISTS category_translation CASCADE;
            DROP TABLE IF EXISTS products CASCADE;
            DROP TABLE IF EXISTS sellers CASCADE;
            DROP TABLE IF EXISTS geolocation CASCADE;
            DROP TABLE IF EXISTS customers CASCADE;
        """))
        conn.commit()
    print("Existing tables dropped")

def create_schema(engine):
    with open('sql/create_tables.sql', 'r') as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("Schema created successfully")

def load_tables(engine):
    tables = [
        ('customers',            'olist_customers_dataset.csv'),
        ('geolocation',          'olist_geolocation_dataset.csv'),
        ('sellers',              'olist_sellers_dataset.csv'),
        ('products',             'olist_products_dataset.csv'),
        ('category_translation', 'product_category_name_translation.csv'),
        ('orders',               'olist_orders_dataset.csv'),
        ('order_items',          'olist_order_items_dataset.csv'),
        ('order_payments',       'olist_order_payments_dataset.csv'),
        ('order_reviews',        'olist_order_reviews_dataset.csv'),
    ]

    for table_name, filename in tables:
        path = Path('data/raw') / filename
        print(f"Loading {filename}...")
        df = pd.read_csv(path, low_memory=False)
        df.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"  {table_name}: {len(df):,} rows loaded")

if __name__ == '__main__':
    engine = get_engine()
    drop_all_tables(engine)
    create_schema(engine)
    load_tables(engine)