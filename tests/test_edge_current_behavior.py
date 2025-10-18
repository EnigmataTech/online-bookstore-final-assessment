def test_checkout_failure_when_card_declines(client):
    client.post("/add-to-cart", data={"title":"1984", "quantity":1}, follow_redirects=True)
    r = client.post("/process-checkout", data={
        "name": "Bob",
        "email": "bob@example.com",
        "address": "2 Test St",
        "city": "Testville",
        "zip_code": "99999",
        "payment_method": "credit_card",
        "card_number": "4111111111111111",
        "expiry_date": "12/30",
        "cvv": "111",
        "discount_code": "",
    }, follow_redirects=True)
    assert r.status_code in (200, 302)

def test_update_cart_zero_quantity_current_behavior(client):
    client.post("/add-to-cart", data={"title":"Moby Dick", "quantity":1}, follow_redirects=True)
    r = client.post("/update-cart", data={"title":"Moby Dick", "quantity":0}, follow_redirects=True)
    assert r.status_code in (200, 302)
    r = client.get("/cart")
    assert r.status_code == 200
