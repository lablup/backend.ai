import{u as W,A as U,c0 as H,a1 as G,e as X,bt as J,cp as w,n,ba as Q,bj as Y,V as Z,aX as A,b9 as K,ay as x,D as ee,a_ as ne,aa as ae,H as le,v as B}from"./index-CwWAznqi.js";import{P as te}from"./ProjectSelectForAdminPage-CZSHPq9X.js";import{S as re}from"./StorageSelect-DHmmTxOm.js";import{r as N,i as oe}from"./icons-BgdBQS0N.js";import{D as se,F as b,m as ie}from"./lodash-RhKGq0BF.js";import{a as P,R as C}from"./index-D3rBwsRJ.js";import{B as de}from"./BAIQuestionIconWithTooltip-BVwNHmCw.js";import{a as ue}from"./Switch-D0ZtHaH2.js";const E=(function(){var m={defaultValue:null,kind:"LocalArgument",name:"input"},o={defaultValue:null,kind:"LocalArgument",name:"projectId"},g=[{kind:"Variable",name:"input",variableName:"input"},{kind:"Variable",name:"projectId",variableName:"projectId"}],p={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},F={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i={alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},y={alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},f={alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null}],storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[m,o],kind:"Fragment",metadata:null,name:"FolderCreateModalV2ProjectMutation",selections:[{alias:null,args:g,concreteType:"CreateVFolderV2Payload",kind:"LinkedField",name:"createVFolderInProject",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"vfolder",plural:!1,selections:[p,d,F,u,i,y,f,{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"BAINodeNotificationItemFragment"}],type:"Node",abstractKey:"__isNode"},kind:"AliasedInlineFragmentSpread",name:"notificationFrgmt"}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[o,m],kind:"Operation",name:"FolderCreateModalV2ProjectMutation",selections:[{alias:null,args:g,concreteType:"CreateVFolderV2Payload",kind:"LinkedField",name:"createVFolderInProject",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"vfolder",plural:!1,selections:[p,d,F,u,i,y,f,{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[l,c,e,k,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},p,k,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},c],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,p],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[l],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[l,c,k,e],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null}]},params:{cacheID:"c06716eb18ea34a92fe79e4494c7d8b0",id:null,metadata:{},name:"FolderCreateModalV2ProjectMutation",operationKind:"mutation",text:`mutation FolderCreateModalV2ProjectMutation(
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
`}}})();E.hash="84b555722712f02e520153bbc3dfa7de";const D=(function(){var m=[{defaultValue:null,kind:"LocalArgument",name:"input"}],o=[{kind:"Variable",name:"input",variableName:"input"}],g={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},d={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e={alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},i={alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},y={alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null}],storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:m,kind:"Fragment",metadata:null,name:"FolderCreateModalV2Mutation",selections:[{alias:null,args:o,concreteType:"CreateVFolderV2Payload",kind:"LinkedField",name:"createVfolderV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"vfolder",plural:!1,selections:[g,p,d,F,e,i,y,{fragment:{kind:"InlineFragment",selections:[{args:null,kind:"FragmentSpread",name:"BAINodeNotificationItemFragment"}],type:"Node",abstractKey:"__isNode"},kind:"AliasedInlineFragmentSpread",name:"notificationFrgmt"}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:m,kind:"Operation",name:"FolderCreateModalV2Mutation",selections:[{alias:null,args:o,concreteType:"CreateVFolderV2Payload",kind:"LinkedField",name:"createVfolderV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"vfolder",plural:!1,selections:[g,p,d,F,e,i,y,{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[f,l,u,c,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},g,c,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},l],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[u,g],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[f],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[f,l,c,u],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null}]},params:{cacheID:"1948e3e1ae75124978e1a4e435a49a31",id:null,metadata:{},name:"FolderCreateModalV2Mutation",operationKind:"mutation",text:`mutation FolderCreateModalV2Mutation(
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
`}}})();D.hash="0a18c7890a957cd2945b8f7f947bd96c";const ce="model-store",me=64,ge=650,he=({onRequestClose:m,project:o,initialValidate:g=!1,initialValues:p={},folderType:d,alertMessage:F,...u})=>{"use memo";const{t:e}=W(),{token:i}=U(),{logger:y}=H(),{getErrorMessage:f}=G(),l=N.useRef(null),c=X(),[k,j]=N.useState(null),S=o??k;N.useEffect(()=>{var a;(a=l.current)!=null&&a.getFieldValue("usage_mode")&&l.current.validateFields(["usage_mode"])},[k]);const{upsertNotification:v}=J(),R={name:"",host:void 0,group:o==null?void 0:o.id,usage_mode:"general",permission:"rw",cloneable:!1},h=d==="project"||d==="model_project",M=d==="model_project",O={...R,...p,...d==="model_project"?{usage_mode:"model",permission:"ro",cloneable:!0}:void 0,...o?{group:o.id}:{}},$=w(D),q=w(E),z=async()=>{var T;let a;try{a=await((T=l.current)==null?void 0:T.validateFields())}catch(r){y.error(r);return}if(!a)return;const t=a.usage_mode==="automount",s=t&&!b(a.name,".")?`.${a.name}`:a.name,V={name:s,host:a.host??null,cloneable:!!a.cloneable},L=t?"general":a.usage_mode;let I;try{h?I=await q({projectId:(S==null?void 0:S.id)??a.group??"",input:{...V,usageMode:L==="model"?"MODEL":"GENERAL",permission:a.permission==="ro"?"READ_ONLY":"READ_WRITE"}}).then(r=>{var _;return(_=r==null?void 0:r.createVFolderInProject)==null?void 0:_.vfolder}):I=await $({input:{...V,usageMode:L,permission:a.permission,projectId:null}}).then(r=>{var _;return(_=r==null?void 0:r.createVfolderV2)==null?void 0:_.vfolder})}catch(r){const _=Array.isArray(r)?ie(r,"message").join(`
`):r instanceof Error?f(r):void 0;v({key:`folder-create-failure-${s}-${Date.now()}`,type:"error",icon:"folder",message:`${e("general.Folder")}: ${s}`,description:e("data.folders.FolderCreationFailed"),extraDescription:_,open:!0}),y.error(r);return}v(I?{key:`folder-create-success-${I.entityId}`,icon:"folder",node:I.notificationFrgmt,description:e("data.folders.FolderCreated"),open:!0}:{key:`folder-create-success-${s}-${Date.now()}`,icon:"folder",message:`${e("general.Folder")}: ${s}`,description:e("data.folders.FolderCreated"),open:!0}),m(I)};return n.jsxs(Q,{isOpen:u.open,onOpenChange:a=>{a||m()},title:e("data.CreateANewStorageFolder"),maskClosable:!1,footer:n.jsxs(le,{justify:"end",gap:2,children:[n.jsx(B,{variant:"secondary",label:e("button.Cancel"),onClick:()=>{m()}}),n.jsx(B,{variant:"primary",label:e("data.Create"),clickAction:async()=>{await z()},"data-testid":"create-folder-button"})]}),width:ge,...u,afterOpenChange:a=>{var t;a&&(j(null),g&&((t=l.current)==null||t.validateFields()))},children:[F?n.jsx("div",{style:{marginBottom:i("--spacing-5")},children:n.jsx(Y,{role:"alert",status:"warning",title:F,container:"section"})}):null,n.jsx(Z,{align:"stretch",style:{paddingLeft:i("--spacing-5"),paddingRight:i("--spacing-5"),paddingTop:F?0:i("--spacing-5")},children:n.jsxs(A,{ref:l,initialValues:O,labelCol:{span:8},labelAlign:"left",children:[o===null&&n.jsxs(n.Fragment,{children:[n.jsx(K,{label:e("data.folders.TargetProject"),name:"group",layout:"horizontal",required:!0,rules:[{required:!0,message:e("data.folders.TargetProjectRequired")}],children:n.jsx(N.Suspense,{fallback:n.jsx(x,{loading:!0,disabled:!0}),children:n.jsx(te,{"data-testid":"folder-create-project-select",domain:c._config.domainName,onSelectProject:a=>{var t,s;j({id:a.projectId,name:a.projectName}),(t=l.current)==null||t.setFieldValue("group",a.projectId),(s=l.current)==null||s.validateFields(["group"])}})})}),n.jsx(ee,{style:{marginBottom:i("--spacing-6")}})]}),n.jsx(K,{label:e("data.Foldername"),name:"name",layout:"horizontal",required:!0,rules:[{pattern:/^[a-zA-Z0-9-_.]+$/,message:e("data.AllowsLettersNumbersAnd-_Dot")},{max:me,message:e("data.FolderNameTooLong")},({getFieldValue:a})=>({validator(t,s){return se(s)?Promise.reject(new Error(e("data.FolderNameRequired"))):a("usage_mode")==="automount"&&!b(s,".")?Promise.reject(new Error(e("data.AutomountFolderNameMustStartWithDot"))):a("usage_mode")!=="automount"&&b(s,".")?Promise.reject(new Error(e("data.DotPrefixReservedForAutomount"))):Promise.resolve()}})],children:n.jsx(ne,{"aria-label":e("data.Foldername"),placeholder:e("maxLength.64chars")})}),n.jsx(K,{label:e("data.UsageMode"),name:"usage_mode",layout:"horizontal",required:!0,rules:h?[{validator:(a,t)=>t==="model"&&(S==null?void 0:S.name)!==ce?Promise.reject(new Error(e("data.folders.CreateModelFolderOnlyInExclusiveProject"))):Promise.resolve()}]:void 0,children:n.jsxs(P,{"aria-label":e("data.UsageMode"),disabled:M,orientation:"horizontal",onChange:()=>{var a;(a=l.current)!=null&&a.getFieldValue("name")&&l.current.validateFields(["name"])},children:[n.jsx(C,{value:"general",label:e("data.General"),"data-testid":"general-usage-mode"}),(c._config.enableModelFolders||h)&&n.jsx(C,{value:"model",label:e("data.Models"),"data-testid":"model-usage-mode"}),!h&&n.jsx(C,{value:"automount",label:e("data.AutoMount"),"data-testid":"automount-usage-mode",endContent:n.jsx(de,{title:e("data.AutomountFolderCreationDesc")})})]})}),n.jsx(K,{label:e("data.folders.Location"),name:"host",layout:"horizontal",required:!0,children:n.jsx(N.Suspense,{fallback:n.jsx(x,{loading:!0,disabled:!0}),children:n.jsx(re,{onChange:a=>{var t;(t=l.current)==null||t.setFieldValue("host",a)},showUsageStatus:!0,autoSelectType:"usage",showSearch:!0})})}),o!==null&&n.jsx(A.Item,{hidden:!0,name:"group"}),n.jsx(A.Item,{dependencies:["usage_mode"],noStyle:!0,required:!0,children:({getFieldValue:a})=>{const t=a("usage_mode")==="model"&&h;return n.jsx(K,{label:e("data.folders.MountPermission"),name:"permission",layout:"horizontal",required:!0,dependencies:["usage_mode"],rules:[{validator:(s,V)=>t&&V==="rw"?Promise.reject(new Error(e("data.folders.ModelProjectFolderRestrictedToReadOnly"))):Promise.resolve()}],children:n.jsxs(P,{"aria-label":e("data.folders.MountPermission"),disabled:M,orientation:"horizontal",children:[n.jsx(C,{value:"rw",label:e("data.ReadWrite"),"data-testid":"rw-permission",isDisabled:t,endContent:!M&&t?n.jsx(ae,{content:e("data.folders.ModelProjectFolderRestrictedToReadOnly"),focusable:!1,icon:n.jsx(oe,{})}):void 0}),n.jsx(C,{value:"ro",label:e("data.ReadOnly"),"data-testid":"ro-permission"})]})})}}),n.jsx(A.Item,{dependencies:["usage_mode"],noStyle:!0,children:({getFieldValue:a})=>a("usage_mode")==="model"&&n.jsx(n.Fragment,{children:n.jsx(K,{label:e("data.folders.Cloneable"),name:"cloneable",layout:"horizontal",children:n.jsx(ue,{"aria-label":e("data.folders.Cloneable")})})})})]})})]})};export{he as F};
//# sourceMappingURL=FolderCreateModalV2-C_WEsabC.js.map
