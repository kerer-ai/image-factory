#!/usr/bin/env python3
"""
扫描配置文件中定义的 Dockerfile，生成构建矩阵
"""

import argparse
import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def get_runner_for_platform(platform: str) -> str:
    """根据平台选择合适的 runner"""
    platform_runners = {
        'linux/amd64': 'ubuntu-latest',
        'linux/arm64': 'ubuntu-22.04-arm',
    }
    return platform_runners.get(platform, 'ubuntu-latest')


def parse_dockerfile_metadata(dockerfile_path: Path) -> Dict[str, Any]:
    """从 Dockerfile 注释中提取元数据"""

    metadata = {
        'name': None,
        'tags': [],
        'platforms': ['linux/amd64', 'linux/arm64'],
        'build_args': {}
    }

    if not dockerfile_path.exists():
        return metadata

    with open(dockerfile_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('#'):
                break

            # 解析 image-name
            match = re.match(r'#\s*image-name:\s*(.+)', line)
            if match:
                metadata['name'] = match.group(1).strip()

            # 解析 image-tags
            match = re.match(r'#\s*image-tags:\s*(.+)', line)
            if match:
                metadata['tags'] = [t.strip() for t in match.group(1).split(',')]

            # 解析 platforms
            match = re.match(r'#\s*platforms:\s*(.+)', line)
            if match:
                metadata['platforms'] = [p.strip() for p in match.group(1).split(',')]

    return metadata


def resolve_template_variables(tag: str, commit_sha: str, branch: str) -> str:
    """解析标签模板变量"""

    replacements = {
        '{{ sha_short }}': commit_sha[:7] if commit_sha else 'unknown',
        '{{ sha }}': commit_sha if commit_sha else 'unknown',
        '{{ date }}': datetime.now().strftime('%Y%m%d'),
        '{{ branch }}': branch
    }

    for var, value in replacements.items():
        tag = tag.replace(var, value)

    return tag


def get_commit_sha(source_dir: Path) -> str:
    """获取仓库的 commit SHA"""

    import subprocess

    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=str(source_dir),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return 'unknown'


def process_config(config_path: str, sources_path: Path) -> List[Dict[str, Any]]:
    """处理单个配置文件，返回构建矩阵列表"""

    matrix = []

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 获取全局默认配置
    global_registry = config.get('registry', 'quay.io')
    global_org = config.get('org', 'kerer')

    for image_config in config.get('images', []):
        source_name = image_config['source']
        source_dir = sources_path / source_name

        if not source_dir.exists():
            print(f"Warning: Source {source_name} not found")
            continue

        dockerfile_rel = image_config.get('dockerfile', 'Dockerfile')
        dockerfile_path = source_dir / dockerfile_rel

        if not dockerfile_path.exists():
            print(f"Warning: Dockerfile not found: {dockerfile_path}")
            continue

        commit_sha = get_commit_sha(source_dir)
        branch = next((s.get('branch', 'main') for s in config.get('sources', []) if s['name'] == source_name), 'main')

        # 解析元数据
        metadata = parse_dockerfile_metadata(dockerfile_path)

        # 确定镜像名
        image_name = image_config['name'] or metadata['name'] or dockerfile_path.parent.name

        # 确定标签
        tags = image_config.get('tags', metadata['tags'] or ['latest'])
        tags = [resolve_template_variables(t, commit_sha, branch) for t in tags]

        # 确定平台
        platforms = image_config.get('platforms', metadata['platforms'])

        # 确定构建上下文
        context_config = image_config.get('context', '')
        if context_config:
            context = str(source_dir / context_config)
        else:
            context = str(source_dir)

        # 确定 registry、org、repository（支持镜像级别和全局级别配置）
        registry = image_config.get('registry', global_registry)
        org = image_config.get('org', global_org)
        repository = image_config.get('repository')

        if not repository:
            print(f"Error: Image '{image_config.get('name', 'unknown')}' missing required field 'repository'")
            continue

        # 为每个平台创建独立的构建任务
        for platform in platforms:
            matrix.append({
                'image_name': image_name,
                'dockerfile': str(dockerfile_path),
                'context': context,
                'tags': '\n'.join([f'type=raw,value={t}' for t in tags]),
                'first_tag': tags[0] if tags else 'latest',
                'platforms': platform,
                'runner': get_runner_for_platform(platform),
                'build_args': image_config.get('build_args', {}),
                'source': source_name,
                'registry': registry,
                'org': org,
                'repository': repository
            })

    return matrix


def generate_matrix(
    config_paths: List[str],
    sources_dir: str,
    output_path: str
):
    """生成构建矩阵，支持多个配置文件"""

    sources_path = Path(sources_dir)
    all_matrix = []

    for config_path in config_paths:
        print(f"Processing config: {config_path}")
        matrix = process_config(config_path, sources_path)
        all_matrix.extend(matrix)

    result = {'matrix': all_matrix}

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Generated matrix with {len(all_matrix)} images")

    for item in all_matrix:
        print(f"  - {item['image_name']}: {item['first_tag']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan Dockerfiles and generate build matrix')
    parser.add_argument('--config', required=True, action='append', help='Path to config file (can be specified multiple times)')
    parser.add_argument('--sources', required=True, help='Directory containing cloned sources')
    parser.add_argument('--output', required=True, help='Output JSON file path')

    args = parser.parse_args()

    generate_matrix(
        config_paths=args.config,
        sources_dir=args.sources,
        output_path=args.output
    )