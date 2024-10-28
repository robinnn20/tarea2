import grpc
import orders_pb2
import orders_pb2_grpc
import random
import time

# Crear una conexión con el servidor gRPC
channel = grpc.insecure_channel('localhost:50051')
stub = orders_pb2_grpc.OrderServiceStub(channel)

# Listas para simular datos aleatorios
product_names = ["Laptop", "Smartphone", "Tablet", "Monitor", "Teclado"]
payment_methods = ["Webpay", "Paypal", "Transferencia"]
card_brands = ["VISA", "Mastercard", "American Express"]
banks = ["Banco Estado", "Santander", "Banco de Chile", "BBVA"]
regions = ["Metropolitana", "Valparaíso", "BioBío", "Araucanía"]
addresses = ["Av. Principal 123", "Calle Falsa 456", "Pasaje Largo 789"]
emails = ["cliente1@example.com", "cliente2@example.com", "cliente3@example.com"]

# Generador de pedidos
def generate_order(order_id):
    order_request = orders_pb2.OrderRequest(
        order_id=str(order_id),
        product_name=random.choice(product_names),
        price=round(random.uniform(100, 2000), 2), # Precio entre 100 y 2000
        payment_method=random.choice(payment_methods),
        card_brand=random.choice(card_brands),
        bank=random.choice(banks),
        shipping_region=random.choice(regions),
        shipping_address=random.choice(addresses),
        customer_email=random.choice(emails)
    )
    return order_request

# Número de pedidos a generar
num_orders = 30

# Crear y enviar pedidos
for i in range(num_orders):
    order_request = generate_order(order_id=i + 1)
    try:
        response = stub.CreateOrder(order_request)
        print(f"Pedido {i + 1}: Respuesta del servidor: {response.message}, Order ID: {response.order_id}")
    except grpc.RpcError as e:
        print(f"Error al enviar el pedido {i + 1}: {e}")
    
    time.sleep(0.5)
