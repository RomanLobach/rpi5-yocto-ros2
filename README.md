# ROS 2 (Jazzy) on a custom Yocto OS for Raspberry Pi 5

A minimal custom Linux image (Yocto Scarthgap) for the Raspberry Pi 5 with ROS 2 Jazzy
and a small demo package, `counter_demo`:

| Node | What it does |
|------|--------------|
| `counter_publisher` | publishes `std_msgs/Int32` 1, 2, 3, … on `/counter` |
| `counter_subscriber` | subscribes to `/counter` and logs every value |
| service `/counter/toggle` (`std_srvs/SetBool`) | `data: true` starts, `data: false` stops the counter |

## Repository layout

```
src/counter_demo/        ROS 2 package (ament_python), builds with colcon or Yocto
meta-ros2-counter/       own Yocto layer: counter-demo recipe, ros2-counter-image,
                         build config template (conf/templates/rpi5-ros2)
layers/                  external layers as git submodules (all on scarthgap):
  poky, meta-openembedded, meta-raspberrypi, meta-ros (meta-ros2-jazzy)
scripts/sync-to-vm.sh    helper for building on macOS (see below)
```

Clone with submodules:

```bash
git clone --recurse-submodules https://github.com/RomanLobach/rpi5-yocto-ros2.git
```

## 1. Try the nodes on a PC (Docker)

```bash
docker run -it --rm -v "$PWD/src:/ws/src" ros:jazzy bash
# inside the container:
apt-get update && apt-get install -y python3-colcon-common-extensions
cd /ws && source /opt/ros/jazzy/setup.bash && colcon build
source install/setup.bash
ros2 launch counter_demo counter.launch.py
```

In a second shell (`docker exec -it <container> bash`, then `source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash`):

```bash
ros2 node list
ros2 topic list -t
ros2 topic echo /counter
ros2 service call /counter/toggle std_srvs/srv/SetBool '{data: false}'   # stop
ros2 service call /counter/toggle std_srvs/srv/SetBool '{data: true}'    # start
```

## 2. Build the OS image

Yocto needs a case-sensitive native Linux filesystem. On macOS (Apple Silicon) use an
[OrbStack](https://orbstack.dev) Ubuntu 24.04 machine (≥16 GB RAM, ≥150 GB disk):

```bash
orb create ubuntu:24.04 yocto
orb -m yocto sudo apt-get install -y gawk wget git diffstat unzip texinfo gcc build-essential \
    chrpath socat cpio python3 python3-pip python3-pexpect xz-utils debianutils iputils-ping \
    python3-git python3-jinja2 python3-subunit zstd liblz4-tool file locales libacl1 lz4 bmap-tools rsync
scripts/sync-to-vm.sh            # mirror the repo into the VM (on a native Linux host skip this)
```

Inside the Linux machine (`orb -m yocto`):

```bash
cd ~/rpi5-yocto-ros2
export LANG=en_US.UTF-8
TEMPLATECONF=$PWD/meta-ros2-counter/conf/templates/rpi5-ros2 source layers/poky/oe-init-build-env build
bitbake ros2-counter-image       # first build takes several hours
```

The configuration template sets `MACHINE = "raspberrypi5"`, `INIT_MANAGER = "systemd"`,
`LICENSE_FLAGS_ACCEPTED = "synaptics-killswitch"` and enables dropbear SSH
(`EXTRA_IMAGE_FEATURES`) plus `debug-tweaks` (passwordless root — lab use only!).

Result: `build/tmp/deploy/images/raspberrypi5/ros2-counter-image-jazzy-raspberrypi5.rootfs.wic.bz2`

## 3. Flash and run on the Raspberry Pi 5

```bash
bmaptool copy ros2-counter-image-jazzy-raspberrypi5.rootfs.wic.bz2 /dev/<sd-card>
# or: bunzip2 -k image.wic.bz2 && sudo dd if=image.wic of=/dev/<sd-card> bs=4M status=progress
```

Boot the Pi with Ethernet attached, find its IP and log in (`root`, no password):

```bash
ssh root@<pi-ip>
source /opt/ros/jazzy/setup.sh
ros2 launch counter_demo counter.launch.py
```
