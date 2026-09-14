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

from .tor_proxy import CONTROL_PATH, TorProxy


class ApplicationService(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        image_tag_flask: str,
        image_tag_java: str,
        image_tag_react: str,
        video_storage=None,
        media_bucket=None,
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
            # Use the public EC2 host for outbound downloads and localhost proxies.
            network_mode=ecs.NetworkMode.HOST,
        )
        if video_storage:
            video_storage.bucket.grant_read_write(task_definition.task_role)
            video_storage.table.grant_read_write_data(task_definition.task_role)
            media_bucket.grant_read(task_definition.task_role, "videos/ml-video.mp4")

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

        youtube_tokens = task_definition.add_container(
            "YouTubeTokenContainer",
            image=ecs.ContainerImage.from_registry(
                "brainicism/bgutil-ytdlp-pot-provider:2.0.0"
            ),
            # Host networking shares localhost; do not expose the token server publicly.
            command=["--host", "127.0.0.1"],
            cpu=128,
            memory_limit_mib=512,
            essential=False,
            enable_restart_policy=True,
            linux_parameters=ecs.LinuxParameters(
                scope, "YouTubeTokenLinuxParameters", init_process_enabled=True
            ),
            health_check=ecs.HealthCheck(
                command=[
                    "CMD", "node", "-e",
                    "fetch('http://127.0.0.1:4416/ping').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))",
                ],
                start_period=Duration.seconds(10),
            ),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="youtube-tokens"),
        )

        self.tor_proxy = TorProxy(self, "TorProxy", cluster=cluster)
        task_definition.add_volume(name="tor-control", host=ecs.Host(source_path=CONTROL_PATH))

        flask = task_definition.add_container(
            "FlaskContainer",
            image=flask_image,
            cpu=512,
            memory_limit_mib=1600,
            essential=True,
            environment={
                "VIDEO_BUCKET": video_storage.bucket.bucket_name,
                "VIDEO_TABLE": video_storage.table.table_name,
                "VIDEO_MEDIA_BUCKET": media_bucket.bucket_name,
                "AWS_DEFAULT_REGION": "us-west-1",
                "TORCH_NUM_THREADS": "1",
                "VIDEO_YOUTUBE_ENABLED": "true",
                "VIDEO_YOUTUBE_TOR": "true",
            } if video_storage else {},
            port_mappings=[ecs.PortMapping(container_port=5000)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="flask"),
        )
        flask.add_mount_points(ecs.MountPoint(
            source_volume="tor-control", container_path="/tor-control", read_only=True,
        ))
        flask.add_container_dependencies(
            ecs.ContainerDependency(
                container=youtube_tokens,
                condition=ecs.ContainerDependencyCondition.HEALTHY,
            )
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

        self.cluster = cluster
        self.service = service
