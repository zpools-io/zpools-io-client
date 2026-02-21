"""Unit tests for zpools_cli.config."""
import pytest
from pathlib import Path

from zpools_cli.config import (
    api_url_to_website_base_url,
    load_rc_file,
    build_client_config,
)


class TestApiUrlToWebsiteBaseUrl:
    """Tests for api_url_to_website_base_url."""

    def test_api_zpools_io_v1_returns_zpools_io(self):
        assert api_url_to_website_base_url("https://api.zpools.io/v1") == "https://zpools.io"

    def test_api_dev_zpools_io_v1_returns_dev_zpools_io(self):
        assert api_url_to_website_base_url("https://api.dev.zpools.io/v1") == "https://dev.zpools.io"

    def test_strips_trailing_path(self):
        assert api_url_to_website_base_url("https://api.zpools.io/v1/extra") == "https://zpools.io"

    def test_strips_trailing_slash(self):
        assert api_url_to_website_base_url("https://api.zpools.io/") == "https://zpools.io"

    def test_unknown_host_returns_same_host_with_https(self):
        assert api_url_to_website_base_url("https://other.example.com/v1") == "https://other.example.com"

    def test_empty_or_invalid_returns_zpools_io(self):
        assert api_url_to_website_base_url("") == "https://zpools.io"
        assert api_url_to_website_base_url("not-a-url") == "https://zpools.io"
