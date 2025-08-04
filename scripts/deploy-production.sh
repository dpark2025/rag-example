#!/bin/bash

# Production Deployment Script for RAG System
# Performs zero-downtime deployment with safety checks

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_TYPE="${1:-docker-compose}"  # docker-compose or kubernetes
ENVIRONMENT="${2:-production}"
DRY_RUN="${3:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Starting pre-deployment checks..."
    
    # Check required tools
    for tool in docker curl jq; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is required but not installed"
        fi
    done
    
    if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        if ! command -v kubectl &> /dev/null; then
            error "kubectl is required for Kubernetes deployment"
        fi
        
        # Check cluster connectivity
        if ! kubectl cluster-info &> /dev/null; then
            error "Cannot connect to Kubernetes cluster"
        fi
    fi
    
    # Check environment file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        error ".env file not found. Copy .env.example and configure it."
    fi
    
    # Validate environment variables
    source "$PROJECT_ROOT/.env"
    required_vars=("SECRET_KEY" "API_SECRET_KEY" "JWT_SECRET" "REDIS_PASSWORD")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable $var is not set"
        fi
    done
    
    # Check SSL certificates for production
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ ! -f "$PROJECT_ROOT/ssl/rag-system.crt" ] || [ ! -f "$PROJECT_ROOT/ssl/rag-system.key" ]; then
            warn "SSL certificates not found. HTTPS will not work."
        else
            # Check certificate expiry
            cert_expiry=$(openssl x509 -enddate -noout -in "$PROJECT_ROOT/ssl/rag-system.crt" | cut -d= -f2)
            cert_expiry_epoch=$(date -d "$cert_expiry" +%s)
            current_epoch=$(date +%s)
            days_until_expiry=$(( (cert_expiry_epoch - current_epoch) / 86400 ))
            
            if [ $days_until_expiry -lt 30 ]; then
                warn "SSL certificate expires in $days_until_expiry days"
            fi
        fi
    fi
    
    success "Pre-deployment checks passed"
}

# Health check function
health_check() {
    local service_url="$1"
    local max_attempts="${2:-30}"
    local attempt=1
    
    log "Performing health check for $service_url"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$service_url" > /dev/null; then
            success "Health check passed for $service_url"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed for $service_url after $max_attempts attempts"
}

# Backup before deployment
create_pre_deployment_backup() {
    log "Creating pre-deployment backup..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] Would create backup"
        return 0
    fi
    
    # Create backup with timestamp
    backup_name="pre-deployment-$(date +%Y%m%d_%H%M%S)"
    
    if [ -x "$PROJECT_ROOT/backup-scripts/backup.sh" ]; then
        BACKUP_NAME="$backup_name" "$PROJECT_ROOT/backup-scripts/backup.sh"
        success "Pre-deployment backup created: $backup_name"
    else
        warn "Backup script not found or not executable"
    fi
}

# Docker Compose deployment
deploy_docker_compose() {
    log "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] Would run: docker-compose -f docker-compose.production.yml up -d"
        return 0
    fi
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Start monitoring stack first
    log "Starting monitoring stack..."
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Wait for monitoring to be ready
    sleep 30
    
    # Deploy main application with rolling update
    log "Starting main application..."
    docker-compose -f docker-compose.production.yml up -d --remove-orphans
    
    # Wait for services to be ready
    sleep 60
    
    # Health checks
    health_check "http://localhost:8000/health"
    health_check "http://localhost:3000/_health"
    
    success "Docker Compose deployment completed"
}

# Kubernetes deployment
deploy_kubernetes() {
    log "Deploying to Kubernetes..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] Would apply Kubernetes manifests"
        kubectl apply -k "$PROJECT_ROOT/k8s/overlays/$ENVIRONMENT" --dry-run=client
        return 0
    fi
    
    # Apply configurations
    log "Applying Kubernetes manifests..."
    kubectl apply -k "$PROJECT_ROOT/k8s/overlays/$ENVIRONMENT"
    
    # Wait for rollout
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available deployment --all -n rag-system --timeout=600s
    
    # Get service endpoints
    local backend_url=$(kubectl get svc rag-rag-backend-service -n rag-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    local frontend_url=$(kubectl get svc rag-reflex-service -n rag-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -n "$backend_url" ]; then
        health_check "http://$backend_url:8000/health"
    fi
    
    if [ -n "$frontend_url" ]; then
        health_check "http://$frontend_url:3000/_health"
    fi
    
    success "Kubernetes deployment completed"
}

# Post-deployment verification
post_deployment_verification() {
    log "Running post-deployment verification..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] Would run post-deployment tests"
        return 0
    fi
    
    # Run functional tests
    if [ -x "$PROJECT_ROOT/scripts/functional-test.sh" ]; then
        log "Running functional tests..."
        "$PROJECT_ROOT/scripts/functional-test.sh"
    else
        warn "Functional test script not found"
    fi
    
    # Performance test
    log "Running basic performance test..."
    if command -v ab &> /dev/null; then
        ab -n 10 -c 2 http://localhost:8000/health || warn "Performance test failed"
    else
        warn "Apache Bench not available for performance testing"
    fi
    
    # Check monitoring
    if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        success "Prometheus is healthy"
    else
        warn "Prometheus health check failed"
    fi
    
    if curl -f -s http://localhost:3001/api/health > /dev/null; then
        success "Grafana is healthy"
    else
        warn "Grafana health check failed"
    fi
    
    success "Post-deployment verification completed"
}

# Rollback function
rollback() {
    error_msg="$1"
    warn "Deployment failed: $error_msg"
    warn "Initiating rollback..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        # Find latest backup
        latest_backup=$(find /backup/output -name "pre-deployment-*.tar.gz" | sort -r | head -1)
        if [ -n "$latest_backup" ]; then
            log "Rolling back to: $latest_backup"
            "$PROJECT_ROOT/backup-scripts/restore.sh" "$latest_backup"
        else
            warn "No pre-deployment backup found for rollback"
        fi
    elif [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        # Kubernetes rollback
        kubectl rollout undo deployment --all -n rag-system
        kubectl rollout status deployment --all -n rag-system --timeout=300s
    fi
    
    error "Deployment failed and rollback attempted"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    
    # Remove old images (keep last 3)
    if command -v docker &> /dev/null; then
        docker image prune -f
        docker system prune -f --volumes
    fi
    
    # Clean old backups (keep last 10)
    find /backup/output -name "pre-deployment-*.tar.gz" | sort -r | tail -n +11 | xargs rm -f
}

# Main deployment function
main() {
    trap 'rollback "Script interrupted"' INT TERM
    
    log "Starting RAG System deployment"
    log "Deployment type: $DEPLOYMENT_TYPE"
    log "Environment: $ENVIRONMENT"
    log "Dry run: $DRY_RUN"
    
    # Run deployment steps
    pre_deployment_checks
    create_pre_deployment_backup
    
    case "$DEPLOYMENT_TYPE" in
        "docker-compose")
            deploy_docker_compose
            ;;
        "kubernetes")
            deploy_kubernetes
            ;;
        *)
            error "Invalid deployment type: $DEPLOYMENT_TYPE. Use 'docker-compose' or 'kubernetes'"
            ;;
    esac
    
    post_deployment_verification
    cleanup
    
    success "RAG System deployment completed successfully!"
    
    # Display access information
    echo
    log "Access Information:"
    if [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        echo "  Frontend: http://localhost:3000"
        echo "  API: http://localhost:8000"
        echo "  Grafana: http://localhost:3001"
        echo "  Prometheus: http://localhost:9090"
    else
        echo "  Check 'kubectl get ingress -n rag-system' for external URLs"
    fi
    echo
}

# Script usage
usage() {
    echo "Usage: $0 [deployment-type] [environment] [dry-run]"
    echo
    echo "Parameters:"
    echo "  deployment-type: docker-compose or kubernetes (default: docker-compose)"
    echo "  environment: production, staging, or development (default: production)"
    echo "  dry-run: true or false (default: false)"
    echo
    echo "Examples:"
    echo "  $0 docker-compose production"
    echo "  $0 kubernetes production true"
    echo "  $0 docker-compose staging"
    exit 1
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
fi

# Run main function
main "$@"