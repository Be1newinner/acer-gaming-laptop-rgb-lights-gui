obj-m	:= src/facer.o

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
PWD       := $(shell pwd)

# Sign the kernel module for secure boot (Ubuntu)
# https://wiki.ubuntu.com/UEFI/SecureBoot/Signing
KEY := /var/lib/shim-signed/mok/MOK.priv
X509 := /var/lib/shim-signed/mok/MOK.der

ifdef LTS
    ccflags-y := -Dlts
endif

all: default

default:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules

	if [ -f "$(KEY)" ] && [ -f "$(X509)" ]; then \
		if [ $$(id -u) -eq 0 ]; then \
			kmodsign sha512 $(KEY) $(X509) src/facer.ko || true; \
		elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then \
			sudo kmodsign sha512 $(KEY) $(X509) src/facer.ko || true; \
		fi \
	fi

bundle:
	./bundle.sh

package-deb:
	./build_deb.sh

package-arch:
	./build_arch.sh

dist:
	./build_all.sh

install:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules_install

install-gui:
	cp -f facer_gui.py /usr/local/bin/rgb-controller
	chmod +x /usr/local/bin/rgb-controller
	ln -sf /usr/local/bin/rgb-controller /usr/local/bin/shipsar-acer-rgb
	ln -sf /usr/local/bin/rgb-controller /usr/local/bin/facer_gui.py
	if [ -d "/usr/share/applications" ]; then \
		cp -f shipsar-acer-rgb.desktop /usr/share/applications/shipsar-acer-rgb.desktop; \
		chmod 644 /usr/share/applications/shipsar-acer-rgb.desktop; \
	fi
	if [ -f "public/logo.png" ]; then \
		mkdir -p /usr/share/pixmaps; \
		cp -f public/logo.png /usr/share/pixmaps/shipsar-acer-rgb.png; \
		chmod 644 /usr/share/pixmaps/shipsar-acer-rgb.png; \
	fi

uninstall-gui:
	rm -f /usr/local/bin/rgb-controller /usr/local/bin/shipsar-acer-rgb /usr/local/bin/facer_gui.py
	rm -f /usr/share/applications/shipsar-acer-rgb.desktop /usr/share/applications/acer-predator-gui.desktop
	rm -f /usr/share/pixmaps/shipsar-acer-rgb.png

clean:
	rm -rf src/*.o src/*~ src/.*.cmd src/*.ko src/*.mod.c \
		.tmp_versions modules.order Module.symvers AcerPredatorRGB.run build dist

dkmsclean:
	@dkms remove facer/0.1 --all || true
	@dkms remove facer/0.2 --all || true
	@dkms remove facer/0.20241016-1bP --all || true
	@dkms remove facer/1.20260725 --all || true

dkms: dkmsclean
	dkms add .
	dkms install -m facer -v 1.20260725

onboot:
	echo "facer" > /etc/modules-load.d/facer.conf

noboot:
	rm -f /etc/modules-load.d/facer.conf