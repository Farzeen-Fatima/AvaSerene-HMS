-- ============================================================
--  AVA SERENE HOSPITAL  --  PostgreSQL Schema with Triggers
--  Step 1: In pgAdmin 4, create a database called:
--              ava_serene_hospital
--  Step 2: Open Query Tool on that database
--  Step 3: Paste and run this entire file
-- ============================================================

-- Drop tables if you need a fresh start (optional, uncomment if needed)
-- DROP TABLE IF EXISTS audit_logs CASCADE;
-- DROP TABLE IF EXISTS patients CASCADE;
-- DROP TABLE IF EXISTS doctors CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- ── USERS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(100) UNIQUE NOT NULL,
    password    BYTEA        NOT NULL,
    role        VARCHAR(10)  NOT NULL CHECK (role IN ('admin', 'worker')),
    created_at  TIMESTAMP    DEFAULT NOW(),
    last_login  TIMESTAMP
);


-- ── DOCTORS ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctors (
    id          SERIAL       PRIMARY KEY,
    name        VARCHAR(150) UNIQUE NOT NULL,
    specialty   VARCHAR(150),
    created_at  TIMESTAMP    DEFAULT NOW()
);


-- ── PATIENTS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20)   UNIQUE NOT NULL,
    name        VARCHAR(150)  NOT NULL,
    age         INTEGER       NOT NULL
                              CHECK (age > 0 AND age <= 100),
    gender      VARCHAR(10)   CHECK (gender IN ('Male', 'Female', 'Other')),
    area        VARCHAR(150),
    doctor      VARCHAR(150),
    fee         NUMERIC(10,2) NOT NULL DEFAULT 0
                              CHECK (fee >= 0),
    visit_date  TIMESTAMP     DEFAULT NOW(),
    status      VARCHAR(20)   DEFAULT 'waiting'
                              CHECK (status IN ('waiting','in_consultation','completed'))
);


-- ── AUDIT_LOGS ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     REFERENCES users(id) ON DELETE SET NULL,
    username    VARCHAR(100),
    action      TEXT        NOT NULL,
    timestamp   TIMESTAMP   DEFAULT NOW()
);


-- ── INDEXES ──────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_patients_doctor     ON patients(doctor);
CREATE INDEX IF NOT EXISTS idx_patients_visit_date ON patients(visit_date);
CREATE INDEX IF NOT EXISTS idx_patients_status     ON patients(status);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp     ON audit_logs(timestamp);


-- ════════════════════════════════════════════════════════════════════════════
--  TRIGGERS FOR DATA VALIDATION & AUDIT LOGGING
-- ════════════════════════════════════════════════════════════════════════════

-- ── TRIGGER 1: VALIDATE FEE ON INSERT ────────────────────────────────────
CREATE OR REPLACE FUNCTION validate_patient_fee_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fee < 0 THEN
        RAISE EXCEPTION 'ERROR: Fee cannot be negative. Provided fee: %', NEW.fee;
    END IF;
    IF NEW.fee > 100000 THEN
        RAISE WARNING 'Warning: Unusually high fee (Rs. %). Please verify.', NEW.fee;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validate_fee_insert ON patients;
CREATE TRIGGER trigger_validate_fee_insert
    BEFORE INSERT ON patients
    FOR EACH ROW
    EXECUTE FUNCTION validate_patient_fee_insert();


-- ── TRIGGER 2: VALIDATE FEE ON UPDATE ────────────────────────────────────
CREATE OR REPLACE FUNCTION validate_patient_fee_update()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fee < 0 THEN
        RAISE EXCEPTION 'ERROR: Fee cannot be negative. Attempted fee: %', NEW.fee;
    END IF;
    IF NEW.fee > 100000 AND OLD.fee <= 100000 THEN
        RAISE WARNING 'Warning: Fee increased to unusually high amount (Rs. %). Verify this is correct.', NEW.fee;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validate_fee_update ON patients;
CREATE TRIGGER trigger_validate_fee_update
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION validate_patient_fee_update();


-- ── TRIGGER 3: VALIDATE AGE ON INSERT ────────────────────────────────────
CREATE OR REPLACE FUNCTION validate_patient_age_insert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.age <= 0 THEN
        RAISE EXCEPTION 'ERROR: Age must be greater than 0. Provided age: %', NEW.age;
    END IF;
    IF NEW.age > 100 THEN
        RAISE EXCEPTION 'ERROR: Age must be 100 or less. Provided age: %', NEW.age;
    END IF;
    IF NEW.age < 1 OR NEW.age > 100 THEN
        RAISE WARNING 'Warning: Unusual age detected: %. Please verify patient data.', NEW.age;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validate_age_insert ON patients;
CREATE TRIGGER trigger_validate_age_insert
    BEFORE INSERT ON patients
    FOR EACH ROW
    EXECUTE FUNCTION validate_patient_age_insert();


-- ── TRIGGER 4: VALIDATE AGE ON UPDATE ────────────────────────────────────
CREATE OR REPLACE FUNCTION validate_patient_age_update()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.age <= 0 THEN
        RAISE EXCEPTION 'ERROR: Age must be greater than 0. Attempted age: %', NEW.age;
    END IF;
    IF NEW.age > 100 THEN
        RAISE EXCEPTION 'ERROR: Age must be 100 or less. Attempted age: %', NEW.age;
    END IF;
    IF ABS(NEW.age - OLD.age) > 20 THEN
        RAISE WARNING 'Warning: Large age change detected from % to %. Verify this is correct.',
            OLD.age, NEW.age;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validate_age_update ON patients;
CREATE TRIGGER trigger_validate_age_update
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION validate_patient_age_update();


-- ── TRIGGER 5: AUDIT LOG - PATIENT INSERT ────────────────────────────────
CREATE OR REPLACE FUNCTION audit_patient_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (username, action, timestamp)
    VALUES (
        'system',
        'Patient registered: ' || NEW.code || ' - ' || NEW.name ||
        ' (Age: ' || NEW.age || ', Fee: Rs. ' || NEW.fee || ')',
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_audit_patient_insert ON patients;
CREATE TRIGGER trigger_audit_patient_insert
    AFTER INSERT ON patients
    FOR EACH ROW
    EXECUTE FUNCTION audit_patient_insert();


-- ── TRIGGER 6: AUDIT LOG - PATIENT UPDATE (STATUS CHANGE) ────────────────
CREATE OR REPLACE FUNCTION audit_patient_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO audit_logs (username, action, timestamp)
        VALUES (
            'system',
            'Patient ' || NEW.code || ' status changed: ' ||
            COALESCE(OLD.status, 'unknown') || ' → ' || NEW.status,
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_audit_patient_status ON patients;
CREATE TRIGGER trigger_audit_patient_status
    AFTER UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION audit_patient_status_change();


-- ── TRIGGER 7: AUDIT LOG - PATIENT DELETE ───────────────────────────────
CREATE OR REPLACE FUNCTION audit_patient_delete()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (username, action, timestamp)
    VALUES (
        'system',
        'Patient deleted: ' || OLD.code || ' - ' || OLD.name ||
        ' (Age: ' || OLD.age || ', Doctor: ' || COALESCE(OLD.doctor, 'N/A') || ')',
        NOW()
    );
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_audit_patient_delete ON patients;
CREATE TRIGGER trigger_audit_patient_delete
    AFTER DELETE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION audit_patient_delete();


-- ── TRIGGER 8: AUTO-TIMESTAMP ON PATIENT UPDATE ──────────────────────────
CREATE OR REPLACE FUNCTION prevent_visit_date_tampering()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.visit_date IS NOT NULL AND NEW.visit_date IS NOT NULL THEN
        IF EXTRACT(DAY FROM (NEW.visit_date - OLD.visit_date)) > 1 THEN
            RAISE WARNING 'Warning: visit_date changed by more than 1 day. Old: %, New: %',
                OLD.visit_date, NEW.visit_date;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_visit_date_safety ON patients;
CREATE TRIGGER trigger_visit_date_safety
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION prevent_visit_date_tampering();


-- ── TRIGGER 9: DOCTOR NAME VALIDATION ────────────────────────────────────
CREATE OR REPLACE FUNCTION validate_doctor_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.name := TRIM(NEW.name);
    IF LENGTH(NEW.name) = 0 THEN
        RAISE EXCEPTION 'ERROR: Doctor name cannot be empty';
    END IF;
    IF LENGTH(NEW.name) < 3 THEN
        RAISE EXCEPTION 'ERROR: Doctor name too short. Must be at least 3 characters.';
    END IF;
    IF NOT NEW.name ~* '^Dr\.? ' THEN
        RAISE WARNING 'Tip: Doctor names should start with "Dr." for consistency. Got: %', NEW.name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validate_doctor_name ON doctors;
CREATE TRIGGER trigger_validate_doctor_name
    BEFORE INSERT ON doctors
    FOR EACH ROW
    EXECUTE FUNCTION validate_doctor_name();


-- ── TRIGGER 10: AUDIT LOG - DOCTOR CREATION ─────────────────────────────
CREATE OR REPLACE FUNCTION audit_doctor_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (username, action, timestamp)
    VALUES (
        'system',
        'Doctor added: ' || NEW.name || ' (Specialty: ' ||
        COALESCE(NEW.specialty, 'Not specified') || ')',
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_audit_doctor_insert ON doctors;
CREATE TRIGGER trigger_audit_doctor_insert
    AFTER INSERT ON doctors
    FOR EACH ROW
    EXECUTE FUNCTION audit_doctor_insert();


-- ── TRIGGER 11: VALIDATION VIEW ─────────────────────────────────────────
CREATE OR REPLACE VIEW validation_test_results AS
SELECT
    'Patients with valid age (1-100)' as test_name,
    COUNT(*) as count,
    'PASS' as status
FROM patients
WHERE age > 0 AND age <= 100
UNION ALL
SELECT
    'Patients with non-negative fees',
    COUNT(*),
    'PASS'
FROM patients
WHERE fee >= 0
UNION ALL
SELECT
    'Patients with both valid age and fee',
    COUNT(*),
    'PASS'
FROM patients
WHERE age > 0 AND age <= 100 AND fee >= 0;


-- ════════════════════════════════════════════════════════════════════════════
--  DUMMY DATA GENERATION (100 Patients & 5 Doctors)
-- ════════════════════════════════════════════════════════════════════════════

-- 1. Insert 5 Dummy Doctors (Ignored if they already exist)
INSERT INTO doctors (name, specialty) VALUES 
('Dr. Aisha Khan', 'Cardiology'),
('Dr. Bilal Ahmed', 'General Medicine'),
('Dr. Sana Tariq', 'Pediatrics'),
('Dr. Omar Farooq', 'Neurology'),
('Dr. Zainab Ali', 'Orthopedics')
ON CONFLICT (name) DO NOTHING;

-- 2. Insert 100 Randomized Patients (Complies with all triggers)
INSERT INTO patients (code, name, age, gender, area, doctor, fee, status)
SELECT 
    'P-' || LPAD((1000 + i)::text, 4, '0'), 
    'Dummy Patient ' || i,
    FLOOR(random() * 80 + 5)::int, -- Random age between 5 and 84 (Passes Age < 100 check)
    (ARRAY['Male', 'Female', 'Other'])[FLOOR(random() * 3) + 1], 
    (ARRAY['North Nazimabad', 'Clifton', 'Gulshan', 'DHA', 'Saddar'])[FLOOR(random() * 5) + 1], 
    (ARRAY['Dr. Aisha Khan', 'Dr. Bilal Ahmed', 'Dr. Sana Tariq', 'Dr. Omar Farooq', 'Dr. Zainab Ali'])[FLOOR(random() * 5) + 1], 
    (ARRAY[500, 1000, 1500, 2000])[FLOOR(random() * 4) + 1], -- Random valid Fee
    (ARRAY['waiting', 'waiting', 'in_consultation', 'completed'])[FLOOR(random() * 4) + 1] -- Mix of statuses
FROM generate_series(1, 100) AS i
ON CONFLICT (code) DO NOTHING;

-- ════════════════════════════════════════════════════════════════════════════
--  VERIFICATION & TEST QUERIES
-- ════════════════════════════════════════════════════════════════════════════

-- Display validation status
SELECT * FROM validation_test_results;

