#!/usr/bin/env python3
"""
扫描所有源仓库中的 Dockerfile，生成构建矩阵
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


def find_dockerfiles(source_dir: Path, dockerfile_path: str = None) -> List[Path]:
    """查找 Dockerfile"""

    if dockerfile_path:
        specific_path = source_dir / dockerfile_path
        if specific_path.exists():
            return [specific_path]
        return []

    dockerfiles = []
    for path in source_dir.rglob('Dockerfile'):
        dockerfiles.append(path)
    for path in source_dir.rglob('*.dockerfile'):
        dockerfiles.append(path)

    return dockerfiles


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


def generate_matrix(
    config_path: str,
    sources_dir: str,
    output_path: str,
    repo_url: str = None,
    repo_dockerfile: str = None,
    image_filter: str = None,
    source_filter: str = None
):
    """生成构建矩阵"""

    matrix = []

    sources_path = Path(sources_dir)

    # 临时仓库模式
    if repo_url:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        source_dir = sources_path / repo_name

        if not source_dir.exists():
            print(f"Error: Cloned repo not found: {source_dir}")
            return

        commit_sha = get_commit_sha(source_dir)

        # 查找 Dockerfile
        dockerfiles = find_dockerfiles(source_dir, repo_dockerfile)

        if not dockerfiles:
            print(f"Warning: No Dockerfile found in {source_dir}")
            return

        for dockerfile in dockerfiles:
            metadata = parse_dockerfile_metadata(dockerfile)

            if not metadata['name']:
                metadata['name'] = dockerfile.parent.name

            context = str(dockerfile.parent)

            tags = metadata['tags'] if metadata['tags'] else ['latest']
            tags = [resolve_template_variables(t, commit_sha, 'main') for t in tags]

            # 为每个平台创建独立的构建任务
            for platform in metadata['platforms']:
                matrix.append({
                    'image_name': metadata['name'],
                    'dockerfile': str(dockerfile),
                    'context': context,
                    'tags': '\n'.join([f'type=raw,value={t}' for t in tags]),
                    'first_tag': tags[0] if tags else 'latest',
                    'platforms': platform,
                    'runner': get_runner_for_platform(platform),
                    'build_args': metadata['build_args'],
                    'source': repo_name
                })

    # 配置驱动模式
    else:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        global_platforms = config.get('global', {}).get('platforms', ['linux/amd64', 'linux/arm64'])

        for image_config in config.get('images', []):
            # 过滤
            if image_filter and image_config['name'] != image_filter:
                continue
            if source_filter and image_config.get('source') != source_filter:
                continue

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
            branch = config.get('sources', [{}])[0].get('branch', 'main')

            # 解析元数据
            metadata = parse_dockerfile_metadata(dockerfile_path)

            # 确定镜像名
            image_name = image_config['name'] or metadata['name'] or dockerfile_path.parent.name

            # 确定标签
            tags = image_config.get('tags', metadata['tags'] or ['latest'])
            tags = [resolve_template_variables(t, commit_sha, branch) for t in tags]

            # 确定平台
            platforms = image_config.get('platforms', global_platforms)

            # 确定构建上下文
            context = str(dockerfile_path.parent)

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
                    'source': source_name
                })

    result = {'matrix': matrix}

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Generated matrix with {len(matrix)} images")

    # 输出矩阵内容供调试
    for item in matrix:
        print(f"  - {item['image_name']}: {item['tags']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan Dockerfiles and generate build matrix')
    parser.add_argument('--config', help='Path to images.yaml')
    parser.add_argument('--sources', required=True, help='Directory containing cloned sources')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    parser.add_argument('--repo-url', help='Temporary repository URL')
    parser.add_argument('--repo-dockerfile', help='Dockerfile path in temporary repo')
    parser.add_argument('--image', help='Filter by image name')
    parser.add_argument('--source', help='Filter by source name')

    args = parser.parse_args()

    generate_matrix(
        config_path=args.config,
        sources_dir=args.sources,
        output_path=args.output,
        repo_url=args.repo_url,
        repo_dockerfile=args.repo_dockerfile,
        image_filter=args.image,
        source_filter=args.source
    )