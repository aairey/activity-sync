"""
Main service loop for running Strava-to-Nextcloud sync as a daemon/service.
Handles signal-based shutdown, error backoff, and periodic sync.
"""

import asyncio
import logging
import os
import signal

from activity_sync.config import SyncConfig
from activity_sync.syncer import StravaNextcloudSync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

RUNNING = True


def handle_shutdown(signum, frame):
    """
    Signal handler for graceful shutdown of the sync service.

    Args:
        signum (int): Signal number.
        frame: Current stack frame (unused).
    """
    global RUNNING
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    RUNNING = False


def get_sleep_interval():
    """
    Get the sleep interval (in seconds) between sync runs from the environment.

    Returns:
        int: Sleep interval in seconds.
    """
    try:
        return int(os.getenv("SYNC_INTERVAL_SECONDS", "600"))
    except Exception:
        return 600


async def main():
    """
    Main async loop for the Strava-to-Nextcloud sync service.
    Handles periodic sync, error backoff, and graceful shutdown.
    """
    global RUNNING
    sleep_interval = get_sleep_interval()
    backoff = 900  # Start with 15 min on error
    max_backoff = 3600  # Max 1 hour
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    while RUNNING:
        try:
            logger.info("Starting Strava-to-Nextcloud sync...")
            config = SyncConfig()
            syncer = StravaNextcloudSync(config)
            if hasattr(syncer, "run") and asyncio.iscoroutinefunction(syncer.run):
                await syncer.run()
            else:
                await asyncio.to_thread(syncer.run)
            logger.info(f"Sync finished. Sleeping for {sleep_interval} seconds before next run.")
            for _ in range(sleep_interval):
                if not RUNNING:
                    break
                await asyncio.sleep(1)
            backoff = 900  # Reset backoff after success
        except Exception as e:
            logger.error(f"Fatal error in sync loop: {e}")
            logger.info(f"Sleeping for {backoff} seconds before retrying after fatal error.")
            for _ in range(backoff):
                if not RUNNING:
                    break
                await asyncio.sleep(1)
            backoff = min(backoff * 2, max_backoff)
    logger.info("Sync service exited.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Service terminated unexpectedly: {e}")
