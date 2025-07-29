# Activity Sync

A tool to synchronize your Strava activities' GPX data with your Nextcloud file server.

## Prerequisites

- Python 3.7+
- Strava API credentials
- Nextcloud server access

## Installation

1. Install dependencies using [uv](https://github.com/astral-sh/uv):
```bash
uv pip install -r pyproject.toml
```

2. Create a `.env` file in the same directory as the script and add your credentials:
```
STRAVA_CLIENT_ID=your_client_id
STRAVA_REFRESH_TOKEN=your_refresh_token
STRAVA_CLIENT_SECRET=your_client_secret
NEXTCLOUD_URL=https://your.nextcloud.server
NEXTCLOUD_USERNAME=your_username
NEXTCLOUD_PASSWORD=your_password
NEXTCLOUD_TARGET_FOLDER=/GPX/Strava  # Optional, defaults to /GPX/Strava
```

## Usage

### Running as a Docker Container (Continuous Sync)

1. **Copy `.env.example` to `.env` and fill in your Strava/Nextcloud credentials:**

   ```sh
   cp .env.example .env
   # Edit .env with your secrets
   ```

2. **Build the Docker image:**

   ```sh
   docker build -t strava-nextcloud-sync .
   ```

3. **Run the container (mount your .env file):**

   ```sh
   docker run --env-file .env \
     -v $(pwd)/logs:/app/logs \
     --name strava-nextcloud-sync \
     --restart unless-stopped \
     strava-nextcloud-sync
   ```

- The service will run continuously, syncing every 10 minutes and automatically handling Strava rate limits.

- All logs will be output to the console and can be persisted by mounting a `logs` directory.
- **No need to mount or persist `synced_activities.json` locally!** The script now stores and loads `synced_activities.json` directly from your Nextcloud target folder. This enables persistent incremental syncing even in a stateless Docker container.


Run the script:
```bash
python -m activity_sync_service
```

The script will:
1. Authenticate with Strava using your credentials
2. Download GPX data for new (not-yet-synced) activities
3. Upload the GPX files to your specified Nextcloud folder
4. Track synced activities in `synced_activities.json` (automatically stored in your Nextcloud folder)

## Notes

- GPX files are named using the activity date and name
- The script uses async operations for better performance
- Error handling is implemented to skip problematic activities
- Already-synced activities are skipped on future runs (incremental sync)
- **The Strava `sport_type` is recorded in the `<desc>` field in each generated GPX file.**
- **To reset incremental syncing, delete `synced_activities.json` from your Nextcloud target folder using the Nextcloud web UI or client.**
- You can schedule this script externally (e.g., with cron or a scheduler) for automated weekly/monthly syncs

## Inspiration

This project was inspired by the following projects:

* [Strava2Gpx](https://github.com/Jime567/strava2gpx)
* [RunGap](https://www.rungap.com)
