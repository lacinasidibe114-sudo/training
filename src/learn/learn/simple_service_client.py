import rclpy
from rclpy.node import Node
from msg_pkg.srv import Add

class SimpleServiceClient(Node):
    def __init__(self):
        super().__init__("simple_service_client")

        # ÉTAPE 1 : On marche jusqu'au restaurant (Créer le client)
        # On dit : "Je veux parler au service 'chatter' qui utilise le menu 'Add'"
        self.cli = self.create_client(Add, "chatter")

        # ÉTAPE 2 : On vérifie si le resto est ouvert (Attendre le service)
        # Si le cuisinier n'est pas là, on attend 1 seconde et on recommence.
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Le serveur n'est pas encore prêt, j'attends...")

        # ÉTAPE 3 : On prend un ticket de commande vide (Créer la requête)
        self.req = Add.Request()

    def send_request(self, a, b):
        # On écrit notre commande sur le ticket
        self.req.a = a
        self.req.b = b

        # ÉTAPE 4 : On donne le ticket au serveur et on attend le plat !
        # call_async = "Voici ma commande, préviens-moi quand c'est prêt"
        self.future = self.cli.call_async(self.req)

        # spin_until_future_complete = "Je reste assis à la table (je spin) 
        # jusqu'à ce que le plat arrive (future complete)"
        rclpy.spin_until_future_complete(self, self.future)

        # ÉTAPE 5 : On mange le plat ! (Récupérer la réponse)
        return self.future.result()

def main():
    rclpy.init()
    
    # On crée le client
    client_node = SimpleServiceClient()
    
    # On lui demande d'additionner 5 et 7
    client_node.get_logger().info("J'envoie la commande 5 + 7...")
    result = client_node.send_request(5, 7)
    
    # On affiche le résultat
    client_node.get_logger().info(f"Le serveur m'a répondu : {result.sum}")
    
    # On rentre à la maison
    client_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

    
