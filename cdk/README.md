# PyTorch Classification CDK

## Application

This stack deploys the application to one `t3.medium` EC2 instance. Docker Compose runs four containers on the instance:

- Flask/PyTorch backend
- Java Spring Boot backend
- React frontend
- Nginx reverse proxy

Each instance starts as a clean Amazon Linux 2023 machine. During deployment, CloudFormation puts the Compose file, environment file, and startup script under `/opt/pytorch`. The script installs Docker and Docker Compose, pulls the four images from ECR, and starts the application.

## CI/CD

Production deployments run only through `.github/workflows/deploy-cdk-aws.yml`. The workflow tests the CDK stack, builds and pushes commit-tagged images, and runs `cdk deploy` with those tags. The tests cover the one-instance limit, CloudFormation signaling, instance replacement, and the rule that CI never terminates an ASG instance. Bootstrap retries are finite, and application failures roll back the deployment instead of repeatedly replacing EC2.

## Deployment flow

```text
GitHub Actions
  -> builds four Docker images
  -> pushes commit-tagged images to ECR
  -> runs cdk deploy with those image tags

CDK / CloudFormation
  -> creates a launch-template version
  -> launches one EC2 instance in an Auto Scaling Group
  -> stores the Compose, environment, and startup-file contents in the stack
  -> the EC2 instance writes those files under /opt/pytorch when it boots
  -> the EC2 instance runs the startup script
  -> CloudFormation waits for the script's success or failure result

EC2 bootstrap
  -> installs Docker and the ECR credential helper
  -> installs Docker Compose if it is missing
  -> pulls the four requested images from ECR
  -> runs docker compose up
  -> checks the running containers and image tags
  -> checks Nginx at http://127.0.0.1/health
```

## How the repository files get onto EC2

CDK reads `assets/docker-compose.yml`, `assets/runtime.env.template`, and `assets/startup_ec2.sh` while it builds the CloudFormation template. Their contents are stored in the stack as instructions for the new EC2 instance. No S3 download or manually prepared server is involved.

Amazon Linux includes an AWS program named `cfn-init`. When the instance boots, CDK-generated user data starts that program. `cfn-init` reads the file contents from the CloudFormation stack, creates these files on the instance, sets their ownership and permissions, and runs the startup script:

```text
/opt/pytorch/docker-compose.yml
/opt/pytorch/runtime.env
/opt/pytorch/startup_ec2.sh
```

After the script finishes, another AWS program named `cfn-signal` sends its exit code back to CloudFormation. Exit code `0` means the instance was configured successfully. Any other exit code fails the deployment and starts rollback.

## EC2 bootstrap

`assets/startup_ec2.sh` contains the setup commands for every new instance. `cfn-init` writes it to `/opt/pytorch/startup_ec2.sh` and runs it as root.

The script:

1. Loads the ECR registry and image tags from `/opt/pytorch/runtime.env`.
2. Installs Docker and `amazon-ecr-credential-helper` with `dnf`.
3. Downloads the pinned Docker Compose plugin if the AMI does not already have it.
4. Configures Docker to authenticate to ECR with the EC2 IAM role.
5. Runs `docker compose pull` and `docker compose up -d --remove-orphans`.
6. Checks that all four containers are running the exact images requested by the deployment.
7. Checks local Nginx health up to 30 times.
8. Exits with `0` on success or `1` on failure.

CloudFormation waits up to 15 minutes for the `cfn-signal` result.

## Why Auto Scaling Group + LaunchTemplate instead of bare EC2 Instance?

CDK uses CloudFormation Init (defined in `bootstrap.py`) to copy files onto each new instance. On boot, CFN Init:

1. Copies the actual script and config files (`startup_ec2.sh`, `docker-compose.yml`, etc.) into `/opt/pytorch/` on disk.
2. Generates a fingerprint hash from those file contents and puts it in the LaunchTemplate metadata so CloudFormation can detect changes between deploys.

With ASG + LaunchTemplate: each deploy creates a new LaunchTemplate version tagged by `deploy-version`. The ASG sees that as different, terminates the old instance, and launches one with the new config automatically.

With bare EC2 Instance (no ASG), CF often treats small changes — new image tags, updated bootstrap scripts — as metadata updates instead of reasons to replace the physical host. You end up with a "deployed" stack version running stale config on an old instance, requiring manual stack deletion to force replacement.

Same single t3.medium (~$30/mo) either way; ASG + LaunchTemplate just makes CloudFormation actually replace instances when you push changes instead of keeping the stale one alive.

## Instance replacement and rollback

The Auto Scaling Group has `min=1`, `desired=1`, and `max=1`. It maintains one EC2 host and cannot scale out.
- Changes to the Compose or bootstrap files change CDK's Init fingerprint and also launch a new instance.
- The ASG uses EC2 health checks, not ALB health checks. A broken container or failed HTTP check does not cause repeated EC2 replacement.
- Docker uses `restart: unless-stopped`, so Docker can restart a crashed container without replacing the host.
- A failed bootstrap sends a failed signal and CloudFormation rolls the update back to the previous stack configuration.
- A corrected deployment creates another instance and runs the corrected bootstrap files.
- A failed first stack creation can end in `ROLLBACK_COMPLETE` and may require stack deletion. Failed updates roll back without that requirement.

## Files involved in bootstrap

- `pytorch_classification_cdk/stack.py` creates the IAM role, security group, launch template, one-instance ASG, target group, and listener rule.
- `pytorch_classification_cdk/bootstrap.py` tells CloudFormation Init which files to copy and which command to run.
- `assets/startup_ec2.sh` installs Docker tooling and starts the application.
- `assets/docker-compose.yml` defines the four containers.
- `assets/runtime.env.template` supplies the ECR registry and image tags used by Compose.
- `assets/nginx/` builds the public reverse proxy and its `/health` endpoint.
- `.github/workflows/deploy-cdk-aws.yml` builds the images, pushes them to ECR, deploys CDK, and waits for ALB target health.

## Failure logs

- CloudFormation stack events show whether the ASG received a success or failure signal.
- EC2 console output shows failures that happen during early boot or package installation.
- `/var/log/cfn-init.log` contains CloudFormation Init output.
- `/var/log/pytorch-bootstrap.log` contains Docker, ECR, Compose, image, and health-check output.

## Manual operations (what used to be in app READMEs)

Before CDK + Docker, each app had its own EC2 manual-deployment notes: running Flask via gunicorn directly on the instance, building Maven jars on EC2 (`nohup java -jar ...`), installing nginx and editing `/etc/nginx/nginx.conf` manually. Those are now dead code — Docker Compose runs all four containers from ECR images, nginx is baked into its own container at `cdk/assets/nginx/`, and CDK manages infrastructure creation/deletion.

If you need to SSH in for debugging a running instance (not required for normal deploys):

- Connect via AWS Systems Manager:
  ```bash
  aws ssm start-session --target <INSTANCE_ID> --profile michael-projects
  ```
- Check containers on the host:
  - `docker ps -a` lists all containers and their status.
  - `docker compose -f /opt/pytorch/docker-compose.yml logs --tail=100` shows container logs.
  - `cat /var/log/pytorch-bootstrap.log` shows bootstrap script output from last launch.

The old per-app manual commands are kept in each app's README under "Legacy EC2 / Nginx Notes (DEAD CODE)" with a link back here for historical reference only.
