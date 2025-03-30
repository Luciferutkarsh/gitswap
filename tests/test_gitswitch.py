"""Tests for GitSwitch main functionality."""

import os
import yaml
import pytest
import subprocess
from pathlib import Path
import tempfile
from unittest.mock import patch, Mock, call, mock_open

# Import modules and functions to test
from gitswitch.gitswitch import (
    ensure_ssh_config_entry,
    remove_ssh_config_entry,
    cmd_add,
    cmd_list,
    cmd_use,
    cmd_remove,
    main,
    create_parser
)


class TestSSHConfig:
    """Test SSH configuration functionality."""

    def test_ensure_ssh_config_entry_new_file(self):
        """Test adding an SSH config entry when the file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_ssh_path = Path(tmp_dir) / 'config'
            
            with patch('gitswitch.gitswitch.SSH_CONFIG_PATH', mock_ssh_path):
                result = ensure_ssh_config_entry('github-test', '/path/to/key')
                
                # Check the result
                assert result is True
                
                # Verify the file was created with correct content
                assert mock_ssh_path.exists()
                content = mock_ssh_path.read_text()
                assert 'Host github-test' in content
                assert 'IdentityFile /path/to/key' in content

    def test_ensure_ssh_config_entry_existing_file(self):
        """Test adding an SSH config entry to an existing config file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_ssh_path = Path(tmp_dir) / 'config'
            
            # Create existing SSH config with some content
            existing_content = "# Existing SSH Config\nHost example\n    HostName example.com\n    User test\n"
            mock_ssh_path.write_text(existing_content)
            
            with patch('gitswitch.gitswitch.SSH_CONFIG_PATH', mock_ssh_path):
                result = ensure_ssh_config_entry('github-test', '/path/to/key')
                
                # Check the result
                assert result is True
                
                # Verify the file was updated correctly
                content = mock_ssh_path.read_text()
                assert existing_content.strip() in content
                assert 'Host github-test' in content
                assert 'IdentityFile /path/to/key' in content

    def test_ensure_ssh_config_entry_existing_alias(self):
        """Test that we don't add a duplicate entry if the alias already exists."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_ssh_path = Path(tmp_dir) / 'config'
            
            # Create existing SSH config with the alias already present
            existing_content = "Host github-test\n    HostName github.com\n    User git\n    IdentityFile /existing/path/to/key\n"
            mock_ssh_path.write_text(existing_content)
            
            with patch('gitswitch.gitswitch.SSH_CONFIG_PATH', mock_ssh_path):
                result = ensure_ssh_config_entry('github-test', '/new/path/to/key')
                
                # Check the result - should be False since the alias exists
                assert result is False
                
                # Verify the file wasn't changed
                content = mock_ssh_path.read_text()
                assert content == existing_content

    def test_remove_ssh_config_entry(self):
        """Test removing an SSH config entry."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_ssh_path = Path(tmp_dir) / 'config'
            
            # Create existing SSH config with multiple entries
            existing_content = """# Some header
Host example
    HostName example.com
    User test

### gitswitch identity: github-test
Host github-test
    HostName github.com
    User git
    IdentityFile /path/to/test/key
    AddKeysToAgent yes
    UseKeychain yes

Host another
    HostName another.com
    User test2
"""
            mock_ssh_path.write_text(existing_content)
            
            with patch('gitswitch.gitswitch.SSH_CONFIG_PATH', mock_ssh_path):
                remove_ssh_config_entry('github-test')
                
                # Verify the file was updated correctly
                content = mock_ssh_path.read_text()
                assert 'Host example' in content
                assert 'Host another' in content
                assert 'Host github-test' not in content
                assert '### gitswitch identity: github-test' not in content


class TestCommands:
    """Test command handlers."""

    @pytest.fixture
    def mock_config(self):
        return {
            'identities': {
                'work': {
                    'git_name': 'Work User',
                    'git_email': 'work@example.com',
                    'ssh_key': '/path/to/work_key'
                },
                'personal': {
                    'git_name': 'Personal User',
                    'git_email': 'personal@example.com',
                    'ssh_key': '/path/to/personal_key'
                }
            }
        }

    @pytest.fixture
    def args_add(self):
        """Create a mock args object for add command."""
        args = Mock()
        args.identity = 'test'
        args.name = 'Test User'
        args.email