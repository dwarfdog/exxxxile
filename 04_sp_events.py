import subprocess

def run_sp_events(command):
    """
    Lance sp_events en exécutant une commande shell.

    :param command: La commande shell à exécuter.
    """
    try:
        print(f"Lancement de sp_events avec la commande : {command}")
        # Exécution de la commande, le processus reste actif
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement de sp_events : {command}\n{e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    # Commande pour démarrer sp_events
    command = "sudo python3 manage.py sp_events"

    # Lancement de sp_events
    run_sp_events(command)
