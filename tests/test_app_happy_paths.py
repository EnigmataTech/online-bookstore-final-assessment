def test_index_lists_books(client):
    r = client.get("/")
    assert r.status_code == 200
    text = r.data.decode("utf-8", errors="ignore")
    assert any(t in text for t in ["The Great Gatsby", "1984", "I Ching", "Moby Dick"])

def test_add_to_cart_and_view(client):
    r = client.post("/add-to-cart", data={"title":"1984", "quantity":2}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/cart")
    assert r.status_code == 200

def test_checkout_success_with_discount(client):
    client.post("/add-to-cart", data={"title":"The Great Gatsby", "quantity":1}, follow_redirects=True)
    r = client.get("/checkout")
    assert r.status_code in (200, 302)
    r = client.post("/process-checkout", data={
        "name": "Alice",
        "email": "alice@example.com",
        "address": "1 Test St",
        "city": "Testville",
        "zip_code": "12345",
        "payment_method": "credit_card",
        "card_number": "4242424242424242",
        "expiry_date": "12/30",
        "cvv": "123",
        "discount_code": "SAVE10",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "/order-confirmation/" in r.headers.get("Location","")
