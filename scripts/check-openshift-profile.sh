#!/usr/bin/env bash
# Read-only namespace API/RBAC preflight, NOT live operator health.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: bash scripts/check-openshift-profile.sh {m09-vm|m13-mesh|m14-knative|m15-cdc}" >&2
  exit 64
fi
profile="$1"
case "$profile" in
  m09-vm|m13-mesh|m14-knative|m15-cdc) ;;
  *) echo "Unknown profile: $profile" >&2; exit 64 ;;
esac
command -v oc >/dev/null || { echo "BLOCKED: oc CLI is not installed"; exit 2; }
namespace="$(oc project -q 2>/dev/null)" || { echo "BLOCKED: no selected Project"; exit 2; }
identity="$(oc whoami 2>/dev/null)" || { echo "BLOCKED: oc login missing/expired"; exit 2; }
if [[ -z "$namespace" || -z "$identity" ]]; then
  echo "BLOCKED: no namespace or identity"
  exit 2
fi
echo "Profile: $profile"
echo "Current Project: $namespace"
echo "These are API discovery + namespace RBAC checks ONLY (no Secrets displayed)."

resources="$(oc api-resources --namespaced=true -o name 2>/dev/null)" || {
  echo "BLOCKED: could not list namespaced API types"
  exit 2
}
failures=0
check_api() {
  local kind="$1"
  if printf '%s\n' "$resources" | grep -Fxq -- "$kind"; then
    echo "PASS api $kind"
  else
    echo "BLOCKED api $kind (not installed/visible)"
    failures=$((failures + 1))
  fi
}
check_can() {
  local verb="$1" kind="$2" result
  result="$(oc auth can-i "$verb" "$kind" -n "$namespace" 2>/dev/null)" || result="unknown"
  if [[ "$result" == "yes" ]]; then
    echo "PASS rbac $verb $kind"
  else
    echo "BLOCKED rbac $verb $kind ($result)"
    failures=$((failures + 1))
  fi
}
check_can create deployments.apps
check_can create services
check_can create secrets
case "$profile" in
  m09-vm)
    check_api virtualmachines.kubevirt.io
    check_api datavolumes.cdi.kubevirt.io
    check_can create virtualmachines.kubevirt.io
    check_can create datavolumes.cdi.kubevirt.io
    check_can create routes.route.openshift.io
    ;;
  m13-mesh)
    for kind in virtualservices.networking.istio.io destinationrules.networking.istio.io peerauthentications.security.istio.io authorizationpolicies.security.istio.io; do
      check_api "$kind"
      check_can create "$kind"
    done
    check_can patch deployments.apps
    ;;
  m14-knative)
    for kind in brokers.eventing.knative.dev triggers.eventing.knative.dev kafkasources.sources.knative.dev; do
      check_api "$kind"
      check_can create "$kind"
    done
    check_can create buildconfigs.build.openshift.io
    ;;
  m15-cdc)
    check_can create buildconfigs.build.openshift.io
    check_can create serviceaccounts
    echo "MANUAL: Verify two PostgreSQL databases, Debezium connector, Kafka topics, Elasticsearch and network access."
    ;;
esac
if (( failures > 0 )); then
  echo "BLOCKED: $failures unmet API/RBAC prerequisite(s). Do not escalate or install cluster-scoped operators in a shared Sandbox."
  exit 2
fi
echo "PASS capability preflight ONLY. Still verify operator health, template/catalog, external dependencies, quota, images and end-to-end lab assertions."
