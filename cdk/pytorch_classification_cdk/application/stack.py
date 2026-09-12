"""Compose the application, shared routing, Spot capacity, and media storage."""

from aws_cdk import CfnParameter, Stack
from constructs import Construct

from .constructs.media_storage import MediaStorage
from .constructs.shared_network import SharedNetwork
from .constructs.application_service import ApplicationService
from .constructs.web_routing import WebRouting
from .constructs.spot_capacity import SpotCapacity


class PytorchClassificationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        MediaStorage(self, "MediaStorage")

        self.param_image_tag_flask = CfnParameter(
            self, "ImageTagFlask", default="flask-api-latest"
        )
        self.param_image_tag_java = CfnParameter(
            self, "ImageTagJava", default="java-api-latest"
        )
        self.param_image_tag_react = CfnParameter(
            self, "ImageTagReact", default="react-front-end-latest"
        )

        network = SharedNetwork(self, "Network")
        application = ApplicationService(
            self, "Application", vpc=network.vpc,
            shared_alb_security_group=network.alb_security_group,
            image_tag_flask=self.param_image_tag_flask.value_as_string,
            image_tag_java=self.param_image_tag_java.value_as_string,
            image_tag_react=self.param_image_tag_react.value_as_string,
        )
        routing = WebRouting(
            self, "Routing", vpc=network.vpc, service=application.service,
        )
        capacity = SpotCapacity(
            self, "Capacity", vpc=network.vpc, cluster=application.cluster,
        )

        # ECS creation waits for listener attachment and available host capacity.
        service = application.service.node.default_child
        service.add_resource_dependency(routing.listener_rule)
        service.add_resource_dependency(capacity.auto_scaling_group.node.default_child)
