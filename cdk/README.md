# PyTorch Image Classification -- Production Deployment (CDK + ECS)

Single Spot t3.medium EC2 instance running the ECS agent, hosting all 3 containers via one ECS task. Uses Spot pricing (~$15 USD/month). Shares `consolidated-load-balancer` across multiple projects.

## Architecture

- AutoScalingGroup: min=1, max=1 Spot t3.medium running ECS-optimized AMI (the actual server your containers run on). The ASG replaces interrupted/failed hosts but is not replaced for application releases.
- ECS cluster: management layer that tracks what to deploy onto that EC2 instance; no extra cost beyond the instance itself
- Task definition: declares 3 containers with CPU/memory limits and port mappings (AWS_VPC mode):
    - Nginx reverse proxy (128 CPU, 200 MB memory) — serves React static files directly + proxies API requests to sibling containers via localhost (`/api-java-spring-boot/*` → Java:8080, `/api-flask-pytorch-models/*` → Flask:5000). Same pattern as ski shop: nginx config baked into the frontend Dockerfile.
    - Flask/PyTorch backend (512 CPU, 1600 MB memory) — runs image classification models; pretrained weights are cached in the image during the Docker build
    - Java Spring Boot backend (256 CPU, 700 MB memory) — orchestrates model calls from React; also calls Flask via localhost:5000 internally
- ECS Service: ensures exactly 1 task is always running; restarts failed tasks automatically
- TargetGroup + ALB listener rule priority=10: routes production host header to our target group via shared load balancer

## EC2 vs Fargate (why you see two things in the console)

This is **ECS on EC2**, not Fargate. Both use an "ECS cluster" as management layer, but:

- **ECS on EC2:** You own a Spot t3.medium instance (~$15/mo). It appears in both consoles:
  - ECS Console → Cluster exists with 1 container instance registered (your server)
  - EC2 Console → The actual running Spot instance you can SSH into via SSM
  
- **Fargate:** AWS manages all infrastructure. Cluster exists but shows 0 container instances — no servers to see or manage anywhere.

Checking "Container instances" is how you tell which launch type a cluster uses. This project has both an ECS cluster AND one EC2 instance because that's the expected setup for ECS on EC2, not two separate deployments.

## Spot pricing

Uses AWS Spot instances (up to 90% cheaper than on-demand). Spot means unused EC2 capacity offered at discount. When demand is high, AWS can reclaim our instance with 2 min notice — ECS drains tasks from the dying instance and ASG launches a replacement automatically. For t3.medium in us-west-1 this happens rarely (~few times per month).

## File responsibilities

- `stack.py`: single ECS stack using an explicit LaunchTemplate + fixed one-instance AutoScalingGroup (the account disabled legacy LaunchConfigurations). Application releases create new ECS task-definition revisions without replacing the host. The ECS capacity provider registers the ASG with the cluster, but managed scaling and managed termination protection are disabled because fixed capacity is intentional and scale-in protection previously blocked clean stack deletion.
- `tests/test_stack.py`: validates the three-container task, Nginx target binding, ALB security-group ingress, listener dependency, stop-first deployment settings, stable host logical IDs, and fixed ASG capacity. Runs in CI before every deploy.
- `existing_resources.py`: hardcoded constants for shared infrastructure (VPC ID, subnets, ALB ARN/security groups, production host header). Centralized to avoid drift between stacks referencing same load balancer.

## Previous approach (deprecated)

Before this rewrite: raw EC2 with CloudFormation Init (cfn-init) + cfn-signal + docker-compose on-host.
- bootstrap.py (~140 lines) generated a massive base64-encoded UserData blob containing ~186 lines of shell commands
- Instance booted, ran shell scripts to install Docker from scratch, authenticate to ECR, pull all 4 images (3GB), run docker-compose up, then signal CloudFormation success
- If cfn-signal did not arrive within timeout (started at 5 min, had to bump to 30 min as images grew), CloudFormation destroyed your working stack thinking deploy failed -- even though instance was probably fine, just slow on cold boot
- No container lifecycle management beyond docker-compose own restart policy; no integration with AWS health checks; ghost EC2 problem from inconsistent fingerprinting required manual SSH debugging

New ECS pattern uses the same t3.medium but:
- Zero bootstrap scripts (ECS agent pre-installed in AMI, auto-registers on boot)
- ECS service declaratively maintains desired_count=1 and replaces failed tasks automatically without cfn-signal gymnastics
- Application updates replace the ECS task without replacing the EC2 host. Because one t3.medium cannot fit two complete tasks, ECS deliberately stops the old task before starting the new one (`minimumHealthyPercent=0`, `maximumPercent=100`); brief deployment downtime is expected.
