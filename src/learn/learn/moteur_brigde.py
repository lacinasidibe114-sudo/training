import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from std_msgs.msg import Float64
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
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0.1)
            # On vide le buffer au cas où il y aurait d'anciens messages
            self.ser.reset_input_buffer()
            time.sleep(2)
            self.get_logger().info(f"Connexion série établie sur {self.serial_port}")
        except serial.SerialException as e:
            self.get_logger().error(f"Impossible d'ouvrir le port série : {e}")
            return

        # 1. PARAMÈTRES (Pour le Tuning P, I, D via rqt_reconfigure)
        self.declare_parameter('kp', 12.8, ParameterDescriptor(description='Kp Proportionnel'))
        self.declare_parameter('ki', 8.3, ParameterDescriptor(description='Ki Intégral'))
        self.declare_parameter('kd', 0.1, ParameterDescriptor(description='Kd Dérivé'))
        self.add_on_set_parameters_callback(self.parameter_callback)

        # 2. TOPIC DE VITESSE (Pour faire tourner le moteur via rqt_publisher)
        self.create_subscription(Float64, 'cmd_vel', self.cmd_vel_callback, 10)

        # 3. NOUVEAU : PUBLISHERS POUR LES GRAPHIQUES (rqt_plot / PlotJuggler)
        # C'est ça qui va remplir tes graphiques !
        self.meas_pub = self.create_publisher(Float64, '/wheel_speed', 10)          # Ce que l'encodeur lit
        self.setpoint_pub = self.create_publisher(Float64, '/wheel_setpoint', 10)   # Ce que tu demandes

        # 4. NOUVEAU : TIMER pour lire l'Arduino en permanence (toutes les 20ms)
        self.read_timer = self.create_timer(0.02, self.read_from_arduino)

        self.get_logger().info("Bridge PID prêt.")
        self.get_logger().info("Topics créés : /wheel_speed et /wheel_setpoint")

    def read_from_arduino(self):
        """Lit les réponses de l'Arduino et les publie dans ROS 2."""
        if self.ser is not None and self.ser.in_waiting > 0:
            try:
                # On lit une ligne complète (jusqu'au '\n')
                line = self.ser.readline().decode('utf-8').strip()
                
                # L'Arduino envoie : "lp20.5," ou "ln15.3,"
                if line.startswith('l') and ',' in line:
                    sign_char = line[1]       # 'p' (positif) ou 'n' (négatif)
                    speed_str = line[2:-1]    # On enlève le 'l', le 'p/n' et la virgule
                    
                    meas_speed = float(speed_str)
                    if sign_char == 'n':
                        meas_speed = -meas_speed
                    
                    # On publie la mesure dans ROS 2 !
                    msg = Float64()
                    msg.data = meas_speed
                    self.meas_pub.publish(msg)
                    
            except Exception as e:
                pass # On ignore les erreurs de parsing silencieusement

    def cmd_vel_callback(self, msg):
        """Reçoit la commande de vitesse et l'envoie à l'Arduino."""
        speed = msg.data
        
        # NOUVEAU : On publie AUSSI la consigne pour pouvoir la comparer sur le graphique
        setpoint_msg = Float64()
        setpoint_msg.data = speed
        self.setpoint_pub.publish(setpoint_msg)
        
        # Envoi à l'Arduino
        if speed >= 0.0:
            self.send_to_arduino(f"lp{speed:.3f},")
        else:
            self.send_to_arduino(f"ln{abs(speed):.3f},")

    def parameter_callback(self, params):
        """Appelé automatiquement dès qu'on bouge un curseur dans rqt_reconfigure."""
        if self.ser is None or not self.ser.is_open:
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