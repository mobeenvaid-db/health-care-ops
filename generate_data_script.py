"""Care Ops - Data Generator Script (runs as serverless spark_python_task)."""

import sys
import psycopg2
import random
import datetime
from databricks.sdk import WorkspaceClient

DB_HOST = sys.argv[1] if len(sys.argv) > 1 else ""
if not DB_HOST:
    raise ValueError("Usage: generate_data_script.py <lakebase_host>")

DB_NAME = "care_ops_db"

import subprocess, json as _json

w = WorkspaceClient()
user = w.current_user.me().user_name

# Try multiple auth methods for Lakebase
token = None

# Method 1: Generate Lakebase credential via API
try:
    endpoint_path = f"projects/home-hospice-care-ops/branches/production/endpoints/primary"
    resp = w.api_client.do("POST", f"/api/2.0/postgres/{endpoint_path}:generateDatabaseCredential")
    token = resp.get("token", "")
    if token:
        print("Auth: Lakebase credential API")
except Exception as e:
    print(f"Lakebase credential API failed: {e}")

# Method 2: OAuth token from workspace client
if not token:
    auth = w.config.authenticate()
    if auth and "Authorization" in auth:
        token = auth["Authorization"].replace("Bearer ", "")
        print("Auth: OAuth token")

if not token:
    raise RuntimeError("Could not obtain auth token for Lakebase")

conn = psycopg2.connect(host=DB_HOST, port=5432, database=DB_NAME,
                        user=user, password=token, sslmode="require")
conn.autocommit = True
cur = conn.cursor()
print(f"Connected to {DB_HOST}/{DB_NAME}")

REGIONS = ["Southeast", "Texas", "Northeast", "Midwest", "Mid-Atlantic", "Mountain West", "Pacific", "Gulf States"]
SERVICE_TYPES = ["Home Health", "Hospice", "Personal Care"]
DIAGNOSES = {
    "Home Health": ["Hip Replacement Recovery", "COPD Management", "Diabetes Wound Care",
                    "Stroke Rehabilitation", "Cardiac Rehabilitation", "Pneumonia Recovery",
                    "Post-surgical Care", "Knee Replacement", "Osteoarthritis", "CHF Management"],
    "Hospice": ["End-stage COPD", "Advanced Cancer", "End-stage Heart Failure",
                "Advanced Dementia", "Terminal Cancer", "End-stage Renal Disease"],
    "Personal Care": ["Elderly Assistance", "Disability Support", "Post-stroke Care",
                      "Chronic Disease Support", "Alzheimer's Care"],
}
PAYERS = ["Medicare", "Medicaid", "Commercial", "Managed Care", "Private Pay"]
FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "Michael", "Linda", "William",
               "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson"]
VISIT_TYPES = ["Skilled Nursing", "Physical Therapy", "Occupational Therapy",
               "Speech Therapy", "Home Health Aide", "Social Work", "Assessment", "Follow-up"]
VISIT_STATUSES = ["Completed", "Completed", "Completed", "Scheduled", "Pending"]
INCIDENT_TYPES = ["Fall - No Injury", "Medication Error", "Documentation Gap",
                  "Equipment Malfunction", "Privacy Concern", "Infection Control Issue"]
SEVERITIES = ["Low", "Low", "Low", "Medium", "Medium", "High"]

today = datetime.date.today()

# 1. Add 1-3 new episodes
num_new = random.randint(1, 3)
for _ in range(num_new):
    svc = random.choice(SERVICE_TYPES)
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    region = random.choice(REGIONS)
    diag = random.choice(DIAGNOSES[svc])
    payer = random.choice(PAYERS)
    end_date = today + datetime.timedelta(days=random.randint(30, 180)) if svc != "Hospice" else None
    cur.execute("INSERT INTO episodes (patient_name, service_type, status, region, start_date, projected_end_date, primary_diagnosis, payer) VALUES (%s,%s,'Active',%s,%s,%s,%s,%s)",
                (name, svc, region, today, end_date, diag, payer))
print(f"Added {num_new} episodes")

# 2. Complete 0-2 episodes
n = random.randint(0, 2)
if n > 0:
    cur.execute("UPDATE episodes SET status='Completed', updated_at=NOW() WHERE episode_id IN (SELECT episode_id FROM episodes WHERE status='Active' AND service_type!='Hospice' ORDER BY RANDOM() LIMIT %s)", (n,))
    print(f"Completed {n} episodes")

# 3. Generate visits
cur.execute("SELECT episode_id, region FROM episodes WHERE status='Active' ORDER BY RANDOM() LIMIT 10")
eps = cur.fetchall()
cur.execute("SELECT provider_id, region FROM providers WHERE status='Active'")
provs = cur.fetchall()
pr = {}
for pid, r in provs:
    pr.setdefault(r, []).append(pid)

nv = random.randint(3, 8)
for _ in range(nv):
    if not eps: break
    eid, reg = random.choice(eps)
    pid = random.choice(pr.get(reg, [provs[0][0]])) if pr.get(reg) else random.choice(provs)[0]
    st = random.choice(VISIT_STATUSES)
    dur = random.randint(25, 65) if st == "Completed" else None
    rat = round(random.uniform(4.2, 5.0), 1) if st == "Completed" else None
    cur.execute("INSERT INTO visits (episode_id, provider_id, region, visit_date, visit_status, visit_type, duration_minutes, patient_rating) VALUES (%s,%s,%s,CURRENT_DATE,%s,%s,%s,%s)",
                (eid, pid, reg, st, random.choice(VISIT_TYPES), dur, rat))
print(f"Added {nv} visits")

# 4. Update metrics
cur.execute("UPDATE providers SET utilization_pct=LEAST(99,GREATEST(60,utilization_pct+(RANDOM()*4-2)::numeric(5,2))) WHERE status='Active'")
cur.execute("UPDATE weekly_revenue SET revenue_amount=GREATEST(1.5,revenue_amount+(RANDOM()*0.4-0.2)::numeric(10,2)) WHERE week_number=(SELECT MAX(week_number) FROM weekly_revenue)")
cur.execute("UPDATE satisfaction_trend SET score=LEAST(5.0,GREATEST(4.0,score+(RANDOM()*0.1-0.05)::numeric(3,1))), responses=responses+FLOOR(RANDOM()*20-5)::int WHERE month_number=(SELECT MAX(month_number) FROM satisfaction_trend)")
cur.execute("UPDATE compliance_scores SET score=LEAST(100,GREATEST(85,score+(RANDOM()*2-1)::numeric(5,1)))")
cur.execute("UPDATE performance_metrics SET score=LEAST(100,GREATEST(80,score+(RANDOM()*2-1)::numeric(5,1)))")
print("Updated metrics")

# 5. Quality incidents
if random.random() < 0.20:
    it = random.choice(INCIDENT_TYPES)
    sv = random.choice(SEVERITIES)
    cur.execute("INSERT INTO quality_incidents (incident_type,severity,status,incident_date,description) VALUES (%s,%s,'Under Review',CURRENT_DATE,%s)",
                (it, sv, f"Auto-generated: {it}"))
    print(f"New incident: {it} ({sv})")
if random.random() < 0.30:
    cur.execute("UPDATE quality_incidents SET status='Resolved' WHERE incident_id IN (SELECT incident_id FROM quality_incidents WHERE status='Under Review' ORDER BY incident_date ASC LIMIT 1)")
    print("Resolved an incident")

# Summary
cur.execute("SELECT (SELECT COUNT(*) FROM episodes WHERE status='Active'), (SELECT COUNT(*) FROM visits WHERE visit_date=CURRENT_DATE), (SELECT COUNT(*) FROM providers WHERE status='Active'), (SELECT COUNT(*) FROM quality_incidents WHERE status!='Resolved')")
r = cur.fetchone()
print(f"\n=== Done === Episodes: {r[0]} | Visits today: {r[1]} | Providers: {r[2]} | Open incidents: {r[3]}")

cur.close()
conn.close()
