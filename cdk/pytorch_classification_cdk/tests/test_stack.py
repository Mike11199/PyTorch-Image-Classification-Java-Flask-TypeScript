"""Infrastructure regression tests for the ECS CDK stack."""

from aws_cdk import App

from pytorch_classification_cdk.stack import PytorchClassificationStack


def synth_template() -> dict:
    app = App()
    stack = PytorchClassificationStack(app, "TestPytorchClassificationStack")
    return app.synth().get_stack_by_name(stack.stack_name).template


def resources_of_type(template: dict, resource_type: str) -> list[dict]:
    """Return all CloudFormation resources of the given type."""
    return [
        r for r in template["Resources"].values() if r["Type"] == resource_type
    ]


def test_ecs_service_runs_one_task():
    """Service maintains exactly one running task (not zero, not multiple)."""
    services = resources_of_type(synth_template(), "AWS::ECS::Service")
    assert len(services) == 1
    assert services[0]["Properties"]["DesiredCount"] == 1


def test_task_definition_has_three_containers():
    """Task definition includes Flask, Java, and Nginx containers — catches accidental container removal."""
    task_defs = resources_of_type(synth_template(), "AWS::ECS::TaskDefinition")
    assert len(task_defs) == 1

    names = {c["Name"] for c in task_defs[0]["Properties"]["ContainerDefinitions"]}
    expected = {"FlaskContainer", "JavaContainer", "NginxContainer"}
    assert set(names).issuperset(expected), f"Missing containers: {expected - names}"


def test_target_group_health_check_points_to_nginx():
    """Target group health check hits /health on port 80 — wrong path causes immediate task termination."""
    tgs = resources_of_type(synth_template(), "AWS::ElasticLoadBalancingV2::TargetGroup")
    assert len(tgs) == 1

    p = tgs[0]["Properties"]
    assert p["Port"] == 80
    assert p["HealthCheckPath"] == "/health"


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
    """ASG min=max=desired=1 — desired=None caused stuck DELETE_IN_PROGRESS on stack destroy."""
    asgs = resources_of_type(synth_template(), "AWS::AutoScaling::AutoScalingGroup")
    assert len(asgs) == 1

    p = asgs[0]["Properties"]
    assert p["MinSize"] == "1"
    assert p["MaxSize"] == "1"
    assert p.get("DesiredCapacity") in ("1", 1), f"Expected DesiredCapacity=1, got {p.get('DesiredCapacity')}"
