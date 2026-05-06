-- ============================================================
-- OLIST E-COMMERCE ANALYTICS
-- Business Analysis Queries
-- ============================================================


-- Q1: Monthly revenue and order volume trend
-- Business question: How has revenue and order volume evolved over time?
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
    COUNT(DISTINCT o.order_id)                       AS total_orders,
    ROUND(SUM(i.price + i.freight_value)::numeric, 2) AS total_revenue,
    ROUND(AVG(i.price)::numeric, 2)                  AS avg_item_price
FROM orders_clean o
JOIN order_items_clean i ON o.order_id = i.order_id
GROUP BY 1
ORDER BY 1;


-- Q2: Top 15 product categories by revenue
-- Business question: Which categories drive the most revenue?
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    COUNT(DISTINCT i.order_id)                       AS total_orders,
    ROUND(SUM(i.price)::numeric, 2)                  AS total_revenue,
    ROUND(AVG(i.price)::numeric, 2)                  AS avg_item_price,
    ROUND(AVG(r.review_score)::numeric, 2)           AS avg_review_score
FROM order_items_clean i
JOIN products_clean p      ON i.product_id = p.product_id
LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
LEFT JOIN order_reviews_clean r  ON i.order_id = r.order_id
GROUP BY 1
ORDER BY total_revenue DESC
LIMIT 15;


-- Q3: Delivery performance by customer state
-- Business question: Where are delivery delays most severe?
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id)                        AS total_orders,
    ROUND(AVG(o.delivery_days)::numeric, 1)           AS avg_delivery_days,
    ROUND(
        SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*), 1
    )                                                  AS late_delivery_pct,
    ROUND(AVG(r.review_score)::numeric, 2)            AS avg_review_score
FROM orders_clean o
JOIN customers c             ON o.customer_id = c.customer_id
LEFT JOIN order_reviews_clean r ON o.order_id = r.order_id
GROUP BY 1
ORDER BY late_delivery_pct DESC;


-- Q4: Top 20 seller performance ranking
-- Business question: Which sellers generate the most revenue and how do they rate on satisfaction?
SELECT
    i.seller_id,
    COUNT(DISTINCT i.order_id)              AS orders_fulfilled,
    ROUND(SUM(i.price)::numeric, 2)         AS total_revenue,
    ROUND(AVG(i.price)::numeric, 2)         AS avg_item_price,
    ROUND(AVG(r.review_score)::numeric, 2)  AS avg_review_score,
    ROUND(AVG(o.delivery_days)::numeric, 1) AS avg_delivery_days
FROM order_items_clean i
JOIN orders_clean o          ON i.order_id = o.order_id
LEFT JOIN order_reviews_clean r ON i.order_id = r.order_id
GROUP BY 1
HAVING COUNT(DISTINCT i.order_id) >= 10
ORDER BY total_revenue DESC
LIMIT 20;


-- Q5: Payment method analysis
-- Business question: How do customers prefer to pay and what is the installment behavior?
SELECT
    payment_type,
    COUNT(*)                                    AS total_transactions,
    ROUND(SUM(payment_value)::numeric, 2)       AS total_value,
    ROUND(AVG(payment_value)::numeric, 2)       AS avg_transaction_value,
    ROUND(AVG(payment_installments)::numeric, 1) AS avg_installments
FROM order_payments_clean
WHERE payment_type != 'not_defined'
GROUP BY 1
ORDER BY total_transactions DESC;


-- Q6: Customer repeat purchase rate
-- Business question: What share of customers come back for a second purchase?
SELECT
    COUNT(DISTINCT customer_unique_id)                                    AS total_unique_customers,
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS repeat_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END)
        * 100.0 / COUNT(DISTINCT customer_unique_id), 2
    )                                                                      AS repeat_rate_pct
FROM (
    SELECT
        c.customer_unique_id,
        COUNT(o.order_id) AS order_count
    FROM customers c
    JOIN orders_clean o ON c.customer_id = o.customer_id
    GROUP BY 1
) sub;


-- Q7: Order volume and revenue by day of week and hour
-- Business question: When do customers shop most — useful for marketing scheduling?
SELECT
    TO_CHAR(order_purchase_timestamp, 'Day') AS day_of_week,
    EXTRACT(DOW FROM order_purchase_timestamp)::int AS day_num,
    EXTRACT(HOUR FROM order_purchase_timestamp)::int AS hour_of_day,
    COUNT(DISTINCT o.order_id)               AS total_orders,
    ROUND(SUM(i.price)::numeric, 2)          AS total_revenue
FROM orders_clean o
JOIN order_items_clean i ON o.order_id = i.order_id
GROUP BY 1, 2, 3
ORDER BY 2, 3;


-- Q8: Review score vs delivery lateness
-- Business question: Does late delivery measurably hurt customer satisfaction?
SELECT
    o.is_late,
    COUNT(*)                                   AS total_orders,
    ROUND(AVG(r.review_score)::numeric, 2)     AS avg_review_score,
    ROUND(
        SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*), 1
    )                                           AS pct_low_scores
FROM orders_clean o
JOIN order_reviews_clean r ON o.order_id = r.order_id
GROUP BY 1
ORDER BY 1;