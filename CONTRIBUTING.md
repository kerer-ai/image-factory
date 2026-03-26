# 贡献指南

感谢你对镜像工厂项目的关注！本文档将帮助你了解如何为项目做出贡献。

## 目录

- [开发环境准备](#开发环境准备)
- [添加新镜像配置](#添加新镜像配置)
- [本地校验配置](#本地校验配置)
- [提交规范](#提交规范)
- [代码风格](#代码风格)

---

## 开发环境准备

### 必需工具

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| uv | 最新版 | Python 包管理器（推荐） |
| Git | 2.0+ | 版本控制 |

### 安装 uv

uv 是一个快速的 Python 包管理器，用于管理虚拟环境和依赖。

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**其他安装方式:** 参见 [uv 官方文档](https://docs.astral.sh/uv/getting-started/installation/)

### 创建虚拟环境

```bash
# 克隆仓库
git clone https://github.com/kerer-ai/image-factory.git
cd image-factory

# 创建虚拟环境并安装依赖
uv venv
uv pip install pyyaml
```

---

## 添加新镜像配置

### 步骤 1: 创建配置文件

在 `config/` 目录下创建新的配置文件，命名格式为 `<project>-images.yml`：

```bash
# 示例：添加 TensorFlow 镜像配置
touch config/tensorflow-images.yml
```

### 步骤 2: 编写配置内容

```yaml
# config/tensorflow-images.yml

sources:
  - name: tensorflow
    url: https://github.com/tensorflow/tensorflow.git
    branch: master

images:
  - name: tensorflow
    source: tensorflow
    dockerfile: tensorflow/tools/docker/Dockerfile
    tags:
      - x86-latest
    platforms:
      - linux/amd64
```

详细配置说明请参考 [配置说明文档](docs/CONFIGURATION.md)。

### 步骤 3: 本地校验

在提交前，使用 `validate-config.py` 脚本校验配置文件格式。

**激活虚拟环境并运行校验：**

```bash
# 激活虚拟环境
# macOS / Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 运行校验
python scripts/validate-config.py config/tensorflow-images.yml
```

**或者使用 uv run 直接运行（无需激活环境）：**

```bash
uv run python scripts/validate-config.py config/tensorflow-images.yml
```

**成功输出示例**：

```
✓ Config validation passed!
  Sources: 1
  Images:  1
```

**失败输出示例**：

```
Errors:
  - Source 0: missing 'url'
  - Image 0: source 'nonexistent' not found in sources
```

### 步骤 4: 提交变更

```bash
git add config/tensorflow-images.yml
git commit -m "config: 添加 TensorFlow 镜像构建配置"
git push origin main
```

---

## 本地校验配置

### 校验工具

`scripts/validate-config.py` 用于校验配置文件格式和完整性。

### 使用方式

```bash
# 方式一：激活虚拟环境后运行
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate   # Windows

python scripts/validate-config.py config/<project>-images.yml

# 方式二：使用 uv run 直接运行（无需激活）
uv run python scripts/validate-config.py config/<project>-images.yml

# 示例
uv run python scripts/validate-config.py config/pytorch-images.yml
```

### 校验内容

| 检查项 | 说明 |
|--------|------|
| 文件存在 | 配置文件是否存在 |
| YAML 格式 | YAML 语法是否正确 |
| sources 必需字段 | 每个源必须有 `name` 和 `url` |
| images 必需字段 | 每个镜像必须有 `name` 和 `source` |
| 引用完整性 | image 的 source 必须在 sources 中定义 |

### 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 校验通过 |
| 1 | 校验失败 |

### 在 CI/CD 中使用

校验脚本已集成到 GitHub Actions workflow 中，每次构建前会自动校验配置文件。

### 校验所有配置

```bash
# 校验所有配置文件
for config in config/*-images.yml; do
  echo "Validating $config..."
  uv run python scripts/validate-config.py "$config" || exit 1
done
```

---

## 提交规范

### Commit Message 格式

```
<type>: <subject>

[optional body]
```

### Type 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat: 添加多架构构建支持 |
| `fix` | Bug 修复 | fix: 修复缓存配置错误 |
| `config` | 配置变更 | config: 添加 TensorFlow 镜像配置 |
| `docs` | 文档更新 | docs: 更新 README |
| `refactor` | 代码重构 | refactor: 简化构建流程 |
| `chore` | 杂项 | chore: 更新依赖版本 |

### 示例

```bash
# 添加新镜像配置
git commit -m "config: 添加 TensorFlow 镜像构建配置"

# 修复 Bug
git commit -m "fix: 修复 ARM 构建缓存路径错误"

# 更新文档
git commit -m "docs: 添加配置说明文档"
```

---

## 代码风格

### Python 代码

- 使用 4 空格缩进
- 遵循 PEP 8 规范
- 添加类型注解（推荐）

### YAML 配置

- 使用 2 空格缩进
- 列表项前加空行（可选）
- 添加注释说明配置用途

### Shell 脚本

- 使用 2 空格缩进
- 变量使用 `${VAR}` 格式
- 添加错误处理

---

## 项目结构

```
image-factory/
├── .github/
│   └── workflows/
│       └── build-images.yml    # GitHub Actions 工作流
├── config/
│   └── *-images.yml            # 镜像配置文件
├── docs/
│   ├── ARCHITECTURE.md         # 架构设计文档
│   ├── CONFIGURATION.md        # 配置说明文档
│   └── PRD.md                  # 产品需求文档
├── scripts/
│   └── validate-config.py      # 配置校验脚本（本地开发工具）
├── CLAUDE.md                   # Claude Code 指南
├── CONTRIBUTING.md             # 本文档
└── README.md                   # 项目说明
```

---

## 获取帮助

- 查看项目文档：[docs/](docs/)
- 提交 Issue：[GitHub Issues](https://github.com/kerer-ai/image-factory/issues)
- 查看 Workflow 执行：[GitHub Actions](https://github.com/kerer-ai/image-factory/actions)

---

感谢你的贡献！