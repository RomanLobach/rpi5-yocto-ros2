SUMMARY = "Raspberry Pi 5 image with ROS 2 Jazzy and the counter_demo nodes"
LICENSE = "MIT"

require recipes-core/images/core-image-base.bb

inherit ros2_image

IMAGE_INSTALL:append = " \
    counter-demo \
    demo-nodes-cpp \
    demo-nodes-py \
    launch-ros \
    rclpy \
    ros2-env \
    ros2cli-common-extensions \
    ros2launch \
    std-msgs \
    std-srvs \
"

# Room for logs and experiments on the target
IMAGE_ROOTFS_EXTRA_SPACE = "524288"
