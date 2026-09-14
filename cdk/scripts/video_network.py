"""Read shared network settings for the video deployment. Does not modify AWS."""

import json
import subprocess


def aws(service, command, *arguments):
    result = subprocess.run(
        ["aws", service, command, *arguments, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def find_route_table(vpc_id, subnet_id):
    tables = aws(
        "ec2", "describe-route-tables",
        "--filters", f"Name=association.subnet-id,Values={subnet_id}",
    )["RouteTables"]

    # Subnets without an explicit association use the VPC's main route table.
    if not tables:
        tables = aws(
            "ec2", "describe-route-tables",
            "--filters", f"Name=vpc-id,Values={vpc_id}",
            "Name=association.main,Values=true",
        )["RouteTables"]
    if len(tables) != 1:
        raise ValueError(f"Expected one route table for subnet {subnet_id}")
    return tables[0]["RouteTableId"]


def stack_endpoint_ids():
    try:
        stack = aws(
            "cloudformation", "list-stack-resources",
            "--stack-name", "PytorchClassificationStack",
        )
    except subprocess.CalledProcessError as error:
        # The application stack does not exist on the first deployment.
        if "does not exist" in error.stderr:
            return set()
        raise

    return {
        resource["PhysicalResourceId"]
        for resource in stack["StackResourceSummaries"]
        if resource["ResourceType"] == "AWS::EC2::VPCEndpoint"
    }


def has_shared_endpoint(endpoints, owned_ids, route_table, service):
    found = False
    for endpoint in endpoints:
        if not endpoint["ServiceName"].endswith(f".{service}"):
            continue
        # Keep CDK-owned endpoints in the template on subsequent deployments.
        if endpoint["VpcEndpointId"] in owned_ids:
            return False
        if route_table in endpoint.get("RouteTableIds", []):
            found = True
    return found


def main():
    exports = {
        item["Name"]: item["Value"]
        for item in aws("cloudformation", "list-exports")["Exports"]
    }
    vpc_id = exports["SharedVpcId"]
    subnet_id = exports["SharedPublicSubnet1Id"]
    route_table = find_route_table(vpc_id, subnet_id)
    endpoints = aws(
        "ec2", "describe-vpc-endpoints",
        "--filters", f"Name=vpc-id,Values={vpc_id}",
    )["VpcEndpoints"]
    owned_ids = stack_endpoint_ids()

    print(f"hosted_zone_id={exports['SharedMachineLearningHostedZoneId']}")
    print(f"route_table_id={route_table}")
    for service in ("s3", "dynamodb"):
        exists = has_shared_endpoint(endpoints, owned_ids, route_table, service)
        print(f"existing_{service}_endpoint={str(exists).lower()}")


if __name__ == "__main__":
    main()
