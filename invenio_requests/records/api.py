# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""API classes for requests in Invenio."""

from datetime import datetime
from enum import Enum

import pytz
from invenio_db import db
from invenio_records.dumpers import ElasticsearchDumper
from invenio_records.systemfields import ConstantField, DictField, ModelField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from ..errors import NoSuchActionError
from .dumpers import CalculatedFieldDumperExt, RequestTypeDumperExt
from .models import RequestEventModel, RequestMetadata
from .systemfields import (
    IdentityField,
    OpenStateCalculatedField,
    ReferencedEntityField,
    RequestStatusField,
    RequestTypeField,
)


class Request(Record):
    """A generic request record."""

    model_cls = RequestMetadata
    """The model class for the request."""

    dumper = ElasticsearchDumper(
        extensions=[
            CalculatedFieldDumperExt("is_open"),
            CalculatedFieldDumperExt("is_expired"),
            RequestTypeDumperExt("request_type"),
        ]
    )
    """Elasticsearch dumper with configured extensions."""

    number = IdentityField("external_id")
    """The request's external identity."""

    metadata = None
    """Disabled metadata field from the base class."""

    index = IndexField("requests-request-v1.0.0", search_alias="requests")
    """The Elasticsearch index to use for the request."""

    schema = ConstantField("$schema", "local://requests/request-v1.0.0.json")
    """The JSON Schema to use for validation."""

    request_type = RequestTypeField("request_type_id")
    """System field for management of the request type.

    This field manages loading of the correct RequestType classes associated with
    `Requests`, based on their `request_type_id` field.
    This is important because the `RequestType` classes are the place where the
    custom request actions are registered.
    """

    topic = ReferencedEntityField("topic")
    """Topic (associated object) of the request."""

    created_by = ReferencedEntityField("created_by")
    """The entity that created the request."""

    receiver = ReferencedEntityField("receiver")
    """The entity that will receive the request."""

    status = RequestStatusField("status")
    """The current status of the request."""

    is_open = OpenStateCalculatedField("is_open")
    """Whether or not the current status can be seen as an 'open' state."""

    expires_at = ModelField("expires_at")
    """Expiration date of the request."""

    @property
    def is_expired(self):
        """Check if the Request is expired."""
        if self.expires_at is None:
            return False

        # comparing timezone-aware and naive datetimes results in an error
        # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive # noqa
        now = datetime.utcnow()
        d = self.expires_at
        if d.tzinfo and d.tzinfo.utcoffset(d) is not None:
            now = now.replace(tzinfo=pytz.utc)

        return d < now

    def get_action(self, action_name):
        """Get the action registered under the given name.

        :param action_name: The registered name of the action.
        :return: The action registered under the given name.
        """
        try:
            return self.request_type.available_actions[action_name](self)
        except KeyError:
            raise NoSuchActionError(action=action_name)

    def can_execute_action(self, action_name, identity):
        """Check if the action registered under the given name can be executed.

        :param action_name: The registered name of the action.
        :param identity: The identity who wants to execute the action.
        :return: Whether or not the action can be executed.
        """
        return self.get_action(action_name).can_execute(identity)

    def execute_action(self, action_name, identity):
        """Execute the action registered under the given name.

        :param action_name: The registered name of the action.
        :param identity: The identity who wants to execute the action.
        :return: The return value of the executed action.
        """
        return self.get_action(action_name).execute(identity)

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Retrieve the request by id.

        :param id_: The record ID (external or internal).
        :param with_deleted: If `True`, then it includes deleted requests.
        :returns: The :class:`Request` instance.
        """
        # note: in case of concurrency errors, `with db.session.no_autoflush` might help
        try:
            query = cls.model_cls.query.filter_by(external_id=str(id_))
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa

            model = query.one()

        except (MultipleResultsFound, NoResultFound):
            # either no results or ambiguous results
            # (e.g. if external_id is None)
            # NOTE: if 'id_' is None, this will return None!
            query = cls.model_cls.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa

            model = query.one()

        if model is None:
            # TODO maybe some kind of `NullRequest`?
            return None

        return cls(model.data, model=model)


class RequestEventType(Enum):
    """Request Event type enum."""

    COMMENT = "C"
    DELETED_COMMENT = "D"


class RequestEventFormat(Enum):
    """Comment/content format enum."""

    HTML = "html"


class RequestEvent(Record):
    """A Request Event."""

    model_cls = RequestEventModel

    # Systemfields
    metadata = None

    request = ModelField(dump=False)
    """The request."""

    request_id = DictField("request_id")
    """The data-layer id of the related Request."""

    type = ModelField("type")
    """The human-readable event type."""

    index = IndexField("request_events-event-v1.0.0", search_alias="request_events")
    """The ES index used."""

    id = ModelField("id")
    """The data-layer id."""

    # TODO: Revisit when dealing with ownership
    created_by = DictField("created_by")
    """Who created the event."""
