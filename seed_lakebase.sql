-- ============================================================
-- Care Ops - Lakebase Schema & Seed Data
-- ============================================================

-- Episodes (Home Health, Hospice, Personal Care)
CREATE TABLE IF NOT EXISTS episodes (
    episode_id SERIAL PRIMARY KEY,
    patient_name VARCHAR(200) NOT NULL,
    service_type VARCHAR(50) NOT NULL,  -- 'Home Health', 'Hospice', 'Personal Care'
    status VARCHAR(30) NOT NULL DEFAULT 'Active',
    region VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    projected_end_date DATE,
    primary_diagnosis VARCHAR(200),
    payer VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Providers
CREATE TABLE IF NOT EXISTS providers (
    provider_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    discipline VARCHAR(30) NOT NULL,  -- RN, LVN, PT, OT, ST, MSW, HHA
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    region VARCHAR(50) NOT NULL,
    utilization_pct DECIMAL(5,2) DEFAULT 0,
    avg_visit_minutes INT DEFAULT 45,
    hire_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Visits
CREATE TABLE IF NOT EXISTS visits (
    visit_id SERIAL PRIMARY KEY,
    episode_id INT REFERENCES episodes(episode_id),
    provider_id INT REFERENCES providers(provider_id),
    region VARCHAR(50) NOT NULL,
    visit_date DATE NOT NULL,
    visit_status VARCHAR(30) NOT NULL DEFAULT 'Scheduled',  -- Scheduled, Completed, Pending, Missed
    visit_type VARCHAR(50),
    duration_minutes INT,
    patient_rating DECIMAL(3,1),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Weekly Revenue
CREATE TABLE IF NOT EXISTS weekly_revenue (
    week_id SERIAL PRIMARY KEY,
    week_number INT NOT NULL,
    week_label VARCHAR(10) NOT NULL,
    revenue_amount DECIMAL(10,2) NOT NULL,
    target_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance Metrics (radar chart data)
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    score DECIMAL(5,1) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Revenue by Payer
CREATE TABLE IF NOT EXISTS revenue_by_payer (
    payer_id SERIAL PRIMARY KEY,
    payer_name VARCHAR(50) NOT NULL,
    revenue DECIMAL(10,2) NOT NULL,
    margin DECIMAL(5,1) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cash Flow
CREATE TABLE IF NOT EXISTS cash_flow (
    flow_id SERIAL PRIMARY KEY,
    month_number INT NOT NULL,
    month_label VARCHAR(10) NOT NULL,
    inflow DECIMAL(10,2) NOT NULL,
    outflow DECIMAL(10,2) NOT NULL,
    net DECIMAL(10,2) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- AR Aging
CREATE TABLE IF NOT EXISTS ar_aging (
    aging_id SERIAL PRIMARY KEY,
    bucket VARCHAR(30) NOT NULL,
    sort_order INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    percentage DECIMAL(5,1) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cost vs Budget
CREATE TABLE IF NOT EXISTS cost_budget (
    cost_id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    current_amount DECIMAL(10,2) NOT NULL,
    budget_amount DECIMAL(10,2) NOT NULL,
    variance DECIMAL(5,1) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Billing Alerts
CREATE TABLE IF NOT EXISTS billing_alerts (
    alert_id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Open',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Satisfaction Trend
CREATE TABLE IF NOT EXISTS satisfaction_trend (
    trend_id SERIAL PRIMARY KEY,
    month_number INT NOT NULL,
    month_label VARCHAR(10) NOT NULL,
    score DECIMAL(3,1) NOT NULL,
    responses INT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Compliance Scores
CREATE TABLE IF NOT EXISTS compliance_scores (
    compliance_id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    score DECIMAL(5,1) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Clinical Outcomes
CREATE TABLE IF NOT EXISTS clinical_outcomes (
    outcome_id SERIAL PRIMARY KEY,
    outcome_name VARCHAR(100) NOT NULL,
    current_value DECIMAL(5,1) NOT NULL,
    target_value DECIMAL(5,1) NOT NULL,
    benchmark_value DECIMAL(5,1) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Quality Incidents
CREATE TABLE IF NOT EXISTS quality_incidents (
    incident_id SERIAL PRIMARY KEY,
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- Low, Medium, High
    status VARCHAR(30) NOT NULL DEFAULT 'Under Review',
    incident_date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_episodes_service ON episodes(service_type);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status);
CREATE INDEX IF NOT EXISTS idx_episodes_region ON episodes(region);
CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_date);
CREATE INDEX IF NOT EXISTS idx_visits_region ON visits(region);
CREATE INDEX IF NOT EXISTS idx_visits_status ON visits(visit_status);
CREATE INDEX IF NOT EXISTS idx_providers_discipline ON providers(discipline);
CREATE INDEX IF NOT EXISTS idx_providers_status ON providers(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON quality_incidents(severity);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Seed Episodes (operates across 36 states in 8 regions)
INSERT INTO episodes (patient_name, service_type, status, region, start_date, projected_end_date, primary_diagnosis, payer) VALUES
-- Home Health episodes across regions
('James Wilson', 'Home Health', 'Active', 'Southeast', '2026-01-15', '2026-04-15', 'Hip Replacement Recovery', 'Medicare'),
('Mary Johnson', 'Home Health', 'Active', 'Texas', '2026-02-01', '2026-05-01', 'Congestive Heart Failure', 'Medicare'),
('Robert Davis', 'Home Health', 'Active', 'Northeast', '2026-01-20', '2026-04-20', 'COPD Management', 'Medicaid'),
('Patricia Brown', 'Home Health', 'Active', 'Mountain West', '2026-02-10', '2026-05-10', 'Diabetes Wound Care', 'Commercial'),
('Michael Miller', 'Home Health', 'Active', 'Midwest', '2026-01-25', '2026-04-25', 'Stroke Rehabilitation', 'Medicare'),
('Linda Garcia', 'Home Health', 'Active', 'Southeast', '2026-02-05', '2026-05-05', 'Knee Replacement', 'Managed Care'),
('William Martinez', 'Home Health', 'Active', 'Texas', '2026-01-30', '2026-04-30', 'Cardiac Rehabilitation', 'Medicare'),
('Barbara Anderson', 'Home Health', 'Active', 'Mid-Atlantic', '2026-02-15', '2026-05-15', 'Pneumonia Recovery', 'Medicare'),
('David Thomas', 'Home Health', 'Active', 'Pacific', '2026-02-20', '2026-05-20', 'Osteoarthritis', 'Private Pay'),
('Susan Jackson', 'Home Health', 'Active', 'Gulf States', '2026-03-01', '2026-06-01', 'Post-surgical Care', 'Commercial'),
-- Hospice episodes
('Helen White', 'Hospice', 'Active', 'Southeast', '2025-12-01', NULL, 'End-stage COPD', 'Medicare'),
('Charles Harris', 'Hospice', 'Active', 'Texas', '2026-01-10', NULL, 'Advanced Cancer', 'Medicare'),
('Margaret Clark', 'Hospice', 'Active', 'Midwest', '2026-01-15', NULL, 'End-stage Heart Failure', 'Medicaid'),
('George Lewis', 'Hospice', 'Active', 'Gulf States', '2026-02-01', NULL, 'Advanced Dementia', 'Medicare'),
('Dorothy Robinson', 'Hospice', 'Active', 'Northeast', '2026-02-10', NULL, 'Terminal Cancer', 'Medicare'),
-- Personal Care episodes
('Karen Walker', 'Personal Care', 'Active', 'Southeast', '2026-01-05', '2026-07-05', 'Elderly Assistance', 'Private Pay'),
('Steven Hall', 'Personal Care', 'Active', 'Texas', '2026-01-20', '2026-07-20', 'Disability Support', 'Medicaid'),
('Nancy Allen', 'Personal Care', 'Active', 'Mid-Atlantic', '2026-02-01', '2026-08-01', 'Post-stroke Care', 'Medicare'),
('Daniel Young', 'Personal Care', 'Active', 'Mountain West', '2026-02-15', '2026-08-15', 'Elderly Assistance', 'Private Pay'),
('Betty King', 'Personal Care', 'Active', 'Pacific', '2026-03-01', '2026-09-01', 'Chronic Disease Support', 'Medicaid');

-- Seed Providers (across disciplines and regions)
INSERT INTO providers (name, discipline, status, region, utilization_pct, avg_visit_minutes, hire_date) VALUES
-- RNs
('Sarah Martinez, RN', 'RN', 'Active', 'Southeast', 94.2, 38, '2019-03-15'),
('David Thompson, RN', 'RN', 'Active', 'Texas', 91.5, 42, '2020-06-01'),
('Jennifer Lee, RN', 'RN', 'Active', 'Northeast', 89.3, 40, '2021-01-10'),
('Amanda Foster, RN', 'RN', 'Active', 'Mid-Atlantic', 93.1, 37, '2018-09-20'),
('Christopher Moore, RN', 'RN', 'Active', 'Midwest', 90.8, 41, '2020-11-15'),
-- LVNs
('Maria Rodriguez, LVN', 'LVN', 'Active', 'Southeast', 88.4, 45, '2020-04-01'),
('Lisa Chang, LVN', 'LVN', 'Active', 'Gulf States', 87.2, 44, '2021-07-15'),
('Angela Brown, LVN', 'LVN', 'Active', 'Texas', 89.7, 43, '2019-12-01'),
-- PTs
('James Chen, PT', 'PT', 'Active', 'Pacific', 86.5, 48, '2018-05-10'),
('Robert Kim, PT', 'PT', 'Active', 'Mountain West', 84.2, 50, '2020-02-20'),
('Michelle Park, PT', 'PT', 'Active', 'Northeast', 85.1, 47, '2021-03-01'),
-- OTs
('Emily Watson, OT', 'OT', 'Active', 'Mid-Atlantic', 79.8, 52, '2019-08-15'),
('Andrew Scott, OT', 'OT', 'Active', 'Midwest', 78.4, 50, '2021-06-01'),
-- STs
('Rachel Green, ST', 'ST', 'Active', 'Southeast', 82.3, 55, '2020-01-15'),
('Kevin Adams, ST', 'ST', 'Active', 'Texas', 80.1, 53, '2021-09-01'),
-- MSWs
('Sandra Nelson, MSW', 'MSW', 'Active', 'Gulf States', 74.6, 60, '2019-11-01'),
('Timothy Hill, MSW', 'MSW', 'Active', 'Pacific', 71.2, 58, '2020-08-15'),
-- HHAs
('Catherine Bell, HHA', 'HHA', 'Active', 'Southeast', 95.1, 35, '2020-03-01'),
('Mark Turner, HHA', 'HHA', 'Active', 'Texas', 93.8, 36, '2019-07-15'),
('Diana Reed, HHA', 'HHA', 'Active', 'Mountain West', 94.5, 34, '2021-01-20');

-- Seed Visits (across 8 national regions)
INSERT INTO visits (episode_id, provider_id, region, visit_date, visit_status, visit_type, duration_minutes, patient_rating) VALUES
-- Southeast (FL, GA, AL, SC, NC, TN) - largest region
(1, 1, 'Southeast', CURRENT_DATE, 'Completed', 'Skilled Nursing', 38, 4.9),
(6, 6, 'Southeast', CURRENT_DATE, 'Completed', 'Skilled Nursing', 44, 4.7),
(11, 14, 'Southeast', CURRENT_DATE, 'Completed', 'Speech Therapy', 55, 4.5),
(16, 18, 'Southeast', CURRENT_DATE, 'Completed', 'Home Health Aide', 35, 4.9),
(1, 1, 'Southeast', CURRENT_DATE, 'Scheduled', 'Follow-up', 40, NULL),
(6, 14, 'Southeast', CURRENT_DATE, 'Pending', 'Speech Therapy', 50, NULL),
-- Texas (TX) - second largest
(2, 2, 'Texas', CURRENT_DATE, 'Completed', 'Skilled Nursing', 42, 4.8),
(7, 8, 'Texas', CURRENT_DATE, 'Completed', 'Skilled Nursing', 43, 4.7),
(12, 15, 'Texas', CURRENT_DATE, 'Completed', 'Speech Therapy', 53, 4.6),
(17, 19, 'Texas', CURRENT_DATE, 'Completed', 'Home Health Aide', 36, 4.9),
(2, 15, 'Texas', CURRENT_DATE, 'Scheduled', 'Speech Therapy', 50, NULL),
-- Northeast (MA, CT, NY, NJ, PA)
(3, 3, 'Northeast', CURRENT_DATE, 'Completed', 'Skilled Nursing', 40, 4.8),
(15, 11, 'Northeast', CURRENT_DATE, 'Completed', 'Physical Therapy', 47, 4.7),
(3, 3, 'Northeast', CURRENT_DATE, 'Scheduled', 'Assessment', 38, NULL),
(15, 11, 'Northeast', CURRENT_DATE, 'Pending', 'Physical Therapy', 48, NULL),
-- Midwest (OH, IN, IL, MI, WI)
(5, 5, 'Midwest', CURRENT_DATE, 'Completed', 'Skilled Nursing', 41, 4.8),
(13, 13, 'Midwest', CURRENT_DATE, 'Completed', 'Occupational Therapy', 52, 4.6),
(5, 5, 'Midwest', CURRENT_DATE, 'Scheduled', 'Assessment', 40, NULL),
(13, 13, 'Midwest', CURRENT_DATE, 'Pending', 'Occupational Therapy', 50, NULL),
-- Mid-Atlantic (VA, MD, DE, DC)
(8, 4, 'Mid-Atlantic', CURRENT_DATE, 'Completed', 'Skilled Nursing', 38, 4.9),
(18, 12, 'Mid-Atlantic', CURRENT_DATE, 'Completed', 'Occupational Therapy', 48, 4.8),
(8, 4, 'Mid-Atlantic', CURRENT_DATE, 'Pending', 'Skilled Nursing', 40, NULL),
-- Mountain West (CO, UT, AZ, NV, NM)
(4, 10, 'Mountain West', CURRENT_DATE, 'Completed', 'Physical Therapy', 50, 4.7),
(20, 20, 'Mountain West', CURRENT_DATE, 'Completed', 'Home Health Aide', 34, 4.8),
(4, 10, 'Mountain West', CURRENT_DATE, 'Scheduled', 'Physical Therapy', 48, NULL),
-- Pacific (CA, OR, WA)
(9, 9, 'Pacific', CURRENT_DATE, 'Completed', 'Physical Therapy', 48, 4.8),
(19, 17, 'Pacific', CURRENT_DATE, 'Scheduled', 'Social Work', 58, NULL),
-- Gulf States (LA, MS, AL)
(10, 7, 'Gulf States', CURRENT_DATE, 'Completed', 'Skilled Nursing', 44, 4.7),
(14, 16, 'Gulf States', CURRENT_DATE, 'Completed', 'Social Work', 60, 4.7),
(10, 7, 'Gulf States', CURRENT_DATE, 'Pending', 'Skilled Nursing', 42, NULL);

-- Seed Weekly Revenue
INSERT INTO weekly_revenue (week_number, week_label, revenue_amount, target_amount) VALUES
(1, 'W1', 2.4, 2.8),
(2, 'W2', 2.7, 2.8),
(3, 'W3', 2.9, 2.8),
(4, 'W4', 3.1, 2.8),
(5, 'W5', 2.8, 2.8),
(6, 'W6', 3.2, 2.8),
(7, 'W7', 3.4, 2.8);

-- Seed Performance Metrics
INSERT INTO performance_metrics (metric_name, score) VALUES
('Clinical Quality', 89.0),
('Compliance', 91.0),
('Documentation', 94.0),
('Efficiency', 87.0),
('Patient Satisfaction', 96.0),
('Visit Completion', 92.0);

-- Seed Revenue by Payer
INSERT INTO revenue_by_payer (payer_name, revenue, margin) VALUES
('Medicare', 12.4, 18.2),
('Medicaid', 4.8, 14.5),
('Commercial', 6.2, 22.3),
('Managed Care', 3.9, 16.8),
('Private Pay', 2.1, 28.5);

-- Seed Cash Flow
INSERT INTO cash_flow (month_number, month_label, inflow, outflow, net) VALUES
(1, 'Oct', 18.2, 15.4, 2.8),
(2, 'Nov', 19.5, 16.1, 3.4),
(3, 'Dec', 21.3, 17.8, 3.5),
(4, 'Jan', 20.1, 16.9, 3.2),
(5, 'Feb', 22.4, 18.2, 4.2),
(6, 'Mar', 23.8, 19.1, 4.7);

-- Seed AR Aging
INSERT INTO ar_aging (bucket, sort_order, amount, percentage) VALUES
('0-30 days', 1, 8.2, 62.0),
('31-60 days', 2, 2.9, 22.0),
('61-90 days', 3, 1.4, 11.0),
('90+ days', 4, 0.7, 5.0);

-- Seed Cost vs Budget
INSERT INTO cost_budget (category, current_amount, budget_amount, variance) VALUES
('Facilities', 1.2, 1.3, -7.7),
('Labor', 12.8, 12.2, 4.9),
('Other', 0.9, 1.0, -10.0),
('Supplies', 2.4, 2.5, -4.0),
('Technology', 1.8, 1.7, 5.9);

-- Seed Billing Alerts
INSERT INTO billing_alerts (alert_type, severity, status, description) VALUES
('Claim Denied', 'High', 'Open', 'Medicare claim denied - missing documentation'),
('Late Filing', 'High', 'Open', 'Medicaid claim past filing deadline'),
('Coding Error', 'Medium', 'Open', 'ICD-10 code mismatch on episode 1042'),
('Authorization Expired', 'High', 'Open', 'Prior auth expired for 3 episodes'),
('Duplicate Claim', 'Low', 'Open', 'Potential duplicate submission detected'),
('Underpayment', 'Medium', 'Open', 'Commercial payer underpaid by $2,340'),
('Missing NPI', 'Medium', 'Open', 'Provider NPI missing on 12 claims'),
('Rate Dispute', 'High', 'Open', 'Managed care rate discrepancy'),
('Timely Filing', 'High', 'Open', 'Approaching filing deadline for 5 claims'),
('Coordination of Benefits', 'Medium', 'Open', 'COB issue with dual-eligible patient');

-- Seed Satisfaction Trend
INSERT INTO satisfaction_trend (month_number, month_label, score, responses) VALUES
(1, 'Sep', 4.6, 842),
(2, 'Oct', 4.7, 891),
(3, 'Nov', 4.6, 823),
(4, 'Dec', 4.8, 934),
(5, 'Jan', 4.7, 876),
(6, 'Feb', 4.8, 912),
(7, 'Mar', 4.9, 1048);

-- Seed Compliance Scores
INSERT INTO compliance_scores (metric_name, score) VALUES
('Documentation', 96.0),
('Infection Control', 98.0),
('Privacy (HIPAA)', 99.0),
('Quality Standards', 93.0),
('Regulatory', 95.0),
('Safety Protocols', 94.0);

-- Seed Clinical Outcomes
INSERT INTO clinical_outcomes (outcome_name, current_value, target_value, benchmark_value) VALUES
('ER Visits', 8.7, 10.0, 12.5),
('Falls Prevention', 94.2, 90.0, 87.3),
('Hospitalization Rate', 12.4, 15.0, 18.2),
('Medication Adherence', 91.8, 90.0, 86.5),
('Wound Healing', 88.3, 85.0, 82.1);

-- Seed Quality Incidents
INSERT INTO quality_incidents (incident_type, severity, status, incident_date, description) VALUES
('Fall - No Injury', 'Low', 'Resolved', '2026-03-14', 'Patient slipped in bathroom, no injuries sustained'),
('Medication Error', 'Medium', 'Under Review', '2026-03-13', 'Wrong dosage administered, caught during review'),
('Documentation Gap', 'Low', 'Resolved', '2026-03-12', 'Missing visit notes for 2 consecutive visits'),
('Equipment Malfunction', 'Medium', 'Resolved', '2026-03-11', 'Portable oxygen concentrator battery failure'),
('Privacy Concern', 'High', 'Under Review', '2026-03-10', 'Patient records accessed from unrecognized device');

SELECT 'SEEDING COMPLETE' as status,
       (SELECT count(*) FROM episodes) as episodes,
       (SELECT count(*) FROM providers) as providers,
       (SELECT count(*) FROM visits) as visits,
       (SELECT count(*) FROM quality_incidents) as incidents;
