### Images partagées (pour une salle sans bon débit internet)

#### 1°) Construire les images une fois :

```bash
docker save $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '^hdd-lab|apache/impala|postgres|zookeeper') | gzip > hdd-images.tgz
```

#### 2°) Puis les distribuer :

```bash
# sur chaque poste :  
gunzip -c hdd-images.tgz | docker load
```
