"""PyTorch image-classification production infrastructure on ECS with EC2 launch type.

Uses Spot pricing (~50% savings vs on-demand t3.medium) for cost efficiency.

Architecture:
- Single Spot t3.medium EC2 instance (min/max/desired=1) running the ECS agent
- Containers run directly on that EC2 instance via Docker (EC2 launch type, not Fargate)
- Task definition defines all 3 containers, memory/CPU limits per container, port mappings
- ECS Service ensures exactly 1 task is always running; restarts failed containers automatically
- Target group attached to consolidated-load-balancer via ALB listener rule for production host header

Cost: ~$11-18/mo Spot t3.medium (vs $30/mo on-demand). No extra charge for ECS control plane.
Spot interruption is handled gracefully - AWS gives 2 min notice, ECS drains tasks, ASG launches replacement.
"""

from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    Tags,
    CfnParameter,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
)

from . import existing_resources


class PytorchClassificationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CloudFormation parameters (passed via --parameters in CI).
        self.param_image_tag_flask = CfnParameter(
            self, "ImageTagFlask", default="flask-api-latest"
        )
        self.param_image_tag_java = CfnParameter(
            self, "ImageTagJava", default="java-api-latest"
        )
        self.param_image_tag_react = CfnParameter(
            self, "ImageTagReact", default="react-front-end-latest"
        )

        # Import existing VPC (from existing_resources.py).
        vpc = ec2.Vpc.from_vpc_attributes(
            self,
            "SharedVPC",
            vpc_id=existing_resources.VPC_ID,
            availability_zones=list(existing_resources.AVAILABILITY_ZONES),
            public_subnet_ids=list(existing_resources.PUBLIC_SUBNET_IDS),
        )

        # ECS cluster (EC2 launch type - no extra charge beyond instance cost).
        cluster = ecs.Cluster(
            self,
            "PytorchCluster",
            vpc=vpc,
            container_insights_v2=ecs.ContainerInsights.DISABLED,
        )

        # Task execution role: ECS agent uses this to pull images from ECR and write logs.
        task_execution_role = iam.Role(
            self,
            "PytorchTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
        )

        # Task definition: defines the containers that ECS will run.
        task_definition = ecs.Ec2TaskDefinition(
            self,
            "PytorchTaskDefinition",
            execution_role=task_execution_role,
            network_mode=ecs.NetworkMode.AWS_VPC,  # Tasks get ENI for IP targets with ALB
        )

        ecr_repo_name = "pytorch-web"

        # Image tags passed via CDK deploy parameters (--parameters ImageTagFlask="...").
        image_tag_flask = self.param_image_tag_flask.value_as_string
        image_tag_java = self.param_image_tag_java.value_as_string
        image_tag_react = self.param_image_tag_react.value_as_string

        account_id = Stack.of(self).account
        region = Stack.of(self).region

        flask_image = ecs.ContainerImage.from_registry(
            f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repo_name}:{image_tag_flask}"
        )
        java_image = ecs.ContainerImage.from_registry(
            f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repo_name}:{image_tag_java}"
        )
        react_image = ecs.ContainerImage.from_registry(
            f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repo_name}:{image_tag_react}"
        )

        # Container 1: Flask/PyTorch backend.
        task_definition.add_container(
            "FlaskContainer",
            image=flask_image,
            cpu=512,
            memory_limit_mib=1600,
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=5000)],  # AWS_VPC auto-matches host_port; no translation allowed
            logging=ecs.LogDrivers.aws_logs(stream_prefix="flask"),
        )

        # Container 2: Java Spring Boot backend.
        task_definition.add_container(
            "JavaContainer",
            image=java_image,
            cpu=256,
            memory_limit_mib=700,
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=8080)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="java"),
        )

        # Container 3: Nginx (serves React static files + proxies API requests to Flask/Java via localhost).
        task_definition.add_container(
            "NginxContainer",
            image=react_image,  # Same as ski shop: nginx with React baked in; no separate containers needed
            cpu=128,
            memory_limit_mib=200,
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=80)],  # ALB targets this port
            logging=ecs.LogDrivers.aws_logs(stream_prefix="nginx"),
        )

        # ECS Service: ensures exactly 1 task is always running. Handles restarts on failure.
        service = ecs.Ec2Service(
            self,
            "PytorchService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            min_healthy_percent=0,
            max_healthy_percent=100,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
        )

        # The task ENI accepts HTTP only from the shared ALB security group.
        shared_alb_security_group = ec2.SecurityGroup.from_security_group_id(
            self,
            "SharedAlbSecurityGroup",
            existing_resources.SHARED_ALB_SECURITY_GROUP_ID,
            mutable=False,
        )
        service.connections.allow_from(
            shared_alb_security_group,
            ec2.Port.tcp(80),
            "Allow shared ALB to reach Nginx",
        )

        # Target group attached to imported shared ALB; uses IP targets for ECS tasks.
        target_group = elbv2.ApplicationTargetGroup(
            self,
            "PytorchTargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,  # ECS tasks get ENIs with IPs
            targets=[
                service.load_balancer_target(
                    container_name="NginxContainer",
                    container_port=80,
                )
            ],
            health_check=elbv2.HealthCheck(
                path="/health",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
            ),
        )

        # Listener rule on shared ALB: production host header -> our target group.
        listener_rule = elbv2.CfnListenerRule(
            self,
            "PytorchListenerRule",
            listener_arn=existing_resources.SHARED_HTTPS_LISTENER_ARN,  # from existing_resources.py
            priority=10,
            conditions=[
                {
                    "field": "host-header",
                    "hostHeaderConfig": {"values": [existing_resources.PRODUCTION_HOST]},  # from existing_resources.py
                }
            ],
            actions=[
                {
                    "type": "forward",
                    "targetGroupArn": target_group.target_group_arn,
                }
            ],
        )

        # ECS rejects service creation when its target group has not yet been
        # associated with a load balancer.
        cfn_service = service.node.default_child
        cfn_service.add_resource_dependency(listener_rule)

        # Instance role for ECS-optimized EC2 instances.
        instance_role = iam.Role(
            self,
            "PytorchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
            ],
        )

        # LaunchTemplate with Spot pricing (account disabled LaunchConfiguration).
        launch_template = ec2.LaunchTemplate(
            self,
            "EcsLaunchTemplate",
            instance_type=ec2.InstanceType("t3.medium"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2023(),  # Pre-installed ECS agent (AL2023)
            role=instance_role,  # Instance profile with ECS + SSM permissions
            user_data=ec2.UserData.for_linux(),  # Required: CDK patches ECS cluster registration here via AsgCapacityProvider
        )

        pytorch_asg = autoscaling.AutoScalingGroup(
            self,
            "PytorchCapacity",
            vpc=vpc,
            min_capacity=1,
            max_capacity=1,
            desired_capacity=1,  # Required: None blocks CDK delete (tries to preserve capacity instead of scaling to 0)
            mixed_instances_policy=autoscaling.MixedInstancesPolicy(
                instances_distribution=autoscaling.InstancesDistribution(
                    spot_allocation_strategy=autoscaling.SpotAllocationStrategy.CAPACITY_OPTIMIZED,
                    on_demand_base_capacity=0,
                    on_demand_percentage_above_base_capacity=0,  # All Spot; no max_price cap (On-Demand price is the ceiling)
                ),
                launch_template=launch_template,
            ),
        )

        # Manually register ASG with cluster - injects ECS bootstrap config into user data.
        from aws_cdk.aws_ecs import AsgCapacityProvider
        capacity_provider = AsgCapacityProvider(
            self,
            "PytorchAsgCapacityProvider",
            auto_scaling_group=pytorch_asg,
            enable_managed_scaling=False,
            enable_managed_termination_protection=False,
            # Registration still patches the ASG user data with the ECS cluster name.
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        # Do not let the deployment circuit breaker evaluate the service before
        # CloudFormation has created the fixed EC2 capacity for the cluster.
        cfn_asg = pytorch_asg.node.default_child
        cfn_service.add_resource_dependency(cfn_asg)

        Tags.of(pytorch_asg).add("DeployedBy", "GitHub-Actions-CDK")
        Tags.of(pytorch_asg).add("Project", "pytorch-image-classification")
