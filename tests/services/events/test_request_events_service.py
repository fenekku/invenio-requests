# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""
import copy

from invenio_requests.proxies import current_requests
from invenio_requests.records.api import RequestEvent, RequestEventType


def test_simple_flow(app, identity_simple, events_service_data, example_request):
    """Interact with comment events."""
    events_service = current_requests.request_events_service
    request_id = example_request.number

    # Create a comment
    item = events_service.create(identity_simple, request_id, events_service_data)
    item_dict = item.to_dict()
    assert events_service_data["type"] == item_dict["type"]
    assert events_service_data["content"] == item_dict["content"]
    assert events_service_data["format"] == item_dict["format"]
    id_ = item.id

    # Read it
    read_item = events_service.read(identity_simple, id_)
    assert item.id == read_item.id
    assert item.to_dict() == read_item.to_dict()

    # Update it
    data = read_item.to_dict()  # should be equivalent to events_service_data
    data["content"] = "An edited comment"
    updated_item = events_service.update(identity_simple, id_, data)
    assert id_ == updated_item.id
    assert "An edited comment" == updated_item.to_dict()["content"]

    # Delete it
    deleted_item = events_service.delete(identity_simple, id_)
    assert deleted_item is True
    read_deleted_item = events_service.read(identity_simple, id_)
    read_del_item_dict = read_deleted_item.to_dict()
    assert id_ == read_deleted_item.id
    assert RequestEventType.REMOVED.value == read_del_item_dict["type"]

    # Search (batch read) events
    # first add another comment
    data = copy.deepcopy(events_service_data)
    data["content"] = "Another comment."
    item2 = events_service.create(identity_simple, request_id, data)
    # Refresh to make changes live
    RequestEvent.index.refresh()
    # then search
    searched_items = events_service.search(
        identity_simple,
        request_id,
        size=10,
        page=1,
    )
    assert 2 == searched_items.total


def test_delete_wipes_content(identity_simple, events_service_data, example_request):
    # Deleting a regular comment empties content and changes type (tested above)
    # Deleting an accept/decline/cancel event just wipes their content
    events_service = current_requests.request_events_service
    request_id = example_request.number
    types = ["ACCEPTED", "DECLINED", "CANCELLED"]

    for typ in types:
        type_value = getattr(RequestEventType, typ).value
        events_service_data["type"] = type_value
        item = events_service.create(identity_simple, request_id, events_service_data)
        item_dict = item.to_dict()
        comment_id = item.id

        events_service.delete(identity_simple, comment_id)

        read_deleted_item = events_service.read(identity_simple, comment_id)
        read_deleted_item_dict = read_deleted_item.to_dict()
        assert item_dict["type"] == read_deleted_item_dict["type"]
        assert "" == read_deleted_item_dict["content"]


def test_update_keeps_type(identity_simple, events_service_data, example_request):
    # The `update`` service method can't be used to change the type
    events_service = current_requests.request_events_service
    request_id = example_request.number
    # event type is COMMENT by default
    item = events_service.create(identity_simple, request_id, events_service_data)
    comment_id = item.id
    item_dict = item.to_dict()
    data = {
        **events_service_data,
        "type": RequestEventType.ACCEPTED.value
    }

    updated_item = events_service.update(identity_simple, comment_id, data)

    updated_item_dict = updated_item.to_dict()
    assert item_dict["type"] == updated_item_dict["type"]
