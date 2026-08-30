"""Build bootstrap metadata for the PyTorch classification EC2 instance.

What this file does:
  On ECS/Fargate, you define a task and AWS handles all of this automatically — no files needed.
  We're on EC2 to save money (~$30/mo vs Fargate), so we manually package our assets into
  CloudFormation Init commands that install them onto raw instances when they boot.

When CDK synthesizes the stack, this module reads docker-compose.yml, runtime.env.template,
and startup_ec2.sh from cdk/assets/ and converts them into CloudFormation Init commands that
copy those files to /opt/pytorch on a new EC2 instance.

How it works:
  - build_bootstrap_init(): Packages the three asset files with proper permissions and creates
    a command to run startup_ec2.sh after they land on disk. CDK attaches this metadata to the ASG,
    so every freshly launched instance (initial deploy or self-healing replacement) installs these
    files automatically from its launch configuration — no S3 downloads, no IAM permissions needed.

  - build_deployment_user_data(): Writes the current image tags into /var/lib/pytorch-deployment/
    as marker files during first boot. This makes CloudFormation detect when GitHub Actions passes
    new SHA-based tags and know it needs to launch a fresh instance with those versions.

Why split this from stack.py:
  Keeps asset handling separate from infrastructure definitions so neither file becomes one giant
  unreadable blob of strings. Stack.py declares AWS resources (ASG, ALB rule); this file handles
  which files end up on the EC2 and how they get installed.
"""

from pathlib import Path

from aws_cdk import aws_ec2 as ec2


_ASSETS_DIR = Path(__file__).parent.parent / "assets"
_INSTALL_DIR = "/opt/pytorch"


def _read_asset(relative_path: str) -> str:
    """Read a version-controlled bootstrap asset during CDK synthesis."""

    return (_ASSETS_DIR / relative_path).read_text(encoding="utf-8")


def _render_runtime_env(
    *,
    registry: str,
    flask_tag: str,
    java_tag: str,
    react_tag: str,
    nginx_tag: str,
) -> str:
    """Render the non-secret Compose environment with CloudFormation tag tokens."""

    replacements = {
        "__REGISTRY__": registry,
        "__FLASK_TAG__": flask_tag,
        "__JAVA_TAG__": java_tag,
        "__REACT_TAG__": react_tag,
        "__NGINX_TAG__": nginx_tag,
    }

    content = _read_asset("runtime.env.template")
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def build_deployment_user_data(
    *,
    flask_tag: str,
    java_tag: str,
    react_tag: str,
    nginx_tag: str,
) -> ec2.UserData:
    """Put image tags in launch user data so parameter changes replace the host.

    CloudFormation does not rerun Init commands when only resource metadata changes.
    These harmless marker files make each image tag part of the launch configuration.
    """

    user_data = ec2.UserData.for_linux()
    user_data.add_commands(
        "mkdir -p /var/lib/pytorch-deployment",
        f'echo "{flask_tag}" > /var/lib/pytorch-deployment/flask-image-tag',
        f'echo "{java_tag}" > /var/lib/pytorch-deployment/java-image-tag',
        f'echo "{react_tag}" > /var/lib/pytorch-deployment/react-image-tag',
        f'echo "{nginx_tag}" > /var/lib/pytorch-deployment/nginx-image-tag',
    )
    return user_data


def build_bootstrap_init(
    *,
    registry: str,
    flask_tag: str,
    java_tag: str,
    react_tag: str,
    nginx_tag: str,
) -> ec2.CloudFormationInit:
    """Create Init metadata that installs assets and runs the bootstrap script.

    CDK appends ``cfn-init`` and ``cfn-signal`` to instance user data. A nonzero
    startup-script exit therefore fails the CloudFormation create or rolling update.
    """

    runtime_env = _render_runtime_env(
        registry=registry,
        flask_tag=flask_tag,
        java_tag=java_tag,
        react_tag=react_tag,
        nginx_tag=nginx_tag,
    )

    return ec2.CloudFormationInit.from_elements(
        ec2.InitFile.from_string(
            f"{_INSTALL_DIR}/docker-compose.yml",
            _read_asset("docker-compose.yml"),
            owner="root",
            group="root",
            mode="000644",
        ),
        ec2.InitFile.from_string(
            f"{_INSTALL_DIR}/runtime.env",
            runtime_env,
            owner="root",
            group="root",
            mode="000600",
        ),
        ec2.InitFile.from_string(
            f"{_INSTALL_DIR}/startup_ec2.sh",
            _read_asset("startup_ec2.sh"),
            owner="root",
            group="root",
            mode="000755",
        ),
        ec2.InitCommand.shell_command(
            f"{_INSTALL_DIR}/startup_ec2.sh",
            cwd=_INSTALL_DIR,
            key="01-bootstrap-containers",
        ),
    )
