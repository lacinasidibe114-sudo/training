import rclpy 
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


class Cmd_control(Node):
    def __init__(self):
        super().__init__("test")

        self.pub = self.create_publisher(Twist , "/cmd_vel" , 10)
        self.safety_stop = self.create_subscription(Bool, "safety_stop" , self.safety_callback , 10)

        self.timer = self.create_timer(0.1 , self.callback)


        self.move = False

    def callback(self):
        msg = Twist()

        if not self.move  :
            msg.linear.x = 2.5 
            msg.angular.z = 0.0
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.pub.publish(msg)

    def safety_callback(self , msgs):

        self.move = msgs.data 


        
    
    


def main():
    rclpy.init()
    test = Cmd_control()
    rclpy.spin(test)
    test.destroy_node()
    rclpy.shutdown()
            
