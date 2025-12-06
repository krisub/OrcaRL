# Config
# Create build directory
mkdir -p ../kbuild_algo_switch

# Generate default config
make O=../kbuild_algo_switch defconfig

# Enable/disable kernel options
scripts/config --file ../kbuild_algo_switch/.config \
  --enable CONFIG_NF_NAT \
  --enable CONFIG_NF_NAT_IPV4 \
  --enable CONFIG_IP_NF_NAT \
  --enable CONFIG_IP_NF_IPTABLES \
  --enable CONFIG_NF_CONNTRACK \
  --enable CONFIG_NF_CONNTRACK_MARK \
  --enable CONFIG_NETFILTER_XT_TARGET_CONNMARK \
  --enable CONFIG_NETFILTER_XT_MATCH_CONNMARK \
  --enable CONFIG_TUN \
  --enable CONFIG_NETFILTER_ADVANCED \
  --disable CONFIG_MODULE_SIG \
  --disable CONFIG_MODULE_SIG_ALL \
  --enable CONFIG_EXT4_FS \
  --enable CONFIG_BLK_DEV_SD \
  --enable CONFIG_BLK_DEV_NBD \
  --enable CONFIG_VIRTIO \
  --enable CONFIG_VIRTIO_BLK \
  --enable CONFIG_VT \
  --enable CONFIG_VT_CONSOLE \
  --enable CONFIG_SERIAL_8250 \
  --enable CONFIG_SERIAL_8250_CONSOLE

# Update config with new options
make O=../kbuild_algo_switch olddefconfig

# Build kernel and modules
make O=../kbuild_algo_switch -j8

# Install modules into the build directory
make O=../kbuild_algo_switch modules_install INSTALL_MOD_PATH=../kbuild_algo_switch

# Install kernel 
make O=../kbuild_algo_switch install INSTALL_PATH=../kbuild_algo_switch/boot
