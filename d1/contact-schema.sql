-- Cloudflare D1：站点反馈表单
-- 执行方式（二选一）
--   控制台：D1 → 选中库 → Console → 粘贴执行
--   命令行：wrangler d1 execute fh6_contacts --remote --file=d1/contact-schema.sql

CREATE TABLE IF NOT EXISTS contacts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  contact     TEXT NOT NULL,
  message     TEXT NOT NULL,
  created_at  INTEGER NOT NULL,          -- Unix 秒，与本项目其他表一致
  ip_hash     TEXT,                      -- 只存 SHA-256，便于限流与追溯，不落原始 IP
  ua          TEXT
);

CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contacts_ip      ON contacts(ip_hash, created_at);
