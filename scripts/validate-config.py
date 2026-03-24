#!/usr/bin/env python3
"""
验证配置文件格式和完整性
"""

import argparse
import sys
import yaml
from pathlib import Path


def validate_config(config_path: str) -> bool:
    """验证配置文件"""

    errors = []
    warnings = []

    # 检查文件是否存在
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        return False

    # 解析 YAML
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format: {e}")
        return False

    if config is None:
        print("Error: Config file is empty")
        return False

    # 验证全局配置
    if 'global' not in config:
        errors.append("Missing 'global' section")
    else:
        if 'registry' not in config['global']:
            warnings.append("Missing 'global.registry', will use quay.io")
        if 'organization' not in config['global']:
            errors.append("Missing 'global.organization'")
        if 'platforms' not in config['global']:
            warnings.append("Missing 'global.platforms', will use defaults")

    # 验证 sources
    source_names = []
    if 'sources' in config:
        for i, source in enumerate(config['sources']):
            if 'name' not in source:
                errors.append(f"Source {i}: missing 'name'")
            else:
                source_names.append(source['name'])
            if 'url' not in source:
                errors.append(f"Source {i}: missing 'url'")

    # 验证 images
    if 'images' in config:
        for i, image in enumerate(config['images']):
            if 'name' not in image:
                errors.append(f"Image {i}: missing 'name'")
            if 'source' not in image:
                errors.append(f"Image {i}: missing 'source'")
            elif image['source'] not in source_names:
                errors.append(f"Image {i}: source '{image['source']}' not found in sources")

    # 验证通知配置
    if 'notifications' in config:
        email = config['notifications'].get('email', {})
        if email.get('enabled') and not email.get('recipients'):
            warnings.append("Email notifications enabled but no recipients configured")

    # 输出结果
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("\n✓ Config validation passed!")
    print(f"  Sources: {len(config.get('sources', []))}")
    print(f"  Images:  {len(config.get('images', []))}")

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate images.yaml config')
    parser.add_argument('config', help='Path to images.yaml')

    args = parser.parse_args()
    success = validate_config(args.config)
    sys.exit(0 if success else 1)