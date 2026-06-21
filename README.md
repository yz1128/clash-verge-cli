# Clash Verge CLI 🖥️

Enhanced command-line interface for Clash Verge VPN client on macOS and Windows.

## Platforms

- **macOS**: `clash_verge_cli.py`
- **Windows**: `clash_verge_cli_windows.py`

## Overview

A comprehensive CLI tool to manage Clash Verge VPN client programmatically. Control proxies, profiles, system settings, monitor traffic, and more - all from terminal.

## ✨ Latest Features (v1.1.0)

- 🚀 **Auto-Select Fastest Node** - Automatically test and select the fastest proxy
- ⚡ **Parallel Latency Testing** - 5-10x faster proxy testing with concurrent connections
- 🌏 **Perfect Chinese Support** - Fixed Windows console encoding issues
- 🔧 **Environment Variable Support** - Use `CLASH_VERGE_CONFIG_PATH` for flexible config
- ⏱️ **Optimized Timeouts** - Separate connection (3s) and read (5s) timeouts

## Features

### 📋 Profile Management
- List, add, delete, and activate profiles
- Support for URL-based subscription profiles
- Quick profile switching by name or UID

### 🌐 Proxy Management
- List all proxies and proxy groups
- Test proxy latency with **parallel testing** (5-10x faster)
- Select specific proxy for any group
- **Auto-select fastest node** - NEW!
- Auto node optimization

### 🔌 System Proxy Control
- Enable/disable system proxy
- Toggle TUN mode
- View proxy guard status

### 📊 Traffic Monitoring
- Real-time upload/download statistics
- Display in human-readable format (GB)
- Traffic data per profile

### 🛡️ Guardian Mode
- Auto-monitor API connectivity
- Automatic node switching on timeout
- Configurable latency thresholds

### 💾 Backup & Restore
- One-click configuration backup
- Restore from previous backups
- Multiple backup slots

### 📝 Logs & Diagnostics
- View real-time logs
- Search logs by keyword
- Health check for APIs

### ⚙️ Advanced Configuration
- Port configuration (HTTP/SOCKS/Mixed/Redir)
- DNS settings display
- Routing rules inspection
- Direct config file editing

## Installation

### Windows

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Run directly
python clash_verge_cli_windows.py --help
```

**Environment Variable (Optional):**
```powershell
# Set custom config path
$env:CLASH_VERGE_CONFIG_PATH = "D:\MyClash\config"
```

**First Run**: On first run, the Windows version will auto-detect your Clash Verge installation. If not found, it will prompt you to enter the config path manually.

Default Windows paths:
```
%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\
%APPDATA%\clash-verge-rev\
%LOCALAPPDATA%\clash-verge-rev\
C:\Program Files\Clash Verge\
```

### macOS

```bash
# Install Python dependencies
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- click >= 8.0.0
- pyyaml >= 6.0
- requests >= 2.28.0

### Install as CLI

```bash
# Make executable
chmod +x clash_verge_cli.py

# Option 1: Run directly
./clash_verge_cli.py --help

# Option 2: Add to PATH
sudo ln -s $(pwd)/clash_verge_cli.py /usr/local/bin/clash-verge
clash-verge --help
```

## Usage

### Quick Start

```bash
# Show status
python clash_verge_cli.py status

# List profiles
python clash_verge_cli.py profiles

# Activate profile
python clash_verge_cli.py activate "my-profile"

# Test proxy latency (parallel, fast!)
python clash_verge_cli.py test "节点选择" --limit 10

# Auto-select fastest proxy (NEW!)
python clash_verge_cli.py auto-select "节点选择" --limit 15
```

### 🚀 New: Auto-Select Fastest Node

Automatically test multiple proxies in parallel and select the fastest one:

```bash
# Test top 10 proxies and auto-select the fastest
python clash_verge_cli_windows.py auto-select "节点选择" --limit 10

# With JSON output for scripting
python clash_verge_cli_windows.py auto-select "节点选择" --limit 10 --json
```

**Performance:**
- Tests 10 nodes in ~8 seconds (vs ~50 seconds serial)
- Automatically selects the lowest latency node
- Perfect for automation and scheduled tasks

### Command Reference

| Command | Description |
|---------|-------------|
| `status` | Show comprehensive status |
| `profiles` | List all profiles |
| `activate <name>` | Switch to profile |
| `add <url>` | Add profile from URL |
| `delete <name>` | Delete profile |
| `proxies` | List all proxies |
| `test <group>` | Test latency for group (parallel) |
| `auto-select <group>` | **NEW** Auto-select fastest proxy |
| `select <group> <proxy>` | Select proxy |
| `sysproxy` | Show system proxy status |
| `sysproxy_set on/off/toggle` | Control system proxy |
| `tun on/off/toggle` | Control TUN mode |
| `ports` | Show port configuration |
| `port_set <type> <port>` | Set port |
| `traffic` | Show traffic stats |
| `backup` | Create backup |
| `backups` | List backups |
| `restore <name>` | Restore backup |
| `logs` | Show logs |
| `loggrep <keyword>` | Search logs |
| `guardian` | Auto-heal mode |
| `health` | Quick health check |
| `restart` | Restart Clash Verge |
| `open_dir` | Open config folder |
| `config` | Show Clash config |
| `vergecfg` | Show Verge config |

### JSON Output

All commands support `--json` flag for programmatic use:

```bash
python clash_verge_cli.py status --json
python clash_verge_cli.py proxies --json
python clash_verge_cli.py traffic --json
```

### Guardian Mode

Auto-monitor and heal when API fails:

```bash
# Run once
python clash_verge_cli.py guardian --once

# Run continuously (default 120s interval)
python clash_verge_cli.py guardian

# Custom interval and latency threshold
python clash_verge_cli.py guardian --interval 60 --max-latency 2000
```

## Configuration

Default config directory:
```
~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/
```

Key files:
- `profiles.yaml` - Profile management
- `verge.yaml` - Verge settings
- `clash-verge.yaml` - Clash core config

## 📝 Changelog

### v1.1.0 (2024-06-21)

**New Features:**
- ✨ Added `auto-select` command for automatic fastest node selection
- ⚡ Parallel latency testing (5-10x faster than serial)
- 🔧 Environment variable support: `CLASH_VERGE_CONFIG_PATH`

**Improvements:**
- 🌏 Fixed Windows console encoding - perfect Chinese support
- ⏱️ Optimized API timeouts (connection: 3s, read: 5s)
- 📦 Auto-detect `io.github.clash-verge-rev.clash-verge-rev` path
- 📚 Added comprehensive Chinese documentation

**Performance:**
- Testing 10 nodes: 50s → 8s (6x improvement)

### v1.0.0 (Initial Release)

- Basic profile management
- Proxy control and selection
- System proxy and TUN mode control
- Traffic monitoring
- Backup and restore
- Log viewing and searching

## Examples

### Daily Usage

```bash
# Morning health check
clash-verge health

# Auto-select fastest node for main groups
clash-verge auto-select "节点选择" --limit 15
clash-verge auto-select "ChatGPT" --limit 10
clash-verge auto-select "Gemini" --limit 10

# Check traffic
clash-verge traffic

# Create backup before changes
clash-verge backup
```

### Automation

```bash
# Cron job for health check
*/5 * * * * /usr/local/bin/clash-verge health >> /var/log/clash.log 2>&1

# Auto-switch on failure (via guardian)
clash-verge guardian --interval 300
```

### Windows Automation

```powershell
# Create auto-optimize.bat for daily use
@echo off
python clash_verge_cli_windows.py auto-select "节点选择" --limit 15
python clash_verge_cli_windows.py auto-select "ChatGPT" --limit 10
echo Optimization complete!
pause
```

## License

MIT License

## 📚 Documentation

- [安装说明.md](./安装说明.md) - 详细的安装和使用指南（中文）
- [优化建议.md](./优化建议.md) - 完整的优化建议和最佳实践（中文）
- [优化完成报告.md](./优化完成报告.md) - v1.1.0 优化详细报告（中文）

## Author

Clash Verge CLI - Enhanced Edition
