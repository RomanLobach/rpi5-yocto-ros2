import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class CounterSubscriber(Node):
    """Logs every value received on /counter."""

    def __init__(self):
        super().__init__('counter_subscriber')
        self._sub = self.create_subscription(Int32, 'counter', self._on_msg, 10)

    def _on_msg(self, msg):
        self.get_logger().info(f'Received: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = CounterSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
