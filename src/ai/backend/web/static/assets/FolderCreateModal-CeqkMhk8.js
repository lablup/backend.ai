import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{ot as r,ut as i,vt as a,x as o}from"./lodash-ClfL87UH.js";/* empty css            */import{t as s}from"./jsx-runtime-BapUIyWk.js";import{_ as c}from"./usePressFeedback-BIoIGSxE.js";import{s as l}from"./DefaultProviders-BFjPhnQa.js";import{t as u}from"./Button-BKkkrlg5.js";import{t as d}from"./VStack-DaUzGF31.js";import{r as f,u as p}from"./Skeleton-D35z7Ria.js";import{i as m,t as h}from"./Form-DK4EItCB.js";import"./form-engine-mhqCLVoE.js";import{t as ee}from"./Divider-ze3owNF7.js";import{H as te}from"./helper-BWFKT_2Y.js";import{a as g}from"./hooks-UUY7pxyu.js";import{t as _}from"./react-relay-BfoHYpUf.js";import{t as ne}from"./useBAILogger-CRaS0DnM.js";import{t as v}from"./BAISelect-D7nL9svF.js";import{t as re}from"./BAIQuestionIconWithTooltip-C0Z6oRPw.js";import{t as ie}from"./BAIText-CtDfjLnS.js";import{t as y}from"./BAIModal-XZIjYM23.js";import{t as b}from"./Banner-ElTQ2msG.js";import{t as x}from"./CheckboxInput-DinsfW7h.js";import{t as S}from"./StorageSelect-BO1z0Zv_.js";import{n as C,t as ae}from"./RadioList-lHcttiUQ.js";import{t as oe}from"./Switch-u5HK1VFM.js";import{t as se}from"./TextInput-B89-yA_Q.js";import"./BAIFormItem-xrBTQyTs.js";import{a as ce,n as le,s as ue}from"./useAppConfig-YxMPgnp9.js";import{t as de}from"./useAccessibleProjects-gzoxrvLz.js";import{r as w}from"./pathBuilder-BpKje1m9.js";import{mt as T}from"./index-49VU5B_r.js";import{t as fe}from"./ProjectSelectForAdminPage-K3CxsGR3.js";var E=n(),D=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`input`},t={defaultValue:null,kind:`LocalArgument`,name:`projectId`},n=[{kind:`Variable`,name:`input`,variableName:`input`},{kind:`Variable`,name:`projectId`,variableName:`projectId`}],r={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},i={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},a={alias:`vfolderStatus`,args:null,kind:`ScalarField`,name:`status`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`host`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},c={alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[s,{alias:null,args:null,kind:`ScalarField`,name:`usageMode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quotaScopeId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cloneable`,storageKey:null}],storageKey:null},l={alias:null,args:null,concreteType:`VFolderAccessControlInfo`,kind:`LinkedField`,name:`accessControl`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`permission`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`ownershipType`,storageKey:null}],storageKey:null},u={alias:null,args:null,concreteType:`VFolderOwnershipInfo`,kind:`LinkedField`,name:`ownership`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`userId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`projectId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`creatorEmail`,storageKey:null}],storageKey:null},d={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},p={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null};return{fragment:{argumentDefinitions:[e,t],kind:`Fragment`,metadata:null,name:`FolderCreateModalProjectMutation`,selections:[{alias:null,args:n,concreteType:`CreateVFolderV2Payload`,kind:`LinkedField`,name:`createVFolderInProject`,plural:!1,selections:[{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`vfolder`,plural:!1,selections:[r,i,a,o,c,l,u,{fragment:{kind:`InlineFragment`,selections:[{args:null,kind:`FragmentSpread`,name:`BAINodeNotificationItemFragment`}],type:`Node`,abstractKey:`__isNode`},kind:`AliasedInlineFragmentSpread`,name:`notificationFrgmt`}],storageKey:null}],storageKey:null}],type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[t,e],kind:`Operation`,name:`FolderCreateModalProjectMutation`,selections:[{alias:null,args:n,concreteType:`CreateVFolderV2Payload`,kind:`LinkedField`,name:`createVFolderInProject`,plural:!1,selections:[{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`vfolder`,plural:!1,selections:[r,i,a,o,c,l,u,{kind:`InlineFragment`,selections:[{kind:`InlineFragment`,selections:[d,f,s,p,{alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`user_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`scaling_group`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`project_id`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},r,p,{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},f],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`vfolder_mounts`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[s,r],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_size`,storageKey:null}],type:`ComputeSessionNode`,abstractKey:null},{kind:`InlineFragment`,selections:[d],type:`VFolder`,abstractKey:null},{kind:`InlineFragment`,selections:[d,f,p,s],type:`VirtualFolderNode`,abstractKey:null}],type:`Node`,abstractKey:`__isNode`}],storageKey:null}],storageKey:null}]},params:{cacheID:`7c55826b566b7f0947031349a552a024`,id:null,metadata:{},name:`FolderCreateModalProjectMutation`,operationKind:`mutation`,text:`mutation FolderCreateModalProjectMutation(
  $projectId: UUID!
  $input: CreateVFolderInScopeInput!
) {
  createVFolderInProject(projectId: $projectId, input: $input) {
    vfolder {
      id
      entityId
      vfolderStatus: status
      host
      metadata {
        name
        usageMode
        quotaScopeId
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
      }
      ...BAINodeNotificationItemFragment
    }
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

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();D.hash=`b957b5b5e9481ee28c655e04b441eb44`;var O=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{kind:`Variable`,name:`input`,variableName:`input`}],n={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},i={alias:`vfolderStatus`,args:null,kind:`ScalarField`,name:`status`,storageKey:null},a={alias:null,args:null,kind:`ScalarField`,name:`host`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},s={alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[o,{alias:null,args:null,kind:`ScalarField`,name:`usageMode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`quotaScopeId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cloneable`,storageKey:null}],storageKey:null},c={alias:null,args:null,concreteType:`VFolderAccessControlInfo`,kind:`LinkedField`,name:`accessControl`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`permission`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`ownershipType`,storageKey:null}],storageKey:null},l={alias:null,args:null,concreteType:`VFolderOwnershipInfo`,kind:`LinkedField`,name:`ownership`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`userId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`projectId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`creatorEmail`,storageKey:null}],storageKey:null},u={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},d={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`FolderCreateModalPersonalMutation`,selections:[{alias:null,args:t,concreteType:`CreateVFolderV2Payload`,kind:`LinkedField`,name:`createVfolderV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`vfolder`,plural:!1,selections:[n,r,i,a,s,c,l,{fragment:{kind:`InlineFragment`,selections:[{args:null,kind:`FragmentSpread`,name:`BAINodeNotificationItemFragment`}],type:`Node`,abstractKey:`__isNode`},kind:`AliasedInlineFragmentSpread`,name:`notificationFrgmt`}],storageKey:null}],storageKey:null}],type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`FolderCreateModalPersonalMutation`,selections:[{alias:null,args:t,concreteType:`CreateVFolderV2Payload`,kind:`LinkedField`,name:`createVfolderV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`VFolder`,kind:`LinkedField`,name:`vfolder`,plural:!1,selections:[n,r,i,a,s,c,l,{kind:`InlineFragment`,selections:[{kind:`InlineFragment`,selections:[u,d,o,f,{alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`user_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`scaling_group`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`project_id`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},n,f,{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},d],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`vfolder_mounts`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[o,n],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_size`,storageKey:null}],type:`ComputeSessionNode`,abstractKey:null},{kind:`InlineFragment`,selections:[u],type:`VFolder`,abstractKey:null},{kind:`InlineFragment`,selections:[u,d,f,o],type:`VirtualFolderNode`,abstractKey:null}],type:`Node`,abstractKey:`__isNode`}],storageKey:null}],storageKey:null}]},params:{cacheID:`b79fb3fba853da3baaab3123e45cc6c0`,id:null,metadata:{},name:`FolderCreateModalPersonalMutation`,operationKind:`mutation`,text:`mutation FolderCreateModalPersonalMutation(
  $input: CreateVFolderV2Input!
) {
  createVfolderV2(input: $input) {
    vfolder {
      id
      entityId
      vfolderStatus: status
      host
      metadata {
        name
        usageMode
        quotaScopeId
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
      }
      ...BAINodeNotificationItemFragment
    }
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

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();O.hash=`f72be6f8be9c5ce9c4d9a4bd6ed4fa85`;var k=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`projectId`}],t=[{alias:null,args:[{fields:[{fields:[{kind:`Literal`,name:`entityType`,value:`vfolder`},{kind:`Variable`,name:`scopeId`,variableName:`projectId`},{kind:`Literal`,name:`scopeType`,value:`project`}],kind:`ObjectValue`,name:`target`}],kind:`ObjectValue`,name:`input`}],concreteType:`MyScopePermissionsPayload`,kind:`LinkedField`,name:`myScopePermissions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ScopeEntityPermission`,kind:`LinkedField`,name:`item`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`permissions`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`FolderCreateModalPermissionQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`FolderCreateModalPermissionQuery`,selections:t},params:{cacheID:`7eb68cf6f19d5a704d5c3384481aeb3e`,id:null,metadata:{},name:`FolderCreateModalPermissionQuery`,operationKind:`query`,text:`query FolderCreateModalPermissionQuery(
  $projectId: UUID!
) {
  myScopePermissions(input: {target: {scopeType: "project", scopeId: $projectId, entityType: "vfolder"}}) {
    item {
      permissions
    }
  }
}
`}}})();k.hash=`8067e8be7c6d01e0f19603af09d11b76`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var A=e(t(),1),j=_(),M=s(),N=`skip_project_folder_confirm`,pe=64,me=650,P=({onRequestClose:e,project:t,initialValidate:n=!1,initialValues:i={},folderType:s,allowAutoMount:_=!1,alertMessage:E,...k})=>{"use memo";let{t:j}=f(),{token:P}=c(),{logger:I}=ne(),{getErrorMessage:L}=T(),R=(0,A.useRef)(null),z=te(),[he,B]=(0,A.useState)(null),V=t??he,{personalProject:H}=de(),U=!!V&&V.id!==(H==null?void 0:H.id)&&s!==`model_project`,W=U&&!(z!=null&&z.is_superadmin),[G,ge]=(0,A.useState)(null),K=U?W?(G==null?void 0:G.projectId)===(V==null?void 0:V.id)?G==null?void 0:G.canCreate:void 0:!0:void 0,_e=!!le(N),ve=ue(),ye=ce(),[be,q]=(0,A.useState)(!1),[J,Y]=(0,A.useState)(!1),[xe,X]=(0,A.useState)(!1),[Se,Z]=(0,A.useState)(!1),{upsertNotification:Q}=l(),Ce={name:``,host:void 0,group:t==null?void 0:t.id,usage_mode:`general`,cloneable:!1},we=s===`model_project`,Te=s===`model_project`?{usage_mode:`model`,cloneable:!0}:void 0,Ee={...Ce,...i,...Te,...!_&&i.usage_mode===`automount`?{usage_mode:`general`}:{},...t?{group:t.id}:{}},De=g(D),Oe=g(O),$=async()=>{let t;try{var n;t=await((n=R.current)==null?void 0:n.validateFields())}catch(e){I.error(e);return}if(!t)return;let r=t.usage_mode===`automount`,i=r&&!o(t.name,`.`)?`.${t.name}`:t.name,s;try{s=r&&_?await Oe({input:{name:i,host:t.host??null,cloneable:!!t.cloneable,usageMode:`general`,permission:`ro`,projectId:null}}).then(e=>{var t;return e==null||(t=e.createVfolderV2)==null?void 0:t.vfolder}):await De({projectId:(V==null?void 0:V.id)??t.group??``,input:{name:i,host:t.host??null,cloneable:!!t.cloneable,usageMode:t.usage_mode===`model`?`MODEL`:`GENERAL`,permission:`READ_ONLY`}}).then(e=>{var t;return e==null||(t=e.createVFolderInProject)==null?void 0:t.vfolder})}catch(e){let t=Array.isArray(e)?a(e,`message`).join(`
`):e instanceof Error?L(e):void 0;Q({key:`folder-create-failure-${i}-${Date.now()}`,type:`error`,icon:`folder`,message:`${j(`general.Folder`)}: ${i}`,description:j(`data.folders.FolderCreationFailed`),extraDescription:t,open:!0}),I.error(e);return}Q(s?{key:`folder-create-success-${s.entityId}`,icon:`folder`,node:s.notificationFrgmt,description:j(`data.folders.FolderCreated`),open:!0}:{key:`folder-create-success-${i}-${Date.now()}`,icon:`folder`,message:`${j(`general.Folder`)}: ${i}`,description:j(`data.folders.FolderCreated`),open:!0}),e(s)};return(0,M.jsxs)(M.Fragment,{children:[(0,M.jsxs)(y,{isOpen:k.open,onOpenChange:t=>{t||e()},title:j(`data.CreateANewStorageFolder`),maskClosable:!1,unmountOnClose:!0,footer:(0,M.jsxs)(p,{justify:`end`,gap:2,children:[(0,M.jsx)(u,{variant:`secondary`,label:j(`button.Cancel`),onClick:()=>{e()}}),(0,M.jsx)(u,{variant:`primary`,label:j(`data.Create`),isDisabled:K===!1,isLoading:Se,clickAction:async()=>{if(K&&!_e){var e;await((e=R.current)==null?void 0:e.validateFields().then(()=>!0).catch(()=>!1))&&q(!0)}else await $()},"data-testid":`create-folder-button`})]}),width:me,...k,afterOpenChange:e=>{if(e&&(B(null),n)){var t;(t=R.current)==null||t.validateFields()}},children:[W&&V?(0,M.jsx)(A.Suspense,{fallback:null,children:(0,M.jsx)(F,{projectId:V.id,onResolved:e=>ge({projectId:V.id,canCreate:e})})}):null,K===void 0?null:(0,M.jsx)(`div`,{style:{marginBottom:P(`--spacing-5`)},children:(0,M.jsx)(b,{role:`status`,status:K?`info`:`warning`,title:j(K?`data.folders.SharedProjectFolderVisibleToMembers`:`data.folders.NoPermissionToCreateFolderInProject`),container:`section`,endContent:H!=null&&H.name?(0,M.jsx)(u,{variant:`secondary`,size:`sm`,label:j(`data.folders.FolderCreationOpenPersonalProject`),onClick:()=>{window.open(w(`project`,`data`,H.name),`_blank`,`noopener,noreferrer`)}}):void 0})}),E?(0,M.jsx)(`div`,{style:{marginBottom:P(`--spacing-5`)},children:(0,M.jsx)(b,{role:`alert`,status:`warning`,title:E,container:`section`})}):null,(0,M.jsx)(d,{align:`stretch`,style:{paddingLeft:P(`--spacing-5`),paddingRight:P(`--spacing-5`),paddingTop:E?0:P(`--spacing-5`)},children:(0,M.jsxs)(h,{ref:R,initialValues:Ee,labelCol:{span:8},labelAlign:`left`,children:[t===null&&(0,M.jsxs)(M.Fragment,{children:[(0,M.jsx)(m,{label:j(`data.folders.TargetProject`),name:`group`,layout:`horizontal`,required:!0,rules:[{required:!0,message:j(`data.folders.TargetProjectRequired`)}],children:(0,M.jsx)(A.Suspense,{fallback:(0,M.jsx)(v,{loading:!0,disabled:!0}),children:(0,M.jsx)(fe,{"data-testid":`folder-create-project-select`,domain:z._config.domainName,onSelectProject:e=>{var t,n;B({id:e.projectId,name:e.projectName}),(t=R.current)==null||t.setFieldValue(`group`,e.projectId),(n=R.current)==null||n.validateFields([`group`])}})})}),(0,M.jsx)(ee,{style:{marginBottom:P(`--spacing-6`)}})]}),(0,M.jsx)(m,{label:j(`data.Foldername`),name:`name`,layout:`horizontal`,required:!0,rules:[{pattern:/^[a-zA-Z0-9-_.]+$/,message:j(`data.AllowsLettersNumbersAnd-_Dot`)},{max:pe,message:j(`data.FolderNameTooLong`)},({getFieldValue:e})=>({validator(t,n){return r(n)?Promise.reject(Error(j(`data.FolderNameRequired`))):e(`usage_mode`)===`automount`&&!o(n,`.`)?Promise.reject(Error(j(`data.AutomountFolderNameMustStartWithDot`))):e(`usage_mode`)!==`automount`&&o(n,`.`)?Promise.reject(Error(j(`data.DotPrefixReservedForAutomount`))):Promise.resolve()}})],children:(0,M.jsx)(se,{"aria-label":j(`data.Foldername`),placeholder:j(`maxLength.64chars`)})}),(0,M.jsx)(m,{label:j(`data.UsageMode`),name:`usage_mode`,layout:`horizontal`,required:!0,children:(0,M.jsxs)(ae,{"aria-label":j(`data.UsageMode`),disabled:we,orientation:`horizontal`,onChange:()=>{var e;(e=R.current)!=null&&e.getFieldValue(`name`)&&R.current.validateFields([`name`])},children:[(0,M.jsx)(C,{value:`general`,label:j(`data.General`),"data-testid":`general-usage-mode`}),(0,M.jsx)(C,{value:`model`,label:j(`data.Models`),"data-testid":`model-usage-mode`}),_&&(0,M.jsx)(C,{value:`automount`,label:j(`data.AutoMount`),"data-testid":`automount-usage-mode`,endContent:(0,M.jsx)(re,{title:j(`data.AutomountFolderCreationDesc`)})})]})}),(0,M.jsx)(m,{label:j(`data.folders.Location`),name:`host`,layout:`horizontal`,required:!0,children:(0,M.jsx)(A.Suspense,{fallback:(0,M.jsx)(v,{loading:!0,disabled:!0}),children:(0,M.jsx)(S,{onChange:e=>{var t;(t=R.current)==null||t.setFieldValue(`host`,e)},showUsageStatus:!0,autoSelectType:`usage`,showSearch:!0})})}),t!==null&&(0,M.jsx)(h.Item,{hidden:!0,name:`group`}),(0,M.jsx)(h.Item,{dependencies:[`usage_mode`],noStyle:!0,children:({getFieldValue:e})=>e(`usage_mode`)===`model`&&(0,M.jsx)(M.Fragment,{children:(0,M.jsx)(m,{label:j(`data.folders.Cloneable`),name:`cloneable`,layout:`horizontal`,children:(0,M.jsx)(oe,{"aria-label":j(`data.folders.Cloneable`)})})})})]})})]}),(0,M.jsx)(y,{open:be,title:j(`data.CreateANewStorageFolder`),okText:j(`data.Create`),confirmLoading:xe,unmountOnClose:!0,onCancel:()=>{q(!1),Y(!1)},onOk:async()=>{X(!0);try{J&&await ve(N,!0).then(()=>ye()).catch(e=>I.error(e))}finally{X(!1)}q(!1),Z(!0);try{await $()}finally{Z(!1)}},"data-testid":`shared-folder-confirm-modal`,children:(0,M.jsxs)(d,{align:`stretch`,gap:3,children:[(0,M.jsx)(ie,{children:j(`data.folders.ConfirmCreateFolderVisibleToMembers`)}),(0,M.jsx)(x,{value:J,onChange:e=>Y(!!e),children:j(`data.folders.DontAskAgain`)})]})})]})},F=e=>{"use memo";let t=(0,E.c)(13),{projectId:n,onResolved:r}=e,a;t[0]===n?a=t[1]:(a={projectId:n},t[0]=n,t[1]=a);let o;t[2]===Symbol.for(`react.memo_cache_sentinel`)?(o={fetchPolicy:`store-and-network`},t[2]=o):o=t[2];let{myScopePermissions:s}=(0,j.useLazyLoadQuery)(k,a,o),c;t[3]===(s==null?void 0:s.item.permissions)?c=t[4]:(c=i(s==null?void 0:s.item.permissions,`CREATE`),t[3]=s==null?void 0:s.item.permissions,t[4]=c);let l=c,u;t[5]!==l||t[6]!==r?(u=()=>r(l),t[5]=l,t[6]=r,t[7]=u):u=t[7];let d=(0,A.useEffectEvent)(u),f;t[8]===d?f=t[9]:(f=()=>{d()},t[8]=d,t[9]=f);let p;return t[10]!==l||t[11]!==n?(p=[n,l],t[10]=l,t[11]=n,t[12]=p):p=t[12],(0,A.useEffect)(f,p),null};export{P as t};
