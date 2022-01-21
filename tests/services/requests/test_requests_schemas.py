def test_load_dump_only_field(app, identity_simple, submit_request, requests_service):
    request = submit_request(identity_simple)
    schema = requests_service._wrap_schema(request.type.marshmallow_schema())

    data, errors = schema.load(
        {"status": "cancelled"},
        context={
            "identity": identity_simple,
            "record": request,
        },
    )

    assert {} == data
    # This might seem surprising, but it's a side-effect of pre-load cleaning.
    # That the data above is {}, is the most important part.
    assert [] == errors


def test_load_additional_field(app, identity_simple, submit_request, requests_service):
    request = submit_request(identity_simple)
    schema = requests_service._wrap_schema(request.type.marshmallow_schema())

    data, errors = schema.load(
        {"receiver": {"user": "42"}},
        context={
            "identity": identity_simple,
            "record": request,
        },
    )

    assert {"receiver": {"user": "42"}} == data
    # This might seem surprising, but it's a side-effect of pre-load cleaning.
    # That the data above is {}, is the most important part.
    assert [] == errors
