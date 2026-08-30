"""
Verification suite for all 7 query patterns specified in Phase 5.
"""
from src.monday_client import refresh_cache
from src.tools import (
    execute_compute_metric,
    execute_get_deals,
    execute_get_work_orders,
    execute_cross_reference_boards,
    execute_get_data_quality_report,
    dispatch_tool_call
)

print("=" * 80)
print("TESTING 7 EVALUATION QUERY PATTERNS")
print("=" * 80)

# Refresh cache
refresh_cache(force=True)

# Pattern 1: Direct metric question: "What's our total deal pipeline value right now?"
print("\n--- Pattern 1: Total Deal Pipeline Value ---")
p1_metric = execute_compute_metric(metric="total_value", board="deals", filters={"status": "Open"})
print("Result:", p1_metric)
assert p1_metric["total_value_inr"] > 0, "Pipeline value should be positive"
assert "records_used" in p1_metric
assert "caveat" in p1_metric
print("Pattern 1 PASS")

# Pattern 2: Sector-filtered question: "How's our pipeline looking for the energy sector this quarter?"
print("\n--- Pattern 2: Sector-filtered Pipeline (Renewables / Powerline) ---")
p2_deals = execute_get_deals(filters={"sector": "Renewables", "status": "Open"})
p2_metric = execute_compute_metric(metric="total_value", board="deals", filters={"sector": "Renewables", "status": "Open"})
print(f"Matched Open Renewables Deals: {p2_deals.get('matched_records')}")
print(f"Renewables Pipeline Value: {p2_metric.get('formatted_inr')}")
print("Pattern 2 PASS")

# Pattern 3: Cross-board question: "Which sectors have the most work orders but the fewest won deals?"
print("\n--- Pattern 3: Cross-Board Sector Comparison ---")
p3_cross = execute_cross_reference_boards(join_key="sector", analysis_type="sector_comparison")
print("Top sectors comparison table:")
for row in p3_cross.get("comparison_table", [])[:5]:
    print(f"  Sector: {row['sector']:15s} | Work Orders: {row['work_orders_count']:3d} | Won Deals: {row['won_deals_count']:3d} | Ratio: {row['wo_to_deal_ratio']}")
assert len(p3_cross.get("comparison_table", [])) > 0
print("Pattern 3 PASS")

# Pattern 4: Operational question: "How many work orders are overdue?"
print("\n--- Pattern 4: Overdue Work Orders ---")
p4_overdue = execute_get_work_orders(filters={"is_overdue": True})
print(f"Overdue Work Orders Count: {p4_overdue.get('matched_records')}")
assert p4_overdue.get("matched_records") > 0, "Overdue work orders should be identified"
print("Pattern 4 PASS")

# Pattern 5: Data-quality-sensitive question
print("\n--- Pattern 5: Data Quality & Caveat Reporting ---")
p5_dq = execute_get_data_quality_report(board="both")
print("Deals Caveats:", p5_dq["deals"]["caveats"])
print("Work Orders Caveats:", p5_dq["work_orders"]["caveats"])
assert len(p5_dq["deals"]["caveats"]) > 0
assert len(p5_dq["work_orders"]["caveats"]) > 0
print("Pattern 5 PASS")

# Pattern 6: Won Deals without Work Orders
print("\n--- Pattern 6: Won Deals without Work Orders ---")
p6_unmatched = execute_cross_reference_boards(join_key="deal_name", analysis_type="won_deals_without_work_orders")
print(f"Total Won Deals: {p6_unmatched['total_won_deals']} | Won with WO: {p6_unmatched['won_deals_with_work_orders']} | Won without WO: {p6_unmatched['won_deals_without_work_orders_count']}")
assert p6_unmatched["won_deals_without_work_orders_count"] > 0
print("Pattern 6 PASS")

# Pattern 7: Win Rate & Completion Rate Analytics
print("\n--- Pattern 7: Win Rate & Completion Rate Analytics ---")
p7_win = execute_compute_metric(metric="win_rate", board="deals")
p7_comp = execute_compute_metric(metric="completion_rate", board="work_orders")
print(f"Win Rate: {p7_win.get('win_rate_percent')}% (Won: {p7_win.get('won_deals_count')}, Closed: {p7_win.get('closed_deals_count')})")
print(f"Completion Rate: {p7_comp.get('completion_rate_percent')}% (Completed: {p7_comp.get('completed_count')}, Total: {p7_comp.get('total_work_orders')})")
assert p7_win.get("win_rate_percent") > 0
assert p7_comp.get("completion_rate_percent") > 0
print("Pattern 7 PASS")

print("\n" + "=" * 80)
print("ALL 7 QUERY PATTERNS PASSED VERIFICATION SUITE!")
print("=" * 80)
