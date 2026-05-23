# CLI

`gopro-api` ships with a command-line interface built on [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich). After installation it is available as `gopro-api` on your `PATH`, or you can invoke it directly as a module:

```bash
python -m gopro_api.cli <command> [options]
```

## Global options

| Option | Default | Description |
|--------|---------|-------------|
| `--timeout` | `60` | Timeout in seconds for API calls and CDN downloads. |
| `--version` | — | Print the installed version and exit. |
| `--help` | — | Show help text. |

## Commands

### `search`

Search your GoPro cloud library within a capture date range.

```bash
gopro-api search --start 2026-03-01 --end 2026-03-03
```

**Options**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--start` | `DATE` | **required** | Range start (inclusive), `YYYY-MM-DD`. |
| `--end` | `DATE` | **required** | Range end (inclusive), `YYYY-MM-DD`. |
| `--per-page` | `INT` | `100` | Items per API page. |
| `--all-pages` | flag | off | Fetch every page automatically. |
| `--json` | flag | off | Print the raw API JSON instead of the tabular view. |

**Default output** — a `# _pages` summary line, then a tab-separated table with columns `id`, `type`, `captured_at`, `filename`, … (other API fields land in an `extra` JSON column).

**`--json`** — pretty-prints the full API-shaped response; combined with `--all-pages` produces a JSON array of every page.

```bash
# Tabular view, all pages
gopro-api search --start 2026-03-01 --end 2026-03-03 --all-pages

# Raw JSON for a single page
gopro-api search --start 2026-03-01 --end 2026-03-03 --per-page 30 --json

# Raw JSON, all pages
gopro-api search --start 2026-03-01 --end 2026-03-03 --json --all-pages
```

---

### `info`

Show download metadata for a single media item.

```bash
gopro-api info MEDIA_ID
```

**Arguments**

| Argument | Description |
|----------|-------------|
| `MEDIA_ID` | The media identifier returned by `search`. |

**Options**

| Option | Description |
|--------|-------------|
| `--json` | Print the full API payload instead of the formatted summary. |

**Default output** — filename on the first line, then one line per downloadable file showing size and CDN URL.

```bash
gopro-api info MEDIA_ID --json
```

---

### `pull`

Download asset(s) for a media item into a local directory.

```bash
gopro-api pull MEDIA_ID ./downloads
```

**Arguments**

| Argument | Description |
|----------|-------------|
| `MEDIA_ID` | The media identifier returned by `search`. |
| `DESTINATION` | Local directory; created if it does not exist. |

**Options**

| Option | Type | Description |
|--------|------|-------------|
| `--height` | `INT` | Target height in pixels (videos). The variation with the smallest squared pixel-delta is chosen; ties go to the larger resolution. |
| `--width` | `INT` | Target width in pixels (videos). Combined with `--height` when both are given. |

**Behaviour by media type**

- **Videos (`.mp4`)** — downloads one `variations` entry: the tallest by default, or the closest to the requested `--height` / `--width`.
- **Photos** — uses the `files` list; one request per file.

```bash
# Default (tallest video variant)
gopro-api pull MEDIA_ID ./downloads

# Closest to 1080 p
gopro-api pull MEDIA_ID ./downloads --height 1080

# Closest to 1920 × 1080
gopro-api pull MEDIA_ID ./downloads --width 1920 --height 1080
```

## Running without an installed entry point

```bash
python -m gopro_api.cli search --start 2026-03-01 --end 2026-03-02
python -m gopro_api.cli info MEDIA_ID
python -m gopro_api.cli pull MEDIA_ID ./out
python -m gopro_api.cli pull MEDIA_ID ./out --height 720
```

## API reference

For the auto-generated docstrings of the CLI internals see [API Reference → CLI](api/cli.md).
