import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)

class DataValidator:
    def __init__(self, engine):
        self.engine = engine
        self.results = []
        self.passed = 0
        self.failed = 0

    def check(self, table, description, query, expect_zero=True):
        with self.engine.connect() as conn:
            result = conn.execute(text(query)).scalar()
        passed = (result == 0) if expect_zero else (result > 0)
        status = 'PASS' if passed else 'FAIL'
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        self.results.append({
            'table': table,
            'check': description,
            'result': result,
            'status': status
        })
        print(f'  [{status}] {description} (value: {result:,})')

    def summary(self):
        total = self.passed + self.failed
        print(f'\n{"="*55}')
        print(f'  Validation Summary: {self.passed}/{total} checks passed')
        if self.failed > 0:
            print(f'  FAILED CHECKS:')
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f'    - [{r["table"]}] {r["check"]}')
        print(f'{"="*55}\n')
        return self.failed == 0

def run_validation(validator):
    print('\n--- Raw Layer Checks ---')

    validator.check(
        'orders', 'No duplicate order_ids in raw orders',
        "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders"
    )
    validator.check(
        'customers', 'No duplicate customer_ids in raw customers',
        "SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM customers"
    )
    validator.check(
        'products', 'No duplicate product_ids in raw products',
        "SELECT COUNT(*) - COUNT(DISTINCT product_id) FROM products"
    )
    validator.check(
        'order_items', 'No negative prices in order_items',
        "SELECT COUNT(*) FROM order_items WHERE price < 0"
    )
    validator.check(
        'order_reviews', 'Review scores within valid range 1-5',
        "SELECT COUNT(*) FROM order_reviews WHERE review_score NOT BETWEEN 1 AND 5"
    )
    validator.check(
        'orders', 'No orders with purchase timestamp after delivery',
        """SELECT COUNT(*) FROM orders
           WHERE order_delivered_customer_date < order_purchase_timestamp"""
    )

    print('\n--- Clean Layer Checks ---')

    validator.check(
        'orders_clean', 'All orders in clean layer have delivered status',
        "SELECT COUNT(*) FROM orders_clean WHERE order_status != 'delivered'"
    )
    validator.check(
        'orders_clean', 'No negative delivery days in clean orders',
        "SELECT COUNT(*) FROM orders_clean WHERE delivery_days <= 0"
    )
    validator.check(
        'orders_clean', 'No null delivery_days in clean orders',
        "SELECT COUNT(*) FROM orders_clean WHERE delivery_days IS NULL"
    )
    validator.check(
        'order_items_clean', 'No zero or negative prices in clean order items',
        "SELECT COUNT(*) FROM order_items_clean WHERE price <= 0"
    )
    validator.check(
        'products_clean', 'No null category names in clean products',
        "SELECT COUNT(*) FROM products_clean WHERE product_category_name IS NULL"
    )
    validator.check(
        'order_reviews_clean', 'No null review scores in clean reviews',
        "SELECT COUNT(*) FROM order_reviews_clean WHERE review_score IS NULL"
    )

    print('\n--- Referential Integrity Checks ---')

    validator.check(
        'orders_clean', 'All clean orders have matching customer',
        """SELECT COUNT(*) FROM orders_clean o
           LEFT JOIN customers c ON o.customer_id = c.customer_id
           WHERE c.customer_id IS NULL"""
    )
    validator.check(
        'order_items_clean', 'All clean order items have matching order',
        """SELECT COUNT(*) FROM order_items_clean i
           LEFT JOIN orders_clean o ON i.order_id = o.order_id
           WHERE o.order_id IS NULL"""
    )
    validator.check(
        'order_items_clean', 'All clean order items have matching product',
        """SELECT COUNT(*) FROM order_items_clean i
           LEFT JOIN products_clean p ON i.product_id = p.product_id
           WHERE p.product_id IS NULL"""
    )

    print('\n--- Business Logic Checks ---')

    validator.check(
        'orders_clean', 'Dataset contains expected minimum order volume',
        "SELECT CASE WHEN COUNT(*) >= 90000 THEN 0 ELSE 1 END FROM orders_clean"
    )
    validator.check(
        'orders_clean', 'Monthly summary covers expected date range',
        """SELECT CASE WHEN COUNT(DISTINCT DATE_TRUNC('month', order_purchase_timestamp)) >= 20
                  THEN 0 ELSE 1 END FROM orders_clean"""
    )
    validator.check(
        'order_payments_clean', 'No payment values of exactly zero',
        "SELECT COUNT(*) FROM order_payments_clean WHERE payment_value = 0 AND payment_type != 'voucher'"
    )

if __name__ == '__main__':
    print('='*55)
    print('  Olist Data Quality Validation Report')
    print(f'  Run at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*55)

    engine = get_engine()
    validator = DataValidator(engine)
    run_validation(validator)
    all_passed = validator.summary()

    if not all_passed:
        exit(1)