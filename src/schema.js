/**
 * 幂等建表：Worker 冷启动时补一次 DDL。
 *
 * 为什么不只用迁移脚本文本：控制台/CLI 执行迁移需要人工介入，
 * 而 D1 支持从 Worker 里跑 CREATE TABLE IF NOT EXISTS，
 * 把「表不存在就 500」这类部署事故直接消掉。语句全是 IF NOT EXISTS，重复执行无副作用。
 */

let ready = false;

const DDL = [
  `CREATE TABLE IF NOT EXISTS users (
     id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, password_hash TEXT,
     email_verified INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0,
     created_at INTEGER NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS user_sessions (
     token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at INTEGER NOT NULL,
     expires_at INTEGER NOT NULL, ip_hash TEXT, ua_hash TEXT)`,
  `CREATE INDEX IF NOT EXISTS idx_usessions_user ON user_sessions(user_id)`,
  `CREATE INDEX IF NOT EXISTS idx_usessions_exp ON user_sessions(expires_at)`,
  `CREATE TABLE IF NOT EXISTS steam_links (
     steam_id TEXT PRIMARY KEY, user_id TEXT NOT NULL UNIQUE, persona TEXT, avatar TEXT,
     linked_at INTEGER NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS auth_rate_limits (
     bucket TEXT PRIMARY KEY, window_start INTEGER NOT NULL, count INTEGER NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS admin_sessions (
     token_hash TEXT PRIMARY KEY, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
     ip_hash TEXT, ua_hash TEXT)`,
  `CREATE INDEX IF NOT EXISTS idx_admin_sessions_exp ON admin_sessions(expires_at)`,
  `CREATE TABLE IF NOT EXISTS tier_overrides (
     car_id TEXT PRIMARY KEY, race_tier TEXT, race_group TEXT, drift_tier TEXT,
     updated_by TEXT, updated_at INTEGER NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS garage (
     user_id TEXT NOT NULL, car_id TEXT NOT NULL, state TEXT NOT NULL,
     updated_at INTEGER NOT NULL, PRIMARY KEY(user_id, car_id))`,
  `CREATE INDEX IF NOT EXISTS idx_garage_car ON garage(car_id, state)`,
  `CREATE TABLE IF NOT EXISTS ratings (
     user_id TEXT NOT NULL, car_id TEXT NOT NULL, score INTEGER NOT NULL,
     updated_at INTEGER NOT NULL, PRIMARY KEY(user_id, car_id))`,
  `CREATE INDEX IF NOT EXISTS idx_ratings_car ON ratings(car_id)`,
  `CREATE TABLE IF NOT EXISTS tunes (
     id TEXT PRIMARY KEY, user_id TEXT NOT NULL, car_id TEXT NOT NULL,
     share_code TEXT NOT NULL, author_id TEXT NOT NULL, tier_group TEXT NOT NULL,
     note TEXT, payload TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
     UNIQUE(car_id, share_code))`,
  `CREATE INDEX IF NOT EXISTS idx_tunes_car ON tunes(car_id, created_at DESC)`,
];

export async function ensureSchema(env) {
  if (ready) return;
  for (const sql of DDL) {
    try {
      await env.DB.prepare(sql).run();
    } catch (e) {
      // 并发冷启动时可能撞上重复建表，忽略即可；其它错误抛出去便于排查
      if (!/already exists/i.test(String(e?.message || e))) throw e;
    }
  }
  ready = true;
}
