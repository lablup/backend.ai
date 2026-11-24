/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var e={CREATE_VFOLDER:`create-vfolder`,MODIFY_VFOLDER:`modify-vfolder`,DELETE_VFOLDER:`delete-vfolder`,MOUNT_IN_SESSION:`mount-in-session`,UPLOAD_FILE:`upload-file`,DOWNLOAD_FILE:`download-file`,INVITE_OTHERS:`invite-others`,SET_USER_PERM:`set-user-specific-permission`},t=t=>e[t]??t.toLowerCase().replace(/_/g,`-`),n=e=>{let n={};for(let r of e??[])n[r.host]=r.permissions.map(t);return n};export{t as n,n as t};
