# 配置说明文档

本文档详细说明镜像工厂配置文件的各项配置项。

## 配置文件位置

```
config/<project>-images.yml
```

**命名规范**：`<项目名>-images.yml`

---

## 配置文件结构

```yaml
# 源仓库定义
sources:
  - name: <名称>
    url: <仓库地址>
    branch: <分支>

# 镜像定义
images:
  - name: <镜像名>
    source: <引用的源>
    dockerfile: <Dockerfile路径>
    tags:
      - <标签1>
      - <标签2>
    platforms:
      - <平台1>
      - <平台2>
    build_args:
      <键>: <值>

# 构建配置（可选）
build:
  severity: <严重级别>
  timeout: <超时时间>

# SBOM 配置（可选）
sbom:
  enabled: <是否启用>
  formats:
    - <格式1>
    - <格式2>
```

---

## 配置项详解

### sources（必需）

定义源代码仓库列表。

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | ✅ | - | 源仓库名称，作为唯一标识 |
| `url` | string | ✅ | - | Git 仓库地址（支持 HTTPS/SSH） |
| `branch` | string | ❌ | `main` | 分支名或标签名 |

**示例**：

```yaml
sources:
  # 基本配置
  - name: pytorch
    url: https://github.com/pytorch/pytorch.git
    branch: main

  # 使用标签
  - name: tensorflow
    url: https://github.com/tensorflow/tensorflow.git
    branch: v2.12.0

  # 私有仓库（SSH）
  - name: private-repo
    url: git@github.com:org/private-repo.git
    branch: develop
```

**注意事项**：
- `name` 必须唯一，后续 `images` 配置通过此名称引用
- `branch` 可以是分支名、标签名或 commit SHA（需使用 `ref` 字段）

---

### images（必需）

定义要构建的镜像列表。

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | ✅ | - | 镜像名称 |
| `source` | string | ✅ | - | 引用的 sources 中的 name |
| `dockerfile` | string | ❌ | `Dockerfile` | Dockerfile 相对于仓库根目录的路径 |
| `tags` | list | ❌ | `['latest']` | 镜像标签列表 |
| `platforms` | list | ❌ | `['linux/amd64']` | 目标构建平台 |
| `build_args` | map | ❌ | `{}` | 构建参数 |

**示例**：

```yaml
images:
  # 最简配置
  - name: myapp
    source: myapp

  # 完整配置
  - name: pytorch
    source: pytorch
    dockerfile: ci/docker/Dockerfile
    tags:
      - x86-latest
      - x86-2.0
    platforms:
      - linux/amd64
    build_args:
      PYTHON_VERSION: "3.10"
      CUDA_VERSION: "11.8"

  # 多平台构建
  - name: myapp
    source: myapp
    tags:
      - latest
    platforms:
      - linux/amd64
      - linux/arm64
```

#### name（镜像名称）

镜像推送到仓库时使用的名称：

```
quay.io/<org>/<name>:<tag>
```

**命名规范**：
- 只使用小写字母、数字、`-`、`_`
- 不超过 63 个字符
- 以字母或数字开头和结尾

#### source（源引用）

必须引用 `sources` 中已定义的名称：

```yaml
sources:
  - name: pytorch        # 定义源
    url: https://...

images:
  - name: pytorch
    source: pytorch      # 引用源（必须匹配）
```

#### dockerfile（Dockerfile 路径）

相对于源仓库根目录的路径：

```yaml
# 源仓库结构
# pytorch/
#   ci/
#     docker/
#       X86/
#         Dockerfile    <-- 目标文件

dockerfile: ci/docker/X86/Dockerfile
```

#### tags（镜像标签）

构建时会自动添加时间戳后缀：

```yaml
tags:
  - x86-latest

# 构建后: x86-latest-20260325140000
```

**标签命名建议**：
- 使用语义化版本：`v1.0.0`、`v2.1.0`
- 标识架构：`x86-latest`、`arm-latest`
- 标识用途：`nightly`、`stable`、`dev`

#### platforms（构建平台）

支持的平台：

| 平台 | Runner | 说明 |
|------|--------|------|
| `linux/amd64` | `ubuntu-latest` | x86_64 架构 |
| `linux/arm64` | `ubuntu-22.04-arm` | ARM64 架构（原生构建） |

**多平台配置**：

```yaml
# 方式1: 每个平台独立配置（推荐）
images:
  - name: pytorch
    source: pytorch
    dockerfile: ci/docker/X86/Dockerfile
    tags: [x86-latest]
    platforms: [linux/amd64]

  - name: pytorch
    source: pytorch
    dockerfile: ci/docker/ARM/Dockerfile
    tags: [arm-latest]
    platforms: [linux/arm64]

# 方式2: 同一 Dockerfile 多平台（需要 Dockerfile 支持多架构）
images:
  - name: myapp
    source: myapp
    tags: [latest]
    platforms:
      - linux/amd64
      - linux/arm64
```

#### build_args（构建参数）

传递给 `docker build --build-arg` 的参数：

```yaml
build_args:
  PYTHON_VERSION: "3.10"
  CUDA_VERSION: "11.8"
  BASE_IMAGE: "nvidia/cuda:11.8-devel"
```

在 Dockerfile 中使用：

```dockerfile
ARG PYTHON_VERSION=3.9
ARG CUDA_VERSION=11.8

FROM nvidia/cuda:${CUDA_VERSION}-devel
...
```

---

### build（可选）

构建行为配置。

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `severity` | string | ❌ | `CRITICAL,HIGH` | 漏洞扫描严重级别 |
| `timeout` | int | ❌ | `30` | 构建超时时间（分钟） |

**示例**：

```yaml
build:
  severity: CRITICAL,HIGH,MEDIUM  # 扫描更多级别
  timeout: 60                      # 延长超时时间
```

**severity 可选值**：

| 值 | 说明 |
|---|------|
| `CRITICAL` | 严重漏洞 |
| `HIGH` | 高危漏洞 |
| `MEDIUM` | 中危漏洞 |
| `LOW` | 低危漏洞 |
| `UNKNOWN` | 未知级别 |

多个级别用逗号分隔。

---

### sbom（可选）

软件物料清单（SBOM）配置。

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `enabled` | bool | ❌ | `true` | 是否生成 SBOM |
| `formats` | list | ❌ | `['spdx', 'cyclonedx']` | SBOM 格式 |

**示例**：

```yaml
sbom:
  enabled: true
  formats:
    - spdx       # SPDX 格式
    - cyclonedx  # CycloneDX 格式
```

**SBOM 格式说明**：

| 格式 | 文件扩展名 | 标准 |
|------|------------|------|
| `spdx` | `.spdx.json` | ISO/IEC 5962:2021 |
| `cyclonedx` | `.cdx.json` | OWASP CycloneDX |

---

## 完整配置示例

### 示例 1: PyTorch 多架构构建

```yaml
# PyTorch 镜像构建配置

sources:
  - name: pytorch
    url: https://github.com/pytorch/pytorch.git
    branch: main

images:
  # X86 版本
  - name: pytorch
    source: pytorch
    dockerfile: ci/docker/X86/Dockerfile
    tags:
      - x86-latest
      - x86-2.0
    platforms:
      - linux/amd64
    build_args:
      PYTHON_VERSION: "3.10"

  # ARM 版本
  - name: pytorch
    source: pytorch
    dockerfile: ci/docker/ARM/Dockerfile
    tags:
      - arm-latest
      - arm-2.0
    platforms:
      - linux/arm64
    build_args:
      PYTHON_VERSION: "3.10"

build:
  severity: CRITICAL,HIGH
  timeout: 30

sbom:
  enabled: true
  formats:
    - spdx
    - cyclonedx
```

### 示例 2: 多项目配置

```yaml
# 多个项目的镜像配置

sources:
  - name: pytorch
    url: https://github.com/pytorch/pytorch.git
    branch: main

  - name: torchvision
    url: https://github.com/pytorch/vision.git
    branch: main

images:
  - name: pytorch
    source: pytorch
    tags: [latest]
    platforms: [linux/amd64]

  - name: torchvision
    source: torchvision
    tags: [latest]
    platforms: [linux/amd64]
```

### 示例 3: 最简配置

```yaml
# 最简配置示例

sources:
  - name: myapp
    url: https://github.com/org/myapp.git

images:
  - name: myapp
    source: myapp
```

---

## 配置校验

在提交配置前，使用校验工具验证：

```bash
python3 scripts/validate-config.py config/<project>-images.yml
```

校验内容包括：
- YAML 格式正确性
- 必需字段完整性
- 引用关系正确性

详见 [CONTRIBUTING.md](../CONTRIBUTING.md)。

---

## 常见问题

### Q: 如何构建私有仓库？

A: 需要在 GitHub Secrets 中配置 SSH 密钥或访问令牌。

### Q: 多个镜像能否共用同一个 Dockerfile？

A: 可以，通过不同的 `build_args` 区分：

```yaml
images:
  - name: myapp-cpu
    source: myapp
    build_args:
      DEVICE: cpu

  - name: myapp-gpu
    source: myapp
    build_args:
      DEVICE: gpu
```

### Q: 如何禁用漏洞扫描？

A: 在手动触发构建时设置 `skip_scan: true`，或使用 `push: false` 仅构建不推送。

### Q: 时间戳标签可以自定义格式吗？

A: 当前固定格式为 `yyyymmddHHMMSS`，如需其他格式请联系维护者。

---

## 相关文档

- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
- [README.md](../README.md) - 项目说明