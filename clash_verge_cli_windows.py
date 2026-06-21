#!/usr/bin/env python3
"""
Clash Verge CLI - Windows Edition
A comprehensive command-line interface for Clash Verge VPN client on Windows
"""

import os
import sys
import yaml
import json
import subprocess
import click
import time
import requests
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import functools

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def output_json(f):
    """Decorator to add JSON output support"""
    @click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        as_json = kwargs.pop('as_json')
        result = f(*args, **kwargs)
        if as_json:
            if hasattr(result, '__dict__'):
                result = vars(result)
            elif not isinstance(result, dict):
                result = {'result': result}
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        return result
    return wrapper


def get_clash_verge_path() -> Path:
    """Get Clash Verge config path - auto-detect or prompt user"""
    # 优先检查环境变量
    env_path = os.environ.get('CLASH_VERGE_CONFIG_PATH')
    if env_path:
        path = Path(env_path)
        if path.exists():
            click.echo(f"[*] Using config from env: {path}")
            return path
        else:
            click.echo(f"[!] Warning: CLASH_VERGE_CONFIG_PATH set but path not found: {path}")

    appdata = os.environ.get('APPDATA', '')
    localappdata = os.environ.get('LOCALAPPDATA', '')

    # 尝试多个可能的路径
    possible_paths = [
        Path(appdata) / 'io.github.clash-verge-rev.clash-verge-rev',
        Path(localappdata) / 'io.github.clash-verge-rev.clash-verge-rev',
        Path(appdata) / 'clash-verge-rev',
        Path(localappdata) / 'clash-verge-rev',
        Path("C:/Program Files/Clash Verge"),
        Path("C:/Program Files (x86)/Clash Verge"),
    ]

    for path in possible_paths:
        if path.exists():
            click.echo(f"[*] Found Clash Verge at: {path}")
            return path

    # 使用纯 ASCII 字符避免编码问题
    click.echo("[!] Clash Verge not found in default locations.")
    click.echo(f"Tried paths:")
    for path in possible_paths:
        click.echo(f"  - {path}")

    custom_path = click.prompt("Please enter Clash Verge config path", type=str)
    return Path(custom_path)


CONFIG_DIR = get_clash_verge_path()
PROFILES_DIR = CONFIG_DIR / "profiles"
VERGE_CONFIG = CONFIG_DIR / "verge.yaml"
CLASH_CONFIG = CONFIG_DIR / "clash-verge.yaml"
BACKUP_DIR = CONFIG_DIR / "clash-verge-rev-backup"


class ClashVergeCLI:
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.profiles_dir = PROFILES_DIR
        self.verge_config = VERGE_CONFIG
        self.clash_config = CLASH_CONFIG
        self.backup_dir = BACKUP_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_yaml(self, file_path: Path) -> Dict:
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def save_yaml(self, file_path: Path, data: Dict):
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def get_profiles(self) -> List[Dict]:
        profiles_yaml = self.config_dir / "profiles.yaml"
        if not profiles_yaml.exists():
            return []
        data = self.load_yaml(profiles_yaml)
        items = data.get('items', [])
        current_uid = data.get('current')
        profiles = []
        for item in items:
            item['is_current'] = item.get('uid') == current_uid
            profiles.append(item)
        return profiles
    
    def get_current_profile(self) -> Optional[Dict]:
        profiles_yaml = self.config_dir / "profiles.yaml"
        if not profiles_yaml.exists():
            return None
        data = self.load_yaml(profiles_yaml)
        current_uid = data.get('current')
        items = data.get('items', [])
        for item in items:
            if item.get('uid') == current_uid:
                return item
        return None
    
    def get_clash_config(self) -> Dict:
        return self.load_yaml(self.clash_config)
    
    def get_verge_config(self) -> Dict:
        return self.load_yaml(self.verge_config)
    
    def save_verge_config(self, config: Dict):
        self.save_yaml(self.verge_config, config)
    
    def get_proxies(self) -> Dict:
        clash = self.get_clash_config()
        return clash.get('proxies', {})
    
    def get_proxy_groups(self) -> List[Dict]:
        clash = self.get_clash_config()
        return clash.get('proxy-groups', [])
    
    def test_proxy_latency(self, proxy_url: str, test_url: str = None) -> Optional[int]:
        if test_url is None:
            test_url = self.get_verge_config().get('default_latency_test', 'https://api.minimax.io/anthropic')
        try:
            proxies = {'http': proxy_url, 'https': proxy_url}
            start = time.time()
            # 连接超时 3 秒，读取超时 5 秒
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=(3, 5),
                allow_redirects=False
            )
            latency = int((time.time() - start) * 1000)
            return latency if response.status_code == 200 else None
        except Exception as e:
            return None
    
    def get_system_proxy_status(self) -> Dict:
        verge = self.get_verge_config()
        return {
            'system_proxy': verge.get('enable_system_proxy', False),
            'tun_mode': verge.get('enable_tun_mode', False),
            'proxy_guard': verge.get('enable_proxy_guard', False),
        }
    
    def set_system_proxy(self, enabled: bool) -> bool:
        verge = self.get_verge_config()
        verge['enable_system_proxy'] = enabled
        self.save_verge_config(verge)
        return enabled
    
    def set_tun_mode(self, enabled: bool) -> bool:
        verge = self.get_verge_config()
        verge['enable_tun_mode'] = enabled
        self.save_verge_config(verge)
        return enabled
    
    def get_dns_config(self) -> Dict:
        clash = self.get_clash_config()
        return clash.get('dns', {})
    
    def get_rules(self) -> List[Dict]:
        clash = self.get_clash_config()
        rules = clash.get('rules', [])
        result = []
        for rule in rules:
            if isinstance(rule, str):
                parts = rule.split(',')
                result.append({
                    'type': parts[0].strip() if parts else 'UNKNOWN',
                    'value': parts[1].strip() if len(parts) > 1 else '',
                    'payload': ','.join(parts[2:]).strip() if len(parts) > 2 else ''
                })
        return result
    
    def get_traffic_stats(self) -> Dict:
        current = self.get_current_profile()
        if not current:
            return {}
        extra = current.get('extra', {})
        return {
            'upload': extra.get('upload', 0),
            'download': extra.get('download', 0),
            'total': extra.get('total', 0),
            'upload_gb': round(extra.get('upload', 0) / (1024**3), 2),
            'download_gb': round(extra.get('download', 0) / (1024**3), 2),
            'total_gb': round(extra.get('total', 0) / (1024**3), 2),
        }
    
    def create_backup(self, name: str = None) -> str:
        if not name:
            name = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / name
        backup_path.mkdir(parents=True, exist_ok=True)
        for file in ['profiles.yaml', 'verge.yaml', 'clash-verge.yaml']:
            src = self.config_dir / file
            if src.exists():
                dst = backup_path / file
                dst.write_text(src.read_text())
        return str(backup_path)
    
    def list_backups(self) -> List[Dict]:
        if not self.backup_dir.exists():
            return []
        backups = []
        for item in sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if item.is_dir():
                backups.append({
                    'name': item.name,
                    'path': str(item),
                    'created': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        return backups
    
    def restore_backup(self, name: str) -> bool:
        backup_path = self.backup_dir / name
        if not backup_path.exists():
            return False
        for file in ['profiles.yaml', 'verge.yaml', 'clash-verge.yaml']:
            src = backup_path / file
            if src.exists():
                dst = self.config_dir / file
                dst.write_text(src.read_text())
        return True
    
    def get_logs(self, lines: int = 50) -> List[str]:
        logs_dir = self.config_dir / "logs"
        if not logs_dir.exists():
            return []
        log_files = list(logs_dir.glob("*.log"))
        if not log_files:
            return []
        latest_log = max(log_files, key=os.path.getctime)
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                return f.readlines()[-lines:]
        except:
            return []
    
    def get_web_ui_list(self) -> List[Dict]:
        verge = self.get_verge_config()
        return verge.get('web_ui_list', []) or []
    
    def get_ports(self) -> Dict:
        verge = self.get_verge_config()
        return {
            'http_port': verge.get('verge_port'),
            'socks_port': verge.get('verge_socks_port'),
            'mixed_port': verge.get('verge_mixed_port'),
            'redir_port': verge.get('verge_redir_port'),
            'enable_http': verge.get('verge_http_enabled'),
            'enable_socks': verge.get('verge_socks_enabled'),
            'enable_redir': verge.get('verge_redir_enabled'),
        }
    
    def set_port(self, port_type: str, port: int, enabled: bool = None) -> Dict:
        verge = self.get_verge_config()
        mapping = {
            'http': ('verge_port', 'verge_http_enabled'),
            'socks': ('verge_socks_port', 'verge_socks_enabled'),
            'mixed': ('verge_mixed_port', None),
            'redir': ('verge_redir_port', 'verge_redir_enabled'),
        }
        if port_type not in mapping:
            return {'error': f'Unknown port type: {port_type}'}
        port_key, enable_key = mapping[port_type]
        verge[port_key] = port
        if enabled is not None and enable_key:
            verge[enable_key] = enabled
        self.save_verge_config(verge)
        return self.get_ports()

    def test_proxies_parallel(self, proxies_info: List[Dict], test_url: str = None, max_workers: int = 10) -> Dict[str, Optional[int]]:
        """并行测试多个代理的延迟"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if test_url is None:
            test_url = self.get_verge_config().get('default_latency_test', 'https://api.minimax.io/anthropic')

        results = {}

        def test_one_proxy(proxy_info):
            name = proxy_info['name']
            proxy = proxy_info['proxy']
            ptype = proxy.get('type', '')

            # 构建代理 URL
            if ptype == 'ss':
                proxy_url = f"ss://{proxy.get('cipher')}:{proxy.get('password')}@{proxy.get('server')}:{proxy.get('port')}"
            elif ptype == 'vmess':
                proxy_url = f"vmess://{proxy.get('password')}@{proxy.get('server')}:{proxy.get('port')}"
            else:
                proxy_url = f"{ptype}://{proxy.get('server')}:{proxy.get('port')}"

            latency = self.test_proxy_latency(proxy_url, test_url)
            return name, latency

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(test_one_proxy, proxy_info): proxy_info['name']
                for proxy_info in proxies_info
            }

            for future in as_completed(future_to_proxy):
                try:
                    name, latency = future.result()
                    results[name] = latency
                except Exception as e:
                    name = future_to_proxy[future]
                    results[name] = None

        return results

    def select_proxy(self, group_name: str, proxy_name: str) -> bool:
        """为指定代理组选择代理节点"""
        clash = self.get_clash_config()
        groups = clash.get('proxy-groups', [])

        for g in groups:
            if g.get('name') == group_name:
                proxies = g.get('proxies', [])
                if proxy_name in proxies:
                    proxies.remove(proxy_name)
                    proxies.insert(0, proxy_name)
                    g['proxies'] = proxies
                    self.save_yaml(self.clash_config, clash)
                    return True
        return False


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Clash Verge CLI - Windows Edition"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = ClashVergeCLI()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def status(ctx, as_json):
    """Show comprehensive status"""
    client = ctx.obj['client']
    current = client.get_current_profile()
    traffic = client.get_traffic_stats()
    sys_proxy = client.get_system_proxy_status()
    ports = client.get_ports()
    
    if as_json:
        result = {
            'config_dir': str(client.config_dir),
            'profiles_count': len(client.get_profiles()),
            'current_profile': None,
            'traffic': traffic,
            'system_proxy': sys_proxy,
            'ports': ports
        }
        if current:
            result['current_profile'] = {
                'name': current.get('name') or current.get('file'),
                'type': current.get('type'),
                'uid': current.get('uid'),
                'selected': current.get('selected', [])
            }
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    click.echo("=== Clash Verge Status (Windows) ===")
    click.echo(f"[DIR] Config: {client.config_dir}")
    click.echo(f"[LIST] Profiles: {len(client.get_profiles())}")
    if current:
        click.echo(f"\n[*] Active: {current.get('name') or current.get('file')}")
        for sel in current.get('selected', []):
            click.echo(f"   * {sel.get('name')}: {sel.get('now')}")
    click.echo(f"\n[STATS] Traffic: UP:{traffic.get('upload_gb', 0)}GB DOWN:{traffic.get('download_gb', 0)}GB")
    click.echo(f"\n[PROXY] Proxy: HTTP:{ports.get('http_port')} SOCKS:{ports.get('socks_port')} Mixed:{ports.get('mixed_port')}")
    click.echo(f"   System: {'ON' if sys_proxy.get('system_proxy') else 'OFF'} | TUN: {'ON' if sys_proxy.get('tun_mode') else 'OFF'}")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def profiles(ctx, as_json):
    """List all profiles"""
    client = ctx.obj['client']
    profiles = client.get_profiles()
    if not profiles:
        if as_json:
            click.echo(json.dumps([], ensure_ascii=False))
        else:
            click.echo("No profiles found")
        return
    if as_json:
        result = [{'name': p.get('name') or p.get('file'), 'type': p.get('type'), 'uid': p.get('uid'), 'is_current': p.get('is_current'), 'url': p.get('url')} for p in profiles]
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    click.echo("=== Profiles ===")
    for i, p in enumerate(profiles, 1):
        name = p.get('name') or p.get('file', f'Profile {i}')
        status = "[*] ACTIVE" if p.get('is_current') else "[ ]"
        click.echo(f"{i}. {name} [{p.get('type')}] {status}")


@cli.command()
@click.argument('profile_name')
@click.pass_context
def activate(ctx, profile_name):
    """Activate a profile by name or UID"""
    client = ctx.obj['client']
    profiles = client.get_profiles()
    target = None
    for p in profiles:
        if p.get('name') == profile_name or p.get('file', '').replace('.yaml', '').replace('.js', '') == profile_name or p.get('uid') == profile_name:
            target = p
            break
    if not target:
        click.echo(f"[X] Profile '{profile_name}' not found")
        return
    profiles_yaml = client.config_dir / "profiles.yaml"
    data = client.load_yaml(profiles_yaml)
    data['current'] = target['uid']
    client.save_yaml(profiles_yaml, data)
    verge = client.load_yaml(client.verge_config)
    verge['current_profile'] = target['uid']
    client.save_yaml(client.verge_config, verge)
    click.echo(f"[OK] Switched to: {target.get('name') or target.get('file')}")


@cli.command()
@click.argument('profile_url')
@click.option('--name', help='Profile name')
@click.pass_context
def add(ctx, profile_url, name):
    """Add a profile from URL"""
    client = ctx.obj['client']
    try:
        click.echo(f"[DOWN] Downloading: {profile_url}")
        response = requests.get(profile_url, timeout=10)
        response.raise_for_status()
        content = response.text
        profiles_yaml = client.config_dir / "profiles.yaml"
        data = client.load_yaml(profiles_yaml)
        if not name:
            name = datetime.now().strftime('profile_%Y%m%d%H%M%S')
        uid = f"url_{int(time.time())}"
        profile_file = client.profiles_dir / f"{uid}.yaml"
        profile_file.write_text(content)
        if 'items' not in data:
            data['items'] = []
        data['items'].append({'uid': uid, 'name': name, 'type': 'url', 'url': profile_url, 'file': f"{uid}.yaml"})
        client.save_yaml(profiles_yaml, data)
        click.echo(f"[OK] Added profile: {name}")
    except Exception as e:
        click.echo(f"[X] Error: {e}")


@cli.command()
@click.argument('profile_name')
@click.pass_context
def delete(ctx, profile_name):
    """Delete a profile"""
    client = ctx.obj['client']
    profiles = client.get_profiles()
    target = None
    for p in profiles:
        if p.get('name') == profile_name or p.get('uid') == profile_name:
            target = p
            break
    if not target:
        click.echo(f"[X] Profile '{profile_name}' not found")
        return
    current = client.get_current_profile()
    if current and current.get('uid') == target.get('uid'):
        click.echo("[X] Cannot delete active profile")
        return
    profiles_yaml = client.config_dir / "profiles.yaml"
    data = client.load_yaml(profiles_yaml)
    data['items'] = [p for p in data.get('items', []) if p.get('uid') != target.get('uid')]
    client.save_yaml(profiles_yaml, data)
    profile_file = client.profiles_dir / f"{target.get('uid')}.yaml"
    if profile_file.exists():
        profile_file.unlink()
    click.echo(f"[OK] Deleted: {target.get('name')}")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.option('--group', help='Filter by proxy group')
@click.pass_context
def proxies(ctx, as_json, group):
    """List all proxies"""
    client = ctx.obj['client']
    clash = client.get_clash_config()
    all_proxies = clash.get('proxies', {})
    groups = clash.get('proxy-groups', [])
    if as_json:
        result = {'proxies': {k: v for k, v in all_proxies.items() if k not in ['DIRECT', 'REJECT']}, 'groups': [{'name': g.get('name'), 'type': g.get('type'), 'proxies': g.get('proxies', [])} for g in groups]}
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    click.echo("=== Proxy Groups ===")
    for g in groups:
        if group and g.get('name') != group:
            continue
        click.echo(f"\n[FOLDER] {g.get('name')} [{g.get('type')}]")
        for p in g.get('proxies', [])[:10]:
            click.echo(f"   * {p}")


@cli.command()
@click.argument('group_name')
@click.option('--limit', default=5, help='Number of proxies to test')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def test(ctx, group_name, limit, as_json):
    """Test proxy latency for a group (parallel)"""
    client = ctx.obj['client']
    clash = client.get_clash_config()
    groups = clash.get('proxy-groups', [])
    target_group = None
    for g in groups:
        if g.get('name') == group_name:
            target_group = g
            break
    if not target_group:
        click.echo(f"[X] Group '{group_name}' not found")
        return

    proxies_list = target_group.get('proxies', [])
    all_proxies = clash.get('proxies', {})

    # 准备要测试的代理信息
    proxies_to_test = []
    for proxy_name in proxies_list[:limit]:
        if proxy_name in ['DIRECT', 'REJECT', 'fallback', 'url-test']:
            continue
        proxy = all_proxies.get(proxy_name, {})
        if proxy:
            proxies_to_test.append({'name': proxy_name, 'proxy': proxy})

    if not proxies_to_test:
        click.echo("[!] No valid proxies to test")
        return

    # 并行测试延迟
    if not as_json:
        click.echo(f"[*] Testing {len(proxies_to_test)} proxies in parallel...")

    results_dict = client.test_proxies_parallel(proxies_to_test)

    # 构建结果列表
    results = []
    for proxy_name, latency in results_dict.items():
        proxy = all_proxies.get(proxy_name, {})
        results.append({
            'name': proxy_name,
            'server': proxy.get('server'),
            'latency_ms': latency
        })

    if as_json:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return

    click.echo(f"\n=== Latency Test: {group_name} ===")
    for r in sorted(results, key=lambda x: x['latency_ms'] or 99999):
        lat = f"{r['latency_ms']}ms" if r['latency_ms'] else "timeout"
        click.echo(f"   {r['name']}: {lat}")



@cli.command()
@click.argument('group_name')
@click.argument('proxy_name')
@click.pass_context
def select(ctx, group_name, proxy_name):
    """Select a proxy for a group"""
    client = ctx.obj['client']
    if client.select_proxy(group_name, proxy_name):
        click.echo(f"[OK] Selected {proxy_name} for {group_name}")
    else:
        click.echo(f"[X] Failed to select {proxy_name} for {group_name}")


@cli.command('auto-select')
@click.argument('group_name')
@click.option('--limit', default=10, help='Test top N proxies')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def auto_select(ctx, group_name, limit, as_json):
    """Auto-select the fastest proxy for a group"""
    client = ctx.obj['client']
    clash = client.get_clash_config()
    groups = clash.get('proxy-groups', [])
    target_group = None

    for g in groups:
        if g.get('name') == group_name:
            target_group = g
            break

    if not target_group:
        if as_json:
            click.echo(json.dumps({'error': f'Group not found: {group_name}'}, ensure_ascii=False))
        else:
            click.echo(f"[X] Group '{group_name}' not found")
        return

    proxies_list = target_group.get('proxies', [])
    all_proxies = clash.get('proxies', {})

    # 准备要测试的代理信息
    proxies_to_test = []
    for proxy_name in proxies_list[:limit]:
        if proxy_name in ['DIRECT', 'REJECT', 'fallback', 'url-test']:
            continue
        proxy = all_proxies.get(proxy_name, {})
        if proxy:
            proxies_to_test.append({'name': proxy_name, 'proxy': proxy})

    if not proxies_to_test:
        if as_json:
            click.echo(json.dumps({'error': 'No valid proxies to test'}, ensure_ascii=False))
        else:
            click.echo("[!] No valid proxies to test")
        return

    # 并行测试延迟
    if not as_json:
        click.echo(f"[*] Testing {len(proxies_to_test)} proxies...")

    results_dict = client.test_proxies_parallel(proxies_to_test)

    # 找到延迟最低的节点
    valid_results = [(name, latency) for name, latency in results_dict.items() if latency is not None]

    if not valid_results:
        if as_json:
            click.echo(json.dumps({'error': 'No proxy available'}, ensure_ascii=False))
        else:
            click.echo("[X] No proxy available (all timeout)")
        return

    fastest = min(valid_results, key=lambda x: x[1])
    fastest_name, fastest_latency = fastest

    # 自动选择最快的节点
    if client.select_proxy(group_name, fastest_name):
        result = {
            'group': group_name,
            'selected': fastest_name,
            'latency_ms': fastest_latency,
            'tested': len(proxies_to_test),
            'available': len(valid_results)
        }

        if as_json:
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            click.echo(f"\n[OK] Auto-selected fastest proxy:")
            click.echo(f"   Group: {group_name}")
            click.echo(f"   Proxy: {fastest_name}")
            click.echo(f"   Latency: {fastest_latency}ms")
            click.echo(f"   Tested: {len(proxies_to_test)} proxies, {len(valid_results)} available")
    else:
        if as_json:
            click.echo(json.dumps({'error': 'Failed to select proxy'}, ensure_ascii=False))
        else:
            click.echo(f"[X] Failed to select {fastest_name}")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def sysproxy(ctx, as_json):
    """Show system proxy status"""
    client = ctx.obj['client']
    status = client.get_system_proxy_status()
    if as_json:
        click.echo(json.dumps(status, ensure_ascii=False, indent=2))
        return
    click.echo("=== System Proxy Status ===")
    click.echo(f"System Proxy: {'ON' if status.get('system_proxy') else 'OFF'}")
    click.echo(f"TUN Mode: {'ON' if status.get('tun_mode') else 'OFF'}")
    click.echo(f"Proxy Guard: {'ON' if status.get('proxy_guard') else 'OFF'}")


@cli.command()
@click.argument('action', type=click.Choice(['on', 'off', 'toggle']))
@click.pass_context
def sysproxy_set(ctx, action):
    """Control system proxy (on/off/toggle)"""
    client = ctx.obj['client']
    status = client.get_system_proxy_status()
    if action == 'toggle':
        new_state = not status.get('system_proxy')
    elif action == 'on':
        new_state = True
    else:
        new_state = False
    client.set_system_proxy(new_state)
    click.echo(f"[OK] System Proxy: {'ON' if new_state else 'OFF'}")


@cli.command()
@click.argument('action', type=click.Choice(['on', 'off', 'toggle']))
@click.pass_context
def tun(ctx, action):
    """Control TUN mode (on/off/toggle)"""
    client = ctx.obj['client']
    status = client.get_system_proxy_status()
    if action == 'toggle':
        new_state = not status.get('tun_mode')
    elif action == 'on':
        new_state = True
    else:
        new_state = False
    client.set_tun_mode(new_state)
    click.echo(f"[OK] TUN Mode: {'ON' if new_state else 'OFF'}")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def ports(ctx, as_json):
    """Show port configuration"""
    client = ctx.obj['client']
    ports = client.get_ports()
    if as_json:
        click.echo(json.dumps(ports, ensure_ascii=False, indent=2))
        return
    click.echo("=== Port Configuration ===")
    click.echo(f"HTTP Port: {ports.get('http_port')} {'(enabled)' if ports.get('enable_http') else '(disabled)'}")
    click.echo(f"SOCKS Port: {ports.get('socks_port')} {'(enabled)' if ports.get('enable_socks') else '(disabled)'}")
    click.echo(f"Mixed Port: {ports.get('mixed_port')}")
    click.echo(f"Redir Port: {ports.get('redir_port')} {'(enabled)' if ports.get('enable_redir') else '(disabled)'}")


@cli.command()
@click.argument('port_type', type=click.Choice(['http', 'socks', 'mixed', 'redir']))
@click.argument('port', type=int)
@click.option('--enable/--disable', default=None, help='Enable or disable')
@click.pass_context
def port_set(ctx, port_type, port, enable):
    """Set port (http/socks/mixed/redir)"""
    client = ctx.obj['client']
    result = client.set_port(port_type, port, enable)
    if 'error' in result:
        click.echo(f"[X] {result['error']}")
    else:
        click.echo(f"[OK] {port_type.upper()} port set to {port}")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def dns(ctx, as_json):
    """Show DNS configuration"""
    client = ctx.obj['client']
    dns = client.get_dns_config()
    if as_json:
        click.echo(json.dumps(dns, ensure_ascii=False, indent=2))
        return
    click.echo("=== DNS Configuration ===")
    click.echo(yaml.dump(dns, default_flow_style=False, allow_unicode=True))


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.option('--type', 'rule_type', help='Filter by rule type')
@click.option('--limit', default=20, help='Number of rules to show')
@click.pass_context
def rules(ctx, as_json, rule_type, limit):
    """Show routing rules"""
    client = ctx.obj['client']
    rules = client.get_rules()
    if rule_type:
        rules = [r for r in rules if r.get('type') == rule_type]
    rules = rules[:limit]
    if as_json:
        click.echo(json.dumps(rules, ensure_ascii=False, indent=2))
        return
    click.echo("=== Routing Rules ===")
    for r in rules:
        click.echo(f"{r.get('type'):20} {r.get('value')[:50]}")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def traffic(ctx, as_json):
    """Show traffic statistics"""
    client = ctx.obj['client']
    traffic = client.get_traffic_stats()
    if as_json:
        click.echo(json.dumps(traffic, ensure_ascii=False, indent=2))
        return
    click.echo("=== Traffic Statistics ===")
    click.echo(f"Upload:   {traffic.get('upload_gb', 0)} GB")
    click.echo(f"Download: {traffic.get('download_gb', 0)} GB")
    click.echo(f"Total:    {traffic.get('total_gb', 0)} GB")


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def backups(ctx, as_json):
    """List all backups"""
    client = ctx.obj['client']
    backups = client.list_backups()
    if as_json:
        click.echo(json.dumps(backups, ensure_ascii=False, indent=2))
        return
    click.echo("=== Backups ===")
    for b in backups:
        click.echo(f"* {b.get('name')} - {b.get('created')}")


@cli.command()
@click.argument('name', required=False)
@click.pass_context
def backup(ctx, name):
    """Create a backup"""
    client = ctx.obj['client']
    backup_path = client.create_backup(name)
    click.echo(f"[OK] Backup created: {backup_path}")


@cli.command()
@click.argument('name')
@click.pass_context
def restore(ctx, name):
    """Restore from a backup"""
    client = ctx.obj['client']
    if client.restore_backup(name):
        click.echo(f"[OK] Restored from: {name}")
    else:
        click.echo(f"[X] Backup not found: {name}")


@cli.command()
@click.option('--lines', default=50, help='Number of lines')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def logs(ctx, lines, as_json):
    """Show logs"""
    client = ctx.obj['client']
    log_lines = client.get_logs(lines)
    if as_json:
        click.echo(json.dumps(log_lines, ensure_ascii=False))
        return
    for line in log_lines:
        click.echo(line.rstrip())


@cli.command()
@click.argument('keyword')
@click.option('--lines', default=100, help='Search range')
@click.pass_context
def loggrep(ctx, keyword, lines):
    """Search logs for keyword"""
    client = ctx.obj['client']
    log_lines = client.get_logs(lines)
    matched = [l for l in log_lines if keyword.lower() in l.lower()]
    click.echo(f"=== Found {len(matched)} matches ===")
    for line in matched[-20:]:
        click.echo(line.rstrip())


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def config(ctx, as_json):
    """Show Clash configuration"""
    client = ctx.obj['client']
    clash = client.get_clash_config()
    if as_json:
        click.echo(json.dumps(clash, ensure_ascii=False, indent=2))
        return
    click.echo("=== Clash Configuration ===")
    click.echo(yaml.dump(clash, default_flow_style=False, allow_unicode=True))


@cli.command()
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
@click.pass_context
def vergecfg(ctx, as_json):
    """Show Verge configuration"""
    client = ctx.obj['client']
    verge = client.get_verge_config()
    if as_json:
        click.echo(json.dumps(verge, ensure_ascii=False, indent=2))
        return
    click.echo("=== Verge Configuration ===")
    safe_verge = {k: v for k, v in verge.items() if 'password' not in k.lower() and 'secret' not in k.lower()}
    click.echo(yaml.dump(safe_verge, default_flow_style=False, allow_unicode=True))


@cli.command()
@click.pass_context
def open_dir(ctx):
    """Open config directory"""
    subprocess.run(['explorer', str(ctx.obj['client'].config_dir)])


@cli.command()
@click.pass_context
def open_logs(ctx):
    """Open logs directory"""
    subprocess.run(['explorer', str(ctx.obj['client'].config_dir / "logs")])


@cli.command()
@click.pass_context
def refresh(ctx):
    """Force refresh configuration"""
    client = ctx.obj['client']
    profiles_yaml = client.config_dir / "profiles.yaml"
    if profiles_yaml.exists():
        os.utime(profiles_yaml, None)
    click.echo("[OK] Configuration refreshed")


@cli.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def set(ctx, key, value):
    """Set Verge config key"""
    client = ctx.obj['client']
    verge = client.get_verge_config()
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    elif value.isdigit():
        value = int(value)
    verge[key] = value
    client.save_verge_config(verge)
    click.echo(f"[OK] Set {key} = {value}")


@cli.command()
@click.pass_context
def path(ctx):
    """Show Clash Verge config path"""
    client = ctx.obj['client']
    click.echo(f"Config directory: {client.config_dir}")
    click.echo(f"Exists: {client.config_dir.exists()}")


@cli.command()
def health():
    """Quick health check"""
    import urllib.request
    import json
    try:
        req = urllib.request.Request('http://127.0.0.1:9097/configs')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            click.echo("[OK] Clash API: 在线")
    except Exception as e:
        click.echo(f"[X] Clash API: {e}")
    try:
        start = time.time()
        r = requests.get('https://api.minimax.io/anthropic', proxies={'http': 'socks5://127.0.0.1:7897', 'https': 'socks5://127.0.0.1:7897'}, timeout=5)
        latency = int((time.time() - start) * 1000)
        click.echo(f"[OK] MiniMax API: {latency}ms")
    except Exception as e:
        click.echo(f"[X] MiniMax API: {str(e)[:50]}")


if __name__ == '__main__':
    cli()
