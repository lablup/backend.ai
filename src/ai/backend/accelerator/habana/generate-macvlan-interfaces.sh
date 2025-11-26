#! /bin/bash
set -e
for pci_bus_id in $(hl-smi --format=csv,noheader -Q bus_id); do
    for net_dev in $(grep PCI_SLOT_NAME /sys/class/net/*/device/uevent | grep "${pci_bus_id}" | awk -F: '{print $1}' | awk -F/ '{print $5}'); do
        docker network create --attachable -o parent="${net_dev}" -d macvlan "gaudi_${net_dev}" >/dev/null
        echo "Docker network gaudi_${net_dev} created"
    done
done
