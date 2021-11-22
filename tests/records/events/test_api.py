# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from jsonschema import ValidationError

from invenio_requests.records import RequestEvent
from invenio_requests.records.api import RequestEventType


def test_request_event_jsonschema(app, db, example_request):
    event = RequestEvent.create(
        {},
        request=example_request.model,
        request_id=example_request.number,
        type=RequestEventType.COMMENT.value,
    )
    db.session.commit()
    assert event.schema

    # JSONSchema validation works.
    pytest.raises(ValidationError, RequestEvent.create, {'garbage': {'bar': 1}})
