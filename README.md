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

Yocto needs a case-sensitive, native Linux filesystem and cannot be built directly on macOS.
On a Linux PC (Ubuntu 22.04/24.04) follow [Build on Linux](#build-on-linux); on a Mac follow
the detailed [Build on macOS](#build-on-macos-apple-silicon) guide below.

What the build configuration does (`meta-ros2-counter/conf/templates/rpi5-ros2`):

- `MACHINE = "raspberrypi5"`, `INIT_MANAGER = "systemd"`,
  `LICENSE_FLAGS_ACCEPTED = "synaptics-killswitch"`;
- dropbear SSH server (`EXTRA_IMAGE_FEATURES`) and `debug-tweaks` (**passwordless root login —
  lab use only, never expose this image to an untrusted network**);
- headless image: `x11 wayland opengl vulkan pulseaudio alsa bluetooth nfc 3g pcmcia` are removed
  from `DISTRO_FEATURES`;
- the image `ros2-counter-image` = `core-image-base` + ROS 2 Jazzy runtime and CLI + `counter_demo`
  + `ros2-env` (loads the ROS environment from `/etc/profile.d/ros2.sh`).

### Build on Linux

```bash
sudo apt-get install -y gawk wget git diffstat unzip texinfo gcc build-essential chrpath socat \
    cpio python3 python3-pip python3-pexpect xz-utils debianutils iputils-ping python3-git \
    python3-jinja2 python3-subunit zstd liblz4-tool file locales libacl1 lz4 bmap-tools rsync
sudo locale-gen en_US.UTF-8

git clone --recurse-submodules https://github.com/RomanLobach/rpi5-yocto-ros2.git
cd rpi5-yocto-ros2
export LANG=en_US.UTF-8
TEMPLATECONF=$PWD/meta-ros2-counter/conf/templates/rpi5-ros2 source layers/poky/oe-init-build-env build
bitbake ros2-counter-image
```

The result is in `build/tmp/deploy/images/raspberrypi5/`:
`ros2-counter-image-jazzy-raspberrypi5.rootfs.wic.bz2` (+ `.wic.bmap`).

### Build on macOS (Apple Silicon)

The idea: the repository lives on the Mac (you edit and commit there), while the build runs inside a
Linux virtual machine on the VM's **own** disk. A Linux VM on Apple Silicon is aarch64 — the same
architecture as the Raspberry Pi 5 — so there is no x86 emulation and the build is fast. (An Intel Mac
would work too, but through an x86 VM and cross-compilation; that path is untested here.)

> **Never build inside a macOS folder** (a Mac volume or the VM's `/Users/...` mount): macOS file
> systems are case-insensitive and slow for Yocto's millions of small files, and the build breaks or
> crawls. Only the sources are mirrored into the VM; `build/`, `downloads/` and `sstate-cache/` live
> on the VM's ext4 disk.

**Requirements:** Apple Silicon Mac, macOS 13+, ≥ 24 GB RAM recommended (16 GB go to the VM),
≥ 150 GB free disk, [Homebrew](https://brew.sh), internet access (several GB of sources).

#### Step 1 — Install OrbStack and give it enough memory

```bash
brew install --cask orbstack
open -a OrbStack            # first start: finish the setup wizard; or run `orbctl start`
orbctl status               # should print "Running"
```

OrbStack's default RAM limit is lower than what C++-heavy ROS packages need. Raise it and restart:

```bash
orbctl config set memory_mib 16384
orbctl stop && orbctl start
```

#### Step 2 — Create the Ubuntu build machine

```bash
orb create ubuntu:24.04 yocto
orb -m yocto bash -c 'free -g | sed -n 2p; nproc; df -h ~ | tail -1'   # expect ~16 GB RAM, all cores, 300+ GB disk
```

Install the Yocto host dependencies inside the machine (nothing is installed on macOS):

```bash
orb -m yocto sudo apt-get update
orb -m yocto sudo apt-get install -y gawk wget git diffstat unzip texinfo gcc build-essential \
    chrpath socat cpio python3 python3-pip python3-pexpect xz-utils debianutils iputils-ping \
    python3-git python3-jinja2 python3-subunit zstd liblz4-tool file locales libacl1 lz4 bmap-tools rsync
orb -m yocto sudo locale-gen en_US.UTF-8
```

#### Step 3 — Clone the repository on the Mac and mirror it into the VM

```bash
git clone --recurse-submodules https://github.com/RomanLobach/rpi5-yocto-ros2.git
cd rpi5-yocto-ros2
scripts/sync-to-vm.sh
```

`scripts/sync-to-vm.sh` rsyncs the repo (without `.git`, `build/`, `downloads/`, `sstate-cache/`) into
`/home/<user>/rpi5-yocto-ros2` inside the VM. Run it again after every change you make on the Mac
(layer, recipes, `src/counter_demo`). Variables `VM` (machine name, default `yocto`) and `DST` (target
directory) can be overridden.

#### Step 4 — Build

Check that the layers and recipes parse, then build. The build prints progress as `Running task N of
~9700`. Later builds reuse `sstate-cache` and only rebuild what changed.

**Measured build time** (author's machine: MacBook Pro, Apple M4 Pro, 12 CPU cores, 24 GB RAM, of
which 16 GB for the OrbStack VM; `BB_NUMBER_THREADS = 10`, `PARALLEL_MAKE = -j 6`):

| Build | Tasks | Time |
|-------|-------|------|
| First full build of `ros2-counter-image` (empty `build/`, `downloads/`, `sstate-cache/`, sources fetched from the internet) | 9677 | **1 h 05 min 30 s** (13:27:44 → 14:33:14 UTC) |
| Rebuild after adding one small recipe (`ros2-env`) | 9694 (9667 reused from cache) | 1 min 17 s |

Times come from the timestamps of the BitBake logs (start of the cooker log to its last write) and
depend on CPU, RAM and internet speed.

```bash
orb -m yocto bash -c '
  export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
  cd ~/rpi5-yocto-ros2
  TEMPLATECONF=$PWD/meta-ros2-counter/conf/templates/rpi5-ros2 source layers/poky/oe-init-build-env build
  bitbake -k ros2-counter-image 2>&1 | tee ~/bitbake-image.log
'
```

Keep the Mac awake for the duration (a sleeping Mac pauses or kills the build) by prefixing the
command with `caffeinate -i`:

```bash
caffeinate -i orb -m yocto bash -c '...same script as above...'
```

Watch the progress from another terminal. Note the **single quotes**: inside double quotes or without
quotes the Mac shell would expand `~` to the Mac home directory instead of the VM's.

```bash
orb -m yocto bash -c 'grep -oE "Running task [0-9]+ of [0-9]+" ~/bitbake-image.log | tail -1'
orb -m yocto bash -c 'tail -f ~/bitbake-image.log | grep --line-buffered -E "Running task|ERROR"'   # Ctrl+C to leave
orb -m yocto bash -c 'grep -E "^ERROR" ~/bitbake-image.log | head'
```

A successful build ends with `Tasks Summary: Attempted N tasks of which … all succeeded`.
A `WARNING … Failed to fetch URL git://github.com/plougher/squashfs-tools.git … attempting MIRRORS`
is harmless — Yocto falls back to a mirror. If the build is interrupted, run the same command again:
it continues from the cache.

#### Step 5 — Get the image out of the VM

The VM sees your Mac files under `/Users/<you>/...`, so copy the artifacts straight into the repo's
`release/` folder (ignored by git):

```bash
mkdir -p release
orb -m yocto bash -c '
  D=~/rpi5-yocto-ros2/build/tmp/deploy/images/raspberrypi5
  cp -L $D/ros2-counter-image-jazzy-raspberrypi5.rootfs.wic.bz2 \
        $D/ros2-counter-image-jazzy-raspberrypi5.rootfs.wic.bmap \
        "'"$PWD"'/release/"
'
shasum -a 256 release/*.wic.bz2
```

#### Step 6 — Optional: test the root filesystem before flashing

The VM is aarch64 like the Pi, so you can run the freshly built rootfs in a `chroot` and try the nodes
without any hardware:

```bash
orb -m yocto bash -c '
  R=~/rpi5-yocto-ros2/build/tmp/work/raspberrypi5-poky-linux/ros2-counter-image/1.0/rootfs
  sudo rm -rf /srv/rootfs-test && sudo mkdir -p /srv/rootfs-test && sudo cp -a $R/. /srv/rootfs-test/
  cd /srv/rootfs-test && sudo mount -t proc proc proc && sudo mount --bind /dev dev && sudo mount -t sysfs sys sys
  sudo chroot /srv/rootfs-test /bin/sh -c ". /etc/profile.d/ros2.sh; ros2 pkg executables counter_demo"
  for m in sys dev proc; do sudo umount -l /srv/rootfs-test/$m; done
'
```

(Fast-DDS prints `SHM Transport is not supported` inside a chroot — that is a chroot artifact and does
not appear on the real board.)

#### Step 7 — Flash the SD card / USB drive from macOS

> **Writing the image erases the whole target device.** Double-check the disk identifier. Choosing
> the wrong disk (for example the internal `disk0`/`disk3`) destroys your Mac's data.

1. Insert the card/drive and list the disks. Identify yours by size and by its partitions
   (e.g. `bootfs` + `Linux` for an old Raspberry Pi OS card); a built-in SD reader shows up as
   "internal, physical", an external drive as "external":

   ```bash
   diskutil list
   ```

2. Unmount it (replace `diskN` with your disk, e.g. `disk4`):

   ```bash
   diskutil unmountDisk /dev/diskN
   ```

3. Write the image. `rdiskN` (raw device) is much faster than `diskN`. `dd` prints nothing until it
   finishes — it takes a few minutes; press `Ctrl+T` to see progress:

   ```bash
   bzcat release/ros2-counter-image-jazzy-raspberrypi5.rootfs.wic.bz2 | sudo dd of=/dev/rdiskN bs=4m
   ```

   If macOS answers `Operation not permitted`, grant your terminal app access to *Removable Volumes*
   (or *Full Disk Access*) in System Settings → Privacy & Security, unmount again and retry.
   [balenaEtcher](https://etcher.balena.io) can also flash the `.wic.bz2` file if you prefer a GUI.

4. Eject:

   ```bash
   diskutil eject /dev/diskN
   ```

#### Troubleshooting (macOS)

| Symptom | Cause / fix |
|---------|-------------|
| `tail`/`grep` on `~/bitbake-image.log` prints nothing | `~` was expanded by the Mac shell — wrap the whole remote command in single quotes: `orb -m yocto bash -c '…'` |
| Build killed, `Killed`/out-of-memory messages | Raise `memory_mib` (Step 1) or lower `BB_NUMBER_THREADS` / `PARALLEL_MAKE` in `build/conf/local.conf` inside the VM, then re-run `bitbake` |
| `Please use a locale setting which supports UTF-8` | `sudo locale-gen en_US.UTF-8` and `export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8` |
| Changes on the Mac have no effect in the build | Run `scripts/sync-to-vm.sh` again |
| Build stops, "disk space" monitor messages | Free space in the VM (`df -h ~`); `build/tmp` can be removed, `sstate-cache` and `downloads` speed up rebuilds |
| Want to start from scratch | `orb delete yocto` removes the VM and everything in it (this cannot be undone) |

## 3. Run on the Raspberry Pi 5

1. Put the flashed card in the Pi 5, connect **Ethernet** (same network as your computer — the image
   gets its address by DHCP) and power it on. The first boot takes a minute or two.
2. Find the Pi's IP address: in the router's client list, or from the Mac:

   ```bash
   for i in $(seq 1 254); do ( nc -z -G 1 192.168.1.$i 22 2>/dev/null && echo "192.168.1.$i:22 open" ) & done; wait
   ```

   (adjust `192.168.1` to your subnet). `No route to host` right after power-on just means it is
   still booting — wait and retry.
3. Log in as `root` (no password):

   ```bash
   ssh root@<pi-ip>
   ```

   After re-flashing the same card, SSH warns that the host key changed: run
   `ssh-keygen -R <pi-ip>` and connect again.
4. Run and check the nodes (the ROS 2 environment is loaded by `/etc/profile.d/ros2.sh`):

   ```bash
   ros2 launch counter_demo counter.launch.py
   ```

   and in a second SSH session:

   ```bash
   ros2 node list
   ros2 topic list -t
   ros2 topic echo /counter
   ros2 service call /counter/toggle std_srvs/srv/SetBool '{data: false}'   # stop
   ros2 service call /counter/toggle std_srvs/srv/SetBool '{data: true}'    # start
   ```
