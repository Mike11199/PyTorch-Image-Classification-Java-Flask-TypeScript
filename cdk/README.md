# PyTorch Image Classification - CDK Deployment

Three containers run as one ECS task on a single Spot `t3.medium` EC2 instance. Estimated infrastructure cost is approximately 15 USD per month. The stack reuses the shared `consolidated-load-balancer`.

## Architecture

- ECS cluster: schedules and monitors the application task.
- ECS service: maintains one task containing Nginx, Java Spring Boot, and Flask/PyTorch.
- Auto Scaling Group: maintains exactly one ECS host (the ec2 we create not Fargate) with `min=1`, `desired=1`, and `max=1`.
- Launch Template: starts an ECS-optimized Amazon Linux 2023 Spot instance.
- Capacity provider: connects the Auto Scaling Group to the ECS cluster.
- Shared ALB: sends `machine-learning-projects.com` traffic to `NginxContainer:80`.

### Container responsibilities

- Nginx: serves the React build and proxies requests to the backends over task-local `localhost` connections.
- Java Spring Boot: handles `/api-java-spring-boot/*` and calls Flask on port 5000.
- Flask/PyTorch: runs image classification on port 5000. Model weights are cached during the Docker build because the task has no runtime internet route.

The target group uses `/health` on Nginx as a basic liveness check. It does not verify backend inference.

## ECS, EC2, and the Auto Scaling Group

This is ECS on EC2, not Fargate.

- ECS replaces failed containers and deploys new task-definition revisions.
- EC2 supplies the compute on which the task runs.
- The Auto Scaling Group replaces the EC2 host after a Spot interruption or host failure.

ECS on EC2 can use a manually managed instance, but ECS cannot replace a failed host by itself. Without the Auto Scaling Group, a Spot interruption would leave the service without capacity until an instance was created and registered manually.

Normal application deployments replace the ECS task on the existing EC2 host. They do not replace the Launch Template, Auto Scaling Group, or EC2 instance.

## Deployment and recovery behavior

- Application update: ECS stops the old task and starts the new revision on the same host.
- Deployment capacity: `minimumHealthyPercent=0` and `maximumPercent=100` because two complete tasks do not fit on one `t3.medium`. Brief deployment downtime is expected.
- Task startup failure: the ECS deployment circuit breaker fails the deployment. An update can roll back to the previous task revision; a first stack creation rolls back the stack.
- Spot interruption or host failure: the Auto Scaling Group launches a replacement host, which registers with ECS and receives the task.
- Stack creation: the ECS service depends on the listener rule and Auto Scaling Group so task deployment does not begin before ALB routing and EC2 capacity exist.
- Stack deletion: managed scaling and managed termination protection are disabled. CloudFormation can scale the Auto Scaling Group to zero and terminate the instance without manual intervention.
- Host termination: CDK creates an ECS draining lifecycle hook using SNS and Lambda. These resources run only during host termination; they are not application services.

## Load balancer cutover

The stack creates a priority-10 rule for `machine-learning-projects.com`. An older priority-3 rule for the same host takes precedence until it is removed or changed manually.

## File responsibilities

- `stack.py`: ECS cluster, task definition, service, Launch Template, fixed Auto Scaling Group, capacity provider, target group, and listener rule.
- `existing_resources.py`: IDs and ARNs for the existing VPC, subnets, shared ALB, listener, security group, and production host.
- `tests/test_stack.py`: five deployment-critical tests covering task layout, ALB routing, security-group ingress, resource ordering, deployment settings, stable host identities, and deletion-safe ASG configuration.
- `.github/workflows/deploy-cdk-aws.yml`: builds immutable container images, pushes them to ECR, runs tests, and deploys the CDK stack.

## Previous approaches and deployment failures

### Bare EC2 bootstrap

The original deployment used CloudFormation Init, shell scripts, and Docker Compose on a raw EC2 instance. Application changes forced instance replacement so bootstrap scripts would run again. Large image pulls and `cfn-signal` timeouts made deployments slow and fragile.

ECS now handles application releases by replacing tasks. EC2 replacement is reserved for actual host changes or failures.

### Versioned host resources

The workflow previously passed a run number into versioned Launch Template and Auto Scaling Group construct IDs. Every application deployment changed CloudFormation logical IDs and replaced the host infrastructure. Fixed construct IDs now keep the host stable across application releases.

### Container and routing failures

- A complete Nginx configuration was copied into `/etc/nginx/conf.d/default.conf`, causing Nginx to exit because top-level directives were invalid there. It now replaces `/etc/nginx/nginx.conf`.
- The ALB originally targeted Flask on port 5000 instead of Nginx on port 80.
- The task security group originally had no ingress from the shared ALB.
- The Nginx Java proxy stripped the Spring class-level route prefix.
- PyTorch attempted to download model weights at runtime despite the task having no internet route. The weights are now cached in the image build.
- Spring upload limits existed only in an ignored local `application.properties`, so deployed containers used Spring's default multipart limit and returned 413. A tracked `application.yml` now packages the 100 MB limits in the Java image.

### Stack deletion hang

ECS capacity-provider defaults enabled managed scaling, managed termination protection, and instance scale-in protection. During deletion, CloudFormation successfully set the Auto Scaling Group to `min=0`, `max=0`, and `desired=0`, but the protected instance remained and blocked deletion.

Managed scaling and managed termination protection are now disabled. Synthesis verifies that new instances are not protected from scale-in.

### Service created before EC2 capacity

The deployment circuit breaker once failed the service while the instance profile was still being created. The ECS service depended on the listener rule but not on the Auto Scaling Group, so CloudFormation could create the service before any container instance existed.

The service now explicitly depends on the Auto Scaling Group. The circuit breaker evaluates task health only after CloudFormation has created host capacity.
