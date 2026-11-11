import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from std_msgs.msg import Float64  # <--- NOUVEAU : Import du message de vitesse
import serial
import time

class PidTunerBridge(Node):
    def __init__(self):
        super().__init__('pid_tuner_bridge')

        # Configuration du port série
        self.serial_port = '/dev/ttyACM0'  # Ton Arduino
        self.baud_rate = 115200
        self.ser = None

        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)
            self.get_logger().info(f"Connexion série établie sur {self.serial_port}")
        except serial.SerialException as e:
            self.get_logger().error(f"Impossible d'ouvrir le port série : {e}")
            return

        # 1. PARAMÈTRES (Pour le Tuning P, I, D)
        self.declare_parameter('kp', 12.8, ParameterDescriptor(description='Kp Proportionnel'))
        self.declare_parameter('ki', 8.3, ParameterDescriptor(description='Ki Intégral'))
        self.declare_parameter('kd', 0.1, ParameterDescriptor(description='Kd Dérivé'))
        self.add_on_set_parameters_callback(self.parameter_callback)

        # 2. TOPIC DE VITESSE (Pour faire tourner le moteur)
        # Il écoute sur le topic standard '/cmd_vel'
        self.create_subscription(Float64, 'cmd_vel', self.cmd_vel_callback, 10)
        
        self.get_logger().info("Bridge PID prêt.")
        self.get_logger().info("1. Utilise 'rqt_reconfigure' pour le tuning.")
        self.get_logger().info("2. Utilise le topic '/cmd_vel' pour la vitesse.")

    def cmd_vel_callback(self, msg):
        """
        Reçoit la commande de vitesse (ex: 30.0 ou -15.0) et l'envoie à l'Arduino.
        """
        speed = msg.data
        
        # Si la vitesse est positive -> Marche Avant ('p')
        if speed >= 0.0:
            self.send_to_arduino(f"lp{speed:.3f},")
        # Si la vitesse est négative -> Marche Arrière ('n')
        else:
            self.send_to_arduino(f"ln{abs(speed):.3f},")

    def parameter_callback(self, params):
        """Appelé automatiquement dès qu'on bouge un curseur dans rqt_reconfigure."""
        if self.ser is None or not self.ser.is_open:
            self.get_logger().warn("Port série non disponible, commande ignorée.")
            return SetParametersResult(successful=False, reason="Port série non ouvert")

        for param in params:
            if param.name == 'kp':
                self.send_to_arduino(f"tp{param.value:.3f},")
            elif param.name == 'ki':
                self.send_to_arduino(f"ti{param.value:.3f},")
            elif param.name == 'kd':
                self.send_to_arduino(f"td{param.value:.3f},")

        return SetParametersResult(successful=True)

    def send_to_arduino(self, command: str):
        """Envoie la commande texte à l'Arduino."""
        if self.ser is not None and self.ser.is_open:
            self.ser.write(command.encode('utf-8'))
            self.get_logger().info(f"Envoyé à Arduino : {command.strip()}")

    def destroy_node(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = PidTunerBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()