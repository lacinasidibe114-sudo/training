import rclpy
from rclpy.node import Node 
from std_msgs.msg import String
import serial



class Transmitter(Node):
    def __init__(self):
        super().__init__("transmitter")


        self.declare_parameter("port" , "/dev/ttyUSB0")
        self.declare_parameter("baudrate" , 115200)

        self.port = self.get_parameter("port").value
        self.baudrate = self.get_parameter("baudrate").value

        self.sub = self.create_subscription(String , "transmitter" , 10 , self.callback())
        self.arduino = serial.Serial(self.port , self.baudrate , timeout=0.1)






    def callback(self , msg :String):
        self.get_logger().info(" new message from arduino %s" % self.arduino.name)
        self.arduino.write(msg.data.encode("utf-8"))










def main():
    rclpy.init()
    transmitter = Transmitter()
    rclpy.spin(transmitter)
    transmitter.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()