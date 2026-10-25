SUMMARY = "ROS 2 counter demo: publisher, subscriber and start/stop service"
DESCRIPTION = "Publishes an incrementing counter on /counter; the counter is \
started and stopped with the /counter/toggle (std_srvs/SetBool) service."
HOMEPAGE = "https://github.com/RomanLobach/rpi5-yocto-ros2"
SECTION = "devel"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit ros_distro_jazzy

ROS_CN = "counter_demo"
ROS_BPN = "counter_demo"

ROS_EXEC_DEPENDS = " \
    launch \
    launch-ros \
    rclpy \
    std-msgs \
    std-srvs \
"

DEPENDS = "${ROS_EXEC_DEPENDS}"
RDEPENDS:${PN} += "${ROS_EXEC_DEPENDS}"

# The package source lives in <repo>/src/counter_demo, outside of the layer,
# so that it can be built with colcon on a PC and with Yocto from the same tree.
FILESEXTRAPATHS:prepend := "${THISDIR}/../../../src:"
SRC_URI = "file://counter_demo"
S = "${WORKDIR}/counter_demo"

ROS_BUILD_TYPE = "ament_python"

inherit ros_${ROS_BUILD_TYPE}
