BEGIN;

LOCK orders IN ROW EXCLUSIVE MODE NOWAIT;

ALTER TABLE orders add column oneway_ping_orderbook FLOAT;
ALTER TABLE orders add column oneway_ping_order FLOAT;
ALTER TABLE orders add column inner_ping FLOAT;

COMMIT;
