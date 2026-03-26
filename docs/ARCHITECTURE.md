# 镜像工厂架构设计

本文档描述 Image Factory 的系统架构和各组件之间的协作关系。

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              配置层                                          │
│                     config/pytorch-images.yml                                │
│                                                                              │
│  registry: quay.io                                                          │
│  org: kerer                                                                 │
│                                                                              │
│  sources:                    images:                                         │
│    - name: pytorch             - name: pytorch                               │
│      url: https://...            repository: pytorch                         │
│      branch: master              dockerfile: ci/docker/X86/Dockerfile        │
│                                  tags: [x86-manylinux2.1-nightly]             │
│                                  platforms: [linux/amd64]                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions Workflow                            │
│                         .github/workflows/build-images.yml                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┴─────────────────────────┐
        ▼                                                         ▼
┌───────────────────────────┐                       ┌───────────────────────────┐
│        prepare            │                       │          build            │
│         Job               │                       │          Job             │
│                           │                       │                           │
│  • 检测配置文件            │                       │  • Docker Buildx          │
│  • 解析配置生成矩阵        │                       │  • Trivy Scan             │
│  • 克隆源仓库             │                       │  • SBOM Generate          │
│  • 上传 sources artifact   │──────────────────────▶│  • Upload artifacts       │
└───────────────────────────┘                       └───────────────────────────┘
```

## 执行流程

```
┌─────────────────┐                    ┌─────────────────┐     ┌──────────────┐
│     prepare     │ ──────────────────▶ │     build       │ ──▶ │   summary    │
│    (准备阶段)    │    sources artifact │   (构建阶段)     │     │  (总结阶段)   │
└─────────────────┘                    └─────────────────┘     └──────────────┘
```

---

## Job 详细设计

### 1. prepare - 准备阶段

**职责**: 检测配置、解析配置生成矩阵、克隆源仓库

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Job: prepare                                                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step: Detect configs to build                                        │   │
│  │                                                                      │   │
│  │ 触发方式检测:                                                         │   │
│  │ ├── 手动触发 + 指定配置 → 使用指定配置文件                             │   │
│  │ ├── Push 触发 → git diff 检测变更的配置文件                           │   │
│  │ └── 定时触发 → 构建所有配置文件                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step: Parse configs and generate matrix                              │   │
│  │                                                                      │   │
│  │ 工具: yq (YAML 处理工具)                                              │   │
│  │ 处理:                                                                 │   │
│  │   ├── 解析配置文件 (registry, org, sources, images)                  │   │
│  │   ├── 校验必填字段 (repository)                                       │   │
│  │   ├── 为每个平台生成独立的矩阵项                                      │   │
│  │   └── 根据平台选择对应 Runner                                         │   │
│  │ 输出: matrix JSON                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step: Clone source repositories                                      │   │
│  │                                                                      │   │
│  │ 处理:                                                                 │   │
│  │   ├── 从 matrix 提取唯一的源仓库列表                                  │   │
│  │   ├── git clone --depth 1 浅克隆                                     │   │
│  │   ├── 支持指定分支/ref                                                │   │
│  │   └── 初始化 submodule (如果存在)                                     │   │
│  │ 输出: sources/ 目录                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Outputs: matrix (构建矩阵 JSON)                                             │
│  Artifacts: sources/ (源代码)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. build - 构建阶段

**职责**: 并行构建多架构镜像，执行安全扫描

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Job: build (矩阵并行执行)                                                   │
│                                                                              │
│  Strategy: matrix.include (每个平台一个任务)                                  │
│                                                                              │
│  ┌───────────────────────────┐     ┌───────────────────────────┐           │
│  │ Runner: ubuntu-latest     │     │ Runner: ubuntu-22.04-arm  │           │
│  │ Platform: linux/amd64     │     │ Platform: linux/arm64     │           │
│  │                           │     │                           │           │
│  │ Steps:                    │     │ Steps:                    │           │
│  │ 1. Download sources       │     │ 1. Download sources       │           │
│  │ 2. Docker Buildx setup    │     │ 2. Docker Buildx setup    │           │
│  │ 3. Registry login         │     │ 3. Registry login         │           │
│  │ 4. Generate timestamp     │     │ 4. Generate timestamp     │           │
│  │ 5. Build & push image     │     │ 5. Build & push image     │           │
│  │ 6. Trivy vulnerability    │     │ 6. Trivy vulnerability    │           │
│  │ 7. SBOM (SPDX/CycloneDX)  │     │ 7. SBOM (SPDX/CycloneDX)  │           │
│  │ 8. Upload artifacts       │     │ 8. Upload artifacts       │           │
│  └───────────────────────────┘     └───────────────────────────┘           │
│                                                                              │
│  特性:                                                                       │
│  - fail-fast: false (一个失败不影响其他)                                     │
│  - GHA 缓存: 加速构建层复用                                                   │
│  - 时间戳标签: 自动拼接 yyyymmddHHMMSS                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. summary - 总结阶段

**职责**: 汇总构建结果，生成报告

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Job: summary                                                               │
│                                                                              │
│  输入:                                                                       │
│  - build-info-* artifacts (构建信息)                                         │
│  - trivy-report-* artifacts (扫描报告)                                       │
│                                                                              │
│  输出 (GitHub Step Summary):                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ## 🏗️ 构建总结                                                       │   │
│  │                                                                      │   │
│  │ ### 📊 构建统计                                                      │   │
│  │ | 总构建数 | 成功 | 失败 |                                            │   │
│  │                                                                      │   │
│  │ ### 📦 构建镜像                                                      │   │
│  │ | 镜像 | 平台 | 标签 | 下载命令 |                                     │   │
│  │                                                                      │   │
│  │ ### 🔒 安全扫描结果                                                  │   │
│  │ | 镜像标签 | CRITICAL | HIGH | MEDIUM | LOW | 状态 |                 │   │
│  │                                                                      │   │
│  │ ### 📁 构建产物                                                      │   │
│  │ | 产物类型 | 命名格式 | 说明 |                                        │   │
│  │                                                                      │   │
│  │ ### ℹ️ 构建信息                                                      │   │
│  │ 触发方式、构建时间、仓库、分支、Commit                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 脚本详细设计

### scripts/validate-config.py

**用途**: 校验配置文件格式和完整性（本地开发工具）

**输入**: 配置文件路径

**校验项**:

| 检查类型 | 校验内容 |
|----------|----------|
| 文件检查 | 文件存在性 |
| 格式检查 | YAML 语法正确性 |
| sources 检查 | 必须有 `name` 和 `url` |
| images 检查 | 必须有 `name`、`source`、`repository` |
| 引用检查 | image.source 必须在 sources 中定义 |

**退出码**: 0 = 成功, 1 = 失败

**使用示例**:
```bash
uv run python scripts/validate-config.py config/pytorch-images.yml
```

---

## 配置文件规范

### 文件命名

```
config/<project>-images.yml
```

### 配置结构

```yaml
# 镜像仓库配置
registry: quay.io              # 可选，默认 quay.io
org: kerer                     # 可选，默认 kerer

# 源仓库定义
sources:
  - name: <唯一标识>           # 必需
    url: <仓库地址>            # 必需
    branch: <分支名>           # 可选，默认 main

# 镜像定义
images:
  - name: <镜像名称>           # 必需
    source: <引用的 source>    # 必需
    repository: <仓库名>       # 必需，推送目标仓库名
    dockerfile: <Dockerfile路径> # 可选，默认 Dockerfile
    tags:                      # 可选
      - <tag1>
    platforms:                 # 可选
      - linux/amd64
      - linux/arm64
    build_args:                # 可选
      KEY: value
```

---

## 触发机制

| 触发类型 | 条件 | 构建范围 |
|----------|------|----------|
| 定时触发 | 每日 UTC 2:00 | 所有配置 |
| Push 触发 | `config/*-images.yml` 变更 | 变更的配置 |
| 手动触发 | workflow_dispatch | 可指定配置 |

### 手动触发参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config` | string | 空 | 配置文件名称 |
| `push` | boolean | true | 是否推送镜像 |
| `skip_scan` | boolean | false | 跳过安全扫描 |
| `skip_sbom` | boolean | false | 跳过 SBOM 生成 |

---

## 多架构策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           构建矩阵生成策略                                   │
└─────────────────────────────────────────────────────────────────────────────┘

配置文件:
  platforms: [linux/amd64, linux/arm64]

                    │
                    ▼ 拆分为独立任务

┌─────────────────────────────┐     ┌─────────────────────────────┐
│ 任务 1                       │     │ 任务 2                       │
│                              │     │                              │
│ platform: linux/amd64        │     │ platform: linux/arm64        │
│ runner: ubuntu-latest        │     │ runner: ubuntu-22.04-arm     │
│                              │     │                              │
│ 原生 x86_64 构建             │     │ 原生 ARM64 构建              │
│ (非 QEMU 模拟)               │     │ (非 QEMU 模拟)               │
└─────────────────────────────┘     └─────────────────────────────┘
                    │                             │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
                    并行执行，互不阻塞
```

---

## 缓存策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Actions 缓存                             │
└─────────────────────────────────────────────────────────────────────────────┘

缓存类型: type=gha,mode=max
缓存范围: 所有构建层
失效策略: 7 天未访问自动清理

优点:
- 无需额外配置 Registry 缓存
- 跨构建共享缓存
- 构建速度显著提升
```

---

## 构建产物

| 产物类型 | 命名格式 | 说明 | 保留时间 |
|----------|----------|------|----------|
| Trivy 扫描报告 | `trivy-report-<tag>-<platform>.txt` | 漏洞扫描结果 | 30 天 |
| SBOM (SPDX) | `sbom-<tag>-<platform>.spdx.json` | SPDX 格式物料清单 | 30 天 |
| SBOM (CycloneDX) | `sbom-<tag>-<platform>.cdx.json` | CycloneDX 格式物料清单 | 30 天 |
| Build info | `build-info-<tag>-<platform>/info.json` | 构建信息 | 1 天 |

> 命名包含平台后缀，确保同名镜像不同平台时产物唯一。

---

## 扩展指南

### 添加新项目

1. 创建配置文件 `config/<project>-images.yml`
2. 定义 `registry`、`org`、`sources` 和 `images`
3. 提交到仓库，自动触发构建

### 添加新平台

1. 在 workflow 的矩阵生成逻辑中添加平台到 runner 的映射
2. 在配置文件中使用新平台

---

## 相关文档

- [README.md](../README.md) - 项目介绍和快速开始
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南
- [CONFIGURATION.md](CONFIGURATION.md) - 配置说明文档
- [LESSONS-LEARNED.md](LESSONS-LEARNED.md) - 错误案例记录
- [PRD.md](PRD.md) - 产品需求文档