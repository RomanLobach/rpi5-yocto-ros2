from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='counter_demo', executable='counter_publisher', output='screen'),
        Node(package='counter_demo', executable='counter_subscriber', output='screen'),
    ])
