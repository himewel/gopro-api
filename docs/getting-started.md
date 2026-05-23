# Getting Started

This page walks you through installing **gopro-api**, setting up your access token, and making your first search request.

## Prerequisites

- Python **3.10** or newer
- A GoPro / Quik account with media in the cloud
- Your `gp_access_token` browser cookie (see [Configuration](configuration.md))

## Installation

### From PyPI

```bash
pip install gopro-api
```

### From source

```bash
git clone https://github.com/himewel/gopro-api.git
cd gopro-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### From a local wheel

```bash
pip install ./dist/gopro_api-*-py3-none-any.whl
```

## Set up your token

Create a `.env` file in your working directory:

```env
GP_ACCESS_TOKEN=your_token_here
```

The library loads it automatically via **pydantic-settings**. See [Configuration](configuration.md) for how to retrieve the token from your browser.

## Quick start — CLI

After installing, `gopro-api` is available on your `PATH`:

```bash
# List media captured on a specific day
gopro-api search --start 2026-03-01 --end 2026-03-02

# Show download metadata for a single media item
gopro-api info MEDIA_ID

# Download a video at the closest resolution to 1080 p
gopro-api pull MEDIA_ID ./downloads --height 1080
```

See the full [CLI reference](cli.md) for all flags and options.

## Quick start — Python library

### Synchronous

```python
from datetime import datetime

from gopro_api.api import GoProAPI
from gopro_api.api.models import CapturedRange, GoProMediaSearchParams

params = GoProMediaSearchParams(
    captured_range=CapturedRange(
        start=datetime.fromisoformat("2026-03-01"),
        end=datetime.fromisoformat("2026-03-02"),
    ),
    per_page=50,
    page=1,
)

with GoProAPI() as api:
    search = api.search(params)
    for item in search.embedded.media:
        meta = api.download(item.id)
        print(meta.filename, len(meta.embedded.files), "files")
```

### Asynchronous

```python
import asyncio
from datetime import datetime

from gopro_api.api import AsyncGoProAPI
from gopro_api.api.models import CapturedRange, GoProMediaSearchParams

params = GoProMediaSearchParams(
    captured_range=CapturedRange(
        start=datetime.fromisoformat("2026-03-01"),
        end=datetime.fromisoformat("2026-03-02"),
    ),
    per_page=50,
    page=1,
)

async def main() -> None:
    async with AsyncGoProAPI() as api:
        search = await api.search(params)
        for item in search.embedded.media:
            meta = await api.download(item.id)
            print(meta.filename, len(meta.embedded.files), "files")

asyncio.run(main())
```

## Next steps

| Topic | Where to go |
|-------|------------|
| All CLI flags | [CLI](cli.md) |
| Token setup | [Configuration](configuration.md) |
| Project internals | [Architecture](ARCHITECTURE.md) |
| Full API reference | [API Reference](api/api.md) |
