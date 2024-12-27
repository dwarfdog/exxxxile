import subprocess

def run_server(command):
    """
    Lance le serveur en exécutant une commande shell.

    :param command: La commande shell à exécuter.
    """
    try:
        print(f"Lancement du serveur avec la commande : {command}")
        # Exécution de la commande, le processus reste actif
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement du serveur : {command}\n{e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    # Commande pour démarrer le serveur
    command = "sudo python3 manage.py runserver 0.0.0.0:8000"

    # Lancement du serveur
    run_server(command)
