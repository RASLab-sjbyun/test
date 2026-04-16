#!/usr/bin/env python3

import yaml
import rclpy

from rclpy.node import Node
from rclpy.action import ActionClient

from nav2_msgs.action import NavigateToPose


class WaypointNavigator(Node):

    def __init__(self):
        super().__init__('waypoint_navigator')
	# navigation 목적지로 보내기 위해 사용하는 action 통신 요청하는 측이 client가 됨 
        self.action_client = ActionClient(
            self,
            NavigateToPose,
            '/navigate_to_pose'
        )
        
	# yaml에 저장된 것을 리스트 형태로 받아옴 
        self.waypoints = self.load_yaml()
        
        # 현재가 몇번 째 지점인지를 파악  
        self.current_index = 0
        
        # goal을 action server에 보냄 
        self.send_next_goal()

    # yaml 파일을 읽어서 list로 반환해주는 함수 
    def load_yaml(self):

        with open('/home/lab/waypoint_list.yaml', 'r') as f:
            data = yaml.safe_load(f)

        return data["waypoints"]


    def send_next_goal(self):

        if self.current_index >= len(self.waypoints):

            self.get_logger().info("All goals completed")
            return

        wp = self.waypoints[self.current_index]

        goal_msg = NavigateToPose.Goal()

        goal_msg.pose.header.frame_id = "map"

        goal_msg.pose.pose.position.x = wp["x"]
        goal_msg.pose.pose.position.y = wp["y"]

        goal_msg.pose.pose.orientation.z = wp["z"]
        goal_msg.pose.pose.orientation.w = wp["w"]

        self.get_logger().info(
            f"Sending Goal {self.current_index+1}"
        )

        self.action_client.wait_for_server()
        
	# action server의 요청
        future = self.action_client.send_goal_async(goal_msg)
	# 요청에 대한 답이 오면 goal_response_callback 실행
        future.add_done_callback(self.goal_response_callback)


    def goal_response_callback(self, future):
    
	# 요청에 대한 답 확인
        goal_handle = future.result()

        if not goal_handle.accepted:

            self.get_logger().info("Goal rejected")
            return

        self.get_logger().info("Goal accepted")
        
	# 요청 수행 중 결과 기다리기
        result_future = goal_handle.get_result_async()
        
	# 수행이 완료 되면 get_result_callback 수행
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):

        self.get_logger().info("Goal completed")

        self.current_index += 1

        self.send_next_goal()


def main(args=None):

    rclpy.init(args=args)

    node = WaypointNavigator()

    rclpy.spin(node)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
