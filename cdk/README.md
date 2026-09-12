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

The ASG keeps exactly one host. Releases stop the old task before starting its replacement; releases and Spot interruptions can cause brief downtime. ECS service creation waits for the listener rule and host capacity.
