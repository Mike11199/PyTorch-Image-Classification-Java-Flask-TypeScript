"""Run the Tor proxy separately from containers with application permissions."""

from pathlib import Path

from aws_cdk import Duration, RemovalPolicy, aws_ecs as ecs, aws_iam as iam, aws_logs as logs
from constructs import Construct

CONTROL_PATH = "/var/lib/pytorch-youtube-tor-control"


class TorProxy(Construct):
    def __init__(self, scope, construct_id, *, cluster):
        super().__init__(scope, construct_id)
        role = iam.Role(self, "Role", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.DENY, actions=["*"], resources=["*"],
        ))
        task = ecs.Ec2TaskDefinition(
            self, "Task", network_mode=ecs.NetworkMode.BRIDGE, task_role=role,
        )
        task.add_volume(name="tor-control", host=ecs.Host(source_path=CONTROL_PATH))
        linux = ecs.LinuxParameters(self, "Linux")
        linux.drop_capabilities(ecs.Capability.ALL)
        linux.add_capabilities(
            ecs.Capability.NET_ADMIN, ecs.Capability.CHOWN, ecs.Capability.FOWNER,
            ecs.Capability.DAC_OVERRIDE, ecs.Capability.SETUID, ecs.Capability.SETGID,
        )
        # Allow headroom for directory-cache updates without filling the tmpfs.
        for path, size in (("/var/lib/tor", 128), ("/run", 1)):
            linux.add_tmpfs(ecs.Tmpfs(
                container_path=path, size=size,
                mount_options=[ecs.TmpfsMountOption.RW, ecs.TmpfsMountOption.NOEXEC,
                               ecs.TmpfsMountOption.NOSUID, ecs.TmpfsMountOption.NODEV],
            ))
        container = task.add_container(
            "Tor",
            image=ecs.ContainerImage.from_asset(str(Path(__file__).resolve().parents[4] / "youtube-tor")),
            cpu=128, memory_limit_mib=384,
            linux_parameters=linux, readonly_root_filesystem=True,
            docker_security_options=["no-new-privileges"],
            # Host ingress remains restricted to the ALB on port 80.
            port_mappings=[ecs.PortMapping(container_port=port, host_port=port) for port in (9051, 9080)],
            health_check=ecs.HealthCheck(
                command=["CMD", "/usr/local/bin/healthcheck.sh"], start_period=Duration.seconds(60),
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="youtube-tor",
                log_group=logs.LogGroup(self, "Logs", retention=logs.RetentionDays.ONE_WEEK,
                                       removal_policy=RemovalPolicy.DESTROY),
            ),
        )
        container.add_mount_points(ecs.MountPoint(
            source_volume="tor-control", container_path="/tor-control", read_only=False,
        ))
        self.service = ecs.Ec2Service(
            self, "Service", cluster=cluster, task_definition=task,
            daemon=True, min_healthy_percent=0, max_healthy_percent=100,
        )
