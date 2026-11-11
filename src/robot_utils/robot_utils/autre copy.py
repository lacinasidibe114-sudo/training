#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from sensor_msgs.msg import LaserScan
import math
from enum import Enum

from twist_mux_msgs.action import  JoyTurbo
from rclpy.action import ActionClient


class State(Enum):
    FREE = 0
    WARNING = 1
    DANGER = 2


class SafetyStop(Node):
    def __init__(self):
        super().__init__("safety_stop")

        self.declare_parameter("danger_distance", 0.5)
        self.declare_parameter("warning_distance", 0.8)

        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("safety_stop_topic", "safety_stop")

        self.danger_distance = self.get_parameter("danger_distance").get_parameter_value().double_value
        self.warning_distance = self.get_parameter("warning_distance").get_parameter_value().double_value

        self.scan_topic = self.get_parameter("scan_topic").get_parameter_value().string_value
        self.safety_stop_topic = self.get_parameter("safety_stop_topic").get_parameter_value().string_value

        self.laser_sub = self.create_subscription(LaserScan, self.scan_topic, self.laser_callback, 10)
        self.safety_stop_pub = self.create_publisher(Bool, self.safety_stop_topic, 10)

        self.decrease = ActionClient(self , JoyTurbo , "/joy_decrease" )
        self.increase = ActionClient(self , JoyTurbo , "/joy_increase" )


        while not self.decrease.wait_for_server(timeout_sec=1.0) and rclpy.ok():
            self.get_logger().info("decrease the trubo is not available ")

        while not self.increase.wait_for_server(timeout_sec=1.0) and rclpy.ok():
            self.get_logger().info("increase the trubo is s not available")

        self.state = State.FREE
        self.prev_state = State.FREE

    def laser_callback(self, msg: LaserScan):
        self.state = State.FREE

        for distance in msg.ranges:
            if not math.isinf(distance) and not math.isnan(distance) and  distance <= self.warning_distance:
                self.state = State.WARNING
                if distance <= self.danger_distance:
                    self.state = State.DANGER
                    self.get_logger().warn("danger detecter ")
                    break


        if self.state != self.prev_state:
            is_safety_stop = Bool()

            if self.prev_state == State.WARNING:
                is_safety_stop.data = False
                self.decrease.send_goal_async(JoyTurbo.Goal())
                
            elif self.state == State.DANGER:
                is_safety_stop.data = True
            elif self.state == State.FREE:
                is_safety_stop.data = False
                self.increase.send_goal_async(JoyTurbo.Goal())

            self.prev_state = self.state
        self.safety_stop_pub.publish(is_safety_stop)


def main():
    rclpy.init()
    safety_stop = SafetyStop()
    rclpy.spin(safety_stop)
    safety_stop.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()