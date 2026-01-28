# Pipeline Architecture

Complete visual documentation of the CI/CD pipeline implementation.

---

## High-Level Overview
```mermaid
graph TB
    DEV[Developer] -->|git push| GH[GitHub Repository]
    GH -->|webhook| GHA[GitHub Actions]
    
    subgraph "CI/CD Pipeline"
        GHA --> TEST[Test Job]
        TEST -->|pass| BUILD[Build Job]
        BUILD -->|pass| DEPLOY[Deploy Job]
        TEST -->|fail| NOTIFY1[Notify Failure]
        BUILD -->|fail| NOTIFY2[Notify Failure]
    end
    
    BUILD --> GHCR[GitHub Container Registry]
    DEPLOY --> AWS[AWS ECS]
    
    style TEST fill:#90EE90
    style BUILD fill:#87CEEB
    style DEPLOY fill:#FFB6C1
    style GHCR fill:#FFA500
    style AWS fill:#FF6B6B
```

---

## Detailed Pipeline Flow

### 1. Trigger Events
```mermaid
flowchart LR
    A[Git Action] --> B{Event Type?}
    B -->|Push to main/develop| C[Run Test + Build]
    B -->|Pull Request to main| D[Run Test Only]
    B -->|Push to other branch| E[No Action]
    
    style C fill:#90EE90
    style D fill:#87CEEB
    style E fill:#FFB6C1
```

**Trigger Configuration:**
```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
```

---

### 2. Job Dependencies
```mermaid
flowchart TB
    START([Push to Repository]) --> TEST
    
    subgraph "Job: Test"
        TEST[Run Tests]
        TEST --> T1[Setup Python]
        T1 --> T2[Cache Dependencies]
        T2 --> T3[Install Poetry]
        T3 --> T4[Install Dependencies]
        T4 --> T5[Run pytest]
        T5 --> T6[Upload Coverage]
    end
    
    TEST -->|Pass| BUILD
    TEST -->|Fail| FAIL1[❌ Pipeline Failed]
    
    subgraph "Job: Build"
        BUILD[Build Docker Image]
        BUILD --> B1[Setup Buildx]
        B1 --> B2[Login to GHCR]
        B2 --> B3[Extract Metadata]
        B3 --> B4[Build Image]
        B4 --> B5[Push to Registry]
    end
    
    BUILD -->|Pass| DEPLOY
    BUILD -->|Fail| FAIL2[❌ Pipeline Failed]
    
    subgraph "Job: Deploy"
        DEPLOY[Deploy to AWS]
        DEPLOY --> D1[Update ECS Task]
        D1 --> D2[Deploy Service]
        D2 --> D3[Health Check]
    end
    
    DEPLOY -->|Pass| SUCCESS[✅ Pipeline Complete]
    DEPLOY -->|Fail| FAIL3[❌ Deployment Failed]
    
    style TEST fill:#90EE90
    style BUILD fill:#87CEEB
    style DEPLOY fill:#FFB6C1
    style SUCCESS fill:#32CD32
    style FAIL1 fill:#FF6B6B
    style FAIL2 fill:#FF6B6B
    style FAIL3 fill:#FF6B6B
```

---

## Job Details

### Job 1: Test

**Purpose**: Validate code quality and functionality
```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant Cache as Cache Storage
    participant Poetry as Poetry
    participant Pytest as Pytest
    participant Codecov as Codecov
    
    GHA->>GHA: Checkout code
    GHA->>GHA: Setup Python 3.11
    GHA->>Cache: Check for cached dependencies
    
    alt Cache Hit
        Cache->>GHA: Restore dependencies
    else Cache Miss
        GHA->>Poetry: Install Poetry
        Poetry->>Poetry: poetry install
        Poetry->>Cache: Save to cache
    end
    
    GHA->>Pytest: poetry run pytest --cov
    Pytest->>Pytest: Run 2 tests
    Pytest->>GHA: Tests passed ✅
    Pytest->>GHA: Generate coverage.xml
    GHA->>Codecov: Upload coverage report
    Codecov->>Codecov: Process coverage
```

**Key Metrics:**
- Runtime: ~1-2 minutes (with cache)
- Coverage: 100%
- Tests: 2 passing

---

### Job 2: Build

**Purpose**: Create production-ready Docker image
```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant Docker as Docker Buildx
    participant Meta as Metadata Action
    participant GHCR as GitHub Container Registry
    
    GHA->>GHA: Checkout code
    GHA->>Docker: Setup Docker Buildx
    GHA->>GHCR: docker login ghcr.io
    GHCR->>GHA: Authentication success
    
    GHA->>Meta: Extract metadata
    Meta->>Meta: Generate tags from branch/SHA
    Meta->>GHA: Return tags & labels
    
    Note over Meta,GHA: Tags:<br/>- main<br/>- sha-abc123<br/>- latest
    
    GHA->>Docker: Build image (multi-stage)
    
    rect rgb(200, 220, 250)
        Note over Docker: Stage 1: Builder<br/>Install Poetry + Dependencies
    end
    
    rect rgb(180, 230, 200)
        Note over Docker: Stage 2: Runtime<br/>Copy venv + App code
    end
    
    Docker->>GHA: Image built successfully
    GHA->>GHCR: Push image with tags
    GHCR->>GHA: Push complete
```

**Key Metrics:**
- Runtime: ~2-3 minutes (with cache)
- Image Size: ~170 MB
- Tags Generated: 3 (branch, SHA, latest)

---

## Docker Build Strategy

### Multi-Stage Build Process
```mermaid
graph LR
    subgraph "Stage 1: Builder"
        A[python:3.11-slim] --> B[Install Poetry]
        B --> C[Copy pyproject.toml<br/>poetry.lock]
        C --> D[poetry install]
        D --> E[virtualenv created<br/>~200MB]
    end
    
    subgraph "Stage 2: Runtime"
        F[python:3.11-slim] --> G[Copy virtualenv<br/>from builder]
        G --> H[Copy app/ code]
        H --> I[Create non-root user]
        I --> J[Final image<br/>~170MB]
    end
    
    E -.->|COPY --from=builder| G
    
    style E fill:#FFB6C1
    style J fill:#90EE90
```

**Why Multi-Stage?**

| Aspect | Single Stage | Multi-Stage |
|--------|--------------|-------------|
| Final Size | ~400 MB | ~170 MB |
| Contains Poetry? | ✅ Yes | ❌ No |
| Build Tools? | ✅ Yes | ❌ No |
| Security Surface | Large | Small |

---

## Image Tagging Strategy
```mermaid
graph TB
    COMMIT[Git Commit: abc123] --> META[Metadata Action]
    
    META --> TAG1[Branch Tag<br/>ghcr.io/.../app:main]
    META --> TAG2[SHA Tag<br/>ghcr.io/.../app:sha-abc123]
    META --> TAG3[Latest Tag<br/>ghcr.io/.../app:latest]
    
    TAG1 --> PUSH[Push to GHCR]
    TAG2 --> PUSH
    TAG3 --> PUSH
    
    PUSH --> USE1[Deploy Production<br/>Use: latest]
    PUSH --> USE2[Rollback Scenario<br/>Use: sha-abc123]
    PUSH --> USE3[Branch Testing<br/>Use: main]
    
    style TAG1 fill:#87CEEB
    style TAG2 fill:#90EE90
    style TAG3 fill:#FFB6C1
```

**Tag Strategy Benefits:**

| Tag Type | Use Case | Example |
|----------|----------|---------|
| `branch` | Environment-specific | `main`, `develop` |
| `sha-*` | Exact version tracking | `sha-abc123` |
| `latest` | Production default | `latest` |

---

## Caching Strategy

### Poetry Dependencies Cache
```mermaid
flowchart TB
    START[Workflow Start] --> CHECK{Cache Exists?}
    
    CHECK -->|Yes| HIT[Cache Hit]
    CHECK -->|No| MISS[Cache Miss]
    
    HIT --> RESTORE[Restore ~/.cache/pypoetry]
    RESTORE --> INSTALL[poetry install<br/>~10 seconds]
    
    MISS --> DOWNLOAD[Download dependencies]
    DOWNLOAD --> FULLINSTALL[poetry install<br/>~90 seconds]
    FULLINSTALL --> SAVE[Save to cache]
    
    INSTALL --> CONTINUE[Continue Pipeline]
    SAVE --> CONTINUE
    
    style HIT fill:#90EE90
    style MISS fill:#FFB6C1
```

**Cache Key:**
```yaml
key: ${{ runner.os }}-poetry-${{ hashFiles('poetry.lock') }}
```

**When Cache Invalidates:**
- ✅ poetry.lock changes
- ✅ OS changes (Linux → macOS)
- ❌ App code changes (no impact)

---

### Docker Layer Cache
```mermaid
flowchart LR
    subgraph "Build Process"
        A[Layer 1:<br/>Base Image] --> B[Layer 2:<br/>System Packages]
        B --> C[Layer 3:<br/>Copy requirements.txt]
        C --> D[Layer 4:<br/>pip install]
        D --> E[Layer 5:<br/>Copy app code]
    end
    
    subgraph "Cache Strategy"
        C -.->|Cached| CACHE1[GitHub Actions Cache]
        D -.->|Cached| CACHE2[GitHub Actions Cache]
    end
    
    style A fill:#FFE4B5
    style B fill:#FFE4B5
    style C fill:#90EE90
    style D fill:#90EE90
    style E fill:#87CEEB
```

**Layer Caching Benefits:**

| Scenario | Without Cache | With Cache |
|----------|---------------|------------|
| Fresh build | 180 seconds | 180 seconds |
| Code change | 180 seconds | 30 seconds |
| Dependency change | 180 seconds | 90 seconds |

---

## Security Flow
```mermaid
flowchart TB
    START[Container Starts] --> USER{Run as root?}
    
    USER -->|Yes| RISK[❌ Security Risk<br/>Full system access]
    USER -->|No| SAFE[✅ Non-root User<br/>Limited access]
    
    SAFE --> PERMS[File Permissions<br/>appuser:appuser]
    PERMS --> RUN[Run Application<br/>Port 8000]
    
    RUN --> EXPOSE{Port < 1024?}
    EXPOSE -->|Yes| NEEDROOT[❌ Needs root]
    EXPOSE -->|No| NOROOT[✅ User can bind]
    
    style RISK fill:#FF6B6B
    style SAFE fill:#90EE90
    style NEEDROOT fill:#FF6B6B
    style NOROOT fill:#90EE90
```

**Security Practices:**
```dockerfile
# ❌ Bad Practice
USER root
CMD ["uvicorn", "app.main:app", "--port", "80"]

# ✅ Good Practice
USER appuser
CMD ["uvicorn", "app.main:app", "--port", "8000"]
```

---

## Deployment Flow (Planned)
```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant ECR as AWS ECR
    participant ECS as AWS ECS
    participant ALB as Application Load Balancer
    participant HEALTH as Health Check
    
    GHA->>ECR: Push Docker image
    ECR->>GHA: Image stored
    
    GHA->>ECS: Update task definition
    ECS->>ECS: Create new task revision
    
    GHA->>ECS: Update service
    ECS->>ECS: Start new tasks
    
    ECS->>ALB: Register new targets
    ALB->>HEALTH: Perform health checks
    
    alt Health Check Pass
        HEALTH->>ALB: Targets healthy
        ALB->>ECS: Route traffic to new tasks
        ECS->>ECS: Drain old tasks
        ECS->>GHA: Deployment successful ✅
    else Health Check Fail
        HEALTH->>ALB: Targets unhealthy
        ALB->>ECS: Keep old tasks
        ECS->>GHA: Deployment failed ❌
        GHA->>ECS: Trigger rollback
    end
```

---

## Monitoring & Observability (Planned)
```mermaid
graph TB
    APP[FastAPI Application] --> LOGS[CloudWatch Logs]
    APP --> METRICS[Prometheus Metrics]
    APP --> TRACES[Distributed Tracing]
    
    LOGS --> DASH1[CloudWatch Dashboard]
    METRICS --> DASH2[Grafana Dashboard]
    TRACES --> DASH3[Jaeger UI]
    
    DASH1 --> ALERT[AlertManager]
    DASH2 --> ALERT
    DASH3 --> ALERT
    
    ALERT --> SLACK[Slack Notifications]
    ALERT --> PAGER[PagerDuty]
    
    style APP fill:#87CEEB
    style LOGS fill:#90EE90
    style METRICS fill:#90EE90
    style TRACES fill:#90EE90
    style ALERT fill:#FFB6C1
```

---

## Performance Metrics

### Build Time Breakdown
```mermaid
pie title Pipeline Duration (with cache)
    "Checkout & Setup" : 15
    "Test Execution" : 30
    "Docker Build" : 120
    "Image Push" : 45
    "Cleanup" : 10
```

**Total**: ~3.5 minutes

### Resource Usage
```mermaid
graph LR
    subgraph "GitHub Actions Runner"
        CPU[2 vCPU] --> MEM[7GB RAM]
        MEM --> DISK[14GB SSD]
    end
    
    subgraph "Resource Consumption"
        DISK --> CACHE[Cache: ~500MB]
        DISK --> IMAGE[Image: ~170MB]
        DISK --> BUILD[Build Artifacts: ~200MB]
    end
    
    style CPU fill:#87CEEB
    style MEM fill:#90EE90
    style DISK fill:#FFB6C1
```

---

## Cost Analysis

### GitHub Actions (Free Tier)

| Resource | Limit | Usage | Status |
|----------|-------|-------|--------|
| Minutes/month | 2,000 | ~100 | ✅ 5% |
| Storage | 500 MB | ~170 MB | ✅ 34% |
| Concurrent jobs | 20 | 1 | ✅ 5% |

**Estimated Monthly Cost**: $0 (within free tier)

---

## Error Handling

### Pipeline Failure Scenarios
```mermaid
flowchart TB
    START[Pipeline Start] --> TEST{Tests Pass?}
    
    TEST -->|No| T_FAIL[Test Failure]
    TEST -->|Yes| BUILD{Build Success?}
    
    T_FAIL --> T_NOTIFY[Notify: Test Failed<br/>❌ Stop Pipeline]
    
    BUILD -->|No| B_FAIL[Build Failure]
    BUILD -->|Yes| DEPLOY{Deploy Success?}
    
    B_FAIL --> B_NOTIFY[Notify: Build Failed<br/>❌ Stop Pipeline]
    
    DEPLOY -->|No| D_FAIL[Deploy Failure]
    DEPLOY -->|Yes| SUCCESS[✅ Success]
    
    D_FAIL --> ROLLBACK[Auto Rollback]
    ROLLBACK --> D_NOTIFY[Notify: Rolled Back<br/>⚠️ Previous Version Active]
    
    style T_FAIL fill:#FF6B6B
    style B_FAIL fill:#FF6B6B
    style D_FAIL fill:#FF6B6B
    style SUCCESS fill:#90EE90
```

---

## Comparison with Alternative Approaches

### GitHub Actions vs Jenkins

| Aspect | GitHub Actions | Jenkins |
|--------|----------------|---------|
| **Setup** | Zero infrastructure | Requires server |
| **Cost** | Free tier (2000 min) | Self-hosted costs |
| **Maintenance** | Managed by GitHub | Self-managed |
| **Integration** | Native GitHub | Plugins needed |
| **Scalability** | Auto-scales | Manual scaling |
| **Learning Curve** | Low (YAML) | Medium (Groovy) |

**When to use GitHub Actions:**
- ✅ GitHub-hosted repositories
- ✅ Simple to medium complexity
- ✅ Want zero maintenance

**When to use Jenkins:**
- ✅ Complex enterprise workflows
- ✅ Non-GitHub repositories
- ✅ Need full control

---

## Future Enhancements
```mermaid
timeline
    title Pipeline Evolution Roadmap
    
    Phase 1 (Current): CI/CD Foundation
        : Automated testing
        : Docker builds
        : Container registry
    
    Phase 2 (Next): Quality & Security
        : Security scanning
        : Code quality gates
        : Dependency updates
    
    Phase 3 (Q2): Cloud Deployment
        : AWS ECS integration
        : Multi-environment
        : Blue-green deployment
    
    Phase 4 (Q3): Advanced Features
        : Observability
        : Auto-scaling
        : Cost optimization
```

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [OCI Image Spec](https://github.com/opencontainers/image-spec)

---

**Last Updated**: January 2026
