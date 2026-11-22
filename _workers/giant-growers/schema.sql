CREATE TABLE IF NOT EXISTS results (
  week TEXT NOT NULL,
  farmer TEXT NOT NULL,
  weight INTEGER NOT NULL,
  PRIMARY KEY (week, farmer)
);
CREATE INDEX IF NOT EXISTS best ON results(week, weight DESC, farmer);
