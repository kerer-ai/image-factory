#!/usr/bin/env python3
"""
克隆配置文件中定义的所有源仓库
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path


def clone_sources(config_path: str, output_dir: str) -> bool:
    """
    解析配置并克隆所有源仓库

    Args:
        config_path: 配置文件路径
        output_dir: 输出目录

    Returns:
        bool: 是否成功
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    sources = config.get('sources', [])

    if not sources:
        print("Warning: No sources defined in config")
        return True

    for source in sources:
        name = source['name']
        url = source['url']
        ref = source.get('ref') or source.get('branch', 'main')

        target_dir = output_path / name

        # 如果目录已存在，跳过
        if target_dir.exists():
            print(f"Source {name} already exists, skipping...")
            continue

        print(f"Cloning {name} from {url} (ref: {ref})...")

        cmd = ['git', 'clone', '--depth', '1']
        if ref:
            cmd.extend(['--branch', ref])
        cmd.extend([url, str(target_dir)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error cloning {name}: {result.stderr}")
            return False

        print(f"Successfully cloned {name}")

        # 检查是否有 submodule，如果有则初始化
        gitmodules_path = target_dir / '.gitmodules'
        if gitmodules_path.exists():
            print(f"Initializing submodules for {name}...")
            submodule_cmd = ['git', 'submodule', 'update', '--init', '--recursive', '--depth', '1']
            result = subprocess.run(submodule_cmd, cwd=str(target_dir), capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error initializing submodules for {name}: {result.stderr}")
                return False
            print(f"Successfully initialized submodules for {name}")

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clone source repositories')
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--output', required=True, help='Output directory for cloned repos')

    args = parser.parse_args()

    success = clone_sources(
        config_path=args.config,
        output_dir=args.output
    )

    sys.exit(0 if success else 1)