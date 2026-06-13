from proxy_rotator import ProxyRotator


def test_empty_proxy_list():
    p = ProxyRotator(proxy_list=[])
    assert p.get() is None
    assert p.count == 0


def test_single_proxy():
    p = ProxyRotator(proxy_list=["http://1.2.3.4:8080"])
    assert p.count == 1
    assert "http://1.2.3.4:8080" in p.available


def test_blacklist_mark():
    p = ProxyRotator(proxy_list=["http://1.2.3.4:8080", "http://5.6.7.8:8080"])
    p.mark_failed("http://1.2.3.4:8080")
    avail = p.available
    assert "http://1.2.3.4:8080" not in avail
    assert "http://5.6.7.8:8080" in avail


def test_blacklist_expiry():
    p = ProxyRotator(proxy_list=["http://1.2.3.4:8080"])
    p.mark_failed("http://1.2.3.4:8080")
    assert "http://1.2.3.4:8080" not in p.available
    assert "http://1.2.3.4:8080" in p._proxies


def test_add_proxy():
    p = ProxyRotator(proxy_list=[])
    p.add("http://9.9.9.9:3128")
    assert p.count == 1
    assert "http://9.9.9.9:3128" in p.available


def test_remove_proxy():
    p = ProxyRotator(proxy_list=["http://1.2.3.4:8080", "http://5.6.7.8:8080"])
    p.remove("http://1.2.3.4:8080")
    assert p.count == 1
    assert "http://5.6.7.8:8080" in p.available
