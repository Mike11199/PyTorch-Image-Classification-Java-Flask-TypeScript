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
        shared_alb_security_group: ec2.ISecurityGroup,
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

        security_group = ec2.SecurityGroup(scope, "PytorchHostSecurityGroup", vpc=vpc)
        security_group.add_ingress_rule(
            shared_alb_security_group, ec2.Port.tcp(80), "Allow shared ALB to reach Nginx"
        )

        launch_template = ec2.LaunchTemplate(
            scope,
            "EcsLaunchTemplate",
            instance_type=ec2.InstanceType("t3.medium"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2023(),
            role=instance_role,
            user_data=ec2.UserData.for_linux(),
            security_group=security_group,
            associate_public_ip_address=True,
        )

        pytorch_asg = autoscaling.AutoScalingGroup(
            scope,
            "PytorchCapacity",
            vpc=vpc,
            min_capacity=1,
            max_capacity=1,
            desired_capacity=1,
            # Replace the host so changes to ECS agent configuration take effect.
            update_policy=autoscaling.UpdatePolicy.replacing_update(),
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

        # Cached images can fill the disk and cause deployment image pulls to fail.
        # Shorten ECS cleanup delays to reclaim stopped containers and unused images.
        launch_template.user_data.add_commands(
            "echo ECS_ENABLE_TASK_IAM_ROLE_NETWORK_HOST=true >> /etc/ecs/ecs.config",
            "echo ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=1m >> /etc/ecs/ecs.config",
            "echo ECS_IMAGE_MINIMUM_CLEANUP_AGE=1m >> /etc/ecs/ecs.config",
            "echo ECS_IMAGE_CLEANUP_INTERVAL=10m >> /etc/ecs/ecs.config",
            "echo ECS_NUM_IMAGES_DELETE_PER_CYCLE=100 >> /etc/ecs/ecs.config",
        )

        Tags.of(pytorch_asg).add("DeployedBy", "GitHub-Actions-CDK")

        Tags.of(pytorch_asg).add("Project", "pytorch-image-classification")
        self.auto_scaling_group = pytorch_asg
