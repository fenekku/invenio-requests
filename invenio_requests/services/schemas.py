# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request Event Schemas."""

from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import fields, validate
from marshmallow_utils import fields as utils_fields

from ..records.api import RequestEventFormat, RequestEventType


class RequestEventSchema(BaseRecordSchema):
    """Schema."""

    type = fields.Str(
        required=True,
        validate=validate.OneOf(choices=[e.value for e in RequestEventType]),
    )
    content = utils_fields.SanitizedHTML()
    format = fields.Str(
        validate=validate.OneOf(choices=[e.value for e in RequestEventFormat]),
        load_default=RequestEventFormat.HTML.value
    )
