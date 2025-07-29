"""
Client for interacting with Nextcloud for file operations related to Strava activity sync.
"""

import json
import logging
import os
from typing import Set

from nextcloud import NextCloud

logger = logging.getLogger(__name__)


class NextcloudClient:
    """
    Handles file operations with Nextcloud for syncing Strava activities and backoff state.
    """

    BACKOFF_FILENAME = "activity_sync_backoff.json"

    def __init__(self, url: str, username: str, password: str, target_folder: str):
        """
        Initialize the Nextcloud client for file operations.

        Args:
            url (str): Nextcloud server URL.
            username (str): Nextcloud username.
            password (str): Nextcloud password.
            target_folder (str): Remote folder in Nextcloud to use for sync.
        """
        self.url = url
        self.username = username
        self.password = password
        self.target_folder = target_folder
        self.remote_state_path = f"{self.target_folder}/synced_activities.json"
        self.local_temp = "synced_activities.json"
        self.nc = NextCloud(
            endpoint=self.url,
            user=self.username,
            password=self.password,
            json_output=True,
        )

    def load_synced_ids(self) -> Set[str]:
        """
        Load the set of synced Strava activity IDs from Nextcloud.

        Returns:
            Set[str]: Set of activity IDs already synced.
        """
        try:
            file_obj = self.nc.get_file(self.remote_state_path)
            content = file_obj.fetch_file_content()
            return set(json.loads(content))
        except Exception as e:
            logger.info(f"No remote synced_activities.json found in Nextcloud ({e}), starting fresh.")
            return set()

    def save_synced_ids(self, synced_ids: Set[str]):
        """
        Save the set of synced Strava activity IDs to Nextcloud.

        Args:
            synced_ids (Set[str]): Set of activity IDs to save.
        """
        try:
            with open(self.local_temp, "w") as f:
                json.dump(list(synced_ids), f)
            self.nc.upload_file(self.local_temp, self.remote_state_path)
            logger.info(f"Uploaded synced_activities.json to Nextcloud: {self.remote_state_path}")
        except Exception as e:
            logger.error(f"Failed to upload synced_activities.json to Nextcloud: {e}")
        finally:
            try:
                if os.path.exists(self.local_temp):
                    os.remove(self.local_temp)
            except Exception:
                pass

    def save_backoff_until(self, dt_utc):
        """
        Persist the next allowed sync time (UTC ISO8601) to Nextcloud.

        Args:
            dt_utc (datetime): The UTC datetime until which syncing is backed off.
        """
        import tempfile

        data = {"backoff_until_utc": dt_utc.isoformat()}
        local_temp = None
        try:
            with tempfile.NamedTemporaryFile("w", delete=False) as tf:
                json.dump(data, tf)
                local_temp = tf.name
            remote_path = f"{self.target_folder}/{self.BACKOFF_FILENAME}"
            self.nc.upload_file(local_temp, remote_path)
            logger.info(f"Uploaded backoff file to Nextcloud: {remote_path}")
        except Exception as e:
            logger.error(f"Failed to upload backoff file to Nextcloud: {e}")
        finally:
            if local_temp and os.path.exists(local_temp):
                try:
                    os.remove(local_temp)
                except Exception:
                    pass

    def load_backoff_until(self):
        """
        Load backoff-until UTC datetime from Nextcloud.

        Returns:
            datetime or None: The UTC datetime until which syncing is backed off, or None if not set.
        """
        from datetime import datetime, timezone

        remote_path = f"{self.target_folder}/{self.BACKOFF_FILENAME}"
        try:
            file_obj = self.nc.get_file(remote_path)
            content = file_obj.fetch_file_content()
            dt_str = json.loads(content)["backoff_until_utc"]
            return datetime.fromisoformat(dt_str).astimezone(timezone.utc)
        except Exception as e:
            logger.info(f"No remote backoff file found in Nextcloud ({e}), proceeding.")
            return None

    def upload_gpx(self, local_path: str, remote_filename: str):
        """
        Upload a GPX file to Nextcloud.

        Args:
            local_path (str): Local path to the GPX file.
            remote_filename (str): Filename to use in Nextcloud.
        """
        remote_path = f"{self.target_folder}/{remote_filename}"
        try:
            self.nc.upload_file(local_path, remote_path)
            logger.info(f"Uploaded GPX file to Nextcloud: {remote_path}")
        except Exception as e:
            logger.error(f"Failed to upload GPX file to Nextcloud: {e}")
