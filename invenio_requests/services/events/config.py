# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request Events Service Config."""

from invenio_records_resources.services import RecordServiceConfig
from invenio_records_resources.services.records.components import DataComponent

from ...records.api import Request, RequestEvent
from ..permissions import PermissionPolicy
from ..schemas import RequestEventSchema
from .customization import CustomizationConfigMixin


class RequestEventsServiceConfig(
        RecordServiceConfig, CustomizationConfigMixin):
    """Config."""

    request_cls = Request
    permission_policy_cls = PermissionPolicy
    schema = RequestEventSchema
    record_cls = RequestEvent
    components = [
        DataComponent,
    ]
