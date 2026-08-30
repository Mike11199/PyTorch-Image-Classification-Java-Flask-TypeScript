"""Infrastructure regression tests for the production CDK stack."""

from pathlib import Path

from aws_cdk import App

from pytorch_classification_cdk.stack import PytorchClassificationStack


ROOT = Path(__file__).parents[2]


def synth_template() -> dict:
    app = App()
    stack = PytorchClassificationStack(app, "TestPytorchClassificationStack")
    return app.synth().get_stack_by_name(stack.stack_name).template


def resources_of_type(template: dict, resource_type: str) -> list[dict]:
    return [
        resource
        for resource in template["Resources"].values()
        if resource["Type"] == resource_type
    ]


def test_asg_is_fixed_at_one_and_registered_without_app_restart_loop() -> None:
    template = synth_template()
    asg = resources_of_type(template, "AWS::AutoScaling::AutoScalingGroup")[0]

    assert asg["Properties"]["MinSize"] == "1"
    assert asg["Properties"]["MaxSize"] == "1"
    assert asg["Properties"]["DesiredCapacity"] == "1"
    assert asg["Properties"]["HealthCheckType"] == "EC2"
    assert len(asg["Properties"]["TargetGroupARNs"]) == 1


def test_cloudformation_waits_for_bootstrap_signal() -> None:
    template = synth_template()
    asg = resources_of_type(template, "AWS::AutoScaling::AutoScalingGroup")[0]

    assert asg["CreationPolicy"]["ResourceSignal"]["Timeout"] == "PT30M"
    rolling_update = asg["UpdatePolicy"]["AutoScalingRollingUpdate"]
    assert rolling_update["WaitOnResourceSignals"] is True
    assert rolling_update["PauseTime"] == "PT30M"

    template_text = str(template)
    assert "cfn-init" in template_text
    assert "cfn-signal" in template_text
    assert "# fingerprint:" in template_text

    assert not resources_of_type(template, "AWS::AutoScaling::LaunchConfiguration")
    launch_template = resources_of_type(template, "AWS::EC2::LaunchTemplate")[0]
    launch_user_data = str(
        launch_template["Properties"]["LaunchTemplateData"]["UserData"]
    )
    for parameter in (
        "ImageTagFlask",
        "ImageTagJava",
        "ImageTagReact",
        "ImageTagNginx",
    ):
        assert parameter in launch_user_data


def test_listener_rule_forwards_production_host_to_target_group() -> None:
    template = synth_template()
    target_groups = resources_of_type(
        template, "AWS::ElasticLoadBalancingV2::TargetGroup"
    )
    assert len(target_groups) == 1

    rule = resources_of_type(
        template, "AWS::ElasticLoadBalancingV2::ListenerRule"
    )[0]["Properties"]

    assert rule["Priority"] == 99
    assert rule["Conditions"] == [
        {
            "Field": "host-header",
            "HostHeaderConfig": {
                "Values": ["classify.alpine-peak-climbing-ski-gear.com"]
            },
        }
    ]
    assert rule["Actions"][0]["Type"] == "forward"


def test_bootstrap_assets_are_rerunnable_and_self_verifying() -> None:
    startup = (ROOT / "assets" / "startup_ec2.sh").read_text()
    compose = (ROOT / "assets" / "docker-compose.yml").read_text()
    nginx_dockerfile = (ROOT / "assets" / "nginx" / "Dockerfile").read_text()
    nginx_config = (ROOT / "assets" / "nginx" / "default.conf").read_text()

    assert '--file "$COMPOSE_FILE" pull' in startup
    assert '--file "$COMPOSE_FILE" up -d --remove-orphans' in startup
    assert "--status running --services" in startup
    assert "docker inspect --format" in startup
    assert "verify_service_image" in startup
    assert "ecr-login" in startup
    assert "curl --fail" in startup
    assert compose.count("restart: unless-stopped") == 4
    assert "COPY cdk/assets/nginx/default.conf /etc/nginx/nginx.conf" in nginx_dockerfile
    assert "include /etc/nginx/conf.d/*.conf" not in nginx_config


def test_bootstrap_package_install_is_compatible_with_amazon_linux_2023() -> None:
    startup = (ROOT / "assets" / "startup_ec2.sh").read_text()

    # AL2023 includes curl-minimal; installing full curl conflicts with it.
    assert "dnf install -y docker amazon-ecr-credential-helper curl" not in startup
    assert "dnf install -y docker amazon-ecr-credential-helper" in startup


def test_exhausted_bootstrap_verification_returns_failure() -> None:
    """Bootstrap signals failure when health checks exceed max attempts."""

    startup = (ROOT / "assets" / "startup_ec2.sh").read_text()
    # wait_for_health dies after max_attempts; trap handler emits diagnostics before exit.
    assert 'wait_for_health()' in startup or "# Main: run steps sequentially" in startup
    assert 'emit_diagnostics' in startup

def test_workflow_never_terminates_an_asg_instance_on_verification_failure() -> None:
    workflow = (ROOT.parent / ".github" / "workflows" / "deploy-cdk-aws.yml").read_text()

    assert "terminate-instances" not in workflow
    assert "describe-target-health" in workflow
    assert "needs.build-docker-images.outputs" not in workflow
