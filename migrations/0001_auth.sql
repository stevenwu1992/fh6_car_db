-- 邮箱注册/登录 + Steam 登录所需表结构
-- 执行：D1 控制台 Console 粘贴，或 wrangler d1 execute <db> --remote --file=migrations/0001_auth.sql

-- 用户：邮箱用户与 Steam 用户共用一张表，互斥字段可为空
CREATE TABLE IF NOT EXISTS users (
  id             TEXT PRIMARY KEY,
  email          TEXT UNIQUE,
  name           TEXT,
  password_hash  TEXT,
  email_verified INTEGER NOT NULL DEFAULT 0,
  is_admin       INTEGER NOT NULL DEFAULT 0,
  created_at     INTEGER NOT NULL
);

-- 会话：只存 token 的 SHA-256，数据库泄露也无法直接冒用
CREATE TABLE IF NOT EXISTS user_sessions (
  token_hash  TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  INTEGER NOT NULL,
  expires_at  INTEGER NOT NULL,
  ip_hash     TEXT,
  ua_hash     TEXT
);
CREATE INDEX IF NOT EXISTS idx_usessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_usessions_exp  ON user_sessions(expires_at);

-- Steam 绑定：一个 SteamID64 只能绑一个账号，一个账号只绑一个 Steam
CREATE TABLE IF NOT EXISTS steam_links (
  steam_id   TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  persona    TEXT,
  avatar     TEXT,
  linked_at  INTEGER NOT NULL
);

-- 登录/注册频次限制（按 IP 与邮箱两个维度）
CREATE TABLE IF NOT EXISTS auth_rate_limits (
  bucket        TEXT PRIMARY KEY,
  window_start  INTEGER NOT NULL,
  count         INTEGER NOT NULL
);
