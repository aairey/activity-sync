"""
Client for interacting with the Strava API and exporting activities to GPX format.
"""

import logging
import time
from datetime import datetime, timedelta

import aiofiles
import aiohttp


class strava2gpx:
    """
    A client for interacting with the Strava API and exporting activities to GPX files.
    """

    def __init__(self, client_id, client_secret, refresh_token):
        """
        Initialize the strava2gpx client.

        Args:
            client_id (str): Strava API client ID.
            client_secret (str): Strava API client secret.
            refresh_token (str): Strava API refresh token.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.activities_list = None
        self.streams = {
            "latlng": 1,
            "altitude": 1,
            "heartrate": 0,
            "cadence": 0,
            "watts": 0,
            "temp": 0,
        }

    async def connect(self):
        """
        Connect to Strava by refreshing and setting the access token.
        """
        self.access_token = await self.refresh_access_token()

    async def get_activities_list(self):
        """
        Retrieve the list of all activities for the authenticated user.

        Returns:
            list: A list of activities, each as a dictionary.
        """
        activities = await self.get_strava_activities(1)
        masterlist = [
            [activity["name"], activity["id"], activity["start_date"], activity["type"]] for activity in activities
        ]
        print("Received " + str(len(masterlist)) + " activities")
        page = 1
        while len(activities) != 0:
            page += 1
            activities = await self.get_strava_activities(page)
            masterlist.extend(
                [
                    [
                        activity["name"],
                        activity["id"],
                        activity["start_date"],
                        activity["type"],
                    ]
                    for activity in activities
                ]
            )
            print("Received " + str(len(masterlist)) + " activities")
        self.activities_list = masterlist
        return masterlist

    async def refresh_access_token(self):
        """
        Refresh the Strava API access token using the refresh token.

        Returns:
            str: The new access token.
        """
        token_endpoint = "https://www.strava.com/api/v3/oauth/token"
        form_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(token_endpoint, data=form_data) as response:
                    if response.status != 200:
                        if response.status == 401:
                            raise Exception("401 Unauthorized: Check Client ID, Client Secret, and Refresh Token")
                        else:
                            raise Exception("Failed to refresh access token")
                    data = await response.json()
                    self.access_token = data["access_token"]
                    return self.access_token
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error("Error refreshing access token: %s", str(e))
                raise

    async def _handle_rate_limit(self, response):
        """
        Handle rate limiting by waiting until the next day if the global rate limit is reached.

        Args:
            response: The aiohttp response object

        Returns:
            bool: True if rate limit was handled and we should retry, False otherwise
        """
        if response.status == 429:  # Too Many Requests
            reset_time = response.headers.get("X-RateLimit-Reset")
            if reset_time:
                reset_timestamp = int(reset_time)
                now = datetime.utcnow().timestamp()
                wait_seconds = max(0, reset_timestamp - now) + 10  # Add 10s buffer

                logger = logging.getLogger(__name__)
                logger.warning(
                    "Rate limit reached. " f"Waiting until {datetime.fromtimestamp(reset_timestamp)} to retry..."
                )

                # Wait until the reset time
                time.sleep(wait_seconds)
                return True
        return False

    async def _make_request(self, method, url, **kwargs):
        """
        Make an HTTP request with rate limit handling.

        Args:
            method: HTTP method (get, post, etc.)
            url: URL to request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the request
        """
        logger = logging.getLogger(__name__)

        while True:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()

                    # Handle rate limiting
                    if await self._handle_rate_limit(response):
                        continue

                    # For other errors, log and raise
                    text = await response.text()
                    logger.error(f"Request failed: {method} {url} - HTTP {response.status}\nResponse: {text}")
                    response.raise_for_status()

    async def get_strava_activities(self, page):
        """
        Retrieve a page of Strava activities.

        Args:
            page (int): The page number to fetch.

        Returns:
            list: A list of activities for the page.
        """
        base_url = "https://www.strava.com/api/v3/athlete/activities"
        params = f"per_page=200&page={page}"
        url = f"{base_url}?{params}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return await self._make_request("get", url, headers=headers)

    async def get_data_stream(self, activity_id):
        """
        Fetch the data stream for a given activity.

        Args:
            activity_id (int): The Strava activity ID.

        Returns:
            dict: The data stream for the activity.
        """
        api_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        query_params = "time"
        for key, value in self.streams.items():
            if value == 1:
                query_params += f",{key}"
        url = f"{api_url}?keys={query_params}&key_by_type=true"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return await self._make_request("get", url, headers=headers)

    async def get_strava_activity(self, activity_id):
        """
        Fetch the details of a single Strava activity.

        Args:
            activity_id (int): The Strava activity ID.

        Returns:
            dict: The activity details.
        """
        api_url = "https://www.strava.com/api/v3/activities/"
        url = f"{api_url}{activity_id}?include_all_efforts=false"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return await self._make_request("get", url, headers=headers)

    async def detect_activity_streams(self, activity):
        """
        Detect which data streams are available for the given activity and update the streams configuration.

        Args:
            activity (dict): The Strava activity data.
        """
        if activity.get("device_watts", False):
            self.streams["watts"] = 1
        else:
            self.streams["watts"] = 0
        if activity["has_heartrate"] is True:
            self.streams["heartrate"] = 1
        else:
            self.streams["heartrate"] = 0
        if "average_cadence" in activity:
            self.streams["cadence"] = 1
        else:
            self.streams["cadence"] = 0
        if "average_temp" in activity:
            self.streams["temp"] = 1
        else:
            self.streams["temp"] = 0

        # get sport_type from detailedActivity
        self.sport_type = activity["sport_type"]

    async def add_seconds_to_timestamp(self, start_timestamp, seconds):
        """
        Add seconds to an ISO8601 timestamp and return the new timestamp.

        Args:
            start_timestamp (str): The starting ISO8601 timestamp.
            seconds (int): Number of seconds to add.

        Returns:
            str: The new ISO8601 timestamp.
        """
        from datetime import datetime

        start_time = datetime.fromisoformat(start_timestamp)
        new_time = start_time + timedelta(seconds=seconds)
        return (new_time.isoformat() + "Z").replace("+00:00", "")

    async def write_to_gpx(self, activity_id, output="build"):
        """
        Write the specified activity to a GPX file.

        Args:
            activity_id (int): The Strava activity ID.
            output (str, optional): The output file prefix. Defaults to "build".
        """
        activity = await self.get_strava_activity(activity_id)
        # Define XML namespaces and schema locations
        schema_parts = [
            "http://www.topografix.com/GPX/1.1",
            "http://www.topografix.com/GPX/1.1/gpx.xsd",
            "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
            "http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd",
            "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
            "http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd",
        ]
        schema_location = " ".join(schema_parts)

        # Build the GPX header
        gpx_header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<gpx "
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xsi:schemaLocation="{schema_location}" '
            'creator="StravaGPX" version="1.1" '
            'xmlns="http://www.topografix.com/GPX/1.1" '
            'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" '
            'xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3">\n'
            "  <metadata>\n"
            f'    <time>{activity["start_date"]}</time>\n'
            "  </metadata>\n"
            "  <trk>\n"
            f'    <name>{activity["name"]}</name>\n'
            f'    <type>{activity["type"]}</type>\n'
            f'    <desc>{activity["sport_type"]}</desc>\n'
            f'    <link>https://www.strava.com/activities/{activity["id"]}</link>\n'
            "    <trkseg>"
        )

        # GPX footer
        gpx_footer = "    </trkseg>\n  </trk>\n</gpx>"

        # Combine header and footer for the final GPX content
        gpx_content = gpx_header + gpx_footer

        try:
            async with aiofiles.open(f"{output}.gpx", "w") as f:
                await f.write(gpx_content)

            await self.detect_activity_streams(activity)
            data_streams = await self.get_data_stream(activity_id)

            if data_streams["latlng"]["original_size"] != data_streams["time"]["original_size"]:
                print("Error: latlng and time streams have different sizes")
                return

            trkpts = []
            for i in range(data_streams["time"]["original_size"]):
                time = await self.add_seconds_to_timestamp(activity["start_date"], data_streams["time"]["data"][i])

                lat = float(data_streams["latlng"]["data"][i][0])
                lon = float(data_streams["latlng"]["data"][i][1])
                ele = float(data_streams["altitude"]["data"][i])

                trkpt = [
                    f'\n   <trkpt lat="{lat:.7f}" lon="{lon:.7f}">',
                    f"    <ele>{ele:.1f}</ele>",
                    f"    <time>{time}</time>",
                    "    <extensions>",
                    "     <gpxtpx:TrackPointExtension>",
                ]

                if self.streams["temp"] == 1:
                    temp = data_streams["temp"]["data"][i]
                    trkpt.append(f"      <gpxtpx:atemp>{temp}</gpxtpx:atemp>")

                if self.streams["watts"] == 1:
                    watts = data_streams["watts"]["data"][i]
                    trkpt.append(f"      <gpxtpx:watts>{watts}</gpxtpx:watts>")

                if self.streams["heartrate"] == 1:
                    hr = data_streams["heartrate"]["data"][i]
                    trkpt.append(f"      <gpxtpx:hr>{hr}</gpxtpx:hr>")

                if self.streams["cadence"] == 1:
                    cad = data_streams["cadence"]["data"][i]
                    trkpt.append(f"      <gpxtpx:cad>{cad}</gpxtpx:cad>")

                trkpt.extend(["     </gpxtpx:TrackPointExtension>", "    </extensions>", "   </trkpt>"])

                trkpts.append("\n".join(trkpt))

            async with aiofiles.open(f"{output}.gpx", "a") as f:
                await f.write("".join(trkpts))
                await f.write(gpx_footer)

            print("GPX file saved successfully.")

        except Exception as err:
            print(f"Error writing GPX file: {str(err)}")
