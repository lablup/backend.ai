SHELL := /bin/bash
BUILD := $(CURDIR)/build
OUT ?= $(CURDIR)/out

.PHONY: all rootfs check image blob manifest reproduce verify clean

all: manifest

rootfs:
	BAI_CC_OUT=$(OUT) $(BUILD)/rootfs.sh

check: rootfs
	BAI_CC_OUT=$(OUT) $(BUILD)/verify-rootfs.sh

image: check
	BAI_CC_OUT=$(OUT) $(BUILD)/image.sh

blob:
	BAI_CC_OUT=$(OUT) $(BUILD)/initdata.sh $(EXTRA_DATA)

manifest: image blob
	BAI_CC_OUT=$(OUT) $(BUILD)/manifest.sh

reproduce:
	BAI_CC_OUT=$(OUT) $(BUILD)/reproduce.sh $(REFERENCE)

verify:
	openssl pkeyutl -verify -rawin -pubin -inkey $(OUT)/build-manifest.json.pub \
		-in $(OUT)/build-manifest.json -sigfile $(OUT)/build-manifest.json.sig
	for f in $(BUILD)/*.sh; do bash -n "$$f" || exit 1; done
	bash -n overlay/opt/kernel/bai-cc-entrypoint
	python3 -m py_compile overlay/opt/kernel/bai_cc_bootstrap.py overlay/usr/local/bin/bai-guest-boot \
		overlay/usr/local/bin/bai-integrity-mount overlay/usr/local/bin/bai-guest-storage

clean:
	rm -rf $(OUT)
