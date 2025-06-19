# Knowledge flow installation

## Installation of dependencies

Follow this [README](https://github.com/fred-agent/deployment-factory/tree/main/charts) to properly install all knowledge-flow dependencies.

## Installation of Knowledge-flow

## Compile Dockerfile to get knowledge-flow image

```
cp dockerfiles/Dockerfile-dev Dockerfile
make docker-build
```

Additional commands if you use k3s
```
docker save knowledge-flow-backend:0.1-dev | gzip > /tmp/image.tar.gz
sudo k3s ctr images import /tmp/image.tar.gz
```

## Install Knowledge-Flow

Overload the file `knowlegde-flow-backend/values.yaml`, specifically the three following variables, we recommend a separated customvalues.yaml file

```
@ConfigMap.data.configuration.yaml
@configMap.data.\.env
@ConfigMap_ext.data.kubeconfig
```

Then deploy knowledge-flow-backend

```
helm upgrade -i knowledge-flow-backend ./knowledge-flow-backend/ -n test
OR
helm upgrade -i knowledge-flow-backend ./knowledge-flow-backend/ -n test --values ./knowledge-flow-backend-custom-values.yaml
```

