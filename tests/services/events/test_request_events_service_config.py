# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test the service configuration."""

import pytest
from invenio_records_permissions.generators import AnyUser, SystemProcess

from invenio_requests.proxies import current_requests
from invenio_requests.services import RequestEventsServiceConfig
from invenio_requests.services.permissions import PermissionPolicy


class CustomPermissionPolicy(PermissionPolicy):
    """Custom permission policy."""

    can_search = [SystemProcess()]
    can_read = [SystemProcess()]
    can_create = [SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]
    can_test = [AnyUser()]


@pytest.fixture(scope="module")
def app_config(app_config):
    """Fixture for customizing the service config via app config."""
    app_config["REQUESTS_PERMISSION_POLICY"] = CustomPermissionPolicy
    return app_config


def test_customizations_via_app_config(app):
    """Test if the customization mechanism works correctly."""
    current_permission_policy_cls = (
        current_requests.request_events_service.config.permission_policy_cls
    )

    assert current_permission_policy_cls is CustomPermissionPolicy
    assert hasattr(current_permission_policy_cls, "can_test")


def test_customization_mixin():
    """Test if the customize mixin method does what it is supposed to do."""
    custom_config_cls = RequestEventsServiceConfig.customize(
        permission_policy=CustomPermissionPolicy
    )

    # check if it created a new class
    assert custom_config_cls is not RequestEventsServiceConfig

    # check if both classes have the correct
    assert RequestEventsServiceConfig.permission_policy_cls is PermissionPolicy
    assert custom_config_cls.permission_policy_cls is CustomPermissionPolicy
