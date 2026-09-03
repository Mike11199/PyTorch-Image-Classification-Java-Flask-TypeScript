# PyTorch image classification CDK

Three containers run as one ECS task on one Spot `t3.medium` EC2 instance. Brief release and Spot-recovery downtime is accepted.

The retained-resource migration is complete. The deployment workflow is active for normal repository, image, and application deployments.

## Ownership

```text
PytorchRepositoryStack
└── retained ECR repository: pytorch-web

PytorchClassificationStack
├── retained root A-alias
├── listener rule and target group
├── ECS cluster, task definition, and service
├── fixed one-host Spot Auto Scaling Group
├── Launch Template and capacity provider
└── application security group
```

Shared CDK owns the VPC, public subnets, ALB security group, hosted zone, certificate, ALB, and listeners.

- Shared IDs are consumed through CloudFormation exports; production network and listener IDs are not stored in source.
- `PytorchRepositoryStack` exports `PytorchRepositoryUri` for immutable container image tags.
- Dependencies are one-way: shared infrastructure, then repository, image pushes, then application.

## Containers

- Nginx serves React and proxies backend requests over task-local `localhost`.
- Java Spring Boot handles `/api-java-spring-boot/*` and calls Flask on port 5000.
- Flask/PyTorch serves inference on port 5000; model weights are cached during image build.
- The ALB health check uses Nginx `/health`; it is routing evidence, not an inference test.

## Host and release behavior

- ECS maintains one application task and replaces tasks for normal releases.
- The Auto Scaling Group keeps `min=1`, `desired=1`, and `max=1` and replaces an interrupted Spot host.
- The explicit Launch Template avoids the account-disabled legacy LaunchConfiguration path.
- `minimumHealthyPercent=0` and `maximumPercent=100` are required because two complete tasks do not fit on one host.
- Managed scaling and managed termination protection are disabled so stack deletion can scale the group to zero.
- The ECS service depends on the listener rule and Auto Scaling Group so routing and host capacity exist first.

## Existing account

- The existing ECR repository, listener rule, and target group were retained and imported without changing physical IDs.
- Shared identifiers now come from CloudFormation exports.
- Drift detection reports `IN_SYNC`; the final CDK diff is empty; target health and HTTPS are healthy.
- Do not rerun retained-resource import steps.

## Fresh environment

1. Deploy shared infrastructure.
2. Deploy `PytorchRepositoryStack`.
3. Build and push all three images.
4. Deploy `PytorchClassificationStack`.
5. Verify target health, HTTPS, Java routing, and inference.
