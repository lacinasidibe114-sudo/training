#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from sensor_msgs.msg import LaserScan
import math
from enum import Enum

from twist_mux_msgs.action import JoyTurbo
from rclpy.action import ActionClient


class State(Enum):
    FREE = 0
    WARNING = 1
    DANGER = 2


class SafetyStop(Node):
    def __init__(self):
        super().__init__("safety_stop")

        # --- Paramètres ---
        self.declare_parameter("danger_distance", 0.5)
        self.declare_parameter("warning_distance", 0.8)
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("safety_stop_topic", "safety_stop")

        self.danger_distance = (
            self.get_parameter("danger_distance")
            .get_parameter_value().double_value
        )
        self.warning_distance = (
            self.get_parameter("warning_distance")
            .get_parameter_value().double_value
        )
        self.scan_topic = (
            self.get_parameter("scan_topic")
            .get_parameter_value().string_value
        )
        self.safety_stop_topic = (
            self.get_parameter("safety_stop_topic")
            .get_parameter_value().string_value
        )

        # --- Sub / Pub ---
        self.laser_sub = self.create_subscription(
            LaserScan, self.scan_topic, self.laser_callback, 10
        )
        self.safety_stop_pub = self.create_publisher(
            Bool, self.safety_stop_topic, 10
        )

        # --- Action clients (NON bloquants) ---
        self.decrease = ActionClient(self, JoyTurbo, "/joy_decrease")
        self.increase = ActionClient(self, JoyTurbo, "/joy_increase")

        # Vérification périodique non bloquante
        self.create_timer(2.0, self._check_action_servers)

        # --- État interne ---
        self.state = State.FREE
        self.prev_state = State.FREE

        # On publie un état initial "pas de stop"
        self._publish_safety_stop(False)

    # ------------------------------------------------------------------
    def _check_action_servers(self):
        """Vérifie l'état des serveurs d'action sans bloquer le nœud."""
        if not self.decrease.server_is_ready():
            self.get_logger().info(
                "decrease turbo action server not available"
            )
        if not self.increase.server_is_ready():
            self.get_logger().info(
                "increase turbo action server not available"
            )

    # ------------------------------------------------------------------
    def _send_goal(self, client: ActionClient, name: str):
        """Envoie un goal seulement si le serveur est prêt."""
        if not client.server_is_ready():
            self.get_logger().warn(
                f"{name} action server not available, skip goal"
            )
            return

        goal = JoyTurbo.Goal()
        future = client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: self._on_goal_response(f, name)
        )

    def _on_goal_response(self, future, name: str):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn(f"{name} goal rejected")
        else:
            self.get_logger().info(f"{name} goal accepted")

    # ------------------------------------------------------------------
    def _publish_safety_stop(self, value: bool):
        msg = Bool()
        msg.data = value
        self.safety_stop_pub.publish(msg)

    # ------------------------------------------------------------------
    def laser_callback(self, msg: LaserScan):
        # 1) Déterminer le nouvel état
        new_state = State.FREE
        for distance in msg.ranges:
            if math.isinf(distance) or math.isnan(distance):
                continue
            if distance <= self.warning_distance:
                new_state = State.WARNING
                if distance <= self.danger_distance:
                    new_state = State.DANGER
                    break

        # 2) Toujours construire le message AVANT le if
        is_safety_stop = Bool()
        is_safety_stop.data = (new_state == State.DANGER)

        # 3) Réagir au changement d'état
        if new_state != self.state:
            if new_state == State.DANGER:
                self.get_logger().warn("DANGER detected -> safety stop")
            elif new_state == State.WARNING:
                # On entre en warning : on réduit le turbo
                self.get_logger().info("WARNING zone -> decrease turbo")
                self._send_goal(self.decrease, "decrease")
            elif new_state == State.FREE:
                # On revient libre : on réaugmente le turbo
                self.get_logger().info("FREE zone -> increase turbo")
                self._send_goal(self.increase, "increase")

            self.prev_state = self.state
            self.state = new_state

        # 4) Publier à chaque scan
        self.safety_stop_pub.publish(is_safety_stop)


# ----------------------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    safety_stop = SafetyStop()
    try:
        rclpy.spin(safety_stop)
    except KeyboardInterrupt:
        pass
    finally:
        safety_stop.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()