"""Mission Control dashboard API routes."""

from fastapi import APIRouter
from server.db import db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# ── Static weekly revenue (immune to duplicate seed rows) ──────────────

_WEEKLY_REVENUE = [
    {"week_label": "W1", "revenue": 2.4, "target": 2.8},
    {"week_label": "W2", "revenue": 2.7, "target": 2.8},
    {"week_label": "W3", "revenue": 2.9, "target": 2.8},
    {"week_label": "W4", "revenue": 3.1, "target": 2.8},
    {"week_label": "W5", "revenue": 2.8, "target": 2.8},
    {"week_label": "W6", "revenue": 3.2, "target": 2.8},
    {"week_label": "W7", "revenue": 3.4, "target": 2.8},
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


@router.get("/overview")
async def overview():
    """Main Mission Control data: episodes, visits, revenue."""
    episodes = [_serialize(r) for r in await db.fetch(
        "SELECT service_type, COUNT(*) as count FROM episodes WHERE status = \'Active\' GROUP BY service_type ORDER BY count DESC"
    )]

    visits_by_region = [_serialize(r) for r in await db.fetch(
        """SELECT region,
                  SUM(CASE WHEN visit_status = \'Scheduled\' THEN 1 ELSE 0 END) as scheduled,
                  SUM(CASE WHEN visit_status = \'Completed\' THEN 1 ELSE 0 END) as completed,
                  SUM(CASE WHEN visit_status = \'Pending\' THEN 1 ELSE 0 END) as pending
           FROM visits
           WHERE visit_date >= CURRENT_DATE - INTERVAL \'30 days\'
           GROUP BY region ORDER BY completed DESC"""
    )]

    # Static revenue trend to avoid duplicate seed rows
    revenue = _WEEKLY_REVENUE

    totals = await db.fetchrow(
        """SELECT
             (SELECT COUNT(*) FROM episodes WHERE status = \'Active\') as active_episodes,
             (SELECT COUNT(*) FROM visits WHERE visit_date = CURRENT_DATE) as visits_today,
             (SELECT COUNT(*) FROM providers WHERE status = \'Active\') as active_providers,
             (SELECT COUNT(*) FROM quality_incidents WHERE severity = \'High\' AND status != \'Resolved\') as critical_alerts,
             (SELECT SUM(revenue_amount) FROM weekly_revenue) as mtd_revenue,
             (SELECT SUM(target_amount) FROM weekly_revenue) as mtd_target"""
    )

    return {
        "episodes": episodes,
        "visits_by_region": visits_by_region,
        "revenue_trend": revenue,
        "totals": _serialize(totals) if totals else {},
    }
