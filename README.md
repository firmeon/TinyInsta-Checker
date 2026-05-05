# TinyInsta checker
Projet de test de scalabilité pour le projet https://github.com/momo54/massive-gcp

Le projet TinyInsta est déployé à cette adresse : https://tinyinsta-gcp.ew.r.appspot.com/

## Résultats

### Expérience 1 - Passage à l'échelle sur la charge
Cette expérience consiste à l'envoi simultané de requêtes au serveur.

![Graphique de concurrence](conc.png)

En analysant le fichier [csv](out/conc.csv), il apparait que le nombre de serveur reste à 1 jusqu'à 20 utilisateurs simultané. Lorsque les 50 utilisateurs arrivent, un nouveau serveur est alloué, ce qui prend du temps. Au total, on arrive à 4 serveurs à la fin des trois runs à 50 utilisateurs.
Les serveurs sont déjà démarrés donc pour 100 utilisateurs le temps est plus faible que pour 50 (pas de démarrage de serveurs).
Pour 1 000, 12 serveurs doivent démarrer, ce qui implique un temps plus conséquent.

En excluant le temps de démarrage des serveurs, l'application passe à l'échelle sur la charge.

### Expérience 2 - Passage à l'échelle sur les données
Cette expérience consite à la récupération d'une timeline en prenant en augmentant les données à récupérer.

![Graphique de fanout](fanout.png)

En analysant le fichier [csv](out/fanout.csv), il apparaît clairement que plus la quantité de personne que l'on suit augmente, plus le temps de la requête augmente. Le nombre de post a été doublé, ce qui implique un nombre de serveur plus important que l'expérience une pour les même paramêtres (50 users simultanés et 20 abonnements).

On voit ici clairement que l'application ne passe pas à l'échelle sur les données.

### Conclusion
Avec ces deux expérience, on peut voir que le modèle choisit ne passe pas à l'échelle. Il faut donc étudier un autre moyen de faire pour que l'application puisse scale.
