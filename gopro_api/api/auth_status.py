"""Shared helpers for building GoPro authentication status results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from gopro_api.api.models import GoProAuthStatus, GoProMediaSearchParams
from gopro_api.config import get_token_info

AUTH_SEARCH_ACCEPT = "application/vnd.gopro.jk.media.search+json; version=2.0.0"

_RequestError = TypeVar("_RequestError", bound=BaseException)


@dataclass(frozen=True, slots=True)
class AuthCheckRequest:
    """Prepared inputs for a token verification ``GET /media/search`` call."""

    headers: dict[str, str]
    params: dict[str, object]
    source: str | None


class AuthStatusResolver:
    """Build :class:`GoProAuthStatus` values for token verification."""

    @staticmethod
    def token_source(*, access_token: str | None, explicit_token: bool) -> str | None:
        """Return where the active access token was loaded from.

        Args:
            access_token: Token value used for API requests.
            explicit_token: Whether the token was passed to the client constructor.

        Returns:
            ``"argument"``, ``"environment"``, ``".env"``, or ``None`` when unset.
        """
        if not access_token:
            return None
        if explicit_token:
            return "argument"
        _, source = get_token_info()
        return source

    @staticmethod
    def prepare_check(
        *,
        access_token: str | None,
        explicit_token: bool,
        get_headers: Callable[[str], dict[str, str]],
    ) -> GoProAuthStatus | AuthCheckRequest:
        """Prepare headers and query params for token verification.

        Args:
            access_token: Token value used for API requests.
            explicit_token: Whether the token was passed to the client constructor.
            get_headers: Client callback that builds request headers for an Accept
                value.

        Returns:
            Missing-token status, or request inputs when verification can proceed.
        """
        if not access_token:
            return AuthStatusResolver.without_request()

        params = GoProMediaSearchParams(per_page=1, page=1)
        return AuthCheckRequest(
            headers=get_headers(AUTH_SEARCH_ACCEPT),
            params=params.model_dump(),
            source=AuthStatusResolver.token_source(
                access_token=access_token,
                explicit_token=explicit_token,
            ),
        )

    @staticmethod
    def without_request() -> GoProAuthStatus:
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

    @staticmethod
    def from_http(*, status_code: int, source: str) -> GoProAuthStatus:
        """Build a status result from an HTTP verification response.

        Args:
            status_code: HTTP status returned by ``GET /media/search``.
            source: Token source label from :meth:`token_source`.

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

    @staticmethod
    def from_request_failure(
        *,
        source: str | None,
        message: str,
    ) -> GoProAuthStatus:
        """Build a status result when the verification request fails.

        Args:
            source: Token source label from :meth:`token_source`.
            message: Human-readable failure summary.

        Returns:
            Parsed authentication status for the caller.
        """
        return GoProAuthStatus(
            token_configured=True,
            token_source=source,
            authenticated=False,
            http_status=None,
            message=message,
        )

    @staticmethod
    def verify_sync(
        *,
        access_token: str | None,
        explicit_token: bool,
        get_headers: Callable[[str], dict[str, str]],
        perform_request: Callable[[AuthCheckRequest], int],
        request_error_type: type[_RequestError],
    ) -> GoProAuthStatus:
        """Run a synchronous token verification request.

        Args:
            access_token: Token value used for API requests.
            explicit_token: Whether the token was passed to the client constructor.
            get_headers: Client callback that builds request headers for an Accept
                value.
            perform_request: Callable that performs ``GET /media/search`` and returns
                the HTTP status code.
            request_error_type: Exception type raised when the HTTP client fails.

        Returns:
            Structured authentication status; never raises for HTTP failures.
        """
        prepared = AuthStatusResolver.prepare_check(
            access_token=access_token,
            explicit_token=explicit_token,
            get_headers=get_headers,
        )
        if isinstance(prepared, GoProAuthStatus):
            return prepared

        try:
            status_code = perform_request(prepared)
        except request_error_type as exc:
            return AuthStatusResolver.from_request_failure(
                source=prepared.source,
                message=f"Request failed: {exc}",
            )
        return AuthStatusResolver.from_http(
            status_code=status_code,
            source=prepared.source or "argument",
        )

    @staticmethod
    async def verify_async(
        *,
        access_token: str | None,
        explicit_token: bool,
        get_headers: Callable[[str], dict[str, str]],
        perform_request: Callable[[AuthCheckRequest], Awaitable[int]],
        request_error_type: type[_RequestError],
    ) -> GoProAuthStatus:
        """Run an asynchronous token verification request.

        Args:
            access_token: Token value used for API requests.
            explicit_token: Whether the token was passed to the client constructor.
            get_headers: Client callback that builds request headers for an Accept
                value.
            perform_request: Callable that performs ``GET /media/search`` and returns
                the HTTP status code.
            request_error_type: Exception type raised when the HTTP client fails.

        Returns:
            Structured authentication status; never raises for HTTP failures.
        """
        prepared = AuthStatusResolver.prepare_check(
            access_token=access_token,
            explicit_token=explicit_token,
            get_headers=get_headers,
        )
        if isinstance(prepared, GoProAuthStatus):
            return prepared

        try:
            status_code = await perform_request(prepared)
        except request_error_type as exc:
            return AuthStatusResolver.from_request_failure(
                source=prepared.source,
                message=f"Request failed: {exc}",
            )
        return AuthStatusResolver.from_http(
            status_code=status_code,
            source=prepared.source or "argument",
        )
