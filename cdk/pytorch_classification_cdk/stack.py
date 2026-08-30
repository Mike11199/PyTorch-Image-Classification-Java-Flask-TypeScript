"""PyTorch image-classification production infrastructure."""

from aws_cdk import CfnParameter, Duration, Stack, Tags
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from constructs import Construct

from . import existing_resources as existing
from .bootstrap import build_bootstrap_init, build_deployment_user_data


class PytorchClassificationStack(Stack):
    """Run one self-healing EC2 host behind the existing shared ALB."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image_tag_flask = CfnParameter(
            self,
            "ImageTagFlask",
            type="String",
            description="Flask/PyTorch image tag.",
            allowed_pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$",
        )
        image_tag_java = CfnParameter(
            self,
            "ImageTagJava",
            type="String",
            description="Java Spring Boot image tag.",
            allowed_pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$",
        )
        image_tag_react = CfnParameter(
            self,
            "ImageTagReact",
            type="String",
            description="React frontend image tag.",
            allowed_pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$",
        )
        image_tag_nginx = CfnParameter(
            self,
            "ImageTagNginx",
            type="String",
            description="Nginx reverse proxy image tag.",
            allowed_pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$",
        )

        vpc = ec2.Vpc.from_vpc_attributes(
            self,
            "ExistingVpc",
            vpc_id=existing.VPC_ID,
            availability_zones=list(existing.AVAILABILITY_ZONES),
            public_subnet_ids=list(existing.PUBLIC_SUBNET_IDS),
        )
        alb_security_group = ec2.SecurityGroup.from_security_group_id(
            self,
            "ExistingAlbSecurityGroup",
            existing.SHARED_ALB_SECURITY_GROUP_ID,
            mutable=False,
        )

        instance_security_group = ec2.SecurityGroup(
            self,
            "PytorchInstanceSecurityGroup",
            vpc=vpc,
            description="HTTP from the shared ALB to PyTorch classification nginx",
            allow_all_outbound=True,
        )
        instance_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=ec2.Port.tcp(80),
            description="HTTP from shared ALB",
        )

        instance_role = iam.Role(
            self,
            "PytorchInstanceRole",
            role_name="pytorch-classification-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
            ],
        )
        instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )
        instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=[
                    f"arn:aws:ecr:{self.region}:{existing.AWS_ACCOUNT_ID}:repository/pytorch-web"
                ],
            )
        )

        registry = (
            f"{existing.AWS_ACCOUNT_ID}.dkr.ecr.{self.region}.amazonaws.com/pytorch-web"
        )
        bootstrap_init = build_bootstrap_init(
            registry=registry,
            flask_tag=image_tag_flask.value_as_string,
            java_tag=image_tag_java.value_as_string,
            react_tag=image_tag_react.value_as_string,
            nginx_tag=image_tag_nginx.value_as_string,
        )
        deployment_user_data = build_deployment_user_data(
            flask_tag=image_tag_flask.value_as_string,
            java_tag=image_tag_java.value_as_string,
            react_tag=image_tag_react.value_as_string,
            nginx_tag=image_tag_nginx.value_as_string,
        )

        # Force ASG to recreate instances whenever startup scripts/configs change.
        deploy_version = self.node.try_get_context("deploy-version") or "1"

        launch_template = ec2.LaunchTemplate(
            self,
            "PytorchLaunchTemplate",
            launch_template_name=f"pytorch-classification-ec2-lt-v{deploy_version}",
            instance_type=ec2.InstanceType("t3.medium"),
            machine_image=ec2.MachineImage.from_ssm_parameter(
                "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"
            ),
            security_group=instance_security_group,
            role=instance_role,
            user_data=deployment_user_data,
            associate_public_ip_address=True,
            require_imdsv2=True,
        )

        pytorch_asg = autoscaling.AutoScalingGroup(
            self,
            "PytorchAutoScalingGroup",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=vpc.public_subnets),
            min_capacity=1,
            max_capacity=1,
            desired_capacity=1,
            launch_template=launch_template,
            health_checks=autoscaling.HealthChecks.ec2(),
            signals=autoscaling.Signals.wait_for_all(
                timeout=Duration.minutes(30),
            ),
            init=bootstrap_init,
            init_options=autoscaling.ApplyCloudFormationInitOptions(
                print_log=True,
                ignore_failures=False,
            ),
        )
        Tags.of(pytorch_asg).add("DeployedBy", "GitHub-Actions-CDK")
        Tags.of(pytorch_asg).add("Project", "pytorch-image-classification")

        target_group = elbv2.ApplicationTargetGroup(
            self,
            "PytorchTargetGroup",
            target_group_name="pytorch-classification-cdk",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.INSTANCE,
            health_check=elbv2.HealthCheck(
                path="/health",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=5,
                unhealthy_threshold_count=2,
            ),
        )
        target_group.set_attribute("deregistration_delay.timeout_seconds", "60")
        pytorch_asg.attach_to_application_target_group(target_group)

        elbv2.CfnListenerRule(
            self,
            "PytorchListenerRule",
            listener_arn=existing.SHARED_HTTPS_LISTENER_ARN,
            priority=99,
            conditions=[
                {
                    "field": "host-header",
                    "hostHeaderConfig": {"values": [existing.PRODUCTION_HOST]},
                }
            ],
            actions=[
                {
                    "type": "forward",
                    "targetGroupArn": target_group.target_group_arn,
                }
            ],
        )
