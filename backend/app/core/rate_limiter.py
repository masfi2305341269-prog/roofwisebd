"""
RoofwiseBD — Enterprise Rate Limiter
Provides sliding-window throttling for authentication, API abuse prevention, and brute-force protection.

Architecture:
- InMemoryRateLimiter: For local development and single-worker test environments.
- RedisRateLimiter: For production multi-worker clusters sharing state via Redis sorted sets.

Documented Redis Failure Policy:
If Redis becomes unavailable (connection refused, network timeout, broker downtime):
- Rate limiting is NEVER silently disabled.
- The limiter logs a CRITICAL operational warning.
- It immediately falls back to a worker-local InMemoryRateLimiter so each worker process
  continues enforcing sliding-window rate limits locally rather than failing open.
- When Redis recovers, operations automatically resume using the shared cluster cache.
"""
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from typing import Dict, Deque, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiterBase(ABC):
    """
    Abstract interface for rate limiting.
    Provides standard methods for sliding-window request throttling.
    """
    @abstractmethod
    def is_rate_limited(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Returns True if the key has exceeded max_attempts within window_seconds."""
        pass

    @abstractmethod
    def record_attempt(self, key: str) -> None:
        """Records an attempt for the given key."""
        pass

    @abstractmethod
    def reset(self, key: str) -> None:
        """Resets the attempts count for the key."""
        pass


class InMemoryRateLimiter(RateLimiterBase):
    """
    In-memory sliding-window rate limiter for local development and single-process deployments.
    Uses collections.deque of epoch timestamps per key.
    """
    def __init__(self):
        self._storage: Dict[str, Deque[float]] = defaultdict(deque)

    def _cleanup(self, key: str, window_seconds: int, now: float) -> None:
        cutoff = now - window_seconds
        queue = self._storage[key]
        while queue and queue[0] < cutoff:
            queue.popleft()

    def is_rate_limited(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        now = time.time()
        self._cleanup(key, window_seconds, now)
        return len(self._storage[key]) >= max_attempts

    def record_attempt(self, key: str) -> None:
        now = time.time()
        self._storage[key].append(now)

    def reset(self, key: str) -> None:
        if key in self._storage:
            self._storage[key].clear()


class RedisRateLimiter(RateLimiterBase):
    """
    Production Redis-backed sliding-window rate limiter.
    Uses Redis sorted sets (ZADD, ZREMRANGEBYSCORE, ZCARD) to track timestamps across all workers.

    Failure Resilience Policy:
    If Redis fails, the limiter NEVER disables rate limiting. It logs a CRITICAL warning and
    falls back to an internal InMemoryRateLimiter so that each worker still throttles brute-force
    attempts locally rather than failing open.
    """
    def __init__(self, redis_url: str, client=None):
        self.redis_url = redis_url
        self._fallback_limiter = InMemoryRateLimiter()
        self._client = client
        self._redis_available: Optional[bool] = None
        self._last_failure_time: float = 0.0
        self._circuit_cooldown_seconds: float = 5.0

        if self._client is None and redis_url:
            try:
                import redis
                # 1-second timeout to minimize request latency during network partitions
                self._client = redis.from_url(
                    redis_url,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                    decode_responses=True
                )
            except Exception as exc:
                logger.critical(
                    "REDIS INIT FAILURE: Could not connect to %s: %s. "
                    "Rate limiting will operate in resilient local fallback mode.",
                    redis_url, exc
                )
                self._client = None

    def _execute_redis_op(self, op_name: str, op_func, fallback_func):
        """
        Executes a Redis operation safely.
        If Redis raises any connection or command exception, logs a warning and
        executes the fallback in-memory operation.
        Includes a circuit-breaker to prevent repeated network stalls during downtime.
        """
        if self._client is None:
            return fallback_func()

        now = time.time()
        # If Redis recently failed, skip attempting TCP network calls during cooldown
        if (now - self._last_failure_time) < self._circuit_cooldown_seconds:
            return fallback_func()

        try:
            res = op_func()
            self._redis_available = True
            self._last_failure_time = 0.0
            return res
        except Exception as exc:
            self._redis_available = False
            self._last_failure_time = now
            logger.critical(
                "REDIS FAILURE during %s: %s. "
                "SAFE FAILURE POLICY: Circuit open for %.1fs. Falling back to local in-memory rate limiting.",
                op_name, exc, self._circuit_cooldown_seconds
            )
            return fallback_func()


    def is_rate_limited(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        def redis_op():
            now = time.time()
            cutoff = now - window_seconds
            pipe = self._client.pipeline()
            redis_key = f"rate_limit:{key}"
            pipe.zremrangebyscore(redis_key, 0, cutoff)
            pipe.zcard(redis_key)
            results = pipe.execute()
            current_count = results[1]
            return current_count >= max_attempts

        def fallback_op():
            policy = settings.RATE_LIMIT_FAILURE_POLICY.lower()
            if policy == "fail_closed":
                logger.warning(
                    "RATE LIMIT FAIL-CLOSED: Redis cluster unavailable. "
                    "Rejecting request for key '%s' to maintain strict security.", key
                )
                return True
            
            effective_attempts = max_attempts
            if policy == "strict_quota":
                workers = max(1, settings.RATE_LIMIT_ESTIMATED_WORKERS)
                effective_attempts = max(1, max_attempts // workers)

            return self._fallback_limiter.is_rate_limited(key, effective_attempts, window_seconds)


        return self._execute_redis_op("is_rate_limited", redis_op, fallback_op)

    def record_attempt(self, key: str) -> None:
        def redis_op():
            now = time.time()
            redis_key = f"rate_limit:{key}"
            pipe = self._client.pipeline()
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, 3600)  # Expire key after 1 hour of inactivity
            pipe.execute()

        def fallback_op():
            self._fallback_limiter.record_attempt(key)

        self._execute_redis_op("record_attempt", redis_op, fallback_op)

    def reset(self, key: str) -> None:
        def redis_op():
            self._client.delete(f"rate_limit:{key}")

        def fallback_op():
            self._fallback_limiter.reset(key)

        self._execute_redis_op("reset", redis_op, fallback_op)


# Global singleton instance based on configuration
_limiter_instance: RateLimiterBase = (
    RedisRateLimiter(settings.REDIS_URL) if settings.REDIS_URL else InMemoryRateLimiter()
)

def get_rate_limiter() -> RateLimiterBase:
    """Dependency injector / accessor for rate limiter instance."""
    return _limiter_instance
