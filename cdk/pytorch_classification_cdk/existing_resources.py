"""Existing AWS resources used by the PyTorch classification stack.

These are live AWS resources shared across services — imported read-only,
never created or modified by this stack.

No value in this file is a credential or secret; SSM parameters are referenced
by ARN only so tasks can resolve them at runtime.
"""

AWS_ACCOUNT_ID = "456461478565"
AWS_REGION = "us-west-1"

# Shared VPC (from existing EC2 instance i-015e44dd047269bd2)
VPC_ID = "vpc-031a34e2307900372"
VPC_CIDR = "172.31.0.0/16"  # Default us-west-1 VPC CIDR (instance private IP is 172.31.x.x)

# Shared ALB resources used without taking ownership of the ALB itself.
SHARED_ALB_ARN = "arn:aws:elasticloadbalancing:us-west-1:456461478565:loadbalancer/app/consolidated-load-balancer/cebd4e468e9c8526"
SHARED_ALB_SECURITY_GROUP_ID = "sg-0190e299544ca1711"
SHARED_HTTPS_LISTENER_ARN = "arn:aws:elasticloadbalancing:us-west-1:456461478565:listener/app/consolidated-load-balancer/cebd4e468e9c8526/119a0202f44da309"
PRODUCTION_HOST = "classify.alpine-peak-climbing-ski-gear.com"

AVAILABILITY_ZONES = ("us-west-1b",)
PUBLIC_SUBNET_IDS = (
    "subnet-0069d564c7d9784e5",  # us-west-1b only for now
)
