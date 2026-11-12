#!/usr/bin/env bash
# Disposable Kubernetes 1.37.0 / Calico 3.33 VXLAN lab on Ubuntu Docker.
# All kubectl calls target the explicit kind-course-lab context.
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
NAME=course-lab
CTX=kind-course-lab
CONFIG="$ROOT/kind-config.yaml"
CALICO="$ROOT/calico-installation.yaml"
CALICO_BASE="https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests"

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
has_cluster() { kind get clusters 2>/dev/null | grep -Fxq "$NAME"; }
kc() { kubectl --context "$CTX" "$@"; }

preflight() {
  local tool
  for tool in docker kind kubectl curl; do
    command -v "$tool" >/dev/null 2>&1 || die "Missing $tool; see README prerequisites."
  done
  docker info >/dev/null 2>&1 || die "Docker daemon not accessible. Check Docker Engine and your user permissions."
  kind version | grep -Eq '(^|[[:space:]])v0\.33\.0([[:space:]]|$)' ||
    die "Use kind v0.33.0 with pinned node image, found: $(kind version)"
  log "Docker and kind v0.33.0 available; no host changes performed"
}

install_calico() (
  set -Eeuo pipefail
  local dir
  dir="$(mktemp -d)"
  trap 'rm -rf -- "$dir"' EXIT
  if ! kc get crd installations.operator.tigera.io >/dev/null 2>&1; then
    log "Downloading Calico 3.33.0 CRDs, Kubernetes >= 1.36 format"
    curl -fSLs --retry 3 "$CALICO_BASE/v3_projectcalico_org.yaml" -o "$dir/crds.yaml"
    test -s "$dir/crds.yaml" || die "Calico CRD bundle download failed"
    kc create -f "$dir/crds.yaml"
  fi
  if ! kc -n tigera-operator get deployment tigera-operator >/dev/null 2>&1; then
    log "Installing Tigera Operator v3.33.0"
    curl -fSLs --retry 3 "$CALICO_BASE/tigera-operator.yaml" -o "$dir/operator.yaml"
    test -s "$dir/operator.yaml" || die "Calico Operator download failed"
    kc create -f "$dir/operator.yaml"
  fi
  kc wait --for=condition=Established crd/installations.operator.tigera.io --timeout=180s
  kc -n tigera-operator rollout status deployment/tigera-operator --timeout=300s
  if ! kc get installation.operator.tigera.io default >/dev/null 2>&1; then
    log "Configuring Calico VXLAN + BGP Disabled, Pod CIDR 10.244.0.0/16"
    kc apply -f "$CALICO"
  fi
)

verify() {
  command -v kubectl >/dev/null || die "kubectl not installed"
  log "Checking explicitly selected $CTX (never the current default context)"
  kc cluster-info
  kc get nodes -o wide
  local count version bgp vxlan cidr
  count="$(kc get nodes -o name | wc -l | tr -d ' ')"
  local control_planes workers
  control_planes="$(kc get nodes -l node-role.kubernetes.io/control-plane -o name | wc -l | tr -d ' ')"
  workers="$((count - control_planes))"
  [[ "$control_planes" == 1 && "$workers" -ge 3 ]] ||
    die "Expected exactly 1 Control Plane and at least 3 Workers; found ${control_planes} Control Planes and ${workers} Workers"
  kc wait --for=condition=Ready nodes --all --timeout=420s
  version="$(kc get node course-lab-control-plane -o jsonpath='{.status.nodeInfo.kubeletVersion}')"
  [[ "$version" == v1.37.0 ]] || die "Wrong Kubernetes version: $version"
  bgp="$(kc get installation.operator.tigera.io default -o jsonpath='{.spec.calicoNetwork.bgp}')"
  vxlan="$(kc get installation.operator.tigera.io default -o jsonpath='{.spec.calicoNetwork.ipPools[0].encapsulation}')"
  cidr="$(kc get installation.operator.tigera.io default -o jsonpath='{.spec.calicoNetwork.ipPools[0].cidr}')"
  [[ "$bgp" == Disabled && "$vxlan" == VXLAN && "$cidr" == 10.244.0.0/16 ]] ||
    die "Calico settings differ: bgp=$bgp, encapsulation=$vxlan, cidr=$cidr"
  kc -n calico-system rollout status daemonset/calico-node --timeout=420s
  kc -n kube-system rollout status deployment/coredns --timeout=240s
  log "PASS: 1 control plane + at least 3 workers Ready, Kubernetes v1.37.0, Calico VXLAN, CoreDNS"
  kc get storageclass
}

up() {
  preflight
  if has_cluster; then
    log "Cluster course-lab already exists. Reusing; use 'make reset' to apply changed node config."
  else
    log "Creating Kubernetes v1.37.0 as 4 Docker container nodes (1 control plane + 3 workers)"
    kind create cluster --name "$NAME" --config "$CONFIG"
  fi
  kc cluster-info >/dev/null || die "Context $CTX unreachable. Check 'kind export logs --name $NAME'."
  install_calico
  verify
}

down() {
  command -v kind >/dev/null || die "kind missing"
  if has_cluster; then
    log "Deleting ONLY kind cluster course-lab; its Pods and volumes are disposable"
    kind delete cluster --name "$NAME"
  else
    log "Cluster course-lab does not exist; nothing to remove"
  fi
}

status() {
  command -v kind >/dev/null || die "kind missing"
  if has_cluster; then
    kc get nodes -o wide
    kc get pods -A
  else
    log "Not running. Start with 'make up'."
  fi
}

load_image() {
  local image="${1:-}"
  [[ -n "$image" ]] || die "Use: make load IMAGE=your-app:dev"
  has_cluster || die "First run 'make up'"
  docker image inspect "$image" >/dev/null || die "Local Docker image not found: $image"
  kind load docker-image --name "$NAME" "$image"
}

case "${1:-}" in
  tools) preflight ;;
  up) up ;;
  verify) verify ;;
  status) status ;;
  down) down ;;
  reset) down; up ;;
  load) load_image "${2:-}" ;;
  *) die "Usage: bash scripts/lab.sh {tools|up|verify|status|down|reset|load IMAGE}" ;;
esac
