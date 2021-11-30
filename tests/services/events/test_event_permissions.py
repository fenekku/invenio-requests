# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Permission tests."""

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError


def test_creator_and_receiver_can_comment(
        app, identity_simple, identity_simple_2, identity_stranger,
        request_events_service, events_service_data, submit_request):
    request = submit_request(identity_simple)
    request_id = request.id

    # Creator
    assert (
        request_events_service.create(identity_simple, request_id, events_service_data)
    )
    # Receiver
    assert (
        request_events_service.create(
            identity_simple_2, request_id, events_service_data
        )
    )
    # Stranger
    with pytest.raises(PermissionDeniedError):
        request_events_service.create(
            identity_stranger, request_id, events_service_data
        )
