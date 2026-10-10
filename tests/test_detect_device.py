from types import SimpleNamespace

from django_datatables.detect_device import detect_device


def request_with(meta):
    return SimpleNamespace(META=meta)


def test_no_user_agent_is_not_mobile():
    assert detect_device(request_with({})) == {'mobile': False}


def test_desktop_user_agent_is_not_mobile():
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'
    assert detect_device(request_with({'HTTP_USER_AGENT': ua})) == {'mobile': False}


def test_android_and_iphone_are_mobile():
    for ua in ('Mozilla/5.0 (Linux; Android 14; Pixel 8)', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'):
        assert detect_device(request_with({'HTTP_USER_AGENT': ua})) == {'mobile': True}
