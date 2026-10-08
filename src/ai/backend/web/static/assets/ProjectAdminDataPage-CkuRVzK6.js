import{i as ce,r as ie,j as n,c4 as wl,K as hl,u as pe,X as Vl,y as gl,a as Ce,l as z,ak as se,bQ as ht,c6 as Ul,N as ye,a8 as bl,a2 as be,a3 as ql,hM as St,dv as El,cJ as de,s as ul,d6 as Vt,q as Rl,en as Ql,dR as bt,ea as Hl,hN as zl,as as cl,br as It,a_ as Wl,aL as Ct,hO as Dt,aU as ml,v as xt,M as jl,e as Mt,Y as Gl,Z as jt,hP as Kt,aR as Yl,aS as Tt,t as Pl,hQ as _t,an as Lt,hR as At,ai as _l,ab as Nt,D as Et,hI as Jl,hS as Pt,hT as vt,b1 as Xl,aM as Zl,al as Bt,L as Ot,b as $t,f3 as wt,hU as Ut,b5 as et,b_ as qt,ec as Rt,bK as Qt,aD as Ht,B as zt,aW as Sl,ap as Wt,b6 as Gt,z as Yt,W as Jt,ct as Xt,d as Zt,a7 as en,bH as kl,bI as ln,cc as Kl,af as tn,ae as nn,aN as an,aT as sn,ag as rn,cd as vl,bP as Bl,bi as on,aa as dn,dj as un,dH as cn,P as mn,at as gn,eH as fn,aj as pn,Q as Fn}from"./index-BEtVe_s6.js";import{B as lt}from"./BAIBulkErrorModal-7rxjlKpL.js";import{Q as yn}from"./QuotaPerStorageVolumePanelCard-DWtuUyLZ.js";import{V as kn}from"./VFolderNodeIdenticonV2-xDX7cdzl.js";import{B as hn}from"./BAIGraphQLPropertyFilter-BWTcuwjq.js";import"./usePrimaryColors-D0Osov_k.js";const tt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIVFolderDeleteButtonV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"VFolder",abstractKey:null};tt.hash="4d44e5f0482b6a1b21c4aac58aa7d9f2";const Sn=t=>{"use memo";const e=ce.c(8),{vfolderFrgmt:r,label:l,tooltip:d,isDisabled:s,onClick:a,size:g}=t,u=g===void 0?"md":g;let i;e[0]===Symbol.for("react.memo_cache_sentinel")?(i=tt,e[0]=i):i=e[0],ie.useFragment(i,r);const F=d??l;let f;e[1]===Symbol.for("react.memo_cache_sentinel")?(f=n.jsx(wl,{}),e[1]=f):f=e[1];let o;return e[2]!==s||e[3]!==l||e[4]!==a||e[5]!==u||e[6]!==F?(o=n.jsx(hl,{label:l,tooltip:F,icon:f,variant:"ghost",size:u,className:"bai-name-action-cell-danger",isDisabled:s,onClick:a}),e[2]=s,e[3]=l,e[4]=a,e[5]=u,e[6]=F,e[7]=o):o=e[7],o},nt=(function(){var t={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},d={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a={defaultValue:null,kind:"LocalArgument",name:"projectId"},g={kind:"Variable",name:"projectId",variableName:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},g],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},F={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o=[f],D={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},g],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:o,storageKey:null},L={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},g],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:o,storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[t,e,r,l,d,s,a],kind:"Fragment",metadata:null,name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:u,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:i,action:"THROW"},F,{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},f],storageKey:null},D,L],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,d,l,t,s,e,r],kind:"Operation",name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:u,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[i,F,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[C,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},i],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[C],storageKey:null},i],storageKey:null}],storageKey:null},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[T,k,C,S,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},i,S,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},k],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[C,i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[T],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[T,k,S,C],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},f],storageKey:null},D,L]},params:{cacheID:"a4fad0e2392532e8e3ff0829457bfd71",id:null,metadata:{},name:"ProjectAdminDataPageQuery",operationKind:"query",text:`query ProjectAdminDataPageQuery(
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
  ...SessionStatusBadgeFragment
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

fragment SessionStatusBadgeFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
  cluster_size
  kernel_nodes {
    edges {
      node {
        id
        status
      }
    }
  }
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
`}}})();nt.hash="1f6d597c1b6abd207b4639a11dd0a327";const at=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkPurgeVFoldersV2Payload",kind:"LinkedField",name:"bulkPurgeVfoldersV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"successes",storageKey:null},{alias:null,args:null,concreteType:"BulkPurgeVFolderV2Error",kind:"LinkedField",name:"failed",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"purgedCount",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"DeleteForeverVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"DeleteForeverVFolderModalV2Mutation",selections:e},params:{cacheID:"1fffaa3e9f288133c1cec83218ab971c",id:null,metadata:{},name:"DeleteForeverVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteForeverVFolderModalV2Mutation(
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
`}}})();at.hash="10a513e45393cfbdcb39e6de438bec7d";const st={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteForeverVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};st.hash="af117d7a409739259841dcfce2d2a493";const rt=t=>{"use memo";var me,Fe,J,ge;const e=ce.c(96);let r,l,d,s;e[0]!==t?({vfolderFrgmts:s,onRequestClose:l,open:d,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d,e[4]=s):(r=e[1],l=e[2],d=e[3],s=e[4]);const{t:a}=pe(),{message:g}=Vl.useApp(),{getErrorMessage:u}=gl(),i=Ce();let F;e[5]!==i?(F=i.supports("bulk-mutation-per-id-results"),e[5]=i,e[6]=F):F=e[6];const f=F,[o,D]=z.useState(null);let L;e[7]===Symbol.for("react.memo_cache_sentinel")?(L=st,e[7]=L):L=e[7];const C=ie.useFragment(L,s);let T;e[8]===Symbol.for("react.memo_cache_sentinel")?(T=at,e[8]=T):T=e[8];const[k,S]=ie.useMutation(T);let j,K,b,y,N,I,V,_,E,p,x,v,c,m,h,A,O;if(e[9]!==S||e[10]!==r||e[11]!==l||e[12]!==d||e[13]!==a||e[14]!==C){y=C??[],K=y.length===1?((Fe=(me=y[0])==null?void 0:me.metadata)==null?void 0:Fe.name)??a("button.Delete"):a("button.Delete");let Z;e[32]!==a?(Z=a("data.folders.Name"),e[32]=a,e[33]=Z):Z=e[33];let q;e[34]!==Z?(q={key:"name",title:Z,dataIndex:"name"},e[34]=Z,e[35]=q):q=e[35];let X;e[36]!==a?(X=a("data.folders.ErrorMessage"),e[36]=a,e[37]=X):X=e[37];let ee;e[38]!==X?(ee={key:"message",title:X,dataIndex:"message"},e[38]=X,e[39]=ee):ee=e[39];let le;e[40]!==q||e[41]!==ee?(le=[q,ee],e[40]=q,e[41]=ee,e[42]=le):le=e[42],b=le,j=ht,c=r,m=!!d,e[43]!==l?(h=P=>{P||l==null||l(!1)},e[43]=l,e[44]=h):h=e[44],e[45]!==a?(A=a("dialog.title.DeleteForever"),e[45]=a,e[46]=A):A=e[46],O=y.length===1?a("data.folders.DeleteForeverDescription",{folderName:((ge=(J=y[0])==null?void 0:J.metadata)==null?void 0:ge.name)??""}):void 0,N=!1,e[47]!==a?(I=a("data.folders.DeleteForever"),e[47]=a,e[48]=I):I=e[48],e[49]!==a?(V=a("button.Cancel"),e[49]=a,e[50]=V):V=e[50],_=S,E=se(y,Vn),p=!0,x=K,v=a("dialog.PleaseTypeToConfirm",{confirmText:K}),e[9]=S,e[10]=r,e[11]=l,e[12]=d,e[13]=a,e[14]=C,e[15]=j,e[16]=K,e[17]=b,e[18]=y,e[19]=N,e[20]=I,e[21]=V,e[22]=_,e[23]=E,e[24]=p,e[25]=x,e[26]=v,e[27]=c,e[28]=m,e[29]=h,e[30]=A,e[31]=O}else j=e[15],K=e[16],b=e[17],y=e[18],N=e[19],I=e[20],V=e[21],_=e[22],E=e[23],p=e[24],x=e[25],v=e[26],c=e[27],m=e[28],h=e[29],A=e[30],O=e[31];let B;e[51]!==K?(B={placeholder:K},e[51]=K,e[52]=B):B=e[52];let M;e[53]!==a?(M=a("dialog.warning.CannotBeUndone"),e[53]=a,e[54]=M):M=e[54];let R;e[55]!==k||e[56]!==u||e[57]!==g||e[58]!==l||e[59]!==y||e[60]!==f||e[61]!==a?(R=()=>{if(y.length===0){l==null||l(!1);return}const Z=se(y,bn);k({variables:{input:{ids:Z}},onCompleted:(q,X)=>{var P,Ie,fe,te,oe,ke;if(X&&X.length>0){const ue=X[0];g.error((ue==null?void 0:ue.message)??u(ue));return}const ee=f?((Ie=(P=q==null?void 0:q.bulkPurgeVfoldersV2)==null?void 0:P.successes)==null?void 0:Ie.length)??0:((fe=q==null?void 0:q.bulkPurgeVfoldersV2)==null?void 0:fe.purgedCount)??0,le=((te=q==null?void 0:q.bulkPurgeVfoldersV2)==null?void 0:te.failed)??[];if(le.length>0){const ue=Ul(se(y,In));D({total:y.length,failures:se(le,he=>({key:he.vfolderId,name:ue[he.vfolderId]??he.vfolderId,message:he.message}))})}else ee===0&&g.error(a("data.folders.FailedToDeleteFolders",{folderNames:se(y,Cn).join(", ")}));ee!==0&&(y.length===1?g.success(a("data.folders.FolderDeletedForever",{folderName:(ke=(oe=y[0])==null?void 0:oe.metadata)==null?void 0:ke.name})):g.success(a("data.folders.MultipleFolderDeletedForever",{count:ee,total:y.length})),l==null||l(!0))},onError:q=>{g.error(u(q))}})},e[55]=k,e[56]=u,e[57]=g,e[58]=l,e[59]=y,e[60]=f,e[61]=a,e[62]=R):R=e[62];let U;e[63]!==j||e[64]!==N||e[65]!==I||e[66]!==V||e[67]!==_||e[68]!==E||e[69]!==p||e[70]!==x||e[71]!==v||e[72]!==B||e[73]!==M||e[74]!==R||e[75]!==c||e[76]!==m||e[77]!==h||e[78]!==A||e[79]!==O?(U=n.jsx(j,{...c,isOpen:m,onOpenChange:h,title:A,description:O,maskClosable:N,okText:I,cancelText:V,confirmLoading:_,items:E,requireConfirmInput:p,confirmText:x,inputLabel:v,inputProps:B,cannotBeUndoneText:M,onOk:R}),e[63]=j,e[64]=N,e[65]=I,e[66]=V,e[67]=_,e[68]=E,e[69]=p,e[70]=x,e[71]=v,e[72]=B,e[73]=M,e[74]=R,e[75]=c,e[76]=m,e[77]=h,e[78]=A,e[79]=O,e[80]=U):U=e[80];const W=!!o,re=(o==null?void 0:o.failures.length)??0,ae=(o==null?void 0:o.total)??0;let w;e[81]!==a||e[82]!==re||e[83]!==ae?(w=a("data.folders.DeleteFailureDescription",{failed:re,total:ae}),e[81]=a,e[82]=re,e[83]=ae,e[84]=w):w=e[84];let G;e[85]!==(o==null?void 0:o.failures)?(G=(o==null?void 0:o.failures)??[],e[85]=o==null?void 0:o.failures,e[86]=G):G=e[86];let Y;e[87]===Symbol.for("react.memo_cache_sentinel")?(Y=()=>D(null),e[87]=Y):Y=e[87];let Q;e[88]!==b||e[89]!==W||e[90]!==w||e[91]!==G?(Q=n.jsx(lt,{open:W,alertDescription:w,columns:b,dataSource:G,onRequestClose:Y}),e[88]=b,e[89]=W,e[90]=w,e[91]=G,e[92]=Q):Q=e[92];let H;return e[93]!==U||e[94]!==Q?(H=n.jsxs(n.Fragment,{children:[U,Q]}),e[93]=U,e[94]=Q,e[95]=H):H=e[95],H};function Vn(t){var e;return{key:t.id??"",label:((e=t.metadata)==null?void 0:e.name)??""}}function bn(t){return ye(t.id)}function In(t){var e;return[ye(t.id),(e=t.metadata)==null?void 0:e.name]}function Cn(t){var e;return(e=t==null?void 0:t.metadata)==null?void 0:e.name}const ot=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkDeleteVFoldersV2Payload",kind:"LinkedField",name:"bulkDeleteVfoldersV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"BulkDeleteVFolderV2Error",kind:"LinkedField",name:"failed",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deletedCount",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"DeleteVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"DeleteVFolderModalV2Mutation",selections:e},params:{cacheID:"ee3e97a85af9c6b5d681ea26074a160b",id:null,metadata:{},name:"DeleteVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteVFolderModalV2Mutation(
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
`}}})();ot.hash="43ec619764a3c87bdd5b6bf723e7080c";const it={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};it.hash="c1b7e252a2275b9b74d0576b46e2f299";const Dn=t=>{"use memo";var re,ae;const e=ce.c(78);let r,l,d;e[0]!==t?({vfolderFrgmts:d,onRequestClose:l,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d):(r=e[1],l=e[2],d=e[3]);const{t:s}=pe(),{message:a}=Vl.useApp(),{getErrorMessage:g}=gl(),u=Ce();let i;e[4]!==u?(i=u.supports("bulk-mutation-per-id-results"),e[4]=u,e[5]=i):i=e[5];const F=i,[f,o]=z.useState(null);let D;e[6]===Symbol.for("react.memo_cache_sentinel")?(D=it,e[6]=D):D=e[6];const L=ie.useFragment(D,d);let C;e[7]===Symbol.for("react.memo_cache_sentinel")?(C=ot,e[7]=C):C=e[7];const[T,k]=ie.useMutation(C);let S,j,K,b,y,N,I,V,_,E,p,x,v;if(e[8]!==r||e[9]!==T||e[10]!==g||e[11]!==k||e[12]!==a||e[13]!==l||e[14]!==F||e[15]!==s||e[16]!==L){const w=L??[];let G;e[30]!==s?(G=s("data.folders.Name"),e[30]=s,e[31]=G):G=e[31];let Y;e[32]!==G?(Y={key:"name",title:G,dataIndex:"name"},e[32]=G,e[33]=Y):Y=e[33];let Q;e[34]!==s?(Q=s("data.folders.ErrorMessage"),e[34]=s,e[35]=Q):Q=e[35];let H;e[36]!==Q?(H={key:"message",title:Q,dataIndex:"message"},e[36]=Q,e[37]=H):H=e[37];let me;e[38]!==Y||e[39]!==H?(me=[Y,H],e[38]=Y,e[39]=H,e[40]=me):me=e[40],K=me,j=bl,E=r.open,e[41]!==l?(p=Fe=>{Fe||l==null||l(!1)},e[41]=l,e[42]=p):p=e[42],e[43]!==s?(x=s("data.folders.MoveToTrash"),e[43]=s,e[44]=x):x=e[44],v=!1,e[45]!==s?(b=s("data.folders.Delete"),e[45]=s,e[46]=b):b=e[46],e[47]===Symbol.for("react.memo_cache_sentinel")?(y={danger:!0},e[47]=y):y=e[47],N=k,I=()=>{if(w.length===0){l==null||l(!1);return}const Fe=se(w,xn);T({variables:{input:{ids:Fe}},onCompleted:(J,ge)=>{var X,ee,le,P,Ie,fe;if(ge&&ge.length>0){const te=ge[0];a.error((te==null?void 0:te.message)??g(te));return}const Z=F?((ee=(X=J==null?void 0:J.bulkDeleteVfoldersV2)==null?void 0:X.items)==null?void 0:ee.length)??0:((le=J==null?void 0:J.bulkDeleteVfoldersV2)==null?void 0:le.deletedCount)??0,q=((P=J==null?void 0:J.bulkDeleteVfoldersV2)==null?void 0:P.failed)??[];if(q.length>0){const te=Ul(se(w,Mn));o({total:w.length,failures:se(q,oe=>({key:oe.vfolderId,name:te[oe.vfolderId]??oe.vfolderId,message:oe.message}))})}else Z===0&&a.error(s("data.folders.FailedToDeleteFolders",{folderNames:se(w,jn).join(", ")}));Z!==0&&(w.length===1?a.success(s("data.folders.FolderDeleted",{folderName:(fe=(Ie=w[0])==null?void 0:Ie.metadata)==null?void 0:fe.name})):a.success(s("data.folders.MultipleFolderDeleted",{count:Z,total:w.length})),l==null||l(!0))},onError:J=>{a.error(g(J))}})},V=r,S=be,_=w.length===1?s("data.folders.MoveToTrashDescription",{folderName:(ae=(re=w[0])==null?void 0:re.metadata)==null?void 0:ae.name}):s("data.folders.MoveToTrashMultipleDescription",{folderLength:w.length}),e[8]=r,e[9]=T,e[10]=g,e[11]=k,e[12]=a,e[13]=l,e[14]=F,e[15]=s,e[16]=L,e[17]=S,e[18]=j,e[19]=K,e[20]=b,e[21]=y,e[22]=N,e[23]=I,e[24]=V,e[25]=_,e[26]=E,e[27]=p,e[28]=x,e[29]=v}else S=e[17],j=e[18],K=e[19],b=e[20],y=e[21],N=e[22],I=e[23],V=e[24],_=e[25],E=e[26],p=e[27],x=e[28],v=e[29];let c;e[48]!==S||e[49]!==_?(c=n.jsx(S,{children:_}),e[48]=S,e[49]=_,e[50]=c):c=e[50];let m;e[51]!==j||e[52]!==b||e[53]!==y||e[54]!==N||e[55]!==I||e[56]!==V||e[57]!==c||e[58]!==E||e[59]!==p||e[60]!==x||e[61]!==v?(m=n.jsx(j,{isOpen:E,onOpenChange:p,title:x,maskClosable:v,okText:b,okButtonProps:y,confirmLoading:N,onOk:I,...V,children:c}),e[51]=j,e[52]=b,e[53]=y,e[54]=N,e[55]=I,e[56]=V,e[57]=c,e[58]=E,e[59]=p,e[60]=x,e[61]=v,e[62]=m):m=e[62];const h=!!f,A=(f==null?void 0:f.failures.length)??0,O=(f==null?void 0:f.total)??0;let B;e[63]!==s||e[64]!==A||e[65]!==O?(B=s("data.folders.DeleteFailureDescription",{failed:A,total:O}),e[63]=s,e[64]=A,e[65]=O,e[66]=B):B=e[66];let M;e[67]!==(f==null?void 0:f.failures)?(M=(f==null?void 0:f.failures)??[],e[67]=f==null?void 0:f.failures,e[68]=M):M=e[68];let R;e[69]===Symbol.for("react.memo_cache_sentinel")?(R=()=>o(null),e[69]=R):R=e[69];let U;e[70]!==K||e[71]!==h||e[72]!==B||e[73]!==M?(U=n.jsx(lt,{open:h,alertDescription:B,columns:K,dataSource:M,onRequestClose:R}),e[70]=K,e[71]=h,e[72]=B,e[73]=M,e[74]=U):U=e[74];let W;return e[75]!==m||e[76]!==U?(W=n.jsxs(n.Fragment,{children:[m,U]}),e[75]=m,e[76]=U,e[77]=W):W=e[77],W};function xn(t){return ye(t.id)}function Mn(t){var e;return[ye(t.id),(e=t.metadata)==null?void 0:e.name]}function jn(t){var e;return(e=t==null?void 0:t.metadata)==null?void 0:e.name}const dt=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"RestoreVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"RestoreVFolderModalV2Mutation",selections:e},params:{cacheID:"14d669a32252e8429330552a9eb6e82e",id:null,metadata:{},name:"RestoreVFolderModalV2Mutation",operationKind:"mutation",text:`mutation RestoreVFolderModalV2Mutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();dt.hash="0efe06c3f5b800e9b582b9d254f35ed3";const ut={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"RestoreVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};ut.hash="3f78d6da02312aa15054515c21edda60";const Kn=t=>{"use memo";var N,I,V,_,E,p;const e=ce.c(34);let r,l,d;e[0]!==t?({vfolderFrgmts:d,onRequestClose:l,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d):(r=e[1],l=e[2],d=e[3]);const{t:s}=pe(),{upsertNotification:a}=ql(),{getErrorMessage:g}=gl(),u=ie.useRelayEnvironment(),[i,F]=z.useState(!1);let f;e[4]===Symbol.for("react.memo_cache_sentinel")?(f=ut,e[4]=f):f=e[4];const o=ie.useFragment(f,d);let D;e[5]!==u?(D=x=>new Promise((v,c)=>{St.commitMutation(u,{mutation:dt,variables:{vfolderId:ye(x)},onCompleted:(m,h)=>{if(h&&h.length>0){c(h[0]);return}v()},onError:m=>c(m)})}),e[5]=u,e[6]=D):D=e[6];const L=D,C=r.open;let T;e[7]!==l?(T=x=>{x||l==null||l(!1)},e[7]=l,e[8]=T):T=e[8];let k;e[9]!==s?(k=s("data.folders.Restore"),e[9]=s,e[10]=k):k=e[10];let S;e[11]!==s?(S=s("data.folders.Restore"),e[11]=s,e[12]=S):S=e[12];let j;e[13]!==g||e[14]!==l||e[15]!==L||e[16]!==s||e[17]!==a||e[18]!==o?(j=()=>{const x=se(o,v=>L(v.id).catch(c=>(a({message:g(c),description:c==null?void 0:c.description,open:!0}),Promise.reject(c))));F(!0),Promise.allSettled(x).then(v=>{var m,h;F(!1);const c=v.every(Tn);c&&((o==null?void 0:o.length)===1?El.success(s("data.folders.FolderRestored",{folderName:(h=(m=o==null?void 0:o[0])==null?void 0:m.metadata)==null?void 0:h.name})):El.success(s("data.folders.MultipleFolderRestored",{folderLength:o==null?void 0:o.length}))),l==null||l(c)})},e[13]=g,e[14]=l,e[15]=L,e[16]=s,e[17]=a,e[18]=o,e[19]=j):j=e[19];let K;e[20]!==s||e[21]!==((I=(N=o==null?void 0:o[0])==null?void 0:N.metadata)==null?void 0:I.name)||e[22]!==(o==null?void 0:o.length)?(K=(o==null?void 0:o.length)===1?s("data.folders.RestoreDescription",{folderName:(_=(V=o==null?void 0:o[0])==null?void 0:V.metadata)==null?void 0:_.name}):s("data.folders.RestoreMultipleDescription",{folderLength:o==null?void 0:o.length}),e[20]=s,e[21]=(p=(E=o==null?void 0:o[0])==null?void 0:E.metadata)==null?void 0:p.name,e[22]=o==null?void 0:o.length,e[23]=K):K=e[23];let b;e[24]!==K?(b=n.jsx(be,{children:K}),e[24]=K,e[25]=b):b=e[25];let y;return e[26]!==r||e[27]!==i||e[28]!==T||e[29]!==k||e[30]!==S||e[31]!==j||e[32]!==b?(y=n.jsx(bl,{isOpen:C,onOpenChange:T,title:k,maskClosable:!1,okText:S,confirmLoading:i,onOk:j,...r,children:b}),e[26]=r,e[27]=i,e[28]=T,e[29]=k,e[30]=S,e[31]=j,e[32]=b,e[33]=y):y=e[33],y};function Tn(t){return t.status==="fulfilled"}const ct=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"VFolderNodesV2RestoreMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"VFolderNodesV2RestoreMutation",selections:e},params:{cacheID:"fc05c41196eaa2483ea656725bdc2909",id:null,metadata:{},name:"VFolderNodesV2RestoreMutation",operationKind:"mutation",text:`mutation VFolderNodesV2RestoreMutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();ct.hash="786c5ce4389066e04eac9355a031686d";const mt=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"DeleteVFolderV2Payload",kind:"LinkedField",name:"deleteVfolderV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"VFolderNodesV2DeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"VFolderNodesV2DeleteMutation",selections:e},params:{cacheID:"267b27dfe24bf987d3e29f11f2c03074",id:null,metadata:{},name:"VFolderNodesV2DeleteMutation",operationKind:"mutation",text:`mutation VFolderNodesV2DeleteMutation(
  $vfolderId: UUID!
) {
  deleteVfolderV2(vfolderId: $vfolderId) {
    id
  }
}
`}}})();mt.hash="6a3f03b7eacad2630bd79321d5da93d7";const gt=(function(){var t={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"VFolderNodesV2Fragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[t],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderPermissionCellV2Fragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonV2Fragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"BAINodeNotificationItemFragment"}],type:"Node",abstractKey:"__isNode"},kind:"AliasedInlineFragmentSpread",name:"notificationFrgmt"}],type:"VFolder",abstractKey:null}})();gt.hash="07611fcd2a8e6b5fb66ca14bf652e541";const ft={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SharedFolderPermissionInfoModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderPermissionCellV2Fragment"}],type:"VFolder",abstractKey:null};ft.hash="5a18839a6dffea1a5a545710cc7e8bda";const pt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"VFolderPermissionCellV2Fragment",selections:[{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};pt.hash="a517ea6cc8c2fc65f02d29454cd0a8c8";const Ft=t=>{"use memo";var N;const e=ce.c(35);let r,l;e[0]!==t?({vfolderFrgmt:l,...r}=t,e[0]=t,e[1]=r,e[2]=l):(r=e[1],l=e[2]);const{t:d}=pe();let s;e[3]===Symbol.for("react.memo_cache_sentinel")?(s=pt,e[3]=s):s=e[3];const a=ie.useFragment(s,l??null);let g;e[4]!==d?(g=d("data.ReadOnly"),e[4]=d,e[5]=g):g=e[5];let u;e[6]!==g?(u={label:g,icon:"R"},e[6]=g,e[7]=u):u=e[7];let i;e[8]!==d?(i=d("data.ReadWrite"),e[8]=d,e[9]=i):i=e[9];let F;e[10]!==i?(F={label:i,icon:"RW"},e[10]=i,e[11]=F):F=e[11];let f;e[12]!==u||e[13]!==F?(f={ro:u,rw:F},e[12]=u,e[13]=F,e[14]=f):f=e[14];const o=f,D=(N=a==null?void 0:a.accessControl)==null?void 0:N.permission,L=D==="READ_ONLY"?"ro":D==="READ_WRITE"||D==="RW_DELETE"?"rw":void 0,C=L?o[L]:void 0;let T;e[15]!==C?(T={permissionInfo:C},e[15]=C,e[16]=T):T=e[16];const{permissionInfo:k}=T;if(!k){let I;e[17]!==d?(I=d("data.folders.NoMountPermission"),e[17]=d,e[18]=I):I=e[18];let V;e[19]===Symbol.for("react.memo_cache_sentinel")?(V=n.jsx(ul,{children:"-"}),e[19]=V):V=e[19];let _;e[20]!==I?(_=n.jsx(Rl,{content:I,children:V}),e[20]=I,e[21]=_):_=e[21];let E;return e[22]!==r||e[23]!==_?(E=n.jsx(de,{gap:2,...r,children:_}),e[22]=r,e[23]=_,e[24]=E):E=e[24],E}const S=k==null?void 0:k.label;let j;e[25]!==S?(j=n.jsx(ul,{children:S}),e[25]=S,e[26]=j):j=e[26];let K;e[27]!==(k==null?void 0:k.icon)?(K=se(k==null?void 0:k.icon,_n),e[27]=k==null?void 0:k.icon,e[28]=K):K=e[28];let b;e[29]!==K?(b=n.jsx(de,{children:K}),e[29]=K,e[30]=b):b=e[30];let y;return e[31]!==r||e[32]!==j||e[33]!==b?(y=n.jsxs(de,{gap:2,...r,children:[j,b]}),e[31]=r,e[32]=j,e[33]=b,e[34]=y):y=e[34],y};function _n(t){return n.jsx(ul,{code:!0,children:Vt(t)},t)}const Ln=t=>{"use memo";var B,M,R,U,W,re;const e=ce.c(63);let r,l,d,s;e[0]!==t?({vfolderFrgmt:s,onRequestClose:d,onLeaveFolder:l,...r}=t,e[0]=t,e[1]=r,e[2]=l,e[3]=d,e[4]=s):(r=e[1],l=e[2],d=e[3],s=e[4]);const{t:a}=pe(),{message:g}=Vl.useApp(),{getErrorMessage:u}=gl(),[i]=Ql(),F=Ce();let f;e[5]===Symbol.for("react.memo_cache_sentinel")?(f=ft,e[5]=f):f=e[5];const o=ie.useFragment(f,s);let D;e[6]!==F?(D={mutationFn:ae=>{const{folderId:w}=ae;return F.vfolder.leave_invited(w)}},e[6]=F,e[7]=D):D=e[7];const L=bt(D),C=((B=o==null?void 0:o.accessControl)==null?void 0:B.ownershipType)==="USER",T=r.open;let k;e[8]!==d?(k=ae=>{ae||d()},e[8]=d,e[9]=k):k=e[9];let S;e[10]!==a?(S=a("data.SharedFolderPermission"),e[10]=a,e[11]=S):S=e[11];let j;e[12]!==C||e[13]!==a?(j=a(C?"data.folders.SharedFolderAlertDesc":"data.folders.ProjectFolderAlertDesc"),e[12]=C,e[13]=a,e[14]=j):j=e[14];let K;e[15]!==j?(K=n.jsx(xt,{status:"info",title:j}),e[15]=j,e[16]=K):K=e[16];let b;e[17]!==a?(b=a("data.FolderInfo"),e[17]=a,e[18]=b):b=e[18];let y;e[19]!==a?(y=a("data.folders.Name"),e[19]=a,e[20]=y):y=e[20];const N=((M=o==null?void 0:o.metadata)==null?void 0:M.name)??"";let I;e[21]!==N?(I=n.jsx(ul,{copyable:!0,children:N}),e[21]=N,e[22]=I):I=e[22];let V;e[23]!==I||e[24]!==y?(V=n.jsx(jl,{label:y,children:I}),e[23]=I,e[24]=y,e[25]=V):V=e[25];let _;e[26]!==a?(_=a("data.folders.Type"),e[26]=a,e[27]=_):_=e[27];let E;e[28]!==C||e[29]!==a?(E=C?n.jsxs(de,{gap:2,children:[n.jsx(be,{children:a("data.User")}),n.jsx(Hl,{size:"1em"})]}):n.jsxs(de,{gap:2,children:[n.jsx(be,{children:a("data.Project")}),n.jsx(zl,{size:"1em"})]}),e[28]=C,e[29]=a,e[30]=E):E=e[30];let p;e[31]!==_||e[32]!==E?(p=n.jsx(jl,{label:_,children:E}),e[31]=_,e[32]=E,e[33]=p):p=e[33];let x;e[34]!==a?(x=a("data.folders.Owner"),e[34]=a,e[35]=x):x=e[35];const v=((R=o==null?void 0:o.ownership)==null?void 0:R.creatorEmail)||((re=(W=(U=o==null?void 0:o.ownership)==null?void 0:U.user)==null?void 0:W.basicInfo)==null?void 0:re.email);let c;e[36]!==x||e[37]!==v?(c=n.jsx(jl,{label:x,children:v}),e[36]=x,e[37]=v,e[38]=c):c=e[38];let m;e[39]!==V||e[40]!==p||e[41]!==c||e[42]!==b?(m=n.jsxs(Mt,{title:b,columns:2,children:[V,p,c]}),e[39]=V,e[40]=p,e[41]=c,e[42]=b,e[43]=m):m=e[43];let h;e[44]!==i||e[45]!==u||e[46]!==C||e[47]!==L||e[48]!==g||e[49]!==l||e[50]!==d||e[51]!==a||e[52]!==o?(h=C?n.jsxs(cl,{align:"stretch",gap:4,children:[n.jsx(It,{level:5,children:a("data.folders.Permission")}),n.jsx(Wl,{bordered:!0,pagination:!1,dataSource:ml([o]),columns:[{key:"userName",title:a("general.E-Mail"),render:()=>i.email},{key:"permissions",title:a("data.folders.MountPermission"),render:An},{key:"control",title:a("data.folders.Control"),render:(ae,w)=>{var G;return n.jsx(de,{justify:"center",children:n.jsx(Ct,{title:a("data.invitation.LeaveSharedFolderDesc",{folderName:(G=w==null?void 0:w.metadata)==null?void 0:G.name}),onConfirm:()=>{const Y=w==null?void 0:w.id,Q=Y?ye(Y):null;Q&&Y&&L.mutate({folderId:Q},{onSuccess:()=>{l==null||l(Y),g.success(a("data.invitation.SuccessfullyLeftSharedFolder")),d(!0)},onError:H=>{g.error(u(H)),d()}})},children:n.jsx(hl,{label:a("data.invitation.LeaveSharedFolder"),tooltip:a("data.invitation.LeaveSharedFolder"),size:"sm",variant:"ghost",icon:n.jsx(Dt,{}),className:"bai-name-action-cell-danger"})})})}}]})]}):null,e[44]=i,e[45]=u,e[46]=C,e[47]=L,e[48]=g,e[49]=l,e[50]=d,e[51]=a,e[52]=o,e[53]=h):h=e[53];let A;e[54]!==m||e[55]!==h||e[56]!==K?(A=n.jsxs(cl,{align:"stretch",gap:5,children:[K,m,h]}),e[54]=m,e[55]=h,e[56]=K,e[57]=A):A=e[57];let O;return e[58]!==r||e[59]!==A||e[60]!==k||e[61]!==S?(O=n.jsx(bl,{isOpen:T,onOpenChange:k,title:S,maskClosable:!1,footer:null,...r,children:A}),e[58]=r,e[59]=A,e[60]=k,e[61]=S,e[62]=O):O=e[62],O};function An(t,e){return n.jsx(Ft,{vfolderFrgmt:e})}const Tl=["name","host","usage_mode","created_at","status"],Nn=[...Tl,...Tl.map(t=>`-${t}`)],Se=t=>_l(Tl,t),En=t=>{"use memo";var E,p,x,v,c,m,h;const e=ce.c(32),{vfolder:r,onShare:l,onDelete:d,onRestore:s,onDeleteForever:a,onStartServiceFallback:g,noDeployTooltip:u}=t,{t:i}=pe(),{token:F}=Nt.useToken(),{generateFolderPath:f}=Et(),o=Gl(),D=((E=r==null?void 0:r.metadata)==null?void 0:E.usageMode)==="DATA",L=((p=r==null?void 0:r.metadata)==null?void 0:p.usageMode)==="MODEL",C=r==null?void 0:r.vfolderStatus;let T;e[0]!==C?(T=Jl(C),e[0]=C,e[1]=T):T=e[1];const k=T;let S,j;if(e[2]!==f||e[3]!==k||e[4]!==L||e[5]!==D||e[6]!==u||e[7]!==d||e[8]!==a||e[9]!==s||e[10]!==l||e[11]!==g||e[12]!==i||e[13]!==r.id||e[14]!==((x=r.metadata)==null?void 0:x.name)||e[15]!==r.vfolderStatus){const A=ye(r.id??"");S=f(A),j=ml([L&&!k?{key:"start-service",title:i("modelService.DeployAsService"),icon:n.jsx(Pt,{}),disabled:u?{reason:u}:!1,action:async()=>{g(A)}}:null,k?null:{key:"share",title:i("button.Share"),icon:n.jsx(vt,{}),onClick:l},k?null:{key:"delete",title:i("data.folders.MoveToTrash"),icon:n.jsx(wl,{}),type:"danger",disabled:D?{reason:i("data.folders.CannotDeletePipelineFolder")}:!1,popConfirm:{title:i("data.folders.MoveToTrash"),description:((v=r==null?void 0:r.metadata)==null?void 0:v.name)??void 0,okText:i("button.Confirm"),cancelText:i("button.Cancel"),okButtonProps:{danger:!0},onConfirm:d}},k?{key:"restore",title:i("data.folders.Restore"),icon:n.jsx(Xl,{}),disabled:D?{reason:i("data.folders.CannotRestorePipelineFolder")}:(r==null?void 0:r.vfolderStatus)!=="DELETE_PENDING"?{reason:i("data.folders.DeletionAlreadyStarted")}:!1,popConfirm:{title:i("data.folders.Restore"),description:((c=r==null?void 0:r.metadata)==null?void 0:c.name)??void 0,okText:i("button.Confirm"),cancelText:i("button.Cancel"),onConfirm:s}}:null,k?{key:"delete-forever",title:i("data.folders.Delete"),icon:n.jsx(Zl,{}),type:"danger",disabled:(r==null?void 0:r.vfolderStatus)!=="DELETE_PENDING"?{reason:i("data.folders.DeletionAlreadyStarted")}:!1,onClick:a}:null]),e[2]=f,e[3]=k,e[4]=L,e[5]=D,e[6]=u,e[7]=d,e[8]=a,e[9]=s,e[10]=l,e[11]=g,e[12]=i,e[13]=r.id,e[14]=(m=r.metadata)==null?void 0:m.name,e[15]=r.vfolderStatus,e[16]=S,e[17]=j}else S=e[16],j=e[17];const K=j;let b;e[18]!==F.fontSizeHeading5?(b={fontSize:F.fontSizeHeading5},e[18]=F.fontSizeHeading5,e[19]=b):b=e[19];let y;e[20]!==b||e[21]!==r?(y=n.jsx(kn,{vfolderNodeIdenticonFrgmt:r,style:b}),e[20]=b,e[21]=r,e[22]=y):y=e[22];const N=(h=r.metadata)==null?void 0:h.name,I=`${S.pathname}?${S.search}`;let V;e[23]!==S||e[24]!==o?(V=()=>{o(S)},e[23]=S,e[24]=o,e[25]=V):V=e[25];let _;return e[26]!==K||e[27]!==y||e[28]!==N||e[29]!==I||e[30]!==V?(_=n.jsx(Qt,{icon:y,title:N,to:I,onTitleClick:V,actions:K,showActions:"always"}),e[26]=K,e[27]=y,e[28]=N,e[29]=I,e[30]=V,e[31]=_):_=e[31],_},Pn=t=>{"use memo";var k;const e=ce.c(18),{host:r}=t,{t:l}=pe(),d=Ce();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let a;e[1]!==d?(a={queryKey:s,queryFn:()=>d.vfolder.list_hosts(),staleTime:3e5,refetchOnMount:!1,refetchOnWindowFocus:!1},e[1]=d,e[2]=a):a=e[2];const{data:g}=$t(a);if(!r)return null;const u=(k=g==null?void 0:g.volume_info)==null?void 0:k[r],i=u==null?void 0:u.usage,F=i==null?void 0:i.percentage;let f,o,D,L;if(e[3]!==l||e[4]!==i||e[5]!==F){const S=F===void 0?l("data.usage.Unknown"):F<70?l("data.usage.Adequate"):F<90?l("data.usage.Caution"):l("data.usage.Insufficient");f=de,o=2,D="center",L=i?n.jsx(wt,{content:l("data.usage.HostStatusTooltip",{status:S}),icon:n.jsx(Ut,{percent:F}),style:{alignItems:"center"}}):null,e[3]=l,e[4]=i,e[5]=F,e[6]=f,e[7]=o,e[8]=D,e[9]=L}else f=e[6],o=e[7],D=e[8],L=e[9];let C;e[10]!==r?(C=n.jsx(be,{children:r}),e[10]=r,e[11]=C):C=e[11];let T;return e[12]!==f||e[13]!==o||e[14]!==D||e[15]!==L||e[16]!==C?(T=n.jsxs(f,{gap:o,align:D,children:[L,C]}),e[12]=f,e[13]=o,e[14]=D,e[15]=L,e[16]=C,e[17]=T):T=e[17],T},vn=t=>{"use memo";const e=ce.c(13),{onOpen:r}=t,{t:l}=pe(),d=Ce();let s;e[0]===Symbol.for("react.memo_cache_sentinel")?(s=["vhostInfo"],e[0]=s):s=e[0];let a;e[1]!==d?(a={queryKey:s,queryFn:()=>d.vfolder.list_hosts()},e[1]=d,e[2]=a):a=e[2];const{data:g}=et(a);if(!qt(Rt((g==null?void 0:g.volume_info)??{}),Un))return null;let i;e[3]!==l?(i=l("data.QuotaPerStorageVolume"),e[3]=l,e[4]=i):i=e[4];let F;e[5]!==r?(F=L=>{L.stopPropagation(),r()},e[5]=r,e[6]=F):F=e[6];let f;e[7]===Symbol.for("react.memo_cache_sentinel")?(f={cursor:"pointer"},e[7]=f):f=e[7];let o;e[8]!==F?(o={size:14,onClick:F,style:f},e[8]=F,e[9]=o):o=e[9];let D;return e[10]!==i||e[11]!==o?(D=n.jsx(Ht,{title:i,iconProps:o}),e[10]=i,e[11]=o,e[12]=D):D=e[12],D},Bn=t=>n.jsx(z.Suspense,{fallback:null,children:n.jsx(vn,{...t})}),On=()=>{"use memo";const t=ce.c(8),e=Ce();let r;t[0]===Symbol.for("react.memo_cache_sentinel")?(r=["vhostInfo"],t[0]=r):r=t[0];let l;t[1]!==e?(l={queryKey:r,queryFn:()=>e.vfolder.list_hosts()},t[1]=e,t[2]=l):l=t[2];const{data:d}=et(l);let s;t[3]!==(d==null?void 0:d.volume_info)?(s=Wt(Gt((d==null?void 0:d.volume_info)??{}),qn),t[3]=d==null?void 0:d.volume_info,t[4]=s):s=t[4];const a=s;if(!a)return null;const[g,u]=a;let i;if(t[5]!==g||t[6]!==u){const F={id:g,...u};i=n.jsx(yn,{defaultVolumeInfo:F}),t[5]=g,t[6]=u,t[7]=i}else i=t[7];return i},$n=t=>{"use memo";const e=ce.c(16),{open:r,onCancel:l}=t,{t:d}=pe();let s;e[0]!==l?(s=o=>{o||l()},e[0]=l,e[1]=s):s=e[1];let a;e[2]!==d?(a=d("data.QuotaPerStorageVolume"),e[2]=d,e[3]=a):a=e[3];let g;e[4]!==d?(g=d("data.HostDetails"),e[4]=d,e[5]=g):g=e[5];let u;e[6]!==g?(u=n.jsx(de,{justify:"end",children:n.jsx(zt,{title:g})}),e[6]=g,e[7]=u):u=e[7];let i;e[8]===Symbol.for("react.memo_cache_sentinel")?(i=n.jsx(z.Suspense,{fallback:n.jsx(Sl,{rows:3}),children:n.jsx(On,{})}),e[8]=i):i=e[8];let F;e[9]!==u?(F=n.jsxs(cl,{align:"stretch",gap:3,children:[u,i]}),e[9]=u,e[10]=F):F=e[10];let f;return e[11]!==r||e[12]!==s||e[13]!==a||e[14]!==F?(f=n.jsx(bl,{isOpen:r,onOpenChange:s,title:a,width:640,maskClosable:!1,footer:null,children:F}),e[11]=r,e[12]=s,e[13]=a,e[14]=F,e[15]=f):f=e[15],f},wn=({vfoldersFrgmt:t,onRemoveRow:e,project:r,noDeployTooltip:l,...d})=>{"use memo";const{t:s}=pe(),{message:a}=Vl.useApp(),[g]=Ql(),[u,i]=z.useState(null),{getErrorMessage:F}=gl(),f=Gl(),o=jt(),{upsertNotification:D}=ql(),[L,C]=z.useState([]),[T,k]=z.useState(null),[S,j]=ie.useQueryLoader(Kt),[K,b]=z.useState(null),[y,N]=z.useState(!1),[I,V]=z.useState(!1),_=ie.useFragment(gt,t),E=ml(_),[p]=ie.useMutation(mt),[x]=ie.useMutation(ct),v=(c,m)=>{var O;const h=(O=m==null?void 0:m.message.match(/sessions\(ids: (\[.*?\])\)/))==null?void 0:O[1],A=JSON.parse((h==null?void 0:h.replace(/'/g,'"'))||"[]");D({open:!0,key:`vfolder-error-${c==null?void 0:c.id}`,node:(c==null?void 0:c.notificationFrgmt)??null,description:F(m).replace(/\(ids[\s\S]*$/,""),extraDescription:Bt(A)?null:n.jsxs(cl,{align:"stretch",children:[n.jsx(be,{color:"secondary",children:s("data.folders.MountedSessions")}),se(A,B=>n.jsx(Ot,{href:"#",style:{fontWeight:"normal"},onClick:M=>{M.preventDefault(),f({pathname:o("session",{scope:"project"}),search:new URLSearchParams({sessionDetail:B}).toString()})},children:B},B))]})})};return n.jsxs(n.Fragment,{children:[n.jsx(Wl,{scroll:{x:"max-content"},resizable:!0,rowKey:c=>c.id,size:"small",dataSource:E,columns:[{key:"name",title:s("data.folders.Name"),dataIndex:["metadata","name"],required:!0,render:(c,m)=>n.jsx(En,{vfolder:m,noDeployTooltip:l,onShare:()=>{var h;((h=m==null?void 0:m.ownership)==null?void 0:h.userId)===(g==null?void 0:g.uuid)?i(ye((m==null?void 0:m.id)??null)):k(m)},onDelete:()=>{const h=m==null?void 0:m.id;h&&p({variables:{vfolderId:ye(h)},onCompleted:(A,O)=>{var B,M;if(O&&O.length>0){v(m,new Error(((B=O[0])==null?void 0:B.message)??""));return}e==null||e(h),a.success(s("data.folders.MovedToTrashBin",{folderName:(M=m==null?void 0:m.metadata)==null?void 0:M.name}))},onError:A=>v(m,A)})},onRestore:()=>{const h=m==null?void 0:m.id;if(!h)return;const A=O=>{D({key:`vfolder-error-${h}`,node:(m==null?void 0:m.notificationFrgmt)??null,description:F(O),open:!0})};x({variables:{vfolderId:ye(h)},onCompleted:(O,B)=>{var M,R;if(B&&B.length>0){A(new Error(((M=B[0])==null?void 0:M.message)??""));return}e==null||e(h),a.success(s("data.folders.FolderRestored",{folderName:(R=m==null?void 0:m.metadata)==null?void 0:R.name}))},onError:A})},onDeleteForever:()=>{C(m?[m]:[])},onStartServiceFallback:h=>{j({},{fetchPolicy:"store-and-network"}),b(h),N(!0)}}),sorter:Se("name")},{key:"status",title:s("data.folders.Status"),dataIndex:"vfolderStatus",render:c=>n.jsx(Yl,{variant:Tt("vfolder",c),label:c}),sorter:Se("status")},{key:"host",title:n.jsxs(de,{gap:2,align:"center",children:[s("data.Host"),n.jsx(Bn,{onOpen:()=>V(!0)})]}),dataIndex:"host",render:c=>n.jsx(Pn,{host:c}),sorter:Se("host")},{key:"permissions",title:s("data.folders.MountPermission"),render:(c,m)=>n.jsx(Ft,{vfolderFrgmt:m})},{key:"ownership_type",title:s("data.folders.Type"),dataIndex:["accessControl","ownershipType"],render:c=>c==="USER"?n.jsxs(de,{gap:2,children:[n.jsx(be,{children:s("data.User")}),n.jsx(Hl,{size:"1em"})]}):n.jsxs(de,{gap:2,children:[n.jsx(be,{children:s("data.Project")}),n.jsx(zl,{size:"1em"})]}),sorter:Se("ownership_type")},{key:"owner",title:s("data.folders.Owner"),render:(c,m)=>{var h,A,O,B,M,R,U;return((h=m.accessControl)==null?void 0:h.ownershipType)==="USER"?(B=(O=(A=m==null?void 0:m.ownership)==null?void 0:A.user)==null?void 0:O.basicInfo)==null?void 0:B.email:(U=(R=(M=m==null?void 0:m.ownership)==null?void 0:M.project)==null?void 0:R.basicInfo)==null?void 0:U.name}},{key:"usage_mode",title:s("data.UsageMode"),dataIndex:["metadata","usageMode"],defaultHidden:!0,sorter:Se("usage_mode"),render:c=>{switch(c){case"GENERAL":return s("data.General");case"DATA":return s("webui.menu.Data");case"MODEL":return s("data.Models");default:return c}}},{key:"num_files",title:s("data.folders.NumberOfFiles"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"cur_size",title:s("data.folders.FolderUsage"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"max_files",title:s("data.folders.MaxFolderQuota"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"max_size",title:s("data.folders.MaxSize"),defaultHidden:!0,sorter:!1,render:()=>"-"},{key:"cloneable",title:s("data.folders.Cloneable"),dataIndex:["metadata","cloneable"],defaultHidden:!0,sorter:Se("cloneable"),render:c=>s(c?"button.Yes":"button.No")},{key:"quota_scope_id",title:s("data.QuotaScopeId"),dataIndex:["metadata","quotaScopeId"],defaultHidden:!0,sorter:Se("quota_scope_id"),render:c=>c?n.jsx(ul,{copyable:!0,children:c}):"-"},{key:"last_used",title:s("credential.LastUsed"),dataIndex:["metadata","lastUsed"],defaultHidden:!0,sorter:Se("last_used"),render:c=>c?Pl(c).format("ll LT"):"-"},{key:"created_at",title:s("data.folders.CreatedAt"),dataIndex:["metadata","createdAt"],defaultHidden:!0,sorter:Se("created_at"),render:c=>c?Pl(c).format("ll LT"):"-"}],...d}),n.jsx(rt,{vfolderFrgmts:L,open:L.length>0,onRequestClose:c=>{c&&L.forEach(m=>e==null?void 0:e(m.id)),C([])}}),n.jsx(_t,{onRequestClose:()=>{i(null)},vfolderId:u,open:!!u}),n.jsx(Ln,{vfolderFrgmt:T,open:!!T,onLeaveFolder:c=>{e==null||e(c)},onRequestClose:()=>{k(null)}}),n.jsx(z.Suspense,{fallback:null,children:S!=null&&K!=null&&r!=null&&n.jsx(Lt,{children:n.jsx(At,{open:y,project:r,vfolderId:K,queryRef:S,onClose:()=>N(!1),onDeployed:()=>N(!1)})})}),n.jsx($n,{open:I,onCancel:()=>V(!1)})]})};function Un(t){return _l(t==null?void 0:t.capabilities,"quota")}function qn(t){const[,e]=t;return _l(e==null?void 0:e.capabilities,"quota")}const Rn=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR","DELETE_COMPLETE"],Qn=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR"],Ol={status:{notIn:Rn}},$l={status:{in:Qn}},Hn="-created_at",zn=["active","deleted"],Wn=["all","general","data","automount","model"],Gn={general:{AND:[{name:{iNotStartsWith:"."}},{usageMode:{equals:"GENERAL"}}]},data:{usageMode:{equals:"DATA"}},automount:{name:{iStartsWith:"."}},model:{usageMode:{equals:"MODEL"}}},Yn=t=>{"use memo";var Ll;const e=ce.c(198),{project:r}=t,{t:l}=pe(),d=Ce(),[s,a]=en("table_column_overrides.ProjectAdminDataPage");let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g=[],e[0]=g):g=e[0];const[u,i]=z.useState(g),[F,f]=kl(!1),{toggle:o}=f,[D,L]=kl(!1),{toggle:C}=L,[T,k]=kl(!1),{toggle:S}=k,[j,K]=kl(!1),{toggle:b}=K;let y;e[1]===Symbol.for("react.memo_cache_sentinel")?(y={current:1,pageSize:10},e[1]=y):y=e[1];const{baiPaginationOption:N,tablePaginationOption:I,setTablePaginationOption:V}=ln(y);let _,E;e[2]===Symbol.for("react.memo_cache_sentinel")?(_={order:Kl(Nn),filter:tn(Jn),statusCategory:Kl(zn).withDefault("active"),mode:Kl(Wn).withDefault("all")},E={history:"replace"},e[2]=_,e[3]=E):(_=e[2],E=e[3]);const[p,x]=nn(_,E);let v;e[4]!==p||e[5]!==I?(v={queryParams:p,tablePaginationOption:I},e[4]=p,e[5]=I,e[6]=v):v=e[6];let c;e[7]!==p.statusCategory||e[8]!==v?(c={[p.statusCategory]:v},e[7]=p.statusCategory,e[8]=v,e[9]=c):c=e[9];const m=z.useRef(c);let h,A;e[10]!==p||e[11]!==I?(h=()=>{m.current[p.statusCategory]={queryParams:p,tablePaginationOption:I}},A=[p,I],e[10]=p,e[11]=I,e[12]=h,e[13]=A):(h=e[12],A=e[13]),z.useEffect(h,A);const O=Gn[p.mode],[B,M]=an(),R=p.statusCategory==="deleted"?$l:Ol;let U;e[14]!==O?(U=O?[O]:[],e[14]=O,e[15]=U):U=e[15];let W;e[16]!==p.filter?(W=p.filter?[p.filter]:[],e[16]=p.filter,e[17]=W):W=e[17];let re;e[18]!==R||e[19]!==U||e[20]!==W?(re={AND:[R,...U,...W]},e[18]=R,e[19]=U,e[20]=W,e[21]=re):re=e[21];const ae=re,w=r.id,G=N.offset,Y=N.first,Q=p.order||Hn;let H;e[22]!==Q?(H=sn(Q),e[22]=Q,e[23]=H):H=e[23];let me;e[24]!==N.first||e[25]!==N.offset||e[26]!==ae||e[27]!==r.id||e[28]!==H?(me={projectId:w,offset:G,limit:Y,filter:ae,orderBy:H,filterForActiveCount:Ol,filterForDeletedCount:$l},e[24]=N.first,e[25]=N.offset,e[26]=ae,e[27]=r.id,e[28]=H,e[29]=me):me=e[29];const Fe=me,J=z.useDeferredValue(Fe),ge=z.useDeferredValue(B);let Z;e[30]===Symbol.for("react.memo_cache_sentinel")?(Z=nt,e[30]=Z):Z=e[30];const q=ge===on?"store-and-network":"network-only";let X;e[31]!==ge||e[32]!==q?(X={fetchPolicy:q,fetchKey:ge},e[31]=ge,e[32]=q,e[33]=X):X=e[33];const ee=ie.useLazyLoadQuery(Z,J,X);let le,P;e[34]!==ee?({projectVfolders:P,...le}=ee,e[34]=ee,e[35]=le,e[36]=P):(le=e[35],P=e[36]);const Ie=p.statusCategory;let fe;e[37]!==x||e[38]!==V?(fe=$=>{const ne=m.current[$]||{};x(null),x({...ne.queryParams,statusCategory:$},{history:"replace"}),V(ne.tablePaginationOption||{current:1,pageSize:10}),i([])},e[37]=x,e[38]=V,e[39]=fe):fe=e[39];let te;e[40]!==l?(te=l("data.Active"),e[40]=l,e[41]=te):te=e[41];let oe;e[42]!==te?(oe=["active",te],e[42]=te,e[43]=oe):oe=e[43];let ke;e[44]!==l?(ke=l("data.folders.TrashBin"),e[44]=l,e[45]=ke):ke=e[45];let ue;e[46]!==ke?(ue=["deleted",ke],e[46]=ke,e[47]=ue):ue=e[47];let he;e[48]!==oe||e[49]!==ue?(he=[oe,ue],e[48]=oe,e[49]=ue,e[50]=he):he=e[50];const Il=he;let De;e[51]!==le||e[52]!==p.statusCategory||e[53]!==Il?(De=Il.map($=>{var Nl;const[ne,Ve]=$,Al=((Nl=le[ne])==null?void 0:Nl.count)??0;return{key:ne,label:Ve,endContent:Al>0?n.jsx(Yl,{label:Al,variant:p.statusCategory===ne?"info":"neutral"}):void 0}}),e[51]=le,e[52]=p.statusCategory,e[53]=Il,e[54]=De):De=e[54];let xe;e[55]!==p.statusCategory||e[56]!==fe||e[57]!==De?(xe=n.jsx(dn,{activeKey:Ie,onChange:fe,items:De}),e[55]=p.statusCategory,e[56]=fe,e[57]=De,e[58]=xe):xe=e[58];let fl;e[59]===Symbol.for("react.memo_cache_sentinel")?(fl={flexShrink:1},e[59]=fl):fl=e[59];const yt=p.mode;let Me;e[60]!==x||e[61]!==V?(Me=$=>{x({mode:$.target.value}),V({current:1}),i([])},e[60]=x,e[61]=V,e[62]=Me):Me=e[62];let je;e[63]!==d._config.enableModelFolders||e[64]!==d._config.fasttrackEndpoint||e[65]!==l?(je=rn([{label:l("data.All"),value:"all"},{label:l("data.General"),value:"general"},((Ll=d==null?void 0:d._config)==null?void 0:Ll.fasttrackEndpoint)&&{label:l("data.Pipeline"),value:"data"},{label:l("data.AutoMount"),value:"automount"},d._config.enableModelFolders&&{label:l("data.Models"),value:"model"}]),e[63]=d._config.enableModelFolders,e[64]=d._config.fasttrackEndpoint,e[65]=l,e[66]=je):je=e[66];let Ke;e[67]!==p.mode||e[68]!==Me||e[69]!==je?(Ke=n.jsx(un,{optionType:"button",value:yt,onChange:Me,options:je}),e[67]=p.mode,e[68]=Me,e[69]=je,e[70]=Ke):Ke=e[70];let Te;e[71]!==l?(Te=l("data.folders.Name"),e[71]=l,e[72]=Te):Te=e[72];let _e;e[73]!==Te?(_e={key:"name",propertyLabel:Te,type:"string"},e[73]=Te,e[74]=_e):_e=e[74];let Le;e[75]!==l?(Le=l("data.folders.Location"),e[75]=l,e[76]=Le):Le=e[76];let Ae;e[77]!==Le?(Ae={key:"host",propertyLabel:Le,type:"string"},e[77]=Le,e[78]=Ae):Ae=e[78];let Ne;e[79]!==_e||e[80]!==Ae?(Ne=[_e,Ae],e[79]=_e,e[80]=Ae,e[81]=Ne):Ne=e[81];const Cl=p.filter??void 0;let Ee;e[82]!==x||e[83]!==V?(Ee=$=>{x({filter:$??null}),V({current:1}),i([])},e[82]=x,e[83]=V,e[84]=Ee):Ee=e[84];let Pe;e[85]!==Ne||e[86]!==Cl||e[87]!==Ee?(Pe=n.jsx(hn,{"data-testid":"vfolder-filter",filterProperties:Ne,value:Cl,onChange:Ee}),e[85]=Ne,e[86]=Cl,e[87]=Ee,e[88]=Pe):Pe=e[88];let ve;e[89]!==Ke||e[90]!==Pe?(ve=n.jsxs(de,{gap:3,align:"start",style:fl,wrap:"wrap",children:[Ke,Pe]}),e[89]=Ke,e[90]=Pe,e[91]=ve):ve=e[91];let Be;e[92]!==p.statusCategory||e[93]!==u||e[94]!==l||e[95]!==o?(Be=u.length>0&&p.statusCategory==="active"&&n.jsxs(n.Fragment,{children:[n.jsx(vl,{count:u.length,onClearSelection:()=>i([])}),n.jsx(Sn,{vfolderFrgmt:u,label:l("data.folders.MoveToTrash"),onClick:()=>{o()}})]}),e[92]=p.statusCategory,e[93]=u,e[94]=l,e[95]=o,e[96]=Be):Be=e[96];let Oe;e[97]!==p.statusCategory||e[98]!==u.length||e[99]!==l||e[100]!==b||e[101]!==C?(Oe=u.length>0&&p.statusCategory==="deleted"&&n.jsxs(n.Fragment,{children:[n.jsx(vl,{count:u.length,onClearSelection:()=>i([])}),n.jsx(Rl,{content:l("data.folders.Restore"),children:n.jsx(hl,{label:l("data.folders.Restore"),icon:n.jsx(Xl,{}),onClick:()=>{C()}})}),n.jsx(hl,{label:l("data.folders.Delete"),tooltip:l("data.folders.Delete"),icon:n.jsx(Zl,{}),className:"bai-name-action-cell-danger",variant:"ghost",onClick:()=>{b()}})]}),e[97]=p.statusCategory,e[98]=u.length,e[99]=l,e[100]=b,e[101]=C,e[102]=Oe):Oe=e[102];const Dl=J!==Fe||ge!==B;let $e;e[103]!==M?($e=$=>{M($)},e[103]=M,e[104]=$e):$e=e[104];let we;e[105]!==B||e[106]!==Dl||e[107]!==$e?(we=n.jsx(cn,{settingId:"project-admin-data",loading:Dl,value:B,onChange:$e}),e[105]=B,e[106]=Dl,e[107]=$e,e[108]=we):we=e[108];let pl;e[109]===Symbol.for("react.memo_cache_sentinel")?(pl=n.jsx(mn,{}),e[109]=pl):pl=e[109];let Ue;e[110]!==l?(Ue=l("data.CreateFolder"),e[110]=l,e[111]=Ue):Ue=e[111];let qe;e[112]!==S?(qe=()=>{S()},e[112]=S,e[113]=qe):qe=e[113];let Re;e[114]!==Ue||e[115]!==qe?(Re=n.jsx(gn,{variant:"primary",icon:pl,label:Ue,onClick:qe}),e[114]=Ue,e[115]=qe,e[116]=Re):Re=e[116];let Qe;e[117]!==Be||e[118]!==Oe||e[119]!==we||e[120]!==Re?(Qe=n.jsxs(de,{gap:2,children:[Be,Oe,we,Re]}),e[117]=Be,e[118]=Oe,e[119]=we,e[120]=Re,e[121]=Qe):Qe=e[121];let He;e[122]!==ve||e[123]!==Qe?(He=n.jsxs(de,{justify:"between",wrap:"wrap",gap:3,children:[ve,Qe]}),e[122]=ve,e[123]=Qe,e[124]=He):He=e[124];let Fl;e[125]===Symbol.for("react.memo_cache_sentinel")?(Fl=n.jsx(Sl,{rows:4}),e[125]=Fl):Fl=e[125];const kt=p.order,xl=J!==Fe;let ze;e[126]!==(P==null?void 0:P.edges)?(ze=ml(se(P==null?void 0:P.edges,"node")),e[126]=P==null?void 0:P.edges,e[127]=ze):ze=e[127];let We;if(e[128]!==(P==null?void 0:P.edges)||e[129]!==u){let $;e[131]!==(P==null?void 0:P.edges)?($=Ve=>{fn(Ve,ml(se(P==null?void 0:P.edges,"node")),i)},e[131]=P==null?void 0:P.edges,e[132]=$):$=e[132];let ne;e[133]!==u?(ne=se(u,Xn),e[133]=u,e[134]=ne):ne=e[134],We={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(Ve){return{disabled:Jl(Ve.vfolderStatus)&&Ve.vfolderStatus!=="DELETE_PENDING"}},onChange:$,selectedRowKeys:ne},e[128]=P==null?void 0:P.edges,e[129]=u,e[130]=We}else We=e[130];const Ml=(P==null?void 0:P.count)??0;let Ge;e[135]!==V||e[136]!==Ml||e[137]!==I.current||e[138]!==I.pageSize?(Ge={pageSize:I.pageSize,current:I.current,total:Ml,onChange($,ne){Bl($)&&Bl(ne)&&V({current:$,pageSize:ne})}},e[135]=V,e[136]=Ml,e[137]=I.current,e[138]=I.pageSize,e[139]=Ge):Ge=e[139];let Ye;e[140]!==x?(Ye=$=>{x({order:$??null})},e[140]=x,e[141]=Ye):Ye=e[141];let Je;e[142]!==M?(Je=$=>{i(ne=>pn(ne,Ve=>Ve.id!==$)),M()},e[142]=M,e[143]=Je):Je=e[143];let Xe;e[144]!==s||e[145]!==a?(Xe={columnOverrides:s,onColumnOverridesChange:a},e[144]=s,e[145]=a,e[146]=Xe):Xe=e[146];let Ze;e[147]!==r||e[148]!==p.order||e[149]!==xl||e[150]!==ze||e[151]!==We||e[152]!==Ge||e[153]!==Ye||e[154]!==Je||e[155]!==Xe?(Ze=n.jsx(z.Suspense,{fallback:Fl,children:n.jsx(wn,{order:kt,loading:xl,project:r,vfoldersFrgmt:ze,rowSelection:We,pagination:Ge,onChangeOrder:Ye,onRemoveRow:Je,tableSettings:Xe})}),e[147]=r,e[148]=p.order,e[149]=xl,e[150]=ze,e[151]=We,e[152]=Ge,e[153]=Ye,e[154]=Je,e[155]=Xe,e[156]=Ze):Ze=e[156];let el;e[157]!==He||e[158]!==Ze?(el=n.jsxs(cl,{align:"stretch",gap:3,children:[He,Ze]}),e[157]=He,e[158]=Ze,e[159]=el):el=e[159];let ll;e[160]!==o||e[161]!==M?(ll=$=>{$&&(M(),i([])),o()},e[160]=o,e[161]=M,e[162]=ll):ll=e[162];let tl;e[163]!==F||e[164]!==u||e[165]!==ll?(tl=n.jsx(Dn,{vfolderFrgmts:u,open:F,onRequestClose:ll}),e[163]=F,e[164]=u,e[165]=ll,e[166]=tl):tl=e[166];let nl;e[167]!==C||e[168]!==M?(nl=$=>{$&&(M(),i([])),C()},e[167]=C,e[168]=M,e[169]=nl):nl=e[169];let al;e[170]!==D||e[171]!==u||e[172]!==nl?(al=n.jsx(Kn,{vfolderFrgmts:u,open:D,onRequestClose:nl}),e[170]=D,e[171]=u,e[172]=nl,e[173]=al):al=e[173];let sl;e[174]!==b||e[175]!==M?(sl=$=>{$&&(M(),i([])),b()},e[174]=b,e[175]=M,e[176]=sl):sl=e[176];let rl;e[177]!==j||e[178]!==u||e[179]!==sl?(rl=n.jsx(rt,{vfolderFrgmts:u,open:j,onRequestClose:sl}),e[177]=j,e[178]=u,e[179]=sl,e[180]=rl):rl=e[180];let ol;e[181]!==l?(ol=l("data.folders.ProjectAdminDataPageAlert"),e[181]=l,e[182]=ol):ol=e[182];let il;e[183]!==S||e[184]!==M?(il=$=>{S(),$&&M()},e[183]=S,e[184]=M,e[185]=il):il=e[185];let dl;e[186]!==T||e[187]!==r||e[188]!==ol||e[189]!==il?(dl=n.jsx(Fn,{open:T,project:r,folderType:"project",alertMessage:ol,onRequestClose:il}),e[186]=T,e[187]=r,e[188]=ol,e[189]=il,e[190]=dl):dl=e[190];let yl;return e[191]!==xe||e[192]!==el||e[193]!==tl||e[194]!==al||e[195]!==rl||e[196]!==dl?(yl=n.jsxs(n.Fragment,{children:[xe,el,tl,al,rl,dl]}),e[191]=xe,e[192]=el,e[193]=tl,e[194]=al,e[195]=rl,e[196]=dl,e[197]=yl):yl=e[197],yl},sa=()=>{"use memo";const t=ce.c(10),{t:e}=pe(),r=Yt();let l;t[0]!==r?(l=Jt(r),t[0]=r,t[1]=l):l=t[1];const d=l;let s;t[2]!==e?(s=e("data.ProjectFolders"),t[2]=e,t[3]=s):s=t[3];let a;t[4]===Symbol.for("react.memo_cache_sentinel")?(a=n.jsx(Sl,{rows:4}),t[4]=a):a=t[4];let g;t[5]!==d?(g=n.jsx(Xt,{children:n.jsx(z.Suspense,{fallback:a,children:d?n.jsx(Yn,{project:d}):n.jsx(Sl,{rows:4})})}),t[5]=d,t[6]=g):g=t[6];let u;return t[7]!==s||t[8]!==g?(u=n.jsx(Zt,{title:s,children:g}),t[7]=s,t[8]=g,t[9]=u):u=t[9],u};function Jn(t){return t}function Xn(t){return t.id}export{sa as default};
//# sourceMappingURL=ProjectAdminDataPage-CkuRVzK6.js.map
