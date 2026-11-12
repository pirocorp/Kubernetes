.DEFAULT_GOAL := help
.PHONY: help tools up verify status down reset load
help:
	@printf '%s\n' 'Kind Kubernetes 1.37 / Calico 3.33 lab:' '  make tools                      - preflight' '  make up                         - create/reuse cluster' '  make verify                     - check Kubernetes and Calico' '  make status                     - list nodes and Pods' '  make down                       - delete cluster only' '  make reset                      - destroy and recreate' '  make load IMAGE=your/app:dev    - load local Docker image'
tools:
	@bash scripts/lab.sh tools
up:
	@bash scripts/lab.sh up
verify:
	@bash scripts/lab.sh verify
status:
	@bash scripts/lab.sh status
down:
	@bash scripts/lab.sh down
reset:
	@bash scripts/lab.sh reset
load:
	@bash scripts/lab.sh load "$(IMAGE)"
