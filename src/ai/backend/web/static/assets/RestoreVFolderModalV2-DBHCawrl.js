import{c as pe,u as ye,bb as Le,a1 as ke,r as X,n as E,ba as Ve,V as Me,T as Se,bt as ve,dW as Te,dG as fe}from"./index-CwWAznqi.js";import{r as Ke}from"./icons-BgdBQS0N.js";import{a1 as Ne,m as Q,g as Ce,a0 as Ae}from"./lodash-RhKGq0BF.js";import{B as De}from"./BAIListAlert-C94F7Q9C.js";import{B as Be}from"./BAIBulkErrorModal-B1rud_RV.js";const Ee=(function(){var t={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},d={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},k={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},F={defaultValue:null,kind:"LocalArgument",name:"scope"},V={kind:"Variable",name:"scope",variableName:"scope"},s=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},V],f={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},I={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},b=[n],h={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},_=[h],m={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},V],concreteType:"VFolderConnection",kind:"LinkedField",name:"scopedVFoldersV2",plural:!1,selections:_,storageKey:null},c={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},V],concreteType:"VFolderConnection",kind:"LinkedField",name:"scopedVFoldersV2",plural:!1,selections:_,storageKey:null},g=[{alias:null,args:null,kind:"ScalarField",name:"expr",storageKey:null}],u={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[t,e,d,a,k,l,F],kind:"Fragment",metadata:null,name:"VFolderNodeListPageQuery",selections:[{alias:null,args:s,concreteType:"VFolderConnection",kind:"LinkedField",name:"scopedVFoldersV2",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:f,action:"THROW"},v,I,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:b,storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},h],storageKey:null},m,c],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[F,k,a,t,l,e,d],kind:"Operation",name:"VFolderNodeListPageQuery",selections:[{alias:null,args:s,concreteType:"VFolderConnection",kind:"LinkedField",name:"scopedVFoldersV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[f,v,I,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[n,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderUsageInfo",kind:"LinkedField",name:"usage",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"numFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"usedBytes",plural:!1,selections:g,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},{alias:null,args:null,concreteType:"VFolderQuotaInfo",kind:"LinkedField",name:"quota",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"maxFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"maxSize",plural:!1,selections:g,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},f],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:b,storageKey:null},f],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[u,r,n,o,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},f,o,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},r],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[n,f],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[u],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[u,r,o,n],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},h],storageKey:null},m,c]},params:{cacheID:"c586a033d456005ce96bbb76ba6108fc",id:null,metadata:{},name:"VFolderNodeListPageQuery",operationKind:"query",text:`query VFolderNodeListPageQuery(
  $scope: VFolderScope!
  $offset: Int
  $limit: Int
  $filter: VFolderFilter
  $orderBy: [VFolderOrderBy!]
  $filterForActiveCount: VFolderFilter
  $filterForDeletedCount: VFolderFilter
) {
  scopedVFoldersV2(scope: $scope, offset: $offset, limit: $limit, filter: $filter, orderBy: $orderBy) @since(version: "26.9.0rc1") {
    edges {
      node {
        id
        entityId
        vfolderStatus: status
        metadata {
          name
        }
        ...VFolderNodesV2Fragment
        ...DeleteVFolderModalV2Fragment
        ...DeleteForeverVFolderModalV2Fragment
        ...RestoreVFolderModalV2Fragment
      }
    }
    count
  }
  active: scopedVFoldersV2(scope: $scope, filter: $filterForActiveCount) @since(version: "26.9.0rc1") {
    count
  }
  deleted: scopedVFoldersV2(scope: $scope, filter: $filterForDeletedCount) @since(version: "26.9.0rc1") {
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

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
    }
  }
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

fragment BAIVirtualFolderNodeNotificationItemFragment on VirtualFolderNode {
  row_id
  id
  name
  status
}

fragment BAIVirtualFolderNodeNotificationItemV2Fragment on VFolder {
  id
  entityId
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
  entityId
  metadata {
    name
  }
}

fragment DeleteVFolderModalV2Fragment on VFolder {
  id
  entityId
  metadata {
    name
  }
  permissions @since(version: "26.9.0rc1")
}

fragment RestoreVFolderModalV2Fragment on VFolder {
  id
  entityId
  metadata {
    name
  }
}

fragment SFTPConnectionInfoModalFragment on ComputeSessionNode {
  row_id
  vfolder_nodes {
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
  queue_position
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
  entityId
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
  entityId
  vfolderStatus: status
  host
  unmanagedPath
  usage {
    numFiles
    usedBytes {
      expr @since(version: "26.8.0")
    }
  }
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
  permissions @since(version: "26.9.0rc1")
  quota {
    maxFiles
    maxSize {
      expr @since(version: "26.8.0")
    }
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
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
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
`}}})();Ee.hash="5459b1457d977f566e80667631b6df1a";const Ie=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"BulkDeleteVFoldersV2Payload",kind:"LinkedField",name:"bulkDeleteVfoldersV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"BulkDeleteVFolderV2Error",kind:"LinkedField",name:"failed",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"DeleteVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"DeleteVFolderModalV2Mutation",selections:e},params:{cacheID:"ff1fcb49e157075a455231242a113339",id:null,metadata:{},name:"DeleteVFolderModalV2Mutation",operationKind:"mutation",text:`mutation DeleteVFolderModalV2Mutation(
  $input: BulkDeleteVFoldersV2Input!
) {
  bulkDeleteVfoldersV2(input: $input) {
    items @since(version: "26.9.0rc1") {
      id
    }
    failed @since(version: "26.9.0rc1") {
      vfolderId
      message
    }
  }
}
`}}})();Ie.hash="28e1ac3a34af553dd31bf25aa15805aa";const be={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"DeleteVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null}],type:"VFolder",abstractKey:null};be.hash="7e5564d1dc95526378431a5ec7dc6211";const We=t=>{"use memo";var se,ie;const e=pe.c(85);let d,a,k;e[0]!==t?({vfolderFrgmts:k,onRequestClose:a,...d}=t,e[0]=t,e[1]=d,e[2]=a,e[3]=k):(d=e[1],a=e[2],k=e[3]);const{t:l}=ye(),{message:F}=Le.useApp(),{getErrorMessage:V}=ke(),[s,f]=Ke.useState(null);let v;e[4]===Symbol.for("react.memo_cache_sentinel")?(v=be,e[4]=v):v=e[4];const I=X.useFragment(v,k);let n;e[5]===Symbol.for("react.memo_cache_sentinel")?(n=Ie,e[5]=n):n=e[5];const[b,h]=X.useMutation(n);let _,m,c,g,u,r,o,L,T,N,C,A,D,B,S,p,i;if(e[6]!==d||e[7]!==b||e[8]!==V||e[9]!==h||e[10]!==F||e[11]!==a||e[12]!==l||e[13]!==I){const{deletable:re,undeletable:oe}=Ne(I??[],xe),M=re===void 0?[]:re,ne=oe===void 0?[]:oe;let R;e[31]!==l?(R=l("data.folders.Name"),e[31]=l,e[32]=R):R=e[32];let O;e[33]!==R?(O={key:"name",title:R,dataIndex:"name"},e[33]=R,e[34]=O):O=e[34];let q;e[35]!==l?(q=l("data.folders.ErrorMessage"),e[35]=l,e[36]=q):q=e[36];let U;e[37]!==q?(U={key:"message",title:q,dataIndex:"message"},e[37]=q,e[38]=U):U=e[38];let G;e[39]!==O||e[40]!==U?(G=[O,U],e[39]=O,e[40]=U,e[41]=G):G=e[41],g=G,c=Ve,S=d.open,e[42]!==a?(p=le=>{le||a==null||a(!1)},e[42]=a,e[43]=p):p=e[43],e[44]!==l?(i=l("data.folders.MoveToTrash"),e[44]=l,e[45]=i):i=e[45],u=!1,e[46]!==l?(r=l("data.folders.Delete"),e[46]=l,e[47]=r):r=e[47],e[48]===Symbol.for("react.memo_cache_sentinel")?(o={danger:!0},e[48]=o):o=e[48],L=h,T=()=>{if(M.length===0){a==null||a(!1);return}const le=Q(M,Pe);b({variables:{input:{ids:le}},onCompleted:(x,ae)=>{var ue,me,ce,ge,Fe;if(ae&&ae.length>0){const z=ae[0];F.error((z==null?void 0:z.message)??V(z));return}const te=((me=(ue=x==null?void 0:x.bulkDeleteVfoldersV2)==null?void 0:ue.items)==null?void 0:me.length)??0,de=((ce=x==null?void 0:x.bulkDeleteVfoldersV2)==null?void 0:ce.failed)??[];if(de.length>0){const z=Ae(Q(M,$e));f({total:M.length,failures:Q(de,J=>({key:J.vfolderId,name:z[J.vfolderId]??J.vfolderId,message:J.message}))})}else te===0&&F.error(l("data.folders.FailedToDeleteFolders",{folderNames:Q(M,we).join(", ")}));te!==0&&(M.length===1?F.success(l("data.folders.FolderDeleted",{folderName:(Fe=(ge=M[0])==null?void 0:ge.metadata)==null?void 0:Fe.name})):F.success(l("data.folders.MultipleFolderDeleted",{count:te,total:M.length})),a==null||a(!0))},onError:x=>{F.error(V(x))}})},N=d,m=Me,A=3,D="stretch",B=ne.length>0&&E.jsx(De,{banner:!0,title:l("data.folders.ExcludedFolders",{count:ne.length}),items:Q(ne,je)}),_=Se,C=M.length===1?l("data.folders.MoveToTrashDescription",{folderName:(ie=(se=M[0])==null?void 0:se.metadata)==null?void 0:ie.name}):l("data.folders.MoveToTrashMultipleDescription",{folderLength:M.length}),e[6]=d,e[7]=b,e[8]=V,e[9]=h,e[10]=F,e[11]=a,e[12]=l,e[13]=I,e[14]=_,e[15]=m,e[16]=c,e[17]=g,e[18]=u,e[19]=r,e[20]=o,e[21]=L,e[22]=T,e[23]=N,e[24]=C,e[25]=A,e[26]=D,e[27]=B,e[28]=S,e[29]=p,e[30]=i}else _=e[14],m=e[15],c=e[16],g=e[17],u=e[18],r=e[19],o=e[20],L=e[21],T=e[22],N=e[23],C=e[24],A=e[25],D=e[26],B=e[27],S=e[28],p=e[29],i=e[30];let K;e[49]!==_||e[50]!==C?(K=E.jsx(_,{children:C}),e[49]=_,e[50]=C,e[51]=K):K=e[51];let y;e[52]!==m||e[53]!==K||e[54]!==A||e[55]!==D||e[56]!==B?(y=E.jsxs(m,{gap:A,align:D,children:[B,K]}),e[52]=m,e[53]=K,e[54]=A,e[55]=D,e[56]=B,e[57]=y):y=e[57];let P;e[58]!==c||e[59]!==u||e[60]!==r||e[61]!==o||e[62]!==L||e[63]!==T||e[64]!==N||e[65]!==y||e[66]!==S||e[67]!==p||e[68]!==i?(P=E.jsx(c,{isOpen:S,onOpenChange:p,title:i,maskClosable:u,okText:r,okButtonProps:o,confirmLoading:L,onOk:T,...N,children:y}),e[58]=c,e[59]=u,e[60]=r,e[61]=o,e[62]=L,e[63]=T,e[64]=N,e[65]=y,e[66]=S,e[67]=p,e[68]=i,e[69]=P):P=e[69];const Y=!!s,Z=(s==null?void 0:s.failures.length)??0,ee=(s==null?void 0:s.total)??0;let $;e[70]!==l||e[71]!==Z||e[72]!==ee?($=l("data.folders.DeleteFailureDescription",{failed:Z,total:ee}),e[70]=l,e[71]=Z,e[72]=ee,e[73]=$):$=e[73];let w;e[74]!==(s==null?void 0:s.failures)?(w=(s==null?void 0:s.failures)??[],e[74]=s==null?void 0:s.failures,e[75]=w):w=e[75];let W;e[76]===Symbol.for("react.memo_cache_sentinel")?(W=()=>f(null),e[76]=W):W=e[76];let j;e[77]!==g||e[78]!==Y||e[79]!==$||e[80]!==w?(j=E.jsx(Be,{open:Y,alertDescription:$,columns:g,dataSource:w,onRequestClose:W}),e[77]=g,e[78]=Y,e[79]=$,e[80]=w,e[81]=j):j=e[81];let H;return e[82]!==P||e[83]!==j?(H=E.jsxs(E.Fragment,{children:[P,j]}),e[82]=P,e[83]=j,e[84]=H):H=e[84],H};function xe(t){return Ce(t.permissions,"SOFT_DELETE")?"deletable":"undeletable"}function Pe(t){return t.entityId}function $e(t){var e;return[t.entityId,(e=t.metadata)==null?void 0:e.name]}function we(t){var e;return(e=t==null?void 0:t.metadata)==null?void 0:e.name}function je(t){var e;return{key:t.id,content:(e=t.metadata)==null?void 0:e.name}}const he=(function(){var t=[{defaultValue:null,kind:"LocalArgument",name:"vfolderId"}],e=[{alias:null,args:[{kind:"Variable",name:"vfolderId",variableName:"vfolderId"}],concreteType:"RestoreVFolderPayload",kind:"LinkedField",name:"restoreVFolder",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:t,kind:"Fragment",metadata:null,name:"RestoreVFolderModalV2Mutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:t,kind:"Operation",name:"RestoreVFolderModalV2Mutation",selections:e},params:{cacheID:"14d669a32252e8429330552a9eb6e82e",id:null,metadata:{},name:"RestoreVFolderModalV2Mutation",operationKind:"mutation",text:`mutation RestoreVFolderModalV2Mutation(
  $vfolderId: UUID!
) {
  restoreVFolder(vfolderId: $vfolderId) {
    id
  }
}
`}}})();he.hash="0efe06c3f5b800e9b582b9d254f35ed3";const _e={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"RestoreVFolderModalV2Fragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],type:"VFolder",abstractKey:null};_e.hash="90f09d6d6de8549dea993b83105db7c1";const He=t=>{"use memo";var T,N,C,A,D,B;const e=pe.c(34);let d,a,k;e[0]!==t?({vfolderFrgmts:k,onRequestClose:a,...d}=t,e[0]=t,e[1]=d,e[2]=a,e[3]=k):(d=e[1],a=e[2],k=e[3]);const{t:l}=ye(),{upsertNotification:F}=ve(),{getErrorMessage:V}=ke(),s=X.useRelayEnvironment(),[f,v]=Ke.useState(!1);let I;e[4]===Symbol.for("react.memo_cache_sentinel")?(I=_e,e[4]=I):I=e[4];const n=X.useFragment(I,k);let b;e[5]!==s?(b=S=>new Promise((p,i)=>{Te.commitMutation(s,{mutation:he,variables:{vfolderId:S},onCompleted:(K,y)=>{if(y&&y.length>0){i(y[0]);return}p()},onError:K=>i(K)})}),e[5]=s,e[6]=b):b=e[6];const h=b,_=d.open;let m;e[7]!==a?(m=S=>{S||a==null||a(!1)},e[7]=a,e[8]=m):m=e[8];let c;e[9]!==l?(c=l("data.folders.Restore"),e[9]=l,e[10]=c):c=e[10];let g;e[11]!==l?(g=l("data.folders.Restore"),e[11]=l,e[12]=g):g=e[12];let u;e[13]!==V||e[14]!==a||e[15]!==h||e[16]!==l||e[17]!==F||e[18]!==n?(u=()=>{const S=Q(n,p=>h(p.entityId).catch(i=>(F({message:V(i),description:i==null?void 0:i.description,open:!0}),Promise.reject(i))));v(!0),Promise.allSettled(S).then(p=>{var K,y;v(!1);const i=p.every(Re);i&&((n==null?void 0:n.length)===1?fe.success(l("data.folders.FolderRestored",{folderName:(y=(K=n==null?void 0:n[0])==null?void 0:K.metadata)==null?void 0:y.name})):fe.success(l("data.folders.MultipleFolderRestored",{folderLength:n==null?void 0:n.length}))),a==null||a(i)})},e[13]=V,e[14]=a,e[15]=h,e[16]=l,e[17]=F,e[18]=n,e[19]=u):u=e[19];let r;e[20]!==l||e[21]!==((N=(T=n==null?void 0:n[0])==null?void 0:T.metadata)==null?void 0:N.name)||e[22]!==(n==null?void 0:n.length)?(r=(n==null?void 0:n.length)===1?l("data.folders.RestoreDescription",{folderName:(A=(C=n==null?void 0:n[0])==null?void 0:C.metadata)==null?void 0:A.name}):l("data.folders.RestoreMultipleDescription",{folderLength:n==null?void 0:n.length}),e[20]=l,e[21]=(B=(D=n==null?void 0:n[0])==null?void 0:D.metadata)==null?void 0:B.name,e[22]=n==null?void 0:n.length,e[23]=r):r=e[23];let o;e[24]!==r?(o=E.jsx(Se,{children:r}),e[24]=r,e[25]=o):o=e[25];let L;return e[26]!==d||e[27]!==f||e[28]!==m||e[29]!==c||e[30]!==g||e[31]!==u||e[32]!==o?(L=E.jsx(Ve,{isOpen:_,onOpenChange:m,title:c,maskClosable:!1,okText:g,confirmLoading:f,onOk:u,...d,children:o}),e[26]=d,e[27]=f,e[28]=m,e[29]=c,e[30]=g,e[31]=u,e[32]=o,e[33]=L):L=e[33],L};function Re(t){return t.status==="fulfilled"}export{We as D,He as R,Ee as n};
//# sourceMappingURL=RestoreVFolderModalV2-DBHCawrl.js.map
