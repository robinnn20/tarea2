from elasticsearch import Elasticsearch
from datetime import datetime
import grpc
from concurrent import futures
import time
import random
import orders_pb2
import orders_pb2_grpc
from confluent_kafka import Producer
from uuid import uuid4
from fsm import PedidoFSM
import threading

# Configuración de Kafka
producer_conf = {
    'bootstrap.servers': 'localhost:9093,localhost:9095',
    'client.id': 'productor1'
}
producer = Producer(producer_conf)

es = Elasticsearch(['http://localhost:9200']) 
index_name = "metrics"

pedidos_fsm = {}

def delivery_report(err, msg):
    if err is not None:
        print(f"Error al enviar mensaje: {err}")
    else:
        print(f"Mensaje enviado a {msg.topic()} [{msg.partition()}]")

def log_to_elasticsearch(data):
    """
    Función para almacenar métricas en Elasticsearch.
    """
    try:
        es.index(index=index_name, body=data)
    except Exception as e:
        print(f"Error al almacenar datos en Elasticsearch: {e}")

def process_order_states(order_id, client_mail, fsm_pedido):
    """
    Procesa todas las transiciones de estado del pedido de manera asíncrona,
    calculando métricas de latencia y throughput.
    """
    estados_tiempos = {
        'Procesando': (3, 5),
        'Preparación': (4, 6),
        'Enviado': (5, 7),
        'Entregado': (6, 8),
        'Finalizado': (3, 4)
    }
    
    current_state = fsm_pedido.estado_actual()
    start_time = datetime.now()
    
    while current_state != 'Finalizado':
        # Simular el tiempo de procesamiento para cada estado
        min_time, max_time = estados_tiempos.get(current_state, (1, 3))
        time.sleep(random.uniform(min_time, max_time))
        
        # Calcular latencia y registrar en Elasticsearch
        latency = (datetime.now() - start_time).total_seconds()
        log_to_elasticsearch({
            "timestamp": datetime.now(),
            "order_id": order_id,
            "state": current_state,
            "latency": latency,
            "metric_type": "latency"
        })

        # Realizar la transición al siguiente estado
        fsm_pedido.transicion('next')
        current_state = fsm_pedido.estado_actual()
        
        # Enviar actualización del estado a Kafka
        state_update = f"Actualización de pedido - ID: {order_id}, Estado: {current_state}, Cliente: {client_mail}"
        producer.produce(
            'orders',
            key=str(uuid4()),
            value=state_update,
            callback=delivery_report
        )
        producer.poll(0)
        
        print(f"Pedido {order_id} actualizado a estado: {current_state}")

    # Calcular el tiempo total de procesamiento y throughput
    processing_time = (datetime.now() - start_time).total_seconds()
    log_to_elasticsearch({
        "timestamp": datetime.now(),
        "order_id": order_id,
        "processing_time": processing_time,
        "metric_type": "processing_time"
    })

class OrderServiceServicer(orders_pb2_grpc.OrderServiceServicer):
    def CreateOrder(self, request, context):
        print(f"Nuevo pedido recibido: {request.product_name}, {request.price}")
        
        # Crear una nueva instancia de FSM para este pedido
        fsm_pedido = PedidoFSM()
        pedidos_fsm[request.order_id] = fsm_pedido
        
        # Registrar el estado inicial
        print(f"Estado inicial del pedido {request.order_id}: {fsm_pedido.estado_actual()}")
        
        # Enviar el pedido inicial a Kafka
        order_data = (
            f"ID: {request.order_id}, "
            f"Producto: {request.product_name}, "
            f"Precio: {request.price}, "
            f"Estado: {fsm_pedido.estado_actual()}, "
            f"Cliente: {request.customer_email}, "
            f"Dirección: {request.shipping_address}, "
            f"Región: {request.shipping_region}, "
            f"Método de pago: {request.payment_method}"
        )
        producer.produce(
            'orders',
            key=str(uuid4()),
            value=order_data,
            callback=delivery_report
        )
        producer.poll(0)
        
        # Iniciar el procesamiento de estados en un hilo separado
        thread = threading.Thread(
            target=process_order_states,
            args=(request.order_id, request.customer_email, fsm_pedido)
        )
        thread.start()
        
        # Log de throughput al crear el pedido
        log_to_elasticsearch({
            "timestamp": datetime.now(),
            "metric_type": "throughput",
            "event": "order_created"
        })
        
        # Responder al cliente
        response = orders_pb2.OrderResponse(
            message="Pedido creado exitosamente",
            order_id=request.order_id
        )
        return response
    
    def GetOrderStatus(self, request, context):
        """
        Método adicional para consultar el estado actual de un pedido
        """
        fsm_pedido = pedidos_fsm.get(request.order_id)
        if fsm_pedido:
            return orders_pb2.OrderStatusResponse(
                order_id=request.order_id,
                status=fsm_pedido.estado_actual()
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Pedido no encontrado')
            return orders_pb2.OrderStatusResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orders_pb2_grpc.add_OrderServiceServicer_to_server(OrderServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Servidor gRPC corriendo en el puerto 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
