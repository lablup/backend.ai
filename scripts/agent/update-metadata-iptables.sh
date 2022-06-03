#! /bin/bash

IPTABLES_REGEX='REDIRECT\s+tcp\s+\-\-\s+anywhere\s+169\.254\.169\.254\s+tcp dpt:http redir ports 40128'
if [ $(id -u) -ne 0 ]; then
    echo "Please run as root."
    exit
fi
if [[ $(sudo iptables -t nat -L PREROUTING) =~ $IPTABLES_REGEX ]]; then
    echo "iptables rule already set, skipping"
else
    sudo iptables -t nat \
        -I PREROUTING \
        -p tcp \
        -d 169.254.169.254 \
        --dport 80 \
        -j REDIRECT \
        --to-ports 40128 \
        -i docker0
    echo "iptables rule updated"
fi
