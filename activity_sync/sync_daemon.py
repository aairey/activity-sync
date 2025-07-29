"""
Daemon service for running Strava-to-Nextcloud sync with signal handling and periodic execution.
"""

import asyncio
import logging
import os
import signal

from .config import SyncConfig
from .syncer import StravaNextcloudSync

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
    Main async function to run the sync service.
    """
    # Set up signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    config = SyncConfig()
    syncer = StravaNextcloudSync(config)

    while RUNNING:
        try:
            await syncer.sync_activities()
        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)

        if RUNNING:  # Don't sleep if we're shutting down
            sleep_time = get_sleep_interval()
            logger.info(f"Waiting {sleep_time} seconds until next sync...")
            await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error in sync service: {e}", exc_info=True)
        raise
