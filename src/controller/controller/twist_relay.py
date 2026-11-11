#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class TwistRelayNode(Node):
    """
    Deux conversions indépendantes :

    1) Sortie twist_mux (Twist, non timestampé) -> TwistStamped
       pour le contrôleur de la base (diff_drive_controller).

    2) Sortie joystick (TwistStamped) -> Twist
       pour l'entrée "joystick" du twist_mux (use_stamped: false).
    """

    def __init__(self):
        super().__init__("twist_relay")

        # --- 1) twist_mux -> contrôleur ---
        self.controller_sub = self.create_subscription(
            Twist,
            "/diff_drive_controller/cmd_vel_unstamped",
            self.controller_twist_callback,
            10
        )
        self.controller_pub = self.create_publisher(
            TwistStamped,
            "/diff_drive_controller/cmd_vel",
            10
        )

        # --- 2) joystick -> twist_mux ---
        self.joy_sub = self.create_subscription(
            TwistStamped,
            "/input_joy/cmd_vel_stamped",
            self.joy_twist_callback,
            10
        )
        self.joy_pub = self.create_publisher(
            Twist,
            "/input_joy/cmd_vel",   # entrée attendue par joystick_relay (turbo/priorité)
            10
        )

    def controller_twist_callback(self, msg: Twist):
        twist_stamped = TwistStamped()
        twist_stamped.header.stamp = self.get_clock().now().to_msg()
        twist_stamped.twist = msg
        self.controller_pub.publish(twist_stamped)

    def joy_twist_callback(self, msg: TwistStamped):
        self.joy_pub.publish(msg.twist)


def main(args=None):
    rclpy.init(args=args)
    node = TwistRelayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()