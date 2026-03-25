---
name: add-image-config
description: 添加新仓库的镜像构建配置，自动生成配置文件并验证
user-invocable: true
---

# 添加新镜像配置

自动化添加新仓库的镜像构建配置。

## 触发条件

当用户请求以下内容时触发：
- "帮我添加 xxx 仓库的镜像配置"
- "给 xxx 项目添加镜像构建"
- "新增 xxx 的镜像配置"
- "为 xxx 仓库生成镜像配置"

## 执行步骤

### 1. 获取仓库信息

向用户确认或获取以下信息：
- 仓库地址（必需）：如 `https://github.com/org/repo.git`
- 分支名称（可选，默认 main）：如 `main`、`master`、`release/v1.0`
- 项目名称（可选，从仓库名提取）

### 2. 克隆仓库并分析

```bash
# 克隆到临时目录
git clone <repo_url> /tmp/<project_name>

# 查找 Dockerfile
find /tmp/<project_name> -name "Dockerfile*" -o -name "*.dockerfile"
```

分析内容：
- Dockerfile 位置
- 构建参数（ARG）
- 是否需要多架构支持

### 3. 生成配置文件

根据 `docs/CONFIGURATION.md` 格式生成配置文件 `config/<project>-images.yml`：

```yaml
# <项目名> 镜像构建配置
# 项目: <仓库地址>

sources:
  - name: <project>
    url: <repo_url>
    branch: <branch>

images:
  - name: <project>
    source: <project>
    dockerfile: <dockerfile_path>
    tags:
      - x86-nightly
    platforms:
      - linux/amd64
    build_args:
      <key>: <value>  # 如果有构建参数

build:
  severity: CRITICAL,HIGH
  timeout: 60

sbom:
  enabled: true
  formats:
    - spdx
    - cyclonedx
```

### 4. 验证配置

```bash
# 使用虚拟环境中的 Python
.venv/Scripts/python scripts/validate-config.py config/<project>-images.yml
```

如果虚拟环境不存在，先创建：
```bash
uv venv .venv
uv pip install pyyaml
```

### 5. 提交并推送

```bash
git add config/<project>-images.yml
git commit -m "config: 添加 <project> 镜像构建配置"
git push origin main
```

### 6. 确认结果

告知用户：
- 配置文件位置
- 镜像标签格式
- 触发构建的方式

## 配置文件规范

参考 `docs/CONFIGURATION.md` 文档。

### 标签命名规范

- 使用 `nightly` 而非 `latest`
- 包含架构标识：`x86-nightly`、`arm-nightly`
- 包含版本标识：`x86-v1.0`、`arm-v1.0`

### 多架构配置

如果需要多架构支持，分别配置：

```yaml
images:
  - name: myapp
    source: myapp
    dockerfile: docker/Dockerfile
    tags: [x86-nightly]
    platforms: [linux/amd64]

  - name: myapp
    source: myapp
    dockerfile: docker/Dockerfile.arm
    tags: [arm-nightly]
    platforms: [linux/arm64]
```

## 注意事项

1. **构建上下文**：默认使用仓库根目录，如果 Dockerfile 需要访问上级目录文件，需配置 `context` 字段
2. **私有仓库**：需要配置 SSH 密钥或访问令牌
3. **构建超时**：复杂项目建议设置 `timeout: 60` 或更长
4. **构建参数**：从 Dockerfile 中提取 ARG 变量作为 build_args

## 示例对话

```
用户: 帮我添加 triton-ascend 仓库的镜像配置

助手: 好的，我来帮你添加 triton-ascend 的镜像配置。

请确认以下信息：
- 仓库地址：https://gitcode.com/Ascend/triton-ascend.git
- 分支：main
- 是否需要多架构支持？

[克隆仓库并分析 Dockerfile...]

找到 Dockerfile: docker/Dockerfile
检测到构建参数: CHIP_TYPE=A3, CANN_VERSION=8.5.0

[生成配置文件...]
[验证配置...]
[提交推送...]

配置已添加完成！
- 配置文件：config/triton-ascend-images.yml
- 镜像标签：quay.io/kerer/triton-ascend:x86-nightly-<timestamp>
```