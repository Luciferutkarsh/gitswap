#!/usr/bin/env python3
"""
GitSwitch: Manage Multiple GitHub Accounts on Mac

A CLI tool to simplify switching between multiple GitHub accounts
by managing Git configs and SSH configurations.
"""
import argparse
import subprocess
from pathlib import Path
import yaml
import sys
import os

# Paths for config files
CONFIG_PATH = Path.home() / ".gitswitch.yml"
SSH_CONFIG_PATH = Path.home() / ".ssh" / "config"

__version__ = "0.1.0"


def load_config():
    """Load identities from the YAML config file."""
    if CONFIG_PATH.exists():
        try:
            data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        except Exception as e:
            print(f"Error reading config file: {e}")
            data = {}
    else:
        data = {}
    if 'identities' not in data:
        data['identities'] = {}
    return data


def save_config(data):
    """Save identities to the YAML config file."""
    CONFIG_PATH.write_text(yaml.safe_dump(data, default_flow_style=False))


def ensure_ssh_config_entry(alias, key_path):
    """Add an SSH config entry for the given alias and key if not already present."""
    SSH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)  # ensure ~/.ssh exists
    if SSH_CONFIG_PATH.exists():
        lines = SSH_CONFIG_PATH.read_text().splitlines()
    else:
        lines = []
    # Check if host alias already exists in config
    for line in lines:
        if line.strip().startswith("Host "):
            parts = line.strip().split()
            if alias in parts[1:]:
                return False  # alias already present
    # Build the new host entry block
    entry = [
        f"### gitswitch identity: {alias}",
        f"Host {alias}",
        "    HostName github.com",
        "    User git",
        f"    IdentityFile {key_path}",
        "    AddKeysToAgent yes",
        "    UseKeychain yes"
    ]
    # Append to SSH config content
    if lines and lines[-1].strip() != "":
        lines.append("")  # add a blank line separator
    lines.extend(entry)
    # Write back to ~/.ssh/config
    SSH_CONFIG_PATH.write_text("\n".join(lines) + "\n")
    return True


def remove_ssh_config_entry(alias):
    """Remove the SSH config entry for the given alias, if it exists."""
    if not SSH_CONFIG_PATH.exists():
        return
    lines = SSH_CONFIG_PATH.read_text().splitlines()
    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("Host "):
            parts = stripped.split()
            if alias in parts[1:]:
                # If alias is on a Host line with others, skip (don't remove partial)
                if len(parts) > 2 and alias in parts[1:]:
                    output_lines.append(line)
                    i += 1
                    continue
                # Remove this Host block
                if output_lines and output_lines[-1].strip().startswith("### gitswitch identity") and alias in output_lines[-1]:
                    output_lines.pop()  # remove preceding marker comment
                i += 1
                # Skip all lines in this host block
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() == "" or (next_line and next_line[0] not in (" ", "\t")):
                        # Stop when reaching a blank line or a non-indented line (next host or global config)
                        break
                    i += 1
                # (We break out of inner loop ready to process next Host or end)
                continue  # continue outer loop without adding current line
        output_lines.append(line)
        i += 1
    SSH_CONFIG_PATH.write_text("\n".join(output_lines) + "\n")


def cmd_add(args):
    """Add a new GitHub account profile."""
    data = load_config()
    identity_id = args.identity
    if ' ' in identity_id:
        print("Error: Identity name should be one word (no spaces).")
        return 1
    if identity_id in data['identities']:
        print(f"Identity '{identity_id}' already exists. Use a different name or remove it first.")
        return 1
    git_name = args.name
    git_email = args.email
    ssh_key = args.key
    # Expand ~/ shorthand in key path
    ssh_key_path = str(Path(ssh_key).expanduser())
    if not Path(ssh_key_path).exists():
        print(f"Warning: The SSH key file {ssh_key_path} was not found. (Make sure the path is correct)")
    alias = f"github-{identity_id}"
    added = ensure_ssh_config_entry(alias, ssh_key_path)
    if added is False:
        print(f"Error: SSH config already has an entry for '{alias}'. Choose a different identity name.")
        return 1
    # Save the new identity
    data['identities'][identity_id] = {'git_name': git_name, 'git_email': git_email, 'ssh_key': ssh_key_path}
    save_config(data)
    print(f"Added identity '{identity_id}' with name '{git_name}' and email '{git_email}'.")
    return 0


def cmd_list(args):
    """List all configured GitHub account profiles."""
    data = load_config()
    identities = data.get('identities', {})
    if not identities:
        print("No identities configured yet. Use 'gitswitch add' to add a profile.")
        return 0
    print("Configured identities:")
    for ident in sorted(identities):
        info = identities[ident]
        print(f" - {ident}: {info['git_name']} <{info['git_email']}> (SSH key: {info['ssh_key']})")
    return 0


def cmd_use(args):
    """Switch to a specific GitHub account profile."""
    data = load_config()
    identity_id = args.identity
    identities = data.get('identities', {})
    if identity_id not in identities:
        print(f"Identity '{identity_id}' not found. Use 'gitswitch list' to see available profiles.")
        return 1
    info = identities[identity_id]
    git_name = info['git_name']
    git_email = info['git_email']
    alias = f"github-{identity_id}"
    if args.local:
        # Local (repo-only) switch
        # Verify we're inside a Git repository
        result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True)
        if result.returncode != 0:
            print("Error: Not a Git repository. Use --global or run this inside a repository.")
            return 1
        try:
            subprocess.run(["git", "config", "user.name", git_name], check=True)
            subprocess.run(["git", "config", "user.email", git_email], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to set local Git config: {e}")
            return 1
        print(f"Switched *local* Git identity to '{identity_id}' ({git_name} / {git_email}).")
        print(f"Reminder: Ensure this repo's remote URL uses '{alias}' so the correct SSH key is used.")
    else:
        # Global switch
        try:
            subprocess.run(["git", "config", "--global", "user.name", git_name], check=True)
            subprocess.run(["git", "config", "--global", "user.email", git_email], check=True)
            
            # Update default github.com key
            update_default_github_key(info['ssh_key'])
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to set global config: {e}")
            return 1
        
        print(f"Switched *global* Git identity to '{identity_id}' ({git_name} / {git_email}).")
        print("You can now use standard github.com URLs with this identity's SSH key.")

def update_default_github_key(key_path):
    """Update the default github.com entry to use specified key"""
    ssh_config = SSH_CONFIG_PATH.read_text().splitlines()
    new_config = []
    in_github_block = False
    updated = False

    # Remove existing github.com configuration
    for line in ssh_config:
        if line.strip().startswith("Host github.com"):
            in_github_block = True
            continue
        if in_github_block:
            if line.strip().startswith("Host"):
                in_github_block = False
            else:
                continue
        new_config.append(line)

    # Add new github.com configuration
    new_config.extend([
        "# gitswitch-managed default github.com",
        "Host github.com",
        "    HostName github.com",
        "    User git",
        f"    IdentityFile {key_path}",
        "    IdentitiesOnly yes",  # Critical: Only use specified key
        "    AddKeysToAgent yes",
        "    UseKeychain yes"
    ])

    SSH_CONFIG_PATH.write_text("\n".join(new_config))
    os.chmod(SSH_CONFIG_PATH, 0o600)
    
def cmd_remove(args):
    """Remove a GitHub account profile."""
    data = load_config()
    identity_id = args.identity
    identities = data.get('identities', {})
    if identity_id not in identities:
        print(f"Identity '{identity_id}' not found.")
        return 1
    # Remove from YAML config
    del identities[identity_id]
    data['identities'] = identities
    save_config(data)
    # Remove from SSH config
    alias = f"github-{identity_id}"
    remove_ssh_config_entry(alias)
    print(f"Removed identity '{identity_id}'. (Make sure to update any repo remotes using '{alias}')")
    return 0


def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(prog="gitswitch", description="Switch between multiple GitHub account profiles.")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'add' command
    parser_add = subparsers.add_parser("add", help="Add a new GitHub account profile")
    parser_add.add_argument("identity", help="Profile identifier (e.g. 'work' or 'personal')")
    parser_add.add_argument("-n", "--name", required=True, help="Full name for Git commits (user.name)")
    parser_add.add_argument("-e", "--email", required=True, help="Email for Git commits (user.email)")
    parser_add.add_argument("-k", "--key", required=True, help="Path to the SSH private key for this account")
    parser_add.set_defaults(func=cmd_add)

    # 'list' command
    parser_list = subparsers.add_parser("list", help="List all configured profiles")
    parser_list.set_defaults(func=cmd_list)

    # 'use' command
    parser_use = subparsers.add_parser("use", help="Switch to a profile (update Git config)")
    parser_use.add_argument("identity", help="Profile identifier to switch to")
    group = parser_use.add_mutually_exclusive_group()
    group.add_argument("-g", "--global", dest="global_flag", action="store_true", help="Switch globally (default if no flag)")
    group.add_argument("-l", "--local", action="store_true", help="Switch only for the current repository")
    parser_use.set_defaults(func=cmd_use)

    # 'remove' command
    parser_remove = subparsers.add_parser("remove", help="Remove a profile")
    parser_remove.add_argument("identity", help="Profile identifier to remove")
    parser_remove.set_defaults(func=cmd_remove)

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())