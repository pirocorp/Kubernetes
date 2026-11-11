# OpenShift/Knative resources for Module 13

This directory is intentionally **not** a global Operator installer.

- [workload.yaml](./workload.yaml): one namespaced .NET Deployment, ClusterIP Service, edge-TLS Route restricted to `/reviews`.
- [knative-eventing.yaml](./knative-eventing.yaml): namespaced Knative Broker, KafkaSource and two Triggers with HTTP callback paths.

**Prerequisites:** authorized OpenShift project, managed Kafka bootstrap address with all four pre-created topics, compatible access, installed Knative Eventing + KafkaSource CRDs, appropriate RBAC and quotas. The tutorial provides exact preflights, steps, verification and cleanup in [Lab 13-E](../labs/LAB-05-OPENSHIFT-KNATIVE.md).

**Important:** `REVIEWS_MODE=knative` means the .NET app publishes to Kafka but consumes incoming Kafka events only through Knative callbacks. It does not also start its own Kafka consumer groups. A KafkaSource transforms Kafka messages into CloudEvents and delivers via Broker/Triggers. The consumer method handles the nested JSON event. The HTTP callback endpoints stay inside the ClusterIP Service and are **not** reachable through the public Route.

The manifests do **not** install Kafka, PostgreSQL, InfluxDB, Grafana, an AI model server, Eventing Operators or cluster-scoped resources. These are separate platform components with their own privileges, lifecycle and security controls. Do not claim that this lab demonstrates a real trained ML model; the default scorer is a deterministic demo classifier.

Upstream specs: [Knative KafkaSource](https://knative.dev/docs/eventing/sources/kafka-source/) and [Knative Trigger](https://knative.dev/docs/eventing/triggers/).
