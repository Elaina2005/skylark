from src.monday_client import refresh_cache
from src.tools import (
    execute_compute_metric,
    execute_get_deals,
    execute_get_work_orders,
    execute_cross_reference_boards,
    execute_get_data_quality_report
)
from src.insights import generate_leadership_update

print("Refreshing Cache...")
cache = refresh_cache(force=True)
print("Cache status:", cache.get("status_message"))

print("\n1. Test Total Pipeline Value:")
res1 = execute_compute_metric(metric="total_value", board="deals", filters={"status": "Open"})
print(res1)

print("\n2. Test Win Rate on Deals:")
res2 = execute_compute_metric(metric="win_rate", board="deals")
print(res2)

print("\n3. Test Overdue Work Orders:")
res3 = execute_get_work_orders(filters={"is_overdue": True})
print(f"Overdue records matched: {res3.get('matched_records')}")

print("\n4. Test Cross Reference (Sector Comparison):")
res4 = execute_cross_reference_boards(join_key="sector", analysis_type="sector_comparison")
print("Top comparison rows:", res4.get("comparison_table", [])[:4])

print("\n5. Test Cross Reference (Won Deals without Work Orders):")
res5 = execute_cross_reference_boards(join_key="deal_name", analysis_type="won_deals_without_work_orders")
print(f"Won deals without WO: {res5.get('won_deals_without_work_orders_count')}")

print("\n6. Test Data Quality Report:")
res6 = execute_get_data_quality_report(board="both")
print("Work Orders Summary:", res6.get("work_orders", {}).get("summary"))
print("Deals Summary:", res6.get("deals", {}).get("summary"))

print("\n7. Test Leadership Update Generator:")
res7 = generate_leadership_update("last_30_days")
print("Leadership update length:", len(res7))
print("\nFirst 400 chars of Leadership Update:\n", res7[:400])

print("\nALL TOOL & INSIGHT TESTS COMPLETED SUCCESSFULLY!")
