import rclpy 
from rclpy.node import Node
from std_srvs.srv import SetBool

import sys


class Server(Node):
    def __init__(self):
        super().__init__("server")


        self.client = self.create_client( SetBool, "marche")

        while not self.client.wait_for_service(timeout_sec=0.1):
            self.get_logger().info(" le server n'estv pas dispo ")


        self.req = SetBool.Request()


    def send_request(self  , active):

        self.req.data = active

        self.future  = self.client.call_async(self.req)

        rclpy.spin_until_future_complete(self , self.future)

        return self.future.result()



def main():
    rclpy.init()
    server = Server()
    if len(sys.argv) !=2:
        print('erreur ecris Tue or False')
    else:
        action = sys.argv[1].format == 'true'
        server.send_request(action )

        server.destroy_service()
        rclpy.shutdown()

if __name__ =='__main__' :
    main()