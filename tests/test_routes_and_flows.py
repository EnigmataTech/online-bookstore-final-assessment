def test_homepage_lists_books(client):
    r = client.get("/")
    assert r.status_code == 200
    text = r.data.decode("utf-8", errors="ignore")
    assert any(t in text for t in ["Book", "Featured", "Catalog", "Home", "The Great Gatsby", "1984", "I Ching", "Moby Dick"])

def test_login_logout_cycle(client):
    r = client.get("/login")
    assert r.status_code in (200, 302)
    r = client.post("/login", data={"email": "demo@bookstore.com", "password": "demo123"}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/logout", follow_redirects=True)
    assert r.status_code in (200, 302)

def test_register_then_login(client):
    r = client.get("/register")
    assert r.status_code in (200, 302)
    email = "testuser+ci@example.com"
    r = client.post("/register", data={"email": email, "password": "pw12345", "name": "CI User", "address": "123 Road"}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.post("/login", data={"email": email, "password": "pw12345"}, follow_redirects=True)
    assert r.status_code in (200, 302)

def test_cart_add_update_remove_flow(client):
    # Add 2 copies of 1984
    r = client.post("/add-to-cart", data={"title": "1984", "quantity": 2}, follow_redirects=True)
    assert r.status_code in (200, 302)
    # View cart
    r = client.get("/cart")
    assert r.status_code == 200
    # Update quantity to 3
    r = client.post("/update-cart", data={"title": "1984", "quantity": 3}, follow_redirects=True)
    assert r.status_code in (200, 302)
    # "Remove" by setting quantity to 0 (your route flashes 'Removed ...')
    r = client.post("/update-cart", data={"title": "1984", "quantity": 0}, follow_redirects=True)
    assert r.status_code in (200, 302)

def test_discount_codes_and_checkout(client):
    client.post("/add-to-cart", data={"title": "The Great Gatsby", "quantity": 1}, follow_redirects=True)
    # There is no dedicated discount endpoint — discount_code is handled in process-checkout
    r = client.get("/checkout")
    assert r.status_code in (200, 302)
    r = client.post(
        "/process-checkout",
        data={
            "name": "Alice",
            "address": "1 Test St",
            "email": "alice@example.com",
            "city": "Testville",
            "zip_code": "12345",
            "payment_method": "credit_card",
            "card_number": "4242424242424242",
            "expiry_date": "12/30",
            "cvv": "123",
            "discount_code": "SAVE10",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "/order-confirmation/" in r.headers.get("Location", "")
