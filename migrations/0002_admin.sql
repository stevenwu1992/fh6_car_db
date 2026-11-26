-- 管理员密码会话 + 分级覆盖表
CREATE TABLE IF NOT EXISTS admin_sessions (
  token_hash  TEXT PRIMARY KEY,
  created_at  INTEGER NOT NULL,
  expires_at  INTEGER NOT NULL,
  ip_hash     TEXT,
  ua_hash     TEXT
);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_exp ON admin_sessions(expires_at);

-- 与 server/ 版字段完全一致，便于将来互导
CREATE TABLE IF NOT EXISTS tier_overrides (
  car_id      TEXT PRIMARY KEY,
  race_tier   TEXT,
  race_group  TEXT,
  drift_tier  TEXT,
  updated_by  TEXT,
  updated_at  INTEGER NOT NULL
);
