"""
Module for handling the loading and saving of synced Strava activity IDs to Nextcloud.
"""

import json
import logging
import os
from typing import Set

from nextcloud import NextCloud

logger = logging.getLogger(__name__)


class SyncedActivitiesStore:
    """
    Handles loading and saving synced activity IDs from/to Nextcloud.
    """

    def __init__(self, nextcloud_url: str, username: str, password: str, target_folder: str):
        """
        Initialize the SyncedActivitiesStore.

        Args:
            nextcloud_url (str): The Nextcloud server URL.
            username (str): Nextcloud username.
            password (str): Nextcloud password.
            target_folder (str): Remote folder in Nextcloud to use for sync.
        """
        self.nextcloud_url = nextcloud_url
        self.username = username
        self.password = password
        self.target_folder = target_folder
        self.remote_path = f"{self.target_folder}/synced_activities.json"
        self.local_temp = "synced_activities.json"

    def load(self) -> Set[str]:
        """
        Load the set of synced activity IDs from Nextcloud.

        Returns:
            Set[str]: Set of synced Strava activity IDs.
        """
        try:
            nc = NextCloud(
                endpoint=self.nextcloud_url,
                user=self.username,
                password=self.password,
            )
            file_obj = nc.get_file(self.remote_path)
            content = file_obj.fetch_file_content()
            return set(json.loads(content))
        except Exception as e:
            logger.info(f"No remote synced_activities.json found in Nextcloud ({e}), starting fresh.")
            return set()

    def save(self, synced_ids: Set[str]):
        """
        Save the set of synced activity IDs to Nextcloud.

        Args:
            synced_ids (Set[str]): Set of synced Strava activity IDs to save.
        """
        try:
            with open(self.local_temp, "w") as f:
                json.dump(list(synced_ids), f)
            nc = NextCloud(
                endpoint=self.nextcloud_url,
                user=self.username,
                password=self.password,
            )
            nc.upload_file(self.local_temp, self.remote_path)
            logger.info(f"Uploaded synced_activities.json to Nextcloud: {self.remote_path}")
        except Exception as e:
            logger.error(f"Failed to upload synced_activities.json to Nextcloud: {e}")
        finally:
            try:
                if os.path.exists(self.local_temp):
                    os.remove(self.local_temp)
            except Exception:
                pass
