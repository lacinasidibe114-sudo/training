import rclpy

from rclpy.node  import Node
from msg_pkg.srv import Add


class SimpleServiceServer(Node):
    def __init__(self):
        super().__init__("simple_service_server")

        self.pub = self.create_service(Add ,"chatter" , self.callback)

     
    def callback(self  , req , res):
        self.get_logger().info(" we recieving a: %d and b: %d " % (req.a, req.b))
        res.sum = req.a + req.b
        self.get_logger().info(" we obtain sum: %d  " % res.sum)

        return res



       


def main():
    rclpy.init()
    simple_service_server = SimpleServiceServer()
    rclpy.spin(simple_service_server)
    simple_service_server.destroy_node()
    rclpy.shutdown()