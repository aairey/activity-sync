"""
Module for synchronizing Strava activities with Nextcloud, handling rate limits and backoff.
"""

import asyncio
import logging
import os

from .config import SyncConfig
from .nextcloud_client import NextcloudClient
from .strava_client import StravaClient

logger = logging.getLogger(__name__)


class StravaNextcloudSync:
    """
    Orchestrates the synchronization of Strava activities to Nextcloud, including rate limiting and backoff.
    """

    def __init__(self, config: SyncConfig):
        """
        Initialize the StravaNextcloudSync object.

        Args:
            config (SyncConfig): The configuration object with credentials and settings.
        """
        self.config = config
        self.strava = StravaClient(
            config.strava_client_id,
            config.strava_client_secret,
            config.strava_refresh_token,
        )
        self.nextcloud = NextcloudClient(
            config.nextcloud_url,
            config.nextcloud_username,
            config.nextcloud_password,
            config.nextcloud_target_folder,
        )
        self.synced_ids = self.nextcloud.load_synced_ids()

    async def sync_activities(self):
        """
        Synchronize new Strava activities to Nextcloud, handling API rate limits and persistent backoff.
        """
        if not self.config.strava_ready():
            raise ValueError("Strava credentials not properly configured")
        # Persistent backoff check
        from datetime import datetime, timedelta, timezone

        backoff_until = self.nextcloud.load_backoff_until()
        now = datetime.now(timezone.utc)
        if backoff_until and now < backoff_until:
            sleep_seconds = (backoff_until - now).total_seconds()
            logger.warning(
                "Persistent backoff in effect. "
                f"Sleeping for {int(sleep_seconds)} seconds until {backoff_until.isoformat()}."
            )
            await asyncio.sleep(sleep_seconds)
        await self.strava.connect()
        logger.info("Connected to Strava. Fetching activities list...")
        activities_list = await self.strava.get_activities_list()
        logger.info(f"Found {len(activities_list)} activities.")
        new_activities = [a for a in activities_list if str(a[1]) not in self.synced_ids]
        logger.info(f"Found {len(new_activities)} new activities to sync.")
        RATE_LIMIT = 100
        SLEEP_SECONDS = 15 * 60
        daily_count = 0
        batch_count = 0
        for idx, (name, activity_id, start_date, activity_type) in enumerate(new_activities):
            if batch_count >= RATE_LIMIT:
                logger.warning("[Rate Limit] Hit 100 requests. Sleeping for 15 minutes to respect Strava API limits...")
                await asyncio.sleep(SLEEP_SECONDS)
                batch_count = 0
            if daily_count >= 1000:
                logger.warning("[Rate Limit] Hit 1000 daily requests. Sleeping until next UTC day.")
                from datetime import datetime, timedelta, timezone

                now = datetime.now(timezone.utc)
                next_utc_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                self.nextcloud.save_backoff_until(next_utc_day)
                sleep_seconds = (next_utc_day - now).total_seconds()
                logger.info(f"Sleeping for {int(sleep_seconds)} seconds until next UTC midnight.")
                await asyncio.sleep(sleep_seconds)
                return
            while True:
                try:
                    logger.info(
                        f"Downloading GPX for activity {activity_id} ({name}) [{idx+1}/{len(new_activities)}] ..."
                    )
                    await self.strava.write_activity_to_gpx(activity_id, "temp_gpx")
                    gpx_filename = f"temp_gpx_{activity_id}.gpx"
                    if not os.path.exists(gpx_filename):
                        gpx_filename = "temp_gpx.gpx"
                    activity_date = start_date[:10]
                    safe_name = name.replace(" ", "_").replace("/", "-")
                    remote_filename = f"{activity_date}_{safe_name}.gpx"
                    self.nextcloud.upload_gpx(gpx_filename, remote_filename)
                    logger.info(f"Successfully uploaded: {remote_filename}")
                    self.synced_ids.add(str(activity_id))
                    self.nextcloud.save_synced_ids(self.synced_ids)
                    os.remove(gpx_filename)
                    batch_count += 1
                    daily_count += 1
                    break
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "Rate Limit Exceeded" in err_msg:
                        logger.warning("[Rate Limit] HTTP 429 detected. Sleeping for 15 minutes before retrying...")
                        await asyncio.sleep(SLEEP_SECONDS)
                        logger.info("[Rate Limit] Resuming after sleep.")
                        continue
                    logger.error(f"Error processing activity {activity_id}: {err_msg}")
                    break

    def run(self):
        """
        Run the synchronization process using asyncio.
        """
        asyncio.run(self.sync_activities())


if __name__ == "__main__":
    config = SyncConfig()
    syncer = StravaNextcloudSync(config)
    syncer.run()
