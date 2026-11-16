import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{F as t,Zn as n,d as r,f as i}from"./icons-Btg1s2wy.js";import{t as a}from"./compiler-runtime-CZQb2eIb.js";import{St as o,nt as s,ut as c,vt as l}from"./lodash-ClfL87UH.js";/* empty css            */import{t as u}from"./jsx-runtime-BapUIyWk.js";import{O as d,at as f,d as p}from"./DefaultProviders-BFjPhnQa.js";import{t as m}from"./Button-BKkkrlg5.js";import{t as h}from"./IconButton-DGkWhkpU.js";import{t as g}from"./VStack-DaUzGF31.js";import{r as _,u as v}from"./Skeleton-D35z7Ria.js";import{t as y}from"./BAITabCountBadge-CbZcLm1Q.js";import{H as b,d as x,rt as ee,y as te}from"./helper-BWFKT_2Y.js";import{r as ne}from"./hooks-UUY7pxyu.js";import{t as S}from"./react-relay-BfoHYpUf.js";import{t as re}from"./useToggle-CAWNf18k.js";import{l as ie,o as ae,u as oe}from"./helper-DF1Eunoe.js";import{t as se}from"./BAIGraphQLPropertyFilter-CNTUQIkF.js";import{t as ce}from"./BAISkeleton-MIjJv1Hr.js";import{t as le}from"./BAISelectionLabel-BTMbVxpE.js";import{n as ue,t as C}from"./BAISegmentedControlItem-erYb9KqU.js";import{i as de}from"./BAIEntityLabelCell-DOyaclRH.js";import{t as fe}from"./BAIEntityLabelBulkEditButton-CRMSgz-m.js";import{a as pe,i as me,n as he,o as ge,r as _e}from"./dist-C3M-rFln.js";import{n as ve}from"./useAccessibleProjects-gzoxrvLz.js";import{t as ye}from"./useCurrentProject-BaleCvMA.js";import{W as be,ht as xe,pt as Se,t as Ce}from"./index-49VU5B_r.js";import{t as we}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{t as Te}from"./BAITabs-Bwz-IwE5.js";import{n as Ee}from"./reactPaginationQueryOptions-DUCwh22X.js";import{a as De,i as Oe,n as ke,t as Ae}from"./VFolderNodesV2-Phte8jg6.js";import{t as je}from"./useVFolderInvitations-D_zm5Puj.js";import{n as Me}from"./useCreateActionArrival-CjxWphnh.js";import{t as Ne}from"./FolderCreateModal-CeqkMhk8.js";import{a as Pe,i as w,n as T,o as Fe,s as Ie}from"./webmcpPageTools-8wcgPkH7.js";import{n as Le,t as Re}from"./RestoreVFolderModalV2-QPHAf-cN.js";var ze=a(),Be=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`filterForActiveCount`},n={defaultValue:null,kind:`LocalArgument`,name:`filterForDeletedCount`},r={defaultValue:null,kind:`LocalArgument`,name:`limit`},i={defaultValue:null,kind:`LocalArgument`,name:`offset`},a={defaultValue:null,kind:`LocalArgument`,name:`orderBy`},o={defaultValue:null,kind:`LocalArgument`,name:`scope`},s={kind:`Variable`,name:`scope`,variableName:`scope`},c=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`limit`,variableName:`limit`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`orderBy`,variableName:`orderBy`},s],l={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},u={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},d={alias:`vfolderStatus`,args:null,kind:`ScalarField`,name:`status`,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},p=[f],m={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},h=[m],g={alias:`active`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForActiveCount`},s],concreteType:`VFolderConnection`,kind:`LinkedField`,name:`scopedVFoldersV2`,plural:!1,selections:h,storageKey:null},_={alias:`deleted`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForDeletedCount`},s],concreteType:`VFolderConnection`,kind:`LinkedField`,name:`scopedVFoldersV2`,plural:!1,selections:h,storageKey:null},v=[{alias:null,args:null,kind:`ScalarField`,name:`expr`,storageKey:null}],y={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},b={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},x={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null};return{fragment:{argumentDefinitions:[e,t,n,r,i,a,o],kind:`Fragment`,metadata:null,name:`VFolderNodeListPageQuery`,selections:[{alias:null,args:c,concreteType:`VFolderConnection`,kind:`LinkedField`,name:`scopedVFoldersV2`,plural:!1,selections:[{kind:`RequiredField`,field:{alias:null,args:null,concreteType:`VFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{kind:`RequiredField`,field:{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{kind:`RequiredField`,field:l,action:`THROW`},u,d,{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:p,storageKey:null},{args:null,kind:`FragmentSpread`,name:`VFolderNodesV2Fragment`},{args:null,kind:`FragmentSpread`,name:`WebMCPVFolderListToolsFragment`},{args:null,kind:`FragmentSpread`,name:`DeleteVFolderModalV2Fragment`},{args:null,kind:`FragmentSpread`,name:`DeleteForeverVFolderModalV2Fragment`},{args:null,kind:`FragmentSpread`,name:`RestoreVFolderModalV2Fragment`}],storageKey:null},action:`THROW`}],storageKey:null},action:`THROW`},m],storageKey:null},g,_],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[o,i,r,e,a,t,n],kind:`Operation`,name:`VFolderNodeListPageQuery`,selections:[{alias:null,args:c,concreteType:`VFolderConnection`,kind:`LinkedField`,name:`scopedVFoldersV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`VFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`node`,plural:!1,selections:[l,u,d,{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[f,{alias:null,args:null,kind:`ScalarField`,name:`usageMode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quotaScopeId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`lastUsed`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cloneable`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`host`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`unmanagedPath`,storageKey:null},{alias:null,args:null,concreteType:`VFolderUsageInfo`,kind:`LinkedField`,name:`usage`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`numFiles`,storageKey:null},{alias:null,args:null,concreteType:`BinarySizeInfo`,kind:`LinkedField`,name:`usedBytes`,plural:!1,selections:v,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderAccessControlInfo`,kind:`LinkedField`,name:`accessControl`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`permission`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`ownershipType`,storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`permissions`,storageKey:null},{alias:null,args:null,concreteType:`VFolderQuotaInfo`,kind:`LinkedField`,name:`quota`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`maxFiles`,storageKey:null},{alias:null,args:null,concreteType:`BinarySizeInfo`,kind:`LinkedField`,name:`maxSize`,plural:!1,selections:v,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderOwnershipInfo`,kind:`LinkedField`,name:`ownership`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`userId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`projectId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`creatorEmail`,storageKey:null},{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`user`,plural:!1,selections:[{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null}],storageKey:null},l],storageKey:null},{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`project`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:p,storageKey:null},l],storageKey:null}],storageKey:null},{alias:null,args:[{kind:`Literal`,name:`limit`,value:100}],concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityLabelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityLabel`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null},l,{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:`entityLabels(limit:100)`},{kind:`InlineFragment`,selections:[{kind:`InlineFragment`,selections:[y,b,f,x,{alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`user_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`scaling_group`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`project_id`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},l,x,{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},b],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`vfolder_mounts`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[f,l],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_size`,storageKey:null}],type:`ComputeSessionNode`,abstractKey:null},{kind:`InlineFragment`,selections:[y],type:`VFolder`,abstractKey:null},{kind:`InlineFragment`,selections:[y,b,x,f],type:`VirtualFolderNode`,abstractKey:null}],type:`Node`,abstractKey:`__isNode`}],storageKey:null}],storageKey:null},m],storageKey:null},g,_]},params:{cacheID:`a03c632b161ac30df34ce4447c26e82a`,id:null,metadata:{},name:`VFolderNodeListPageQuery`,operationKind:`query`,text:`query VFolderNodeListPageQuery(
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
        ...WebMCPVFolderListToolsFragment
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

fragment WebMCPVFolderListToolsFragment on VFolder {
  entityId
  vfolderStatus: status
  host
  usage {
    numFiles
    usedBytes {
      expr @since(version: "26.8.0")
    }
  }
  metadata {
    name
    usageMode
    createdAt
    lastUsed
    cloneable
  }
  accessControl {
    ownershipType
  }
  ownership {
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
}

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();Be.hash=`be1bd74ffffaaacd8623ee623748c0d6`;var E=(function(){var e={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null};return{argumentDefinitions:[],kind:`Fragment`,metadata:{plural:!0},name:`WebMCPVFolderListToolsFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:`vfolderStatus`,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`host`,storageKey:null},{alias:null,args:null,concreteType:`VFolderUsageInfo`,kind:`LinkedField`,name:`usage`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`numFiles`,storageKey:null},{alias:null,args:null,concreteType:`BinarySizeInfo`,kind:`LinkedField`,name:`usedBytes`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`expr`,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[e,{alias:null,args:null,kind:`ScalarField`,name:`usageMode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`lastUsed`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cloneable`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderAccessControlInfo`,kind:`LinkedField`,name:`accessControl`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`ownershipType`,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`VFolderOwnershipInfo`,kind:`LinkedField`,name:`ownership`,plural:!1,selections:[{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`user`,plural:!1,selections:[{alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`project`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[e],storageKey:null}],storageKey:null}],storageKey:null}],type:`VFolder`,abstractKey:null}})();E.hash=`13dc2202728cbda4bf684786bba2e834`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var Ve=S(),D=u(),He=`folder`,Ue=`path`,O=[{key:`name`,fields:[`name`],required:!0},{key:`status`,fields:[`status`]},{key:`host`,fields:[`host`]},{key:`ownership_type`,fields:[`ownershipType`]},{key:`owner`,fields:[`owner`]},{key:`usage_mode`,fields:[`usageMode`],defaultHidden:!0},{key:`num_files`,fields:[`numFiles`],defaultHidden:!0},{key:`cur_size`,fields:[`usageBytes`],defaultHidden:!0},{key:`cloneable`,fields:[`cloneable`],defaultHidden:!0},{key:`last_used`,fields:[`lastUsed`],defaultHidden:!0},{key:`created_at`,fields:[`createdAt`],defaultHidden:!0}],k=e=>{"use memo";let t=(0,ze.c)(28),{vfoldersFrgmt:n,columnOverrides:r,page:i,pageSize:a,total:o,pending:s,viewParams:c}=e,{pathname:u,search:d}=ee(),f=(0,Ve.useFragment)(E,n),p;if(t[0]!==r||t[1]!==i||t[2]!==a||t[3]!==s||t[4]!==o||t[5]!==f){let e=l(oe(f),Ge);p=Ie({rows:e,columns:O,columnOverrides:r,page:i,pageSize:a,total:o,pending:s}),t[0]=r,t[1]=i,t[2]=a,t[3]=s,t[4]=o,t[5]=f,t[6]=p}else p=t[6];let m=p,h,g;if(t[7]!==d){let e=new URLSearchParams(d);h=e.get(He),g=e.get(Ue),t[7]=d,t[8]=h,t[9]=g}else h=t[8],g=t[9];let _=g,v;t[10]===m?v=t[11]:(v=()=>m,t[10]=m,t[11]=v);let y;t[12]!==i||t[13]!==a||t[14]!==u||t[15]!==s||t[16]!==c?(y=()=>Fe(u,{...c,current:i,pageSize:a},s),t[12]=i,t[13]=a,t[14]=u,t[15]=s,t[16]=c,t[17]=y):y=t[17];let b;t[18]!==_||t[19]!==m||t[20]!==h||t[21]!==u||t[22]!==d?(b=()=>{let e=T(m.rows,h&&ae(h).toLowerCase(),w(u,d,He,h??``));return e&&{...e,folderPath:_??null}},t[18]=_,t[19]=m,t[20]=h,t[21]=u,t[22]=d,t[23]=b):b=t[23];let x;return t[24]!==v||t[25]!==y||t[26]!==b?(x={noun:`vfolder`,plural:`folders`,rowFields:`Row fields: id (folder UUID), name, status, host, ownershipType (USER or GROUP), owner, usageMode, numFiles, usageBytes, cloneable, lastUsed, createdAt.`,currentMeaning:`the folder open in the file explorer, with folderPath being the directory shown inside it`,readRows:v,readViewState:y,readCurrent:b},t[24]=v,t[25]=y,t[26]=b,t[27]=x):x=t[27],Pe(x),null},We=e=>{"use memo";let t=(0,ze.c)(3),n=be(),r;return t[0]!==n||t[1]!==e?(r=n?(0,D.jsx)(k,{...e}):null,t[0]=n,t[1]=e,t[2]=r):r=t[2],r};function Ge(e){var t,n,r,i,a,o,s,c,l,u,d;return{id:e.entityId,name:((t=e.metadata)==null?void 0:t.name)??null,status:e.vfolderStatus??null,host:e.host??null,ownershipType:((n=e.accessControl)==null?void 0:n.ownershipType)??null,owner:(((r=e.accessControl)==null?void 0:r.ownershipType)===`USER`?(i=e.ownership)==null||(i=i.user)==null||(i=i.basicInfo)==null?void 0:i.email:(a=e.ownership)==null||(a=a.project)==null||(a=a.basicInfo)==null?void 0:a.name)??null,usageMode:((o=e.metadata)==null?void 0:o.usageMode)??null,numFiles:((s=e.usage)==null?void 0:s.numFiles)??null,usageBytes:((c=e.usage)==null||(c=c.usedBytes)==null?void 0:c.expr)??null,cloneable:((l=e.metadata)==null?void 0:l.cloneable)??null,lastUsed:((u=e.metadata)==null?void 0:u.lastUsed)??null,createdAt:((d=e.metadata)==null?void 0:d.createdAt)??null}}
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var A=e(n(),1),Ke=`-created_at`,qe=[`active`,`deleted`],Je=[`all`,`general`,`data`,`automount`,`model`],Ye=[`DELETE_PENDING`,`DELETE_ONGOING`,`DELETE_ERROR`,`DELETE_COMPLETE`],Xe=[`DELETE_PENDING`,`DELETE_ONGOING`,`DELETE_ERROR`],Ze={status:{notIn:Ye}},Qe={status:{in:Xe}},$e=[`READY`,`CLONING`,`DELETE_PENDING`,`DELETE_ONGOING`,`DELETE_COMPLETE`,`DELETE_ERROR`],et={general:{AND:[{name:{iNotStartsWith:`.`}},{usageMode:{equals:`GENERAL`}}]},data:{usageMode:{equals:`DATA`}},automount:{name:{iStartsWith:`.`}},model:{usageMode:{equals:`MODEL`}}},tt=e=>{"use memo";let n=(0,ze.c)(265),a;n[0]===e?a=n[1]:({...a}=e,n[0]=e,n[1]=a);let{t:u}=_(),ee=Se(`vfolder`),S=ye(),ae;n[2]===S?ae=n[3]:(ae=Ce(S),n[2]=S,n[3]=ae);let C=ae,be=ve(S.id),[Pe]=p(),w=b(),[T]=je(),Fe;n[4]===Symbol.for(`react.memo_cache_sentinel`)?(Fe=_e.withOptions({history:`replace`}),n[4]=Fe):Fe=n[4];let[,Ie]=pe(`invitation`,Fe),[E,He]=d(`table_column_overrides.VFolderNodeListPage`),Ue;n[5]===Symbol.for(`react.memo_cache_sentinel`)?(Ue=[],n[5]=Ue):Ue=n[5];let[O,k]=(0,A.useState)(Ue),[Ge,Ye]=(0,A.useState)(S.id);Ge!==S.id&&(Ye(S.id),k([]));let[Xe,tt]=re(!1),{toggle:j,setRight:st}=tt,[ct,lt]=re(!1),{toggle:M}=lt,[ut,dt]=re(!1),{toggle:N}=dt,[ft,pt]=re(!1),{toggle:P}=pt,mt;n[6]===Symbol.for(`react.memo_cache_sentinel`)?(mt={current:1,pageSize:10},n[6]=mt):mt=n[6];let{baiPaginationOption:F,tablePaginationOption:I,setTablePaginationOption:L}=Ee(mt),ht,gt;n[7]===Symbol.for(`react.memo_cache_sentinel`)?(gt={order:me(ke),filter:he(nt),statusCategory:me(qe).withDefault(`active`),mode:me(Je).withDefault(`all`)},ht={history:`replace`},n[7]=ht,n[8]=gt):(ht=n[7],gt=n[8]);let[R,z]=ge(gt,ht),B;n[9]!==R||n[10]!==I?(B={queryParams:R,tablePaginationOption:I},n[9]=R,n[10]=I,n[11]=B):B=n[11];let _t;n[12]!==R.statusCategory||n[13]!==B?(_t={[R.statusCategory]:B},n[12]=R.statusCategory,n[13]=B,n[14]=_t):_t=n[14];let vt=(0,A.useRef)(_t),yt,bt;n[15]!==R||n[16]!==I?(yt=()=>{vt.current[R.statusCategory]={queryParams:R,tablePaginationOption:I}},bt=[R,I],n[15]=R,n[16]=I,n[17]=yt,n[18]=bt):(yt=n[17],bt=n[18]),(0,A.useEffect)(yt,bt);let xt=et[R.mode],[St,V]=ne(),Ct=R.statusCategory===`deleted`?Qe:Ze,H;n[19]===xt?H=n[20]:(H=xt?[xt]:[],n[19]=xt,n[20]=H);let U;n[21]===R.filter?U=n[22]:(U=R.filter?[R.filter]:[],n[21]=R.filter,n[22]=U);let wt;n[23]!==Ct||n[24]!==H||n[25]!==U?(wt={AND:[Ct,...H,...U]},n[23]=Ct,n[24]=H,n[25]=U,n[26]=wt):wt=n[26];let Tt=wt,Et;n[27]===V?Et=n[28]:(Et=()=>{V()},n[27]=V,n[28]=Et);let Dt=(0,A.useEffectEvent)(Et),Ot;n[29]===Dt?Ot=n[30]:(Ot=()=>{Dt()},n[29]=Dt,n[30]=Ot);let kt;n[31]===T.length?kt=n[32]:(kt=[T.length],n[31]=T.length,n[32]=kt),(0,A.useEffect)(Ot,kt),Me(st);let At;n[33]!==Pe||n[34]!==C?(At=C?{project:[{value:C.id}]}:{user:[{value:Pe.uuid}]},n[33]=Pe,n[34]=C,n[35]=At):At=n[35];let jt=At,Mt=F.offset,Nt=F.limit,Pt=R.order||Ke,W;n[36]===Pt?W=n[37]:(W=x(Pt),n[36]=Pt,n[37]=W);let Ft;n[38]!==F.limit||n[39]!==F.offset||n[40]!==Tt||n[41]!==W||n[42]!==jt?(Ft={scope:jt,offset:Mt,limit:Nt,filter:Tt,orderBy:W,filterForActiveCount:Ze,filterForDeletedCount:Qe},n[38]=F.limit,n[39]=F.offset,n[40]=Tt,n[41]=W,n[42]=jt,n[43]=Ft):Ft=n[43];let It=Ft,Lt=(0,A.useDeferredValue)(It),Rt=(0,A.useDeferredValue)(St),zt=Rt===`first`?`store-and-network`:`network-only`,Bt;n[44]!==Rt||n[45]!==zt?(Bt={fetchPolicy:zt,fetchKey:Rt},n[44]=Rt,n[45]=zt,n[46]=Bt):Bt=n[46];let Vt=(0,Ve.useLazyLoadQuery)(Be,Lt,Bt),G,K;n[47]===Vt?(G=n[48],K=n[49]):({scopedVFoldersV2:K,...G}=Vt,n[47]=Vt,n[48]=G,n[49]=K);let Ht;n[50]===(K==null?void 0:K.edges)?Ht=n[51]:(Ht=oe(l(K==null?void 0:K.edges,`node`)),n[50]=K==null?void 0:K.edges,n[51]=Ht);let q=Ht,J;n[52]===u?J=n[53]:(J=u(`data.Folders`),n[52]=u,n[53]=J);let Y;n[54]===u?Y=n[55]:(Y=u(`data.CreateFolder`),n[54]=u,n[55]=Y);let X;n[56]===j?X=n[57]:(X=()=>{j()},n[56]=j,n[57]=X);let Z;n[58]!==Y||n[59]!==X?(Z=(0,D.jsx)(m,{variant:`primary`,label:Y,onClick:X}),n[58]=Y,n[59]=X,n[60]=Z):Z=n[60];let Ut=R.statusCategory,Wt;n[61]!==z||n[62]!==L?(Wt=e=>{let t=vt.current[e]||{mode:`all`};z(null),z({...t.queryParams,statusCategory:e}),L(t.tablePaginationOption||{current:1}),k([])},n[61]=z,n[62]=L,n[63]=Wt):Wt=n[63];let Gt;n[64]!==T.length||n[65]!==Ie||n[66]!==u?(Gt=T.length>0?(0,D.jsx)(f,{href:`#`,onClick:e=>{e.preventDefault(),Ie(`true`)},children:`${u(`data.invitation.PendingInvitations`)} (${T.length})`}):void 0,n[64]=T.length,n[65]=Ie,n[66]=u,n[67]=Gt):Gt=n[67];let Kt;n[68]===u?Kt=n[69]:(Kt=u(`data.Active`),n[68]=u,n[69]=Kt);let qt;n[70]===Kt?qt=n[71]:(qt=[`active`,Kt],n[70]=Kt,n[71]=qt);let Jt;n[72]===u?Jt=n[73]:(Jt=u(`data.folders.TrashBin`),n[72]=u,n[73]=Jt);let Yt;n[74]===Jt?Yt=n[75]:(Yt=[`deleted`,Jt],n[74]=Jt,n[75]=Yt);let Xt;n[76]!==qt||n[77]!==Yt?(Xt=[qt,Yt],n[76]=qt,n[77]=Yt,n[78]=Xt):Xt=n[78];let Zt=Xt,Qt;n[79]!==G||n[80]!==R.statusCategory||n[81]!==Zt?(Qt=Zt.map(e=>{var t;let[n,r]=e;return{key:n,label:r,endContent:(0,D.jsx)(y,{count:(t=G[n])==null?void 0:t.count,selected:R.statusCategory===n})}}),n[79]=G,n[80]=R.statusCategory,n[81]=Zt,n[82]=Qt):Qt=n[82];let $t;n[83]!==R.statusCategory||n[84]!==Wt||n[85]!==Gt||n[86]!==Qt?($t=(0,D.jsx)(Te,{activeKey:Ut,onChange:Wt,tabBarExtraContent:Gt,items:Qt}),n[83]=R.statusCategory,n[84]=Wt,n[85]=Gt,n[86]=Qt,n[87]=$t):$t=n[87];let en;n[88]===Symbol.for(`react.memo_cache_sentinel`)?(en={flexShrink:1},n[88]=en):en=n[88];let tn=R.mode,nn;n[89]!==z||n[90]!==L?(nn=e=>{z({mode:e}),L({current:1}),k([])},n[89]=z,n[90]=L,n[91]=nn):nn=n[91];let rn;if(n[92]!==w._config.enableModelFolders||n[93]!==w._config.fasttrackEndpoint||n[94]!==u){let e;if(n[96]!==w._config.fasttrackEndpoint||n[97]!==u){var an;e=(w==null||(an=w._config)==null?void 0:an.fasttrackEndpoint)&&{label:u(`data.Pipeline`),value:`data`},n[96]=w._config.fasttrackEndpoint,n[97]=u,n[98]=e}else e=n[98];let t;n[99]!==w._config.enableModelFolders||n[100]!==u?(t=w._config.enableModelFolders&&{label:u(`data.Models`),value:`model`},n[99]=w._config.enableModelFolders,n[100]=u,n[101]=t):t=n[101],rn=ie([{label:u(`data.All`),value:`all`},{label:u(`data.General`),value:`general`},e,{label:u(`data.AutoMount`),value:`automount`},t]).map(rt),n[92]=w._config.enableModelFolders,n[93]=w._config.fasttrackEndpoint,n[94]=u,n[95]=rn}else rn=n[95];let on;n[102]!==R.mode||n[103]!==nn||n[104]!==rn?(on=(0,D.jsx)(ue,{value:tn,onChange:nn,children:rn}),n[102]=R.mode,n[103]=nn,n[104]=rn,n[105]=on):on=n[105];let sn;n[106]===u?sn=n[107]:(sn=u(`data.folders.Name`),n[106]=u,n[107]=sn);let cn;n[108]===sn?cn=n[109]:(cn={key:`name`,propertyLabel:sn,type:`string`},n[108]=sn,n[109]=cn);let ln;n[110]===u?ln=n[111]:(ln=u(`data.folders.Status`),n[110]=u,n[111]=ln);let un;n[112]===Symbol.for(`react.memo_cache_sentinel`)?(un=l([...$e],it),n[112]=un):un=n[112];let dn;n[113]===ln?dn=n[114]:(dn={key:`status`,propertyLabel:ln,type:`enum`,strictSelection:!0,defaultOperator:`equals`,options:un},n[113]=ln,n[114]=dn);let fn;n[115]===u?fn=n[116]:(fn=u(`data.folders.Location`),n[115]=u,n[116]=fn);let pn;n[117]===fn?pn=n[118]:(pn={key:`host`,propertyLabel:fn,type:`string`},n[117]=fn,n[118]=pn);let mn;n[119]===u?mn=n[120]:(mn=u(`data.folders.Cloneable`),n[119]=u,n[120]=mn);let hn;n[121]===mn?hn=n[122]:(hn={key:`cloneable`,propertyLabel:mn,type:`boolean`},n[121]=mn,n[122]=hn);let gn;n[123]!==ee||n[124]!==u?(gn=ee?[{key:`labels.some.key`,propertyLabel:u(`entityLabel.LabelKey`),type:`string`},{key:`labels.some.value`,propertyLabel:u(`entityLabel.LabelValue`),type:`string`}]:[],n[123]=ee,n[124]=u,n[125]=gn):gn=n[125];let _n;n[126]!==cn||n[127]!==dn||n[128]!==pn||n[129]!==hn||n[130]!==gn?(_n=[cn,dn,pn,hn,...gn],n[126]=cn,n[127]=dn,n[128]=pn,n[129]=hn,n[130]=gn,n[131]=_n):_n=n[131];let vn=R.filter??void 0,yn;n[132]!==z||n[133]!==L?(yn=e=>{z({filter:e??null}),L({current:1}),k([])},n[132]=z,n[133]=L,n[134]=yn):yn=n[134];let bn;n[135]!==_n||n[136]!==vn||n[137]!==yn?(bn=(0,D.jsx)(se,{"data-testid":`vfolder-filter`,filterProperties:_n,value:vn,onChange:yn}),n[135]=_n,n[136]=vn,n[137]=yn,n[138]=bn):bn=n[138];let xn;n[139]!==on||n[140]!==bn?(xn=(0,D.jsxs)(v,{gap:3,align:`start`,style:en,wrap:`wrap`,children:[on,bn]}),n[139]=on,n[140]=bn,n[141]=xn):xn=n[141];let Sn;n[142]!==R.statusCategory||n[143]!==O||n[144]!==u||n[145]!==M||n[146]!==V?(Sn=O.length>0&&R.statusCategory===`active`&&(0,D.jsxs)(v,{gap:1,align:`center`,children:[(0,D.jsx)(le,{count:O.length,onClearSelection:()=>k([])}),(0,D.jsx)(fe,{entityType:`vfolder`,targets:O.map(at),onLabelsChanged:()=>V()}),(0,D.jsx)(h,{label:u(`data.folders.MoveToTrash`),tooltip:u(`data.folders.MoveToTrash`),icon:(0,D.jsx)(r,{color:`var(--color-error)`}),variant:`ghost`,onClick:()=>{M()}})]}),n[142]=R.statusCategory,n[143]=O,n[144]=u,n[145]=M,n[146]=V,n[147]=Sn):Sn=n[147];let Cn;n[148]!==R.statusCategory||n[149]!==O.length||n[150]!==u||n[151]!==P||n[152]!==N?(Cn=O.length>0&&R.statusCategory===`deleted`&&(0,D.jsxs)(v,{gap:1,align:`center`,children:[(0,D.jsx)(le,{count:O.length,onClearSelection:()=>k([])}),(0,D.jsx)(h,{label:u(`data.folders.Restore`),tooltip:u(`data.folders.Restore`),icon:(0,D.jsx)(t,{}),variant:`ghost`,onClick:()=>{N()}}),(0,D.jsx)(h,{label:u(`data.folders.Delete`),tooltip:u(`data.folders.Delete`),icon:(0,D.jsx)(i,{color:`var(--color-error)`}),variant:`ghost`,onClick:()=>{P()}})]}),n[148]=R.statusCategory,n[149]=O.length,n[150]=u,n[151]=P,n[152]=N,n[153]=Cn):Cn=n[153];let wn=Lt!==It||Rt!==St,Tn;n[154]===V?Tn=n[155]:(Tn=e=>{V(e)},n[154]=V,n[155]=Tn);let En;n[156]!==St||n[157]!==wn||n[158]!==Tn?(En=(0,D.jsx)(we,{settingId:`vfolder-list`,loading:wn,value:St,onChange:Tn}),n[156]=St,n[157]=wn,n[158]=Tn,n[159]=En):En=n[159];let Dn;n[160]!==Sn||n[161]!==Cn||n[162]!==En?(Dn=(0,D.jsxs)(v,{gap:2,children:[Sn,Cn,En]}),n[160]=Sn,n[161]=Cn,n[162]=En,n[163]=Dn):Dn=n[163];let On;n[164]!==xn||n[165]!==Dn?(On=(0,D.jsxs)(v,{justify:`between`,wrap:`wrap`,gap:3,children:[xn,Dn]}),n[164]=xn,n[165]=Dn,n[166]=On):On=n[166];let kn=K==null?void 0:K.count,An=Lt!==It,jn;n[167]===R.filter?jn=n[168]:(jn=R.filter?JSON.stringify(R.filter):null,n[167]=R.filter,n[168]=jn);let Mn;n[169]!==R||n[170]!==jn?(Mn={...R,filter:jn},n[169]=R,n[170]=jn,n[171]=Mn):Mn=n[171];let Nn;n[172]!==E||n[173]!==kn||n[174]!==An||n[175]!==Mn||n[176]!==I.current||n[177]!==I.pageSize||n[178]!==q?(Nn=(0,D.jsx)(We,{vfoldersFrgmt:q,columnOverrides:E,page:I.current,pageSize:I.pageSize,total:kn,pending:An,viewParams:Mn}),n[172]=E,n[173]=kn,n[174]=An,n[175]=Mn,n[176]=I.current,n[177]=I.pageSize,n[178]=q,n[179]=Nn):Nn=n[179];let Pn;n[180]===Symbol.for(`react.memo_cache_sentinel`)?(Pn=(0,D.jsx)(ce,{rows:4}),n[180]=Pn):Pn=n[180];let Fn=R.order,In=Lt!==It,Ln;if(n[181]!==O||n[182]!==q){let e;n[184]===q?e=n[185]:(e=e=>{te(e,q,k)},n[184]=q,n[185]=e);let t;n[186]===O?t=n[187]:(t=l(O,ot),n[186]=O,n[187]=t),Ln={type:`checkbox`,preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:De(e.vfolderStatus)&&e.vfolderStatus!==`DELETE_PENDING`}},onChange:e,selectedRowKeys:t},n[181]=O,n[182]=q,n[183]=Ln}else Ln=n[183];let Rn=(K==null?void 0:K.count)??0,zn;n[188]!==L||n[189]!==Rn||n[190]!==I.current||n[191]!==I.pageSize?(zn={pageSize:I.pageSize,current:I.current,total:Rn,onChange(e,t){s(e)&&s(t)&&L({current:e,pageSize:t})}},n[188]=L,n[189]=Rn,n[190]=I.current,n[191]=I.pageSize,n[192]=zn):zn=n[192];let Bn;n[193]===z?Bn=n[194]:(Bn=e=>{z({order:e??null})},n[193]=z,n[194]=Bn);let Vn;n[195]===V?Vn=n[196]:(Vn=()=>V(),n[195]=V,n[196]=Vn);let Q;n[197]!==z||n[198]!==L?(Q=e=>{z({filter:de(e)}),L({current:1}),k([])},n[197]=z,n[198]=L,n[199]=Q):Q=n[199];let Hn;n[200]===V?Hn=n[201]:(Hn=e=>{k(t=>o(t,t=>t.id!==e)),V()},n[200]=V,n[201]=Hn);let Un;n[202]!==E||n[203]!==He?(Un={columnOverrides:E,onColumnOverridesChange:He},n[202]=E,n[203]=He,n[204]=Un):Un=n[204];let Wn;n[205]!==C||n[206]!==R.order||n[207]!==In||n[208]!==Ln||n[209]!==zn||n[210]!==Bn||n[211]!==Vn||n[212]!==Q||n[213]!==Hn||n[214]!==Un||n[215]!==q?(Wn=(0,D.jsx)(A.Suspense,{fallback:Pn,children:(0,D.jsx)(Ae,{order:Fn,loading:In,project:C,vfoldersFrgmt:q,rowSelection:Ln,pagination:zn,onChangeOrder:Bn,onLabelsChanged:Vn,onLabelClick:Q,onRemoveRow:Hn,tableSettings:Un})}),n[205]=C,n[206]=R.order,n[207]=In,n[208]=Ln,n[209]=zn,n[210]=Bn,n[211]=Vn,n[212]=Q,n[213]=Hn,n[214]=Un,n[215]=q,n[216]=Wn):Wn=n[216];let Gn;n[217]!==On||n[218]!==Nn||n[219]!==Wn?(Gn=(0,D.jsxs)(g,{align:`stretch`,gap:3,children:[On,Nn,Wn]}),n[217]=On,n[218]=Nn,n[219]=Wn,n[220]=Gn):Gn=n[220];let Kn;n[221]!==J||n[222]!==Z||n[223]!==$t||n[224]!==Gn?(Kn=(0,D.jsxs)(xe,{title:J,extra:Z,children:[$t,Gn]}),n[221]=J,n[222]=Z,n[223]=$t,n[224]=Gn,n[225]=Kn):Kn=n[225];let qn=R.mode===`model`?`model`:R.mode===`automount`?`automount`:`general`,Jn;n[226]===qn?Jn=n[227]:(Jn={usage_mode:qn},n[226]=qn,n[227]=Jn);let Yn;n[228]!==j||n[229]!==V?(Yn=e=>{e&&V(),j()},n[228]=j,n[229]=V,n[230]=Yn):Yn=n[230];let Xn;n[231]!==Xe||n[232]!==be||n[233]!==C||n[234]!==Jn||n[235]!==Yn?(Xn=(0,D.jsx)(Ne,{open:Xe,project:C,allowAutoMount:be,initialValues:Jn,onRequestClose:Yn}),n[231]=Xe,n[232]=be,n[233]=C,n[234]=Jn,n[235]=Yn,n[236]=Xn):Xn=n[236];let Zn;n[237]!==M||n[238]!==V?(Zn=(e,t)=>{e&&V(),t&&k(e=>o(e,e=>c(t,e.id))),M()},n[237]=M,n[238]=V,n[239]=Zn):Zn=n[239];let Qn;n[240]!==ct||n[241]!==O||n[242]!==Zn?(Qn=(0,D.jsx)(Le,{vfolderFrgmts:O,open:ct,onRequestClose:Zn}),n[240]=ct,n[241]=O,n[242]=Zn,n[243]=Qn):Qn=n[243];let $n;n[244]!==N||n[245]!==V?($n=e=>{e&&(V(),k([])),N()},n[244]=N,n[245]=V,n[246]=$n):$n=n[246];let er;n[247]!==ut||n[248]!==O||n[249]!==$n?(er=(0,D.jsx)(Re,{vfolderFrgmts:O,open:ut,onRequestClose:$n}),n[247]=ut,n[248]=O,n[249]=$n,n[250]=er):er=n[250];let $;n[251]!==P||n[252]!==V?($=e=>{e&&(V(),k([])),P()},n[251]=P,n[252]=V,n[253]=$):$=n[253];let tr;n[254]!==ft||n[255]!==O||n[256]!==$?(tr=(0,D.jsx)(Oe,{vfolderFrgmts:O,open:ft,onRequestClose:$}),n[254]=ft,n[255]=O,n[256]=$,n[257]=tr):tr=n[257];let nr;return n[258]!==a||n[259]!==tr||n[260]!==Kn||n[261]!==Xn||n[262]!==Qn||n[263]!==er?(nr=(0,D.jsxs)(g,{align:`stretch`,gap:5,...a,children:[Kn,Xn,Qn,er,tr]}),n[258]=a,n[259]=tr,n[260]=Kn,n[261]=Xn,n[262]=Qn,n[263]=er,n[264]=nr):nr=n[264],nr};function nt(e){return e}function rt(e){return(0,D.jsx)(C,{value:e.value,label:e.label},e.value)}function it(e){return{label:e,value:e}}function at(e){var t;return{entityId:e.entityId,name:((t=e.metadata)==null?void 0:t.name)??void 0}}function ot(e){return e.id}export{tt as default};
