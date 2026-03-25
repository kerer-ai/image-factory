# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Image Factory is a container image automation build system that builds Docker images from external repositories and pushes them to quay.io. It supports multi-architecture builds (amd64/arm64) using native GitHub runners.

## Architecture

```
config/images.yaml → GitHub Actions → Build Matrix → Multi-arch Images → quay.io
```

**Two build modes:**
- **Config-driven**: Sources defined in `config/images.yaml`, triggered by schedule/config change
- **Temporary repo**: Manual trigger with `repo_url` parameter for one-time builds

**Multi-arch strategy:**
- `linux/amd64` runs on `ubuntu-latest`
- `linux/arm64` runs on `ubuntu-22.04-arm` (native ARM, not QEMU emulation)

Each platform gets a separate matrix job with its own runner, enabling parallel builds.

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/clone-sources.py` | Clones source repos from config or temp URL |
| `scripts/scan-dockerfiles.py` | Scans Dockerfiles and generates build matrix JSON |
| `scripts/validate-config.py` | Validates `config/images.yaml` schema |

## Configuration File

`config/images.yaml` is the single source of truth. Structure:

```yaml
global:
  registry: quay.io
  organization: ${QUAY_ORG}
  platforms: [linux/amd64, linux/arm64]

sources:
  - name: repo-name
    url: https://github.com/org/repo.git
    branch: main

images:
  - name: image-name
    source: repo-name
    dockerfile: path/to/Dockerfile
    tags: [tag1, tag2]
    platforms: [linux/amd64]  # optional override
```

## Build Matrix Generation

`scan-dockerfiles.py` generates a matrix where **each platform becomes a separate job**:

```json
{
  "matrix": [
    {
      "image_name": "myapp",
      "dockerfile": "sources/repo/Dockerfile",
      "context": "sources/repo",
      "tags": "type=raw,value=latest\ntype=raw,value=v1.0",
      "first_tag": "latest",
      "platforms": "linux/amd64",
      "runner": "ubuntu-latest"
    },
    {
      "image_name": "myapp",
      "platforms": "linux/arm64",
      "runner": "ubuntu-22.04-arm"
    }
  ]
}
```

## Common Commands

```bash
# Validate config
python3 scripts/validate-config.py config/images.yaml

# Trigger manual build
gh workflow run build-images.yml -f push=true

# Build specific image
gh workflow run build-images.yml -f image=myapp -f push=false

# Temporary repo build
gh workflow run build-images.yml \
  -f repo_url=https://github.com/user/repo.git \
  -f repo_dockerfile=Dockerfile \
  -f push=false

# Check build status
gh run list --workflow=build-images.yml --limit 5
```

## Build Caching

Uses dual caching:
1. **Registry cache**: `buildcache-amd64` / `buildcache-arm64` tags
2. **GitHub Actions cache**: For layer reuse

## Build Artifacts

Artifacts are named by the first tag (not image name) to avoid collisions:
- `trivy-report-<tag>.txt`
- `sbom-<tag>.spdx.json`
- `sbom-<tag>.cdx.json`

## GitHub Secrets Required

- `QUAY_USERNAME`: quay.io username (format: `org+robot_name`)
- `QUAY_ROBOT_TOKEN`: quay.io Robot Token
- `SSH_DEPLOY_KEY_*`: For private repos (optional)

## GitHub Variables Required

- `QUAY_ORG`: quay.io organization name