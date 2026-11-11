import rclpy

from rclpy.node  import Node
from std_msgs.msg import String 




class SimplePublisher(Node):
    def __init__(self):
        super().__init__("simple_publisher")

        self.pub = self.create_publisher(String , "chatter" , 10)

        self.counter = 0
        self.frequence = 1.0 
        self.get_logger().info( " publier at %d Hz" % self.frequence)
        self.timer = self.create_timer(self.frequence , self.callback)


    def callback(self):
        msg = String()
        msg.data = "hello ros2 %d" % self.counter
        self.pub.publish(msg)
        self.counter += 1 


def main():
    rclpy.init()
    simple_publisher = SimplePublisher()
    rclpy.spin(simple_publisher)
    simple_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()