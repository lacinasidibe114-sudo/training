import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import ComputePathToPose, FollowPath
from geometry_msgs.msg import PoseStamped

class NavTester(Node):
    def __init__(self):
        super().__init__('nav_tester')
        self.planner_client  = ActionClient(self, ComputePathToPose, 'compute_path_to_pose')
        self.controller_client = ActionClient(self, FollowPath, 'follow_path')

    def run(self):
        # 1. Calculer le chemin
        self.planner_client.wait_for_server()
        goal = ComputePathToPose.Goal()
        goal.goal.header.frame_id = 'map'
        goal.goal.pose.position.x = 1.0
        goal.goal.pose.position.y = 0.5
        goal.goal.pose.orientation.w = 1.0
        goal.planner_id = 'GridBased'
        goal.use_start = False
        self.get_logger().info('Calcul du chemin...')
        path_result = self.planner_client.send_goal(goal).result.path

        # 2. Envoyer au controller
        self.controller_client.wait_for_server()
        follow = FollowPath.Goal()
        follow.path = path_result
        follow.controller_id = 'FollowPath'
        follow.goal_checker_id = 'general_goal_checker'
        self.get_logger().info('Envoi du chemin au controller...')
        self.controller_client.send_goal_async(follow)

def main():
    rclpy.init()
    node = NavTester()
    node.run()
    rclpy.spin(node)

if __name__ == '__main__':
    main()