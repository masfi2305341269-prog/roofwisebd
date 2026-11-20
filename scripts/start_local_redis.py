"""
RoofwiseBD — Local Redis Server Runner
Starts a lightweight standalone Redis server listening on 127.0.0.1:6379.
Uses standard RESP protocol. Enables multi-worker rate limiting in local environments.

Usage:
    python scripts/start_local_redis.py
"""
import sys
import time
import logging

try:
    from fakeredis import TcpFakeServer
except ImportError:
    print("[ERROR] 'fakeredis' is required. Run: pip install fakeredis")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RoofwiseLocalRedis")

def main():
    host = "127.0.0.1"
    port = 6379
    print("=" * 65)
    print(f"☀️  RoofwiseBD — Local Redis Server")
    print(f"   Listening on: redis://{host}:{port}/0")
    print(f"   Supports multi-worker rate limiting and session synchronization")
    print("   Press Ctrl+C to stop.")
    print("=" * 65)

    server = TcpFakeServer((host, port), server_type="redis")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping local Redis server...")
    finally:
        server.server_close()
        logger.info("Local Redis server stopped.")

if __name__ == "__main__":
    main()
