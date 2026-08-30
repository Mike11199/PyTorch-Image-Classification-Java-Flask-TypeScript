"""Synthesize the PyTorch classification production stack locally.

`cdk synth` creates only a CloudFormation template. It does not contact AWS,
bootstrap CDK, deploy, change DNS, or alter live traffic.
"""

from aws_cdk import App, Environment

from pytorch_classification_cdk.existing_resources import AWS_ACCOUNT_ID, AWS_REGION
from pytorch_classification_cdk.stack import PytorchClassificationStack


def main() -> None:
    app = App()
    PytorchClassificationStack(
        app,
        "PytorchClassificationStack",
        env=Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION),
    )
    app.synth()


if __name__ == "__main__":
    main()
