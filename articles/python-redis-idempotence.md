# Python + Redis Idempotence
Create an API idempotence layer using Python and Redis

## Deploy Redis
```shell
❯ kubectl --context rancher-desktop apply -f kubernetes/redis-secret.yaml
secret/redis-secret created
❯ kubectl --context rancher-desktop apply -f kubernetes/redis-config.yaml
configmap/redis-config created
❯ kubectl --context rancher-desktop apply -f kubernetes/redis-deployment.yaml
deployment.apps/redis-deployment created
❯ kubectl --context rancher-desktop apply -f kubernetes/redis-service.yaml
service/redis-service created
❯ kubectl --context rancher-desktop get secrets
NAME            TYPE                                  DATA   AGE
redis-secret    Opaque                                1      31s
❯ kubectl --context rancher-desktop get configmaps
NAME                   DATA   AGE
redis-config           1      62s
❯ kubectl --context rancher-desktop get deployments.apps
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
redis-deployment   1/1     1            1           5m1s
❯ kubectl --context rancher-desktop get service
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
kubernetes      ClusterIP   10.43.0.1       <none>        443/TCP     280d
redis-service   ClusterIP   10.43.157.132   <none>        6379/TCP    4m43s
```

### Connect to Redis
Install `redis-cli` client
```shell
❯ brew install redis
```
Port-forward the Kubernetes `redis-service` to a local host port `6380`
```shell
kubectl --context rancher-desktop port-forward service/redis-service 6380:6379
```
Connect to the Redis service using the client
```shell
redis-cli -h 127.0.0.1 -p 6380 -a YourPasswordHere
```
Try set and retrieve a key
```shell
127.0.0.1:6380> SET my-key "Foo, bar!"
OK
127.0.0.1:6380> GET my-key
"Foo, bar!"
127.0.0.1:6380>
```
