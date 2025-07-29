"""
Test for exporting a single Strava activity to GPX using the StravaClient.
"""

import os

import pytest
from dotenv import load_dotenv

from activity_sync.config import SyncConfig
from activity_sync.strava_client import StravaClient

load_dotenv()


@pytest.mark.asyncio
async def test_single_activity_gpx():
    """
    Test that a single Strava activity can be exported to GPX and the file is created.
    """
    config = SyncConfig()
    strava = StravaClient(
        config.strava_client_id,
        config.strava_client_secret,
        config.strava_refresh_token,
    )
    await strava.connect()
    activities = await strava.get_activities_list()
    assert activities, "No activities found for Strava account."
    name, activity_id, start_date, activity_type = activities[0]
    await strava.write_activity_to_gpx(activity_id, "test_gpx")
    gpx_filename = f"test_gpx_{activity_id}.gpx"
    if not os.path.exists(gpx_filename):
        gpx_filename = "test_gpx.gpx"
    try:
        assert os.path.exists(gpx_filename), f"GPX file not created: {gpx_filename}"
    finally:
        if os.path.exists(gpx_filename):
            print("GPX file created: " + gpx_filename)
            os.remove(gpx_filename)
