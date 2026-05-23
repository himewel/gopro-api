# Configuration

`gopro-api` uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load settings from the environment and from a `.env` file in the current working directory.

## Required settings

| Variable | Description |
|----------|-------------|
| `GP_ACCESS_TOKEN` | Your GoPro cloud access token (the value of the `gp_access_token` browser cookie). |

## `.env` file

Create a `.env` file at the root of your project (or wherever you run the CLI from):

```env
GP_ACCESS_TOKEN=your_token_here
```

!!! warning "Never commit `.env`"
    Add `.env` to your `.gitignore`. The token grants full access to your GoPro cloud account.

## Overriding the token in code

Pass the token directly when constructing a client — this takes precedence over the environment:

```python
from gopro_api.api import GoProAPI, AsyncGoProAPI

with GoProAPI(access_token="your_token_here") as api:
    ...

async with AsyncGoProAPI(access_token="your_token_here") as api:
    ...
```

## Retrieving `gp_access_token` from your browser

Sign in to [gopro.com](https://gopro.com) or [quik.gopro.com](https://quik.gopro.com). The site sets a cookie named **`gp_access_token`**.

=== "Chrome / Edge / Brave"

    1. Open the site while logged in.
    2. Press **F12** to open DevTools → **Application** tab → **Cookies** → select the origin (e.g. `https://quik.gopro.com`).
    3. Copy the **Value** of `gp_access_token`.

=== "Firefox"

    1. Press **F12** → **Storage** tab → **Cookies** → select the origin.
    2. Copy the **Value** of `gp_access_token`.

=== "Network panel (Chromium)"

    1. Open **DevTools** → **Network** tab.
    2. Trigger any request to `api.gopro.com` (e.g. browse your media library).
    3. Click on the request → **Headers** → scroll to **Request Headers** → **Cookie**.
    4. Copy the value after `gp_access_token=` up to the next `;` (or end of the string).

!!! tip "HttpOnly cookies"
    If the cookie is **HttpOnly**, the Application panel will not show its value. Use the **Network panel** method instead.

## Token expiry

Tokens expire. If you receive a **401 Unauthorized** error, return to your browser and copy a fresh token value.

## API reference

See [`gopro_api.config`](api/utils.md) for the `Settings` class that loads these values.
