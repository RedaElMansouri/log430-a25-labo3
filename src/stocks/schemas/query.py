import graphene
from graphene import ObjectType, String, Int
from stocks.schemas.product import Product
from db import get_redis_conn
from stocks.queries.read_product import get_product_by_id

class Query(ObjectType):       
    product = graphene.Field(Product, id=String(required=True))
    stock_level = Int(product_id=String(required=True))
    
    def resolve_product(self, info, id):
        """Resolve product by id combining MySQL product info and Redis stock quantity."""
        # Fetch product master data from MySQL
        product_row = get_product_by_id(int(id))
        if not product_row:
            return None

        # Fetch stock qty from Redis (fallback 0 if missing)
        redis_client = get_redis_conn()
        quantity_val = redis_client.hget(f"stock:{id}", "quantity")
        quantity = int(quantity_val) if quantity_val is not None else 0

        return Product(
            id=int(product_row.get('id', id)),
            name=product_row.get('name'),
            sku=product_row.get('sku'),
            price=product_row.get('price'),
            quantity=quantity
        )
    
    def resolve_stock_level(self, info, product_id):
        """ Retrieve stock quantity from Redis """
        redis_client = get_redis_conn()
        quantity = redis_client.hget(f"stock:{product_id}", "quantity")
        return int(quantity) if quantity else 0