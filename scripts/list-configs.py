#!/usr/bin/env python3
"""
列出 config/ 目录下所有可用的配置文件
"""

import json
from pathlib import Path


def list_configs(config_dir: str = 'config') -> list:
    """扫描配置目录，返回所有 *-images.yml 文件"""
    config_path = Path(config_dir)
    if not config_path.exists():
        return []

    configs = sorted(config_path.glob('*-images.yml'))
    return [c.name for c in configs]


def main():
    configs = list_configs()

    # 输出 JSON 格式供 GitHub Actions 使用
    result = {'configs': configs}
    print(json.dumps(result))

    # 也输出可读格式
    if configs:
        print("\nAvailable configs:", file=__import__('sys').stderr)
        for cfg in configs:
            print(f"  - {cfg}", file=__import__('sys').stderr)


if __name__ == '__main__':
    main()