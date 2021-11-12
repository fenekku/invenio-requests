# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for generic and customizable requests."""

from invenio_base.utils import load_or_import_from_config

from . import config
from .resources import (
    RequestCommentsResource,
    RequestCommentsResourceConfig,
    RequestsResource,
    RequestsResourceConfig,
)
from .services import (
    RequestEventsService,
    RequestEventsServiceConfig,
    RequestsService,
    RequestsServiceConfig,
    RequestTypeRegistry,
)


class InvenioRequests:
    """Invenio-Requests extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        self.requests_service = None
        self.requests_resource = None
        self.request_comments_service = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_services(app)
        self.init_resources()
        self.init_registry(app)
        app.extensions["invenio-requests"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("REQUESTS_"):
                app.config.setdefault(k, getattr(config, k))

    def service_configs(self, app):
        """Customized service configs."""
        # overall requests/comments permission policy
        permission_policy = load_or_import_from_config(
            key="REQUESTS_PERMISSION_POLICY", app=app
        )

        class ServiceConfigs:
            requests = RequestsServiceConfig.customize(
                permission_policy=permission_policy,
            )
            request_events = RequestEventsServiceConfig.customize(
                permission_policy=permission_policy,
            )

        return ServiceConfigs

    def init_services(self, app):
        """Initialize the service and resource for Requests."""
        service_configs = self.service_configs(app)

        self.requests_service = RequestsService(
            config=service_configs.requests,
        )
        self.request_events_service = RequestEventsService(
            config=service_configs.request_events,
        )

    def init_resources(self):
        """Init resources."""
        self.requests_resource = RequestsResource(
            service=self.requests_service,
            config=RequestsResourceConfig,
        )

        self.request_events_resource = RequestCommentsResource(
            service=self.request_events_service,
            config=RequestCommentsResourceConfig,
        )

    def init_registry(self, app):
        """Initialize the resgistry for Requests per type."""
        self.request_type_registry = RequestTypeRegistry(
            app.config["REQUESTS_REGISTERED_TYPES"]
        )
