CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY,
    account_name TEXT,
    tier TEXT,
    account_arr_usd INTEGER,
    first_response_latency_mins INTEGER,
    linked_incident_id TEXT
);

INSERT INTO support_tickets VALUES
('TKT-901', 'Apex Financial', 'enterprise', 850000, 142, 'INC-402'),
('TKT-902', 'Breeze Retail', 'mid-market', 95000, 180, 'INC-402'),
('TKT-903', 'Cobalt Health', 'enterprise', 520000, 28, 'INC-409'),
('TKT-904', 'Delta Logistics', 'enterprise', 600000, 95, 'INC-402'),
('TKT-905', 'Echo Media', 'enterprise', 410000, 45, 'INC-409');
