"""
Tests for the configuration module.
"""

import os
import tempfile
from pathlib import Path
import unittest
from unittest import mock
from dataclasses import asdict

import yaml

from ams.core.config import Config, load_config, LogLevel


class TestConfig(unittest.TestCase):
    """Test cases for the configuration module."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for key in list(os.environ.keys()):
            if key.startswith("AMS_"):
                del os.environ[key]

    def test_default_config(self):
        """Test that default configuration is loaded correctly."""
        config = Config()
        self.assertEqual(config.server.host, "0.0.0.0")
        self.assertEqual(config.server.port, 8000)
        self.assertEqual(config.server.reload, False)
        self.assertEqual(config.server.log_level, LogLevel.INFO)
        self.assertEqual(config.server.workers, 1)

    def test_env_vars_config(self):
        """Test that environment variables override default configuration."""
        # Set environment variables
        os.environ["AMS_HOST"] = "127.0.0.1"
        os.environ["AMS_PORT"] = "9000"
        os.environ["AMS_RELOAD"] = "true"
        os.environ["AMS_LOG_LEVEL"] = "debug"
        os.environ["AMS_WORKERS"] = "2"

        config = Config()
        self.assertEqual(config.server.host, "127.0.0.1")
        self.assertEqual(config.server.port, 9000)
        self.assertEqual(config.server.reload, True)
        self.assertEqual(config.server.log_level, LogLevel.DEBUG)
        self.assertEqual(config.server.workers, 2)

    def test_file_config(self):
        """Test that configuration can be loaded from a file."""
        config_data = {
            "server": {
                "host": "localhost",
                "port": 8080,
                "reload": True,
                "log_level": "warning",
                "workers": 3
            },
            "database": {
                "url": "postgresql://user:pass@localhost/db",
                "echo": True,
                "pool_size": 10
            }
        }

        # Create a temporary file with test configuration
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
            yaml.dump(config_data, temp)
            temp_path = temp.name

        try:
            # Load configuration from the file
            config = Config.from_file(temp_path)
            
            # Check server configuration
            self.assertEqual(config.server.host, "localhost")
            self.assertEqual(config.server.port, 8080)
            self.assertEqual(config.server.reload, True)
            self.assertEqual(config.server.log_level, LogLevel.WARNING)
            self.assertEqual(config.server.workers, 3)
            
            # Check database configuration
            self.assertEqual(config.database.url, "postgresql://user:pass@localhost/db")
            self.assertEqual(config.database.echo, True)
            self.assertEqual(config.database.pool_size, 10)
            
            # Test to_dict method
            config_dict = config.to_dict()
            self.assertEqual(config_dict["server"]["host"], "localhost")
            self.assertEqual(config_dict["database"]["url"], "postgresql://user:pass@localhost/db")
        finally:
            # Clean up the temporary file
            Path(temp_path).unlink()

    def test_load_config_function(self):
        """Test the load_config function."""
        with mock.patch("ams.core.config.Config.from_file") as mock_from_file:
            mock_from_file.return_value = Config()
            with mock.patch("ams.core.config.Config.setup_logging") as mock_setup_logging:
                config = load_config("/path/to/config.yaml")
                mock_from_file.assert_called_once_with("/path/to/config.yaml")
                mock_setup_logging.assert_called_once()
                self.assertIsInstance(config, Config)

    def test_missing_config_file(self):
        """Test behavior when config file is missing."""
        config = Config.from_file("/nonexistent/path/to/config.yaml")
        # Should fall back to default values
        self.assertEqual(config.server.host, "0.0.0.0")
        self.assertEqual(config.server.port, 8000)

    def test_config_asdict(self):
        """Test conversion of Config to dictionary."""
        config = Config()
        config_dict = asdict(config)
        self.assertIsInstance(config_dict, dict)
        self.assertIn("server", config_dict)
        self.assertIn("database", config_dict)
        self.assertIn("security", config_dict)
        self.assertIn("llm", config_dict)


if __name__ == "__main__":
    unittest.main() 