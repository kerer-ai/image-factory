#!/usr/bin/env python3
"""
克隆配置文件中定义的所有源仓库
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path


def clone_sources(config_path: str, output_dir: str, repo_url: str = None, repo_branch: str = 'main') -> bool:
    """
    解析配置并克隆所有源仓库

    Args:
        config_path: 配置文件路径
        output_dir: 输出目录
        repo_url: 临时仓库 URL（可选，用于临时仓库构建模式）
        repo_branch: 临时仓库分支

    Returns:
        bool: 是否成功
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 临时仓库模式
    if repo_url:
        print(f"Temporary repo mode: {repo_url}")
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        target_dir = output_path / repo_name

        print(f"Cloning {repo_name} from {repo_url} (branch: {repo_branch})...")

        cmd = ['git', 'clone', '--depth', '1', '--branch', repo_branch, repo_url, str(target_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error cloning {repo_url}: {result.stderr}")
            return False

        print(f"Successfully cloned {repo_name}")
        return True

    # 配置驱动模式
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

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clone source repositories')
    parser.add_argument('--config', required=False, help='Path to images.yaml')
    parser.add_argument('--output', required=True, help='Output directory for cloned repos')
    parser.add_argument('--repo-url', help='Temporary repository URL')
    parser.add_argument('--repo-branch', default='main', help='Temporary repository branch')

    args = parser.parse_args()

    # 临时仓库模式不需要配置文件
    if not args.repo_url and not args.config:
        print("Error: Either --config or --repo-url is required")
        sys.exit(1)

    success = clone_sources(
        config_path=args.config,
        output_dir=args.output,
        repo_url=args.repo_url,
        repo_branch=args.repo_branch
    )

    sys.exit(0 if success else 1)