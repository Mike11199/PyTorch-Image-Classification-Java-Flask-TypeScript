#!/bin/bash
# Bootstrap script for the PyTorch classification EC2 instance (run via cfn-init).
#
# Why this file exists:
#   On ECS/Fargate, AWS manages Docker lifecycle automatically — you define a task,
#   and the control plane handles pulling images, starting containers, restarting on failure,
#   and health checks. No startup scripts needed.
#
#   On EC2, we own the bare OS. This script manually does what ECS/Fargate would do for us:
#     - Installs Docker + Compose CLI plugin (ECS has Docker built-in)
#     - Configures ECR auth via instance role (Fargate handles this automatically)
#     - Pulls container images from our private ECR repo (service definitions reference images directly in ECS)
#     - Starts all 4 services via docker-compose (ECS task definition defines tasks + dependencies)
#     - Verifies containers are healthy before signaling success (ECS has built-in health checks)
#   In exchange for this manual work, we save ~$30/mo vs Fargate and get full OS access.
#
# How it runs:
#   Called by cfn-init on every newly launched ASG instance (initial boot or self-healing replacement).
#   Nonzero exit → cfn-signal FAILURE → CloudFormation rolls back / ASG replaces the instance automatically.

set -Eeuo pipefail

WORK_DIR="/opt/pytorch"
COMPOSE_FILE="$WORK_DIR/docker-compose.yml"
ENV_FILE="$WORK_DIR/runtime.env"
COMPOSE_VERSION="v2.29.7"

exec > >(tee -a /var/log/pytorch-bootstrap.log) 2>&1

echo "== Starting PyTorch classification bootstrap =="

log_step() { echo ">> $*" >&2; echo ">> $*" >>/dev/stderr; }
die() { log_step "ERROR: $*"; exit 1; }

# ---------------------------------------------------------------------------
# Load and validate environment variables
# ---------------------------------------------------------------------------
validate_env() {
    cd "$WORK_DIR"
    set -a
    # shellcheck disable=SC1091
    source "$ENV_FILE" || die "Failed to source $ENV_FILE"
    set +a

    for variable in REGISTRY FLASK_TAG JAVA_TAG REACT_TAG NGINX_TAG; do
        if [ -z "${!variable:-}" ]; then
            die "Missing required variable: $variable"
        fi
    done
}

# ---------------------------------------------------------------------------
# Install Docker, Compose CLI plugin, and ECR credential helper
# ---------------------------------------------------------------------------
install_docker() {
    log_step "Installing Docker..."
    dnf install -y docker amazon-ecr-credential-helper || die "dnf install failed"
    systemctl enable --now docker || die "Failed to start Docker daemon"

    if ! docker compose version >/dev/null 2>&1; then
        machine_arch="$(uname -m)"
        case "$machine_arch" in
            x86_64) compose_arch="x86_64" ;;
            aarch64) compose_arch="aarch64" ;;
            *) die "Unsupported architecture: $machine_arch" ;;
        esac

        install -d -m 0755 /usr/local/lib/docker/cli-plugins
        curl --fail --location --retry 3 \
            "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${compose_arch}" \
            --output /usr/local/lib/docker/cli-plugins/docker-compose || die "Failed to download Docker Compose"
        chmod 0755 /usr/local/lib/docker/cli-plugins/docker-compose
    fi

    docker --version
    docker compose version
}

# ---------------------------------------------------------------------------
# Configure ECR auth via IMDSv2 credential helper (EC2 role supplies tokens)
# ---------------------------------------------------------------------------
configure_ecr_auth() {
    log_step "Configuring ECR auth..."
    registry_host="${REGISTRY%%/*}"
    install -d -m 0700 /root/.docker
    printf '{"credHelpers":{"%s":"ecr-login"}}\n' "$registry_host" > /root/.docker/config.json || die "Failed to write docker config"
    chmod 0600 /root/.docker/config.json
}

# ---------------------------------------------------------------------------
# Pull images with retry (ECR auth can take ~120s on fresh boot)
# ---------------------------------------------------------------------------
pull_images() {
    log_step "Pulling Docker images..."
    local max_retries=12
    for attempt in $(seq 1 "$max_retries"); do
        echo "Docker compose pull attempt $attempt/$max_retries..." >&2
        if docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" pull; then
            return 0
        fi
        echo "Pull failed (attempt $attempt), sleeping 15s before retry..." >&2
        sleep 15
    done

    die "Docker compose pull failed after $max_retries attempts."
}

# ---------------------------------------------------------------------------
# Start containers via docker-compose
# ---------------------------------------------------------------------------
start_services() {
    log_step "Starting services with docker-compose..."
    docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" up -d --remove-orphans || die "docker compose up failed."
}

# ---------------------------------------------------------------------------
# Verify a specific service is running the expected image
# ---------------------------------------------------------------------------
verify_service_image() {
    local service="$1"
    local expected_image="$2"
    local container_id actual_image

    container_id="$(docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" ps -q "$service")" || return 1
    [ -n "$container_id" ] || return 1

    actual_image="$(docker inspect --format '{{.Config.Image}}' "$container_id")" || return 1
    if [ "$actual_image" != "$expected_image" ]; then
        echo "Image mismatch for $service: expected $expected_image, found $actual_image" >&2
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Health checks: all services running + nginx answers /health
# ---------------------------------------------------------------------------
wait_for_health() {
    log_step "Waiting for health check..."
    local max_attempts=30
    for attempt in $(seq 1 "$max_attempts"); do
        running_services="$(docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" ps --status running --services | wc -l)" || true

        if [ "$running_services" -eq 4 ] && \
            verify_service_image "flask-backend" "$REGISTRY:$FLASK_TAG" && \
            verify_service_image "java-backend" "$REGISTRY:$JAVA_TAG" && \
            verify_service_image "react-frontend" "$REGISTRY:$REACT_TAG" && \
            verify_service_image "reverse-proxy" "$REGISTRY:$NGINX_TAG" && \
            curl --fail --silent --show-error http://127.0.0.1/health; then
            echo "" >&2
            docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" ps
            echo "== Bootstrap completed successfully ==" >&2
            return 0
        fi

        echo "Health check $attempt/$max_attempts: $running_services/4 services running; retrying in 10 seconds..." >&2
        sleep 10
    done

    die "Bootstrap verification failed after $max_attempts attempts."
}

# ---------------------------------------------------------------------------
# Emit diagnostics on failure (called only via trap or explicit call)
# ---------------------------------------------------------------------------
emit_diagnostics() {
    echo "" >&2
    echo "=== DIAGNOSTICS ===" >&2
    docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" ps || true
    docker compose --env-file "$ENV_FILE" --file "$COMPOSE_FILE" logs --tail=100 || true
    curl --fail http://127.0.0.1/health || true
}

# ---------------------------------------------------------------------------
# Main: run steps sequentially; trap for diagnostics on failure
# ---------------------------------------------------------------------------
trap 'emit_diagnostics' ERR EXIT

validate_env
install_docker
configure_ecr_auth
pull_images
start_services
wait_for_health

echo "== Bootstrap finished successfully ==" >&2
exit 0
