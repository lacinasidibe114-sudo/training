import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class SimpleSubscriber(Node):
    def __init__(self):
        super().__init__("simple_subscriber")

        # Souscription au topic "chatter" (messages String)
        self.sub_chatter = self.create_subscription(
            String,
            "chatter",
            self.chatter_callback,
            10
        )

        # Souscription au topic "cmd_vel" (messages Twist)
        self.sub_cmd_vel = self.create_subscription(
            Twist,
            "cmd_vel",
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info("Subscriber node started, waiting for messages...")

    def chatter_callback(self, msg):
        self.get_logger().info(f"Received String: {msg.data}")

    def cmd_vel_callback(self, msg):
        self.get_logger().info(
            f"Received Twist: linear.x = {msg.linear.x:.2f}, angular.z = {msg.angular.z:.2f}"
        )

def main():
    rclpy.init()
    subscriber = SimpleSubscriber()
    rclpy.spin(subscriber)
    subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()