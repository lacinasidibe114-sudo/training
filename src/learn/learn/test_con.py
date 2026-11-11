import rclpy 
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool


class Cmd_control(Node):
    def __init__(self):
        super().__init__("cmd")

        self.odom = self.create_subscription(Odometry , "/odom" , self.odom_data  , 10)
        self.pub = self.create_publisher(Twist , "/cmd_vel" , 10)
        self.ser  = self.create_service(SetBool , "marche" , self.servecall)


        self.timer = self.create_timer(0.1 , self.callback)
        self.move = True
        self.marche = False


    def callback(self):
        msg = Twist()

        if self.move and self.marche :
            msg.linear.x = 2.5 
            msg.angular.z = 0.0
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.pub.publish(msg)
        
    
    

    def odom_data(self , msg):

        pos = msg.pose.pose.position 
        orientatation = msg.pose.pose.orientation 

        if self.move and pos.x >= 5.0 :
            self.move = False
            mm =Twist()
            mm.linear.x = 0.0
            mm.angular.z = 0.0 
            self.pub.publish(mm)

    def servecall(self,req , res): 

        self.marche = req.data

        if self.marche:
            self.move = True
            res.success = True
            res.message = "activate"
            self.get_logger().info(res.message)

        else:

            res.success = True
            res.message = "deactivate"
            self.get_logger().info(res.message)

        return res

def main():
    rclpy.init()
    cmd = Cmd_control()
    rclpy.spin(cmd)
    cmd.destroy_node()
    rclpy.shutdown()
            
