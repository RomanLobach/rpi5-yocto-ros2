SUMMARY = "Shell environment for ROS 2 (/etc/profile.d/ros2.sh)"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit ros_distro_jazzy python3-dir

SRC_URI = "file://ros2.sh"
S = "${WORKDIR}"

do_install() {
    install -d ${D}${sysconfdir}/profile.d
    install -m 0644 ${WORKDIR}/ros2.sh ${D}${sysconfdir}/profile.d/ros2.sh
    sed -i -e 's|@ROS_DISTRO@|${ROS_DISTRO}|g' \
           -e 's|@PYTHON_DIR@|${PYTHON_DIR}|g' \
           ${D}${sysconfdir}/profile.d/ros2.sh
}

FILES:${PN} = "${sysconfdir}/profile.d/ros2.sh"
