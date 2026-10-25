import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from std_srvs.srv import SetBool


class CounterPublisher(Node):
    """Publishes an incrementing counter to /counter.

    The counter can be started/stopped with the /counter/toggle service
    (std_srvs/SetBool: data=true -> start, data=false -> stop).
    """

    def __init__(self):
        super().__init__('counter_publisher')
        self.declare_parameter('period', 1.0)
        self.declare_parameter('autostart', True)

        self._count = 0
        self._running = self.get_parameter('autostart').value

        self._pub = self.create_publisher(Int32, 'counter', 10)
        self._srv = self.create_service(SetBool, 'counter/toggle', self._on_toggle)
        self._timer = self.create_timer(self.get_parameter('period').value, self._on_timer)

        self.get_logger().info(
            f'Counter {"running" if self._running else "stopped"}; '
            'use service /counter/toggle to start/stop')

    def _on_timer(self):
        if not self._running:
            return
        self._count += 1
        msg = Int32()
        msg.data = self._count
        self._pub.publish(msg)
        self.get_logger().info(f'Publishing: {msg.data}')

    def _on_toggle(self, request, response):
        self._running = request.data
        response.success = True
        response.message = 'counter started' if self._running else 'counter stopped'
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = CounterPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
