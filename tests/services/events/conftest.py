# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request Events conftest."""

import pytest

from invenio_requests.records.api import RequestEventFormat, RequestEventType


@pytest.fixture()
def events_service_data():
    """Input data for the Request Events Service."""
    return {
        "type": RequestEventType.COMMENT.value,
        "payload": {
            "content": "This is a comment.",
            "format": RequestEventFormat.HTML.value,
        }
    }
