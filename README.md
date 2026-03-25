# 镜像工厂 (Image Factory)

通用化的容器镜像自动化构建系统，支持多仓库、多架构、安全扫描和 SBOM 生成。

## 功能特性

- **源码分离**：Dockerfile 存放在外部仓库，通过配置文件声明
- **多架构支持**：同时支持 x86_64 和 arm64 架构，使用原生 Runner 加速构建
- **安全扫描**：Trivy 漏洞扫描 + SBOM 生成（漏洞不影响镜像推送）
- **灵活触发**：定时构建 + 手动触发 + 配置变更触发
- **临时仓库**：支持手动输入仓库 URL 一次性构建
- **构建缓存**：Registry 缓存 + GitHub Actions 缓存双重加速

## 性能特性

| 架构 | Runner | 构建时间 |
|------|--------|----------|
| linux/amd64 | ubuntu-latest | ~1.5 分钟 |
| linux/arm64 | ubuntu-22.04-arm (原生 ARM) | ~40 秒 |

> 使用 GitHub 原生 ARM Runner 替代 QEMU 模拟，ARM 构建速度提升 20 倍以上。

## 快速开始

### 1. 配置 GitHub Secrets

| Secret 名称 | 说明 |
|------------|------|
| `QUAY_USERNAME` | quay.io 用户名（格式：`org+robot_name`） |
| `QUAY_ROBOT_TOKEN` | quay.io Robot Token |
| `SSH_DEPLOY_KEY_*` | 私有仓库 Deploy Key（可选） |

### 2. 配置 GitHub Variables

| 变量名 | 说明 |
|--------|------|
| `QUAY_ORG` | quay.io 组织名 |

### 3. 编辑配置文件

编辑 `config/images.yaml`，添加源仓库和镜像配置：

```yaml
# 全局配置
global:
  registry: quay.io
  organization: ${QUAY_ORG}
  platforms:
    - linux/amd64
    - linux/arm64

# 源仓库列表
sources:
  - name: my-images
    url: https://github.com/myorg/images.git
    branch: main

# 镜像构建配置
images:
  - name: myapp
    source: my-images
    dockerfile: myapp/Dockerfile
    tags:
      - x86-latest
      - x86-1.0
    platforms:
      - linux/amd64

  - name: myapp
    source: my-images
    dockerfile: myapp/Dockerfile.arm
    tags:
      - arm-latest
      - arm-1.0
    platforms:
      - linux/arm64
```

### 4. 触发构建

- **自动**：每日 UTC 2:00（北京时间 10:00）
- **手动**：GitHub Actions -> Run workflow
- **配置变更**：修改 `config/images.yaml` 自动触发

## 使用方式

### 配置驱动模式

在 `config/images.yaml` 中定义源仓库和镜像。

### 临时仓库模式

手动触发时输入仓库地址，无需修改配置：

```
repo_url: https://github.com/user/test-images.git
repo_branch: main
repo_dockerfile: python/Dockerfile
push: false
```

## 构建缓存

系统使用双重缓存策略加速构建：

| 缓存类型 | 说明 |
|----------|------|
| Registry 缓存 | `buildcache-amd64` / `buildcache-arm64` 标签 |
| GitHub Actions 缓存 | 构建层缓存 |

## 目录结构

```
image-factory/
├── .github/workflows/
│   └── build-images.yml    # GitHub Actions 工作流
├── config/
│   └── images.yaml         # 镜像配置文件
├── scripts/
│   ├── clone-sources.py    # 源仓库克隆脚本
│   ├── scan-dockerfiles.py # Dockerfile 扫描脚本
│   └── validate-config.py  # 配置校验脚本
└── README.md
```

## 验证方法

```bash
# 验证配置文件
python3 scripts/validate-config.py config/images.yaml

# 手动触发构建
gh workflow run build-images.yml -f image=myapp -f push=false

# 临时仓库构建
gh workflow run build-images.yml \
  -f repo_url=https://github.com/user/test-images.git \
  -f push=false
```

## 构建产物

每次构建生成以下产物（保留 30 天）：

| 产物 | 命名格式 | 说明 |
|------|----------|------|
| Trivy 扫描报告 | `trivy-report-<tag>.txt` | 漏洞扫描结果 |
| SBOM (SPDX) | `sbom-<tag>.spdx.json` | SPDX 格式物料清单 |
| SBOM (CycloneDX) | `sbom-<tag>.cdx.json` | CycloneDX 格式物料清单 |

## 手动触发参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | string | 空 | 指定源仓库名称 |
| `image` | string | 空 | 指定镜像名称 |
| `repo_url` | string | 空 | 临时仓库地址 |
| `repo_branch` | string | main | 临时仓库分支 |
| `repo_dockerfile` | string | Dockerfile | Dockerfile 路径 |
| `push` | boolean | true | 是否推送到仓库 |
| `skip_scan` | boolean | false | 跳过安全扫描 |
| `skip_sbom` | boolean | false | 跳过 SBOM 生成 |

## License

MIT