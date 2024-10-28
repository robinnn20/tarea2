from datetime import datetime
from elasticsearch import Elasticsearch
import time

class PedidoFSM:
    # Definición de los estados y transiciones permitidas
    estados = {
        'Procesando': {'next': 'Preparación'},
        'Preparación': {'next': 'Enviado', 'previous': 'Procesando'},
        'Enviado': {'next': 'Entregado', 'previous': 'Preparación'},
        'Entregado': {'next': 'Finalizado', 'previous': 'Enviado'},
        'Finalizado': {'previous': 'Entregado'}
    }

    def __init__(self, estado_inicial='Procesando'):
        self.estado = estado_inicial
        self.timestamp_entrada = datetime.now()
        self.es = Elasticsearch(['http://localhost:9200'])

    def transicion(self, evento):
        if evento in self.estados[self.estado]:
            # Calcula la latencia en el estado actual antes de cambiar de estado
            latencia = (datetime.now() - self.timestamp_entrada).total_seconds()

            # Registrar la métrica de latencia en Elasticsearch
            self._registrar_metricas(latencia)

            # Actualizar el estado y el timestamp de entrada para el nuevo estado
            self.estado = self.estados[self.estado][evento]
            self.timestamp_entrada = datetime.now()
        else:
            raise ValueError(f"Transición no válida desde el estado {self.estado} con evento '{evento}'")

    def estado_actual(self):
        return self.estado

    def _registrar_metricas(self, latencia):
        """Envía las métricas de latencia a Elasticsearch"""
        doc = {
            'estado': self.estado,
            'timestamp': datetime.now(),
            'latencia': latencia
        }
        
        # Enviar el documento a Elasticsearch al índice `order_metrics`
        self.es.index(index='order_metrics', document=doc)
        print(f"Registrando métrica en Elasticsearch: {doc}")
