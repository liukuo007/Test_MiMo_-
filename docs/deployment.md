# 部署指南

## Docker 部署

```bash
# 构建并启动所有服务
make docker-up

# 停止所有服务
make docker-down
```

## Kubernetes 部署

```bash
# 创建命名空间
kubectl apply -f deploy/k8s/namespace.yaml

# 部署后端
kubectl apply -f deploy/k8s/backend-deployment.yaml

# 部署前端
kubectl apply -f deploy/k8s/frontend-deployment.yaml

# 配置 Ingress
kubectl apply -f deploy/k8s/ingress.yaml
```

## 环境变量

参考 `.env.example` 文件配置环境变量。

关键配置项：

- `DATABASE_URL`: PostgreSQL 连接字符串
- `REDIS_URL`: Redis 连接字符串
- `JWT_SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `MQTT_BROKER_URL`: MQTT Broker 地址
