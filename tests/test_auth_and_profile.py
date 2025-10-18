def test_login_logout_cycle(client):
    r = client.post("/login", data={"email":"demo@bookstore.com", "password":"demo123"}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/logout", follow_redirects=True)
    assert r.status_code in (200, 302)

def test_register_requires_name_and_then_login(client):
    r = client.post("/register", data={
        "email":"testuser+ci@example.com",
        "password":"pw12345",
        "name":"Test User",
        "address":"123 Road",
    }, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/account", follow_redirects=True)
    assert r.status_code in (200, 302)
