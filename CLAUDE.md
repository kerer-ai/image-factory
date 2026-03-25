# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供代码仓库的开发指南。

## 项目概述

镜像工厂是一个容器镜像自动化构建系统，从外部仓库构建 Docker 镜像并推送到 quay.io。支持多架构构建（amd64/arm64），使用 GitHub 原生 Runner 加速。

## 架构

```
config/images.yaml → GitHub Actions → 构建矩阵 → 多架构镜像 → quay.io
```

**两种构建模式：**
- **配置驱动**：源仓库定义在 `config/images.yaml`，定时或配置变更时触发
- **临时仓库**：手动触发时传入 `repo_url` 参数，一次性构建

**多架构策略：**
- `linux/amd64` 运行在 `ubuntu-latest`
- `linux/arm64` 运行在 `ubuntu-22.04-arm`（原生 ARM，非 QEMU 模拟）

每个平台生成独立的矩阵任务，使用各自的 Runner，实现并行构建。

## 关键脚本

| 脚本 | 用途 |
|------|------|
| `scripts/clone-sources.py` | 从配置或临时 URL 克隆源仓库 |
| `scripts/scan-dockerfiles.py` | 扫描 Dockerfile 并生成构建矩阵 JSON |
| `scripts/validate-config.py` | 校验 `config/images.yaml` 配置格式 |

## 配置文件

`config/images.yaml` 是唯一的配置源。结构：

```yaml
global:
  registry: quay.io
  organization: ${QUAY_ORG}
  platforms: [linux/amd64, linux/arm64]

sources:
  - name: 仓库名
    url: https://github.com/org/repo.git
    branch: main

images:
  - name: 镜像名
    source: 仓库名
    dockerfile: path/to/Dockerfile
    tags: [tag1, tag2]
    platforms: [linux/amd64]  # 可选覆盖
```

## 构建矩阵生成

`scan-dockerfiles.py` 生成矩阵时，**每个平台独立成一个 job**：

```json
{
  "matrix": [
    {
      "image_name": "myapp",
      "dockerfile": "sources/repo/Dockerfile",
      "context": "sources/repo",
      "tags": "type=raw,value=latest\ntype=raw,value=v1.0",
      "first_tag": "latest",
      "platforms": "linux/amd64",
      "runner": "ubuntu-latest"
    },
    {
      "image_name": "myapp",
      "platforms": "linux/arm64",
      "runner": "ubuntu-22.04-arm"
    }
  ]
}
```

## 常用命令

```bash
# 校验配置
python3 scripts/validate-config.py config/images.yaml

# 手动触发构建
gh workflow run build-images.yml -f push=true

# 构建指定镜像
gh workflow run build-images.yml -f image=myapp -f push=false

# 临时仓库构建
gh workflow run build-images.yml \
  -f repo_url=https://github.com/user/repo.git \
  -f repo_dockerfile=Dockerfile \
  -f push=false

# 查看构建状态
gh run list --workflow=build-images.yml --limit 5
```

## 构建缓存

使用双重缓存：
1. **Registry 缓存**：`buildcache-amd64` / `buildcache-arm64` 标签
2. **GitHub Actions 缓存**：用于层复用

## 构建产物

产物使用第一个标签命名（非镜像名），避免冲突：
- `trivy-report-<tag>.txt`
- `sbom-<tag>.spdx.json`
- `sbom-<tag>.cdx.json`

## 必需的 GitHub Secrets

- `QUAY_USERNAME`：quay.io 用户名（格式：`org+robot_name`）
- `QUAY_ROBOT_TOKEN`：quay.io Robot Token
- `SSH_DEPLOY_KEY_*`：私有仓库 Deploy Key（可选）

## 必需的 GitHub Variables

- `QUAY_ORG`：quay.io 组织名