# 镜像工厂 (Image Factory)

通用化的容器镜像自动化构建系统，支持多仓库、多架构、安全扫描和 SBOM 生成。

## 功能特性

- **源码分离**：Dockerfile 存放在外部仓库，通过配置文件声明
- **多架构支持**：同时支持 x86_64 和 arm64 架构
- **安全扫描**：Trivy 漏洞扫描 + SBOM 生成
- **灵活触发**：定时构建 + 手动触发 + 配置变更触发
- **临时仓库**：支持手动输入仓库 URL 一次性构建

## 快速开始

### 1. 配置 GitHub Secrets

| Secret 名称 | 说明 |
|------------|------|
| `QUAY_USERNAME` | quay.io 用户名 |
| `QUAY_ROBOT_TOKEN` | quay.io Robot Token |
| `SSH_DEPLOY_KEY_*` | 私有仓库 Deploy Key（可选） |

### 2. 配置 GitHub Variables

| 变量名 | 说明 |
|--------|------|
| `QUAY_ORG` | quay.io 组织名 |

### 3. 编辑配置文件

编辑 `config/images.yaml`，添加源仓库和镜像配置。

### 4. 触发构建

- **自动**：每日 UTC 2:00（北京时间 10:00）
- **手动**：GitHub Actions -> Run workflow

## 使用方式

### 配置驱动模式

在 `config/images.yaml` 中定义源仓库和镜像：

```yaml
sources:
  - name: base-images
    url: https://github.com/your-org/base-images.git
    branch: main

images:
  - name: centos9-python
    source: base-images
    dockerfile: python/Dockerfile
    tags:
      - latest
      - "3.12"
```

### 临时仓库模式

手动触发时输入仓库地址，无需修改配置：

```
repo_url: https://github.com/user/test-images.git
repo_branch: main
repo_dockerfile: python/Dockerfile
push: false
```

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
gh workflow run build-images.yml -f image=centos9-python -f push=false

# 临时仓库构建
gh workflow run build-images.yml \
  -f repo_url=https://github.com/user/test-images.git \
  -f push=false
```

## 构建产物

每次构建生成以下产物（保留 30 天）：

| 产物 | 说明 |
|------|------|
| `trivy-report-<image>.txt` | 漏洞扫描报告 |
| `sbom-<image>.spdx.json` | SPDX 格式 SBOM |
| `sbom-<image>.cdx.json` | CycloneDX 格式 SBOM |

## License

MIT