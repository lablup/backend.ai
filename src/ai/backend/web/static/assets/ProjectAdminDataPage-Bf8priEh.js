import{i as ce,r as ie,j as a,c2 as $l,N as yl,u as pe,Y as kl,z as ml,a as Ce,l as Z,am as se,bO as yt,c4 as wl,O as ye,a9 as hl,a3 as be,a4 as Ul,hH as kt,dl as Nl,cI as ue,t as Vl,d1 as ht,e4 as ql,dG as Vt,hI as Ql,hJ as Rl,at as ul,bq as St,aZ as Hl,aM as bt,hK as It,aT as cl,w as Ct,M as xl,e as Dt,Z as zl,_ as xt,hL as Mt,g as Gl,aR as Kt,v as El,hM as jt,ap as Tt,hN as _t,ak as Tl,ac as At,E as Lt,hD as Wl,hO as Nt,hP as Et,b0 as Yl,aN as Jl,an as Pt,L as vt,b as Bt,eJ as Ot,hQ as $t,b4 as Zl,bY as wt,f4 as Ut,bI as qt,aE as Qt,B as Rt,aV as Kl,aq as Ht,b5 as zt,A as Gt,X as Wt,cr as Yt,d as Jt,a8 as Zt,bF as Fl,bG as Xt,ca as Ml,ah as en,af as ln,aO as tn,aS as nn,ai as an,cb as Pl,s as sn,bN as vl,bh as rn,ab as on,de as dn,dx as un,P as cn,au as mn,ej as gn,al as fn,U as pn}from"./index-B-6GqBhJ.js";import{B as Xl}from"./BAIBulkErrorModal-CBEyVxbv.js";import{Q as Fn}from"./QuotaPerStorageVolumePanelCard-DnjJ5Nl_.js";import{V as yn}from"./VFolderNodeIdenticonV2-AK00ceM8.js";import{B as kn}from"./BAIGraphQLPropertyFilter-Bp1GJNAy.js";import"./usePrimaryColors-DChSm2xm.js";const et={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIVFolderDeleteButtonV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"VFolder",abstractKey:null};et.hash="4d44e5f0482b6a1b21c4aac58aa7d9f2";const hn=t=>{"use memo";const e=ce.c(8),{vfolderFrgmt:r,label:l,tooltip:d,isDisabled:s,onClick:n,size:g}=t,u=g===void 0?"md":g;let i;e[0]===Symbol.for("react.memo_cache_sentinel")?(i=et,e[0]=i):i=e[0],ie.useFragment(i,r);const F=d??l;let f;e[1]===Symbol.for("react.memo_cache_sentinel")?(f=a.jsx($l,{}),e[1]=f):f=e[1];let o;return e[2]!==s||e[3]!==l||e[4]!==n||e[5]!==u||e[6]!==F?(o=a.jsx(yl,{label:l,tooltip:F,icon:f,variant:"ghost",size:u,className:"bai-name-action-cell-danger",isDisabled:s,onClick:n}),e[2]=s,e[3]=l,e[4]=n,e[5]=u,e[6]=F,e[7]=o):o=e[7],o},lt=(function(){var t={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},d={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},n={defaultValue:null,kind:"LocalArgument",name:"projectId"},g={kind:"Variable",name:"projectId",variableName:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},g],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},F={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[f],D={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},g],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:o,storageKey:null},_={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},g],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:o,storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[t,e,r,l,d,s,n],kind:"Fragment",metadata:null,name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:u,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:i,action:"THROW"},F,{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},f],storageKey:null},D,_],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,d,l,t,s,e,r],kind:"Operation",name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:u,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[i,F,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[V,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},i],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[V],storageKey:null},i],storageKey:null}],storageKey:null},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[S,T,V,y,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},i,y,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[V,i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[S],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[S,T,y,V],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},f],storageKey:null},D,_]},params:{cacheID:"8052e04b636ce630b2aac1d9ed54f299",id:null,metadata:{},name:"ProjectAdminDataPageQuery",operationKind:"query",text:`query ProjectAdminDataPageQuery(
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
`}}})();lt.hash="1f6d597c1b6abd207b4639a11dd0a327";const tt=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkPurgeVFoldersV2Payload",kind:"LinkedField",name:"bulkPurgeVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"successes",storageKey:null},{alias:null,args:null,concreteType:"BulkPurgeVFolderV2Error",kind:"LinkedField",name:"failed",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"purgedCount",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"DeleteForeverVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"DeleteForeverVFolderModalV2Mutation",selections:e},params:{cacheID:"1fffaa3e9f288133c1cec83218ab971c",id:null,metadata:{},name:"DeleteForeverVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteForeverVFolderModalV2Mutation(
  $input: BulkPurgeVFoldersV2Input!
) {
  bulkPurgeVfoldersV2(input: $input) {
    successes @since(version: "26.9.0")
    failed @since(version: "26.4.4") {
      vfolderId
      message
    }
    purgedCount @deprecatedSince(version: "26.9.0")
  }
}
`}}})();tt.hash="10a513e45393cfbdcb39e6de438bec7d";const nt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteForeverVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};nt.hash="af117d7a409739259841dcfce2d2a493";const at=t=>{"use memo";var me,Fe,Y,ge;const e=ce.c(96);let r,l,d,s;e[0]!==t?({vfolderFrgmts:s,onRequestClose:l,open:d,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d,e[4]=s):(r=e[1],l=e[2],d=e[3],s=e[4]);const{t:n}=pe(),{message:g}=kl.useApp(),{getErrorMessage:u}=ml(),i=Ce();let F;e[5]!==i?(F=i.supports("bulk-mutation-per-id-results"),e[5]=i,e[6]=F):F=e[6];const f=F,[o,D]=Z.useState(null);let _;e[7]===Symbol.for("react.memo_cache_sentinel")?(_=nt,e[7]=_):_=e[7];const V=ie.useFragment(_,s);let S;e[8]===Symbol.for("react.memo_cache_sentinel")?(S=tt,e[8]=S):S=e[8];const[T,y]=ie.useMutation(S);let M,K,b,k,P,j,I,v,B,p,C,N,c,m,h,A,O;if(e[9]!==y||e[10]!==r||e[11]!==l||e[12]!==d||e[13]!==n||e[14]!==V){k=V??[],K=k.length===1?((Fe=(me=k[0])==null?void 0:me.metadata)==null?void 0:Fe.name)??n("button.Delete"):n("button.Delete");let X;e[32]!==n?(X=n("data.folders.Name"),e[32]=n,e[33]=X):X=e[33];let q;e[34]!==X?(q={key:"name",title:X,dataIndex:"name"},e[34]=X,e[35]=q):q=e[35];let J;e[36]!==n?(J=n("data.folders.ErrorMessage"),e[36]=n,e[37]=J):J=e[37];let ee;e[38]!==J?(ee={key:"message",title:J,dataIndex:"message"},e[38]=J,e[39]=ee):ee=e[39];let le;e[40]!==q||e[41]!==ee?(le=[q,ee],e[40]=q,e[41]=ee,e[42]=le):le=e[42],b=le,M=yt,c=r,m=!!d,e[43]!==l?(h=L=>{L||l==null||l(!1)},e[43]=l,e[44]=h):h=e[44],e[45]!==n?(A=n("dialog.title.DeleteForever"),e[45]=n,e[46]=A):A=e[46],O=k.length===1?n("data.folders.DeleteForeverDescription",{folderName:((ge=(Y=k[0])==null?void 0:Y.metadata)==null?void 0:ge.name)??""}):void 0,P=!1,e[47]!==n?(j=n("data.folders.DeleteForever"),e[47]=n,e[48]=j):j=e[48],e[49]!==n?(I=n("button.Cancel"),e[49]=n,e[50]=I):I=e[50],v=y,B=se(k,Vn),p=!0,C=K,N=n("dialog.PleaseTypeToConfirm",{confirmText:K}),e[9]=y,e[10]=r,e[11]=l,e[12]=d,e[13]=n,e[14]=V,e[15]=M,e[16]=K,e[17]=b,e[18]=k,e[19]=P,e[20]=j,e[21]=I,e[22]=v,e[23]=B,e[24]=p,e[25]=C,e[26]=N,e[27]=c,e[28]=m,e[29]=h,e[30]=A,e[31]=O}else M=e[15],K=e[16],b=e[17],k=e[18],P=e[19],j=e[20],I=e[21],v=e[22],B=e[23],p=e[24],C=e[25],N=e[26],c=e[27],m=e[28],h=e[29],A=e[30],O=e[31];let E;e[51]!==K?(E={placeholder:K},e[51]=K,e[52]=E):E=e[52];let x;e[53]!==n?(x=n("dialog.warning.CannotBeUndone"),e[53]=n,e[54]=x):x=e[54];let Q;e[55]!==T||e[56]!==u||e[57]!==g||e[58]!==l||e[59]!==k||e[60]!==f||e[61]!==n?(Q=()=>{if(k.length===0){l==null||l(!1);return}const X=se(k,Sn);T({variables:{input:{ids:X}},onCompleted:(q,J)=>{var L,Ie,fe,te,oe,ke;if(J&&J.length>0){const de=J[0];g.error((de==null?void 0:de.message)??u(de));return}const ee=f?((Ie=(L=q==null?void 0:q.bulkPurgeVfoldersV2)==null?void 0:L.successes)==null?void 0:Ie.length)??0:((fe=q==null?void 0:q.bulkPurgeVfoldersV2)==null?void 0:fe.purgedCount)??0,le=((te=q==null?void 0:q.bulkPurgeVfoldersV2)==null?void 0:te.failed)??[];if(le.length>0){const de=wl(se(k,bn));D({total:k.length,failures:se(le,he=>({key:he.vfolderId,name:de[he.vfolderId]??he.vfolderId,message:he.message}))})}else ee===0&&g.error(n("data.folders.FailedToDeleteFolders",{folderNames:se(k,In).join(", ")}));ee!==0&&(k.length===1?g.success(n("data.folders.FolderDeletedForever",{folderName:(ke=(oe=k[0])==null?void 0:oe.metadata)==null?void 0:ke.name})):g.success(n("data.folders.MultipleFolderDeletedForever",{count:ee,total:k.length})),l==null||l(!0))},onError:q=>{g.error(u(q))}})},e[55]=T,e[56]=u,e[57]=g,e[58]=l,e[59]=k,e[60]=f,e[61]=n,e[62]=Q):Q=e[62];let U;e[63]!==M||e[64]!==P||e[65]!==j||e[66]!==I||e[67]!==v||e[68]!==B||e[69]!==p||e[70]!==C||e[71]!==N||e[72]!==E||e[73]!==x||e[74]!==Q||e[75]!==c||e[76]!==m||e[77]!==h||e[78]!==A||e[79]!==O?(U=a.jsx(M,{...c,isOpen:m,onOpenChange:h,title:A,description:O,maskClosable:P,okText:j,cancelText:I,confirmLoading:v,items:B,requireConfirmInput:p,confirmText:C,inputLabel:N,inputProps:E,cannotBeUndoneText:x,onOk:Q}),e[63]=M,e[64]=P,e[65]=j,e[66]=I,e[67]=v,e[68]=B,e[69]=p,e[70]=C,e[71]=N,e[72]=E,e[73]=x,e[74]=Q,e[75]=c,e[76]=m,e[77]=h,e[78]=A,e[79]=O,e[80]=U):U=e[80];const z=!!o,re=(o==null?void 0:o.failures.length)??0,ae=(o==null?void 0:o.total)??0;let w;e[81]!==n||e[82]!==re||e[83]!==ae?(w=n("data.folders.DeleteFailureDescription",{failed:re,total:ae}),e[81]=n,e[82]=re,e[83]=ae,e[84]=w):w=e[84];let G;e[85]!==(o==null?void 0:o.failures)?(G=(o==null?void 0:o.failures)??[],e[85]=o==null?void 0:o.failures,e[86]=G):G=e[86];let W;e[87]===Symbol.for("react.memo_cache_sentinel")?(W=()=>D(null),e[87]=W):W=e[87];let R;e[88]!==b||e[89]!==z||e[90]!==w||e[91]!==G?(R=a.jsx(Xl,{open:z,alertDescription:w,columns:b,dataSource:G,onRequestClose:W}),e[88]=b,e[89]=z,e[90]=w,e[91]=G,e[92]=R):R=e[92];let H;return e[93]!==U||e[94]!==R?(H=a.jsxs(a.Fragment,{children:[U,R]}),e[93]=U,e[94]=R,e[95]=H):H=e[95],H};function Vn(t){var e;return{key:t.id??"",label:((e=t.metadata)==null?void 0:e.name)??""}}function Sn(t){return ye(t.id)}function bn(t){var e;return[ye(t.id),(e=t.metadata)==null?void 0:e.name]}function In(t){var e;return(e=t==null?void 0:t.metadata)==null?void 0:e.name}const st=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkDeleteVFoldersV2Payload",kind:"LinkedField",name:"bulkDeleteVfoldersV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"BulkDeleteVFolderV2Error",kind:"LinkedField",name:"failed",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deletedCount",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"DeleteVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"DeleteVFolderModalV2Mutation",selections:e},params:{cacheID:"ee3e97a85af9c6b5d681ea26074a160b",id:null,metadata:{},name:"DeleteVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteVFolderModalV2Mutation(
  $input: BulkDeleteVFoldersV2Input!
) {
  bulkDeleteVfoldersV2(input: $input) {
    items @since(version: "26.9.0") {
      id
    }
    failed @since(version: "26.9.0") {
      vfolderId
      message
    }
    deletedCount @deprecatedSince(version: "26.9.0")
  }
}
`}}})();st.hash="43ec619764a3c87bdd5b6bf723e7080c";const rt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};rt.hash="c1b7e252a2275b9b74d0576b46e2f299";const Cn=t=>{"use memo";var re,ae;const e=ce.c(78);let r,l,d;e[0]!==t?({vfolderFrgmts:d,onRequestClose:l,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d):(r=e[1],l=e[2],d=e[3]);const{t:s}=pe(),{message:n}=kl.useApp(),{getErrorMessage:g}=ml(),u=Ce();let i;e[4]!==u?(i=u.supports("bulk-mutation-per-id-results"),e[4]=u,e[5]=i):i=e[5];const F=i,[f,o]=Z.useState(null);let D;e[6]===Symbol.for("react.memo_cache_sentinel")?(D=rt,e[6]=D):D=e[6];const _=ie.useFragment(D,d);let V;e[7]===Symbol.for("react.memo_cache_sentinel")?(V=st,e[7]=V):V=e[7];const[S,T]=ie.useMutation(V);let y,M,K,b,k,P,j,I,v,B,p,C,N;if(e[8]!==r||e[9]!==S||e[10]!==g||e[11]!==T||e[12]!==n||e[13]!==l||e[14]!==F||e[15]!==s||e[16]!==_){const w=_??[];let G;e[30]!==s?(G=s("data.folders.Name"),e[30]=s,e[31]=G):G=e[31];let W;e[32]!==G?(W={key:"name",title:G,dataIndex:"name"},e[32]=G,e[33]=W):W=e[33];let R;e[34]!==s?(R=s("data.folders.ErrorMessage"),e[34]=s,e[35]=R):R=e[35];let H;e[36]!==R?(H={key:"message",title:R,dataIndex:"message"},e[36]=R,e[37]=H):H=e[37];let me;e[38]!==W||e[39]!==H?(me=[W,H],e[38]=W,e[39]=H,e[40]=me):me=e[40],K=me,M=hl,B=r.open,e[41]!==l?(p=Fe=>{Fe||l==null||l(!1)},e[41]=l,e[42]=p):p=e[42],e[43]!==s?(C=s("data.folders.MoveToTrash"),e[43]=s,e[44]=C):C=e[44],N=!1,e[45]!==s?(b=s("data.folders.Delete"),e[45]=s,e[46]=b):b=e[46],e[47]===Symbol.for("react.memo_cache_sentinel")?(k={danger:!0},e[47]=k):k=e[47],P=T,j=()=>{if(w.length===0){l==null||l(!1);return}const Fe=se(w,Dn);S({variables:{input:{ids:Fe}},onCompleted:(Y,ge)=>{var J,ee,le,L,Ie,fe;if(ge&&ge.length>0){const te=ge[0];n.error((te==null?void 0:te.message)??g(te));return}const X=F?((ee=(J=Y==null?void 0:Y.bulkDeleteVfoldersV2)==null?void 0:J.items)==null?void 0:ee.length)??0:((le=Y==null?void 0:Y.bulkDeleteVfoldersV2)==null?void 0:le.deletedCount)??0,q=((L=Y==null?void 0:Y.bulkDeleteVfoldersV2)==null?void 0:L.failed)??[];if(q.length>0){const te=wl(se(w,xn));o({total:w.length,failures:se(q,oe=>({key:oe.vfolderId,name:te[oe.vfolderId]??oe.vfolderId,message:oe.message}))})}else X===0&&n.error(s("data.folders.FailedToDeleteFolders",{folderNames:se(w,Mn).join(", ")}));X!==0&&(w.length===1?n.success(s("data.folders.FolderDeleted",{folderName:(fe=(Ie=w[0])==null?void 0:Ie.metadata)==null?void 0:fe.name})):n.success(s("data.folders.MultipleFolderDeleted",{count:X,total:w.length})),l==null||l(!0))},onError:Y=>{n.error(g(Y))}})},I=r,y=be,v=w.length===1?s("data.folders.MoveToTrashDescription",{folderName:(ae=(re=w[0])==null?void 0:re.metadata)==null?void 0:ae.name}):s("data.folders.MoveToTrashMultipleDescription",{folderLength:w.length}),e[8]=r,e[9]=S,e[10]=g,e[11]=T,e[12]=n,e[13]=l,e[14]=F,e[15]=s,e[16]=_,e[17]=y,e[18]=M,e[19]=K,e[20]=b,e[21]=k,e[22]=P,e[23]=j,e[24]=I,e[25]=v,e[26]=B,e[27]=p,e[28]=C,e[29]=N}else y=e[17],M=e[18],K=e[19],b=e[20],k=e[21],P=e[22],j=e[23],I=e[24],v=e[25],B=e[26],p=e[27],C=e[28],N=e[29];let c;e[48]!==y||e[49]!==v?(c=a.jsx(y,{children:v}),e[48]=y,e[49]=v,e[50]=c):c=e[50];let m;e[51]!==M||e[52]!==b||e[53]!==k||e[54]!==P||e[55]!==j||e[56]!==I||e[57]!==c||e[58]!==B||e[59]!==p||e[60]!==C||e[61]!==N?(m=a.jsx(M,{isOpen:B,onOpenChange:p,title:C,maskClosable:N,okText:b,okButtonProps:k,confirmLoading:P,onOk:j,...I,children:c}),e[51]=M,e[52]=b,e[53]=k,e[54]=P,e[55]=j,e[56]=I,e[57]=c,e[58]=B,e[59]=p,e[60]=C,e[61]=N,e[62]=m):m=e[62];const h=!!f,A=(f==null?void 0:f.failures.length)??0,O=(f==null?void 0:f.total)??0;let E;e[63]!==s||e[64]!==A||e[65]!==O?(E=s("data.folders.DeleteFailureDescription",{failed:A,total:O}),e[63]=s,e[64]=A,e[65]=O,e[66]=E):E=e[66];let x;e[67]!==(f==null?void 0:f.failures)?(x=(f==null?void 0:f.failures)??[],e[67]=f==null?void 0:f.failures,e[68]=x):x=e[68];let Q;e[69]===Symbol.for("react.memo_cache_sentinel")?(Q=()=>o(null),e[69]=Q):Q=e[69];let U;e[70]!==K||e[71]!==h||e[72]!==E||e[73]!==x?(U=a.jsx(Xl,{open:h,alertDescription:E,columns:K,dataSource:x,onRequestClose:Q}),e[70]=K,e[71]=h,e[72]=E,e[73]=x,e[74]=U):U=e[74];let z;return e[75]!==m||e[76]!==U?(z=a.jsxs(a.Fragment,{children:[m,U]}),e[75]=m,e[76]=U,e[77]=z):z=e[77],z};function Dn(t){return ye(t.id)}function xn(t){var e;return[ye(t.id),(e=t.metadata)==null?void 0:e.name]}function Mn(t){var e;return(e=t==null?void 0:t.metadata)==null?void 0:e.name}const ot=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"RestoreVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"RestoreVFolderModalV2Mutation",selections:e},params:{cacheID:"14d669a32252e8429330552a9eb6e82e",id:null,metadata:{},name:"RestoreVFolderModalV2Mutation",operationKind:"mutation",text:`mutation RestoreVFolderModalV2Mutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();ot.hash="0efe06c3f5b800e9b582b9d254f35ed3";const it={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"RestoreVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};it.hash="3f78d6da02312aa15054515c21edda60";const Kn=t=>{"use memo";var P,j,I,v,B,p;const e=ce.c(34);let r,l,d;e[0]!==t?({vfolderFrgmts:d,onRequestClose:l,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d):(r=e[1],l=e[2],d=e[3]);const{t:s}=pe(),{upsertNotification:n}=Ul(),{getErrorMessage:g}=ml(),u=ie.useRelayEnvironment(),[i,F]=Z.useState(!1);let f;e[4]===Symbol.for("react.memo_cache_sentinel")?(f=it,e[4]=f):f=e[4];const o=ie.useFragment(f,d);let D;e[5]!==u?(D=C=>new Promise((N,c)=>{kt.commitMutation(u,{mutation:ot,variables:{vfolderId:ye(C)},onCompleted:(m,h)=>{if(h&&h.length>0){c(h[0]);return}N()},onError:m=>c(m)})}),e[5]=u,e[6]=D):D=e[6];const _=D,V=r.open;let S;e[7]!==l?(S=C=>{C||l==null||l(!1)},e[7]=l,e[8]=S):S=e[8];let T;e[9]!==s?(T=s("data.folders.Restore"),e[9]=s,e[10]=T):T=e[10];let y;e[11]!==s?(y=s("data.folders.Restore"),e[11]=s,e[12]=y):y=e[12];let M;e[13]!==g||e[14]!==l||e[15]!==_||e[16]!==s||e[17]!==n||e[18]!==o?(M=()=>{const C=se(o,N=>_(N.id).catch(c=>(n({message:g(c),description:c==null?void 0:c.description,open:!0}),Promise.reject(c))));F(!0),Promise.allSettled(C).then(N=>{var m,h;F(!1);const c=N.every(jn);c&&((o==null?void 0:o.length)===1?Nl.success(s("data.folders.FolderRestored",{folderName:(h=(m=o==null?void 0:o[0])==null?void 0:m.metadata)==null?void 0:h.name})):Nl.success(s("data.folders.MultipleFolderRestored",{folderLength:o==null?void 0:o.length}))),l==null||l(c)})},e[13]=g,e[14]=l,e[15]=_,e[16]=s,e[17]=n,e[18]=o,e[19]=M):M=e[19];let K;e[20]!==s||e[21]!==((j=(P=o==null?void 0:o[0])==null?void 0:P.metadata)==null?void 0:j.name)||e[22]!==(o==null?void 0:o.length)?(K=(o==null?void 0:o.length)===1?s("data.folders.RestoreDescription",{folderName:(v=(I=o==null?void 0:o[0])==null?void 0:I.metadata)==null?void 0:v.name}):s("data.folders.RestoreMultipleDescription",{folderLength:o==null?void 0:o.length}),e[20]=s,e[21]=(p=(B=o==null?void 0:o[0])==null?void 0:B.metadata)==null?void 0:p.name,e[22]=o==null?void 0:o.length,e[23]=K):K=e[23];let b;e[24]!==K?(b=a.jsx(be,{children:K}),e[24]=K,e[25]=b):b=e[25];let k;return e[26]!==r||e[27]!==i||e[28]!==S||e[29]!==T||e[30]!==y||e[31]!==M||e[32]!==b?(k=a.jsx(hl,{isOpen:V,onOpenChange:S,title:T,maskClosable:!1,okText:y,confirmLoading:i,onOk:M,...r,children:b}),e[26]=r,e[27]=i,e[28]=S,e[29]=T,e[30]=y,e[31]=M,e[32]=b,e[33]=k):k=e[33],k};function jn(t){return t.status==="fulfilled"}const dt=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"VFolderNodesV2RestoreMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"VFolderNodesV2RestoreMutation",selections:e},params:{cacheID:"fc05c41196eaa2483ea656725bdc2909",id:null,metadata:{},name:"VFolderNodesV2RestoreMutation",operationKind:"mutation",text:`mutation VFolderNodesV2RestoreMutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();dt.hash="786c5ce4389066e04eac9355a031686d";const ut=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"DeleteVFolderV2Payload",kind:"LinkedField",name:"deleteVfolderV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"VFolderNodesV2DeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"VFolderNodesV2DeleteMutation",selections:e},params:{cacheID:"267b27dfe24bf987d3e29f11f2c03074",id:null,metadata:{},name:"VFolderNodesV2DeleteMutation",operationKind:"mutation",text:`mutation VFolderNodesV2DeleteMutation(
  $vfolderId: UUID!
) {
  deleteVfolderV2(vfolderId: $vfolderId) {
    id
  }
}
`}}})();ut.hash="6a3f03b7eacad2630bd79321d5da93d7";const ct=(function(){var t={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"VFolderNodesV2Fragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[t],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderPermissionCellV2Fragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonV2Fragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"BAINodeNotificationItemFragment"}],type:"Node",abstractKey:"__isNode"},kind:"AliasedInlineFragmentSpread",name:"notificationFrgmt"}],type:"VFolder",abstractKey:null}})();ct.hash="07611fcd2a8e6b5fb66ca14bf652e541";const mt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SharedFolderPermissionInfoModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderPermissionCellV2Fragment"}],type:"VFolder",abstractKey:null};mt.hash="5a18839a6dffea1a5a545710cc7e8bda";const gt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"VFolderPermissionCellV2Fragment",selections:[{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};gt.hash="a517ea6cc8c2fc65f02d29454cd0a8c8";const ft=t=>{"use memo";var k;const e=ce.c(27);let r,l;e[0]!==t?({vfolderFrgmt:l,...r}=t,e[0]=t,e[1]=r,e[2]=l):(r=e[1],l=e[2]);const{t:d}=pe();let s;e[3]===Symbol.for("react.memo_cache_sentinel")?(s=gt,e[3]=s):s=e[3];const n=ie.useFragment(s,l??null);let g;e[4]!==d?(g=d("data.ReadOnly"),e[4]=d,e[5]=g):g=e[5];let u;e[6]!==g?(u={label:g,icon:"R"},e[6]=g,e[7]=u):u=e[7];let i;e[8]!==d?(i=d("data.ReadWrite"),e[8]=d,e[9]=i):i=e[9];let F;e[10]!==i?(F={label:i,icon:"RW"},e[10]=i,e[11]=F):F=e[11];let f;e[12]!==u||e[13]!==F?(f={ro:u,rw:F},e[12]=u,e[13]=F,e[14]=f):f=e[14];const o=f,D=((k=n==null?void 0:n.accessControl)==null?void 0:k.permission)==="READ_ONLY"?"ro":"rw",_=o[D];let V;e[15]!==_?(V={permissionInfo:_},e[15]=_,e[16]=V):V=e[16];const{permissionInfo:S}=V,T=S==null?void 0:S.label;let y;e[17]!==T?(y=a.jsx(Vl,{children:T}),e[17]=T,e[18]=y):y=e[18];let M;e[19]!==(S==null?void 0:S.icon)?(M=se(S==null?void 0:S.icon,Tn),e[19]=S==null?void 0:S.icon,e[20]=M):M=e[20];let K;e[21]!==M?(K=a.jsx(ue,{children:M}),e[21]=M,e[22]=K):K=e[22];let b;return e[23]!==r||e[24]!==y||e[25]!==K?(b=a.jsxs(ue,{gap:2,...r,children:[y,K]}),e[23]=r,e[24]=y,e[25]=K,e[26]=b):b=e[26],b};function Tn(t){return a.jsx(Vl,{code:!0,children:ht(t)},t)}const _n=t=>{"use memo";var E,x,Q,U,z,re;const e=ce.c(63);let r,l,d,s;e[0]!==t?({vfolderFrgmt:s,onRequestClose:d,onLeaveFolder:l,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d,e[4]=s):(r=e[1],l=e[2],d=e[3],s=e[4]);const{t:n}=pe(),{message:g}=kl.useApp(),{getErrorMessage:u}=ml(),[i]=ql(),F=Ce();let f;e[5]===Symbol.for("react.memo_cache_sentinel")?(f=mt,e[5]=f):f=e[5];const o=ie.useFragment(f,s);let D;e[6]!==F?(D={mutationFn:ae=>{const{folderId:w}=ae;return F.vfolder.leave_invited(w)}},e[6]=F,e[7]=D):D=e[7];const _=Vt(D),V=((E=o==null?void 0:o.accessControl)==null?void 0:E.ownershipType)==="USER",S=r.open;let T;e[8]!==d?(T=ae=>{ae||d()},e[8]=d,e[9]=T):T=e[9];let y;e[10]!==n?(y=n("data.SharedFolderPermission"),e[10]=n,e[11]=y):y=e[11];let M;e[12]!==V||e[13]!==n?(M=n(V?"data.folders.SharedFolderAlertDesc":"data.folders.ProjectFolderAlertDesc"),e[12]=V,e[13]=n,e[14]=M):M=e[14];let K;e[15]!==M?(K=a.jsx(Ct,{status:"info",title:M}),e[15]=M,e[16]=K):K=e[16];let b;e[17]!==n?(b=n("data.FolderInfo"),e[17]=n,e[18]=b):b=e[18];let k;e[19]!==n?(k=n("data.folders.Name"),e[19]=n,e[20]=k):k=e[20];const P=((x=o==null?void 0:o.metadata)==null?void 0:x.name)??"";let j;e[21]!==P?(j=a.jsx(Vl,{copyable:!0,children:P}),e[21]=P,e[22]=j):j=e[22];let I;e[23]!==j||e[24]!==k?(I=a.jsx(xl,{label:k,children:j}),e[23]=j,e[24]=k,e[25]=I):I=e[25];let v;e[26]!==n?(v=n("data.folders.Type"),e[26]=n,e[27]=v):v=e[27];let B;e[28]!==V||e[29]!==n?(B=V?a.jsxs(ue,{gap:2,children:[a.jsx(be,{children:n("data.User")}),a.jsx(Ql,{size:"1em"})]}):a.jsxs(ue,{gap:2,children:[a.jsx(be,{children:n("data.Project")}),a.jsx(Rl,{size:"1em"})]}),e[28]=V,e[29]=n,e[30]=B):B=e[30];let p;e[31]!==v||e[32]!==B?(p=a.jsx(xl,{label:v,children:B}),e[31]=v,e[32]=B,e[33]=p):p=e[33];let C;e[34]!==n?(C=n("data.folders.Owner"),e[34]=n,e[35]=C):C=e[35];const N=((Q=o==null?void 0:o.ownership)==null?void 0:Q.creatorEmail)||((re=(z=(U=o==null?void 0:o.ownership)==null?void 0:U.user)==null?void 0:z.basicInfo)==null?void 0:re.email);let c;e[36]!==C||e[37]!==N?(c=a.jsx(xl,{label:C,children:N}),e[36]=C,e[37]=N,e[38]=c):c=e[38];let m;e[39]!==I||e[40]!==p||e[41]!==c||e[42]!==b?(m=a.jsxs(Dt,{title:b,columns:2,children:[I,p,c]}),e[39]=I,e[40]=p,e[41]=c,e[42]=b,e[43]=m):m=e[43];let h;e[44]!==i||e[45]!==u||e[46]!==V||e[47]!==_||e[48]!==g||e[49]!==l||e[50]!==d||e[51]!==n||e[52]!==o?(h=V?a.jsxs(ul,{align:"stretch",gap:4,children:[a.jsx(St,{level:5,children:n("data.folders.Permission")}),a.jsx(Hl,{bordered:!0,pagination:!1,dataSource:cl([o]),columns:[{key:"userName",title:n("general.E-Mail"),render:()=>i.email},{key:"permissions",title:n("data.folders.MountPermission"),render:An},{key:"control",title:n("data.folders.Control"),render:(ae,w)=>{var G;return a.jsx(ue,{justify:"center",children:a.jsx(bt,{title:n("data.invitation.LeaveSharedFolderDesc",{folderName:(G=w==null?void 0:w.metadata)==null?void 0:G.name}),onConfirm:()=>{const W=w==null?void 0:w.id,R=W?ye(W):null;R&&W&&_.mutate({folderId:R},{onSuccess:()=>{l==null||l(W),g.success(n("data.invitation.SuccessfullyLeftSharedFolder")),d(!0)},onError:H=>{g.error(u(H)),d()}})},children:a.jsx(yl,{label:n("data.invitation.LeaveSharedFolder"),tooltip:n("data.invitation.LeaveSharedFolder"),size:"sm",variant:"ghost",icon:a.jsx(It,{}),className:"bai-name-action-cell-danger"})})})}}]})]}):null,e[44]=i,e[45]=u,e[46]=V,e[47]=_,e[48]=g,e[49]=l,e[50]=d,e[51]=n,e[52]=o,e[53]=h):h=e[53];let A;e[54]!==m||e[55]!==h||e[56]!==K?(A=a.jsxs(ul,{align:"stretch",gap:5,children:[K,m,h]}),e[54]=m,e[55]=h,e[56]=K,e[57]=A):A=e[57];let O;return e[58]!==r||e[59]!==A||e[60]!==T||e[61]!==y?(O=a.jsx(hl,{isOpen:S,onOpenChange:T,title:y,maskClosable:!1,footer:null,...r,children:A}),e[58]=r,e[59]=A,e[60]=T,e[61]=y,e[62]=O):O=e[62],O};function An(t,e){return a.jsx(ft,{vfolderFrgmt:e})}const jl=["name","host","usage_mode","created_at","status"],Ln=[...jl,...jl.map(t=>`-${t}`)],Ve=t=>Tl(jl,t),Nn=t=>{"use memo";var B,p,C,N,c,m,h;const e=ce.c(32),{vfolder:r,onShare:l,onDelete:d,onRestore:s,onDeleteForever:n,onStartServiceFallback:g,noDeployTooltip:u}=t,{t:i}=pe(),{token:F}=At.useToken(),{generateFolderPath:f}=Lt(),o=zl(),D=((B=r==null?void 0:r.metadata)==null?void 0:B.usageMode)==="DATA",_=((p=r==null?void 0:r.metadata)==null?void 0:p.usageMode)==="MODEL",V=r==null?void 0:r.vfolderStatus;let S;e[0]!==V?(S=Wl(V),e[0]=V,e[1]=S):S=e[1];const T=S;let y,M;if(e[2]!==f||e[3]!==T||e[4]!==_||e[5]!==D||e[6]!==u||e[7]!==d||e[8]!==n||e[9]!==s||e[10]!==l||e[11]!==g||e[12]!==i||e[13]!==r.id||e[14]!==((C=r.metadata)==null?void 0:C.name)||e[15]!==r.vfolderStatus){const A=ye(r.id??"");y=f(A),M=cl([_&&!T?{key:"start-service",title:i("modelService.DeployAsService"),icon:a.jsx(Nt,{}),disabled:u?{reason:u}:!1,action:async()=>{g(A)}}:null,T?null:{key:"share",title:i("button.Share"),icon:a.jsx(Et,{}),onClick:l},T?null:{key:"delete",title:i("data.folders.MoveToTrash"),icon:a.jsx($l,{}),type:"danger",disabled:D?{reason:i("data.folders.CannotDeletePipelineFolder")}:!1,popConfirm:{title:i("data.folders.MoveToTrash"),description:((N=r==null?void 0:r.metadata)==null?void 0:N.name)??void 0,okText:i("button.Confirm"),cancelText:i("button.Cancel"),okButtonProps:{danger:!0},onConfirm:d}},T?{key:"restore",title:i("data.folders.Restore"),icon:a.jsx(Yl,{}),disabled:D?{reason:i("data.folders.CannotRestorePipelineFolder")}:(r==null?void 0:r.vfolderStatus)!=="DELETE_PENDING"?{reason:i("data.folders.DeletionAlreadyStarted")}:!1,popConfirm:{title:i("data.folders.Restore"),description:((c=r==null?void 0:r.metadata)==null?void 0:c.name)??void 0,okText:i("button.Confirm"),cancelText:i("button.Cancel"),onConfirm:s}}:null,T?{key:"delete-forever",title:i("data.folders.Delete"),icon:a.jsx(Jl,{}),type:"danger",disabled:(r==null?void 0:r.vfolderStatus)!=="DELETE_PENDING"?{reason:i("data.folders.DeletionAlreadyStarted")}:!1,onClick:n}:null]),e[2]=f,e[3]=T,e[4]=_,e[5]=D,e[6]=u,e[7]=d,e[8]=n,e[9]=s,e[10]=l,e[11]=g,e[12]=i,e[13]=r.id,e[14]=(m=r.metadata)==null?void 0:m.name,e[15]=r.vfolderStatus,e[16]=y,e[17]=M}else y=e[16],M=e[17];const K=M;let b;e[18]!==F.fontSizeHeading5?(b={fontSize:F.fontSizeHeading5},e[18]=F.fontSizeHeading5,e[19]=b):b=e[19];let k;e[20]!==b||e[21]!==r?(k=a.jsx(yn,{vfolderNodeIdenticonFrgmt:r,style:b}),e[20]=b,e[21]=r,e[22]=k):k=e[22];const P=(h=r.metadata)==null?void 0:h.name,j=`${y.pathname}?${y.search}`;let I;e[23]!==y||e[24]!==o?(I=()=>{o(y)},e[23]=y,e[24]=o,e[25]=I):I=e[25];let v;return e[26]!==K||e[27]!==k||e[28]!==P||e[29]!==j||e[30]!==I?(v=a.jsx(qt,{icon:k,title:P,to:j,onTitleClick:I,actions:K,showActions:"always"}),e[26]=K,e[27]=k,e[28]=P,e[29]=j,e[30]=I,e[31]=v):v=e[31],v},En=t=>{"use memo";var T;const e=ce.c(18),{host:r}=t,{t:l}=pe(),d=Ce();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let n;e[1]!==d?(n={queryKey:s,queryFn:()=>d.vfolder.list_hosts(),staleTime:3e5,refetchOnMount:!1,refetchOnWindowFocus:!1},e[1]=d,e[2]=n):n=e[2];const{data:g}=Bt(n);if(!r)return null;const u=(T=g==null?void 0:g.volume_info)==null?void 0:T[r],i=u==null?void 0:u.usage,F=i==null?void 0:i.percentage;let f,o,D,_;if(e[3]!==l||e[4]!==i||e[5]!==F){const y=F===void 0?l("data.usage.Unknown"):F<70?l("data.usage.Adequate"):F<90?l("data.usage.Caution"):l("data.usage.Insufficient");f=ue,o=2,D="center",_=i?a.jsx(Ot,{content:l("data.usage.HostStatusTooltip",{status:y}),icon:a.jsx($t,{percent:F}),style:{alignItems:"center"}}):null,e[3]=l,e[4]=i,e[5]=F,e[6]=f,e[7]=o,e[8]=D,e[9]=_}else f=e[6],o=e[7],D=e[8],_=e[9];let V;e[10]!==r?(V=a.jsx(be,{children:r}),e[10]=r,e[11]=V):V=e[11];let S;return e[12]!==f||e[13]!==o||e[14]!==D||e[15]!==_||e[16]!==V?(S=a.jsxs(f,{gap:o,align:D,children:[_,V]}),e[12]=f,e[13]=o,e[14]=D,e[15]=_,e[16]=V,e[17]=S):S=e[17],S},Pn=t=>{"use memo";const e=ce.c(13),{onOpen:r}=t,{t:l}=pe(),d=Ce();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let n;e[1]!==d?(n={queryKey:s,queryFn:()=>d.vfolder.list_hosts()},e[1]=d,e[2]=n):n=e[2];const{data:g}=Zl(n);if(!wt(Ut((g==null?void 0:g.volume_info)??{}),wn))return null;let i;e[3]!==l?(i=l("data.QuotaPerStorageVolume"),e[3]=l,e[4]=i):i=e[4];let F;e[5]!==r?(F=_=>{_.stopPropagation(),r()},e[5]=r,e[6]=F):F=e[6];let f;e[7]===Symbol.for("react.memo_cache_sentinel")?(f={cursor:"pointer"},e[7]=f):f=e[7];let o;e[8]!==F?(o={size:14,onClick:F,style:f},e[8]=F,e[9]=o):o=e[9];let D;return e[10]!==i||e[11]!==o?(D=a.jsx(Qt,{title:i,iconProps:o}),e[10]=i,e[11]=o,e[12]=D):D=e[12],D},vn=t=>a.jsx(Z.Suspense,{fallback:null,children:a.jsx(Pn,{...t})}),Bn=()=>{"use memo";const t=ce.c(8),e=Ce();let r;t[0]===Symbol.for("react.memo_cache_sentinel")?(r=["vhostInfo"],t[0]=r):r=t[0];let l;t[1]!==e?(l={queryKey:r,queryFn:()=>e.vfolder.list_hosts()},t[1]=e,t[2]=l):l=t[2];const{data:d}=Zl(l);let s;t[3]!==(d==null?void 0:d.volume_info)?(s=Ht(zt((d==null?void 0:d.volume_info)??{}),Un),t[3]=d==null?void 0:d.volume_info,t[4]=s):s=t[4];const n=s;if(!n)return null;const[g,u]=n;let i;if(t[5]!==g||t[6]!==u){const F={id:g,...u};i=a.jsx(Fn,{defaultVolumeInfo:F}),t[5]=g,t[6]=u,t[7]=i}else i=t[7];return i},On=t=>{"use memo";const e=ce.c(16),{open:r,onCancel:l}=t,{t:d}=pe();let s;e[0]!==l?(s=o=>{o||l()},e[0]=l,e[1]=s):s=e[1];let n;e[2]!==d?(n=d("data.QuotaPerStorageVolume"),e[2]=d,e[3]=n):n=e[3];let g;e[4]!==d?(g=d("data.HostDetails"),e[4]=d,e[5]=g):g=e[5];let u;e[6]!==g?(u=a.jsx(ue,{justify:"end",children:a.jsx(Rt,{title:g})}),e[6]=g,e[7]=u):u=e[7];let i;e[8]===Symbol.for("react.memo_cache_sentinel")?(i=a.jsx(Z.Suspense,{fallback:a.jsx(Kl,{rows:3}),children:a.jsx(Bn,{})}),e[8]=i):i=e[8];let F;e[9]!==u?(F=a.jsxs(ul,{align:"stretch",gap:3,children:[u,i]}),e[9]=u,e[10]=F):F=e[10];let f;return e[11]!==r||e[12]!==s||e[13]!==n||e[14]!==F?(f=a.jsx(hl,{isOpen:r,onOpenChange:s,title:n,width:640,maskClosable:!1,footer:null,children:F}),e[11]=r,e[12]=s,e[13]=n,e[14]=F,e[15]=f):f=e[15],f},$n=({vfoldersFrgmt:t,onRemoveRow:e,project:r,noDeployTooltip:l,...d})=>{"use memo";const{t:s}=pe(),{message:n}=kl.useApp(),[g]=ql(),[u,i]=Z.useState(null),{getErrorMessage:F}=ml(),f=zl(),o=xt(),{upsertNotification:D}=Ul(),[_,V]=Z.useState([]),[S,T]=Z.useState(null),[y,M]=ie.useQueryLoader(Mt),[K,b]=Z.useState(null),[k,P]=Z.useState(!1),[j,I]=Z.useState(!1),v=ie.useFragment(ct,t),B=cl(v),[p]=ie.useMutation(ut),[C]=ie.useMutation(dt),N=(c,m)=>{var O;const h=(O=m==null?void 0:m.message.match(/sessions\(ids: (\[.*?\])\)/))==null?void 0:O[1],A=JSON.parse((h==null?void 0:h.replace(/'/g,'"'))||"[]");D({open:!0,key:`vfolder-error-${c==null?void 0:c.id}`,node:(c==null?void 0:c.notificationFrgmt)??null,description:F(m).replace(/\(ids[\s\S]*$/,""),extraDescription:Pt(A)?null:a.jsxs(ul,{align:"stretch",children:[a.jsx(be,{color:"secondary",children:s("data.folders.MountedSessions")}),se(A,E=>a.jsx(vt,{href:"#",style:{fontWeight:"normal"},onClick:x=>{x.preventDefault(),f({pathname:o("session",{scope:"project"}),search:new URLSearchParams({sessionDetail:E}).toString()})},children:E},E))]})})};return a.jsxs(a.Fragment,{children:[a.jsx(Hl,{scroll:{x:"max-content"},resizable:!0,rowKey:c=>c.id,size:"small",dataSource:B,columns:[{key:"name",title:s("data.folders.Name"),dataIndex:["metadata","name"],required:!0,render:(c,m)=>a.jsx(Nn,{vfolder:m,noDeployTooltip:l,onShare:()=>{var h;((h=m==null?void 0:m.ownership)==null?void 0:h.userId)===(g==null?void 0:g.uuid)?i(ye((m==null?void 0:m.id)??null)):T(m)},onDelete:()=>{const h=m==null?void 0:m.id;h&&p({variables:{vfolderId:ye(h)},onCompleted:(A,O)=>{var E,x;if(O&&O.length>0){N(m,new Error(((E=O[0])==null?void 0:E.message)??""));return}e==null||e(h),n.success(s("data.folders.MovedToTrashBin",{folderName:(x=m==null?void 0:m.metadata)==null?void 0:x.name}))},onError:A=>N(m,A)})},onRestore:()=>{const h=m==null?void 0:m.id;if(!h)return;const A=O=>{D({key:`vfolder-error-${h}`,node:(m==null?void 0:m.notificationFrgmt)??null,description:F(O),open:!0})};C({variables:{vfolderId:ye(h)},onCompleted:(O,E)=>{var x,Q;if(E&&E.length>0){A(new Error(((x=E[0])==null?void 0:x.message)??""));return}e==null||e(h),n.success(s("data.folders.FolderRestored",{folderName:(Q=m==null?void 0:m.metadata)==null?void 0:Q.name}))},onError:A})},onDeleteForever:()=>{V(m?[m]:[])},onStartServiceFallback:h=>{M({},{fetchPolicy:"store-and-network"}),b(h),P(!0)}}),sorter:Ve("name")},{key:"status",title:s("data.folders.Status"),dataIndex:"vfolderStatus",render:c=>a.jsx(Gl,{variant:Kt("vfolder",c),label:c}),sorter:Ve("status")},{key:"host",title:a.jsxs(ue,{gap:2,align:"center",children:[s("data.Host"),a.jsx(vn,{onOpen:()=>I(!0)})]}),dataIndex:"host",render:c=>a.jsx(En,{host:c}),sorter:Ve("host")},{key:"permissions",title:s("data.folders.MountPermission"),render:(c,m)=>a.jsx(ft,{vfolderFrgmt:m})},{key:"ownership_type",title:s("data.folders.Type"),dataIndex:["accessControl","ownershipType"],render:c=>c==="USER"?a.jsxs(ue,{gap:2,children:[a.jsx(be,{children:s("data.User")}),a.jsx(Ql,{size:"1em"})]}):a.jsxs(ue,{gap:2,children:[a.jsx(be,{children:s("data.Project")}),a.jsx(Rl,{size:"1em"})]}),sorter:Ve("ownership_type")},{key:"owner",title:s("data.folders.Owner"),render:(c,m)=>{var h,A,O,E,x,Q,U;return((h=m.accessControl)==null?void 0:h.ownershipType)==="USER"?(E=(O=(A=m==null?void 0:m.ownership)==null?void 0:A.user)==null?void 0:O.basicInfo)==null?void 0:E.email:(U=(Q=(x=m==null?void 0:m.ownership)==null?void 0:x.project)==null?void 0:Q.basicInfo)==null?void 0:U.name}},{key:"usage_mode",title:s("data.UsageMode"),dataIndex:["metadata","usageMode"],defaultHidden:!0,sorter:Ve("usage_mode"),render:c=>{switch(c){case"GENERAL":return s("data.General");case"DATA":return s("webui.menu.Data");case"MODEL":return s("data.Models");default:return c}}},{key:"num_files",title:s("data.folders.NumberOfFiles"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"cur_size",title:s("data.folders.FolderUsage"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"max_files",title:s("data.folders.MaxFolderQuota"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"max_size",title:s("data.folders.MaxSize"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"cloneable",title:s("data.folders.Cloneable"),dataIndex:["metadata","cloneable"],defaultHidden:!0,sorter:Ve("cloneable"),render:c=>s(c?"button.Yes":"button.No")},{key:"quota_scope_id",title:s("data.QuotaScopeId"),dataIndex:["metadata","quotaScopeId"],defaultHidden:!0,sorter:Ve("quota_scope_id"),render:c=>c?a.jsx(Vl,{copyable:!0,children:c}):"-"},{key:"last_used",title:s("credential.LastUsed"),dataIndex:["metadata","lastUsed"],defaultHidden:!0,sorter:Ve("last_used"),render:c=>c?El(c).format("ll LT"):"-"},{key:"created_at",title:s("data.folders.CreatedAt"),dataIndex:["metadata","createdAt"],defaultHidden:!0,sorter:Ve("created_at"),render:c=>c?El(c).format("ll LT"):"-"}],...d}),a.jsx(at,{vfolderFrgmts:_,open:_.length>0,onRequestClose:c=>{c&&_.forEach(m=>e==null?void 0:e(m.id)),V([])}}),a.jsx(jt,{onRequestClose:()=>{i(null)},vfolderId:u,open:!!u}),a.jsx(_n,{vfolderFrgmt:S,open:!!S,onLeaveFolder:c=>{e==null||e(c)},onRequestClose:()=>{T(null)}}),a.jsx(Z.Suspense,{fallback:null,children:y!=null&&K!=null&&r!=null&&a.jsx(Tt,{children:a.jsx(_t,{open:k,project:r,vfolderId:K,queryRef:y,onClose:()=>P(!1),onDeployed:()=>P(!1)})})}),a.jsx(On,{open:j,onCancel:()=>I(!1)})]})};function wn(t){return Tl(t==null?void 0:t.capabilities,"quota")}function Un(t){const[,e]=t;return Tl(e==null?void 0:e.capabilities,"quota")}const qn=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR","DELETE_COMPLETE"],Qn=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR"],Bl={status:{notIn:qn}},Ol={status:{in:Qn}},Rn="-created_at",Hn=["active","deleted"],zn=["all","general","data","automount","model"],Gn={general:{AND:[{name:{iNotStartsWith:"."}},{usageMode:{equals:"GENERAL"}}]},data:{usageMode:{equals:"DATA"}},automount:{name:{iStartsWith:"."}},model:{usageMode:{equals:"MODEL"}}},Wn=t=>{"use memo";var _l;const e=ce.c(197),{project:r}=t,{t:l}=pe(),d=Ce(),[s,n]=Zt("table_column_overrides.ProjectAdminDataPage");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g=[],e[0]=g):g=e[0];const[u,i]=Z.useState(g),[F,f]=Fl(!1),{toggle:o}=f,[D,_]=Fl(!1),{toggle:V}=_,[S,T]=Fl(!1),{toggle:y}=T,[M,K]=Fl(!1),{toggle:b}=K;let k;e[1]===Symbol.for("react.memo_cache_sentinel")?(k={current:1,pageSize:10},e[1]=k):k=e[1];const{baiPaginationOption:P,tablePaginationOption:j,setTablePaginationOption:I}=Xt(k);let v,B;e[2]===Symbol.for("react.memo_cache_sentinel")?(v={order:Ml(Ln),filter:en(Yn),statusCategory:Ml(Hn).withDefault("active"),mode:Ml(zn).withDefault("all")},B={history:"replace"},e[2]=v,e[3]=B):(v=e[2],B=e[3]);const[p,C]=ln(v,B);let N;e[4]!==p||e[5]!==j?(N={queryParams:p,tablePaginationOption:j},e[4]=p,e[5]=j,e[6]=N):N=e[6];let c;e[7]!==p.statusCategory||e[8]!==N?(c={[p.statusCategory]:N},e[7]=p.statusCategory,e[8]=N,e[9]=c):c=e[9];const m=Z.useRef(c);let h,A;e[10]!==p||e[11]!==j?(h=()=>{m.current[p.statusCategory]={queryParams:p,tablePaginationOption:j}},A=[p,j],e[10]=p,e[11]=j,e[12]=h,e[13]=A):(h=e[12],A=e[13]),Z.useEffect(h,A);const O=Gn[p.mode],[E,x]=tn(),Q=p.statusCategory==="deleted"?Ol:Bl;let U;e[14]!==O?(U=O?[O]:[],e[14]=O,e[15]=U):U=e[15];let z;e[16]!==p.filter?(z=p.filter?[p.filter]:[],e[16]=p.filter,e[17]=z):z=e[17];let re;e[18]!==Q||e[19]!==U||e[20]!==z?(re={AND:[Q,...U,...z]},e[18]=Q,e[19]=U,e[20]=z,e[21]=re):re=e[21];const ae=re,w=r.id,G=P.offset,W=P.first,R=p.order||Rn;let H;e[22]!==R?(H=nn(R),e[22]=R,e[23]=H):H=e[23];let me;e[24]!==P.first||e[25]!==P.offset||e[26]!==ae||e[27]!==r.id||e[28]!==H?(me={projectId:w,offset:G,limit:W,filter:ae,orderBy:H,filterForActiveCount:Bl,filterForDeletedCount:Ol},e[24]=P.first,e[25]=P.offset,e[26]=ae,e[27]=r.id,e[28]=H,e[29]=me):me=e[29];const Fe=me,Y=Z.useDeferredValue(Fe),ge=Z.useDeferredValue(E);let X;e[30]===Symbol.for("react.memo_cache_sentinel")?(X=lt,e[30]=X):X=e[30];const q=ge===rn?"store-and-network":"network-only";let J;e[31]!==ge||e[32]!==q?(J={fetchPolicy:q,fetchKey:ge},e[31]=ge,e[32]=q,e[33]=J):J=e[33];const ee=ie.useLazyLoadQuery(X,Y,J);let le,L;e[34]!==ee?({projectVfolders:L,...le}=ee,e[34]=ee,e[35]=le,e[36]=L):(le=e[35],L=e[36]);const Ie=p.statusCategory;let fe;e[37]!==C||e[38]!==I?(fe=$=>{const ne=m.current[$]||{};C(null),C({...ne.queryParams,statusCategory:$},{history:"replace"}),I(ne.tablePaginationOption||{current:1,pageSize:10}),i([])},e[37]=C,e[38]=I,e[39]=fe):fe=e[39];let te;e[40]!==l?(te=l("data.Active"),e[40]=l,e[41]=te):te=e[41];let oe;e[42]!==te?(oe=["active",te],e[42]=te,e[43]=oe):oe=e[43];let ke;e[44]!==l?(ke=l("data.folders.TrashBin"),e[44]=l,e[45]=ke):ke=e[45];let de;e[46]!==ke?(de=["deleted",ke],e[46]=ke,e[47]=de):de=e[47];let he;e[48]!==oe||e[49]!==de?(he=[oe,de],e[48]=oe,e[49]=de,e[50]=he):he=e[50];const Sl=he;let De;e[51]!==le||e[52]!==p.statusCategory||e[53]!==Sl?(De=Sl.map($=>{var Ll;const[ne,Se]=$,Al=((Ll=le[ne])==null?void 0:Ll.count)??0;return{key:ne,label:Se,endContent:Al>0?a.jsx(Gl,{label:Al,variant:p.statusCategory===ne?"info":"neutral"}):void 0}}),e[51]=le,e[52]=p.statusCategory,e[53]=Sl,e[54]=De):De=e[54];let xe;e[55]!==p.statusCategory||e[56]!==fe||e[57]!==De?(xe=a.jsx(on,{activeKey:Ie,onChange:fe,items:De}),e[55]=p.statusCategory,e[56]=fe,e[57]=De,e[58]=xe):xe=e[58];let gl;e[59]===Symbol.for("react.memo_cache_sentinel")?(gl={flexShrink:1},e[59]=gl):gl=e[59];const pt=p.mode;let Me;e[60]!==C||e[61]!==I?(Me=$=>{C({mode:$.target.value}),I({current:1}),i([])},e[60]=C,e[61]=I,e[62]=Me):Me=e[62];let Ke;e[63]!==d._config.enableModelFolders||e[64]!==d._config.fasttrackEndpoint||e[65]!==l?(Ke=an([{label:l("data.All"),value:"all"},{label:l("data.General"),value:"general"},((_l=d==null?void 0:d._config)==null?void 0:_l.fasttrackEndpoint)&&{label:l("data.Pipeline"),value:"data"},{label:l("data.AutoMount"),value:"automount"},d._config.enableModelFolders&&{label:l("data.Models"),value:"model"}]),e[63]=d._config.enableModelFolders,e[64]=d._config.fasttrackEndpoint,e[65]=l,e[66]=Ke):Ke=e[66];let je;e[67]!==p.mode||e[68]!==Me||e[69]!==Ke?(je=a.jsx(dn,{optionType:"button",value:pt,onChange:Me,options:Ke}),e[67]=p.mode,e[68]=Me,e[69]=Ke,e[70]=je):je=e[70];let Te;e[71]!==l?(Te=l("data.folders.Name"),e[71]=l,e[72]=Te):Te=e[72];let _e;e[73]!==Te?(_e={key:"name",propertyLabel:Te,type:"string"},e[73]=Te,e[74]=_e):_e=e[74];let Ae;e[75]!==l?(Ae=l("data.folders.Location"),e[75]=l,e[76]=Ae):Ae=e[76];let Le;e[77]!==Ae?(Le={key:"host",propertyLabel:Ae,type:"string"},e[77]=Ae,e[78]=Le):Le=e[78];let Ne;e[79]!==_e||e[80]!==Le?(Ne=[_e,Le],e[79]=_e,e[80]=Le,e[81]=Ne):Ne=e[81];const bl=p.filter??void 0;let Ee;e[82]!==C||e[83]!==I?(Ee=$=>{C({filter:$??null}),I({current:1}),i([])},e[82]=C,e[83]=I,e[84]=Ee):Ee=e[84];let Pe;e[85]!==Ne||e[86]!==bl||e[87]!==Ee?(Pe=a.jsx(kn,{"data-testid":"vfolder-filter",filterProperties:Ne,value:bl,onChange:Ee}),e[85]=Ne,e[86]=bl,e[87]=Ee,e[88]=Pe):Pe=e[88];let ve;e[89]!==je||e[90]!==Pe?(ve=a.jsxs(ue,{gap:3,align:"start",style:gl,wrap:"wrap",children:[je,Pe]}),e[89]=je,e[90]=Pe,e[91]=ve):ve=e[91];let Be;e[92]!==p.statusCategory||e[93]!==u||e[94]!==l||e[95]!==o?(Be=u.length>0&&p.statusCategory==="active"&&a.jsxs(a.Fragment,{children:[a.jsx(Pl,{count:u.length,onClearSelection:()=>i([])}),a.jsx(hn,{vfolderFrgmt:u,label:l("data.folders.MoveToTrash"),onClick:()=>{o()}})]}),e[92]=p.statusCategory,e[93]=u,e[94]=l,e[95]=o,e[96]=Be):Be=e[96];let Oe;e[97]!==p.statusCategory||e[98]!==u.length||e[99]!==l||e[100]!==b||e[101]!==V?(Oe=u.length>0&&p.statusCategory==="deleted"&&a.jsxs(a.Fragment,{children:[a.jsx(Pl,{count:u.length,onClearSelection:()=>i([])}),a.jsx(sn,{content:l("data.folders.Restore"),children:a.jsx(yl,{label:l("data.folders.Restore"),icon:a.jsx(Yl,{}),onClick:()=>{V()}})}),a.jsx(yl,{label:l("data.folders.Delete"),tooltip:l("data.folders.Delete"),icon:a.jsx(Jl,{}),className:"bai-name-action-cell-danger",variant:"ghost",onClick:()=>{b()}})]}),e[97]=p.statusCategory,e[98]=u.length,e[99]=l,e[100]=b,e[101]=V,e[102]=Oe):Oe=e[102];const Il=Y!==Fe||ge!==E;let $e;e[103]!==x?($e=$=>{x($)},e[103]=x,e[104]=$e):$e=e[104];let we;e[105]!==E||e[106]!==Il||e[107]!==$e?(we=a.jsx(un,{settingId:"project-admin-data",loading:Il,value:E,onChange:$e}),e[105]=E,e[106]=Il,e[107]=$e,e[108]=we):we=e[108];let fl;e[109]===Symbol.for("react.memo_cache_sentinel")?(fl=a.jsx(cn,{}),e[109]=fl):fl=e[109];let Ue;e[110]!==l?(Ue=l("data.CreateFolder"),e[110]=l,e[111]=Ue):Ue=e[111];let qe;e[112]!==y?(qe=()=>{y()},e[112]=y,e[113]=qe):qe=e[113];let Qe;e[114]!==Ue||e[115]!==qe?(Qe=a.jsx(mn,{variant:"primary",icon:fl,label:Ue,onClick:qe}),e[114]=Ue,e[115]=qe,e[116]=Qe):Qe=e[116];let Re;e[117]!==Be||e[118]!==Oe||e[119]!==we||e[120]!==Qe?(Re=a.jsxs(ue,{gap:2,children:[Be,Oe,we,Qe]}),e[117]=Be,e[118]=Oe,e[119]=we,e[120]=Qe,e[121]=Re):Re=e[121];let He;e[122]!==ve||e[123]!==Re?(He=a.jsxs(ue,{justify:"between",wrap:"wrap",gap:3,children:[ve,Re]}),e[122]=ve,e[123]=Re,e[124]=He):He=e[124];const Ft=p.order,Cl=Y!==Fe;let ze;e[125]!==(L==null?void 0:L.edges)?(ze=cl(se(L==null?void 0:L.edges,"node")),e[125]=L==null?void 0:L.edges,e[126]=ze):ze=e[126];let Ge;if(e[127]!==(L==null?void 0:L.edges)||e[128]!==u){let $;e[130]!==(L==null?void 0:L.edges)?($=Se=>{gn(Se,cl(se(L==null?void 0:L.edges,"node")),i)},e[130]=L==null?void 0:L.edges,e[131]=$):$=e[131];let ne;e[132]!==u?(ne=se(u,Jn),e[132]=u,e[133]=ne):ne=e[133],Ge={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(Se){return{disabled:Wl(Se.vfolderStatus)&&Se.vfolderStatus!=="DELETE_PENDING"}},onChange:$,selectedRowKeys:ne},e[127]=L==null?void 0:L.edges,e[128]=u,e[129]=Ge}else Ge=e[129];const Dl=(L==null?void 0:L.count)??0;let We;e[134]!==I||e[135]!==Dl||e[136]!==j.current||e[137]!==j.pageSize?(We={pageSize:j.pageSize,current:j.current,total:Dl,onChange($,ne){vl($)&&vl(ne)&&I({current:$,pageSize:ne})}},e[134]=I,e[135]=Dl,e[136]=j.current,e[137]=j.pageSize,e[138]=We):We=e[138];let Ye;e[139]!==C?(Ye=$=>{C({order:$??null})},e[139]=C,e[140]=Ye):Ye=e[140];let Je;e[141]!==x?(Je=$=>{i(ne=>fn(ne,Se=>Se.id!==$)),x()},e[141]=x,e[142]=Je):Je=e[142];let Ze;e[143]!==s||e[144]!==n?(Ze={columnOverrides:s,onColumnOverridesChange:n},e[143]=s,e[144]=n,e[145]=Ze):Ze=e[145];let Xe;e[146]!==r||e[147]!==p.order||e[148]!==Cl||e[149]!==ze||e[150]!==Ge||e[151]!==We||e[152]!==Ye||e[153]!==Je||e[154]!==Ze?(Xe=a.jsx($n,{order:Ft,loading:Cl,project:r,vfoldersFrgmt:ze,rowSelection:Ge,pagination:We,onChangeOrder:Ye,onRemoveRow:Je,tableSettings:Ze}),e[146]=r,e[147]=p.order,e[148]=Cl,e[149]=ze,e[150]=Ge,e[151]=We,e[152]=Ye,e[153]=Je,e[154]=Ze,e[155]=Xe):Xe=e[155];let el;e[156]!==He||e[157]!==Xe?(el=a.jsxs(ul,{align:"stretch",gap:3,children:[He,Xe]}),e[156]=He,e[157]=Xe,e[158]=el):el=e[158];let ll;e[159]!==o||e[160]!==x?(ll=$=>{$&&(x(),i([])),o()},e[159]=o,e[160]=x,e[161]=ll):ll=e[161];let tl;e[162]!==F||e[163]!==u||e[164]!==ll?(tl=a.jsx(Cn,{vfolderFrgmts:u,open:F,onRequestClose:ll}),e[162]=F,e[163]=u,e[164]=ll,e[165]=tl):tl=e[165];let nl;e[166]!==V||e[167]!==x?(nl=$=>{$&&(x(),i([])),V()},e[166]=V,e[167]=x,e[168]=nl):nl=e[168];let al;e[169]!==D||e[170]!==u||e[171]!==nl?(al=a.jsx(Kn,{vfolderFrgmts:u,open:D,onRequestClose:nl}),e[169]=D,e[170]=u,e[171]=nl,e[172]=al):al=e[172];let sl;e[173]!==b||e[174]!==x?(sl=$=>{$&&(x(),i([])),b()},e[173]=b,e[174]=x,e[175]=sl):sl=e[175];let rl;e[176]!==M||e[177]!==u||e[178]!==sl?(rl=a.jsx(at,{vfolderFrgmts:u,open:M,onRequestClose:sl}),e[176]=M,e[177]=u,e[178]=sl,e[179]=rl):rl=e[179];let ol;e[180]!==l?(ol=l("data.folders.ProjectAdminDataPageAlert"),e[180]=l,e[181]=ol):ol=e[181];let il;e[182]!==y||e[183]!==x?(il=$=>{y(),$&&x()},e[182]=y,e[183]=x,e[184]=il):il=e[184];let dl;e[185]!==S||e[186]!==r||e[187]!==ol||e[188]!==il?(dl=a.jsx(pn,{open:S,project:r,folderType:"project",alertMessage:ol,onRequestClose:il}),e[185]=S,e[186]=r,e[187]=ol,e[188]=il,e[189]=dl):dl=e[189];let pl;return e[190]!==xe||e[191]!==el||e[192]!==tl||e[193]!==al||e[194]!==rl||e[195]!==dl?(pl=a.jsxs(a.Fragment,{children:[xe,el,tl,al,rl,dl]}),e[190]=xe,e[191]=el,e[192]=tl,e[193]=al,e[194]=rl,e[195]=dl,e[196]=pl):pl=e[196],pl},aa=()=>{"use memo";const t=ce.c(10),{t:e}=pe(),r=Gt();let l;t[0]!==r?(l=Wt(r),t[0]=r,t[1]=l):l=t[1];const d=l;let s;t[2]!==e?(s=e("data.ProjectFolders"),t[2]=e,t[3]=s):s=t[3];let n;t[4]===Symbol.for("react.memo_cache_sentinel")?(n=a.jsx(Kl,{rows:4}),t[4]=n):n=t[4];let g;t[5]!==d?(g=a.jsx(Yt,{children:a.jsx(Z.Suspense,{fallback:n,children:d?a.jsx(Wn,{project:d}):a.jsx(Kl,{rows:4})})}),t[5]=d,t[6]=g):g=t[6];let u;return t[7]!==s||t[8]!==g?(u=a.jsx(Jt,{title:s,children:g}),t[7]=s,t[8]=g,t[9]=u):u=t[9],u};function Yn(t){return t}function Jn(t){return t.id}export{aa as default};
//# sourceMappingURL=ProjectAdminDataPage-Bf8priEh.js.map
