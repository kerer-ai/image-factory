# 镜像工厂架构设计

本文档描述 Image Factory 的系统架构和各组件之间的协作关系。

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              配置层                                          │
│                     config/pytorch-images.yml                                │
│                                                                              │
│  sources:                    images:                                         │
│    - name: pytorch             - name: pytorch                               │
│      url: https://...            dockerfile: ci/docker/X86/Dockerfile        │
│      branch: master             tags: [x86-manylinux2.1-nightly]             │
│                                 platforms: [linux/amd64]                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions Workflow                            │
│                         .github/workflows/build-images.yml                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│    prepare    │           │     clone     │           │     build     │
│     Job       │           │     Job       │           │     Job       │
└───────────────┘           └───────────────┘           └───────────────┘
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│validate-config│           │clone-sources  │           │  Docker Buildx│
│     .py       │           │     .py       │           │  Trivy Scan   │
│               │           │scan-dockerfiles│           │  SBOM Generate│
│               │           │     .py       │           │               │
└───────────────┘           └───────────────┘           └───────────────┘
```

## 执行流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   prepare   │ ──▶ │    clone    │ ──▶ │     build       │ ──▶ │   summary    │
│  (准备阶段)  │     │  (克隆阶段)  │     │   (构建阶段)     │     │  (总结阶段)   │
└─────────────┘     └─────────────┘     └─────────────────┘     └──────────────┘
```

---

## Job 详细设计

### 1. prepare - 准备阶段

**职责**: 确定构建目标，校验配置正确性

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
│  │ Step: Validate configs                                               │   │
│  │                                                                      │   │
│  │ 脚本: scripts/validate-config.py                                     │   │
│  │ 输入: 配置文件路径                                                    │   │
│  │ 校验:                                                                 │   │
│  │   ├── YAML 格式正确性                                                 │   │
│  │   ├── sources 定义完整性 (name, url)                                  │   │
│  │   ├── images 定义完整性 (name, source)                                │   │
│  │   └── 引用完整性 (image.source 存在于 sources 中)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Output: configs (JSON 数组)                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. clone - 克隆阶段

**职责**: 克隆源代码，生成构建矩阵

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Job: clone                                                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step: Clone source repositories                                      │   │
│  │                                                                      │   │
│  │ 脚本: scripts/clone-sources.py                                       │   │
│  │ 输入: --config 配置文件, --output 输出目录                            │   │
│  │ 处理:                                                                 │   │
│  │   ├── 解析配置文件中的 sources 列表                                   │   │
│  │   ├── git clone --depth 1 浅克隆                                     │   │
│  │   └── 支持指定分支/ref                                                │   │
│  │ 输出: sources/ 目录                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step: Scan Dockerfiles and generate matrix                           │   │
│  │                                                                      │   │
│  │ 脚本: scripts/scan-dockerfiles.py                                    │   │
│  │ 输入: --config 配置文件, --sources 源码目录, --output 输出文件        │   │
│  │ 处理:                                                                 │   │
│  │   ├── 检查 Dockerfile 文件存在                                        │   │
│  │   ├── 解析 Dockerfile 注释元数据                                      │   │
│  │   ├── 为每个平台生成独立的构建任务                                    │   │
│  │   └── 根据平台选择对应 Runner                                         │   │
│  │ 输出: matrix.json                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Output: matrix (构建矩阵 JSON)                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. build - 构建阶段

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

### 4. summary - 总结阶段

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

**用途**: 校验配置文件格式和完整性

**输入**: 配置文件路径

**校验项**:

| 检查类型 | 校验内容 |
|----------|----------|
| 文件检查 | 文件存在性 |
| 格式检查 | YAML 语法正确性 |
| sources 检查 | 必须有 `name` 和 `url` |
| images 检查 | 必须有 `name` 和 `source` |
| 引用检查 | image.source 必须在 sources 中定义 |

**退出码**: 0 = 成功, 1 = 失败

**使用示例**:
```bash
python3 scripts/validate-config.py config/pytorch-images.yml
```

---

### scripts/clone-sources.py

**用途**: 根据配置克隆源仓库

**输入参数**:
- `--config`: 配置文件路径
- `--output`: 输出目录

**处理流程**:
```
解析配置文件 sources
    │
    ▼
遍历每个 source
    │
    ├── 检查目录是否存在
    │   ├── 存在 → 跳过
    │   └── 不存在 → 执行克隆
    │
    ▼
git clone --depth 1 --branch <ref> <url> <output>/<name>
```

**输出**: `sources/<name>/` 目录

**使用示例**:
```bash
python3 scripts/clone-sources.py \
  --config config/pytorch-images.yml \
  --output sources/
```

---

### scripts/scan-dockerfiles.py

**用途**: 扫描 Dockerfile 并生成构建矩阵

**输入参数**:
- `--config`: 配置文件路径（支持多个，`nargs='+'`）
- `--sources`: 源码目录
- `--output`: 输出 JSON 文件路径

**处理流程**:
```
解析配置文件 images
    │
    ▼
遍历每个 image 配置
    │
    ├── 检查 Dockerfile 是否存在
    │
    ├── 解析 Dockerfile 注释元数据 (可选)
    │   ├── # image-name: <name>
    │   ├── # image-tags: <tag1>,<tag2>
    │   └── # platforms: <platform1>,<platform2>
    │
    ├── 为每个平台创建独立的矩阵项
    │   │
    │   ├── linux/amd64 → runner: ubuntu-latest
    │   └── linux/arm64 → runner: ubuntu-22.04-arm
    │
    ▼
输出 matrix.json
```

**输出格式**:
```json
{
  "matrix": [
    {
      "image_name": "pytorch",
      "dockerfile": "sources/pytorch/ci/docker/X86/Dockerfile",
      "context": "sources/pytorch/ci/docker/X86",
      "tags": "type=raw,value=x86-manylinux2.1-nightly",
      "first_tag": "x86-manylinux2.1-nightly",
      "platforms": "linux/amd64",
      "runner": "ubuntu-latest",
      "build_args": {}
    }
  ]
}
```

**使用示例**:
```bash
# 单个配置文件
python3 scripts/scan-dockerfiles.py \
  --config config/pytorch-images.yml \
  --sources sources/ \
  --output matrix.json

# 多个配置文件
python3 scripts/scan-dockerfiles.py \
  --config config/pytorch-images.yml config/triton-ascend-images.yml \
  --sources sources/ \
  --output matrix.json
```

---

## 配置文件规范

### 文件命名

```
config/<project>-images.yml
```

### 配置结构

```yaml
# 源仓库定义
sources:
  - name: <唯一标识>           # 必需
    url: <仓库地址>            # 必需
    branch: <分支名>           # 可选，默认 main

# 镜像定义
images:
  - name: <镜像名称>           # 必需
    source: <引用的 source>    # 必需
    dockerfile: <Dockerfile路径> # 可选，默认 Dockerfile
    tags:                      # 可选
      - <tag1>
      - <tag2>
    platforms:                 # 可选
      - linux/amd64
      - linux/arm64
    build_args:                # 可选
      KEY: value

# 构建配置 (可选)
build:
  severity: CRITICAL,HIGH
  timeout: 30

# SBOM 配置 (可选)
sbom:
  enabled: true
  formats:
    - spdx
    - cyclonedx
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
│                              │     │                              │
│ 构建时间: ~1.5 分钟          │     │ 构建时间: ~40 秒             │
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

┌─────────────────────────────────────────────────────────────────────────────┐
│ GitHub Actions 缓存                                                          │
│                                                                              │
│ 缓存类型: type=gha,mode=max                                                  │
│ 缓存范围: 所有构建层                                                          │
│ 失效策略: 7 天未访问自动清理                                                  │
│                                                                              │
│ 优点:                                                                        │
│ - 无需额外配置 Registry 缓存                                                 │
│ - 跨构建共享缓存                                                             │
│ - 构建速度显著提升                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
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
2. 定义 `sources` 和 `images`
3. 提交到仓库，自动触发构建

### 添加新平台

1. 在 `scan-dockerfiles.py` 的 `get_runner_for_platform()` 添加映射
2. 在配置文件中使用新平台

### 自定义构建流程

1. 修改 workflow 文件
2. 添加新的 Step 或 Job
3. 调整脚本逻辑

---

## 相关文档

- [README.md](../README.md) - 项目介绍和快速开始
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南
- [CONFIGURATION.md](CONFIGURATION.md) - 配置说明文档
- [LESSONS-LEARNED.md](LESSONS-LEARNED.md) - 错误案例记录
- [PRD.md](PRD.md) - 产品需求文档