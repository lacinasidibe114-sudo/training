import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class WebcamPublisher(Node):
    def __init__(self):
        super().__init__('webcam_publisher')

        self.publisher_ = self.create_publisher(Image, 'rgb', 10)
        timer_period = 0.1
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.br = CvBridge()
        self.cap = cv2.VideoCapture(0)
       

        self.get_logger().info("Publisher webcam démarré")

    def timer_callback(self):
        ret, frame = self.cap.read()

        if ret:
            ros_image = self.br.cv2_to_imgmsg(frame, encoding="bgr8")
            self.publisher_.publish(ros_image)
            self.get_logger().debug('Image publiée')
        
        else:
            self.get_logger().warn("Impossible de lire la webcam")

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    webcam_publisher = WebcamPublisher()
    rclpy.spin(webcam_publisher)
    webcam_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()