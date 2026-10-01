# Procédure de connexion VPN

## Quand utiliser le VPN

Le VPN permet d'accéder aux applications internes depuis l'extérieur de l'entreprise. Le client utilisé par l'entreprise s'appelle GlobalProtect.

## Première connexion

Ouvrir GlobalProtect puis saisir le portail `vpn.entreprise.test`. Utiliser l'adresse professionnelle comme identifiant et le mot de passe habituel. Valider ensuite le code MFA reçu sur le téléphone professionnel.

## Erreur « portail inaccessible »

Vérifier d'abord que la connexion Internet fonctionne en ouvrant un site public. Contrôler ensuite que le portail saisi est exactement `vpn.entreprise.test`. Ne pas ajouter `https://` dans le champ du portail.

## Mot de passe accepté mais connexion refusée

Fermer complètement GlobalProtect puis le rouvrir. Vérifier que la demande MFA n'attend pas une validation. Après trois refus consécutifs, patienter dix minutes avant un nouvel essai.

## Escalade

Si le problème persiste, créer un ticket dans la catégorie `Réseau > VPN`. Joindre l'heure de l'essai et une capture du message d'erreur, sans jamais transmettre le mot de passe ni le code MFA.
