import os
import time
import subprocess

# Définir les commandes pour chaque script à lancer une seule fois
single_run_commands = [
    "sudo python3 manage.py runserver 0.0.0.0:8000",
    "sudo python3 manage.py sp_process_all",
    "sudo python3 manage.py sp_events",
    "sudo python3 manage.py sp_battle"
]

# Commande pour le script à exécuter périodiquement
periodic_command = "sudo python3 manage.py update_player"
periodic_interval = 60  # Intervalle en secondes

def launch_single_run_scripts():
    for command in single_run_commands:
        try:
            print(f"Lancement de : {command}")
            if os.name == 'nt':  # Windows
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", command], shell=True)
            else:  # Unix/Linux/MacOS
                subprocess.Popen(["x-terminal-emulator", "-e", command], start_new_session=True)

            time.sleep(2)  # Attendre 2 secondes avant de lancer le prochain script
        except Exception as e:
            print(f"Erreur lors du lancement de la commande : {command}\n{e}")

def launch_periodic_script():
    try:
        while True:
            print(f"Exécution périodique de : {periodic_command}")
            if os.name == 'nt':  # Windows
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", periodic_command], shell=True)
            else:  # Unix/Linux/MacOS
                subprocess.Popen(["x-terminal-emulator", "-e", periodic_command], start_new_session=True)

            time.sleep(periodic_interval)
    except KeyboardInterrupt:
        print("Arrêt de l'exécution périodique.")

if __name__ == "__main__":
    # Vérification des privilèges administrateurs (Linux uniquement)
    if os.name != 'nt' and os.geteuid() != 0:
        print("Ce script doit être exécuté avec les droits administrateur.")
        exit(1)

    # Lancer les scripts exécutés une seule fois
    launch_single_run_scripts()

    # Lancer le script périodique
    launch_periodic_script()
