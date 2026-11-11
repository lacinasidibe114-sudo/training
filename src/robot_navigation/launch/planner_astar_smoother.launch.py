from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    planner_params      = '/home/sidibe/training/src/robot_navigation/config/planner_sever_complet.yaml'
    controller_params   = '/home/sidibe/training/src/robot_navigation/config/controller_server.yaml'
    bt_navigator_params = '/home/sidibe/training/src/robot_navigation/config/bt_navigator.yaml'
    behavior_params     = '/home/sidibe/training/src/robot_navigation/config/behavior_server.yaml'

    # ---- planner_server (contient aussi global_costmap) ----
    planner = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[planner_params],
    )

    # ---- smoother_server ----
    smoother = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[planner_params],
    )

    # ---- controller_server (contient aussi local_costmap) ----
    controller = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[controller_params],
        #remappings=[('cmd_vel', 'cmd_vel_nav')],
    )

    # ---- bt_navigator ----
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[bt_navigator_params],
    )

    # ---- behavior_server ----
    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',          # ← le nom réel du nœud
        output='screen',
        parameters=[behavior_params],
    )

    # ---- lifecycle_manager ----
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': [
                'planner_server',
                'smoother_server',
                'controller_server',
                'bt_navigator',
                'behavior_server',       # ← CORRIGÉ
            ],
            'bond_timeout': 10.0,
        }],
    )

    # ---- serveurs d'abord, lifecycle_manager ensuite ----
    delayed_servers = TimerAction(
        period=3.0,
        actions=[planner, smoother, controller, bt_navigator, behavior_server],
    )
    delayed_lifecycle = TimerAction(
        period=5.0,
        actions=[lifecycle_manager],
    )

    return LaunchDescription([delayed_servers, delayed_lifecycle])