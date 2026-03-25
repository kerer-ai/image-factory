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
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML format: {e}")
        return False

    if config is None:
        print("Error: Config file is empty")
        return False

    # 验证 sources（必需）
    source_names = []
    if 'sources' not in config or not config['sources']:
        errors.append("Missing or empty 'sources' section")
    else:
        for i, source in enumerate(config['sources']):
            if 'name' not in source:
                errors.append(f"Source {i}: missing 'name'")
            else:
                source_names.append(source['name'])
            if 'url' not in source:
                errors.append(f"Source {i}: missing 'url'")

    # 验证 images（必需）
    if 'images' not in config or not config['images']:
        errors.append("Missing or empty 'images' section")
    else:
        for i, image in enumerate(config['images']):
            if 'name' not in image:
                errors.append(f"Image {i}: missing 'name'")
            if 'source' not in image:
                errors.append(f"Image {i}: missing 'source'")
            elif image['source'] not in source_names:
                errors.append(f"Image {i}: source '{image['source']}' not found in sources")

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

    print("\n[OK] Config validation passed!")
    print(f"  Sources: {len(config.get('sources', []))}")
    print(f"  Images:  {len(config.get('images', []))}")

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate config file')
    parser.add_argument('config', help='Path to config file (*-images.yml)')

    args = parser.parse_args()
    success = validate_config(args.config)
    sys.exit(0 if success else 1)