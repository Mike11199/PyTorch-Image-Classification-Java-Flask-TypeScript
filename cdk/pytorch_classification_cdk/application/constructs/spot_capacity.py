"""Set up one Spot EC2 host and connect its capacity to the ECS cluster."""

from aws_cdk import (
    Tags,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
)
from constructs import Construct


class SpotCapacity(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        cluster: ecs.Cluster,
    ) -> None:
        super().__init__(scope, construct_id)
        # Preserve deployed resource paths while separating their implementation.

        instance_role = iam.Role(
            scope,
            "PytorchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
            ],
        )

        launch_template = ec2.LaunchTemplate(
            scope,
            "EcsLaunchTemplate",
            instance_type=ec2.InstanceType("t3.medium"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2023(),
            role=instance_role,
            user_data=ec2.UserData.for_linux(),
        )

        pytorch_asg = autoscaling.AutoScalingGroup(
            scope,
            "PytorchCapacity",
            vpc=vpc,
            min_capacity=1,
            max_capacity=1,
            desired_capacity=1,
            mixed_instances_policy=autoscaling.MixedInstancesPolicy(
                instances_distribution=autoscaling.InstancesDistribution(
                    spot_allocation_strategy=autoscaling.SpotAllocationStrategy.CAPACITY_OPTIMIZED,
                    on_demand_base_capacity=0,
                    on_demand_percentage_above_base_capacity=0,
                ),
                launch_template=launch_template,
            ),
        )

        capacity_provider = ecs.AsgCapacityProvider(
            scope,
            "PytorchAsgCapacityProvider",
            auto_scaling_group=pytorch_asg,
            enable_managed_scaling=False,
            enable_managed_termination_protection=False,
        )

        cluster.add_asg_capacity_provider(capacity_provider)

        Tags.of(pytorch_asg).add("DeployedBy", "GitHub-Actions-CDK")

        Tags.of(pytorch_asg).add("Project", "pytorch-image-classification")
        self.auto_scaling_group = pytorch_asg
