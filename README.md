# 镜像工厂 (Image Factory)

容器镜像自动化构建系统，从外部仓库构建 Docker 镜像并推送到 quay.io。

## 功能

- 从外部 Git 仓库构建容器镜像
- 支持 x86_64 和 ARM64 多架构并行构建
- 自动漏洞扫描和 SBOM 生成
- 定时构建、配置变更触发、手动触发

## 项目结构

```
image-factory/
├── .github/workflows/
│   └── build-images.yml     # GitHub Actions 构建工作流
├── config/
│   └── *-images.yml         # 镜像构建配置文件
├── docs/
│   ├── ARCHITECTURE.md      # 架构设计文档
│   ├── CONFIGURATION.md     # 配置说明文档
│   └── PRD.md               # 产品需求文档
├── scripts/
│   ├── clone-sources.py     # 克隆源仓库
│   ├── scan-dockerfiles.py  # 生成构建矩阵
│   └── validate-config.py   # 校验配置文件
├── CLAUDE.md                # Claude Code 开发指南
├── CONTRIBUTING.md          # 贡献指南
└── README.md                # 本文档
```

## 文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `.github/workflows/build-images.yml` | GitHub Actions 工作流定义 |
| `config/*-images.yml` | 镜像构建配置，每个项目一个文件 |
| `scripts/clone-sources.py` | 根据配置克隆源代码仓库 |
| `scripts/scan-dockerfiles.py` | 扫描 Dockerfile 生成构建矩阵 |
| `scripts/validate-config.py` | 本地校验配置文件格式 |
| `docs/ARCHITECTURE.md` | 系统架构和执行流程 |
| `docs/CONFIGURATION.md` | 配置项详细说明 |

## 快速开始

1. 在 `config/` 目录创建配置文件
2. 本地校验：`python3 scripts/validate-config.py config/<project>-images.yml`
3. 提交配置文件，自动触发构建

详细步骤请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 相关文档

| 文档 | 说明 |
|------|------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 配置说明文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计文档 |

## License

MIT