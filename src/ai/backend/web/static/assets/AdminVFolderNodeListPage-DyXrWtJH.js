import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{F as t,H as ee,Zn as n,d as te,f as ne}from"./icons-Btg1s2wy.js";import{t as r}from"./compiler-runtime-CZQb2eIb.js";import{St as i,nt as re,ut as ie,vt as a}from"./lodash-ClfL87UH.js";/* empty css            */import{t as o}from"./jsx-runtime-BapUIyWk.js";import{O as ae}from"./DefaultProviders-BFjPhnQa.js";import{t as oe}from"./Button-BKkkrlg5.js";import{t as se}from"./IconButton-DGkWhkpU.js";import{t as ce}from"./VStack-DaUzGF31.js";import{r as le,u as s}from"./Skeleton-D35z7Ria.js";import{t as ue}from"./Badge-8q4sdq1t.js";import{H as de,d as fe,y as pe}from"./helper-BWFKT_2Y.js";import{r as me}from"./hooks-UUY7pxyu.js";import{t as c}from"./react-relay-BfoHYpUf.js";import{t as he}from"./useToggle-CAWNf18k.js";import{l as ge,u as _e}from"./helper-DF1Eunoe.js";import{t as ve}from"./BAIGraphQLPropertyFilter-CNTUQIkF.js";import{t as ye}from"./BAISkeleton-MIjJv1Hr.js";import{t as be}from"./BAISelectionLabel-BTMbVxpE.js";import{n as xe,t as Se}from"./BAISegmentedControlItem-erYb9KqU.js";import{i as Ce}from"./BAIEntityLabelCell-DOyaclRH.js";import{t as we}from"./BAIEntityLabelBulkEditButton-CRMSgz-m.js";import{i as Te,n as Ee,o as De}from"./dist-C3M-rFln.js";import{n as Oe}from"./AstryxSecondaryTheme-CI-CS4ra.js";import{ht as ke,pt as Ae}from"./index-49VU5B_r.js";import{t as je}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{t as Me}from"./BAITabs-Bwz-IwE5.js";import{n as Ne}from"./reactPaginationQueryOptions-DUCwh22X.js";import{a as Pe,i as Fe,n as Ie,t as Le}from"./VFolderNodesV2-Phte8jg6.js";import{t as Re}from"./FolderCreateModal-CeqkMhk8.js";import{n as ze,t as Be}from"./RestoreVFolderModalV2-QPHAf-cN.js";var Ve=r(),He=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`filterForActiveCount`},ee={defaultValue:null,kind:`LocalArgument`,name:`filterForDeletedCount`},n={defaultValue:null,kind:`LocalArgument`,name:`limit`},te={defaultValue:null,kind:`LocalArgument`,name:`offset`},ne={defaultValue:null,kind:`LocalArgument`,name:`orderBy`},r=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`orderBy`,variableName:`orderBy`}],i={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},re={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},ie={alias:`vfolderStatus`,args:null,kind:`ScalarField`,name:`status`,storageKey:null},a={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},o=[a],ae={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},oe=[ae],se={alias:`active`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForActiveCount`}],concreteType:`VFolderConnection`,kind:`LinkedField`,name:`adminVfoldersV2`,plural:!1,selections:oe,storageKey:null},ce={alias:`deleted`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForDeletedCount`}],concreteType:`VFolderConnection`,kind:`LinkedField`,name:`adminVfoldersV2`,plural:!1,selections:oe,storageKey:null},le=[{alias:null,args:null,kind:`ScalarField`,name:`expr`,storageKey:null}],s={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},ue={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},de={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null};return{fragment:{argumentDefinitions:[e,t,ee,n,te,ne],kind:`Fragment`,metadata:null,name:`AdminVFolderNodeListPageQuery`,selections:[{alias:null,args:r,concreteType:`VFolderConnection`,kind:`LinkedField`,name:`adminVfoldersV2`,plural:!1,selections:[{kind:`RequiredField`,field:{alias:null,args:null,concreteType:`VFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{kind:`RequiredField`,field:{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{kind:`RequiredField`,field:i,action:`THROW`},re,ie,{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:o,storageKey:null},{args:null,kind:`FragmentSpread`,name:`VFolderNodesV2Fragment`},{args:null,kind:`FragmentSpread`,name:`DeleteVFolderModalV2Fragment`},{args:null,kind:`FragmentSpread`,name:`DeleteForeverVFolderModalV2Fragment`},{args:null,kind:`FragmentSpread`,name:`RestoreVFolderModalV2Fragment`}],storageKey:null},action:`THROW`}],storageKey:null},action:`THROW`},ae],storageKey:null},se,ce],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[te,n,e,ne,t,ee],kind:`Operation`,name:`AdminVFolderNodeListPageQuery`,selections:[{alias:null,args:r,concreteType:`VFolderConnection`,kind:`LinkedField`,name:`adminVfoldersV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`VFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`node`,plural:!1,selections:[i,re,ie,{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[a,{alias:null,args:null,kind:`ScalarField`,name:`usageMode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quotaScopeId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`lastUsed`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cloneable`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`host`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`unmanagedPath`,storageKey:null},{alias:null,args:null,concreteType:`VFolderUsageInfo`,kind:`LinkedField`,name:`usage`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`numFiles`,storageKey:null},{alias:null,args:null,concreteType:`BinarySizeInfo`,kind:`LinkedField`,name:`usedBytes`,plural:!1,selections:le,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderAccessControlInfo`,kind:`LinkedField`,name:`accessControl`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`permission`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`ownershipType`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`permissions`,storageKey:null},{alias:null,args:null,concreteType:`VFolderQuotaInfo`,kind:`LinkedField`,name:`quota`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`maxFiles`,storageKey:null},{alias:null,args:null,concreteType:`BinarySizeInfo`,kind:`LinkedField`,name:`maxSize`,plural:!1,selections:le,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderOwnershipInfo`,kind:`LinkedField`,name:`ownership`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`userId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`projectId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`creatorEmail`,storageKey:null},{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`user`,plural:!1,selections:[{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null}],storageKey:null},i],storageKey:null},{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`project`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:o,storageKey:null},i],storageKey:null}],storageKey:null},{alias:null,args:[{kind:`Literal`,name:`limit`,value:100}],concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityLabelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityLabel`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null},i,{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:`entityLabels(limit:100)`},{kind:`InlineFragment`,selections:[{kind:`InlineFragment`,selections:[s,ue,a,de,{alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`user_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`scaling_group`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`project_id`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},i,de,{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},ue],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`vfolder_mounts`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_size`,storageKey:null}],type:`ComputeSessionNode`,abstractKey:null},{kind:`InlineFragment`,selections:[s],type:`VFolder`,abstractKey:null},{kind:`InlineFragment`,selections:[s,ue,de,a],type:`VirtualFolderNode`,abstractKey:null}],type:`Node`,abstractKey:`__isNode`}],storageKey:null}],storageKey:null},ae],storageKey:null},se,ce]},params:{cacheID:`669d1fb1c3feb71b69e5f4ce0c87bf8a`,id:null,metadata:{},name:`AdminVFolderNodeListPageQuery`,operationKind:`query`,text:`query AdminVFolderNodeListPageQuery(
  $offset: Int
  $limit: Int
  $filter: VFolderFilter
  $orderBy: [VFolderOrderBy!]
  $filterForActiveCount: VFolderFilter
  $filterForDeletedCount: VFolderFilter
) {
  adminVfoldersV2(offset: $offset, limit: $limit, filter: $filter, orderBy: $orderBy) {
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
  active: adminVfoldersV2(filter: $filterForActiveCount) {
    count
  }
  deleted: adminVfoldersV2(filter: $filterForDeletedCount) {
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

fragment InviteFolderSettingModalFragment on VFolder {
  id
  entityId
  metadata {
    name
    usageMode
  }
  accessControl {
    permission
    ownershipType
  }
  ownership {
    userId
    projectId
  }
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
  ...VFolderNodeIdenticonV2Fragment
  ...SharedFolderPermissionInfoModalV2Fragment
  ...InviteFolderSettingModalFragment
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
`}}})();He.hash=`92e6f71c20673fc29f11689016aa1dd5`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var l=e(n(),1),Ue=c(),u=o(),We=[`DELETE_PENDING`,`DELETE_ONGOING`,`DELETE_ERROR`,`DELETE_COMPLETE`],Ge={status:{notIn:We}},Ke={status:{in:We}},qe=`-created_at`,Je=[`active`,`deleted`],Ye=[`all`,`general`,`data`,`automount`,`model`],Xe={general:{AND:[{name:{iNotStartsWith:`.`}},{usageMode:{equals:`GENERAL`}}]},data:{usageMode:{equals:`DATA`}},automount:{name:{iStartsWith:`.`}},model:{usageMode:{equals:`MODEL`}}},Ze=[`READY`,`CLONING`,`DELETE_PENDING`,`DELETE_ONGOING`,`DELETE_COMPLETE`,`DELETE_ERROR`],Qe=e=>{"use memo";let n=(0,Ve.c)(230),{t:r}=le(),o=Ae(`vfolder`),c=de(),[Se,We]=ae(`table_column_overrides.AdminVFolderNodeListPage`),Qe;n[0]===Symbol.for(`react.memo_cache_sentinel`)?(Qe=[],n[0]=Qe):Qe=n[0];let[d,f]=(0,l.useState)(Qe),[it,at]=he(!1),{toggle:p}=at,[ot,st]=he(!1),{toggle:m}=st,[ct,lt]=he(!1),{toggle:ut}=lt,[dt,ft]=he(!1),{toggle:pt}=ft,mt;n[1]===Symbol.for(`react.memo_cache_sentinel`)?(mt={current:1,pageSize:10},n[1]=mt):mt=n[1];let{baiPaginationOption:h,tablePaginationOption:g,setTablePaginationOption:_}=Ne(mt),ht,gt;n[2]===Symbol.for(`react.memo_cache_sentinel`)?(ht={order:Te(Ie),filter:Ee($e),statusCategory:Te(Je).withDefault(`active`),mode:Te(Ye).withDefault(`all`)},gt={history:`replace`},n[2]=ht,n[3]=gt):(ht=n[2],gt=n[3]);let[v,y]=De(ht,gt),b;n[4]!==v||n[5]!==g?(b={queryParams:v,tablePaginationOption:g},n[4]=v,n[5]=g,n[6]=b):b=n[6];let _t;n[7]!==v.statusCategory||n[8]!==b?(_t={[v.statusCategory]:b},n[7]=v.statusCategory,n[8]=b,n[9]=_t):_t=n[9];let vt=(0,l.useRef)(_t),yt,bt;n[10]!==v||n[11]!==g?(yt=()=>{vt.current[v.statusCategory]={queryParams:v,tablePaginationOption:g}},bt=[v,g],n[10]=v,n[11]=g,n[12]=yt,n[13]=bt):(yt=n[12],bt=n[13]),(0,l.useEffect)(yt,bt);let xt=Xe[v.mode],[St,x]=me(),Ct=v.statusCategory===`deleted`?Ke:Ge,S;n[14]===xt?S=n[15]:(S=xt?[xt]:[],n[14]=xt,n[15]=S);let C;n[16]===v.filter?C=n[17]:(C=v.filter?[v.filter]:[],n[16]=v.filter,n[17]=C);let wt;n[18]!==Ct||n[19]!==S||n[20]!==C?(wt={AND:[Ct,...S,...C]},n[18]=Ct,n[19]=S,n[20]=C,n[21]=wt):wt=n[21];let Tt=wt,Et=h.offset,Dt=h.limit,Ot=v.order||qe,w;n[22]===Ot?w=n[23]:(w=fe(Ot),n[22]=Ot,n[23]=w);let kt;n[24]!==h.limit||n[25]!==h.offset||n[26]!==Tt||n[27]!==w?(kt={offset:Et,limit:Dt,filter:Tt,orderBy:w,filterForActiveCount:Ge,filterForDeletedCount:Ke},n[24]=h.limit,n[25]=h.offset,n[26]=Tt,n[27]=w,n[28]=kt):kt=n[28];let At=kt,jt=(0,l.useDeferredValue)(At),Mt=(0,l.useDeferredValue)(St),Nt=Mt===`first`?`store-and-network`:`network-only`,Pt;n[29]!==Mt||n[30]!==Nt?(Pt={fetchPolicy:Nt,fetchKey:Mt},n[29]=Mt,n[30]=Nt,n[31]=Pt):Pt=n[31];let Ft=(0,Ue.useLazyLoadQuery)(He,jt,Pt),T,E;n[32]===Ft?(T=n[33],E=n[34]):({adminVfoldersV2:T,...E}=Ft,n[32]=Ft,n[33]=T,n[34]=E);let D;n[35]===r?D=n[36]:(D=r(`data.Folders`),n[35]=r,n[36]=D);let It=v.statusCategory,O;n[37]!==y||n[38]!==_?(O=e=>{let t=vt.current[e]||{mode:`all`};y(null),y({...t.queryParams,statusCategory:e},{history:`replace`}),_(t.tablePaginationOption||{current:1}),f([])},n[37]=y,n[38]=_,n[39]=O):O=n[39];let k;if(n[40]!==E||n[41]!==v.statusCategory||n[42]!==r){let e;n[44]!==E||n[45]!==v.statusCategory?(e=(e,t)=>{var ee;let n=((ee=E[t])==null?void 0:ee.count)??0;return{key:t,label:e,endContent:n>0?(0,u.jsx)(ue,{label:n,variant:v.statusCategory===t?`info`:`neutral`}):void 0}},n[44]=E,n[45]=v.statusCategory,n[46]=e):e=n[46],k=a({active:r(`data.Active`),deleted:r(`data.folders.TrashBin`)},e),n[40]=E,n[41]=v.statusCategory,n[42]=r,n[43]=k}else k=n[43];let A;n[47]!==v.statusCategory||n[48]!==O||n[49]!==k?(A=(0,u.jsx)(Me,{activeKey:It,onChange:O,items:k}),n[47]=v.statusCategory,n[48]=O,n[49]=k,n[50]=A):A=n[50];let Lt;n[51]===Symbol.for(`react.memo_cache_sentinel`)?(Lt={flexShrink:1},n[51]=Lt):Lt=n[51];let Rt=v.mode,j;n[52]!==y||n[53]!==_?(j=e=>{y({mode:e}),_({current:1}),f([])},n[52]=y,n[53]=_,n[54]=j):j=n[54];let M;if(n[55]!==c._config.enableModelFolders||n[56]!==c._config.fasttrackEndpoint||n[57]!==r){let e;if(n[59]!==c._config.fasttrackEndpoint||n[60]!==r){var zt;e=(c==null||(zt=c._config)==null?void 0:zt.fasttrackEndpoint)&&{label:r(`data.Pipeline`),value:`data`},n[59]=c._config.fasttrackEndpoint,n[60]=r,n[61]=e}else e=n[61];let t;n[62]!==c._config.enableModelFolders||n[63]!==r?(t=c._config.enableModelFolders&&{label:r(`data.Models`),value:`model`},n[62]=c._config.enableModelFolders,n[63]=r,n[64]=t):t=n[64],M=ge([{label:r(`data.All`),value:`all`},{label:r(`data.General`),value:`general`},e,{label:r(`data.AutoMount`),value:`automount`},t]).map(et),n[55]=c._config.enableModelFolders,n[56]=c._config.fasttrackEndpoint,n[57]=r,n[58]=M}else M=n[58];let N;n[65]!==v.mode||n[66]!==j||n[67]!==M?(N=(0,u.jsx)(xe,{value:Rt,onChange:j,children:M}),n[65]=v.mode,n[66]=j,n[67]=M,n[68]=N):N=n[68];let P;n[69]===r?P=n[70]:(P=r(`data.folders.Name`),n[69]=r,n[70]=P);let F;n[71]===P?F=n[72]:(F={key:`name`,propertyLabel:P,type:`string`},n[71]=P,n[72]=F);let I;n[73]===r?I=n[74]:(I=r(`data.folders.Location`),n[73]=r,n[74]=I);let L;n[75]===I?L=n[76]:(L={key:`host`,propertyLabel:I,type:`string`},n[75]=I,n[76]=L);let R;n[77]===r?R=n[78]:(R=r(`data.folders.Status`),n[77]=r,n[78]=R);let Bt;n[79]===Symbol.for(`react.memo_cache_sentinel`)?(Bt=a([...Ze],tt),n[79]=Bt):Bt=n[79];let z;n[80]===R?z=n[81]:(z={key:`status`,propertyLabel:R,type:`enum`,strictSelection:!0,options:Bt},n[80]=R,n[81]=z);let B;n[82]===r?B=n[83]:(B=r(`data.folders.CreatedAt`),n[82]=r,n[83]=B);let V;n[84]===B?V=n[85]:(V={key:`createdAt`,propertyLabel:B,type:`datetime`},n[84]=B,n[85]=V);let H;n[86]===r?H=n[87]:(H=r(`data.folders.Cloneable`),n[86]=r,n[87]=H);let U;n[88]===H?U=n[89]:(U={key:`cloneable`,propertyLabel:H,type:`boolean`},n[88]=H,n[89]=U);let W;n[90]!==o||n[91]!==r?(W=o?[{key:`labels.some.key`,propertyLabel:r(`entityLabel.LabelKey`),type:`string`},{key:`labels.some.value`,propertyLabel:r(`entityLabel.LabelValue`),type:`string`}]:[],n[90]=o,n[91]=r,n[92]=W):W=n[92];let G;n[93]!==F||n[94]!==L||n[95]!==z||n[96]!==V||n[97]!==U||n[98]!==W?(G=[F,L,z,V,U,...W],n[93]=F,n[94]=L,n[95]=z,n[96]=V,n[97]=U,n[98]=W,n[99]=G):G=n[99];let Vt=v.filter??void 0,K;n[100]!==y||n[101]!==_?(K=e=>{y({filter:e??null}),_({current:1}),f([])},n[100]=y,n[101]=_,n[102]=K):K=n[102];let q;n[103]!==G||n[104]!==Vt||n[105]!==K?(q=(0,u.jsx)(ve,{"data-testid":`vfolder-filter`,filterProperties:G,value:Vt,onChange:K}),n[103]=G,n[104]=Vt,n[105]=K,n[106]=q):q=n[106];let Ht;n[107]!==N||n[108]!==q?(Ht=(0,u.jsxs)(s,{gap:3,align:`start`,style:Lt,wrap:`wrap`,children:[N,q]}),n[107]=N,n[108]=q,n[109]=Ht):Ht=n[109];let J;n[110]!==v.statusCategory||n[111]!==d||n[112]!==r||n[113]!==p||n[114]!==x?(J=d.length>0&&v.statusCategory===`active`&&(0,u.jsxs)(s,{gap:1,align:`center`,children:[(0,u.jsx)(be,{count:d.length,onClearSelection:()=>f([])}),(0,u.jsx)(we,{entityType:`vfolder`,targets:d.map(nt),onLabelsChanged:()=>x()}),(0,u.jsx)(se,{label:r(`data.folders.MoveToTrash`),tooltip:r(`data.folders.MoveToTrash`),icon:(0,u.jsx)(te,{color:`var(--color-error)`}),variant:`ghost`,onClick:()=>{p()}})]}),n[110]=v.statusCategory,n[111]=d,n[112]=r,n[113]=p,n[114]=x,n[115]=J):J=n[115];let Y;n[116]!==v.statusCategory||n[117]!==d.length||n[118]!==r||n[119]!==pt||n[120]!==m?(Y=d.length>0&&v.statusCategory===`deleted`&&(0,u.jsxs)(s,{gap:1,align:`center`,children:[(0,u.jsx)(be,{count:d.length,onClearSelection:()=>f([])}),(0,u.jsx)(se,{label:r(`data.folders.Restore`),tooltip:r(`data.folders.Restore`),icon:(0,u.jsx)(t,{}),variant:`ghost`,onClick:()=>{m()}}),(0,u.jsx)(se,{label:r(`data.folders.Delete`),tooltip:r(`data.folders.Delete`),icon:(0,u.jsx)(ne,{color:`var(--color-error)`}),variant:`ghost`,onClick:()=>{pt()}})]}),n[116]=v.statusCategory,n[117]=d.length,n[118]=r,n[119]=pt,n[120]=m,n[121]=Y):Y=n[121];let Ut=jt!==At||Mt!==St,X;n[122]===x?X=n[123]:(X=e=>{x(e)},n[122]=x,n[123]=X);let Z;n[124]!==St||n[125]!==Ut||n[126]!==X?(Z=(0,u.jsx)(je,{settingId:`admin-vfolder-list`,loading:Ut,value:St,onChange:X}),n[124]=St,n[125]=Ut,n[126]=X,n[127]=Z):Z=n[127];let Wt;n[128]===Symbol.for(`react.memo_cache_sentinel`)?(Wt=(0,u.jsx)(ee,{}),n[128]=Wt):Wt=n[128];let Q;n[129]===r?Q=n[130]:(Q=r(`data.CreateFolder`),n[129]=r,n[130]=Q);let Gt;n[131]===ut?Gt=n[132]:(Gt=()=>{ut()},n[131]=ut,n[132]=Gt);let Kt;n[133]!==Q||n[134]!==Gt?(Kt=(0,u.jsx)(oe,{variant:`primary`,icon:Wt,label:Q,onClick:Gt}),n[133]=Q,n[134]=Gt,n[135]=Kt):Kt=n[135];let qt;n[136]!==J||n[137]!==Y||n[138]!==Z||n[139]!==Kt?(qt=(0,u.jsxs)(s,{gap:2,children:[J,Y,Z,Kt]}),n[136]=J,n[137]=Y,n[138]=Z,n[139]=Kt,n[140]=qt):qt=n[140];let Jt;n[141]!==Ht||n[142]!==qt?(Jt=(0,u.jsxs)(s,{justify:`between`,wrap:`wrap`,gap:3,children:[Ht,qt]}),n[141]=Ht,n[142]=qt,n[143]=Jt):Jt=n[143];let Yt;n[144]===Symbol.for(`react.memo_cache_sentinel`)?(Yt=(0,u.jsx)(ye,{rows:4}),n[144]=Yt):Yt=n[144];let Xt=v.order,Zt=jt!==At,Qt;n[145]===r?Qt=n[146]:(Qt=r(`data.folders.CannotDeployFromAdminMenu`),n[145]=r,n[146]=Qt);let $t;n[147]===(T==null?void 0:T.edges)?$t=n[148]:($t=_e(a(T==null?void 0:T.edges,`node`)),n[147]=T==null?void 0:T.edges,n[148]=$t);let en;if(n[149]!==(T==null?void 0:T.edges)||n[150]!==d){let e;n[152]===(T==null?void 0:T.edges)?e=n[153]:(e=e=>{pe(e,_e(a(T==null?void 0:T.edges,`node`)),f)},n[152]=T==null?void 0:T.edges,n[153]=e);let t;n[154]===d?t=n[155]:(t=a(d,rt),n[154]=d,n[155]=t),en={type:`checkbox`,preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:Pe(e.vfolderStatus)&&e.vfolderStatus!==`DELETE_PENDING`}},onChange:e,selectedRowKeys:t},n[149]=T==null?void 0:T.edges,n[150]=d,n[151]=en}else en=n[151];let tn=(T==null?void 0:T.count)??0,nn;n[156]!==_||n[157]!==tn||n[158]!==g.current||n[159]!==g.pageSize?(nn={pageSize:g.pageSize,current:g.current,total:tn,onChange(e,t){re(e)&&re(t)&&_({current:e,pageSize:t})}},n[156]=_,n[157]=tn,n[158]=g.current,n[159]=g.pageSize,n[160]=nn):nn=n[160];let rn;n[161]===y?rn=n[162]:(rn=e=>{y({order:e??null})},n[161]=y,n[162]=rn);let an;n[163]===x?an=n[164]:(an=()=>x(),n[163]=x,n[164]=an);let on;n[165]!==y||n[166]!==_?(on=e=>{y({filter:Ce(e)}),_({current:1}),f([])},n[165]=y,n[166]=_,n[167]=on):on=n[167];let sn;n[168]===x?sn=n[169]:(sn=e=>{f(t=>i(t,t=>t.id!==e)),x()},n[168]=x,n[169]=sn);let cn;n[170]===Symbol.for(`react.memo_cache_sentinel`)?(cn={cur_size:{hidden:!1},max_size:{hidden:!1},created_at:{hidden:!1}},n[170]=cn):cn=n[170];let $;n[171]!==Se||n[172]!==We?($={columnOverrides:Se,defaultColumnOverrides:cn,onColumnOverridesChange:We},n[171]=Se,n[172]=We,n[173]=$):$=n[173];let ln;n[174]!==v.order||n[175]!==Zt||n[176]!==Qt||n[177]!==$t||n[178]!==en||n[179]!==nn||n[180]!==rn||n[181]!==an||n[182]!==on||n[183]!==sn||n[184]!==$?(ln=(0,u.jsx)(l.Suspense,{fallback:Yt,children:(0,u.jsx)(Le,{order:Xt,loading:Zt,project:null,noDeployTooltip:Qt,vfoldersFrgmt:$t,rowSelection:en,pagination:nn,onChangeOrder:rn,onLabelsChanged:an,showLabelsByDefault:!0,onLabelClick:on,onRemoveRow:sn,tableSettings:$})}),n[174]=v.order,n[175]=Zt,n[176]=Qt,n[177]=$t,n[178]=en,n[179]=nn,n[180]=rn,n[181]=an,n[182]=on,n[183]=sn,n[184]=$,n[185]=ln):ln=n[185];let un;n[186]!==Jt||n[187]!==ln?(un=(0,u.jsxs)(ce,{align:`stretch`,gap:3,children:[Jt,ln]}),n[186]=Jt,n[187]=ln,n[188]=un):un=n[188];let dn;n[189]!==D||n[190]!==A||n[191]!==un?(dn=(0,u.jsxs)(ke,{title:D,children:[A,un]}),n[189]=D,n[190]=A,n[191]=un,n[192]=dn):dn=n[192];let fn;n[193]!==p||n[194]!==x?(fn=(e,t)=>{e&&x(),t&&f(e=>i(e,e=>ie(t,e.id))),p()},n[193]=p,n[194]=x,n[195]=fn):fn=n[195];let pn;n[196]!==it||n[197]!==d||n[198]!==fn?(pn=(0,u.jsx)(ze,{vfolderFrgmts:d,open:it,onRequestClose:fn}),n[196]=it,n[197]=d,n[198]=fn,n[199]=pn):pn=n[199];let mn;n[200]!==m||n[201]!==x?(mn=e=>{e&&(x(),f([])),m()},n[200]=m,n[201]=x,n[202]=mn):mn=n[202];let hn;n[203]!==ot||n[204]!==d||n[205]!==mn?(hn=(0,u.jsx)(Be,{vfolderFrgmts:d,open:ot,onRequestClose:mn}),n[203]=ot,n[204]=d,n[205]=mn,n[206]=hn):hn=n[206];let gn;n[207]!==pt||n[208]!==x?(gn=e=>{e&&(x(),f([])),pt()},n[207]=pt,n[208]=x,n[209]=gn):gn=n[209];let _n;n[210]!==dt||n[211]!==d||n[212]!==gn?(_n=(0,u.jsx)(Fe,{vfolderFrgmts:d,open:dt,onRequestClose:gn}),n[210]=dt,n[211]=d,n[212]=gn,n[213]=_n):_n=n[213];let vn;n[214]===r?vn=n[215]:(vn=r(`data.folders.AdminDataPageAlert`),n[214]=r,n[215]=vn);let yn;n[216]!==ut||n[217]!==x?(yn=e=>{ut(),e&&x()},n[216]=ut,n[217]=x,n[218]=yn):yn=n[218];let bn;n[219]!==ct||n[220]!==vn||n[221]!==yn?(bn=(0,u.jsx)(Re,{open:ct,project:null,alertMessage:vn,onRequestClose:yn}),n[219]=ct,n[220]=vn,n[221]=yn,n[222]=bn):bn=n[222];let xn;return n[223]!==e||n[224]!==dn||n[225]!==pn||n[226]!==hn||n[227]!==_n||n[228]!==bn?(xn=(0,u.jsx)(Oe,{children:(0,u.jsxs)(ce,{align:`stretch`,gap:5,...e,children:[dn,pn,hn,_n,bn]})}),n[223]=e,n[224]=dn,n[225]=pn,n[226]=hn,n[227]=_n,n[228]=bn,n[229]=xn):xn=n[229],xn};function $e(e){return e}function et(e){return(0,u.jsx)(Se,{value:e.value,label:e.label},e.value)}function tt(e){return{label:e,value:e}}function nt(e){var t;return{entityId:e.entityId,name:((t=e.metadata)==null?void 0:t.name)??void 0}}function rt(e){return e.id}export{Qe as default};
