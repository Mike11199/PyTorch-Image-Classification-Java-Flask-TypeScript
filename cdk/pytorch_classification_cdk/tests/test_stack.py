"""Infrastructure regression tests for the ECS CDK stack."""

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
    assert "rewrite ^/api-java-spring-boot/" not in nginx_config
    assert "proxy_pass http://127.0.0.1:8080;" in nginx_config

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
    assert ingress[0]["Properties"]["SourceSecurityGroupId"] == "sg-0190e299544ca1711"

    service_resource = next(
        resource
        for resource in template["Resources"].values()
        if resource["Type"] == "AWS::ECS::Service"
    )
    dependencies = service_resource.get("DependsOn", [])
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    assert "PytorchListenerRule" in dependencies


def test_listener_rule_routes_production_host():
    """Listener rule uses correct priority (10) and production host — wrong values cause traffic collision."""
    rules = resources_of_type(
        synth_template(), "AWS::ElasticLoadBalancingV2::ListenerRule"
    )
    assert len(rules) == 1

    r = rules[0]["Properties"]
    assert r["Priority"] == 10
    assert r["Conditions"][0]["HostHeaderConfig"]["Values"] == ["machine-learning-projects.com"]


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
