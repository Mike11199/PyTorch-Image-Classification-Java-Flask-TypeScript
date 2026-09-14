"""Infrastructure invariants, synthesized once for the suite."""

import pytest
from aws_cdk.assertions import Match, Template

from app import build_app


@pytest.fixture(scope="module")
def assembly():
    return build_app().synth()


@pytest.fixture(scope="module")
def application(assembly):
    return Template.from_json(
        assembly.get_stack_by_name("PytorchClassificationStack").template
    )


def test_stack_order_and_repository_retention(assembly):
    repository, application, media = [assembly.get_stack_by_name(name) for name in (
        "PytorchRepositoryStack", "PytorchClassificationStack", "PytorchMediaStack"
    )]
    assert repository.id in {d.id for d in application.dependencies}
    assert application.id in {d.id for d in media.dependencies}
    assert media.environment.region == "us-east-1"
    Template.from_json(repository.template).has_resource("AWS::ECR::Repository", {
        "Properties": {"RepositoryName": "pytorch-web", "EmptyOnDelete": False},
        "DeletionPolicy": "Retain", "UpdateReplacePolicy": "Retain",
    })


def test_single_task_updates_wait_for_routing_and_capacity(application):
    application.resource_count_is("AWS::ECS::Service", 2)
    application.has_resource_properties("AWS::ECS::Service", {
        "DesiredCount": 1,
        "DeploymentConfiguration": {
            "MinimumHealthyPercent": 0, "MaximumPercent": 100,
            "DeploymentCircuitBreaker": {"Enable": True, "Rollback": True},
        },
        "LoadBalancers": Match.array_with([Match.object_like({
            "ContainerName": "NginxContainer", "ContainerPort": 80,
        })]),
    })
    service = next(s for s in application.find_resources("AWS::ECS::Service").values()
                   if s["Properties"].get("LoadBalancers"))
    for kind in ("AWS::ElasticLoadBalancingV2::ListenerRule",
                 "AWS::AutoScaling::AutoScalingGroup"):
        assert set(application.find_resources(kind)) <= set(service["DependsOn"])


def test_container_images_ports_and_memory(application):
    task = next(t for t in application.find_resources("AWS::ECS::TaskDefinition").values()
                if t["Properties"]["NetworkMode"] == "host")
    assert task["Properties"]["NetworkMode"] == "host"
    containers = task["Properties"]["ContainerDefinitions"]
    assert len(containers) == 4
    containers = [c for c in containers if c["Name"] != "YouTubeTokenContainer"]
    for container, (name, tag, port, memory) in zip(containers, (
        ("FlaskContainer", "ImageTagFlask", 5000, 1600),
        ("JavaContainer", "ImageTagJava", 8080, 700),
        ("NginxContainer", "ImageTagReact", 80, 200),
    )):
        assert container["Name"] == name
        assert container["Memory"] == memory
        assert container["PortMappings"][0]["ContainerPort"] == port
        assert container["Image"] == {"Fn::Join": ["", [
            {"Fn::ImportValue": "PytorchRepositoryUri"}, ":", {"Ref": tag},
        ]]}


def test_shared_alb_routes_to_nginx(application):
    application.has_resource_properties("AWS::EC2::SecurityGroupIngress", {
        "FromPort": 80, "ToPort": 80,
        "SourceSecurityGroupId": {"Fn::ImportValue": "SharedAlbSecurityGroupId"},
    })
    application.has_resource("AWS::ElasticLoadBalancingV2::TargetGroup", {
        "Properties": {"Port": 80, "TargetType": "instance", "HealthCheckPath": "/health",
                       "VpcId": {"Fn::ImportValue": "SharedVpcId"}},
        "DeletionPolicy": "Retain",
    })
    application.has_resource_properties("AWS::ElasticLoadBalancingV2::ListenerRule", {
        "Priority": 3, "ListenerArn": {"Fn::ImportValue": "SharedHttpsListenerArn"},
        "Conditions": [{"Field": "host-header", "HostHeaderConfig": {
            "Values": ["machine-learning-projects.com"],
        }}],
    })
    application.has_resource("AWS::Route53::RecordSet", {
        "Properties": {"Name": "machine-learning-projects.com.", "Type": "A",
                       "HostedZoneId": {"Fn::ImportValue": "SharedMachineLearningHostedZoneId"}},
        "DeletionPolicy": "Retain",
    })


def test_fixed_spot_capacity(application):
    application.has_resource_properties("AWS::AutoScaling::AutoScalingGroup", {
        "MinSize": "1", "MaxSize": "1", "DesiredCapacity": "1",
        "VPCZoneIdentifier": [{"Fn::ImportValue": "SharedPublicSubnet1Id"}],
        "MixedInstancesPolicy": {"InstancesDistribution": {
            "OnDemandBaseCapacity": 0, "OnDemandPercentageAboveBaseCapacity": 0,
        }},
    })
    application.has_resource_properties("AWS::EC2::LaunchTemplate", {
        "LaunchTemplateData": {"InstanceType": "t3.medium"},
    })
    application.has_resource_properties("AWS::ECS::CapacityProvider", {
        "AutoScalingGroupProvider": {"ManagedScaling": Match.absent(),
                                     "ManagedTerminationProtection": "DISABLED"},
    })


def test_private_retained_media_uses_pay_as_you_go_cloudfront(application, assembly):
    application.has_resource("AWS::S3::Bucket", {
        "DeletionPolicy": "Retain", "UpdateReplacePolicy": "Retain",
        "Properties": {"PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
        }},
    })
    media = Template.from_json(assembly.get_stack_by_name("PytorchMediaStack").template)
    media.resource_count_is("AWS::CloudFront::Distribution", 1)
    media.resource_count_is("AWS::CloudFront::OriginAccessControl", 1)
    media.resource_count_is("AWS::PricingPlanManager::Subscription", 0)
    media.resource_count_is("AWS::WAFv2::WebACL", 0)
    media.has_resource_properties("AWS::CloudFront::ResponseHeadersPolicy", {
        "ResponseHeadersPolicyConfig": {
            "CustomHeadersConfig": Match.absent(),
            "CorsConfig": {"AccessControlAllowOrigins": {"Items": ["*"]},
                           "OriginOverride": True},
        },
    })
    media.has_resource_properties("AWS::CloudFront::Distribution", {
        "DistributionConfig": {"DefaultCacheBehavior": {
            "ViewerProtocolPolicy": "redirect-to-https",
        }},
    })
