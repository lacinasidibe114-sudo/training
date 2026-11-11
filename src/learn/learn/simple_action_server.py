import rclpy

from rclpy.node  import Node
from rclpy.action import ActionServer
import time

from msg_pkg.action import Fibonacci

class SimpleActionServer(Node):
    def __init__(self):
        super().__init__("simple_action_server")


        self.action =  ActionServer( self , Fibonacci , 'fibonacci' , self.callback )
        self.get_logger().info("the actiion  server starting  " )

    def callback (self  , goal_handle):
        self.get_logger().info(" recieve goal request with goal_data %d " % goal_handle.request.goal_data )

        feedback_msg= Fibonacci.Feedback()
        feedback_msg.partial_sequence = [0 , 1]

        for i in range(1, goal_handle.request.goal_data):
            feedback_msg.partial_sequence.append(
                feedback_msg.partial_sequence[i] + feedback_msg.partial_sequence[i-1])
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.partial_sequence))
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1)

        goal_handle.succeed()

        resultat = Fibonacci.Result()
        resultat.sequence=  feedback_msg.partial_sequence
        return resultat



def main():
    rclpy.init()
    simple_action_server = SimpleActionServer()
    rclpy.spin(simple_action_server)

if __name__ == '__main__':
    main()