"""
Client wrapper for Strava API interactions, using strava2gpx for activity export.
"""

import logging
from typing import Any, List

from activity_sync.strava2gpx.client import strava2gpx

logger = logging.getLogger(__name__)


class StravaClient:
    """
    Wrapper client for interacting with Strava using strava2gpx.
    """

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """
        Initialize StravaClient.

        Args:
            client_id (str): Strava API client ID.
            client_secret (str): Strava API client secret.
            refresh_token (str): Strava API refresh token.
        """
        self.api = strava2gpx(client_id, client_secret, refresh_token)

    async def connect(self):
        """
        Connect to Strava by refreshing the access token.
        """
        await self.api.connect()

    async def get_activities_list(self) -> List[Any]:
        """
        Retrieve the list of all activities for the authenticated user.

        Returns:
            List[Any]: List of Strava activities.
        """
        return await self.api.get_activities_list()

    async def write_activity_to_gpx(self, activity_id: int, output: str = "build"):
        """
        Export a Strava activity to a GPX file.

        Args:
            activity_id (int): The Strava activity ID.
            output (str, optional): Output file prefix. Defaults to "build".
        """
        await self.api.write_to_gpx(activity_id, output)
