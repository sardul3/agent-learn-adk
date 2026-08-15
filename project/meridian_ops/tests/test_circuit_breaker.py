from meridian_ops.safety.circuit_breaker import CircuitBreaker


def test_opens_after_three_timeouts():
    br = CircuitBreaker(failure_threshold=3, cooldown_s=30.0)
    br.record_timeout(now=100.0)
    br.record_timeout(now=101.0)
    assert br.allow_call(now=102.0) is True
    br.record_timeout(now=102.0)
    assert br.allow_call(now=102.0) is False
    assert br.allow_call(now=131.9) is False
    assert br.allow_call(now=132.0) is True  # cooldown elapsed


def test_success_resets_failures():
    br = CircuitBreaker(failure_threshold=3, cooldown_s=30.0)
    br.record_timeout(now=1.0)
    br.record_timeout(now=2.0)
    br.record_success()
    br.record_timeout(now=3.0)
    assert br.allow_call(now=3.0) is True