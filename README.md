# 镜像工厂 (Image Factory)

通用化的容器镜像自动化构建系统，支持多配置文件、多架构、安全扫描和 SBOM 生成。

## 功能特性

- **多配置文件**：每个项目独立配置文件，互不影响
- **源码分离**：Dockerfile 存放在外部仓库，通过配置文件声明
- **多架构支持**：同时支持 x86_64 和 arm64 架构，使用原生 Runner 加速构建
- **安全扫描**：Trivy 漏洞扫描 + SBOM 生成（漏洞不影响镜像推送）
- **灵活触发**：定时构建 + 手动触发 + 配置变更触发
- **构建缓存**：Registry 缓存 + GitHub Actions 缓存双重加速

## 性能特性

| 架构 | Runner | 构建时间 |
|------|--------|----------|
| linux/amd64 | ubuntu-latest | ~1.5 分钟 |
| linux/arm64 | ubuntu-22.04-arm (原生 ARM) | ~40 秒 |

> 使用 GitHub 原生 ARM Runner 替代 QEMU 模拟，ARM 构建速度提升 20 倍以上。

## 配置文件

配置文件位于 `config/` 目录，命名为 `*-images.yml`：

```
config/
├── pytorch-images.yml      # PyTorch 项目配置
├── tensorflow-images.yml   # TensorFlow 项目配置
└── ...
```

每个配置文件独立完整：

```yaml
# config/pytorch-images.yml
sources:
  - name: pytorch
    url: https://github.com/org/pytorch.git
    branch: main

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

### 配置项说明

| 配置项 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `sources[].name` | string | 是 | 源仓库名称（唯一标识） |
| `sources[].url` | string | 是 | 仓库地址 |
| `sources[].branch` | string | 否 | 分支名，默认 main |
| `images[].name` | string | 是 | 镜像名称 |
| `images[].source` | string | 是 | 引用的源仓库名称 |
| `images[].dockerfile` | string | 否 | Dockerfile 路径，默认 Dockerfile |
| `images[].tags` | list | 否 | 镜像标签列表（自动添加时间戳后缀） |
| `images[].platforms` | list | 否 | 目标平台 |

> 详细配置说明请参考 [配置说明文档](docs/CONFIGURATION.md)。

## 触发方式

| 触发类型 | 说明 |
|----------|------|
| 定时触发 | 每日 UTC 2:00（北京时间 10:00）构建所有配置 |
| 配置变更 | `config/*-images.yml` 变更时自动触发对应项目构建 |
| 手动触发 | 通过 GitHub Actions 界面手动执行 |

### 手动触发参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `config` | string | 空 | 配置文件名称（如 pytorch-images.yml，留空构建所有） |
| `push` | boolean | true | 是否推送到仓库 |
| `skip_scan` | boolean | false | 跳过安全扫描 |
| `skip_sbom` | boolean | false | 跳过 SBOM 生成 |

## 快速开始

### 1. 配置 GitHub Secrets

| Secret 名称 | 说明 |
|------------|------|
| `QUAY_USERNAME` | quay.io 用户名（格式：`org+robot_name`） |
| `QUAY_ROBOT_TOKEN` | quay.io Robot Token |

### 2. 配置 GitHub Variables

| 变量名 | 说明 |
|--------|------|
| `QUAY_ORG` | quay.io 组织名 |

### 3. 创建配置文件

在 `config/` 目录创建项目配置文件：

```bash
# 复制示例配置
cp config/pytorch-images.yml config/myproject-images.yml

# 编辑配置
vim config/myproject-images.yml
```

### 4. 触发构建

- **自动**：推送配置文件变更自动触发
- **手动**：GitHub Actions -> Run workflow -> 选择配置文件

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
│   ├── pytorch-images.yml  # PyTorch 镜像配置
│   └── *-images.yml        # 其他项目配置
├── docs/
│   ├── ARCHITECTURE.md     # 架构设计文档
│   ├── CONFIGURATION.md    # 配置说明文档
│   └── PRD.md              # 产品需求文档
├── scripts/
│   ├── clone-sources.py    # 源仓库克隆脚本
│   ├── scan-dockerfiles.py # Dockerfile 扫描脚本
│   └── validate-config.py  # 配置校验脚本
├── CONTRIBUTING.md         # 贡献指南
└── README.md
```

## 验证方法

```bash
# 验证配置文件
python3 scripts/validate-config.py config/pytorch-images.yml

# 手动触发指定配置
gh workflow run build-images.yml -f config=pytorch-images.yml

# 手动触发，不推送镜像
gh workflow run build-images.yml -f config=pytorch-images.yml -f push=false
```

## 构建产物

每次构建生成以下产物（保留 30 天）：

| 产物 | 命名格式 | 说明 |
|------|----------|------|
| Trivy 扫描报告 | `trivy-report-<tag>.txt` | 漏洞扫描结果 |
| SBOM (SPDX) | `sbom-<tag>.spdx.json` | SPDX 格式物料清单 |
| SBOM (CycloneDX) | `sbom-<tag>.cdx.json` | CycloneDX 格式物料清单 |

## License

MIT

## 文档

| 文档 | 说明 |
|------|------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 配置说明文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计文档 |