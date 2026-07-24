#!/bin/bash
# Shipsar Developers - Acer Predator Turbo & RGB Control Service Installer
# Installs service under /opt/shipsar-developers/acer-rgb-controller

mode=${1:-install} # Allowed modes: "install" and "remove". Default: install.
service=shipsar-acer-rgb # Service name
target_dir=/opt/shipsar-developers/acer-rgb-controller # Installation folder
service_dir=/etc/systemd/system # Service setup folder

echo "[Mode: $mode]";

# Sudo check
if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi

# Check systemctl is installed
if [[ -z "$(whereis systemctl | sed 's/systemctl: //')"  ]]; then echo "systemctl is not installed"; exit 1; fi
# Check rsync is installed	
if [[ -z "$(whereis rsync | sed 's/rsync: //')"  ]]; then echo "rsync is not installed"; exit 1; fi

if [[ "$mode" == "install" || "$mode" == "remove" ]]; then
	# Remove legacy init.d/rc.d/turbo-fan files if present
	rm -f /etc/init.d/turbo-fan /etc/rc*.d/*turbo-fan /etc/init.d/shipsar-acer-rgb

	# Check service is present and remove if yes.
	if [[ "$(systemctl --type=service | grep -E 'shipsar-acer-rgb|turbo-fan')" ]]; then
		echo "['$service' service detected. Cleaning up...]";
		systemctl stop $service turbo-fan 2>/dev/null || true
		systemctl disable $service turbo-fan 2>/dev/null || true
		rm -f $service_dir/shipsar-acer-rgb.service $service_dir/turbo-fan.service
		systemctl reset-failed 2>/dev/null || true
		systemctl daemon-reload
	fi
		
	# Remove old files
	echo "[Remove old data]";
	rm -rvf $target_dir /opt/turbo-fan
	rm -f /etc/modprobe.d/blacklist-acer-wmi.conf
	rm -f /etc/udev/rules.d/99-acer-gkbbl.rules
	rm -f /usr/local/bin/rgb-controller /usr/local/bin/shipsar-acer-rgb /usr/local/bin/facer_gui.py /usr/bin/rgb-controller /usr/bin/shipsar-acer-rgb
	rm -f /usr/share/applications/shipsar-acer-rgb.desktop /usr/share/applications/acer-predator-gui.desktop
	rm -f /usr/share/pixmaps/shipsar-acer-rgb.png
fi;

if [[ "$mode" == "install" ]]
then
	echo "[Create directories]";
	mkdir -p $target_dir

	echo "[Blacklist stock acer_wmi module]";
	echo "blacklist acer_wmi" > /etc/modprobe.d/blacklist-acer-wmi.conf

	echo "[Create udev rules for Acer RGB keyboard]";
	echo 'KERNEL=="acer-gkbbl*", MODE="0666"' > /etc/udev/rules.d/99-acer-gkbbl.rules
	udevadm control --reload-rules 2>/dev/null || true
	udevadm trigger 2>/dev/null || true

	echo "[Copy new data]";
	rsync -av ./* $target_dir --exclude=".git/*"

	# Install GUI application launcher (rgb-controller) and desktop shortcut
	echo "[Install GUI Application Launcher & Desktop Icon]";
	cat << 'EOF' > /usr/local/bin/rgb-controller
#!/bin/sh
exec python3 /opt/shipsar-developers/acer-rgb-controller/facer_gui.py "$@"
EOF
	chmod +x /usr/local/bin/rgb-controller
	ln -sf /usr/local/bin/rgb-controller /usr/local/bin/shipsar-acer-rgb
	ln -sf /usr/local/bin/rgb-controller /usr/local/bin/facer_gui.py

	if [ -d "/usr/share/applications" ]; then
		cp -f $target_dir/shipsar-acer-rgb.desktop /usr/share/applications/shipsar-acer-rgb.desktop
		chmod 644 /usr/share/applications/shipsar-acer-rgb.desktop
	fi

	if [ -f "$target_dir/public/logo.png" ]; then
		mkdir -p /usr/share/pixmaps
		cp -f $target_dir/public/logo.png /usr/share/pixmaps/shipsar-acer-rgb.png
		chmod 644 /usr/share/pixmaps/shipsar-acer-rgb.png
	fi

	echo "[Create shipsar-acer-rgb service]"
	cat << EOF > $service_dir/shipsar-acer-rgb.service
[Unit]
Description=Shipsar Acer Predator RGB & Turbo Control Service
After=multi-user.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=$target_dir
ExecStart=/bin/bash $target_dir/service.sh
ExecStop=/bin/bash $target_dir/uninstall.sh

[Install]
WantedBy=multi-user.target
EOF
	chown -R root:root $target_dir
	chmod 755 $target_dir/service.sh

	systemctl reset-failed $service 2>/dev/null || true
	systemctl daemon-reload
	systemctl enable $service
	systemctl start --no-block $service
	echo "[*] Done! Shipsar Acer RGB Keyboard and Turbo service installed and active."
	echo "[*] Launch GUI anytime with command 'rgb-controller' or from Application Menu."
fi
