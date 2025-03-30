# GitSwitch

## Manage Multiple GitHub Accounts on Mac

GitSwitch is a Python-based CLI tool that simplifies the process of managing multiple GitHub accounts (for example, a personal and a work account) on one machine. It allows quick switching between multiple GitHub accounts by updating your Git config and SSH config as needed.

---

## Features

- **Multiple Identity Profiles**: Add multiple Git identity profiles, each with a name, email, and SSH key.
- **Global or Local Scope**: Switch the Git identity globally (affecting all repositories) or locally for the current repository only.
- **SSH Key Management**: Configure SSH host aliases for each account so the correct SSH key is used when pushing to GitHub.
- **Host Aliases for GitHub**: Each account is given a distinct SSH host alias (e.g., `github-work` for your work account).
- **User-Friendly CLI Commands**: Provides intuitive subcommands.

---

## Installation

```bash
pip install gitswitch
```

## Usage

### Add a new account

```bash
gitswitch add work -n "Your Name" -e "your.email@company.com" -k "~/.ssh/id_ed25519_work"
```

This creates an SSH config alias `github-work` and stores the profile in `~/.gitswitch.yml`.

### List configured accounts

```bash
gitswitch list
```

Output:

```text
Configured identities:
 - personal: Your Name <your.personal@example.com> (SSH key: /Users/you/.ssh/id_ed25519_personal)
 - work: Your Name <your.email@company.com> (SSH key: /Users/you/.ssh/id_ed25519_work)
```

### Switch global identity

```bash
gitswitch use work --global
```

This sets your global `user.name` and `user.email` to the work profile.

### Switch identity locally (per repo)

```bash
cd ~/projects/personal/MyProj
gitswitch use personal -l
```

This only changes the Git config in the current repository's `.git/config`.

### Remove an identity

```bash
gitswitch remove work
```

This deletes the "work" entry from `~/.gitswitch.yml` and removes the corresponding block from `~/.ssh/config`.

## How It Works

### Git Identity

Git uses `user.name` and `user.email` settings to identify the author of commits. GitSwitch updates these settings either globally or locally for one repository.

### SSH Key Management

To handle multiple accounts on GitHub, SSH keys are used to authenticate as different users. GitSwitch uses SSH host aliases, such as `github-work` or `github-personal`, to point to GitHub but with specific SSH keys.

For example, an entry in your SSH config might look like:

```text
Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
    AddKeysToAgent yes
    UseKeychain yes
```

### Using Host Aliases in Git

Once an alias is set, you need to use it in your Git remote URL for repositories of that account. For instance:

```bash
git clone git@github-work:YourWorkUsername/YourRepo.git
```

Or update an existing repo's origin URL:

```bash
git remote set-url origin git@github-work:YourWorkUsername/YourRepo.git
```

## Troubleshooting

### SSH Authentication Issues

If you get "Permission denied (publickey)" when pushing or cloning, check:

- The repository's Git remote URL is using the correct host alias.
- Your SSH keys are added to the `ssh-agent`.
- Your public key is added to the corresponding GitHub account.

### Commit Author Incorrect

If your commits are showing under the wrong GitHub account, check the `user.email` in your Git config.

### Multiple Accounts on One Repo

Generally, each Git repository has a single remote URL (`origin`) and thus a single account context. If you need to contribute to one repo from two accounts, you'd normally use separate clones or change remote URLs when needed.

## License

This project is licensed under the MIT License - see the LICENSE file for details.