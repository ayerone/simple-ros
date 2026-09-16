from example_interfaces.msg import String

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class Listener(Node):

    def __init__(self):
        super().__init__('listener')
        self.sub = self.create_subscription(String, 'chatter', self.chatter_callback, 10)

    def chatter_callback(self, msg):
        self.get_logger().info('I heard: [%s]' % msg.data)


def main(args=None):
    try:
        with rclpy.init(args=args):
            node = Listener()
            rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass


if __name__ == '__main__':
    main()
