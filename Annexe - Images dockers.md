### Images partagées (pour une salle sans bon débit internet)

#### 1°) Construire les images une fois :

```bash
docker save $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '^hdd-lab|apache/impala|postgres|zookeeper') | gzip > hdd-images.tgz
```

Récupérer ce fichier tgz avec WinSCP ( ex. : l'image Ubuntu tourne sous HyperV)


#### 2°) Puis distribuer :

Exemple pour Unbuntu dans WSL2 : 
```bash
cp -r '/mnt/f/Formation/Hadoop HDD - Dévt - 3 jours/05. Images docker/hdd-images.tgz' ~/HDD/
```

```bash
# sur chaque poste :  
gunzip -c hdd-images.tgz | docker load
```
