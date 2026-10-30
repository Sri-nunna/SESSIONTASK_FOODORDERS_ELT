-- Run these queries in food_orders_analytics_db after the ELT pipeline.

-- 1. Total order value (only records with a known Order Value are included).
SELECT SUM(`Order Value`) AS total_order_value
FROM cleaned_food_orders
WHERE `Order Value` IS NOT NULL;

-- 2. Average order value.
SELECT AVG(`Order Value`) AS average_order_value
FROM cleaned_food_orders
WHERE `Order Value` IS NOT NULL;

-- 3. Payment method with the highest number of orders.
SELECT `Payment Method`, COUNT(*) AS order_count
FROM cleaned_food_orders
WHERE `Payment Method` IS NOT NULL
  AND `Payment Method` <> 'Unknown'
GROUP BY `Payment Method`
ORDER BY order_count DESC
LIMIT 1;

-- 4. Order channel with the highest number of orders.
SELECT `Order Channel`, COUNT(*) AS order_count
FROM cleaned_food_orders
GROUP BY `Order Channel`
ORDER BY order_count DESC
LIMIT 1;

-- 5. Average delivery time (valid, non-negative durations only).
SELECT AVG(Delivery_Time_Minutes) AS average_delivery_time_minutes
FROM cleaned_food_orders
WHERE Delivery_Time_Minutes IS NOT NULL
  AND Delivery_Time_Minutes >= 0;

-- 6. Total platform net revenue. NULL means one or more formula inputs were missing.
SELECT SUM(Platform_Net_Revenue) AS total_platform_net_revenue,
       COUNT(Platform_Net_Revenue) AS records_included
FROM cleaned_food_orders
WHERE Platform_Net_Revenue IS NOT NULL;
