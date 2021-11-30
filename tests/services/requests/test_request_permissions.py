# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission tests."""
import copy

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from invenio_requests.records.api import RequestEventFormat


@pytest.fixture()
def requests_service_action_input_data():
    return {
        "payload": {
            "content": "Can I belong to the community?",
            "format": RequestEventFormat.HTML.value,
        }
    }


def test_only_creator_can_submit(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, create_request):
    request = create_request(identity_simple)
    request_id = request.id
    data = requests_service_action_input_data

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "submit", data)
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple_2, request_id, "submit", data)
    # Creator
    assert (
        requests_service.execute_action(identity_simple, request_id, "submit", data)
    )


def test_only_receiver_can_accept(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    data = copy.deepcopy(requests_service_action_input_data)
    data["payload"]["content"] = "You are in."

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "accept", data)
    # Creator
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple, request_id, "accept", data)
    # Receiver
    assert (
        requests_service.execute_action(identity_simple_2, request_id, "accept", data)
    )


def test_only_receiver_can_decline(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id
    data = copy.deepcopy(requests_service_action_input_data)
    data["payload"]["content"] = "You are NOT in."

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "decline", data)
    # Creator
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple, request_id, "decline", data)
    # Receiver
    assert (
        requests_service.execute_action(identity_simple_2, request_id, "decline", data)
    )


def test_only_creator_can_cancel(
        app, identity_simple, identity_simple_2, identity_stranger,
        requests_service, requests_service_action_input_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id

    # Stranger
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_stranger, request_id, "cancel")
    # Receiver
    with pytest.raises(PermissionDeniedError):
        requests_service.execute_action(identity_simple_2, request_id, "cancel")
    # Creator
    assert (
        requests_service.execute_action(identity_simple, request_id, "cancel")
    )
