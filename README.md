# tarea2

 instrucciones para instalar las librerías 

1. **gRPC**:
   ```bash
   pip install grpcio
   pip install grpcio-tools
   ```

2. **Confluent Kafka**:
   ```bash
   pip install confluent-kafka
   ```

3. **Elasticsearch**:
   ```bash
   pip install elasticsearch
   ```

4. **python-dotenv** (para cargar variables de entorno desde un archivo `.env`):
   ```bash
   pip install python-dotenv
   ```
 instrucciones para inicializar el sistema  
   
5. **Primero construir el docker-compose** :
   ```bash
   sudo docker-compose up --build
   ```
6. **Segundo inicializar servidor grpc** :
   ```bash
   sudo python3 servidor/grpc_server.py
   ``` 
7. **Luego de iniciar el servidor se inicializa el consumer** :
   ```bash
   sudo python3 cliente/consumer.py
   ```
8. **Luego de iniciar el consumer se inicializa el servicio de mail** :
   ```bash
   sudo python3 cliente/send_email.py
   ```    
9. **Luego de iniciar el consumer se inicializa el cliente grpc para generar pedidos en ciertas cantidades** :
   ```bash
   sudo python3 cliente/grpc_client_traffic.py
   ``` 
