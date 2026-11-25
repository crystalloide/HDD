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
	 Version:           29.8.1
	 API version:       1.56
	 Go version:        go1.26.8
	 Git commit:        4a63305
	 Built:             Tue Sep 15 16:25:42 2026
	 OS/Arch:           linux/amd64
	 Context:           default

	Server: Docker Engine - Community
	 Engine:
	  Version:          29.8.1
	  API version:      1.56 (minimum version 1.40)
	  Go version:       go1.26.8
	  Git commit:       464cd50
	  Built:            Tue Sep 15 16:25:42 2026
	  OS/Arch:          linux/amd64
	  Experimental:     false
	 containerd:
	  Version:          v2.3.5
	  GitCommit:        1294c24a7da8e5a793ed378161673abe94118892
	 runc:
	  Version:          1.5.1
	  GitCommit:        v1.5.1-0-g8f2685a4
	 docker-init:
	  Version:          0.19.0
	  GitCommit:        de40ad0
  
  
####  Vérifions : 

```bash
docker compose version
```

Affichage : 
	Docker Compose version v5.5.1
