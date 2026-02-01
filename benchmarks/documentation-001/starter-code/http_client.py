"""HTTP client library for making HTTP requests with retry support and flexible configuration.

This module provides HTTPClient for making requests, Response for handling responses,
RetryConfig for configuring retry behavior, and HTTPError for error handling.

Example:
    from http_client import HTTPClient
    client = HTTPClient(base_url="https://httpbin.org")
    response = client.get("/get")
    print(response.status_code)
    data = response.json()
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional, Union
from http.client import HTTPResponse
import time


class HTTPError(Exception):
    """Exception raised when an HTTP request fails.

    Attributes:
        status_code: The HTTP status code (e.g., 404, 500). May be 0 for connection errors.
        message: Human-readable error message.
        response_body: Optional response body content if available.

    Example:
        from http_client import HTTPClient, HTTPError
        try:
            client = HTTPClient()
            client.get("https://httpbin.org/status/404")
        except HTTPError as e:
            print(e.status_code, e.message)
    """

    def __init__(self, status_code: int, message: str, response_body: Optional[str] = None):
        """Initialize HTTPError with status code, message, and optional response body.

        Args:
            status_code: The HTTP status code.
            message: Error message or reason phrase.
            response_body: Optional raw response body string.
        """
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")


class RetryConfig:
    """Configuration for retry behavior on failed HTTP requests.

    When a request fails with a configurable status code (e.g., 503),
    the client will retry after a backoff delay.

    Attributes:
        max_retries: Maximum number of retry attempts.
        backoff_factor: Base delay in seconds; actual delay is backoff_factor * 2^attempt.
        retry_statuses: List of HTTP status codes that trigger a retry (default: 500, 502, 503, 504).

    Example:
        from http_client import RetryConfig, HTTPClient
        config = RetryConfig(max_retries=5, backoff_factor=2.0)
        client = HTTPClient(retry_config=config)
    """

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0,
                 retry_statuses: Optional[list] = None):
        """Initialize RetryConfig.

        Args:
            max_retries: Maximum number of retry attempts. Defaults to 3.
            backoff_factor: Base delay in seconds for exponential backoff. Defaults to 1.0.
            retry_statuses: List of status codes to retry on. Defaults to [500, 502, 503, 504].
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses or [500, 502, 503, 504]


class HTTPClient:
    """HTTP client for making GET, POST, PUT, PATCH, and DELETE requests.

    Supports optional base URL, default headers, timeout, and retry configuration.
    Response bodies can be sent as form data, JSON, or raw bytes.

    Attributes:
        base_url: Base URL prepended to relative endpoints (trailing slash removed).
        default_headers: Headers included in every request.
        timeout: Request timeout in seconds.
        retry_config: Optional RetryConfig for retrying on server errors.

    Example:
        from http_client import HTTPClient
        client = HTTPClient(base_url="https://httpbin.org", timeout=10)
        response = client.get("/get", params={"key": "value"})
        assert response.is_success()
    """

    def __init__(self, base_url: str = "", default_headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30, retry_config: Optional[RetryConfig] = None):
        """Initialize the HTTP client.

        Args:
            base_url: Base URL for relative endpoints. Defaults to empty string.
            default_headers: Optional dict of headers applied to every request.
            timeout: Request timeout in seconds. Defaults to 30.
            retry_config: Optional RetryConfig for retrying on server errors.
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.retry_config = retry_config

    def _build_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            url = endpoint
        else:
            endpoint = endpoint.lstrip('/')
            url = f"{self.base_url}/{endpoint}" if self.base_url else endpoint

        if params:
            query_string = urllib.parse.urlencode(params)
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{query_string}"

        return url

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged_headers = self.default_headers.copy()
        if headers:
            merged_headers.update(headers)
        return merged_headers

    def _prepare_body(self, data: Optional[Union[Dict, str]] = None,
                     json_data: Optional[Dict] = None) -> Optional[bytes]:
        if json_data is not None:
            return json.dumps(json_data).encode('utf-8')
        elif isinstance(data, dict):
            return urllib.parse.urlencode(data).encode('utf-8')
        elif isinstance(data, str):
            return data.encode('utf-8')
        return None

    def _execute_request(self, method: str, url: str, headers: Dict[str, str],
                        body: Optional[bytes] = None) -> HTTPResponse:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            response = urllib.request.urlopen(req, timeout=self.timeout)
            return response
        except urllib.error.HTTPError as e:
            response_body = e.read().decode('utf-8', errors='ignore') if e.fp else None
            raise HTTPError(e.code, e.reason, response_body)
        except urllib.error.URLError as e:
            raise HTTPError(0, str(e.reason))

    def _should_retry(self, error: HTTPError, attempt: int) -> bool:
        if not self.retry_config or attempt >= self.retry_config.max_retries:
            return False
        return error.status_code in self.retry_config.retry_statuses

    def _calculate_backoff(self, attempt: int) -> float:
        if not self.retry_config:
            return 0
        return self.retry_config.backoff_factor * (2 ** attempt)

    def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None, data: Optional[Union[Dict, str]] = None,
                json_data: Optional[Dict] = None) -> 'Response':
        """Send an HTTP request and return a Response.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            endpoint: URL path or full URL. Relative paths use base_url if set.
            params: Optional query parameters to append to the URL.
            headers: Optional additional headers for this request.
            data: Optional request body as dict (form-encoded), str, or None.
            json_data: Optional dict to send as JSON body; sets Content-Type to application/json.

        Returns:
            Response object with status, headers, and body.

        Raises:
            HTTPError: If the request fails or returns an error status after retries.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            resp = client.request("POST", "/post", json_data={"name": "test"})
        """
        url = self._build_url(endpoint, params)
        merged_headers = self._prepare_headers(headers)

        if json_data is not None and 'Content-Type' not in merged_headers:
            merged_headers['Content-Type'] = 'application/json'
        elif isinstance(data, dict) and 'Content-Type' not in merged_headers:
            merged_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        body = self._prepare_body(data, json_data)

        attempt = 0
        last_error = None

        while attempt <= (self.retry_config.max_retries if self.retry_config else 0):
            try:
                http_response = self._execute_request(method, url, merged_headers, body)
                return Response(http_response)
            except HTTPError as e:
                last_error = e
                if self._should_retry(e, attempt):
                    backoff = self._calculate_backoff(attempt)
                    time.sleep(backoff)
                    attempt += 1
                else:
                    raise

        raise last_error

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> 'Response':
        """Send a GET request.

        Args:
            endpoint: URL path or full URL.
            params: Optional query parameters.
            headers: Optional request headers.

        Returns:
            Response object.

        Raises:
            HTTPError: If the request fails.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            response = client.get("/get")
            print(response.json())
        """
        return self.request('GET', endpoint, params=params, headers=headers)

    def post(self, endpoint: str, data: Optional[Union[Dict, str]] = None,
             json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> 'Response':
        """Send a POST request.

        Args:
            endpoint: URL path or full URL.
            data: Optional body as dict (form-encoded) or str.
            json_data: Optional dict sent as JSON body.
            headers: Optional request headers.

        Returns:
            Response object.

        Raises:
            HTTPError: If the request fails.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            response = client.post("/post", json_data={"key": "value"})
        """
        return self.request('POST', endpoint, headers=headers, data=data, json_data=json_data)

    def put(self, endpoint: str, data: Optional[Union[Dict, str]] = None,
            json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> 'Response':
        """Send a PUT request.

        Args:
            endpoint: URL path or full URL.
            data: Optional body as dict or str.
            json_data: Optional dict sent as JSON body.
            headers: Optional request headers.

        Returns:
            Response object.

        Raises:
            HTTPError: If the request fails.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            response = client.put("/put", json_data={"updated": True})
        """
        return self.request('PUT', endpoint, headers=headers, data=data, json_data=json_data)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> 'Response':
        """Send a DELETE request.

        Args:
            endpoint: URL path or full URL.
            headers: Optional request headers.

        Returns:
            Response object.

        Raises:
            HTTPError: If the request fails.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            response = client.delete("/delete")
        """
        return self.request('DELETE', endpoint, headers=headers)

    def patch(self, endpoint: str, data: Optional[Union[Dict, str]] = None,
              json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> 'Response':
        """Send a PATCH request.

        Args:
            endpoint: URL path or full URL.
            data: Optional body as dict or str.
            json_data: Optional dict sent as JSON body.
            headers: Optional request headers.

        Returns:
            Response object.

        Raises:
            HTTPError: If the request fails.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            response = client.patch("/patch", json_data={"field": "value"})
        """
        return self.request('PATCH', endpoint, headers=headers, data=data, json_data=json_data)


class Response:
    """Wrapper around HTTP response providing status, headers, and body access.

    Body is read lazily. Use .content for bytes, .text for decoded str, .json() for parsed JSON.

    Example:
        from http_client import HTTPClient
        client = HTTPClient(base_url="https://httpbin.org")
        response = client.get("/get")
        if response.is_success():
            data = response.json()
    """

    def __init__(self, http_response: HTTPResponse):
        """Wrap an http.client.HTTPResponse.

        Args:
            http_response: The underlying HTTPResponse from urlopen.
        """
        self._response = http_response
        self._content = None
        self._text = None
        self._json_data = None

    @property
    def status_code(self) -> int:
        """Return the HTTP status code (e.g., 200, 404).

        Returns:
            Integer status code.
        """
        return self._response.status

    @property
    def headers(self) -> Dict[str, str]:
        """Return response headers as a dict.

        Returns:
            Dict mapping header names to values.
        """
        return dict(self._response.headers)

    @property
    def content(self) -> bytes:
        """Return raw response body as bytes.

        Returns:
            Raw response body. Cached after first read.
        """
        if self._content is None:
            self._content = self._response.read()
        return self._content

    @property
    def text(self) -> str:
        """Return response body decoded as string.

        Uses charset from Content-Type or defaults to utf-8.

        Returns:
            Decoded string. Cached after first read.
        """
        if self._text is None:
            charset = self._get_charset()
            self._text = self.content.decode(charset, errors='replace')
        return self._text

    def _get_charset(self) -> str:
        content_type = self._response.headers.get('Content-Type', '')
        if 'charset=' in content_type:
            return content_type.split('charset=')[-1].split(';')[0].strip()
        return 'utf-8'

    def json(self) -> Union[Dict, list]:
        """Parse response body as JSON and return dict or list.

        Returns:
            Parsed JSON (dict or list).

        Raises:
            json.JSONDecodeError: If body is not valid JSON.

        Example:
            from http_client import HTTPClient
            client = HTTPClient(base_url="https://httpbin.org")
            response = client.get("/get")
            data = response.json()
        """
        if self._json_data is None:
            self._json_data = json.loads(self.text)
        return self._json_data

    def is_success(self) -> bool:
        """Return True if status code is 2xx.

        Returns:
            True if 200 <= status_code < 300.
        """
        return 200 <= self.status_code < 300

    def is_redirect(self) -> bool:
        """Return True if status code is 3xx.

        Returns:
            True if 300 <= status_code < 400.
        """
        return 300 <= self.status_code < 400

    def is_client_error(self) -> bool:
        """Return True if status code is 4xx.

        Returns:
            True if 400 <= status_code < 500.
        """
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        """Return True if status code is 5xx.

        Returns:
            True if 500 <= status_code < 600.
        """
        return 500 <= self.status_code < 600
