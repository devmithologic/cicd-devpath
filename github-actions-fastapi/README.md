# GitHub Actions + FastAPI CI/CD Pipeline

[![CI/CD Pipeline](https://github.com/devmithologic/cicd-devpath/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/devmithologic/cicd-devpath/actions/workflows/ci-cd.yml)
[![codecov](https://codecov.io/gh/devmithologic/cicd-devpath/branch/main/graph/badge.svg)](https://codecov.io/gh/devmithologic/cicd-devpath)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://hub.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Complete CI/CD pipeline implementation using GitHub Actions for automated testing, building, and deployment of a FastAPI application.

---

## 🎯 Project Overview

This project demonstrates a **production-ready CI/CD pipeline** from code commit to container registry, implementing industry best practices for:

- Automated testing with coverage reporting
- Docker multi-stage builds optimized for Python/Poetry
- Multi-tag container image strategy
- GitHub Container Registry integration
- Security scanning and quality gates

### Pipeline Architecture

> 📊 **[View Detailed Pipeline Diagrams](./docs/pipeline-architecture.md)** - Interactive Mermaid diagrams showing complete workflow

```
┌─────────────┐
│  Git Push   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  GitHub Actions Trigger │
└──────┬──────────────────┘
       │
       ├──► Job 1: Test
       │    ├─ Setup Python 3.12
       │    ├─ Cache Poetry dependencies
       │    ├─ Run pytest with coverage
       │    └─ Upload coverage to Codecov
       │
       ├──► Job 2: Build (if tests pass)
       │    ├─ Setup Docker Buildx
       │    ├─ Login to GHCR
       │    ├─ Extract metadata (tags/labels)
       │    ├─ Build multi-stage image
       │    └─ Push to GitHub Container Registry
       │
       └──► Job 3: Deploy (planned)
            └─ Deploy to AWS ECS
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Application** | FastAPI 0.104+, Uvicorn |
| **Language** | Python 3.12+ |
| **Dependency Management** | Poetry |
| **Testing** | pytest, pytest-cov, httpx |
| **Containerization** | Docker (multi-stage builds) |
| **CI/CD** | GitHub Actions |
| **Container Registry** | GitHub Container Registry (GHCR) |
| **Code Coverage** | Codecov |

---

## 📋 Features Implemented

### ✅ Continuous Integration (CI)

- **Automated Testing**: Runs on every push and pull request
- **Code Coverage**: Measures and reports test coverage (currently 100%)
- **Dependency Caching**: Poetry dependencies cached for faster builds
- **Matrix Testing**: Ready to test across multiple Python versions

### ✅ Continuous Delivery (CD)

- **Docker Multi-Stage Builds**: 
  - Builder stage with Poetry
  - Runtime stage with only production dependencies
  - Non-root user for security
  
- **Smart Image Tagging**:
```
  ghcr.io/devmithologic/fastapi-cicd:main         # Branch name
  ghcr.io/devmithologic/fastapi-cicd:sha-abc123   # Git commit SHA
  ghcr.io/devmithologic/fastapi-cicd:latest       # Latest stable
```

- **Layer Caching**: GitHub Actions cache for faster rebuilds

- **OCI Labels**: Automatic metadata for traceability
```
  org.opencontainers.image.created
  org.opencontainers.image.source
  org.opencontainers.image.revision
```

---

## 🚀 Local Development

### Prerequisites

- Python 3.12+
- Poetry
- Docker (optional)

### Setup
```bash
# Clone the repository
git clone https://github.com/devmithologic/cicd-devpath.git
cd cicd-devpath/github-actions-fastapi

# Install dependencies
poetry install

# Activate virtual environment
eval $(poetry env activate)
```

### Run the Application
```bash
# Development mode with auto-reload
poetry run uvicorn app.main:app --reload

# Access the application
# API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Run Tests
```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 🐳 Docker

### Build Locally
```bash
docker build -t fastapi-cicd:local .
```

### Run Container
```bash
docker run -d -p 8000:8000 --name fastapi-app fastapi-cicd:local

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health

# View logs
docker logs fastapi-app

# Stop and remove
docker stop fastapi-app
docker rm fastapi-app
```

### Pull from Registry
```bash
# Pull latest image
docker pull ghcr.io/devmithologic/fastapi-cicd:latest

# Run production image
docker run -d -p 8000:8000 ghcr.io/devmithologic/fastapi-cicd:latest
```

---

## 📦 Dependency Management Workflow

This project uses **Poetry** for development and **requirements.txt** for Docker builds.

### Why This Approach?

- **poetry.lock** → Source of truth for all dependencies
- **requirements.txt** → Lighter Docker images (no Poetry in production)
- **Consistency** → requirements.txt generated from poetry.lock

### Updating Dependencies
```bash
# Add new dependency
poetry add <package>

# Update existing dependencies
poetry update

# Regenerate requirements.txt
./update-requirements.sh

# Commit both files
git add poetry.lock requirements.txt
git commit -m "deps: update dependencies"
```

---

## 🔄 CI/CD Pipeline Details

### Triggers
```yaml
on:
  push:
    branches: [ main, develop ]    # Build and deploy
  pull_request:
    branches: [ main ]             # Test only
```

### Jobs

#### 1️⃣ Test Job

**Purpose**: Validate code quality and functionality

**Steps**:
1. Checkout code
2. Setup Python 3.11
3. Cache Poetry dependencies
4. Install Poetry
5. Install project dependencies
6. Run pytest with coverage
7. Upload coverage to Codecov

**Runtime**: ~1-2 minutes (with cache)

---

#### 2️⃣ Build Job

**Purpose**: Build and publish Docker image

**Runs**: Only on push (not PRs)  
**Depends on**: Test job must pass

**Steps**:
1. Checkout code
2. Setup Docker Buildx
3. Login to GitHub Container Registry
4. Extract metadata (generate tags/labels)
5. Build multi-stage Docker image
6. Push to GHCR with multiple tags

**Runtime**: ~2-3 minutes (with cache)

---

### Caching Strategy

**Poetry Dependencies**:
```yaml
cache-key: ${{ runner.os }}-poetry-${{ hashFiles('poetry.lock') }}
```
- Cache invalidates when poetry.lock changes
- ~90% faster dependency installation

**Docker Layers**:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```
- Caches intermediate Docker layers
- ~50% faster image builds

---

## 🏗️ Docker Image Strategy

### Multi-Stage Build Benefits

| Stage | Purpose | Size Impact |
|-------|---------|-------------|
| **Builder** | Install Poetry, build dependencies | +200MB (discarded) |
| **Runtime** | Copy only virtualenv + app code | ~150-180MB (final) |

### Security Practices
```dockerfile
# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Minimal base image
FROM python:3.11-slim

# No Poetry in production
# Only pip + requirements.txt
```

---

## 📊 Monitoring & Observability

### Current Implementation

- ✅ **Test Coverage**: Tracked via Codecov
- ✅ **Build Status**: GitHub Actions badges
- ✅ **Image Labels**: OCI metadata for traceability

### Planned

- 🔲 Application Performance Monitoring (APM)
- 🔲 Log aggregation (CloudWatch)
- 🔲 Container metrics (Prometheus)
- 🔲 Distributed tracing (Jaeger)

---

## 🔐 Security Considerations

### Implemented

- ✅ Non-root container user
- ✅ Multi-stage builds (smaller attack surface)
- ✅ Dependency pinning via poetry.lock
- ✅ Automated dependency updates (Dependabot - planned)

### Secrets Management
```yaml
# GitHub Actions secrets used:
GITHUB_TOKEN          # Auto-provided by GitHub
AWS_ACCESS_KEY_ID     # For AWS deployment (planned)
AWS_SECRET_ACCESS_KEY # For AWS deployment (planned)
```

---

## 📈 Performance Metrics

### Build Times (with cache)

| Job | Duration |
|-----|----------|
| Test | ~1-2 min |
| Build | ~2-3 min |
| **Total** | **~3-5 min** |

### Image Sizes
```
Builder stage:  ~400 MB  (discarded)
Runtime stage:  ~170 MB  (final)
```

---

## 🎓 Key Learnings

### DevOps Best Practices Demonstrated

1. **Separation of Concerns**
   - Test job validates code
   - Build job creates artifacts
   - Deploy job handles infrastructure

2. **Fail Fast Principle**
   - Tests run before build
   - Build runs before deploy
   - Each stage gates the next

3. **Immutable Artifacts**
   - Docker images tagged with commit SHA
   - Enables rollback to any previous version

4. **Declarative Configuration**
   - Everything in code (YAML)
   - Version controlled
   - Reproducible

### Technical Challenges Solved

| Challenge | Solution |
|-----------|----------|
| Slow dependency installation | Poetry caching with hashFiles() |
| Large Docker images | Multi-stage builds |
| Tag management complexity | docker/metadata-action |
| Monorepo structure | Explicit context paths |

---

## 🔮 Roadmap

### Phase 1: CI/CD Foundation ✅
- [x] FastAPI application with tests
- [x] Docker containerization
- [x] GitHub Actions pipeline
- [x] Container registry integration

### Phase 2: Quality & Security 🚧
- [ ] Security scanning (Trivy)
- [ ] Dependency vulnerability checks
- [ ] Linting and formatting (ruff, black)
- [ ] Pre-commit hooks

### Phase 3: Cloud Deployment 📋
- [ ] AWS ECS deployment
- [ ] Infrastructure as Code (Terraform)
- [ ] Environment management (dev/staging/prod)
- [ ] Blue-green deployment strategy

### Phase 4: Observability 📋
- [ ] Application metrics (Prometheus)
- [ ] Log aggregation (CloudWatch/ELK)
- [ ] Distributed tracing
- [ ] Performance monitoring

---

## 📚 Resources

### Official Documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Poetry Documentation](https://python-poetry.org/)

### Related Projects
- [Main Repository](https://github.com/devmithologic/cicd-devpath) - Complete CI/CD learning path
- [Jenkins + K8s Project](../jenkins-k8s-helm/) - Alternative CI/CD approach

---

## 🤝 Contributing

This is a learning project, but feedback and suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -m 'Add some improvement'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Alejandro Zamudio**
- DevOps Engineer with 4+ years experience
- Specializing in CI/CD automation and container orchestration
- [GitHub](https://github.com/devmithologic)
- [LinkedIn](https://linkedin.com/in/aazamudi)

---

## 🙏 Acknowledgments

This project was built as part of my DevOps/SRE career development path, documenting real-world CI/CD implementation patterns used in enterprise environments.

---

**Last Updated**: January 2026
