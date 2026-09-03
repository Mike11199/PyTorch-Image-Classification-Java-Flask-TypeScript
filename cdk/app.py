"""Synthesize the PyTorch classification infrastructure locally."""

from aws_cdk import App

from pytorch_classification_cdk.repository_stack import RepositoryStack
from pytorch_classification_cdk.stack import PytorchClassificationStack


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
    return app


def main() -> None:
    build_app().synth()


if __name__ == "__main__":
    main()
