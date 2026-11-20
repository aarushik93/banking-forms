from app.ratelimit import SlidingWindowRateLimiter


def test_limiter_blocks_after_limit():
    limiter = SlidingWindowRateLimiter(limit_per_minute=3)
    assert all(limiter.allow("1.2.3.4") for _ in range(3))
    assert not limiter.allow("1.2.3.4")
    # Other clients are unaffected
    assert limiter.allow("5.6.7.8")


def test_limiter_disabled_when_zero():
    limiter = SlidingWindowRateLimiter(limit_per_minute=0)
    assert all(limiter.allow("1.2.3.4") for _ in range(100))
