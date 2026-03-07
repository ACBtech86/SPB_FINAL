-- BCSrvSqlMq - PostgreSQL Database Schema
-- Created: 2026-02-26
-- Database: bcspbstr
--
-- IMPORTANT: This is a TEMPLATE based on the SQL Server version.
-- You MUST verify column definitions, data types, and constraints
-- against your original SQL Server database schema.

-- Connect to the database first:
-- psql -h localhost -U postgres -d bcspbstr

-- ============================================================================
-- Table: spb_log_bacen
-- Purpose: Service activity log
-- ============================================================================

CREATE TABLE IF NOT EXISTS spb_log_bacen (
    log_id          SERIAL PRIMARY KEY,
    log_timestamp   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_level       VARCHAR(10),           -- DEBUG, INFO, WARNING, ERROR
    log_source      VARCHAR(50),           -- Service component
    log_message     TEXT,
    log_details     TEXT,
    session_id      VARCHAR(50),
    user_id         VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_spb_log_timestamp ON spb_log_bacen(log_timestamp);
CREATE INDEX IF NOT EXISTS idx_spb_log_level ON spb_log_bacen(log_level);
CREATE INDEX IF NOT EXISTS idx_spb_log_session ON spb_log_bacen(session_id);

-- ============================================================================
-- Table: spb_bacen_to_local
-- Purpose: Messages from Bacen to local system (inbound)
-- ============================================================================

CREATE TABLE IF NOT EXISTS spb_bacen_to_local (
    msg_id              SERIAL PRIMARY KEY,
    msg_timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    msg_type            VARCHAR(50),       -- Message type code
    msg_content         TEXT,              -- Message payload (XML/JSON)
    msg_status          VARCHAR(20),       -- RECEIVED, PROCESSING, PROCESSED, ERROR
    msg_priority        INTEGER DEFAULT 5,
    msg_queue           VARCHAR(100),      -- Source queue name
    msg_correlation_id  VARCHAR(100),      -- MQ correlation ID
    msg_reply_queue     VARCHAR(100),      -- Reply-to queue
    processed_at        TIMESTAMP,
    error_message       TEXT,
    retry_count         INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bacen_local_timestamp ON spb_bacen_to_local(msg_timestamp);
CREATE INDEX IF NOT EXISTS idx_bacen_local_status ON spb_bacen_to_local(msg_status);
CREATE INDEX IF NOT EXISTS idx_bacen_local_corr_id ON spb_bacen_to_local(msg_correlation_id);
CREATE INDEX IF NOT EXISTS idx_bacen_local_type ON spb_bacen_to_local(msg_type);

-- ============================================================================
-- Table: spb_local_to_bacen
-- Purpose: Messages from local system to Bacen (outbound)
-- ============================================================================

CREATE TABLE IF NOT EXISTS spb_local_to_bacen (
    msg_id              SERIAL PRIMARY KEY,
    msg_timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    msg_type            VARCHAR(50),       -- Message type code
    msg_content         TEXT,              -- Message payload (XML/JSON)
    msg_status          VARCHAR(20),       -- PENDING, SENT, CONFIRMED, ERROR
    msg_priority        INTEGER DEFAULT 5,
    msg_queue           VARCHAR(100),      -- Target queue name
    msg_correlation_id  VARCHAR(100),      -- MQ correlation ID
    msg_reply_queue     VARCHAR(100),      -- Reply-to queue
    sent_at             TIMESTAMP,
    confirmed_at        TIMESTAMP,
    error_message       TEXT,
    retry_count         INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_local_bacen_timestamp ON spb_local_to_bacen(msg_timestamp);
CREATE INDEX IF NOT EXISTS idx_local_bacen_status ON spb_local_to_bacen(msg_status);
CREATE INDEX IF NOT EXISTS idx_local_bacen_corr_id ON spb_local_to_bacen(msg_correlation_id);
CREATE INDEX IF NOT EXISTS idx_local_bacen_type ON spb_local_to_bacen(msg_type);

-- ============================================================================
-- Table: spb_controle
-- Purpose: Control/configuration table
-- ============================================================================

CREATE TABLE IF NOT EXISTS spb_controle (
    control_id      SERIAL PRIMARY KEY,
    control_key     VARCHAR(100) UNIQUE NOT NULL,  -- Configuration key
    control_value   TEXT,                          -- Configuration value
    control_type    VARCHAR(50),                   -- DATA_TYPE: STRING, INT, BOOL, JSON
    description     TEXT,
    is_active       BOOLEAN DEFAULT true,
    last_modified   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by     VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX IF NOT EXISTS idx_controle_key ON spb_controle(control_key);
CREATE INDEX IF NOT EXISTS idx_controle_active ON spb_controle(is_active);

-- ============================================================================
-- Sample Control Data
-- ============================================================================

INSERT INTO spb_controle (control_key, control_value, control_type, description)
VALUES
    ('SERVICE_VERSION', '1.0.0', 'STRING', 'BCSrvSqlMq service version'),
    ('MAX_RETRY_COUNT', '3', 'INT', 'Maximum retry attempts for failed messages'),
    ('RETRY_DELAY_MS', '5000', 'INT', 'Delay between retries (milliseconds)'),
    ('SERVICE_ENABLED', 'true', 'BOOL', 'Enable/disable service processing')
ON CONFLICT (control_key) DO NOTHING;

-- ============================================================================
-- Trigger: Auto-update updated_at timestamp
-- ============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to message tables
CREATE TRIGGER update_bacen_local_timestamp
    BEFORE UPDATE ON spb_bacen_to_local
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_local_bacen_timestamp
    BEFORE UPDATE ON spb_local_to_bacen
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Grant Permissions (adjust username as needed)
-- ============================================================================

-- Example: Grant permissions to application user
-- Replace 'bcsrv_user' with your actual PostgreSQL user

-- CREATE USER bcsrv_user WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE bcspbstr TO bcsrv_user;
-- GRANT USAGE ON SCHEMA public TO bcsrv_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bcsrv_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bcsrv_user;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- List all tables
-- \dt

-- Check table structures
-- \d spb_log_bacen
-- \d spb_bacen_to_local
-- \d spb_local_to_bacen
-- \d spb_controle

-- Test inserts
-- INSERT INTO spb_log_bacen (log_level, log_source, log_message)
-- VALUES ('INFO', 'SETUP', 'Database schema created successfully');

-- SELECT * FROM spb_log_bacen;
-- SELECT * FROM spb_controle;

-- ============================================================================
-- Notes
-- ============================================================================

-- 1. SERIAL vs IDENTITY:
--    - SERIAL is PostgreSQL's auto-increment (creates a sequence)
--    - For PostgreSQL 10+, you can use GENERATED ALWAYS AS IDENTITY
--
-- 2. Data Types:
--    - SQL Server VARCHAR(MAX) → PostgreSQL TEXT
--    - SQL Server DATETIME → PostgreSQL TIMESTAMP
--    - SQL Server BIT → PostgreSQL BOOLEAN
--    - SQL Server NVARCHAR → PostgreSQL VARCHAR (UTF-8 by default)
--
-- 3. Check your original SQL Server schema for:
--    - Additional columns
--    - Foreign key constraints
--    - Check constraints
--    - Default values
--    - Triggers and stored procedures
--
-- 4. Migration Tools:
--    - pgloader (automated SQL Server → PostgreSQL migration)
--    - ora2pg (Oracle/SQL Server to PostgreSQL)
--    - Manual export/import via CSV

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
