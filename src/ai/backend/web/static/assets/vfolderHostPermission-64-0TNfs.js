/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const r={CREATE_VFOLDER:"create-vfolder",MODIFY_VFOLDER:"modify-vfolder",DELETE_VFOLDER:"delete-vfolder",MOUNT_IN_SESSION:"mount-in-session",UPLOAD_FILE:"upload-file",DOWNLOAD_FILE:"download-file",INVITE_OTHERS:"invite-others",SET_USER_PERM:"set-user-specific-permission"},t=o=>r[o]??o.toLowerCase().replace(/_/g,"-"),E=o=>{const e={};for(const s of o??[])e[s.host]=s.permissions.map(t);return e};export{E as a,t as v};
//# sourceMappingURL=vfolderHostPermission-64-0TNfs.js.map
