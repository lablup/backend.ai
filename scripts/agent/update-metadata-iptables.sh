#! /bin/bash

LISTEN_PORT=${LISTEN_PORT:-40128}
IPTABLES_REGEX="REDIRECT\s+tcp\s+\-\-\s+anywhere\s+169\.254\.169\.254\s+tcp dpt:http redir ports ${LISTEN_PORT}"
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
        --to-ports ${LISTEN_PORT} \
        -i docker0
    echo "iptables rule updated"
fi
