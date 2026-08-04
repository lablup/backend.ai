#!/bin/bash

check() {
    return 0
}

depends() {
    echo crypt network
}

install() {
    inst_multiple cryptsetup openssl base64 od tr cut mktemp shred
    inst_binary /usr/bin/kbs-client
    inst_script "${moddir}/unlock-state-volume" /usr/bin/unlock-state-volume
    inst_simple "${moddir}/backendai-unlock-state.service" \
        "${systemdsystemunitdir}/backendai-unlock-state.service"
    $SYSTEMCTL -q --root "$initdir" enable backendai-unlock-state.service
}
