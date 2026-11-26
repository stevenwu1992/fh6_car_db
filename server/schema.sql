-- 玩家身份与数据（Node 版，字段与 docs/architecture-player-identity.md 对齐）
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  display_name  TEXT,
  avatar_url    TEXT,
  is_anonymous  INTEGER NOT NULL DEFAULT 1,
  is_admin      INTEGER NOT NULL DEFAULT 0,
  merged_into   TEXT,
  created_at    INTEGER NOT NULL,
  last_seen_at  INTEGER
);

CREATE TABLE IF NOT EXISTS identities (
  id            TEXT PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider      TEXT NOT NULL,
  provider_uid  TEXT NOT NULL,
  email         TEXT,
  created_at    INTEGER NOT NULL,
  UNIQUE (provider, provider_uid)
);
CREATE INDEX IF NOT EXISTS idx_identities_user ON identities(user_id);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash    TEXT PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at    INTEGER NOT NULL,
  expires_at    INTEGER NOT NULL,
  ip_hash       TEXT,
  ua_hash       TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS garage (
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  car_id        TEXT NOT NULL,
  state         TEXT NOT NULL CHECK (state IN ('owned','favorite','wishlist')),
  updated_at    INTEGER NOT NULL,
  PRIMARY KEY (user_id, car_id)
);
CREATE INDEX IF NOT EXISTS idx_garage_car ON garage(car_id, state);

CREATE TABLE IF NOT EXISTS ratings (
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  car_id        TEXT NOT NULL,
  score         INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
  updated_at    INTEGER NOT NULL,
  PRIMARY KEY (user_id, car_id)
);
CREATE INDEX IF NOT EXISTS idx_ratings_car ON ratings(car_id);

CREATE TABLE IF NOT EXISTS tunes (
  id            TEXT PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  car_id        TEXT NOT NULL,
  share_code    TEXT NOT NULL,           -- 游戏内 9 位数字调校分享码
  author_id     TEXT NOT NULL,           -- 调校作者的游戏 ID（非站内昵称）
  tier_group    TEXT NOT NULL,           -- 适用强度分级，如 S1 800泥地 / 漂移神车
  note          TEXT NOT NULL DEFAULT '',-- 说明，最多 100 个中文字符
  payload       TEXT NOT NULL DEFAULT '{}',
  created_at    INTEGER NOT NULL,
  updated_at    INTEGER NOT NULL,
  UNIQUE (car_id, share_code)
);
CREATE INDEX IF NOT EXISTS idx_tunes_car ON tunes(car_id, created_at DESC);

CREATE TABLE IF NOT EXISTS tier_overrides (
  car_id        TEXT PRIMARY KEY,
  race_tier     TEXT,
  race_group    TEXT,
  drift_tier    TEXT,
  updated_by    TEXT,
  updated_at    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS login_tokens (
  token_hash    TEXT PRIMARY KEY,
  email         TEXT NOT NULL,
  user_id       TEXT,
  next_path     TEXT,
  created_at    INTEGER NOT NULL,
  expires_at    INTEGER NOT NULL,
  used_at       INTEGER
);
CREATE INDEX IF NOT EXISTS idx_login_tokens_email ON login_tokens(email);

CREATE TABLE IF NOT EXISTS rate_limits (
  bucket        TEXT PRIMARY KEY,
  window_start  INTEGER NOT NULL,
  count         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
  id            TEXT PRIMARY KEY,
  user_id       TEXT,
  action        TEXT NOT NULL,
  detail        TEXT,
  created_at    INTEGER NOT NULL
);

-- 管理员密码会话：与玩家会话完全分离。
-- 独立 cookie（fh6_admin）、短时效、不写 users.is_admin，
-- 这样密码泄露的最后影响面是一段时间的管理权限，而不是某个账号被永久提权。
CREATE TABLE IF NOT EXISTS admin_sessions (
  token_hash    TEXT PRIMARY KEY,
  created_at    INTEGER NOT NULL,
  expires_at    INTEGER NOT NULL,
  ip_hash       TEXT,
  ua_hash       TEXT
);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_exp ON admin_sessions(expires_at);
