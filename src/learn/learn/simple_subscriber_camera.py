import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
#from ultralytics import YOLO

class WebcamSubscriber(Node):
    def __init__(self):
        super().__init__('webcam_subscriber')
        self.br = CvBridge()
  #      self.model = YOLO("yolov8n.pt")
        self.latest_image = None

        # QoS adapté pour une caméra
        from rclpy.qos import QoSProfile, QoSReliabilityPolicy
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)

        self.subscription = self.create_subscription(
            Image, 'rgb', self.image_callback, qos
        )

        self.timer = self.create_timer(0.1, self.process_image)

        self.get_logger().info("Subscriber démarré")

    def image_callback(self, msg):
        self.latest_image = msg  

    def process_image(self):
        if self.latest_image is None:
            return
        try:
            cv_image = self.br.imgmsg_to_cv2(self.latest_image, 'bgr8')
            
            results = self.model(cv_image)[0]  # premier (et unique) résultat
            
            annotated = results.plot()

            PERSON_CLASS = 0

            if results.boxes is not None:
                for box in results.boxes:
                    # Récupérer la classe et la confiance
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if cls == PERSON_CLASS:
                        # Coordonnées de la boîte [x1, y1, x2, y2]
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        
                        # Centre de la boîte
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        
                        # Dessiner un cercle rouge sur l'image annotée
                        cv2.circle(annotated, (cx, cy), radius=6, color=(0, 0, 255), thickness=-1)
                        
                        # Optionnel : afficher les coordonnées dans la console
                        self.get_logger().debug(f"Personne au centre ({cx}, {cy}) conf={conf:.2f}")
                        # Si vous voulez voir en console, passez le niveau de log à DEBUG
                        # ou utilisez print() temporairement.

            cv2.imshow("YOLO Detection + Centre", annotated)
            cv2.waitKey(1)

        except Exception as e:
            self.get_logger().error(f"Erreur traitement : {e}")

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = WebcamSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()