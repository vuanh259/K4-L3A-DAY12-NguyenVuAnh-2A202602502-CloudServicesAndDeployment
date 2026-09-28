"""Checks for simultaneous requests and startup behavior beyond lab fixtures."""
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limiter import RateLimiter


def test_rate_limit_is_atomic_across_instances(fake_redis):
    def hit(_):
        try:
            RateLimiter(fake_redis, 5).check("parallel", now=1000)
            return 200
        except HTTPException as exc:
            return exc.status_code

    with ThreadPoolExecutor(max_workers=12) as pool:
        statuses = list(pool.map(hit, range(30)))
    assert statuses.count(200) == 5
    assert statuses.count(429) == 25
    assert fake_redis.zcard("ratelimit:parallel") == 5


def test_lifespan_can_start_in_testclient_thread():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
