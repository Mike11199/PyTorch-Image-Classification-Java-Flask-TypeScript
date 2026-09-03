"""Infrastructure regression tests for the ECS CDK stack."""

import importlib.util
import json
from pathlib import Path

from aws_cdk import App

from pytorch_classification_cdk.stack import PytorchClassificationStack


def synth_template(deploy_version: str | None = None) -> dict:
    context = {"deploy-version": deploy_version} if deploy_version else None
    app = App(context=context)
    stack = PytorchClassificationStack(app, "TestPytorchClassificationStack")
    return app.synth().get_stack_by_name(stack.stack_name).template


def resources_of_type(template: dict, resource_type: str) -> list[dict]:
    """Return all CloudFormation resources of the given type."""
    return [
        r for r in template["Resources"].values() if r["Type"] == resource_type
    ]


def test_repository_stack_owns_retained_live_repository_and_exports_uri():
    from pytorch_classification_cdk.repository_stack import RepositoryStack

    app = App()
    stack = RepositoryStack(app, "TestPytorchRepositoryStack")
    template = app.synth().get_stack_by_name(stack.stack_name).template

    repository = template["Resources"]["PytorchRepository"]
    lifecycle_policy = json.loads(
        repository["Properties"].pop("LifecyclePolicy")["LifecyclePolicyText"]
    )
    assert repository == {
        "Type": "AWS::ECR::Repository",
        "Properties": {
            "EmptyOnDelete": False,
            "EncryptionConfiguration": {"EncryptionType": "AES256"},
            "ImageScanningConfiguration": {"ScanOnPush": False},
            "ImageTagMutability": "MUTABLE",
            "RepositoryName": "pytorch-web",
        },
        "UpdateReplacePolicy": "Retain",
        "DeletionPolicy": "Retain",
    }
    assert template["Outputs"]["PytorchRepositoryUri"]["Export"] == {
        "Name": "PytorchRepositoryUri"
    }
    assert lifecycle_policy["rules"] == [
        {
            "rulePriority": priority,
            "description": description,
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": [prefix],
                "countType": "imageCountMoreThan",
                "countNumber": 3,
            },
            "action": {"type": "expire"},
        }
        for priority, description, prefix in (
            (1, "Keep the three most recent Flask API images", "flask-api-"),
            (2, "Keep the three most recent Java API images", "java-api-"),
            (3, "Keep the three most recent frontend images", "react-front-end-"),
        )
    ] + [
        {
            "rulePriority": 4,
            "description": "Expire untagged images after one day",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 1,
            },
            "action": {"type": "expire"},
        }
    ]


def test_cdk_app_defines_repository_before_dependent_application_stack():
    app_path = Path(__file__).parents[2] / "app.py"
    spec = importlib.util.spec_from_file_location("pytorch_cdk_app", app_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    app = module.build_app()
    assembly = app.synth()
    repository_artifact = assembly.get_stack_by_name("PytorchRepositoryStack")
    application_artifact = assembly.get_stack_by_name("PytorchClassificationStack")

    assert repository_artifact.id in {
        dependency.id for dependency in application_artifact.dependencies
    }


def test_account_specific_resource_ids_are_not_stored_in_source():
    cdk_root = Path(__file__).parents[2]
    source = "\n".join(
        path.read_text()
        for path in (
            cdk_root / "app.py",
            cdk_root / "pytorch_classification_cdk/existing_resources.py",
        )
    )
    for forbidden in (
        "456461478565",
        "us-west-1",
        "172.31.0.0/16",
        "vpc-031a34e2307900372",
        "subnet-0069d564c7d9784e5",
        "sg-0190e299544ca1711",
        "arn:aws:elasticloadbalancing",
    ):
        assert forbidden not in source


def test_active_workflow_deploys_repository_before_building_application():
    workflows = Path(__file__).parents[3] / ".github/workflows"
    active = workflows / "deploy-cdk-aws.yml"
    disabled = workflows / "deploy-cdk-aws.yml.disabled"
    assert active.exists()
    assert not disabled.exists()

    workflow = active.read_text()
    repository_deploy = workflow.index("cdk deploy PytorchRepositoryStack")
    login = workflow.index("aws-actions/amazon-ecr-login")
    build = workflow.index("docker build")
    application_deploy = workflow.index("cdk deploy PytorchClassificationStack")

    assert repository_deploy < login < build < application_deploy
    assert "describe-repositories" not in workflow
    assert "create-repository" not in workflow


def test_application_deploy_excludes_the_already_deployed_repository_stack():
    """Image parameters must be sent only to the application stack."""
    workflow = (
        Path(__file__).parents[3] / ".github/workflows/deploy-cdk-aws.yml"
    ).read_text()
    application_deploy = workflow[
        workflow.index("cdk deploy PytorchClassificationStack") :
    ]

    assert "--exclusively" in application_deploy
    assert application_deploy.index("--exclusively") < application_deploy.index(
        "--parameters"
    )


def test_ecs_service_runs_one_task():
    """Singleton service uses stop-first updates and rolls back failed deployments."""
    services = resources_of_type(synth_template(), "AWS::ECS::Service")
    assert len(services) == 1
    properties = services[0]["Properties"]
    assert properties["DesiredCount"] == 1
    assert properties["DeploymentConfiguration"]["MinimumHealthyPercent"] == 0
    assert properties["DeploymentConfiguration"]["MaximumPercent"] == 100
    assert properties["DeploymentConfiguration"]["DeploymentCircuitBreaker"] == {
        "Enable": True,
        "Rollback": True,
    }


def test_task_definition_has_three_containers():
    """Runtime images include all containers, valid Java routing, and cached model weights."""
    task_defs = resources_of_type(synth_template(), "AWS::ECS::TaskDefinition")
    assert len(task_defs) == 1

    names = {c["Name"] for c in task_defs[0]["Properties"]["ContainerDefinitions"]}
    expected = {"FlaskContainer", "JavaContainer", "NginxContainer"}
    assert set(names).issuperset(expected), f"Missing containers: {expected - names}"

    project_root = Path(__file__).parents[3]
    nginx_config = (project_root / "frontend/nginx/default.conf").read_text()
    assert "client_max_body_size 100M;" in nginx_config
    assert "rewrite ^/api-java-spring-boot/" not in nginx_config
    assert "proxy_pass http://127.0.0.1:8080;" in nginx_config

    spring_config = (
        project_root
        / "backend-java-spring-boot/src/main/resources/application.yml"
    ).read_text()
    assert "max-file-size: 100MB" in spring_config
    assert "max-request-size: 100MB" in spring_config

    flask_dockerfile = (project_root / "backend-flask-pytorch/Dockerfile").read_text()
    assert "ENV TORCH_HOME=/opt/torch-cache" in flask_dockerfile
    assert "RUN python prefetch_models.py" in flask_dockerfile

    prefetch_script = (project_root / "backend-flask-pytorch/prefetch_models.py").read_text()
    assert "FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT" in prefetch_script
    assert "MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT" in prefetch_script


def test_target_group_health_check_points_to_nginx():
    """ALB can reach Nginx and service creation waits for listener attachment."""
    template = synth_template()
    tgs = resources_of_type(template, "AWS::ElasticLoadBalancingV2::TargetGroup")
    assert len(tgs) == 1

    p = tgs[0]["Properties"]
    assert p["Port"] == 80
    assert p["HealthCheckPath"] == "/health"

    services = resources_of_type(template, "AWS::ECS::Service")
    assert len(services) == 1
    assert services[0]["Properties"]["LoadBalancers"] == [
        {
            "ContainerName": "NginxContainer",
            "ContainerPort": 80,
            "TargetGroupArn": {"Ref": next(
                logical_id
                for logical_id, resource in template["Resources"].items()
                if resource["Type"] == "AWS::ElasticLoadBalancingV2::TargetGroup"
            )},
        }
    ]

    ingress = resources_of_type(template, "AWS::EC2::SecurityGroupIngress")
    assert len(ingress) == 1
    assert ingress[0]["Properties"]["FromPort"] == 80
    assert ingress[0]["Properties"]["ToPort"] == 80
    assert ingress[0]["Properties"]["SourceSecurityGroupId"] == {
        "Fn::ImportValue": "SharedAlbSecurityGroupId"
    }

    service_security_groups = resources_of_type(template, "AWS::EC2::SecurityGroup")
    assert len(service_security_groups) == 1
    assert service_security_groups[0]["Properties"]["VpcId"] == {
        "Fn::ImportValue": "SharedVpcId"
    }

    service_resource = next(
        resource
        for resource in template["Resources"].values()
        if resource["Type"] == "AWS::ECS::Service"
    )
    dependencies = service_resource.get("DependsOn", [])
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    assert "PytorchListenerRule" in dependencies
    asg_logical_id = next(
        logical_id
        for logical_id, resource in template["Resources"].items()
        if resource["Type"] == "AWS::AutoScaling::AutoScalingGroup"
    )
    assert asg_logical_id in dependencies


def test_listener_rule_routes_production_host():
    """Listener rule uses the current production priority and host."""
    rules = resources_of_type(
        synth_template(), "AWS::ElasticLoadBalancingV2::ListenerRule"
    )
    assert len(rules) == 1

    r = rules[0]["Properties"]
    assert r["Priority"] == 3
    assert r["Conditions"][0]["HostHeaderConfig"]["Values"] == ["machine-learning-projects.com"]
    assert r["ListenerArn"] == {"Fn::ImportValue": "SharedHttpsListenerArn"}
    listener_rule = synth_template()["Resources"]["PytorchListenerRule"]
    assert listener_rule["DeletionPolicy"] == "Retain"
    assert listener_rule["UpdateReplacePolicy"] == "Retain"


def test_shared_network_and_repository_are_consumed_through_exports():
    template = synth_template()

    target_group = resources_of_type(
        template, "AWS::ElasticLoadBalancingV2::TargetGroup"
    )[0]
    assert target_group["Properties"]["VpcId"] == {
        "Fn::ImportValue": "SharedVpcId"
    }
    assert target_group["DeletionPolicy"] == "Retain"
    assert target_group["UpdateReplacePolicy"] == "Retain"

    asg = resources_of_type(template, "AWS::AutoScaling::AutoScalingGroup")[0]
    assert asg["Properties"]["VPCZoneIdentifier"] == [
        {"Fn::ImportValue": "SharedPublicSubnet1Id"}
    ]

    task_definition = resources_of_type(template, "AWS::ECS::TaskDefinition")[0]
    images = {
        container["Name"]: container["Image"]
        for container in task_definition["Properties"]["ContainerDefinitions"]
    }
    for name, parameter in (
        ("FlaskContainer", "ImageTagFlask"),
        ("JavaContainer", "ImageTagJava"),
        ("NginxContainer", "ImageTagReact"),
    ):
        assert images[name] == {
            "Fn::Join": [
                "",
                [
                    {"Fn::ImportValue": "PytorchRepositoryUri"},
                    ":",
                    {"Ref": parameter},
                ],
            ]
        }


def test_owns_retained_root_alias_using_shared_outputs():
    template = synth_template()
    records = resources_of_type(template, "AWS::Route53::RecordSet")

    assert len(records) == 1
    alias = template["Resources"]["MachineLearningAliasRecord"]
    assert alias["DeletionPolicy"] == "Retain"
    assert alias["UpdateReplacePolicy"] == "Retain"
    assert alias["Properties"] == {
        "Name": "machine-learning-projects.com.",
        "Type": "A",
        "HostedZoneId": {"Fn::ImportValue": "SharedMachineLearningHostedZoneId"},
        "AliasTarget": {
            "DNSName": {
                "Fn::Join": [
                    "",
                    [
                        "dualstack.",
                        {"Fn::ImportValue": "SharedLoadBalancerDnsName"},
                        ".",
                    ],
                ]
            },
            "HostedZoneId": {
                "Fn::ImportValue": "SharedLoadBalancerCanonicalHostedZoneId"
            },
            "EvaluateTargetHealth": True,
        },
    }


def test_asg_is_fixed_at_one_instance():
    """ASG remains one instance and CI run numbers do not replace host resources."""
    template_v1 = synth_template("1")
    template_v2 = synth_template("2")
    asgs = resources_of_type(template_v1, "AWS::AutoScaling::AutoScalingGroup")
    assert len(asgs) == 1

    p = asgs[0]["Properties"]
    assert p["MinSize"] == "1"
    assert p["MaxSize"] == "1"
    assert p.get("DesiredCapacity") in ("1", 1), f"Expected DesiredCapacity=1, got {p.get('DesiredCapacity')}"
    assert p.get("NewInstancesProtectedFromScaleIn") in (None, False)

    capacity_providers = resources_of_type(template_v1, "AWS::ECS::CapacityProvider")
    assert len(capacity_providers) == 1
    provider = capacity_providers[0]["Properties"]["AutoScalingGroupProvider"]
    assert "ManagedScaling" not in provider
    assert provider["ManagedTerminationProtection"] == "DISABLED"

    def logical_ids(template: dict, resource_type: str) -> set[str]:
        return {
            logical_id
            for logical_id, resource in template["Resources"].items()
            if resource["Type"] == resource_type
        }

    assert logical_ids(template_v1, "AWS::AutoScaling::AutoScalingGroup") == logical_ids(
        template_v2, "AWS::AutoScaling::AutoScalingGroup"
    )
    assert logical_ids(template_v1, "AWS::EC2::LaunchTemplate") == logical_ids(
        template_v2, "AWS::EC2::LaunchTemplate"
    )

    workflow = (
        Path(__file__).parents[3] / ".github/workflows/deploy-cdk-aws.yml"
    ).read_text()
    assert "--context deploy-version" not in workflow
    assert "github.run_number" not in workflow
