"""Create the Route 53 alias, load balancer listener rule, and target group."""

from aws_cdk import (
    Duration,
    Fn,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as route53,
)
from constructs import Construct

from ... import existing_resources


class WebRouting(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        service: ecs.Ec2Service,
    ) -> None:
        super().__init__(scope, construct_id)
        # Preserve deployed resource paths while separating their implementation.

        alias_record = route53.CfnRecordSet(
            scope,
            "MachineLearningAliasRecordResource",
            hosted_zone_id=Fn.import_value("SharedMachineLearningHostedZoneId"),
            name=f"{existing_resources.PRODUCTION_HOST}.",
            type="A",
            alias_target=route53.CfnRecordSet.AliasTargetProperty(
                dns_name=Fn.join(
                    "",
                    [
                        "dualstack.",
                        Fn.import_value("SharedLoadBalancerDnsName"),
                        ".",
                    ],
                ),
                hosted_zone_id=Fn.import_value(
                    "SharedLoadBalancerCanonicalHostedZoneId"
                ),
                evaluate_target_health=True,
            ),
        )

        alias_record.override_logical_id("MachineLearningAliasRecord")

        alias_record.apply_removal_policy(RemovalPolicy.RETAIN)

        target_group = elbv2.ApplicationTargetGroup(
            scope,
            "PytorchTargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
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

        target_group.node.default_child.apply_removal_policy(RemovalPolicy.RETAIN)

        listener_rule = elbv2.CfnListenerRule(
            scope,
            "PytorchListenerRule",
            listener_arn=Fn.import_value("SharedHttpsListenerArn"),
            priority=existing_resources.LISTENER_RULE_PRIORITY,
            conditions=[
                {
                    "field": "host-header",
                    "hostHeaderConfig": {"values": [existing_resources.PRODUCTION_HOST]},
                }
            ],
            actions=[
                {
                    "type": "forward",
                    "targetGroupArn": target_group.target_group_arn,
                }
            ],
        )

        listener_rule.apply_removal_policy(RemovalPolicy.RETAIN)
        self.listener_rule = listener_rule
