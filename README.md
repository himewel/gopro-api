# gopro

Small Python client for the **GoPro cloud / Quik** media API (`api.gopro.com`): search your library and fetch download metadata, using **async I/O** (`aiohttp`) and **Pydantic** models.

This is an unofficial project; it is not affiliated with GoPro.

## Requirements

- Python 3.10+
- A valid **GoPro access token** (see [Configuration](#configuration))

## Install

From the repository root (editable install for development):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

Or install from a built wheel once you have one:

```bash
pip install ./dist/gopro-0.1.0-py3-none-any.whl
```

## Configuration

The client reads `GP_ACCESS_TOKEN` from the environment (after loading `.env` if present).

Create a `.env` file in the project root:

```env
GP_ACCESS_TOKEN=your_token_here
```

The HTTP client sends it as a cookie: `gp_access_token=<value>`.

Put **only the token string** in `GP_ACCESS_TOKEN` (not the `gp_access_token=` prefix).

### Retrieving `gp_access_token` from your browser

You need an active session in the GoPro web experience (e.g. [Quik / GoPro web](https://gopro.com) — sign in and open your media library). The site stores the API token in a cookie named **`gp_access_token`**.

**Chrome / Edge / Brave**

1. Open the GoPro site while logged in (same browser profile you use for the cloud library).
2. Press **F12** (or **Ctrl+Shift+I** / **Cmd+Option+I**) to open DevTools.
3. Open the **Application** tab → **Storage** → **Cookies** → select the site origin (often `https://quik.gopro.com` or another `*.gopro.com` host).
4. Find the row **`gp_access_token`**, copy the **Value** column only.

**Firefox**

1. Open DevTools (**F12**) → **Storage** tab → **Cookies** → pick the relevant `gopro.com` origin.
2. Copy the value of **`gp_access_token`**.

**Using the Network panel (any Chromium-based browser)**

1. DevTools → **Network** tab; enable **Preserve log** if useful.
2. Reload or navigate in the library so requests to **`api.gopro.com`** appear.
3. Click a request to `api.gopro.com` → **Headers** → **Request Headers** → **Cookie**.
4. Locate `gp_access_token=...` in that string and copy everything **after** the first `=` up to the next `;` (or end of string).  
   - If the value is long or URL-encoded, copy carefully so you do not include a trailing semicolon or another cookie name.

**Notes**

- Cookies are **HttpOnly** on some setups; if you do not see `gp_access_token` in Application/Storage, use the **Network** method on a request that already hit `api.gopro.com`.
- Tokens **expire**; if API calls start failing with 401, sign in again and repeat the steps above.
- Treat the value like a password.

**Security:** Do not commit `.env` or real tokens. The repo’s `.gitignore` should exclude `.env`.

## Usage

Always use `GoProAPI` as an **async context manager** so the underlying `aiohttp` session is opened and closed correctly.

```python
import asyncio
from datetime import datetime

from gopro.api.gopro import GoProAPI
from gopro.api.models import CapturedRange, GoProMediaSearchParams


async def main() -> None:
    params = GoProMediaSearchParams(
        captured_range=CapturedRange(
            start=datetime.fromisoformat("2026-03-01"),
            end=datetime.fromisoformat("2026-03-02"),
        ),
        per_page=50,
        page=1,
    )

    async with GoProAPI() as api:
        search = await api.search(params)
        for item in search.embedded.media:
            meta = await api.download(item.id)
            print(meta.filename, len(meta.embedded.files), "files")


if __name__ == "__main__":
    asyncio.run(main())
```

### Models

- **Requests:** `GoProMediaSearchParams`, `CapturedRange`, and related defaults live in `gopro.api.models`.
- **Responses:** Parsed JSON types (search hits, download URLs, pagination) are defined in the same module.

Search query parameters use Python lists where the API expects comma-separated strings; serialization is handled when calling `model_dump()`.

## Project layout

| Path | Role |
|------|------|
| `gopro/api/gopro.py` | `GoProAPI` — `search`, `download` |
| `gopro/api/models.py` | Pydantic request/response models |
| `gopro/config.py` | `load_dotenv`, `GP_ACCESS_TOKEN` |
| `setup.py` | Package metadata and dependencies |

## License

This project is licensed under the [MIT License](LICENSE).

GoPro, Quik, and related marks are trademarks of their respective owners. This software is not affiliated with or endorsed by GoPro.
