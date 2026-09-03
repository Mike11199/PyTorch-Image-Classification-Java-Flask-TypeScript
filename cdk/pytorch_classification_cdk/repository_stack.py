"""ECR repository infrastructure owned independently from the application."""

import json

from aws_cdk import CfnOutput, RemovalPolicy, Stack, aws_ecr as ecr
from constructs import Construct


class RepositoryStack(Stack):
    """Own the retained ECR repository used by the application images."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository = ecr.CfnRepository(
            self,
            "Repository",
            repository_name="pytorch-web",
            image_tag_mutability="MUTABLE",
            image_scanning_configuration=ecr.CfnRepository.ImageScanningConfigurationProperty(
                scan_on_push=False
            ),
            encryption_configuration=ecr.CfnRepository.EncryptionConfigurationProperty(
                encryption_type="AES256"
            ),
            lifecycle_policy=ecr.CfnRepository.LifecyclePolicyProperty(
                lifecycle_policy_text=json.dumps(
                    {
                        "rules": [
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
                                (
                                    1,
                                    "Keep the three most recent Flask API images",
                                    "flask-api-",
                                ),
                                (
                                    2,
                                    "Keep the three most recent Java API images",
                                    "java-api-",
                                ),
                                (
                                    3,
                                    "Keep the three most recent frontend images",
                                    "react-front-end-",
                                ),
                            )
                        ]
                        + [
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
                    }
                )
            ),
            empty_on_delete=False,
        )
        repository.override_logical_id("PytorchRepository")
        repository.apply_removal_policy(RemovalPolicy.RETAIN)

        CfnOutput(
            self,
            "PytorchRepositoryUri",
            value=repository.attr_repository_uri,
            export_name="PytorchRepositoryUri",
        )
