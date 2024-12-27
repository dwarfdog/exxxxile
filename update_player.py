import subprocess
import time

def run_periodic_command(command, interval):
    """
    Exécute une commande périodiquement à un intervalle donné.

    :param command: La commande shell à exécuter.
    :param interval: Intervalle en secondes entre chaque exécution.
    """
    while True:
        try:
            print(f"Exécution de la commande : {command}")
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'exécution de la commande : {command}\n{e}")
        except Exception as e:
            print(f"Erreur inattendue : {e}")
        finally:
            print(f"Attente de {interval} secondes avant la prochaine exécution.")
            time.sleep(interval)

if __name__ == "__main__":
    # Commande à exécuter
    command = "sudo python3 manage.py update_player"

    # Intervalle en secondes
    interval = 60

    # Lancement de la commande périodique
    run_periodic_command(command, interval)
