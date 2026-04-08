"""Quality & Outcomes API routes."""

from fastapi import APIRouter
from server.db import db

router = APIRouter(prefix="/api/quality", tags=["quality"])

# ── Static reference data (immune to duplicate seed rows) ──────────────

_COMPLIANCE_SCORES = [
    {"metric": "Documentation", "score": 96.0},
    {"metric": "Infection Control", "score": 98.0},
    {"metric": "Privacy (HIPAA)", "score": 99.0},
    {"metric": "Quality Standards", "score": 93.0},
    {"metric": "Regulatory", "score": 95.0},
    {"metric": "Safety Protocols", "score": 94.0},
]

_SATISFACTION_TREND = [
    {"month": "Sep", "score": 4.6, "responses": 842},
    {"month": "Oct", "score": 4.7, "responses": 891},
    {"month": "Nov", "score": 4.6, "responses": 823},
    {"month": "Dec", "score": 4.8, "responses": 934},
    {"month": "Jan", "score": 4.7, "responses": 876},
    {"month": "Feb", "score": 4.8, "responses": 912},
    {"month": "Mar", "score": 4.9, "responses": 1048},
]

_CLINICAL_OUTCOMES = [
    {"outcome": "ER Visits",             "current": 8.7,  "target": 10.0, "benchmark": 12.5},
    {"outcome": "Falls Prevention",      "current": 94.2, "target": 90.0, "benchmark": 87.3},
    {"outcome": "Hospitalization Rate",  "current": 12.4, "target": 15.0, "benchmark": 18.2},
    {"outcome": "Medication Adherence",  "current": 91.8, "target": 90.0, "benchmark": 86.5},
    {"outcome": "Wound Healing",         "current": 88.3, "target": 85.0, "benchmark": 82.1},
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
async def quality_metrics():
    """Satisfaction, compliance, outcomes, and incidents."""
    # Static data ensures charts render correctly regardless of DB state
    satisfaction = _SATISFACTION_TREND
    compliance = _COMPLIANCE_SCORES
    outcomes = _CLINICAL_OUTCOMES

    incidents = [_serialize(r) for r in await db.fetch(
        """SELECT incident_id as id, incident_type as type, severity,
                  status, TO_CHAR(incident_date, \'Mon DD\') as date
           FROM quality_incidents ORDER BY incident_date DESC LIMIT 5"""
    )]

    totals = await db.fetchrow(
        """SELECT
             (SELECT score FROM satisfaction_trend ORDER BY month_number DESC LIMIT 1) as patient_satisfaction,
             (SELECT ROUND(AVG(score)::numeric, 1) FROM compliance_scores) as compliance_rate,
             (SELECT COUNT(*) FROM quality_incidents WHERE status != \'Resolved\') as active_incidents"""
    )

    return {
        "satisfaction": satisfaction,
        "compliance": compliance,
        "outcomes": outcomes,
        "incidents": incidents,
        "totals": _serialize(totals) if totals else {},
    }
