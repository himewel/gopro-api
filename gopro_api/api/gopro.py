"""Synchronous GoPro cloud API client (``requests``)."""

import requests

from gopro_api.config import get_settings, get_token_info
from gopro_api.api.models import (
    GoProAuthStatus,
    GoProMediaDownloadResponse,
    GoProMediaSearchParams,
    GoProMediaSearchResponse,
)


class GoProAPI:
    """Synchronous client for ``https://api.gopro.com`` (Quik / cloud library).

    Use as a context manager so a ``requests.Session`` is created and closed
    around ``search`` and ``download``. Pass ``access_token`` to override
    :func:`~gopro_api.config.get_settings`.
    """

    def __init__(self, access_token: str | None = None, timeout: float = 10.0) -> None:
        """Create a sync client.

        Args:
            access_token: ``gp_access_token`` cookie value; defaults to
                :attr:`~gopro_api.config.Settings.gp_access_token` from settings.
            timeout: Per-request timeout in seconds passed to ``requests``.
        """
        self._explicit_token = access_token is not None
        self.access_token = access_token or get_settings().gp_access_token
        self._timeout = timeout
        self._session: requests.Session | None = None

    @property
    def base_url(self) -> str:
        """HTTPS origin for API requests.

        Returns:
            Always ``https://api.gopro.com``.
        """
        return "https://api.gopro.com"

    def get_headers(self, accept: str) -> dict[str, str]:
        """Build headers for a JSON API request.

        Args:
            accept: Full ``Accept`` header value (vendor MIME type + version).

        Returns:
            Mapping with ``Cookie`` (token) and ``Accept``.
        """
        return {
            "Cookie": "gp_access_token=" + self.access_token,
            "Accept": accept,
        }

    def __enter__(self) -> "GoProAPI":
        """Open a ``requests.Session`` for the duration of the ``with`` block.

        Returns:
            ``self`` for use inside the ``with`` body.
        """
        self._session = requests.Session()
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the session and clear internal state.

        Args:
            *exc: Exception info from the interpreter (ignored).
        """
        if self._session is not None:
            self._session.close()
            self._session = None

    def _session_or_raise(self) -> requests.Session:
        """Return the active ``requests.Session``.

        Returns:
            The session opened in ``__enter__``.

        Raises:
            RuntimeError: If called before ``__enter__`` or after ``__exit__``.
        """
        if self._session is None:
            msg = "Use GoProAPI as a context manager: with GoProAPI() as api: ..."
            raise RuntimeError(msg)
        return self._session

    def download(self, media_id: str) -> GoProMediaDownloadResponse:
        """Return download metadata and CDN URLs for one media item.

        Calls ``GET /media/{media_id}/download`` with the GoPro media JSON
        vendor MIME type.

        Args:
            media_id: Cloud library identifier for the media item.

        Returns:
            Parsed response (filenames, variations, embedded files, CDN URLs).

        Raises:
            RuntimeError: If used outside ``with GoProAPI() as api``.
            requests.HTTPError: When the response status is not successful.
            pydantic.ValidationError: If the JSON body does not match the model.
        """
        headers = self.get_headers("application/vnd.gopro.jk.media+json; version=2.0.0")
        session = self._session_or_raise()
        response = session.get(
            f"{self.base_url}/media/{media_id}/download",
            headers=headers,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return GoProMediaDownloadResponse.model_validate_json(response.text)

    def search(self, params: GoProMediaSearchParams) -> GoProMediaSearchResponse:
        """Search media in the cloud library with structured query parameters.

        Calls ``GET /media/search``; ``params.model_dump()`` is sent as the query
        string after serialization.

        Args:
            params: Search filters (capture range, pagination, fields, etc.).

        Returns:
            Paginated search results and embedded media rows.

        Raises:
            RuntimeError: If used outside ``with GoProAPI() as api``.
            requests.HTTPError: When the response status is not successful.
            pydantic.ValidationError: If the JSON body does not match the model.
        """
        headers = self.get_headers(
            "application/vnd.gopro.jk.media.search+json; version=2.0.0",
        )
        session = self._session_or_raise()
        response = session.get(
            f"{self.base_url}/media/search",
            headers=headers,
            params=params.model_dump(),
            timeout=self._timeout,
        )
        response.raise_for_status()
        return GoProMediaSearchResponse.model_validate_json(response.text)

    def _token_source(self) -> str | None:
        """Return where the active access token was loaded from.

        Returns:
            ``"argument"``, ``"environment"``, ``".env"``, or ``None`` when unset.
        """
        if not self.access_token:
            return None
        if self._explicit_token:
            return "argument"
        _, source = get_token_info()
        return source

    def _auth_status_without_request(self) -> GoProAuthStatus:
        """Build a status result when no token is configured.

        Returns:
            Status indicating the token is missing.
        """
        return GoProAuthStatus(
            token_configured=False,
            token_source=None,
            authenticated=None,
            http_status=None,
            message="GP_ACCESS_TOKEN is not set.",
        )

    def _auth_status_from_http(
        self, *, status_code: int, source: str
    ) -> GoProAuthStatus:
        """Build a status result from an HTTP verification response.

        Args:
            status_code: HTTP status returned by ``GET /media/search``.
            source: Token source label from :meth:`_token_source`.

        Returns:
            Parsed authentication status for the caller.
        """
        if status_code == 200:
            return GoProAuthStatus(
                token_configured=True,
                token_source=source,
                authenticated=True,
                http_status=status_code,
                message="Access token is valid.",
            )
        if status_code == 401:
            return GoProAuthStatus(
                token_configured=True,
                token_source=source,
                authenticated=False,
                http_status=status_code,
                message="Access token was rejected (expired or invalid).",
            )
        return GoProAuthStatus(
            token_configured=True,
            token_source=source,
            authenticated=False,
            http_status=status_code,
            message=f"Unexpected HTTP status {status_code}.",
        )

    def check_auth(self) -> GoProAuthStatus:
        """Verify that the configured access token is accepted by the API.

        Performs a lightweight ``GET /media/search`` request with ``per_page=1``.

        Returns:
            Structured authentication status; never raises for HTTP failures.

        Raises:
            RuntimeError: If used outside ``with GoProAPI() as api``.
        """
        if not self.access_token:
            return self._auth_status_without_request()

        headers = self.get_headers(
            "application/vnd.gopro.jk.media.search+json; version=2.0.0",
        )
        params = GoProMediaSearchParams(per_page=1, page=1)
        session = self._session_or_raise()
        source = self._token_source()
        try:
            response = session.get(
                f"{self.base_url}/media/search",
                headers=headers,
                params=params.model_dump(),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            return GoProAuthStatus(
                token_configured=True,
                token_source=source,
                authenticated=False,
                http_status=None,
                message=f"Request failed: {exc}",
            )
        return self._auth_status_from_http(
            status_code=response.status_code,
            source=source or "argument",
        )
