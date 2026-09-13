"""Set up the ECS cluster, application containers, and service."""

from aws_cdk import (
    Duration,
    Fn,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    RemovalPolicy,
    aws_logs as logs,
)
from constructs import Construct


class ApplicationService(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        shared_alb_security_group: ec2.ISecurityGroup,
        image_tag_flask: str,
        image_tag_java: str,
        image_tag_react: str,
    ) -> None:
        super().__init__(scope, construct_id)
        # Preserve deployed resource paths while separating their implementation.

        cluster = ecs.Cluster(
            scope,
            "PytorchCluster",
            vpc=vpc,
            container_insights_v2=ecs.ContainerInsights.DISABLED,
        )

        task_execution_role = iam.Role(
            scope,
            "PytorchTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
        )

        task_definition = ecs.Ec2TaskDefinition(
            scope,
            "PytorchTaskDefinition",
            execution_role=task_execution_role,
            network_mode=ecs.NetworkMode.AWS_VPC,
        )

        repository_uri = Fn.import_value("PytorchRepositoryUri")

        flask_image = ecs.ContainerImage.from_registry(
            Fn.join("", [repository_uri, ":", image_tag_flask])
        )

        java_image = ecs.ContainerImage.from_registry(
            Fn.join("", [repository_uri, ":", image_tag_java])
        )

        react_image = ecs.ContainerImage.from_registry(
            Fn.join("", [repository_uri, ":", image_tag_react])
        )

        task_definition.add_container(
            "FlaskContainer",
            image=flask_image,
            cpu=512,
            memory_limit_mib=1600,
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=5000)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="flask"),
        )

        task_definition.add_container(
            "JavaContainer",
            image=java_image,
            cpu=256,
            memory_limit_mib=700,
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=8080)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="java"),
        )

        task_definition.add_container(
            "NginxContainer",
            image=react_image,
            cpu=128,
            memory_limit_mib=200,
            essential=True,
            port_mappings=[ecs.PortMapping(container_port=80)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="nginx"),
        )

        for construct in task_definition.node.find_all():
            if isinstance(construct, logs.LogGroup):
                construct.apply_removal_policy(RemovalPolicy.DESTROY)

        service = ecs.Ec2Service(
            scope,
            "PytorchService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            min_healthy_percent=0,
            max_healthy_percent=100,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            bake_time=Duration.minutes(5),
        )

        service.connections.allow_from(
            shared_alb_security_group,
            ec2.Port.tcp(80),
            "Allow shared ALB to reach Nginx",
        )
        self.cluster = cluster
        self.service = service
