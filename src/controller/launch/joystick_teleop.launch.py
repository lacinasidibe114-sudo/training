import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    controller_pkg = get_package_share_directory('controller')

    joy_teleop = Node(
        package="joy_teleop",
        executable="joy_teleop",
        parameters=[
            os.path.join(controller_pkg, "config", "joy_teleop.yaml"),
        ],
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joystick",
        parameters=[
            os.path.join(controller_pkg, "config", "joy_config.yaml"),
        ],
    )

    twist_mux_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("twist_mux"),
                "launch",
                "twist_mux_launch.py",
            )
        ),
        launch_arguments={
            "cmd_vel_out": "diff_drive_controller/cmd_vel_unstamped",
            "config_locks": os.path.join(controller_pkg, "config", "twist_mux_locks.yaml"),
            "config_topics": os.path.join(controller_pkg, "config", "twist_mux_topics.yaml"),
            "config_joy": os.path.join(controller_pkg, "config", "twist_mux_joy.yaml"),
        }.items(),
    )

    twist_relay_node = Node(
        package="controller",
        executable="twist_relay",
        name="twist_relay",
    )

    return LaunchDescription(
        [
            joy_teleop,
            joy_node,
            twist_mux_launch,
            twist_relay_node,
        ]
    )