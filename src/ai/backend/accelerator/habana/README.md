# Backend.AI Accelerator Plugin for Habana

Install this package in the same virtual environment as the Backend.AI agents.
The agents then detect Habana devices on their hosts and make them available to
Backend.AI kernel sessions.

```console
$ pip install -e <Path to this repository>
```

This open-source edition of the Habana plugin supports allocating one or more Habana
devices to a container, slot by slot.

## Compatibility Matrix

TBD

## Generating Docker macvlan interfaces for inter-container networking
```sh
#! /bin/bash
set -e
for pci_bus_id in $(hl-smi --format=csv,noheader -Q bus_id); do
    for net_dev in $(grep PCI_SLOT_NAME /sys/class/net/*/device/uevent | grep "${pci_bus_id}" | awk -F: '{print $1}' | awk -F/ '{print $5}'); do
        docker network create --attachable -o parent="${net_dev}" -d macvlan "gaudi_${net_dev}" >/dev/null
        echo "Docker network gaudi_${net_dev} created"
    done
done
```
