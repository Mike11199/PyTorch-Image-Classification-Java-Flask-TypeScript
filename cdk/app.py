"""Synthesize the PyTorch classification infrastructure locally."""

from aws_cdk import App, Environment

from pytorch_classification_cdk.media.stack import MediaStack
from pytorch_classification_cdk.repository.stack import RepositoryStack
from pytorch_classification_cdk.application.stack import PytorchClassificationStack


def build_app() -> App:
    app = App()
    repository_stack = RepositoryStack(
        app, "PytorchRepositoryStack", analytics_reporting=False
    )
    application_stack = PytorchClassificationStack(
        app,
        "PytorchClassificationStack",
    )
    application_stack.add_stack_dependency(repository_stack)
    delivery_stack = MediaStack(
        app, "PytorchMediaStack", env=Environment(region="us-east-1"),
        analytics_reporting=False,
    )
    delivery_stack.add_stack_dependency(application_stack)
    return app


def main() -> None:
    build_app().synth()


if __name__ == "__main__":
    main()
