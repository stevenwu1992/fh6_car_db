-- 调校：游戏内发布时间 + 点赞
-- 说明：Worker 冷启动时 src/schema.js 会自动补同样的 DDL（幂等），
-- 这份脚本只用于手工迁移/留档。

ALTER TABLE tunes ADD COLUMN game_date TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS tune_likes (
  tune_id    TEXT NOT NULL,
  user_id    TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (tune_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tune_likes_tune ON tune_likes(tune_id);
