import{i as W,r as Q,j as a,c0 as vt,K as ct,u as Y,X as mt,y as nt,al as Z,bM as pn,N as se,a8 as gt,a2 as te,a3 as Bt,l as q,hI as Fn,dG as _t,d4 as G,dp as yn,cB as Ot,a as at,cI as kn,hJ as $t,hK as wt,as as et,bp as hn,aY as Ut,aL as Vn,cA as Sn,aS as tt,v as bn,s as Rt,M as It,e as In,Y as qt,Z as Cn,hL as Dn,g as Qt,aQ as Mn,t as At,hM as xn,ao as jn,hN as Tn,aj as xt,ab as Kn,D as _n,hE as Ht,hO as An,hP as Nn,a$ as zt,aM as Gt,am as Ln,L as Pn,b as En,cD as vn,hQ as Bn,b3 as Wt,bW as On,f5 as $n,bG as wn,aD as Un,B as Rn,aU as Dt,ap as qn,b4 as Qn,z as Hn,W as zn,co as Gn,d as Wn,a7 as Yn,bD as ut,bE as Jn,c8 as Ct,ag as Xn,ae as Zn,aN as ea,aR as ta,ah as na,c9 as Nt,q as aa,bL as Lt,bg as la,aa as sa,cC as ra,cz as oa,P as ia,at as da,ew as ua,ak as ca,Q as ma}from"./index-DPebpL40.js";import{Q as ga}from"./QuotaPerStorageVolumePanelCard-YBRaxgvI.js";import{V as fa}from"./VFolderNodeIdenticonV2-BgKThcSZ.js";import{B as pa}from"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import"./usePrimaryColors-XfXvQlI3.js";const Yt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIVFolderDeleteButtonV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"VFolder",abstractKey:null};Yt.hash="4d44e5f0482b6a1b21c4aac58aa7d9f2";const Fa=n=>{"use memo";const e=W.c(8),{vfolderFrgmt:r,label:t,tooltip:d,isDisabled:s,onClick:l,size:m}=n,u=m===void 0?"md":m;let i;e[0]===Symbol.for("react.memo_cache_sentinel")?(i=Yt,e[0]=i):i=e[0],Q.useFragment(i,r);const F=d??t;let h;e[1]===Symbol.for("react.memo_cache_sentinel")?(h=a.jsx(vt,{}),e[1]=h):h=e[1];let o;return e[2]!==s||e[3]!==t||e[4]!==l||e[5]!==u||e[6]!==F?(o=a.jsx(ct,{label:t,tooltip:F,icon:h,variant:"ghost",size:u,className:"bai-name-action-cell-danger",isDisabled:s,onClick:l}),e[2]=s,e[3]=t,e[4]=l,e[5]=u,e[6]=F,e[7]=o):o=e[7],o},Jt=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},t={defaultValue:null,kind:"LocalArgument",name:"limit"},d={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},l={defaultValue:null,kind:"LocalArgument",name:"projectId"},m={kind:"Variable",name:"projectId",variableName:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},m],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},F={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[h],C={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},m],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:o,storageKey:null},M={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},m],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:o,storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[n,e,r,t,d,s,l],kind:"Fragment",metadata:null,name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:u,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:i,action:"THROW"},F,{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},h],storageKey:null},C,M],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,d,t,n,s,e,r],kind:"Operation",name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:u,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[i,F,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[y,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},i],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[y],storageKey:null},i],storageKey:null}],storageKey:null},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[f,V,y,k,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},i,k,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[f],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[f,V,k,y],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},h],storageKey:null},C,M]},params:{cacheID:"8052e04b636ce630b2aac1d9ed54f299",id:null,metadata:{},name:"ProjectAdminDataPageQuery",operationKind:"query",text:`query ProjectAdminDataPageQuery(
  $projectId: UUID!
  $offset: Int
  $limit: Int
  $filter: VFolderFilter
  $orderBy: [VFolderOrderBy!]
  $filterForActiveCount: VFolderFilter
  $filterForDeletedCount: VFolderFilter
) {
  projectVfolders(projectId: $projectId, offset: $offset, limit: $limit, filter: $filter, orderBy: $orderBy) {
    edges {
      node {
        id
        vfolderStatus: status
        ...VFolderNodesV2Fragment
        ...DeleteVFolderModalV2Fragment
        ...DeleteForeverVFolderModalV2Fragment
        ...RestoreVFolderModalV2Fragment
        ...BAIVFolderDeleteButtonV2Fragment
      }
    }
    count
  }
  active: projectVfolders(projectId: $projectId, filter: $filterForActiveCount) {
    count
  }
  deleted: projectVfolders(projectId: $projectId, filter: $filterForDeletedCount) {
    count
  }
}

fragment AppLaunchConfirmationModalFragment on ComputeSessionNode {
  id
  row_id
  name
  ...useBackendAIAppLauncherFragment
}

fragment AppLauncherModalFragment on ComputeSessionNode {
  id
  row_id
  name
  service_ports
  access_key
  ...useBackendAIAppLauncherFragment
  ...SFTPConnectionInfoModalFragment
  ...TensorboardPathModalFragment
  ...AppLaunchConfirmationModalFragment
}

fragment BAIComputeSessionNodeNotificationItemFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  ...SessionActionButtonsFragment
  ...SessionStatusTagFragment
}

fragment BAINodeNotificationItemFragment on Node {
  __isNode: __typename
  ... on ComputeSessionNode {
    __typename
    status
    name
    row_id
    ...BAIComputeSessionNodeNotificationItemFragment
  }
  ... on VFolder {
    __typename
    ...BAIVirtualFolderNodeNotificationItemV2Fragment
  }
  ... on VirtualFolderNode {
    __typename
    status
    ...BAIVirtualFolderNodeNotificationItemFragment
  }
  id
}

fragment BAIVFolderDeleteButtonV2Fragment on VFolder {
  id
}

fragment BAIVirtualFolderNodeNotificationItemFragment on VirtualFolderNode {
  row_id
  id
  name
  status
}

fragment BAIVirtualFolderNodeNotificationItemV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment ContainerCommitModalFragment on ComputeSessionNode {
  id
  name
  row_id
}

fragment ContainerLogModalFragment on ComputeSessionNode {
  id
  row_id
  name
  status
  access_key
  kernel_nodes {
    edges {
      node {
        id
        row_id
        container_id
        cluster_idx
        cluster_role
        cluster_hostname
      }
    }
  }
}

fragment DeleteForeverVFolderModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment DeleteVFolderModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment RestoreVFolderModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment SFTPConnectionInfoModalFragment on ComputeSessionNode {
  row_id
  vfolder_nodes @since(version: "25.4.0") {
    edges {
      node {
        name
        id
      }
    }
  }
}

fragment SessionActionButtonsFragment on ComputeSessionNode {
  id
  name
  row_id
  type
  status
  access_key
  service_ports
  commit_status
  user_id
  ...TerminateSessionModalFragment
  ...ContainerLogModalFragment
  ...ContainerCommitModalFragment
  ...AppLauncherModalFragment
  ...SFTPConnectionInfoModalFragment
  ...useBackendAIAppLauncherFragment
}

fragment SessionStatusTagFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
}

fragment SharedFolderPermissionInfoModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
  accessControl {
    ownershipType
  }
  ownership {
    creatorEmail
    user {
      basicInfo {
        email
      }
      id
    }
  }
  ...VFolderPermissionCellV2Fragment
}

fragment TensorboardPathModalFragment on ComputeSessionNode {
  id
  row_id
  name
  ...useBackendAIAppLauncherFragment
}

fragment TerminateSessionModalFragment on ComputeSessionNode {
  id
  row_id
  name
  scaling_group
  access_key
  project_id
  kernel_nodes {
    edges {
      node {
        container_id
        agent_id
        id
      }
    }
  }
}

fragment VFolderNodeIdenticonV2Fragment on VFolder {
  id
}

fragment VFolderNodesV2Fragment on VFolder {
  id
  vfolderStatus: status
  host
  unmanagedPath
  metadata {
    name
    usageMode
    quotaScopeId
    createdAt
    lastUsed
    cloneable
  }
  accessControl {
    permission
    ownershipType
  }
  ownership {
    userId
    projectId
    creatorEmail
    user {
      basicInfo {
        email
      }
      id
    }
    project {
      basicInfo {
        name
      }
      id
    }
  }
  ...VFolderPermissionCellV2Fragment
  ...VFolderNodeIdenticonV2Fragment
  ...SharedFolderPermissionInfoModalV2Fragment
  ...DeleteForeverVFolderModalV2Fragment
  ...BAINodeNotificationItemFragment
}

fragment VFolderPermissionCellV2Fragment on VFolder {
  accessControl {
    permission
  }
}

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();Jt.hash="1f6d597c1b6abd207b4639a11dd0a327";const Xt=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkPurgeVFoldersV2Payload",kind:"LinkedField",name:"bulkPurgeVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"purgedCount",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"DeleteForeverVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"DeleteForeverVFolderModalV2Mutation",selections:e},params:{cacheID:"ec0678be01bd641d826e9bc9a2693eb0",id:null,metadata:{},name:"DeleteForeverVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteForeverVFolderModalV2Mutation(
  $input: BulkPurgeVFoldersV2Input!
) {
  bulkPurgeVfoldersV2(input: $input) {
    purgedCount
  }
}
`}}})();Xt.hash="ed8f37af9563c755ccfc33151d5d168f";const Zt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteForeverVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};Zt.hash="af117d7a409739259841dcfce2d2a493";const en=n=>{"use memo";var P,O,$,_;const e=W.c(66);let r,t,d,s;e[0]!==n?({vfolderFrgmts:s,onRequestClose:t,open:d,...r}=n,e[0]=n,e[1]=r,e[2]=t,e[3]=d,e[4]=s):(r=e[1],t=e[2],d=e[3],s=e[4]);const{t:l}=Y(),{message:m}=mt.useApp(),{getErrorMessage:u}=nt();let i;e[5]===Symbol.for("react.memo_cache_sentinel")?(i=Zt,e[5]=i):i=e[5];const F=Q.useFragment(i,s);let h;e[6]===Symbol.for("react.memo_cache_sentinel")?(h=Xt,e[6]=h):h=e[6];const[o,C]=Q.useMutation(h);let M,y,f,V,k,x,j,S,K,A,T,D,N,B,p,b;e[7]!==C||e[8]!==r||e[9]!==t||e[10]!==d||e[11]!==l||e[12]!==F?(f=F??[],y=f.length===1?((O=(P=f[0])==null?void 0:P.metadata)==null?void 0:O.name)??l("button.Delete"):l("button.Delete"),M=pn,A=r,T=!!d,e[29]!==t?(D=U=>{U||t==null||t(!1)},e[29]=t,e[30]=D):D=e[30],e[31]!==l?(N=l("dialog.title.DeleteForever"),e[31]=l,e[32]=N):N=e[32],B=f.length===1?l("data.folders.DeleteForeverDescription",{folderName:((_=($=f[0])==null?void 0:$.metadata)==null?void 0:_.name)??""}):void 0,p=!1,e[33]!==l?(b=l("data.folders.DeleteForever"),e[33]=l,e[34]=b):b=e[34],e[35]!==l?(V=l("button.Cancel"),e[35]=l,e[36]=V):V=e[36],k=C,x=Z(f,ya),j=!0,S=y,K=l("dialog.PleaseTypeToConfirm",{confirmText:y}),e[7]=C,e[8]=r,e[9]=t,e[10]=d,e[11]=l,e[12]=F,e[13]=M,e[14]=y,e[15]=f,e[16]=V,e[17]=k,e[18]=x,e[19]=j,e[20]=S,e[21]=K,e[22]=A,e[23]=T,e[24]=D,e[25]=N,e[26]=B,e[27]=p,e[28]=b):(M=e[13],y=e[14],f=e[15],V=e[16],k=e[17],x=e[18],j=e[19],S=e[20],K=e[21],A=e[22],T=e[23],D=e[24],N=e[25],B=e[26],p=e[27],b=e[28]);let L;e[37]!==y?(L={placeholder:y},e[37]=y,e[38]=L):L=e[38];let c;e[39]!==l?(c=l("dialog.warning.CannotBeUndone"),e[39]=l,e[40]=c):c=e[40];let g;e[41]!==o||e[42]!==u||e[43]!==m||e[44]!==t||e[45]!==f||e[46]!==l?(g=()=>{if(f.length===0){t==null||t(!1);return}const U=Z(f,ka);o({variables:{input:{ids:U}},onCompleted:(w,H)=>{var J,z,re;if(H&&H.length>0){const X=H[0];m.error((X==null?void 0:X.message)??u(X));return}const ee=((J=w==null?void 0:w.bulkPurgeVfoldersV2)==null?void 0:J.purgedCount)??0;if(ee===0){m.error(l("data.folders.FailedToDeleteFolders",{folderNames:Z(f,ha).join(", ")}));return}f.length===1?m.success(l("data.folders.FolderDeletedForever",{folderName:(re=(z=f[0])==null?void 0:z.metadata)==null?void 0:re.name})):m.success(l("data.folders.MultipleFolderDeletedForever",{count:ee,total:f.length})),t==null||t(!0)},onError:w=>{m.error(u(w))}})},e[41]=o,e[42]=u,e[43]=m,e[44]=t,e[45]=f,e[46]=l,e[47]=g):g=e[47];let I;return e[48]!==M||e[49]!==V||e[50]!==k||e[51]!==x||e[52]!==j||e[53]!==S||e[54]!==K||e[55]!==L||e[56]!==c||e[57]!==g||e[58]!==A||e[59]!==T||e[60]!==D||e[61]!==N||e[62]!==B||e[63]!==p||e[64]!==b?(I=a.jsx(M,{...A,isOpen:T,onOpenChange:D,title:N,description:B,maskClosable:p,okText:b,cancelText:V,confirmLoading:k,items:x,requireConfirmInput:j,confirmText:S,inputLabel:K,inputProps:L,cannotBeUndoneText:c,onOk:g}),e[48]=M,e[49]=V,e[50]=k,e[51]=x,e[52]=j,e[53]=S,e[54]=K,e[55]=L,e[56]=c,e[57]=g,e[58]=A,e[59]=T,e[60]=D,e[61]=N,e[62]=B,e[63]=p,e[64]=b,e[65]=I):I=e[65],I};function ya(n){var e;return{key:n.id??"",label:((e=n.metadata)==null?void 0:e.name)??""}}function ka(n){return se(n.id)}function ha(n){var e;return(e=n==null?void 0:n.metadata)==null?void 0:e.name}const tn=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkDeleteVFoldersV2Payload",kind:"LinkedField",name:"bulkDeleteVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"deletedCount",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"DeleteVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"DeleteVFolderModalV2Mutation",selections:e},params:{cacheID:"4c634cd755935ee2cb040749d5321e31",id:null,metadata:{},name:"DeleteVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteVFolderModalV2Mutation(
  $input: BulkDeleteVFoldersV2Input!
) {
  bulkDeleteVfoldersV2(input: $input) {
    deletedCount
  }
}
`}}})();tn.hash="145309ffdb360f52c306ad651117ab30";const nn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};nn.hash="c1b7e252a2275b9b74d0576b46e2f299";const Va=n=>{"use memo";var B,p;const e=W.c(48);let r,t,d;e[0]!==n?({vfolderFrgmts:d,onRequestClose:t,...r}=n,e[0]=n,e[1]=r,e[2]=t,e[3]=d):(r=e[1],t=e[2],d=e[3]);const{t:s}=Y(),{message:l}=mt.useApp(),{getErrorMessage:m}=nt();let u;e[4]===Symbol.for("react.memo_cache_sentinel")?(u=nn,e[4]=u):u=e[4];const i=Q.useFragment(u,d);let F;e[5]===Symbol.for("react.memo_cache_sentinel")?(F=tn,e[5]=F):F=e[5];const[h,o]=Q.useMutation(F);let C,M,y,f,V,k,x,j,S,K,A,T;if(e[6]!==r||e[7]!==h||e[8]!==m||e[9]!==o||e[10]!==l||e[11]!==t||e[12]!==s||e[13]!==i){const b=i??[];M=gt,x=r.open,e[26]!==t?(j=L=>{L||t==null||t(!1)},e[26]=t,e[27]=j):j=e[27],e[28]!==s?(S=s("data.folders.MoveToTrash"),e[28]=s,e[29]=S):S=e[29],K=!1,e[30]!==s?(A=s("data.folders.Delete"),e[30]=s,e[31]=A):A=e[31],e[32]===Symbol.for("react.memo_cache_sentinel")?(T={danger:!0},e[32]=T):T=e[32],y=o,f=()=>{if(b.length===0){t==null||t(!1);return}const L=Z(b,Sa);h({variables:{input:{ids:L}},onCompleted:(c,g)=>{var P,O,$;if(g&&g.length>0){const _=g[0];l.error((_==null?void 0:_.message)??m(_));return}const I=((P=c==null?void 0:c.bulkDeleteVfoldersV2)==null?void 0:P.deletedCount)??0;if(I===0){l.error(s("data.folders.FailedToDeleteFolders",{folderNames:Z(b,ba).join(", ")}));return}b.length===1?l.success(s("data.folders.FolderDeleted",{folderName:($=(O=b[0])==null?void 0:O.metadata)==null?void 0:$.name})):l.success(s("data.folders.MultipleFolderDeleted",{count:I,total:b.length})),t==null||t(!0)},onError:c=>{l.error(m(c))}})},V=r,C=te,k=b.length===1?s("data.folders.MoveToTrashDescription",{folderName:(p=(B=b[0])==null?void 0:B.metadata)==null?void 0:p.name}):s("data.folders.MoveToTrashMultipleDescription",{folderLength:b.length}),e[6]=r,e[7]=h,e[8]=m,e[9]=o,e[10]=l,e[11]=t,e[12]=s,e[13]=i,e[14]=C,e[15]=M,e[16]=y,e[17]=f,e[18]=V,e[19]=k,e[20]=x,e[21]=j,e[22]=S,e[23]=K,e[24]=A,e[25]=T}else C=e[14],M=e[15],y=e[16],f=e[17],V=e[18],k=e[19],x=e[20],j=e[21],S=e[22],K=e[23],A=e[24],T=e[25];let D;e[33]!==C||e[34]!==k?(D=a.jsx(C,{children:k}),e[33]=C,e[34]=k,e[35]=D):D=e[35];let N;return e[36]!==M||e[37]!==y||e[38]!==f||e[39]!==V||e[40]!==D||e[41]!==x||e[42]!==j||e[43]!==S||e[44]!==K||e[45]!==A||e[46]!==T?(N=a.jsx(M,{isOpen:x,onOpenChange:j,title:S,maskClosable:K,okText:A,okButtonProps:T,confirmLoading:y,onOk:f,...V,children:D}),e[36]=M,e[37]=y,e[38]=f,e[39]=V,e[40]=D,e[41]=x,e[42]=j,e[43]=S,e[44]=K,e[45]=A,e[46]=T,e[47]=N):N=e[47],N};function Sa(n){return se(n.id)}function ba(n){var e;return(e=n==null?void 0:n.metadata)==null?void 0:e.name}const an=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"RestoreVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"RestoreVFolderModalV2Mutation",selections:e},params:{cacheID:"14d669a32252e8429330552a9eb6e82e",id:null,metadata:{},name:"RestoreVFolderModalV2Mutation",operationKind:"mutation",text:`mutation RestoreVFolderModalV2Mutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();an.hash="0efe06c3f5b800e9b582b9d254f35ed3";const ln={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"RestoreVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};ln.hash="3f78d6da02312aa15054515c21edda60";const Ia=n=>{"use memo";var A,T,D,N,B,p;const e=W.c(34);let r,t,d;e[0]!==n?({vfolderFrgmts:d,onRequestClose:t,...r}=n,e[0]=n,e[1]=r,e[2]=t,e[3]=d):(r=e[1],t=e[2],d=e[3]);const{t:s}=Y(),{upsertNotification:l}=Bt(),{getErrorMessage:m}=nt(),u=Q.useRelayEnvironment(),[i,F]=q.useState(!1);let h;e[4]===Symbol.for("react.memo_cache_sentinel")?(h=ln,e[4]=h):h=e[4];const o=Q.useFragment(h,d);let C;e[5]!==u?(C=b=>new Promise((L,c)=>{Fn.commitMutation(u,{mutation:an,variables:{vfolderId:se(b)},onCompleted:(g,I)=>{if(I&&I.length>0){c(I[0]);return}L()},onError:g=>c(g)})}),e[5]=u,e[6]=C):C=e[6];const M=C,y=r.open;let f;e[7]!==t?(f=b=>{b||t==null||t(!1)},e[7]=t,e[8]=f):f=e[8];let V;e[9]!==s?(V=s("data.folders.Restore"),e[9]=s,e[10]=V):V=e[10];let k;e[11]!==s?(k=s("data.folders.Restore"),e[11]=s,e[12]=k):k=e[12];let x;e[13]!==m||e[14]!==t||e[15]!==M||e[16]!==s||e[17]!==l||e[18]!==o?(x=()=>{const b=Z(o,L=>M(L.id).catch(c=>(l({message:m(c),description:c==null?void 0:c.description,open:!0}),Promise.reject(c))));F(!0),Promise.allSettled(b).then(L=>{var g,I;F(!1);const c=L.every(Ca);c&&((o==null?void 0:o.length)===1?_t.success(s("data.folders.FolderRestored",{folderName:(I=(g=o==null?void 0:o[0])==null?void 0:g.metadata)==null?void 0:I.name})):_t.success(s("data.folders.MultipleFolderRestored",{folderLength:o==null?void 0:o.length}))),t==null||t(c)})},e[13]=m,e[14]=t,e[15]=M,e[16]=s,e[17]=l,e[18]=o,e[19]=x):x=e[19];let j;e[20]!==s||e[21]!==((T=(A=o==null?void 0:o[0])==null?void 0:A.metadata)==null?void 0:T.name)||e[22]!==(o==null?void 0:o.length)?(j=(o==null?void 0:o.length)===1?s("data.folders.RestoreDescription",{folderName:(N=(D=o==null?void 0:o[0])==null?void 0:D.metadata)==null?void 0:N.name}):s("data.folders.RestoreMultipleDescription",{folderLength:o==null?void 0:o.length}),e[20]=s,e[21]=(p=(B=o==null?void 0:o[0])==null?void 0:B.metadata)==null?void 0:p.name,e[22]=o==null?void 0:o.length,e[23]=j):j=e[23];let S;e[24]!==j?(S=a.jsx(te,{children:j}),e[24]=j,e[25]=S):S=e[25];let K;return e[26]!==r||e[27]!==i||e[28]!==f||e[29]!==V||e[30]!==k||e[31]!==x||e[32]!==S?(K=a.jsx(gt,{isOpen:y,onOpenChange:f,title:V,maskClosable:!1,okText:k,confirmLoading:i,onOk:x,...r,children:S}),e[26]=r,e[27]=i,e[28]=f,e[29]=V,e[30]=k,e[31]=x,e[32]=S,e[33]=K):K=e[33],K};function Ca(n){return n.status==="fulfilled"}const sn=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"VFolderNodesV2RestoreMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"VFolderNodesV2RestoreMutation",selections:e},params:{cacheID:"fc05c41196eaa2483ea656725bdc2909",id:null,metadata:{},name:"VFolderNodesV2RestoreMutation",operationKind:"mutation",text:`mutation VFolderNodesV2RestoreMutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();sn.hash="786c5ce4389066e04eac9355a031686d";const rn=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"DeleteVFolderV2Payload",kind:"LinkedField",name:"deleteVfolderV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"VFolderNodesV2DeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"VFolderNodesV2DeleteMutation",selections:e},params:{cacheID:"267b27dfe24bf987d3e29f11f2c03074",id:null,metadata:{},name:"VFolderNodesV2DeleteMutation",operationKind:"mutation",text:`mutation VFolderNodesV2DeleteMutation(
  $vfolderId: UUID!
) {
  deleteVfolderV2(vfolderId: $vfolderId) {
    id
  }
}
`}}})();rn.hash="6a3f03b7eacad2630bd79321d5da93d7";const on=(function(){var n={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"VFolderNodesV2Fragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[n,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[n],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderPermissionCellV2Fragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonV2Fragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"BAINodeNotificationItemFragment"}],type:"Node",abstractKey:"__isNode"},kind:"AliasedInlineFragmentSpread",name:"notificationFrgmt"}],type:"VFolder",abstractKey:null}})();on.hash="07611fcd2a8e6b5fb66ca14bf652e541";const dn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SharedFolderPermissionInfoModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderPermissionCellV2Fragment"}],type:"VFolder",abstractKey:null};dn.hash="5a18839a6dffea1a5a545710cc7e8bda";const un={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"VFolderPermissionCellV2Fragment",selections:[{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};un.hash="a517ea6cc8c2fc65f02d29454cd0a8c8";const cn=n=>{"use memo";var K;const e=W.c(27);let r,t;e[0]!==n?({vfolderFrgmt:t,...r}=n,e[0]=n,e[1]=r,e[2]=t):(r=e[1],t=e[2]);const{t:d}=Y();let s;e[3]===Symbol.for("react.memo_cache_sentinel")?(s=un,e[3]=s):s=e[3];const l=Q.useFragment(s,t??null);let m;e[4]!==d?(m=d("data.ReadOnly"),e[4]=d,e[5]=m):m=e[5];let u;e[6]!==m?(u={label:m,icon:"R"},e[6]=m,e[7]=u):u=e[7];let i;e[8]!==d?(i=d("data.ReadWrite"),e[8]=d,e[9]=i):i=e[9];let F;e[10]!==i?(F={label:i,icon:"RW"},e[10]=i,e[11]=F):F=e[11];let h;e[12]!==u||e[13]!==F?(h={ro:u,rw:F},e[12]=u,e[13]=F,e[14]=h):h=e[14];const o=h,C=((K=l==null?void 0:l.accessControl)==null?void 0:K.permission)==="READ_ONLY"?"ro":"rw",M=o[C];let y;e[15]!==M?(y={permissionInfo:M},e[15]=M,e[16]=y):y=e[16];const{permissionInfo:f}=y,V=f==null?void 0:f.label;let k;e[17]!==V?(k=a.jsx(te,{children:V}),e[17]=V,e[18]=k):k=e[18];let x;e[19]!==(f==null?void 0:f.icon)?(x=Z(f==null?void 0:f.icon,Da),e[19]=f==null?void 0:f.icon,e[20]=x):x=e[20];let j;e[21]!==x?(j=a.jsx(G,{children:x}),e[21]=x,e[22]=j):j=e[22];let S;return e[23]!==r||e[24]!==k||e[25]!==j?(S=a.jsxs(G,{gap:2,...r,children:[k,j]}),e[23]=r,e[24]=k,e[25]=j,e[26]=S):S=e[26],S};function Da(n){return a.jsx(te,{type:"code",children:yn(n)},n)}const Ma=n=>{"use memo";var $,_,U,w,H,ee;const e=W.c(63);let r,t,d,s;e[0]!==n?({vfolderFrgmt:s,onRequestClose:d,onLeaveFolder:t,...r}=n,e[0]=n,e[1]=r,e[2]=t,e[3]=d,e[4]=s):(r=e[1],t=e[2],d=e[3],s=e[4]);const{t:l}=Y(),{message:m}=mt.useApp(),{getErrorMessage:u}=nt(),[i]=Ot(),F=at();let h;e[5]===Symbol.for("react.memo_cache_sentinel")?(h=dn,e[5]=h):h=e[5];const o=Q.useFragment(h,s);let C;e[6]!==F?(C={mutationFn:J=>{const{folderId:z}=J;return F.vfolder.leave_invited(z)}},e[6]=F,e[7]=C):C=e[7];const M=kn(C),y=(($=o==null?void 0:o.accessControl)==null?void 0:$.ownershipType)==="USER",f=r.open;let V;e[8]!==d?(V=J=>{J||d()},e[8]=d,e[9]=V):V=e[9];let k;e[10]!==l?(k=l("data.SharedFolderPermission"),e[10]=l,e[11]=k):k=e[11];let x;e[12]!==y||e[13]!==l?(x=l(y?"data.folders.SharedFolderAlertDesc":"data.folders.ProjectFolderAlertDesc"),e[12]=y,e[13]=l,e[14]=x):x=e[14];let j;e[15]!==x?(j=a.jsx(bn,{status:"info",title:x}),e[15]=x,e[16]=j):j=e[16];let S;e[17]!==l?(S=l("data.FolderInfo"),e[17]=l,e[18]=S):S=e[18];let K;e[19]!==l?(K=l("data.folders.Name"),e[19]=l,e[20]=K):K=e[20];const A=((_=o==null?void 0:o.metadata)==null?void 0:_.name)??"";let T;e[21]!==A?(T=a.jsx(Rt,{copyable:!0,children:A}),e[21]=A,e[22]=T):T=e[22];let D;e[23]!==T||e[24]!==K?(D=a.jsx(It,{label:K,children:T}),e[23]=T,e[24]=K,e[25]=D):D=e[25];let N;e[26]!==l?(N=l("data.folders.Type"),e[26]=l,e[27]=N):N=e[27];let B;e[28]!==y||e[29]!==l?(B=y?a.jsxs(G,{gap:2,children:[a.jsx(te,{children:l("data.User")}),a.jsx($t,{size:"1em"})]}):a.jsxs(G,{gap:2,children:[a.jsx(te,{children:l("data.Project")}),a.jsx(wt,{size:"1em"})]}),e[28]=y,e[29]=l,e[30]=B):B=e[30];let p;e[31]!==N||e[32]!==B?(p=a.jsx(It,{label:N,children:B}),e[31]=N,e[32]=B,e[33]=p):p=e[33];let b;e[34]!==l?(b=l("data.folders.Owner"),e[34]=l,e[35]=b):b=e[35];const L=((U=o==null?void 0:o.ownership)==null?void 0:U.creatorEmail)||((ee=(H=(w=o==null?void 0:o.ownership)==null?void 0:w.user)==null?void 0:H.basicInfo)==null?void 0:ee.email);let c;e[36]!==b||e[37]!==L?(c=a.jsx(It,{label:b,children:L}),e[36]=b,e[37]=L,e[38]=c):c=e[38];let g;e[39]!==D||e[40]!==p||e[41]!==c||e[42]!==S?(g=a.jsxs(In,{title:S,columns:2,children:[D,p,c]}),e[39]=D,e[40]=p,e[41]=c,e[42]=S,e[43]=g):g=e[43];let I;e[44]!==i||e[45]!==u||e[46]!==y||e[47]!==M||e[48]!==m||e[49]!==t||e[50]!==d||e[51]!==l||e[52]!==o?(I=y?a.jsxs(et,{align:"stretch",gap:4,children:[a.jsx(hn,{level:5,children:l("data.folders.Permission")}),a.jsx(Ut,{bordered:!0,pagination:!1,dataSource:tt([o]),columns:[{key:"userName",title:l("general.E-Mail"),render:()=>i.email},{key:"permissions",title:l("data.folders.MountPermission"),render:xa},{key:"control",title:l("data.folders.Control"),render:(J,z)=>{var re;return a.jsx(G,{justify:"center",children:a.jsx(Vn,{title:l("data.invitation.LeaveSharedFolderDesc",{folderName:(re=z==null?void 0:z.metadata)==null?void 0:re.name}),onConfirm:()=>{const X=z==null?void 0:z.id,ne=X?se(X):null;ne&&X&&M.mutate({folderId:ne},{onSuccess:()=>{t==null||t(X),m.success(l("data.invitation.SuccessfullyLeftSharedFolder")),d(!0)},onError:oe=>{m.error(u(oe)),d()}})},children:a.jsx(ct,{label:l("data.invitation.LeaveSharedFolder"),tooltip:l("data.invitation.LeaveSharedFolder"),size:"sm",variant:"ghost",icon:a.jsx(Sn,{}),className:"bai-name-action-cell-danger"})})})}}]})]}):null,e[44]=i,e[45]=u,e[46]=y,e[47]=M,e[48]=m,e[49]=t,e[50]=d,e[51]=l,e[52]=o,e[53]=I):I=e[53];let P;e[54]!==g||e[55]!==I||e[56]!==j?(P=a.jsxs(et,{align:"stretch",gap:5,children:[j,g,I]}),e[54]=g,e[55]=I,e[56]=j,e[57]=P):P=e[57];let O;return e[58]!==r||e[59]!==P||e[60]!==V||e[61]!==k?(O=a.jsx(gt,{isOpen:f,onOpenChange:V,title:k,maskClosable:!1,footer:null,...r,children:P}),e[58]=r,e[59]=P,e[60]=V,e[61]=k,e[62]=O):O=e[62],O};function xa(n,e){return a.jsx(cn,{vfolderFrgmt:e})}const Mt=["name","host","usage_mode","created_at","status"],ja=[...Mt,...Mt.map(n=>`-${n}`)],ae=n=>xt(Mt,n),Ta=n=>{"use memo";var B,p,b,L,c,g,I;const e=W.c(32),{vfolder:r,onShare:t,onDelete:d,onRestore:s,onDeleteForever:l,onStartServiceFallback:m,noDeployTooltip:u}=n,{t:i}=Y(),{token:F}=Kn.useToken(),{generateFolderPath:h}=_n(),o=qt(),C=((B=r==null?void 0:r.metadata)==null?void 0:B.usageMode)==="DATA",M=((p=r==null?void 0:r.metadata)==null?void 0:p.usageMode)==="MODEL",y=r==null?void 0:r.vfolderStatus;let f;e[0]!==y?(f=Ht(y),e[0]=y,e[1]=f):f=e[1];const V=f;let k,x;if(e[2]!==h||e[3]!==V||e[4]!==M||e[5]!==C||e[6]!==u||e[7]!==d||e[8]!==l||e[9]!==s||e[10]!==t||e[11]!==m||e[12]!==i||e[13]!==r.id||e[14]!==((b=r.metadata)==null?void 0:b.name)||e[15]!==r.vfolderStatus){const P=se(r.id??"");k=h(P),x=tt([M&&!V?{key:"start-service",title:i("modelService.DeployAsService"),icon:a.jsx(An,{}),disabled:u?{reason:u}:!1,action:async()=>{m(P)}}:null,V?null:{key:"share",title:i("button.Share"),icon:a.jsx(Nn,{}),onClick:t},V?null:{key:"delete",title:i("data.folders.MoveToTrash"),icon:a.jsx(vt,{}),type:"danger",disabled:C?{reason:i("data.folders.CannotDeletePipelineFolder")}:!1,popConfirm:{title:i("data.folders.MoveToTrash"),description:((L=r==null?void 0:r.metadata)==null?void 0:L.name)??void 0,okText:i("button.Confirm"),cancelText:i("button.Cancel"),okButtonProps:{danger:!0},onConfirm:d}},V?{key:"restore",title:i("data.folders.Restore"),icon:a.jsx(zt,{}),disabled:C?{reason:i("data.folders.CannotRestorePipelineFolder")}:(r==null?void 0:r.vfolderStatus)!=="DELETE_PENDING"?{reason:i("data.folders.DeletionAlreadyStarted")}:!1,popConfirm:{title:i("data.folders.Restore"),description:((c=r==null?void 0:r.metadata)==null?void 0:c.name)??void 0,okText:i("button.Confirm"),cancelText:i("button.Cancel"),onConfirm:s}}:null,V?{key:"delete-forever",title:i("data.folders.Delete"),icon:a.jsx(Gt,{}),type:"danger",disabled:(r==null?void 0:r.vfolderStatus)!=="DELETE_PENDING"?{reason:i("data.folders.DeletionAlreadyStarted")}:!1,onClick:l}:null]),e[2]=h,e[3]=V,e[4]=M,e[5]=C,e[6]=u,e[7]=d,e[8]=l,e[9]=s,e[10]=t,e[11]=m,e[12]=i,e[13]=r.id,e[14]=(g=r.metadata)==null?void 0:g.name,e[15]=r.vfolderStatus,e[16]=k,e[17]=x}else k=e[16],x=e[17];const j=x;let S;e[18]!==F.fontSizeHeading5?(S={fontSize:F.fontSizeHeading5},e[18]=F.fontSizeHeading5,e[19]=S):S=e[19];let K;e[20]!==S||e[21]!==r?(K=a.jsx(fa,{vfolderNodeIdenticonFrgmt:r,style:S}),e[20]=S,e[21]=r,e[22]=K):K=e[22];const A=(I=r.metadata)==null?void 0:I.name,T=`${k.pathname}?${k.search}`;let D;e[23]!==k||e[24]!==o?(D=()=>{o(k)},e[23]=k,e[24]=o,e[25]=D):D=e[25];let N;return e[26]!==j||e[27]!==K||e[28]!==A||e[29]!==T||e[30]!==D?(N=a.jsx(wn,{icon:K,title:A,to:T,onTitleClick:D,actions:j,showActions:"always"}),e[26]=j,e[27]=K,e[28]=A,e[29]=T,e[30]=D,e[31]=N):N=e[31],N},Ka=n=>{"use memo";var V;const e=W.c(18),{host:r}=n,{t}=Y(),d=at();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let l;e[1]!==d?(l={queryKey:s,queryFn:()=>d.vfolder.list_hosts(),staleTime:3e5,refetchOnMount:!1,refetchOnWindowFocus:!1},e[1]=d,e[2]=l):l=e[2];const{data:m}=En(l);if(!r)return null;const u=(V=m==null?void 0:m.volume_info)==null?void 0:V[r],i=u==null?void 0:u.usage,F=i==null?void 0:i.percentage;let h,o,C,M;if(e[3]!==t||e[4]!==i||e[5]!==F){const k=F===void 0?t("data.usage.Unknown"):F<70?t("data.usage.Adequate"):F<90?t("data.usage.Caution"):t("data.usage.Insufficient");h=G,o=2,C="center",M=i?a.jsx(vn,{content:t("data.usage.HostStatusTooltip",{status:k}),icon:a.jsx(Bn,{percent:F}),style:{alignItems:"center"}}):null,e[3]=t,e[4]=i,e[5]=F,e[6]=h,e[7]=o,e[8]=C,e[9]=M}else h=e[6],o=e[7],C=e[8],M=e[9];let y;e[10]!==r?(y=a.jsx(te,{children:r}),e[10]=r,e[11]=y):y=e[11];let f;return e[12]!==h||e[13]!==o||e[14]!==C||e[15]!==M||e[16]!==y?(f=a.jsxs(h,{gap:o,align:C,children:[M,y]}),e[12]=h,e[13]=o,e[14]=C,e[15]=M,e[16]=y,e[17]=f):f=e[17],f},_a=n=>{"use memo";const e=W.c(13),{onOpen:r}=n,{t}=Y(),d=at();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let l;e[1]!==d?(l={queryKey:s,queryFn:()=>d.vfolder.list_hosts()},e[1]=d,e[2]=l):l=e[2];const{data:m}=Wt(l);if(!On($n((m==null?void 0:m.volume_info)??{}),Ea))return null;let i;e[3]!==t?(i=t("data.QuotaPerStorageVolume"),e[3]=t,e[4]=i):i=e[4];let F;e[5]!==r?(F=M=>{M.stopPropagation(),r()},e[5]=r,e[6]=F):F=e[6];let h;e[7]===Symbol.for("react.memo_cache_sentinel")?(h={cursor:"pointer"},e[7]=h):h=e[7];let o;e[8]!==F?(o={size:14,onClick:F,style:h},e[8]=F,e[9]=o):o=e[9];let C;return e[10]!==i||e[11]!==o?(C=a.jsx(Un,{title:i,iconProps:o}),e[10]=i,e[11]=o,e[12]=C):C=e[12],C},Aa=n=>a.jsx(q.Suspense,{fallback:null,children:a.jsx(_a,{...n})}),Na=()=>{"use memo";const n=W.c(8),e=at();let r;n[0]===Symbol.for("react.memo_cache_sentinel")?(r=["vhostInfo"],n[0]=r):r=n[0];let t;n[1]!==e?(t={queryKey:r,queryFn:()=>e.vfolder.list_hosts()},n[1]=e,n[2]=t):t=n[2];const{data:d}=Wt(t);let s;n[3]!==(d==null?void 0:d.volume_info)?(s=qn(Qn((d==null?void 0:d.volume_info)??{}),va),n[3]=d==null?void 0:d.volume_info,n[4]=s):s=n[4];const l=s;if(!l)return null;const[m,u]=l;let i;if(n[5]!==m||n[6]!==u){const F={id:m,...u};i=a.jsx(ga,{defaultVolumeInfo:F}),n[5]=m,n[6]=u,n[7]=i}else i=n[7];return i},La=n=>{"use memo";const e=W.c(16),{open:r,onCancel:t}=n,{t:d}=Y();let s;e[0]!==t?(s=o=>{o||t()},e[0]=t,e[1]=s):s=e[1];let l;e[2]!==d?(l=d("data.QuotaPerStorageVolume"),e[2]=d,e[3]=l):l=e[3];let m;e[4]!==d?(m=d("data.HostDetails"),e[4]=d,e[5]=m):m=e[5];let u;e[6]!==m?(u=a.jsx(G,{justify:"end",children:a.jsx(Rn,{title:m})}),e[6]=m,e[7]=u):u=e[7];let i;e[8]===Symbol.for("react.memo_cache_sentinel")?(i=a.jsx(q.Suspense,{fallback:a.jsx(Dt,{rows:3}),children:a.jsx(Na,{})}),e[8]=i):i=e[8];let F;e[9]!==u?(F=a.jsxs(et,{align:"stretch",gap:3,children:[u,i]}),e[9]=u,e[10]=F):F=e[10];let h;return e[11]!==r||e[12]!==s||e[13]!==l||e[14]!==F?(h=a.jsx(gt,{isOpen:r,onOpenChange:s,title:l,width:640,maskClosable:!1,footer:null,children:F}),e[11]=r,e[12]=s,e[13]=l,e[14]=F,e[15]=h):h=e[15],h},Pa=({vfoldersFrgmt:n,onRemoveRow:e,project:r,noDeployTooltip:t,...d})=>{"use memo";const{t:s}=Y(),{message:l}=mt.useApp(),[m]=Ot(),[u,i]=q.useState(null),{getErrorMessage:F}=nt(),h=qt(),o=Cn(),{upsertNotification:C}=Bt(),[M,y]=q.useState([]),[f,V]=q.useState(null),[k,x]=Q.useQueryLoader(Dn),[j,S]=q.useState(null),[K,A]=q.useState(!1),[T,D]=q.useState(!1),N=Q.useFragment(on,n),B=tt(N),[p]=Q.useMutation(rn),[b]=Q.useMutation(sn),L=(c,g)=>{var O;const I=(O=g==null?void 0:g.message.match(/sessions\(ids: (\[.*?\])\)/))==null?void 0:O[1],P=JSON.parse((I==null?void 0:I.replace(/'/g,'"'))||"[]");C({open:!0,key:`vfolder-error-${c==null?void 0:c.id}`,node:(c==null?void 0:c.notificationFrgmt)??null,description:F(g).replace(/\(ids[\s\S]*$/,""),extraDescription:Ln(P)?null:a.jsxs(et,{align:"stretch",children:[a.jsx(te,{color:"secondary",children:s("data.folders.MountedSessions")}),Z(P,$=>a.jsx(Pn,{href:"#",style:{fontWeight:"normal"},onClick:_=>{_.preventDefault(),h({pathname:o("session",{scope:"project"}),search:new URLSearchParams({sessionDetail:$}).toString()})},children:$},$))]})})};return a.jsxs(a.Fragment,{children:[a.jsx(Ut,{scroll:{x:"max-content"},resizable:!0,rowKey:c=>c.id,size:"small",dataSource:B,columns:[{key:"name",title:s("data.folders.Name"),dataIndex:["metadata","name"],required:!0,render:(c,g)=>a.jsx(Ta,{vfolder:g,noDeployTooltip:t,onShare:()=>{var I;((I=g==null?void 0:g.ownership)==null?void 0:I.userId)===(m==null?void 0:m.uuid)?i(se((g==null?void 0:g.id)??null)):V(g)},onDelete:()=>{const I=g==null?void 0:g.id;I&&p({variables:{vfolderId:se(I)},onCompleted:(P,O)=>{var $,_;if(O&&O.length>0){L(g,new Error((($=O[0])==null?void 0:$.message)??""));return}e==null||e(I),l.success(s("data.folders.MovedToTrashBin",{folderName:(_=g==null?void 0:g.metadata)==null?void 0:_.name}))},onError:P=>L(g,P)})},onRestore:()=>{const I=g==null?void 0:g.id;if(!I)return;const P=O=>{C({key:`vfolder-error-${I}`,node:(g==null?void 0:g.notificationFrgmt)??null,description:F(O),open:!0})};b({variables:{vfolderId:se(I)},onCompleted:(O,$)=>{var _,U;if($&&$.length>0){P(new Error(((_=$[0])==null?void 0:_.message)??""));return}e==null||e(I),l.success(s("data.folders.FolderRestored",{folderName:(U=g==null?void 0:g.metadata)==null?void 0:U.name}))},onError:P})},onDeleteForever:()=>{y(g?[g]:[])},onStartServiceFallback:I=>{x({},{fetchPolicy:"store-and-network"}),S(I),A(!0)}}),sorter:ae("name")},{key:"status",title:s("data.folders.Status"),dataIndex:"vfolderStatus",render:c=>a.jsx(Qt,{variant:Mn("vfolder",c),label:c}),sorter:ae("status")},{key:"host",title:a.jsxs(G,{gap:2,align:"center",children:[s("data.Host"),a.jsx(Aa,{onOpen:()=>D(!0)})]}),dataIndex:"host",render:c=>a.jsx(Ka,{host:c}),sorter:ae("host")},{key:"permissions",title:s("data.folders.MountPermission"),render:(c,g)=>a.jsx(cn,{vfolderFrgmt:g})},{key:"ownership_type",title:s("data.folders.Type"),dataIndex:["accessControl","ownershipType"],render:c=>c==="USER"?a.jsxs(G,{gap:2,children:[a.jsx(te,{children:s("data.User")}),a.jsx($t,{size:"1em"})]}):a.jsxs(G,{gap:2,children:[a.jsx(te,{children:s("data.Project")}),a.jsx(wt,{size:"1em"})]}),sorter:ae("ownership_type")},{key:"owner",title:s("data.folders.Owner"),render:(c,g)=>{var I,P,O,$,_,U,w;return((I=g.accessControl)==null?void 0:I.ownershipType)==="USER"?($=(O=(P=g==null?void 0:g.ownership)==null?void 0:P.user)==null?void 0:O.basicInfo)==null?void 0:$.email:(w=(U=(_=g==null?void 0:g.ownership)==null?void 0:_.project)==null?void 0:U.basicInfo)==null?void 0:w.name}},{key:"usage_mode",title:s("data.UsageMode"),dataIndex:["metadata","usageMode"],defaultHidden:!0,sorter:ae("usage_mode"),render:c=>{switch(c){case"GENERAL":return s("data.General");case"DATA":return s("webui.menu.Data");case"MODEL":return s("data.Models");default:return c}}},{key:"num_files",title:s("data.folders.NumberOfFiles"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"cur_size",title:s("data.folders.FolderUsage"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"max_files",title:s("data.folders.MaxFolderQuota"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"max_size",title:s("data.folders.MaxSize"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"cloneable",title:s("data.folders.Cloneable"),dataIndex:["metadata","cloneable"],defaultHidden:!0,sorter:ae("cloneable"),render:c=>s(c?"button.Yes":"button.No")},{key:"quota_scope_id",title:s("data.QuotaScopeId"),dataIndex:["metadata","quotaScopeId"],defaultHidden:!0,sorter:ae("quota_scope_id"),render:c=>c?a.jsx(Rt,{copyable:!0,children:c}):"-"},{key:"last_used",title:s("credential.LastUsed"),dataIndex:["metadata","lastUsed"],defaultHidden:!0,sorter:ae("last_used"),render:c=>c?At(c).format("ll LT"):"-"},{key:"created_at",title:s("data.folders.CreatedAt"),dataIndex:["metadata","createdAt"],defaultHidden:!0,sorter:ae("created_at"),render:c=>c?At(c).format("ll LT"):"-"}],...d}),a.jsx(en,{vfolderFrgmts:M,open:M.length>0,onRequestClose:c=>{c&&M.forEach(g=>e==null?void 0:e(g.id)),y([])}}),a.jsx(xn,{onRequestClose:()=>{i(null)},vfolderId:u,open:!!u}),a.jsx(Ma,{vfolderFrgmt:f,open:!!f,onLeaveFolder:c=>{e==null||e(c)},onRequestClose:()=>{V(null)}}),a.jsx(q.Suspense,{fallback:null,children:k!=null&&j!=null&&r!=null&&a.jsx(jn,{children:a.jsx(Tn,{open:K,project:r,vfolderId:j,queryRef:k,onClose:()=>A(!1),onDeployed:()=>A(!1)})})}),a.jsx(La,{open:T,onCancel:()=>D(!1)})]})};function Ea(n){return xt(n==null?void 0:n.capabilities,"quota")}function va(n){const[,e]=n;return xt(e==null?void 0:e.capabilities,"quota")}const Ba=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR","DELETE_COMPLETE"],Oa=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR"],Pt={status:{notIn:Ba}},Et={status:{in:Oa}},$a=["active","deleted"],wa=["all","general","data","automount","model"],Ua={general:{AND:[{name:{iNotStartsWith:"."}},{usageMode:{equals:"GENERAL"}}]},data:{usageMode:{equals:"DATA"}},automount:{name:{iStartsWith:"."}},model:{usageMode:{equals:"MODEL"}}},Ra=n=>{"use memo";var jt;const e=W.c(197),{project:r}=n,{t}=Y(),d=at(),[s,l]=Yn("table_column_overrides.ProjectAdminDataPage");let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=[],e[0]=m):m=e[0];const[u,i]=q.useState(m),[F,h]=ut(!1),{toggle:o}=h,[C,M]=ut(!1),{toggle:y}=M,[f,V]=ut(!1),{toggle:k}=V,[x,j]=ut(!1),{toggle:S}=j;let K;e[1]===Symbol.for("react.memo_cache_sentinel")?(K={current:1,pageSize:10},e[1]=K):K=e[1];const{baiPaginationOption:A,tablePaginationOption:T,setTablePaginationOption:D}=Jn(K);let N,B;e[2]===Symbol.for("react.memo_cache_sentinel")?(N={order:Ct(ja).withDefault("-created_at"),filter:Xn(qa),statusCategory:Ct($a).withDefault("active"),mode:Ct(wa).withDefault("all")},B={history:"replace"},e[2]=N,e[3]=B):(N=e[2],B=e[3]);const[p,b]=Zn(N,B);let L;e[4]!==p||e[5]!==T?(L={queryParams:p,tablePaginationOption:T},e[4]=p,e[5]=T,e[6]=L):L=e[6];let c;e[7]!==p.statusCategory||e[8]!==L?(c={[p.statusCategory]:L},e[7]=p.statusCategory,e[8]=L,e[9]=c):c=e[9];const g=q.useRef(c);let I,P;e[10]!==p||e[11]!==T?(I=()=>{g.current[p.statusCategory]={queryParams:p,tablePaginationOption:T}},P=[p,T],e[10]=p,e[11]=T,e[12]=I,e[13]=P):(I=e[12],P=e[13]),q.useEffect(I,P);const O=Ua[p.mode],[$,_]=ea(),U=p.statusCategory==="deleted"?Et:Pt;let w;e[14]!==O?(w=O?[O]:[],e[14]=O,e[15]=w):w=e[15];let H;e[16]!==p.filter?(H=p.filter?[p.filter]:[],e[16]=p.filter,e[17]=H):H=e[17];let ee;e[18]!==U||e[19]!==w||e[20]!==H?(ee={AND:[U,...w,...H]},e[18]=U,e[19]=w,e[20]=H,e[21]=ee):ee=e[21];const J=ee,z=r.id,re=A.offset,X=A.first;let ne;e[22]!==p.order?(ne=ta(p.order),e[22]=p.order,e[23]=ne):ne=e[23];let oe;e[24]!==A.first||e[25]!==A.offset||e[26]!==J||e[27]!==r.id||e[28]!==ne?(oe={projectId:z,offset:re,limit:X,filter:J,orderBy:ne,filterForActiveCount:Pt,filterForDeletedCount:Et},e[24]=A.first,e[25]=A.offset,e[26]=J,e[27]=r.id,e[28]=ne,e[29]=oe):oe=e[29];const ft=oe,pt=q.useDeferredValue(ft),Ze=q.useDeferredValue($);let lt;e[30]===Symbol.for("react.memo_cache_sentinel")?(lt=Jt,e[30]=lt):lt=e[30];const Ft=Ze===la?"store-and-network":"network-only";let st;e[31]!==Ze||e[32]!==Ft?(st={fetchPolicy:Ft,fetchKey:Ze},e[31]=Ze,e[32]=Ft,e[33]=st):st=e[33];const yt=Q.useLazyLoadQuery(lt,pt,st);let ie,E;e[34]!==yt?({projectVfolders:E,...ie}=yt,e[34]=yt,e[35]=ie,e[36]=E):(ie=e[35],E=e[36]);const mn=p.statusCategory;let de;e[37]!==b||e[38]!==D?(de=v=>{const R=g.current[v]||{};b(null),b({...R.queryParams,statusCategory:v},{history:"replace"}),D(R.tablePaginationOption||{current:1,pageSize:10}),i([])},e[37]=b,e[38]=D,e[39]=de):de=e[39];let ue;e[40]!==t?(ue=t("data.Active"),e[40]=t,e[41]=ue):ue=e[41];let ce;e[42]!==ue?(ce=["active",ue],e[42]=ue,e[43]=ce):ce=e[43];let me;e[44]!==t?(me=t("data.folders.TrashBin"),e[44]=t,e[45]=me):me=e[45];let ge;e[46]!==me?(ge=["deleted",me],e[46]=me,e[47]=ge):ge=e[47];let rt;e[48]!==ce||e[49]!==ge?(rt=[ce,ge],e[48]=ce,e[49]=ge,e[50]=rt):rt=e[50];const kt=rt;let fe;e[51]!==ie||e[52]!==p.statusCategory||e[53]!==kt?(fe=kt.map(v=>{var Kt;const[R,le]=v,Tt=((Kt=ie[R])==null?void 0:Kt.count)??0;return{key:R,label:le,endContent:Tt>0?a.jsx(Qt,{label:Tt,variant:p.statusCategory===R?"info":"neutral"}):void 0}}),e[51]=ie,e[52]=p.statusCategory,e[53]=kt,e[54]=fe):fe=e[54];let pe;e[55]!==p.statusCategory||e[56]!==de||e[57]!==fe?(pe=a.jsx(sa,{activeKey:mn,onChange:de,items:fe}),e[55]=p.statusCategory,e[56]=de,e[57]=fe,e[58]=pe):pe=e[58];let ot;e[59]===Symbol.for("react.memo_cache_sentinel")?(ot={flexShrink:1},e[59]=ot):ot=e[59];const gn=p.mode;let Fe;e[60]!==b||e[61]!==D?(Fe=v=>{b({mode:v.target.value}),D({current:1}),i([])},e[60]=b,e[61]=D,e[62]=Fe):Fe=e[62];let ye;e[63]!==d._config.enableModelFolders||e[64]!==d._config.fasttrackEndpoint||e[65]!==t?(ye=na([{label:t("data.All"),value:"all"},{label:t("data.General"),value:"general"},((jt=d==null?void 0:d._config)==null?void 0:jt.fasttrackEndpoint)&&{label:t("data.Pipeline"),value:"data"},{label:t("data.AutoMount"),value:"automount"},d._config.enableModelFolders&&{label:t("data.Models"),value:"model"}]),e[63]=d._config.enableModelFolders,e[64]=d._config.fasttrackEndpoint,e[65]=t,e[66]=ye):ye=e[66];let ke;e[67]!==p.mode||e[68]!==Fe||e[69]!==ye?(ke=a.jsx(ra,{optionType:"button",value:gn,onChange:Fe,options:ye}),e[67]=p.mode,e[68]=Fe,e[69]=ye,e[70]=ke):ke=e[70];let he;e[71]!==t?(he=t("data.folders.Name"),e[71]=t,e[72]=he):he=e[72];let Ve;e[73]!==he?(Ve={key:"name",propertyLabel:he,type:"string"},e[73]=he,e[74]=Ve):Ve=e[74];let Se;e[75]!==t?(Se=t("data.folders.Location"),e[75]=t,e[76]=Se):Se=e[76];let be;e[77]!==Se?(be={key:"host",propertyLabel:Se,type:"string"},e[77]=Se,e[78]=be):be=e[78];let Ie;e[79]!==Ve||e[80]!==be?(Ie=[Ve,be],e[79]=Ve,e[80]=be,e[81]=Ie):Ie=e[81];const ht=p.filter??void 0;let Ce;e[82]!==b||e[83]!==D?(Ce=v=>{b({filter:v??null}),D({current:1}),i([])},e[82]=b,e[83]=D,e[84]=Ce):Ce=e[84];let De;e[85]!==Ie||e[86]!==ht||e[87]!==Ce?(De=a.jsx(pa,{"data-testid":"vfolder-filter",filterProperties:Ie,value:ht,onChange:Ce}),e[85]=Ie,e[86]=ht,e[87]=Ce,e[88]=De):De=e[88];let Me;e[89]!==ke||e[90]!==De?(Me=a.jsxs(G,{gap:3,align:"start",style:ot,wrap:"wrap",children:[ke,De]}),e[89]=ke,e[90]=De,e[91]=Me):Me=e[91];let xe;e[92]!==p.statusCategory||e[93]!==u||e[94]!==t||e[95]!==o?(xe=u.length>0&&p.statusCategory==="active"&&a.jsxs(a.Fragment,{children:[a.jsx(Nt,{count:u.length,onClearSelection:()=>i([])}),a.jsx(Fa,{vfolderFrgmt:u,label:t("data.folders.MoveToTrash"),onClick:()=>{o()}})]}),e[92]=p.statusCategory,e[93]=u,e[94]=t,e[95]=o,e[96]=xe):xe=e[96];let je;e[97]!==p.statusCategory||e[98]!==u.length||e[99]!==t||e[100]!==S||e[101]!==y?(je=u.length>0&&p.statusCategory==="deleted"&&a.jsxs(a.Fragment,{children:[a.jsx(Nt,{count:u.length,onClearSelection:()=>i([])}),a.jsx(aa,{content:t("data.folders.Restore"),children:a.jsx(ct,{label:t("data.folders.Restore"),icon:a.jsx(zt,{}),onClick:()=>{y()}})}),a.jsx(ct,{label:t("data.folders.Delete"),tooltip:t("data.folders.Delete"),icon:a.jsx(Gt,{}),className:"bai-name-action-cell-danger",variant:"ghost",onClick:()=>{S()}})]}),e[97]=p.statusCategory,e[98]=u.length,e[99]=t,e[100]=S,e[101]=y,e[102]=je):je=e[102];const Vt=pt!==ft||Ze!==$;let Te;e[103]!==_?(Te=v=>{_(v)},e[103]=_,e[104]=Te):Te=e[104];let Ke;e[105]!==$||e[106]!==Vt||e[107]!==Te?(Ke=a.jsx(oa,{settingId:"project-admin-data",loading:Vt,value:$,onChange:Te}),e[105]=$,e[106]=Vt,e[107]=Te,e[108]=Ke):Ke=e[108];let it;e[109]===Symbol.for("react.memo_cache_sentinel")?(it=a.jsx(ia,{}),e[109]=it):it=e[109];let _e;e[110]!==t?(_e=t("data.CreateFolder"),e[110]=t,e[111]=_e):_e=e[111];let Ae;e[112]!==k?(Ae=()=>{k()},e[112]=k,e[113]=Ae):Ae=e[113];let Ne;e[114]!==_e||e[115]!==Ae?(Ne=a.jsx(da,{variant:"primary",icon:it,label:_e,onClick:Ae}),e[114]=_e,e[115]=Ae,e[116]=Ne):Ne=e[116];let Le;e[117]!==xe||e[118]!==je||e[119]!==Ke||e[120]!==Ne?(Le=a.jsxs(G,{gap:2,children:[xe,je,Ke,Ne]}),e[117]=xe,e[118]=je,e[119]=Ke,e[120]=Ne,e[121]=Le):Le=e[121];let Pe;e[122]!==Me||e[123]!==Le?(Pe=a.jsxs(G,{justify:"between",wrap:"wrap",gap:3,children:[Me,Le]}),e[122]=Me,e[123]=Le,e[124]=Pe):Pe=e[124];const fn=p.order,St=pt!==ft;let Ee;e[125]!==(E==null?void 0:E.edges)?(Ee=tt(Z(E==null?void 0:E.edges,"node")),e[125]=E==null?void 0:E.edges,e[126]=Ee):Ee=e[126];let ve;if(e[127]!==(E==null?void 0:E.edges)||e[128]!==u){let v;e[130]!==(E==null?void 0:E.edges)?(v=le=>{ua(le,tt(Z(E==null?void 0:E.edges,"node")),i)},e[130]=E==null?void 0:E.edges,e[131]=v):v=e[131];let R;e[132]!==u?(R=Z(u,Qa),e[132]=u,e[133]=R):R=e[133],ve={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(le){return{disabled:Ht(le.vfolderStatus)&&le.vfolderStatus!=="DELETE_PENDING"}},onChange:v,selectedRowKeys:R},e[127]=E==null?void 0:E.edges,e[128]=u,e[129]=ve}else ve=e[129];const bt=(E==null?void 0:E.count)??0;let Be;e[134]!==D||e[135]!==bt||e[136]!==T.current||e[137]!==T.pageSize?(Be={pageSize:T.pageSize,current:T.current,total:bt,onChange(v,R){Lt(v)&&Lt(R)&&D({current:v,pageSize:R})}},e[134]=D,e[135]=bt,e[136]=T.current,e[137]=T.pageSize,e[138]=Be):Be=e[138];let Oe;e[139]!==b?(Oe=v=>{b({order:v??null})},e[139]=b,e[140]=Oe):Oe=e[140];let $e;e[141]!==_?($e=v=>{i(R=>ca(R,le=>le.id!==v)),_()},e[141]=_,e[142]=$e):$e=e[142];let we;e[143]!==s||e[144]!==l?(we={columnOverrides:s,onColumnOverridesChange:l},e[143]=s,e[144]=l,e[145]=we):we=e[145];let Ue;e[146]!==r||e[147]!==p.order||e[148]!==St||e[149]!==Ee||e[150]!==ve||e[151]!==Be||e[152]!==Oe||e[153]!==$e||e[154]!==we?(Ue=a.jsx(Pa,{order:fn,loading:St,project:r,vfoldersFrgmt:Ee,rowSelection:ve,pagination:Be,onChangeOrder:Oe,onRemoveRow:$e,tableSettings:we}),e[146]=r,e[147]=p.order,e[148]=St,e[149]=Ee,e[150]=ve,e[151]=Be,e[152]=Oe,e[153]=$e,e[154]=we,e[155]=Ue):Ue=e[155];let Re;e[156]!==Pe||e[157]!==Ue?(Re=a.jsxs(et,{align:"stretch",gap:3,children:[Pe,Ue]}),e[156]=Pe,e[157]=Ue,e[158]=Re):Re=e[158];let qe;e[159]!==o||e[160]!==_?(qe=v=>{v&&(_(),i([])),o()},e[159]=o,e[160]=_,e[161]=qe):qe=e[161];let Qe;e[162]!==F||e[163]!==u||e[164]!==qe?(Qe=a.jsx(Va,{vfolderFrgmts:u,open:F,onRequestClose:qe}),e[162]=F,e[163]=u,e[164]=qe,e[165]=Qe):Qe=e[165];let He;e[166]!==y||e[167]!==_?(He=v=>{v&&(_(),i([])),y()},e[166]=y,e[167]=_,e[168]=He):He=e[168];let ze;e[169]!==C||e[170]!==u||e[171]!==He?(ze=a.jsx(Ia,{vfolderFrgmts:u,open:C,onRequestClose:He}),e[169]=C,e[170]=u,e[171]=He,e[172]=ze):ze=e[172];let Ge;e[173]!==S||e[174]!==_?(Ge=v=>{v&&(_(),i([])),S()},e[173]=S,e[174]=_,e[175]=Ge):Ge=e[175];let We;e[176]!==x||e[177]!==u||e[178]!==Ge?(We=a.jsx(en,{vfolderFrgmts:u,open:x,onRequestClose:Ge}),e[176]=x,e[177]=u,e[178]=Ge,e[179]=We):We=e[179];let Ye;e[180]!==t?(Ye=t("data.folders.ProjectAdminDataPageAlert"),e[180]=t,e[181]=Ye):Ye=e[181];let Je;e[182]!==k||e[183]!==_?(Je=v=>{k(),v&&_()},e[182]=k,e[183]=_,e[184]=Je):Je=e[184];let Xe;e[185]!==f||e[186]!==r||e[187]!==Ye||e[188]!==Je?(Xe=a.jsx(ma,{open:f,project:r,folderType:"project",alertMessage:Ye,onRequestClose:Je}),e[185]=f,e[186]=r,e[187]=Ye,e[188]=Je,e[189]=Xe):Xe=e[189];let dt;return e[190]!==pe||e[191]!==Re||e[192]!==Qe||e[193]!==ze||e[194]!==We||e[195]!==Xe?(dt=a.jsxs(a.Fragment,{children:[pe,Re,Qe,ze,We,Xe]}),e[190]=pe,e[191]=Re,e[192]=Qe,e[193]=ze,e[194]=We,e[195]=Xe,e[196]=dt):dt=e[196],dt},Ja=()=>{"use memo";const n=W.c(10),{t:e}=Y(),r=Hn();let t;n[0]!==r?(t=zn(r),n[0]=r,n[1]=t):t=n[1];const d=t;let s;n[2]!==e?(s=e("data.ProjectFolders"),n[2]=e,n[3]=s):s=n[3];let l;n[4]===Symbol.for("react.memo_cache_sentinel")?(l=a.jsx(Dt,{rows:4}),n[4]=l):l=n[4];let m;n[5]!==d?(m=a.jsx(Gn,{children:a.jsx(q.Suspense,{fallback:l,children:d?a.jsx(Ra,{project:d}):a.jsx(Dt,{rows:4})})}),n[5]=d,n[6]=m):m=n[6];let u;return n[7]!==s||n[8]!==m?(u=a.jsx(Wn,{title:s,children:m}),n[7]=s,n[8]=m,n[9]=u):u=n[9],u};function qa(n){return n}function Qa(n){return n.id}export{Ja as default};
//# sourceMappingURL=ProjectAdminDataPage-BnXu_c2y.js.map
