# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供代码仓库的开发指南。

## 项目概述

镜像工厂是一个容器镜像自动化构建系统，从外部仓库构建 Docker 镜像并推送到 quay.io。支持多配置文件、多架构构建（amd64/arm64），使用 GitHub 原生 Runner 加速。

## 架构

```
config/*-images.yml → prepare (解析配置+克隆源) → build (矩阵并行构建) → quay.io
```

**配置文件结构：**
- 配置文件存放在 `config/` 目录
- 命名格式：`*-images.yml`（如 `pytorch-images.yml`）
- 每个配置文件独立完整，包含 sources、images、registry、org 定义

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
- 修改配置格式 → 更新 `docs/CONFIGURATION.md`
- 修改 workflow 逻辑 → 更新 `docs/ARCHITECTURE.md`
- 遇到问题并修复 → 更新 `docs/LESSONS-LEARNED.md`
- 新增文档 → 更新 README.md 和 CLAUDE.md 的「相关文档」表格

## 关键脚本

| 脚本 | 用途 |
|------|------|
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

使用 GitHub Actions 缓存加速构建：
- 缓存类型：`type=gha,mode=max`
- 缓存范围：所有构建层
- 失效策略：7 天未访问自动清理

## 标签策略

所有镜像标签自动追加时间戳后缀 `yyyymmddHHMMSS`：
- 配置：`tags: [latest]`
- 实际：`latest-20260325100000`

## 手动触发参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config` | string | 空（构建所有） | 配置文件名称 |
| `push` | boolean | true | 是否推送镜像 |
| `skip_scan` | boolean | false | 跳过安全扫描 |
| `skip_sbom` | boolean | false | 跳过 SBOM 生成 |

## 构建产物

产物命名包含标签和平台，确保唯一性：
- `trivy-report-<tag>-<platform>.txt`
- `sbom-<tag>-<platform>.spdx.json`
- `sbom-<tag>-<platform>.cdx.json`
- `build-info-<tag>-<platform>/info.json`

## 必需的 GitHub Secrets

- `QUAY_USERNAME`：quay.io 用户名（格式：`org+robot_name`）
- `QUAY_ROBOT_TOKEN`：quay.io Robot Token

## 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目说明和快速开始 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 配置说明文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计文档 |
| [docs/LESSONS-LEARNED.md](docs/LESSONS-LEARNED.md) | 错误案例记录 |
| [docs/PRD.md](docs/PRD.md) | 产品需求文档 |