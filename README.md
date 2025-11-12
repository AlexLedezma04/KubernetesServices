# Práctica Kubernetes - Azure Kubernetes Service (AKS)

Aplicación web de práctica desplegada en Azure Kubernetes Service, compuesta por un frontend en Nginx, una API REST en Flask y una base de datos MariaDB.

## Arquitectura

El proyecto consta de tres componentes principales:

- **Frontend**: Servidor Nginx que sirve una interfaz web estática
- **API**: Aplicación Flask que expone endpoints REST
- **Base de datos**: MariaDB para persistencia de datos

## Estructura del Proyecto

```
.
├── api
│   ├── app.py                      # Aplicación Flask
│   ├── Dockerfile                  # Imagen Docker de la API
│   └── requirements.txt            # Dependencias Python
├── docker-compose.yml              # Configuración para desarrollo local
├── frontend
│   ├── Dockerfile                  # Imagen Docker del frontend
│   ├── index.html                  # Interfaz web
│   └── nginx.conf                  # Configuración de Nginx
└── k8s
    ├── api-deployment.yaml         # Deployment y Service de la API
    ├── frontend-deployment.yaml    # Deployment y Service del frontend
    └── mariadb-deployment.yaml     # Deployment y Service de MariaDB
```

## Endpoints de la API

- `GET /healthz` - Health check de la API
- `GET /products` - Obtiene lista de productos

## Requisitos Previos

Antes de comenzar, asegúrate de tener instaladas las siguientes herramientas (Esto es una guía para usuarios que usen un sistema operativo Linux Debian o derivados.)

### 1. Instalar Docker

```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

sudo usermod -aG docker $USER
```

### 2. Instalar kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

kubectl version --client
```

### 3. Instalar Azure CLI

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 4. Verificar instalaciones

```bash
docker --version
kubectl version --client
az --version
```

## Despliegue en Azure Kubernetes Service

### Paso 1: Autenticarse en Azure

```bash
az login
```

### Paso 2: Crear un Resource Group

```bash
az group create --name myResourceGroup --location eastus
```

### Paso 3: Crear un Azure Container Registry (ACR)

```bash
az acr create --resource-group myResourceGroup --name myContainerRegistry --sku Basic
```

### Paso 4: Autenticarse en ACR

```bash
az acr login --name myContainerRegistry
```

### Paso 5: Construir y subir las imágenes Docker

#### Construir imagen de la API

```bash
cd api
docker build -t mycontainerregistry.azurecr.io/api:v1 .
docker push mycontainerregistry.azurecr.io/api:v1
cd ..
```

#### Construir imagen del Frontend

```bash
cd frontend
docker build -t mycontainerregistry.azurecr.io/frontend:v1 .
docker push mycontainerregistry.azurecr.io/frontend:v1
cd ..
```

### Paso 6: Crear un clúster de AKS

```bash
az aks create \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --node-count 2 \
  --generate-ssh-keys \
  --attach-acr myContainerRegistry
```

### Paso 7: Conectarse al clúster

```bash
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
```

### Paso 8: Verificar conexión

```bash
kubectl get nodes
```

### Paso 9: Actualizar manifiestos de Kubernetes

Edita los archivos en la carpeta `k8s/` y reemplaza las referencias de imágenes Docker con tus imágenes de ACR:

```yaml
image: mycontainerregistry.azurecr.io/api:v1
```

### Paso 10: Desplegar en Kubernetes

```bash
kubectl apply -f k8s/mariadb-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

### Paso 11: Verificar el despliegue

```bash
kubectl get pods
kubectl get services
```

### Paso 12: Obtener la IP externa del frontend

```bash
kubectl get service frontend-service --watch
```

Espera hasta que aparezca una IP externa y accede a la aplicación desde tu navegador.

## Variables de Entorno

Las siguientes variables de entorno se utilizan en los deployments:

### MariaDB
- `MYSQL_ROOT_PASSWORD`: contraseña del usuario root (default: rootpassword)
- `MYSQL_DATABASE`: nombre de la base de datos (default: mydb)
- `MYSQL_USER`: usuario de la base de datos (default: user)
- `MYSQL_PASSWORD`: contraseña del usuario (default: password)

### API Flask
- `DATABASE_HOST`: host de la base de datos (default: mariadb-service)
- `DATABASE_USER`: usuario de la base de datos (default: user)
- `DATABASE_PASSWORD`: contraseña del usuario (default: password)
- `DATABASE_NAME`: nombre de la base de datos (default: mydb)

## Desarrollo Local

Para ejecutar el proyecto localmente con Docker Compose:

```bash
docker-compose up --build
```

Accede a:
- Frontend: http://localhost:80
- API: http://localhost:5000

## Comandos Útiles

### Ver logs de un pod

```bash
kubectl logs <nombre-del-pod>
```

### Acceder a un pod

```bash
kubectl exec -it <nombre-del-pod> -- /bin/bash
```

### Eliminar todos los recursos

```bash
kubectl delete -f k8s/
```

### Eliminar el clúster de AKS

```bash
az aks delete --resource-group myResourceGroup --name myAKSCluster
```

### Eliminar el Resource Group

```bash
az group delete --name myResourceGroup --yes --no-wait
```

## Solución de Problemas

### Los pods no inician

```bash
kubectl describe pod <nombre-del-pod>
```

### Error de autenticación con ACR

```bash
az aks update --resource-group myResourceGroup --name myAKSCluster --attach-acr myContainerRegistry
```

### Verificar conectividad entre servicios

```bash
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Dentro del contenedor:
nslookup api-service
nslookup mariadb-service
```