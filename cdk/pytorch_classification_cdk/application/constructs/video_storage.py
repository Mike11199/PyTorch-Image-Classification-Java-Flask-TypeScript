"""Private retained video results, expiring uploads, and on-demand job records."""

from aws_cdk import (
    CfnCondition,
    CfnOutput,
    CfnParameter,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_ec2 as ec2,
    aws_s3 as s3,
)
from constructs import Construct


class VideoStorage(Construct):
    """Provide retained outputs, expiring inputs, and private AWS access."""

    def __init__(self, scope: Construct, construct_id: str, *, vpc: ec2.IVpc):
        """Create video resources without changing their deployed construct paths."""
        super().__init__(scope, construct_id)
        self.bucket = self.create_bucket()
        self.table = self.create_table()
        self.create_endpoints(scope, vpc)
        CfnOutput(scope, "VideoBucketName", value=self.bucket.bucket_name)
        CfnOutput(scope, "VideoJobsTableName", value=self.table.table_name)

    def create_bucket(self):
        """Retain results while expiring temporary uploads and previews."""
        return s3.Bucket(
            self,
            "Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
            # Only temporary inputs expire; videos/ contains retained playback and masks.
            lifecycle_rules=[
                s3.LifecycleRule(
                    prefix="jobs/",
                    expiration=Duration.days(1),
                    abort_incomplete_multipart_upload_after=Duration.days(1),
                )
            ],
            cors=[
                s3.CorsRule(
                    allowed_origins=[
                        "https://machine-learning-projects.com",
                        "http://localhost:5173",
                    ],
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.HEAD,
                        s3.HttpMethods.POST,
                    ],
                    allowed_headers=["*"],
                    exposed_headers=["ETag", "Content-Length", "Content-Range"],
                )
            ],
        )

    def create_table(self):
        """Store job records and let TTL expire unfinished jobs."""
        return dynamodb.Table(
            self,
            "Jobs",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expiresAt",
            removal_policy=RemovalPolicy.RETAIN,
        )

    def create_endpoints(self, scope, vpc):
        """Add gateway routes only when the shared subnet has none."""
        route_table = CfnParameter(
            scope,
            "VideoRouteTableId",
            type="String",
            description="Route table used by the shared ECS subnet",
        )
        for service in ("s3", "dynamodb"):
            present = CfnParameter(
                scope,
                f"VideoExisting{service.title()}Endpoint",
                default="false",
                allowed_values=["true", "false"],
            )
            condition = CfnCondition(
                self,
                f"Create{service.title()}Endpoint",
                expression=Fn.condition_equals(present.value_as_string, "false"),
            )
            endpoint = ec2.CfnVPCEndpoint(
                self,
                f"{service.title()}Endpoint",
                vpc_id=vpc.vpc_id,
                vpc_endpoint_type="Gateway",
                service_name=f"com.amazonaws.{Stack.of(self).region}.{service}",
                route_table_ids=[route_table.value_as_string],
            )
            endpoint.cfn_options.condition = condition
