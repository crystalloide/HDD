## Annexe : Ubuntu : installation de docker et docker compose : 

```bash
sudo apt update
```

Quelques dépendances sont nécessaires pour l'installation : 

```bash
sudo apt install curl apt-transport-https ca-certificates software-properties-common
```
Une fois les listes de paquets mises à jour et les paquets logiciels requis en place, on peut installer Docker :

#### Installation de Docker :

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```
Ensuite, on ajoute le référentiel Docker APT au système :

La commande crée un fichier référentiel docker.list dans le répertoire /etc/apt/sources.list.d

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

#### Ensuite, on met à jour le gestionnaire de paquet local pour qu'il prenne en compte le référentiel nouvellement ajouté :

```bash
sudo apt update
```

#### On installe maintenant Docker Community Edition (téléchargement et utilisation gratuits) comme suit :

Dans cette commande, l'option -y permet une installation non interactive :

```bash
sudo apt install docker-ce -y
```

```bash
sudo systemctl status docker
sudo systemctl start docker
sudo systemctl status docker
```

```bash
sudo usermod -aG docker user
```

```bash
su user
```
```bash
docker version
```

Affichage : 

Client: Docker Engine - Community
 Version:           29.10.1
 API version:       1.57
 Go version:        go1.27.4
 Git commit:        c48360f
 Built:             Tue Nov 24 19:44:17 2026
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          29.10.1
  API version:      1.57 (minimum version 1.40)
  Go version:       go1.27.4
  Git commit:       54cd494
  Built:            Tue Nov 24 19:44:40 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.4.2
  GitCommit:        b7a25261e029d68978bbf290df0a62fc819b3c51
 runc:
  Version:          1.5.3
  GitCommit:        v1.5.3-0-g46365c62
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
  
  
####  Vérifions : 

```bash
docker compose version
```

Affichage : 
	Docker Compose version v5.8.0
