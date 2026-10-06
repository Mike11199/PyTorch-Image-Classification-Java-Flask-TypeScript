# PyTorch image classification CDK

React/Nginx, Java, and Flask/PyTorch run as one ECS task on one Spot `t3.medium` EC2 host. Deployments run through GitHub Actions.

## Structure and ownership

```text
app.py                                  # connects the three stacks
pytorch_classification_cdk/
+-- existing_resources.py                # application constants
+-- application/
|   +-- stack.py                         # PytorchClassificationStack
|   \-- constructs/
|       +-- application_service.py       # ECS cluster, containers, and service
|       +-- shared_network.py            # imports shared networking
|       +-- web_routing.py               # Route 53 alias, ALB rule, and target group
|       +-- spot_capacity.py             # EC2 launch template and one-host Spot ASG
|       \-- media_storage.py             # retained private S3 bucket
+-- media/
|   \-- stack.py                         # PytorchMediaStack (us-east-1)
\-- repository/
    \-- stack.py                         # PytorchRepositoryStack: retained pytorch-web ECR
```

The application stack owns the S3 bucket in `us-west-1`. The media stack owns pay-as-you-go CloudFront, origin access control, the bucket policy, an ACM certificate, and Route 53 A/AAAA records for `assets.machine-learning-projects.com`. Its certificate requires `us-east-1`.

Shared infrastructure owns the VPC, subnets, ALB security group, hosted zone, ALB certificate, load balancer, and listeners. This application imports their CloudFormation exports.

## Deployment

Deploy shared infrastructure first; its workflow bootstraps missing CDK environments in both regions. The [site workflow](../.github/workflows/deploy-cdk-aws.yml) then deploys the repository, builds and pushes three images, and deploys the application and media stacks together. It reads the hosted-zone ID from shared exports.

A fresh account needs GitHub AWS credentials and the region configured, plus domain registration/name-server delegation. Media files must be copied into S3 separately; deploying CDK creates the resources, not their content.

## Runtime

Nginx serves React and proxies Java and Flask over task-local `localhost`. Model weights are cached during the Flask image build. The ALB checks Nginx `/health`.

Flask reserves 1,600 MiB for ECS placement and can use up to 2,560 MiB while loading
and running Qwen alongside the resident Python process. The former 1,600 MiB hard
limit caused the kernel to kill Qwen during startup. Reservations across both ECS
tasks total 3,396 MiB, leaving room for the OS and ECS agent on the existing host.

The shared ALB must allow a 320-second idle timeout (configured in
`shared-infra-aws-cdk`). CPU inference allows 240 seconds per model call; Java
limits the full assistant request to 300 seconds, and Nginx/browser allow 310.
The former 60-second ALB timeout cut off cold assistant requests before completion.

The ASG keeps exactly one host. Releases stop the old task before starting its replacement; releases and Spot interruptions can cause brief downtime. ECS service creation waits for the listener rule and host capacity.

New hosts make stopped containers and unused images eligible for cleanup after one minute, checking images every ten minutes. Existing hosts need a one-time ECS configuration update; disk sizes and ECR retention are unchanged.
