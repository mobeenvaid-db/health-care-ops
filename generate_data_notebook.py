# Databricks notebook source
# MAGIC %md
# MAGIC # Care Ops - Real-Time Data Simulator
# MAGIC
# MAGIC This notebook continuously generates realistic healthcare operations data
# MAGIC into the Lakebase database. The Care Ops dashboard auto-refreshes
# MAGIC every 15 seconds, so changes appear in near real-time.
# MAGIC
# MAGIC **How to use:** Run All cells. The final cell loops indefinitely, generating
# MAGIC new episodes, visits, provider metric shifts, revenue fluctuations, and
# MAGIC quality incidents every 30 seconds. Stop the cell to pause generation.

# COMMAND ----------

# MAGIC %pip install psycopg2-binary
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import requests, json

# Lakebase connection details
PROJECT = "home-hospice-care-ops"
BRANCH = "production"
ENDPOINT = "primary"
DB_NAME = "care_ops_db"

# Get a proper Lakebase credential via the postgres API
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
workspace_url = ctx.apiUrl().get()
api_token = ctx.apiToken().get()

endpoint_path = f"projects/{PROJECT}/branches/{BRANCH}/endpoints/{ENDPOINT}"

# Get the endpoint host
resp = requests.get(
    f"{workspace_url}/api/2.0/postgres/{endpoint_path}",
    headers={"Authorization": f"Bearer {api_token}"}
)
resp.raise_for_status()
endpoint_info = resp.json()
DB_HOST = endpoint_info.get("status", {}).get("hosts", {}).get("host", "")
if not DB_HOST:
    print(f"WARNING: Could not extract host. Full response:\n{json.dumps(endpoint_info, indent=2)}")
else:
    print(f"Lakebase host: {DB_HOST}")

# Generate a database credential using the correct API endpoint
resp = requests.post(
    f"{workspace_url}/api/2.0/postgres/credentials",
    headers={"Authorization": f"Bearer {api_token}"},
    json={"endpoint": endpoint_path}
)
resp.raise_for_status()
cred = resp.json()
DB_TOKEN = cred.get("token", "")
# Username is your Databricks identity (email), not returned in the credential response
DB_USER = ctx.userName().get()

if not DB_TOKEN:
    print(f"ERROR: Credential generation returned empty token.")
    print(f"Full credential response:\n{json.dumps(cred, indent=2)}")
    raise ValueError("Failed to obtain valid Lakebase credentials.")

print(f"Authenticated as: {DB_USER}")
print(f"Token expires: {cred.get('expire_time', 'unknown')}")
print(f"Token length: {len(DB_TOKEN)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Connect to Lakebase

# COMMAND ----------

import psycopg2

conn = psycopg2.connect(
    host=DB_HOST, port=5432, database=DB_NAME,
    user=DB_USER, password=DB_TOKEN, sslmode="require"
)
conn.autocommit = True
cur = conn.cursor()

# Verify connection
cur.execute("SELECT COUNT(*) FROM episodes WHERE status = 'Active'")
count = cur.fetchone()[0]
print(f"Connected! Active episodes: {count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reference Data

# COMMAND ----------

import random
import datetime
import time

REGIONS = [
    "Southeast",      # FL, GA, AL, SC, NC, TN
    "Texas",          # TX
    "Northeast",      # MA, CT, NY, NJ, PA
    "Midwest",        # OH, IN, IL, MI, WI
    "Mid-Atlantic",   # VA, MD, DE, DC
    "Mountain West",  # CO, UT, AZ, NV, NM
    "Pacific",        # CA, OR, WA
    "Gulf States",    # LA, MS
]

SERVICE_TYPES = ["Home Health", "Hospice", "Personal Care"]

DIAGNOSES = {
    "Home Health": [
        "Hip Replacement Recovery", "COPD Management", "Diabetes Wound Care",
        "Stroke Rehabilitation", "Cardiac Rehabilitation", "Pneumonia Recovery",
        "Post-surgical Care", "Knee Replacement", "Osteoarthritis", "CHF Management",
        "Hypertension Management", "Fall Recovery", "Cellulitis Treatment",
    ],
    "Hospice": [
        "End-stage COPD", "Advanced Cancer", "End-stage Heart Failure",
        "Advanced Dementia", "Terminal Cancer", "End-stage Renal Disease",
        "ALS", "End-stage Liver Disease",
    ],
    "Personal Care": [
        "Elderly Assistance", "Disability Support", "Post-stroke Care",
        "Chronic Disease Support", "Alzheimer's Care", "Parkinson's Support",
    ],
}

PAYERS = ["Medicare", "Medicaid", "Commercial", "Managed Care", "Private Pay"]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "Michael", "Linda", "William",
    "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Daniel", "Nancy", "Mark", "Lisa",
    "Steven", "Betty", "Paul", "Dorothy", "Andrew", "Sandra", "Kenneth", "Ashley",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Lewis",
]

VISIT_TYPES = [
    "Skilled Nursing", "Physical Therapy", "Occupational Therapy",
    "Speech Therapy", "Home Health Aide", "Social Work", "Assessment",
    "Follow-up", "Wound Care", "IV Therapy", "Pain Management",
]

INCIDENT_TYPES = [
    "Fall - No Injury", "Medication Error", "Documentation Gap",
    "Equipment Malfunction", "Privacy Concern", "Infection Control Issue",
    "Communication Failure", "Scheduling Error", "Supply Shortage",
    "Patient Complaint", "Missed Visit",
]

SEVERITIES = ["Low", "Low", "Low", "Medium", "Medium", "High"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Simulation Functions

# COMMAND ----------

def add_episodes(cur, n=None):
    """Add new patient episodes across regions."""
    n = n or random.randint(1, 4)
    today = datetime.date.today()
    added = []
    for _ in range(n):
        svc = random.choices(SERVICE_TYPES, weights=[60, 25, 15])[0]  # weighted toward Home Health
        region = random.choices(REGIONS, weights=[22, 18, 12, 12, 10, 8, 8, 10])[0]  # weighted by regional presence
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        diag = random.choice(DIAGNOSES[svc])
        payer = random.choices(PAYERS, weights=[55, 15, 15, 10, 5])[0]  # Medicare dominant
        end_date = today + datetime.timedelta(days=random.randint(30, 180)) if svc != "Hospice" else None
        cur.execute(
            "INSERT INTO episodes (patient_name, service_type, status, region, start_date, projected_end_date, primary_diagnosis, payer) VALUES (%s,%s,'Active',%s,%s,%s,%s,%s)",
            (name, svc, region, today, end_date, diag, payer)
        )
        added.append(f"{name} ({svc}, {region})")
    return added


def complete_episodes(cur, n=None):
    """Discharge/complete some active episodes."""
    n = n or random.randint(0, 3)
    if n == 0:
        return 0
    cur.execute(
        "UPDATE episodes SET status='Completed', updated_at=NOW() WHERE episode_id IN (SELECT episode_id FROM episodes WHERE status='Active' AND service_type!='Hospice' ORDER BY RANDOM() LIMIT %s)", (n,)
    )
    return n


def generate_visits(cur, n=None):
    """Generate new visits across all regions."""
    n = n or random.randint(5, 15)
    cur.execute("SELECT episode_id, region FROM episodes WHERE status='Active' ORDER BY RANDOM() LIMIT 20")
    eps = cur.fetchall()
    if not eps:
        return 0

    cur.execute("SELECT provider_id, region FROM providers WHERE status='Active'")
    provs = cur.fetchall()
    pr = {}
    for pid, r in provs:
        pr.setdefault(r, []).append(pid)

    count = 0
    for _ in range(n):
        eid, reg = random.choice(eps)
        pid = random.choice(pr.get(reg, [provs[0][0]])) if pr.get(reg) else random.choice(provs)[0]
        status = random.choices(["Completed", "Scheduled", "Pending"], weights=[65, 20, 15])[0]
        vtype = random.choice(VISIT_TYPES)
        dur = random.randint(25, 65) if status == "Completed" else None
        rat = round(random.uniform(4.2, 5.0), 1) if status == "Completed" else None
        cur.execute(
            "INSERT INTO visits (episode_id, provider_id, region, visit_date, visit_status, visit_type, duration_minutes, patient_rating) VALUES (%s,%s,%s,CURRENT_DATE,%s,%s,%s,%s)",
            (eid, pid, reg, status, vtype, dur, rat)
        )
        count += 1
    return count


def update_metrics(cur):
    """Drift provider utilization, revenue, satisfaction, compliance."""
    cur.execute("UPDATE providers SET utilization_pct=LEAST(99,GREATEST(60, utilization_pct + (RANDOM()*4-2)::numeric(5,2))) WHERE status='Active'")
    cur.execute("UPDATE weekly_revenue SET revenue_amount=GREATEST(1.5, revenue_amount + (RANDOM()*0.4-0.2)::numeric(10,2)) WHERE week_number=(SELECT MAX(week_number) FROM weekly_revenue)")
    cur.execute("UPDATE satisfaction_trend SET score=LEAST(5.0,GREATEST(4.0, score + (RANDOM()*0.1-0.05)::numeric(3,1))), responses=responses + FLOOR(RANDOM()*20-5)::int WHERE month_number=(SELECT MAX(month_number) FROM satisfaction_trend)")
    cur.execute("UPDATE compliance_scores SET score=LEAST(100,GREATEST(85, score + (RANDOM()*2-1)::numeric(5,1)))")
    cur.execute("UPDATE performance_metrics SET score=LEAST(100,GREATEST(80, score + (RANDOM()*2-1)::numeric(5,1)))")


def handle_incidents(cur):
    """Occasionally create new incidents or resolve old ones."""
    created = None
    if random.random() < 0.25:
        it = random.choice(INCIDENT_TYPES)
        sv = random.choice(SEVERITIES)
        cur.execute(
            "INSERT INTO quality_incidents (incident_type, severity, status, incident_date, description) VALUES (%s,%s,'Under Review',CURRENT_DATE,%s)",
            (it, sv, f"{it} detected during routine monitoring")
        )
        created = f"{it} ({sv})"

    resolved = False
    if random.random() < 0.35:
        cur.execute("UPDATE quality_incidents SET status='Resolved' WHERE incident_id IN (SELECT incident_id FROM quality_incidents WHERE status='Under Review' ORDER BY incident_date ASC LIMIT 1)")
        resolved = cur.rowcount > 0

    return created, resolved


def get_summary(cur):
    """Get current state summary."""
    cur.execute("""
        SELECT
            (SELECT COUNT(*) FROM episodes WHERE status = 'Active'),
            (SELECT COUNT(*) FROM visits WHERE visit_date = CURRENT_DATE),
            (SELECT COUNT(*) FROM providers WHERE status = 'Active'),
            (SELECT COUNT(*) FROM quality_incidents WHERE status != 'Resolved'),
            (SELECT SUM(revenue_amount) FROM weekly_revenue),
            (SELECT score FROM satisfaction_trend ORDER BY month_number DESC LIMIT 1)
    """)
    return cur.fetchone()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Continuous Simulation
# MAGIC
# MAGIC This cell runs in an infinite loop, generating data every **30 seconds**.
# MAGIC The dashboard auto-refreshes every 15 seconds, so you'll see changes appear
# MAGIC in near real-time. **Cancel this cell to stop generation.**

# COMMAND ----------

import sys

cycle = 0
print("=" * 70)
print("  Care Ops - Micro-Change Simulator Started")
print("  Generating small data changes every 2 seconds.")
print("  Cancel cell to stop.")
print("=" * 70)

# Print initial state so user can see baseline
stats = get_summary(cur)
ep_count, visit_count, prov_count, incident_count, revenue, satisfaction = stats
print(f"  Baseline | Episodes: {ep_count} | Visits today: {visit_count} | Revenue: ${revenue:.1f}M | Satisfaction: {satisfaction}/5.0 | Open incidents: {incident_count}")
print()

while True:
    cycle += 1
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    actions = []  # track what happened this cycle

    try:
        # Refresh connection token every 750 cycles (~25 min at 2s)
        if cycle % 750 == 0:
            cur.close()
            conn.close()
            resp = requests.post(
                f"{workspace_url}/api/2.0/postgres/credentials",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"endpoint": endpoint_path}
            )
            cred = resp.json()
            DB_TOKEN = cred.get("token", "")
            DB_USER = ctx.userName().get()
            conn = psycopg2.connect(
                host=DB_HOST, port=5432, database=DB_NAME,
                user=DB_USER, password=DB_TOKEN, sslmode="require"
            )
            conn.autocommit = True
            cur = conn.cursor()
            actions.append("token-refresh")

        # --- Micro-changes each cycle ---

        # 15% chance: add 1 episode
        if random.random() < 0.15:
            svc = random.choices(SERVICE_TYPES, weights=[60, 25, 15])[0]
            region = random.choices(REGIONS, weights=[22, 18, 12, 12, 10, 8, 8, 10])[0]
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            diag = random.choice(DIAGNOSES[svc])
            payer = random.choices(PAYERS, weights=[55, 15, 15, 10, 5])[0]
            today = datetime.date.today()
            end_date = today + datetime.timedelta(days=random.randint(30, 180)) if svc != "Hospice" else None
            cur.execute(
                "INSERT INTO episodes (patient_name, service_type, status, region, start_date, projected_end_date, primary_diagnosis, payer) VALUES (%s,%s,'Active',%s,%s,%s,%s,%s)",
                (name, svc, region, today, end_date, diag, payer)
            )
            actions.append("+episode")

        # 5% chance: complete 1 episode
        if random.random() < 0.05:
            cur.execute(
                "UPDATE episodes SET status='Completed', updated_at=NOW() WHERE episode_id IN (SELECT episode_id FROM episodes WHERE status='Active' AND service_type!='Hospice' ORDER BY RANDOM() LIMIT 1)"
            )
            actions.append("-episode")

        # 40% chance: add 1-2 visits
        if random.random() < 0.40:
            cur.execute("SELECT episode_id, region FROM episodes WHERE status='Active' ORDER BY RANDOM() LIMIT 5")
            eps = cur.fetchall()
            if eps:
                cur.execute("SELECT provider_id, region FROM providers WHERE status='Active'")
                provs = cur.fetchall()
                pr = {}
                for pid, r in provs:
                    pr.setdefault(r, []).append(pid)

                n_visits = random.randint(1, 2)
                for _ in range(n_visits):
                    eid, reg = random.choice(eps)
                    pid = random.choice(pr.get(reg, [provs[0][0]])) if pr.get(reg) else random.choice(provs)[0]
                    st = random.choices(["Completed", "Scheduled", "Pending"], weights=[65, 20, 15])[0]
                    dur = random.randint(25, 65) if st == "Completed" else None
                    rat = round(random.uniform(4.2, 5.0), 1) if st == "Completed" else None
                    cur.execute(
                        "INSERT INTO visits (episode_id, provider_id, region, visit_date, visit_status, visit_type, duration_minutes, patient_rating) VALUES (%s,%s,%s,CURRENT_DATE,%s,%s,%s,%s)",
                        (eid, pid, reg, st, random.choice(VISIT_TYPES), dur, rat)
                    )
                actions.append(f"+{n_visits}visits")

        # 20% chance: tiny metric drift
        if random.random() < 0.20:
            cur.execute("UPDATE providers SET utilization_pct=LEAST(99,GREATEST(60, utilization_pct + (RANDOM()*1.0-0.5)::numeric(5,2))) WHERE provider_id = (SELECT provider_id FROM providers WHERE status='Active' ORDER BY RANDOM() LIMIT 1)")
            cur.execute("UPDATE weekly_revenue SET revenue_amount=GREATEST(1.5, revenue_amount + (RANDOM()*0.08-0.04)::numeric(10,2)) WHERE week_number=(SELECT MAX(week_number) FROM weekly_revenue)")
            actions.append("metrics")

        # 10% chance: nudge satisfaction/compliance
        if random.random() < 0.10:
            cur.execute("UPDATE satisfaction_trend SET score=LEAST(5.0,GREATEST(4.0, score + (RANDOM()*0.04-0.02)::numeric(3,1))), responses=responses + FLOOR(RANDOM()*5)::int WHERE month_number=(SELECT MAX(month_number) FROM satisfaction_trend)")
            cur.execute("UPDATE compliance_scores SET score=LEAST(100,GREATEST(85, score + (RANDOM()*0.6-0.3)::numeric(5,1))) WHERE compliance_id = (SELECT compliance_id FROM compliance_scores ORDER BY RANDOM() LIMIT 1)")
            cur.execute("UPDATE performance_metrics SET score=LEAST(100,GREATEST(80, score + (RANDOM()*0.6-0.3)::numeric(5,1))) WHERE metric_id = (SELECT metric_id FROM performance_metrics ORDER BY RANDOM() LIMIT 1)")
            actions.append("compliance")

        # 3% chance: new incident
        if random.random() < 0.03:
            it = random.choice(INCIDENT_TYPES)
            sv = random.choice(SEVERITIES)
            cur.execute(
                "INSERT INTO quality_incidents (incident_type, severity, status, incident_date, description) VALUES (%s,%s,'Under Review',CURRENT_DATE,%s)",
                (it, sv, f"{it} detected during routine monitoring")
            )
            actions.append(f"+incident({sv})")

        # 5% chance: resolve incident
        if random.random() < 0.05:
            cur.execute("UPDATE quality_incidents SET status='Resolved' WHERE incident_id IN (SELECT incident_id FROM quality_incidents WHERE status='Under Review' ORDER BY incident_date ASC LIMIT 1)")
            actions.append("-incident")

        # Print compact activity indicator every cycle
        action_str = ", ".join(actions) if actions else "idle"
        print(f"  [{ts}] #{cycle:>4d}  {action_str}")

        # Print full summary every 15 cycles (~30 sec)
        if cycle % 15 == 0:
            stats = get_summary(cur)
            ep_count, visit_count, prov_count, incident_count, revenue, satisfaction = stats
            print(f"  ---- Summary | Episodes: {ep_count} | Visits today: {visit_count} | Revenue: ${revenue:.1f}M | Satisfaction: {satisfaction}/5.0 | Incidents: {incident_count} ----")

    except Exception as e:
        print(f"  [{ts}] Error: {e}")

    time.sleep(2)