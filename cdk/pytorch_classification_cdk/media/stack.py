"""CloudFront delivery and its certificate live in us-east-1.

The main application stack owns regional S3 storage through MediaStorage.
"""
from aws_cdk import (
    CfnOutput, CfnParameter, Stack,
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_s3 as s3,
)
from constructs import Construct

from ..existing_resources import PRODUCTION_HOST
from ..application.constructs.media_storage import MEDIA_REGION, media_bucket_name

MEDIA_HOST = f"assets.{PRODUCTION_HOST}"


class MediaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        zone_id = CfnParameter(self, "HostedZoneId", type="AWS::Route53::HostedZone::Id")
        zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "ExistingZone", hosted_zone_id=zone_id.value_as_string,
            zone_name=PRODUCTION_HOST,
        )
        bucket = s3.Bucket.from_bucket_attributes(
            self, "MediaBucket", bucket_name=media_bucket_name(self),
            region=MEDIA_REGION,
        )
        certificate = acm.Certificate(
            self, "MediaCertificate", domain_name=MEDIA_HOST,
            validation=acm.CertificateValidation.from_dns(zone),
        )
        distribution = cloudfront.Distribution(
            self, "MediaDistribution", domain_names=[MEDIA_HOST],
            certificate=certificate,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                # Allow browser image analysis without disabling media caching.
                response_headers_policy=cloudfront.ResponseHeadersPolicy(
                    self, "PublicMediaHeaders",
                    cors_behavior=cloudfront.ResponseHeadersCorsBehavior(
                        access_control_allow_origins=["*"],
                        access_control_allow_methods=["GET", "HEAD"],
                        access_control_allow_headers=["*"],
                        access_control_allow_credentials=False,
                        origin_override=True,
                    ),
                ),
            ),
            comment="PyTorch media",
        )
        # CloudFormation supports cross-region S3 bucket policies from us-east-1.
        # Keep permissions with the distribution to avoid cross-region exports or
        # granting access to other distributions in this account.
        s3.CfnBucketPolicy(
            self, "RegionalMediaBucketPolicy", bucket=bucket.bucket_name,
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "cloudfront.amazonaws.com"},
                        "Action": "s3:GetObject",
                        "Resource": bucket.arn_for_objects("*"),
                        "Condition": {"StringEquals": {"AWS:SourceArn": distribution.distribution_arn}},
                    },
                    {
                        "Effect": "Deny", "Principal": {"AWS": "*"},
                        "Action": "s3:*",
                        "Resource": [bucket.bucket_arn, bucket.arn_for_objects("*")],
                        "Condition": {"Bool": {"aws:SecureTransport": "false"}},
                    },
                ],
            },
        )
        for record_type in (route53.ARecord, route53.AaaaRecord):
            record_type(
                self, record_type.__name__, zone=zone, record_name="assets",
                target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution)),
            )
        CfnOutput(self, "MediaBucketName", value=bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
        CfnOutput(self, "MediaBaseUrl", value=f"https://{MEDIA_HOST}")
