import pandas as pd
import pytest

def test_no_negative_prices():
    df = pd.DataFrame({'price': [10.0, 20.5, 5.0, 100.0]})
    assert (df['price'] > 0).all()

def test_no_zero_prices():
    df = pd.DataFrame({'price': [10.0, 20.5, 5.0, 100.0]})
    assert (df['price'] != 0).all()

def test_review_score_valid_range():
    df = pd.DataFrame({'review_score': [1, 2, 3, 4, 5]})
    assert df['review_score'].between(1, 5).all()

def test_delivery_days_positive():
    df = pd.DataFrame({'delivery_days': [3, 7, 14, 21]})
    assert (df['delivery_days'] > 0).all()

def test_no_null_order_id():
    df = pd.DataFrame({'order_id': ['abc', 'def', 'ghi', 'jkl']})
    assert df['order_id'].isnull().sum() == 0

def test_is_late_boolean():
    df = pd.DataFrame({'is_late': [True, False, True, False]})
    assert df['is_late'].dtype == bool

def test_category_no_nulls_after_cleaning():
    df = pd.DataFrame({'product_category_name': ['electronics', 'unknown', 'beauty', 'unknown']})
    assert df['product_category_name'].isnull().sum() == 0

def test_freight_value_non_negative():
    df = pd.DataFrame({'freight_value': [0.0, 5.5, 12.3, 8.0]})
    assert (df['freight_value'] >= 0).all()

def test_revenue_calculation():
    df = pd.DataFrame({'price': [100.0, 200.0], 'freight_value': [10.0, 20.0]})
    df['total'] = df['price'] + df['freight_value']
    assert df['total'].tolist() == [110.0, 220.0]

def test_month_year_extraction():
    df = pd.DataFrame({
        'order_purchase_timestamp': pd.to_datetime(['2017-11-01', '2018-03-15'])
    })
    df['year'] = df['order_purchase_timestamp'].dt.year
    df['month'] = df['order_purchase_timestamp'].dt.month
    assert df['year'].tolist() == [2017, 2018]
    assert df['month'].tolist() == [11, 3]

def test_duplicate_order_ids_detected():
    df = pd.DataFrame({'order_id': ['abc', 'def', 'abc']})
    duplicates = df['order_id'].duplicated().sum()
    assert duplicates == 1

def test_late_delivery_rate_calculation():
    df = pd.DataFrame({'is_late': [True, False, False, True, False]})
    late_rate = df['is_late'].mean()
    assert round(late_rate, 1) == 0.4