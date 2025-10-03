
import json
import time
import pytest
from store_manager import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_graphql_product_query(client):
    # Create a unique product
    unique_sku = f"SKU-{int(time.time() * 1000)}"
    product_payload = {"name": "GraphQL Item", "sku": unique_sku, "price": 12.34}
    resp = client.post(
        '/products', data=json.dumps(product_payload), content_type='application/json'
    )
    assert resp.status_code == 201
    product_id = resp.get_json()['product_id']

    # Set stock for this product
    set_stock_payload = {"product_id": product_id, "quantity": 7}
    resp = client.post(
        '/stocks', data=json.dumps(set_stock_payload), content_type='application/json'
    )
    assert resp.status_code == 201

    # Query GraphQL for product fields
    gql_query = (
        "query($id: String!) { "
        "  product(id: $id) { id name sku price quantity } "
        "}"
    )
    body = {"query": gql_query, "variables": {"id": str(product_id)}}
    resp = client.post('/stocks/graphql-query', data=json.dumps(body), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'data' in data and data['data'] is not None
    assert data.get('errors') in (None, [])

    product = data['data']['product']
    assert product['id'] == product_id
    assert product['name'] == 'GraphQL Item'
    assert product['sku'] == unique_sku
    # Float comparisons: allow small tolerance
    assert abs(product['price'] - 12.34) < 1e-6
    assert product['quantity'] == 7
