# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Requests service."""

from invenio_db import db
from invenio_records_resources.services import (
    RecordService,
    RecordServiceConfig,
    ServiceSchemaWrapper,
)
from invenio_records_resources.services.records.components import DataComponent
from invenio_records_resources.services.records.links import pagination_links
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from ...proxies import current_registry
from ...records.api import Request
from .components import IdentifierComponent
from .config import RequestsServiceConfig
from .links import RequestLink
from .results import RequestItem, RequestList


class RequestsService(RecordService):
    """Requests service."""

    @property
    def request_type_registry(self):
        """Request_type_registry."""
        return current_registry

    def _wrap_schema(self, schema):
        """Wrap schema."""
        return ServiceSchemaWrapper(self, schema)

    def _request_from_model(self, model):
        """Request from model."""
        # TODO handle 'model is None' more gracefully
        #      -> may happen e.g. when reading a deleted request
        request_cls = self.request_type_registry.lookup(
            model.data.get("request_type", None)
        )
        return request_cls(model.data, model=model)

    def _get_request(self, id_):
        """Placeholder docstring."""
        # TODO first query by external ID, then by internal?
        try:
            model = self.record_cls.model_cls.query.filter_by(
                external_id=str(id_)
            ).one()

        except (MultipleResultsFound, NoResultFound):
            # either no results or ambiguous results
            # (e.g. if external_id is None)
            # NOTE: if 'id_' is None, this will return None!
            model = self.record_cls.model_cls.query.get(id_)

        # TODO add registry as part of the configuration
        request = self._request_from_model(model)
        return request

    def create(self, identity, data, request_class):
        """Create a record."""
        self.require_permission(identity, "create")

        schema = self._wrap_schema(request_class.marshmallow_schema)
        data, errors = schema.load(
            data,
            context={"identity": identity},
        )

        # it's the components that will populate the actual data
        request = request_class.create({})

        # run components
        for component in self.components:
            if hasattr(component, "create"):
                component.create(
                    identity,
                    data=data,
                    record=request,
                    errors=errors,
                )

        # persist record (DB and index)
        request.commit()
        db.session.commit()
        if self.indexer:
            self.indexer.index(request)

        return self.result_item(
            self,
            identity,
            request,
            schema=schema,
            links_tpl=self.links_item_tpl,
            errors=errors,
        )

    def read(self, id_, identity):
        """Retrieve a request."""
        # resolve and require permission
        request = self._get_request(id_)
        self.require_permission(identity, "read", record=request)

        # run components
        for component in self.components:
            if hasattr(component, "read"):
                component.read(identity, record=request)

        return self.result_item(
            self,
            identity,
            request,
            schema=self._wrap_schema(request.marshmallow_schema),
            links_tpl=self.links_item_tpl,
        )

    def read_all(self, identity, fields, max_records=150, **kwargs):
        """Search for records matching the querystring."""
        # TODO check later
        return super().read_all(identity, fields, max_records=max_records, **kwargs)

    def read_many(self, identity, ids, fields=None, **kwargs):
        """Search for requests matching the ids."""
        # TODO check later
        return super().read_many(identity, ids, fields=fields, **kwargs)

    def scan(self, identity, params=None, es_preference=None, **kwargs):
        """Scan for requests matching the querystring."""
        # TODO check later
        return super().scan(identity, params=None, es_preference=None, **kwargs)

    def search(self, identity, params=None, es_preference=None, **kwargs):
        """Search for records matching the querystring."""
        # TODO check later
        return super().search(identity, es_preference=None, **kwargs)

    def update(self, id_, identity, data):
        """Replace a request."""
        request = self._get_request(id_)

        # TODO do we need revisions for requests?
        # self.check_revision_id(request, revision_id)

        # check permissions
        self.require_permission(identity, "update", record=request)

        schema = self._wrap_schema(request.marshmallow_schema)
        data, _ = schema.load(
            data,
            context={
                "identity": identity,
                "record": request,
            },
        )

        # run components
        for component in self.components:
            if hasattr(component, "update"):
                component.update(identity, data=data, record=request)

        request.commit()
        db.session.commit()

        if self.indexer:
            self.indexer.index(request)

        return self.result_item(
            self,
            identity,
            request,
            schema=schema,
            links_tpl=self.links_item_tpl,
        )

    def delete(self, id_, identity):
        """Delete a request from database and search indexes."""
        request = self._get_request(id_)

        # TODO do we need revisions for requests?
        # self.check_revision_id(request, revision_id)

        # check permissions
        self.require_permission(identity, "delete", record=request)

        # run components
        for component in self.components:
            if hasattr(component, "delete"):
                component.delete(identity, record=request)

        request.delete()
        db.session.commit()

        if self.indexer:
            self.indexer.delete(request, refresh=True)

        return True

    def reindex(self, identity, params=None, es_preference=None, **kwargs):
        """Reindex records matching the query parameters."""
        # TODO check later
        return super().reindex(identity, params=None, es_preference=None, **kwargs)

    def rebuild_index(self, identity):
        """Reindex all records managed by this service."""
        for req_meta in self.record_cls.model_cls.query.all():
            request = self._request_from_model(req_meta)

            if not request.is_deleted:
                self.indexer.index(request)

    def execute_action(self, action, id_, identity):
        """Execute the given action for the request, if possible.

        For instance, it would be not possible to execute the specified
        action on the request, if the latter has the wrong status.
        """
        request = self._get_request(id_)

        # TODO permission checks

        # check if the action *can* be executed
        # (i.e. the request has the right status, etc.)
        if not request.can_execute_action(action, identity):
            # TODO proper exception
            raise Exception

        return request.execute_action(action, identity)
