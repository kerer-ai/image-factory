# 镜像工厂（Image Factory）产品需求文档（PRD）

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v5.1 |
| 创建日期 | 2026-03-24 |
| 更新日期 | 2026-03-25 |
| 状态 | 已实现 |

---

## 1. 项目背景与目标

### 1.1 背景

当前团队需要一套标准化的容器镜像构建系统，现有镜像构建流程存在以下问题：
- 手动构建效率低下
- 镜像版本管理混乱
- 缺乏多架构支持
- 更新不及时
- Dockerfile 分散在各个项目仓库，缺乏统一管理

### 1.2 目标

构建一个通用化的自动化镜像工厂系统，实现：
- **多配置文件**：每个项目独立配置文件，互不影响
- **源码分离**：Dockerfile 存放在外部仓库，通过配置文件声明
- **自动化构建**：基于 GitHub Actions 实现定时和手动触发构建
- **多架构支持**：同时支持 x86_64 和 arm64 架构，使用原生 Runner 加速
- **标准化管理**：统一镜像构建流程和版本管理
- **安全可靠**：镜像安全扫描 + SBOM 生成

### 1.3 成功指标

| 指标 | 目标值 | 实际值 |
|------|--------|--------|
| 镜像构建成功率 | ≥ 95% | ✓ |
| X86 构建时间 | ≤ 5 分钟 | ~1.5 分钟 |
| ARM 构建时间 | ≤ 5 分钟 | ~40 秒（原生 Runner） |
| 新增镜像时间 | ≤ 10 分钟 | ✓（仅需修改配置） |
| 安全报告覆盖 | 100% | ✓ |

---

## 2. 功能需求

### 2.1 核心功能

#### 2.1.1 仓库管理

| 功能项 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| 多仓库配置 | 支持配置多个 Dockerfile 源仓库 | P0 | ✓ |
| 仓库认证 | 支持 Public 和 Private 仓库 | P0 | ✓ |
| 分支选择 | 支持指定拉取的分支或标签 | P1 | ✓ |
| 自动拉取 | 触发时自动拉取最新代码 | P0 | ✓ |

#### 2.1.2 Dockerfile 发现与解析

| 功能项 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| 自动扫描 | 扫描仓库中的所有 Dockerfile | P0 | ✓ |
| 路径配置 | 支持指定 Dockerfile 所在路径 | P0 | ✓ |
| 元数据解析 | 从 Dockerfile 提取镜像名称、标签等信息 | P0 | ✓ |
| 构建参数 | 支持 Docker build-args 配置 | P1 | ✓ |

#### 2.1.3 镜像构建

| 功能项 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| 定时构建 | 每日自动触发构建（UTC 2:00 / 北京时间 10:00） | P0 | ✓ |
| 手动构建 | 支持通过 GitHub Actions 手动触发 | P0 | ✓ |
| 临时仓库构建 | 支持手动输入仓库 URL，一次性构建镜像 | P1 | ✓ |
| 选择性构建 | 支持指定单个或多个镜像构建 | P1 | ✓ |
| 多架构构建 | 支持 amd64 和 arm64 架构，使用原生 Runner | P0 | ✓ |

#### 2.1.4 镜像推送

| 功能项 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| quay.io 推送 | 推送镜像到 quay.io 仓库 | P0 | ✓ |
| 多仓库支持 | 支持按镜像配置推送到不同仓库 | P1 | - |
| 推送验证 | 验证镜像推送完整性 | P1 | ✓ |

#### 2.1.5 安全扫描

| 功能项 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| 漏洞扫描 | 使用 Trivy 扫描镜像漏洞 | P0 | ✓ |
| 扫描报告 | 生成安全扫描报告，漏洞不影响镜像推送 | P1 | ✓ |
| 报告存档 | 扫描报告上传为构建产物（保留 30 天） | P1 | ✓ |

#### 2.1.6 SBOM 生成

| 功能项 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| SBOM 生成 | 使用 Trivy 生成软件物料清单 | P0 | ✓ |
| 多格式支持 | 支持 SPDX 和 CycloneDX 格式 | P1 | ✓ |
| SBOM 存档 | SBOM 文件上传为构建产物（保留 30 天） | P1 | ✓ |

### 2.2 非功能需求

#### 2.2.1 安全性

| 需求 | 描述 |
|------|------|
| 凭证管理 | 使用 GitHub Secrets 管理敏感信息 |
| 仓库访问 | Private 仓库通过 Deploy Key 访问 |
| 镜像扫描 | 构建完成后使用 Trivy 进行安全扫描 |
| SBOM 生成 | 每次构建生成 SBOM，支持供应链安全审计 |

#### 2.2.2 可维护性

| 需求 | 描述 |
|------|------|
| 配置驱动 | 所有镜像配置集中在一个 YAML 文件 |
| 结构清晰 | 清晰的目录结构，便于维护 |
| 日志记录 | 构建日志完整可追溯 |

#### 2.2.3 性能优化

| 需求 | 描述 |
|------|------|
| 原生 ARM Runner | 使用 ubuntu-22.04-arm 替代 QEMU 模拟，构建速度提升 20 倍 |
| Registry 缓存 | 使用镜像仓库缓存已构建层，加速后续构建 |
| GitHub Actions 缓存 | 双重缓存保障，避免重复构建相同层 |
| 并行构建 | 多架构镜像并行构建，互不阻塞 |

---

## 3. 技术架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        镜像工厂 (image-factory)                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      配置文件 (images.yaml)                       │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │   │
│  │  │  Source Repo 1│  │  Source Repo 2│  │  Source Repo N│        │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions 工作流                            │
│                                                                          │
│   触发方式: 定时触发 / 手动触发 / 配置变更触发                             │
│                                                                          │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│   │ 1.拉取   │──▶│ 2.扫描   │──▶│ 3.构建   │──▶│ 4.扫描   │            │
│   │ 源仓库   │   │Dockerfile│   │  镜像    │   │ + SBOM   │            │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘            │
│                                     │               │                   │
│                                     ▼               ▼                   │
│                              ┌──────────┐    ┌──────────┐               │
│                              │ 5.推送   │    │ 6.产物   │               │
│                              │  镜像    │    │ 上传     │               │
│                              └──────────┘    └──────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌───────────────────┐
                         │   quay.io Registry │
                         │   (镜像 + 缓存)    │
                         └───────────────────┘
```

### 3.2 多架构构建策略

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           构建矩阵 (Matrix)                               │
│                                                                          │
│   ┌─────────────────────────────┐   ┌─────────────────────────────┐     │
│   │   X86 构建任务               │   │   ARM 构建任务               │     │
│   │                             │   │                             │     │
│   │   Runner: ubuntu-latest     │   │   Runner: ubuntu-22.04-arm  │     │
│   │   Platform: linux/amd64     │   │   Platform: linux/arm64     │     │
│   │   Cache: buildcache-amd64   │   │   Cache: buildcache-arm64   │     │
│   │                             │   │                             │     │
│   │   构建时间: ~1.5 分钟        │   │   构建时间: ~40 秒           │     │
│   └─────────────────────────────┘   └─────────────────────────────┘     │
│                                                                          │
│                    两个任务并行执行，互不阻塞                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 构建流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  准备阶段   │ ──▶ │  构建阶段   │ ──▶ │  后处理阶段 │
│             │     │             │     │             │
│ - 解析配置  │     │ - 原生ARM   │     │ - 安全扫描  │
│ - 克隆仓库  │     │   构建加速  │     │ - SBOM生成  │
│ - 生成矩阵  │     │ - 推送镜像  │     │ - 缓存更新  │
│             │     │ - 缓存推送  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 3.4 仓库结构

```
image-factory/
├── .github/
│   └── workflows/
│       └── build-images.yml       # 主构建工作流
├── config/
│   ├── pytorch-images.yml         # PyTorch 镜像配置
│   ├── tensorflow-images.yml      # TensorFlow 镜像配置
│   └── *-images.yml               # 其他项目配置
├── scripts/
│   └── validate-config.py       # 配置文件校验脚本（本地开发工具）
├── .gitignore
└── README.md
```

---

## 4. 配置文件设计

### 4.1 配置文件结构

每个项目独立配置文件，位于 `config/` 目录，命名为 `*-images.yml`：

```yaml
# config/pytorch-images.yml

# 源仓库列表
sources:
  - name: pytorch
    url: https://github.com/myorg/pytorch.git
    branch: main

# 镜像构建配置
images:
  - name: pytorch
    source: pytorch
    dockerfile: Dockerfile
    tags:
      - x86-latest
      - x86-1.0
    platforms:
      - linux/amd64

  - name: pytorch
    source: pytorch
    dockerfile: Dockerfile.arm
    tags:
      - arm-latest
    platforms:
      - linux/arm64
```

### 4.2 配置项说明

| 配置项 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `sources[].name` | string | 是 | 源仓库名称（唯一标识） |
| `sources[].url` | string | 是 | 仓库地址（HTTPS 或 SSH） |
| `sources[].branch` | string | 否 | 分支名，默认 main |
| `images[].name` | string | 是 | 镜像名称 |
| `images[].source` | string | 是 | 引用的源仓库名称 |
| `images[].dockerfile` | string | 否 | Dockerfile 路径，默认 Dockerfile |
| `images[].tags` | list | 否 | 镜像标签列表 |
| `images[].platforms` | list | 否 | 目标平台 |
| `images[].build_args` | map | 否 | 构建参数 |

### 4.3 模板变量

镜像标签支持以下模板变量：

| 变量 | 示例值 | 说明 |
|------|--------|------|
| `{{ sha_short }}` | `abc1234` | 源仓库短 commit SHA |
| `{{ sha }}` | `abc1234...` | 源仓库完整 commit SHA |
| `{{ date }}` | `20260325` | 构建日期 |
| `{{ branch }}` | `main` | 源仓库分支名 |

---

## 5. 镜像命名规范

### 5.1 命名格式

```
<registry>/<organization>/<image-name>:<tag>
```

**示例：**
```
quay.io/kerer/pytorch:x86-manylinux2.1-latest
quay.io/kerer/pytorch:arm-manylinux2014-latest
```

### 5.2 标签策略建议

| 标签类型 | 示例 | 说明 |
|----------|------|------|
| 架构标识 | `x86-latest` / `arm-latest` | 区分不同架构 |
| 版本号 | `x86-1.0` / `arm-1.0` | 包含版本信息 |
| SHA | `abc1234` | 可追溯的 commit |

---

## 6. 触发方式

| 触发类型 | 说明 |
|----------|------|
| 定时触发 | 每日 UTC 2:00（北京时间 10:00）构建所有配置 |
| 手动触发 | 通过 GitHub Actions 界面手动执行，可选择配置文件 |
| 配置变更 | `config/*-images.yml` 变更时触发对应项目构建 |

### 6.1 手动触发参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config` | string | 空 | 配置文件名称（如 pytorch-images.yml，留空构建所有） |
| `push` | boolean | true | 是否推送到仓库 |
| `skip_scan` | boolean | false | 跳过安全扫描 |
| `skip_sbom` | boolean | false | 跳过 SBOM 生成 |

---

## 7. 构建产物

每次构建生成以下产物（保留 30 天）：

| 产物 | 文件名格式 | 说明 |
|------|------------|------|
| Trivy 扫描报告 | `trivy-report-<tag>.txt` | 漏洞扫描结果 |
| SBOM (SPDX) | `sbom-<tag>.spdx.json` | SPDX 格式物料清单 |
| SBOM (CycloneDX) | `sbom-<tag>.cdx.json` | CycloneDX 格式物料清单 |

---

## 8. 配置要求

### 8.1 GitHub Secrets

| Secret 名称 | 说明 | 必需 |
|------------|------|------|
| `QUAY_USERNAME` | quay.io 用户名（格式：`org+robot_name`） | 是 |
| `QUAY_ROBOT_TOKEN` | quay.io Robot Token | 是 |
| `SSH_DEPLOY_KEY_*` | 私有仓库 Deploy Key | 私有仓库必需 |

### 8.2 GitHub Variables

| 变量名 | 说明 |
|--------|------|
| `QUAY_ORG` | quay.io 组织名 |

---

## 9. 验证方法

### 9.1 配置验证

```bash
python3 scripts/validate-config.py config/pytorch-images.yml

# 列出所有配置
python3 scripts/list-configs.py
```

### 9.2 构建验证

```bash
# 手动触发工作流（配置驱动模式）
gh workflow run build-images.yml -f image=centos9-python -f push=false

# 手动触发工作流（临时仓库模式）
gh workflow run build-images.yml \
  -f repo_url=https://github.com/user/test-images.git \
  -f push=false

# 查看构建状态
gh run list --workflow=build-images.yml --limit 5
```

### 9.3 镜像验证

```bash
# 拉取镜像
docker pull quay.io/${ORG}/pytorch:x86-manylinux2.1-latest
docker pull quay.io/${ORG}/pytorch:arm-manylinux2014-latest

# 查看镜像信息
docker inspect quay.io/${ORG}/pytorch:x86-manylinux2.1-latest
```

---

## 10. 性能优化

### 10.1 原生 ARM Runner

使用 GitHub 提供的 `ubuntu-22.04-arm` Runner 替代 QEMU 模拟：

| 对比项 | QEMU 模拟 | 原生 ARM Runner |
|--------|----------|-----------------|
| 构建时间 | ~15 分钟 | ~40 秒 |
| 资源消耗 | 高（模拟器开销） | 低（原生执行） |
| 稳定性 | 一般 | 高 |

### 10.2 构建缓存

使用双重缓存策略：

| 缓存类型 | 存储位置 | 用途 |
|----------|----------|------|
| Registry 缓存 | `buildcache-amd64` / `buildcache-arm64` 标签 | 跨工作流复用 |
| GitHub Actions 缓存 | Actions Cache | 本工作流内复用 |

---

## 11. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 私有仓库访问 | 中 | 使用 Deploy Key，支持多仓库 |
| 配置文件错误 | 中 | 添加 YAML 校验脚本 |
| Dockerfile 解析失败 | 低 | fallback 使用目录名作为镜像名 |
| 构建矩阵过大 | 低 | 支持 filter 过滤特定镜像 |

---

## 12. 附录

### 12.1 术语说明

| 术语 | 说明 |
|------|------|
| Buildx | Docker 的构建工具，支持多架构构建 |
| Matrix | GitHub Actions 的并行构建矩阵 |
| SBOM | Software Bill of Materials，软件物料清单 |
| SPDX | Linux 基金会 SBOM 标准 |
| CycloneDX | OWASP SBOM 标准 |
| Runner | GitHub Actions 执行环境 |

### 12.2 参考链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)
- [Trivy 官方文档](https://aquasecurity.github.io/trivy/)
- [quay.io 文档](https://docs.quay.io/)
- [GitHub-hosted Runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)

---

## 13. 审核记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-03-24 | v1.0 | 初始版本 |
| 2026-03-24 | v2.0 | 重构为通用化架构 |
| 2026-03-24 | v3.0 | 精简文档，移除冗余代码，聚焦逻辑架构 |
| 2026-03-24 | v3.1 | 新增镜像命名规范章节 |
| 2026-03-24 | v3.2 | 新增临时仓库构建模式 |
| 2026-03-25 | v4.0 | 更新性能优化章节，使用原生 ARM Runner，移除通知功能，更新构建产物命名 |
| 2026-03-25 | v5.0 | 重构为多配置文件架构，每个项目独立配置文件 |
| 2026-03-25 | v5.1 | 简化手动触发参数，移除临时仓库模式 |