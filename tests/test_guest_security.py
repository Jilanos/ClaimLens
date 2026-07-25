from claimlens.auth import guest_csrf_token, new_guest_token


def test_guest_csrf_is_bound_to_guest_identity():
    first = new_guest_token()
    second = new_guest_token()

    assert guest_csrf_token(first) != guest_csrf_token(second)
    assert guest_csrf_token(first) == guest_csrf_token(first)
