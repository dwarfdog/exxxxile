import os
import time
import subprocess

# Commandes pour chaque script directement (fusion des fichiers existants)
commands = [
    "sudo python3 manage.py runserver 0.0.0.0:8000",  # Lancement du serveur
    "sudo python3 manage.py sp_process_all",          # Process all
    "sudo python3 manage.py sp_events",              # Events
    "sudo python3 manage.py sp_battle"               # Battle
]

# Commande pour le script périodique
periodic_command = "sudo python3 manage.py update_player"
periodic_interval = 60  # Intervalle en secondes

def launch_scripts():
    for command in commands:
        try:
            print(f"Lancement de : {command}")
            if os.name != 'nt':  # Unix/Linux/MacOS
                subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{command}; exec bash"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            else:
                raise EnvironmentError("Ce script est conçu pour être utilisé sous Linux avec GNOME Terminal.")

            time.sleep(2)  # Attendre 2 secondes avant de lancer le prochain script
        except Exception as e:
            print(f"Erreur lors du lancement de la commande : {command}\n{e}")

def launch_periodic_script():
    try:
        while True:
            print(f"Exécution périodique de : {periodic_command}")
            if os.name != 'nt':  # Unix/Linux/MacOS
                subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{periodic_command}; exec bash"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            else:
                raise EnvironmentError("Ce script est conçu pour être utilisé sous Linux avec GNOME Terminal.")

            time.sleep(periodic_interval)
    except KeyboardInterrupt:
        print("Arrêt de l'exécution périodique.")

if __name__ == "__main__":
    # Vérification des privilèges administrateurs (Linux uniquement)
    if os.name != 'nt' and os.geteuid() != 0:
        print("Ce script doit être exécuté avec les droits administrateur.")
        exit(1)

    # Lancer les scripts exécutés une seule fois
    launch_scripts()

    # Lancer le script périodique
    launch_periodic_script()
