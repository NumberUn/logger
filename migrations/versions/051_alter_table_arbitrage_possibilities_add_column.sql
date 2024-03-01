BEGIN;

LOCK arbitrage_possibilities IN ROW EXCLUSIVE MODE NOWAIT;

ALTER TABLE arbitrage_possibilities add column env varchar(64);
ALTER TABLE arbitrage_possibilities add column target_profit FLOAT;

COMMIT;
