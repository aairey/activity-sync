"""
Configuration module for Strava-to-Nextcloud sync service.
Loads environment variables and provides a configuration class.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class SyncConfig:
    """
    Holds configuration values loaded from environment variables for Strava and Nextcloud.
    """

    def __init__(self):
        """
        Initialize SyncConfig by loading environment variables.
        """
        self.strava_client_id = os.getenv("STRAVA_CLIENT_ID")
        self.strava_refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
        self.strava_client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        self.nextcloud_url = os.getenv("NEXTCLOUD_URL")
        self.nextcloud_username = os.getenv("NEXTCLOUD_USERNAME")
        self.nextcloud_password = os.getenv("NEXTCLOUD_PASSWORD")
        self.nextcloud_target_folder = os.getenv("NEXTCLOUD_TARGET_FOLDER", "/GPX/Strava")
        self.sync_interval_seconds = int(os.getenv("SYNC_INTERVAL_SECONDS", "600"))

    def strava_ready(self) -> bool:
        """
        Check if Strava credentials are configured.

        Returns:
            bool: True if all Strava credentials are present, False otherwise.
        """
        return all(
            [
                self.strava_client_id,
                self.strava_refresh_token,
                self.strava_client_secret,
            ]
        )
