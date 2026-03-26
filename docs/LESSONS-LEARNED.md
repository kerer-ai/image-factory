# 错误案例记录

本文档记录项目开发过程中遇到的问题及其解决方案，供后续参考。

---

## 案例 1：多配置文件只构建第一个（已通过架构简化解决）

### 问题描述

手动触发 workflow 不指定配置文件时，预期构建所有配置文件，但实际只构建了第一个配置（pytorch），未构建 triton-ascend。

### 问题定位

原 `scan-dockerfiles.py` 脚本和 workflow 逻辑中：

```yaml
# 错误代码
configs='${{ needs.prepare.outputs.configs }}'
first_config=$(echo "$configs" | jq -r '.[0]')  # ❌ 只取第一个！
python3 scripts/scan-dockerfiles.py \
  --config "$first_config" \
  ...
```

`.[0]` 只取了 JSON 数组的第一个元素，导致后续配置被忽略。

### 解决方案

**最终方案**：简化架构，移除 Python 脚本依赖，使用 yq + shell 在 workflow 中直接处理：

```yaml
# 直接使用 yq 解析所有配置文件
for config in ${{ steps.detect.outputs.configs }}; do
  # 解析配置并生成矩阵
  yq eval '.images[] | ...' "config/$config"
done
```

### 经验教训

- 处理列表/数组时，注意是否需要遍历全部元素
- 复杂逻辑可以考虑简化，减少外部脚本依赖

---

## 案例 2：产物命名冲突风险

### 问题描述

构建产物（Trivy 报告、SBOM、build-info）使用 `first_tag` 命名，当配置了相同 `name` + `tags` 但不同 `platforms` 时会导致 artifact 冲突。

### 问题场景

```yaml
# 危险配置示例
images:
  - name: myapp
    tags: [latest]
    platforms: [linux/amd64]
  - name: myapp
    tags: [latest]
    platforms: [linux/arm64]  # ❌ 产物会冲突！
```

两个镜像的 `first_tag` 都是 `latest-20260325100000`，上传 artifact 时会冲突。

### 解决方案

产物命名添加平台后缀：

```yaml
name: trivy-report-${{ steps.tags.outputs.first_tag_with_timestamp }}-${{ matrix.platforms }}
name: sbom-${{ steps.tags.outputs.first_tag_with_timestamp }}-${{ matrix.platforms }}
name: build-info-${{ steps.tags.outputs.first_tag_with_timestamp }}-${{ matrix.platforms }}
```

### 经验教训

- 多架构构建时，平台差异可能带来命名冲突
- 使用 matrix 变量命名产物时，确保包含区分因素（如 platform）

---

## 案例 3：远端 Registry 残留 -local Tag

### 问题描述

每次构建后，quay.io 上会出现两个 tag：
- `arm-manylinux2014-nightly-20260325101512`（正常）
- `arm-manylinux2014-nightly-20260325101512-local`（残留）

### 问题定位

原代码为扫描多架构镜像创建了远端 tag：

```yaml
# 错误代码
- name: Pull image for scanning
  run: |
    docker buildx imagetools create --tag ...-local ...  # 在远端创建 tag
    docker pull --platform ...

- name: Remove local tag
  run: |
    docker buildx imagetools rm ...-local || true  # 删除失败但被忽略
```

问题原因：
1. quay.io 可能不支持 `imagetools rm` 删除 tag
2. `|| true` 吞掉了错误，导致问题被掩盖

### 解决方案

使用 `docker pull --platform` 直接拉取特定平台镜像，无需创建额外 tag：

```yaml
- name: Pull image for scanning
  run: |
    docker pull --platform ${{ matrix.platforms }} ${{ env.REGISTRY }}/${{ env.ORG }}/${{ matrix.image_name }}:${{ steps.tags.outputs.first_tag_with_timestamp }}
```

> Docker 20.10+ 支持从 manifest list 直接拉取特定平台镜像。

### 经验教训

- 避免在远端创建临时资源，清理逻辑可能失败
- `|| true` 会掩盖错误，应谨慎使用
- 优先使用原生能力（如 `--platform`）而非 workaround

---

## 检查清单

在修改 workflow 时，检查以下要点：

- [ ] 多配置/多镜像场景是否全部处理
- [ ] artifact 命名是否唯一（考虑 name + tag + platform 组合）
- [ ] 是否有远端资源的创建和清理逻辑
- [ ] 错误处理是否恰当（避免 `|| true` 掩盖问题）