import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
from std_srvs.srv import SetBool

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')

        self.srv = self.create_service(SetBool, '~/toggle_detection', self.toggle_detection_callback)
        self.detection_enabled = False

        self.model = YOLO('yolov8n.pt')

        self.pub = self.create_publisher(
            Image, '/rgb/image_annotated', qos_profile_sensor_data)

        self.bridge = CvBridge()
        self.cap = cv2.VideoCapture('/dev/video2', cv2.CAP_V4L2)

        if not self.cap.isOpened():
            self.get_logger().error("Impossible d'ouvrir la caméra")
            return
        
    

        self.timer = self.create_timer(0.033, self.timer_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        if self.detection_enabled:
            results = self.model(frame, classes=[0], device=0,  verbose=False)
            annotated = results[0].plot()
            

        else:
            annotated = frame   

        msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'

        self.pub.publish(msg)
    
        

    def toggle_detection_callback(self, request, response):
        self.detection_enabled = request.data
        response.success = True
        response.message = f"Detection {'enabled' if self.detection_enabled else 'disabled'}"
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()