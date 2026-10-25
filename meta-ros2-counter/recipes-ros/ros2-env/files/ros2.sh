# ROS 2 environment for interactive shells (equivalent of `source /opt/ros/<distro>/setup.sh`)
export ROS_DISTRO=@ROS_DISTRO@
export ROS_VERSION=2
export ROS_PYTHON_VERSION=3
export AMENT_PREFIX_PATH=/opt/ros/@ROS_DISTRO@
export PATH=/opt/ros/@ROS_DISTRO@/bin:$PATH
export PYTHONPATH=/opt/ros/@ROS_DISTRO@/lib/@PYTHON_DIR@/site-packages${PYTHONPATH:+:$PYTHONPATH}
export LD_LIBRARY_PATH=/opt/ros/@ROS_DISTRO@/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
