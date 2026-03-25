#!/usr/bin/env python3
"""
检测本次提交中变更的配置文件
用于 GitHub Actions 的 push 触发场景
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_changed_configs(base_ref: str = 'HEAD~1', config_pattern: str = 'config/*-images.yml') -> list:
    """
    获取变更的配置文件列表

    Args:
        base_ref: 基准引用，默认为 HEAD~1
        config_pattern: 配置文件模式

    Returns:
        变更的配置文件列表
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', base_ref, 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )

        changed_files = result.stdout.strip().split('\n')
        changed_files = [f for f in changed_files if f]

        # 过滤出变更的配置文件
        config_dir = config_pattern.split('/')[0]
        changed_configs = [
            f for f in changed_files
            if f.startswith(config_dir + '/') and f.endswith('-images.yml')
        ]

        return changed_configs

    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description='Detect changed config files')
    parser.add_argument('--base', default='HEAD~1', help='Base ref for comparison')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    configs = get_changed_configs(base_ref=args.base)

    if args.json:
        result = {'configs': configs}
        print(json.dumps(result))
    else:
        if configs:
            print("Changed configs:")
            for cfg in configs:
                print(f"  - {cfg}")
        else:
            print("No config changes detected")


if __name__ == '__main__':
    main()