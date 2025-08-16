users (
  id UUID PRIMARY KEY,
  email TEXT,
  pass_hash TEXT,
  first_name TEXT,
  last_name TEXT,
  created_at TIMESTAMP,
  role TEXT -- 'admin', 'manager', 'tenant'
)