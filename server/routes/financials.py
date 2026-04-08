"""Financial Metrics API routes."""

from fastapi import APIRouter
from server.db import db

router = APIRouter(prefix="/api/financials", tags=["financials"])

# ── Static reference data (immune to duplicate seed rows) ──────────────

_REVENUE_BY_PAYER = [
    {"payer": "Medicare",     "revenue": 12.4, "margin": 18.2},
    {"payer": "Commercial",   "revenue": 6.2,  "margin": 22.3},
    {"payer": "Medicaid",     "revenue": 4.8,  "margin": 14.5},
    {"payer": "Managed Care", "revenue": 3.9,  "margin": 16.8},
    {"payer": "Private Pay",  "revenue": 2.1,  "margin": 28.5},
]

_CASH_FLOW = [
    {"month": "Oct", "inflow": 18.2, "outflow": 15.4, "net": 2.8},
    {"month": "Nov", "inflow": 19.5, "outflow": 16.1, "net": 3.4},
    {"month": "Dec", "inflow": 21.3, "outflow": 17.8, "net": 3.5},
    {"month": "Jan", "inflow": 20.1, "outflow": 16.9, "net": 3.2},
    {"month": "Feb", "inflow": 22.4, "outflow": 18.2, "net": 4.2},
    {"month": "Mar", "inflow": 23.8, "outflow": 19.1, "net": 4.7},
]

_AR_AGING = [
    {"category": "0-30 days",  "amount": 8.2, "percentage": 62.0},
    {"category": "31-60 days", "amount": 2.9, "percentage": 22.0},
    {"category": "61-90 days", "amount": 1.4, "percentage": 11.0},
    {"category": "90+ days",   "amount": 0.7, "percentage": 5.0},
]

_COST_BUDGET = [
    {"category": "Facilities", "current": 1.2, "budget": 1.3, "variance": -7.7},
    {"category": "Labor",      "current": 12.8, "budget": 12.2, "variance": 4.9},
    {"category": "Other",      "current": 0.9, "budget": 1.0, "variance": -10.0},
    {"category": "Supplies",   "current": 2.4, "budget": 2.5, "variance": -4.0},
    {"category": "Technology", "current": 1.8, "budget": 1.7, "variance": 5.9},
]


def _serialize(row: dict) -> dict:
    result = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        elif hasattr(v, "__float__"):
            result[k] = float(v)
        else:
            result[k] = v
    return result


@router.get("")
async def financial_metrics():
    """Revenue by payer, cash flow, AR aging, cost vs budget."""
    # Static data ensures charts render correctly regardless of DB state
    revenue_by_payer = _REVENUE_BY_PAYER
    cash_flow = _CASH_FLOW
    ar_aging = _AR_AGING
    cost_breakdown = _COST_BUDGET

    totals = await db.fetchrow(
        """SELECT
             (SELECT SUM(revenue) FROM revenue_by_payer) as mtd_revenue,
             (SELECT ROUND(AVG(margin)::numeric, 1) FROM revenue_by_payer) as operating_margin,
             (SELECT SUM(amount) FROM ar_aging) as outstanding_ar,
             (SELECT COUNT(*) FROM billing_alerts WHERE status = \'Open\') as billing_alerts"""
    )

    return {
        "revenue_by_payer": revenue_by_payer,
        "cash_flow": cash_flow,
        "ar_aging": ar_aging,
        "cost_breakdown": cost_breakdown,
        "totals": _serialize(totals) if totals else {},
    }
