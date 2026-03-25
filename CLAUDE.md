# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供代码仓库的开发指南。

## 项目概述

镜像工厂是一个容器镜像自动化构建系统，从外部仓库构建 Docker 镜像并推送到 quay.io。支持多配置文件、多架构构建（amd64/arm64），使用 GitHub 原生 Runner 加速。

## 架构

```
config/*-images.yml → GitHub Actions → 构建矩阵 → 多架构镜像 → quay.io
```

**配置文件结构：**
- 配置文件存放在 `config/` 目录
- 命名格式：`*-images.yml`（如 `pytorch-images.yml`）
- 每个配置文件独立完整，包含 sources 和 images 定义

**触发机制：**
- 定时触发：每日 UTC 2:00 构建所有配置
- 配置变更：`config/*-images.yml` 变更时触发对应项目构建
- 手动触发：可选择指定配置文件或构建所有

**多架构策略：**
- `linux/amd64` 运行在 `ubuntu-latest`
- `linux/arm64` 运行在 `ubuntu-22.04-arm`（原生 ARM，非 QEMU 模拟）

每个平台生成独立的矩阵任务，使用各自的 Runner，实现并行构建。

## 开发规范

**文档同步：** 修改代码或 workflow 后，及时更新相关文档：
- 新增脚本 → 更新「关键脚本」表格
- 修改配置格式 → 更新 `docs/CONFIGURATION.md`
- 修改 workflow 逻辑 → 更新 `docs/ARCHITECTURE.md`
- 遇到问题并修复 → 更新 `docs/LESSONS-LEARNED.md`
- 新增文档 → 更新 README.md 和 CLAUDE.md 的「相关文档」表格

## 关键脚本

| 脚本 | 用途 |
|------|------|
| `scripts/clone-sources.py` | 从配置克隆源仓库 |
| `scripts/scan-dockerfiles.py` | 扫描 Dockerfile 并生成构建矩阵 JSON |
| `scripts/validate-config.py` | 校验配置文件格式（本地开发工具） |

## 配置文件格式

详见 [docs/CONFIGURATION.md](docs/CONFIGURATION.md)。

## Skills

本项目提供以下 Claude Code Skills：

| Skill | 触发方式 | 说明 |
|-------|----------|------|
| `add-image-config` | "添加 xxx 仓库镜像配置" | 自动化添加新仓库的镜像构建配置 |

使用示例：
```
帮我添加 xxx 仓库的镜像配置
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
# 校验配置（使用 uv 虚拟环境）
uv run python scripts/validate-config.py config/pytorch-images.yml

# 手动触发指定配置
gh workflow run build-images.yml -f config=pytorch-images.yml -f push=true

# 构建所有配置
gh workflow run build-images.yml -f push=true

# 构建但不推送
gh workflow run build-images.yml -f config=pytorch-images.yml -f push=false

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

## 必需的 GitHub Variables

- `QUAY_ORG`：quay.io 组织名

## 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目说明和快速开始 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 配置说明文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计文档 |
| [docs/LESSONS-LEARNED.md](docs/LESSONS-LEARNED.md) | 错误案例记录 |
| [docs/PRD.md](docs/PRD.md) | 产品需求文档 |