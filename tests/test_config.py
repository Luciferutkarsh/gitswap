"""Tests for GitSwitch configuration handling."""

import os
import yaml
from pathlib import Path
import tempfile
import pytest
from unittest.mock import patch, mock_open

# Import the functions we want to test
from gitswitch.gitswitch import load_config, save_config


class TestConfig:
    """Test configuration loading and saving functionality."""

    def test_load_config_file_not_exists(self):
        """Test loading config when file doesn't exist."""
        with patch('gitswitch.gitswitch.CONFIG_PATH', Path('/non/existent/path.yml')):
            config = load_config()
            assert config == {'identities': {}}

    def test_load_config_file_exists(self):
        """Test loading config when file exists with data."""
        mock_data = {'identities': {'work': {'git_name': 'Test User', 'git_email': 'test@example.com', 'ssh_key': '/path/to/key'}}}
        with tempfile.NamedTemporaryFile(suffix='.yml') as tmp_file:
            tmp_path = Path(tmp_file.name)
            # Write test data to temp file
            tmp_file.write(yaml.dump(mock_data).encode('utf-8'))
            tmp_file.flush()
            
            with patch('gitswitch.gitswitch.CONFIG_PATH', tmp_path):
                config = load_config()
                assert config == mock_data

    def test_load_config_file_invalid(self):
        """Test loading config when file exists but is invalid YAML."""
        with tempfile.NamedTemporaryFile(suffix='.yml') as tmp_file:
            tmp_path = Path(tmp_file.name)
            # Write invalid YAML to temp file
            tmp_file.write(b'identities: - invalid: yaml')
            tmp_file.flush()
            
            with patch('gitswitch.gitswitch.CONFIG_PATH', tmp_path):
                config = load_config()
                assert config == {'identities': {}}

    def test_save_config(self):
        """Test saving configuration to a file."""
        mock_data = {'identities': {'personal': {'git_name': 'Personal User', 'git_email': 'personal@example.com', 'ssh_key': '/path/to/personal_key'}}}
        
        # Create temporary directory for our test
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / 'test_config.yml'
            
            with patch('gitswitch.gitswitch.CONFIG_PATH', config_path):
                save_config(mock_data)
                
                # Verify the file was created
                assert config_path.exists()
                
                # Verify the content is correct
                saved_data = yaml.safe_load(config_path.read_text())
                assert saved_data == mock_data