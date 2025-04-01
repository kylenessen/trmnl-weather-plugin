# TRMNL Weather Plugin Project Strategy

## Goal

To display real-time weather data from a personal WeatherFlow Tempest weather station on a TRMNL display using a custom Private Plugin.

## Data Source

-   **Weather Data:** WeatherFlow Tempest API (REST)
-   **Authentication:** WeatherFlow Personal Access Token
-   **Endpoint:** `GET /swd/rest/observations/station/{station_id}` - Provides the latest observation data, including temperature, wind, humidity, pressure, UV index, rain accumulation, etc.

## TRMNL Plugin Type

-   **Private Plugin:** Managed within the user's TRMNL account.
-   **Strategy:** Polling

## Intermediate Data Handling (GitHub Actions + Pages)

To bridge the gap between the authenticated WeatherFlow API and the TRMNL Polling URL requirement, and to avoid cluttering the main git history, the following approach will be used:

1.  **GitHub Repository:** The project code, including the fetch script, workflow, and HTML template, resides in the `trmnl-weather-plugin` GitHub repository.
2.  **Fetch Script (`fetch_weather.py`):**
    *   A Python script within the repository.
    *   Uses the WeatherFlow Personal Access Token (stored securely as a GitHub Secret named `WF_TOKEN`) and the user's `station_id`.
    *   Makes a request to the WeatherFlow API endpoint.
    *   Parses the response, extracts relevant weather metrics, performs necessary unit conversions (e.g., C to F, m/s to mph).
    *   Writes the processed data into a simple JSON file (`weather_data.json`).
3.  **GitHub Action Workflow (`.github/workflows/fetch_weather.yml`):**
    *   Runs automatically on a schedule (e.g., every 15 minutes).
    *   Sets up Python environment and installs dependencies (`requests`).
    *   Executes the `fetch_weather.py` script, passing the `WF_TOKEN` secret as an environment variable.
    *   Takes the generated `weather_data.json` file.
    *   Deploys this single file to GitHub Pages associated with the repository. This overwrites the previous version of the file on the Pages site without creating new commits in the repository branches.
4.  **GitHub Pages:**
    *   Enabled for the repository.
    *   Serves the `weather_data.json` file at a stable public URL (e.g., `https://<username>.github.io/<repo-name>/weather_data.json`). This URL will be used as the TRMNL Polling URL.

## TRMNL Display Template

-   **File:** `trmnl_template.html`
-   **Content:**
    *   Standard HTML structure.
    *   Includes TRMNL's CSS (`plugins.css`) and JS (`plugins.js`) for styling and functionality.
    *   Uses Liquid templating syntax (e.g., `{{ temperature_f }}`, `{{ wind_speed_mph }}`) to dynamically insert the weather data fetched from `weather_data.json`.
    *   Layout designed to present the key weather metrics clearly on the 800x480 display (e.g., using TRMNL's grid system or custom CSS).

## Setup and Configuration Summary

1.  User generates a WeatherFlow Personal Access Token.
2.  User adds the token as a GitHub Secret (`WF_TOKEN`) to the repository.
3.  User enables GitHub Pages for the repository, configured to deploy via the GitHub Action.
4.  User creates a Private Plugin in TRMNL:
    *   Sets Strategy to "Polling".
    *   Sets Polling URL to the GitHub Pages URL of `weather_data.json`.
    *   Pastes the content of `trmnl_template.html` into the Markup field.
    *   Sets the desired polling interval.
5.  User adds the configured plugin instance to a TRMNL playlist.

This strategy leverages GitHub Actions and Pages to provide a serverless, automated way to fetch and serve the weather data for the TRMNL plugin without requiring external hosting or polluting the git history.
