"""Import the shared VPC, public subnets, and load balancer security group."""

from aws_cdk import Fn, aws_ec2 as ec2
from constructs import Construct


class SharedNetwork(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)
        # Preserve deployed resource paths while separating their implementation.

        vpc = ec2.Vpc.from_vpc_attributes(
            scope,
            "SharedVPC",
            vpc_id=Fn.import_value("SharedVpcId"),
            availability_zones=[
                Fn.import_value("SharedPublicSubnet1AvailabilityZone")
            ],
            public_subnet_ids=[Fn.import_value("SharedPublicSubnet1Id")],
        )

        shared_alb_security_group = ec2.SecurityGroup.from_security_group_id(
            scope,
            "SharedAlbSecurityGroup",
            Fn.import_value("SharedAlbSecurityGroupId"),
            mutable=False,
        )
        self.vpc = vpc
        self.alb_security_group = shared_alb_security_group
