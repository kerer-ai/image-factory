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
├── .claude/skills/
│   └── add-image-config.md   # Claude Code skill
├── .github/workflows/
│   └── build-images.yml      # GitHub Actions 构建工作流
├── config/
│   └── *-images.yml          # 镜像构建配置文件
├── docs/
│   ├── ARCHITECTURE.md       # 架构设计文档
│   ├── CONFIGURATION.md      # 配置说明文档
│   ├── LESSONS-LEARNED.md    # 错误案例记录
│   └── PRD.md                # 产品需求文档
├── scripts/
│   └── validate-config.py    # 校验配置文件（本地开发工具）
├── CLAUDE.md                 # Claude Code 开发指南
├── CONTRIBUTING.md           # 贡献指南
└── README.md                 # 本文档
```

## 文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `.claude/skills/add-image-config.md` | Claude Code skill，自动化添加镜像配置 |
| `.github/workflows/build-images.yml` | GitHub Actions 工作流定义 |
| `config/*-images.yml` | 镜像构建配置，每个项目一个文件 |
| `scripts/validate-config.py` | 本地校验配置文件格式 |
| `docs/ARCHITECTURE.md` | 系统架构和执行流程 |
| `docs/CONFIGURATION.md` | 配置项详细说明 |
| `docs/LESSONS-LEARNED.md` | 错误案例记录和经验教训 |

## 快速开始

### 方式一：使用 Claude Code 自动添加

如果你使用 [Claude Code](https://claude.ai/code)，可以直接告诉 Claude：

```
帮我添加 xxx 仓库的镜像配置
```

Claude 会自动执行以下步骤：
1. 克隆目标仓库并分析 Dockerfile 位置和构建参数
2. 生成符合规范的配置文件 `config/<project>-images.yml`
3. 验证配置格式
4. 提交并推送到远端

**支持的触发方式**：
- "帮我添加 xxx 仓库的镜像配置"
- "给 xxx 项目添加镜像构建"
- "新增 xxx 的镜像配置"

详见 [.claude/skills/add-image-config.md](.claude/skills/add-image-config.md)。

### 方式二：手动添加

1. 安装 [uv](https://docs.astral.sh/uv/)（Python 包管理器）
2. 创建虚拟环境并安装依赖：
   ```bash
   uv venv
   uv pip install pyyaml
   ```
3. 在 `config/` 目录创建配置文件
4. 本地校验：
   ```bash
   uv run python scripts/validate-config.py config/<project>-images.yml
   ```
5. 提交配置文件，自动触发构建

详细步骤请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 相关文档

| 文档 | 说明 |
|------|------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 配置说明文档 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计文档 |
| [docs/LESSONS-LEARNED.md](docs/LESSONS-LEARNED.md) | 错误案例记录 |

## License

MIT