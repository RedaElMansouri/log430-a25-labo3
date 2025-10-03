"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`)
    # Utiliser un SKU unique pour éviter les collisions si les tests sont rejoués
    import time
    unique_sku = f"SKU-{int(time.time() * 1000)}"
    product_data = {'name': 'Some Item', 'sku': unique_sku, 'price': 99.90}
    response = client.post('/products',
                        data=json.dumps(product_data),
                        content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['product_id'] > 0 
    product_id = data['product_id']

    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    set_stock_payload = { 'product_id': product_id, 'quantity': 5 }
    response = client.post('/stocks',
                        data=json.dumps(set_stock_payload),
                        content_type='application/json')
    assert response.status_code == 201
    result = response.get_json()
    assert 'result' in result

    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 201
    stock = response.get_json()
    assert stock.get('product_id') == product_id
    qty_initial = int(stock.get('quantity', -1))
    print(f"Quantité initiale pour produit {product_id}: {qty_initial}")
    assert qty_initial == 5

    # 4. Faites une commande de l'article que vous avez crée, 2 unités (`POST /orders`)
    order_payload = {
        'user_id': 1,  # utilisateur existant de la BD d'initialisation
        'items': [
            { 'product_id': product_id, 'quantity': 2 }
        ]
    }
    response = client.post('/orders',
                        data=json.dumps(order_payload),
                        content_type='application/json')
    assert response.status_code == 201
    order_resp = response.get_json()
    assert order_resp['order_id'] > 0
    order_id = order_resp['order_id']

    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 201
    stock_after_order = response.get_json()
    assert stock_after_order.get('product_id') == product_id
    qty_after_order = int(stock_after_order.get('quantity', -1))
    print(f"Quantité après commande pour produit {product_id}: {qty_after_order}")
    assert qty_after_order == 3

    # 6. Étape extra: supprimez la commande et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
    response = client.delete(f'/orders/{order_id}')
    assert response.status_code in (200, 201)
    del_resp = response.get_json()
    assert del_resp.get('deleted') is True

    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 201
    stock_after_delete = response.get_json()
    assert stock_after_delete.get('product_id') == product_id
    qty_after_delete = int(stock_after_delete.get('quantity', -1))
    print(f"Quantité après suppression de commande pour produit {product_id}: {qty_after_delete}")
    assert qty_after_delete == 5

    # Impression de la quantité pour l'article avec id=2 (données d'initialisation)
    resp2 = client.get('/stocks/2')
    if resp2.status_code == 201:
        stock2 = resp2.get_json()
        qty2 = int(stock2.get('quantity', -1))
        print(f"Quantité pour produit 2: {qty2}")