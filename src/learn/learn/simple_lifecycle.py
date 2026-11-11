import rclpy
from rclpy.lifecycle import Node , State , TransitionCallbackReturn
from std_msgs.msg import String

import time 

class Simplepub(Node):
    def __init__(self  , node_name  , **Kwargs) :
        super().__init__(node_name  ,**Kwargs )

    def on_configure(self, state : State) -> TransitionCallbackReturn:
        self.sub = self.create_subscription(String , "chatter" , self.callback , 10)
        self.get_logger().info('lifecycle node on configure called')
        return  TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state : State) -> TransitionCallbackReturn:
        self.destroy_subscription(self.sub)
        self.get_logger().info('lifecycle node on_shutdown called')
        return  TransitionCallbackReturn.SUCCESS


    def on_cleanup(self, state : State) -> TransitionCallbackReturn:
        self.destroy_subscription(self.sub)
        self.get_logger().info('lifecycle node on_cleanup called')
        return  TransitionCallbackReturn.SUCCESS

    def on_activate(self, state : State) -> TransitionCallbackReturn:
        self.get_logger().info('lifecycle node on_activate called')
        time.sleep(2)
        return  super().on_activate(state)


    def on_deactivate(self, state : State) -> TransitionCallbackReturn:
        self.get_logger().info('lifecycle node on_deactivate called')
        return  super().on_deactivate(state)


    def callback(self  , msg):

        currente_state = self.state_machine.currente_state

        if currente_state[1]== "active":
            self.get_logger().info(" I head : " % msg.data)


        msg = String()
        msg.data = "I ros2 "



def main():
    rclpy.init()
    executor = rclpy.executors.SimpleThreadExecutor()

    simple_pub = Simplepub( "simple_lifecycle")
    executor.add_node( simple_pub)
    rclpy.spin(simple_pub)
    simple_pub.destroy_node()
    rclpy.shutdown


if __name__ == '__main__':
    main()

