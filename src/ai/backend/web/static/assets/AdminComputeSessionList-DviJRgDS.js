import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{V as t,Zn as n,g as r,yt as i}from"./icons-Btg1s2wy.js";import{t as a}from"./compiler-runtime-CZQb2eIb.js";import{Dt as o,Lt as s,V as c,et as l,nt as u,ot as ee,qt as d,vt as f}from"./lodash-ClfL87UH.js";/* empty css            */import{t as p}from"./jsx-runtime-BapUIyWk.js";import{t as m}from"./Tooltip-QQJy2agO.js";import{O as te,f as ne}from"./DefaultProviders-BFjPhnQa.js";import{t as re}from"./IconButton-DGkWhkpU.js";import{r as ie}from"./Skeleton-D35z7Ria.js";import{t as h}from"./BAIFlex-BElkJeHW.js";import{t as ae}from"./BAITabCountBadge-CbZcLm1Q.js";import{t as oe}from"./app-shim-DTEBzR8d.js";import{G as se,rt as ce,y as le}from"./helper-BWFKT_2Y.js";import{r as ue}from"./hooks-UUY7pxyu.js";import{t as g}from"./react-relay-BfoHYpUf.js";import{t as de}from"./useBAILogger-CRaS0DnM.js";import{l as fe,u as pe}from"./helper-DF1Eunoe.js";import{n as me,t as he}from"./BAIPropertyFilter-Bp3-ZYGr.js";import{t as ge}from"./Banner-ElTQ2msG.js";import{t as _e}from"./BAISelectionLabel-BTMbVxpE.js";import{t as ve}from"./TerminateSessionModal-Dc4-a-eq.js";import{t as ye}from"./SessionResourceGrid-NpN_xa97.js";import{t as be}from"./BAIResourceUnitGridSkeleton-CtTggOjx.js";import{n as xe,t as Se}from"./BAISegmentedControlItem-erYb9KqU.js";import{t as Ce}from"./BAIAdminProjectSelect-C4ysrhzW.js";import{i as we,o as Te,r as Ee}from"./dist-C3M-rFln.js";import{t as De}from"./AutoUpdateFetchKeyButton-C-RHyKup.js";import{t as Oe}from"./BAITabs-Bwz-IwE5.js";import{n as ke}from"./reactPaginationQueryOptions-DUCwh22X.js";import{n as Ae,t as je}from"./SessionNodes-DSXFqOUS.js";import{t as Me}from"./useCSVExport-1G9JGm2Z.js";import{t as Ne}from"./WebMCPSessionListTools-7clhwggn.js";var Pe=a(),Fe=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`filter`},t={defaultValue:null,kind:`LocalArgument`,name:`filterForAllCount`},n={defaultValue:null,kind:`LocalArgument`,name:`filterForBatchCount`},r={defaultValue:null,kind:`LocalArgument`,name:`filterForInferenceCount`},i={defaultValue:null,kind:`LocalArgument`,name:`filterForInteractiveCount`},a={defaultValue:null,kind:`LocalArgument`,name:`filterForSystemCount`},o={defaultValue:20,kind:`LocalArgument`,name:`first`},s={defaultValue:0,kind:`LocalArgument`,name:`offset`},c={defaultValue:null,kind:`LocalArgument`,name:`order`},l=[{kind:`Variable`,name:`filter`,variableName:`filter`},{kind:`Variable`,name:`first`,variableName:`first`},{kind:`Variable`,name:`offset`,variableName:`offset`},{kind:`Variable`,name:`order`,variableName:`order`}],u={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},ee={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},d={alias:null,args:null,kind:`ScalarField`,name:`count`,storageKey:null},f={kind:`Literal`,name:`first`,value:0},p={kind:`Literal`,name:`offset`,value:0},m=[d],te={alias:`all`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForAllCount`},f,p],concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:m,storageKey:null},ne={alias:`interactive`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForInteractiveCount`},f,p],concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:m,storageKey:null},re={alias:`inference`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForInferenceCount`},f,p],concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:m,storageKey:null},ie={alias:`batch`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForBatchCount`},f,p],concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:m,storageKey:null},h={alias:`system`,args:[{kind:`Variable`,name:`filter`,variableName:`filterForSystemCount`},f,p],concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:m,storageKey:null},ae={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null},oe={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},se={alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},ce=[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null}],le={alias:null,args:null,kind:`ScalarField`,name:`tag`,storageKey:null},ue=[{alias:null,args:null,concreteType:`ComputeSessionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[u,ae,ee,oe],storageKey:null}],storageKey:null},d];return{fragment:{argumentDefinitions:[e,t,n,r,i,a,o,s,c],kind:`Fragment`,metadata:null,name:`AdminComputeSessionListQuery`,selections:[{kind:`CatchField`,field:{alias:`computeSessionNodeResult`,args:l,concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:[{kind:`RequiredField`,field:{alias:null,args:null,concreteType:`ComputeSessionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{kind:`RequiredField`,field:{alias:null,args:null,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{kind:`RequiredField`,field:u,action:`THROW`},{kind:`RequiredField`,field:ee,action:`THROW`},{args:null,kind:`FragmentSpread`,name:`SessionNodesFragment`},{args:null,kind:`FragmentSpread`,name:`TerminateSessionModalFragment`},{args:null,kind:`FragmentSpread`,name:`WebMCPSessionListToolsFragment`}],storageKey:null},action:`THROW`}],storageKey:null},action:`THROW`},d],storageKey:null},to:`RESULT`},te,ne,re,ie,h],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[o,s,e,c,t,i,r,n,a],kind:`Operation`,name:`AdminComputeSessionListQuery`,selections:[{alias:`computeSessionNodeResult`,args:l,concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`compute_session_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`ComputeSessionEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[u,ee,ae,oe,{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`user_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`agent_ids`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`priority`,storageKey:null},se,{alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_size`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[u,oe,{alias:null,args:null,kind:`ScalarField`,name:`live_stat`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,concreteType:`ImageNode`,kind:`LinkedField`,name:`image`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`base_image_name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null},{alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`tags`,plural:!0,selections:ce,storageKey:null},{alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`labels`,plural:!0,selections:ce,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`registry`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`namespace`,storageKey:null},le,u],storageKey:null},ae,{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},se,{alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`created_at`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`starts_at`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`terminated_at`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`occupied_slots`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`requested_slots`,storageKey:null},le,{alias:null,args:null,kind:`ScalarField`,name:`idle_checks`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`project_id`,storageKey:null},{alias:null,args:null,concreteType:`UserNode`,kind:`LinkedField`,name:`owner`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null},u],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`resource_opts`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`vfolder_mounts`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[ae,ee,u],storageKey:null}],storageKey:null},d],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`scaling_group`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`startup_command`,storageKey:null},{alias:null,args:null,concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`dependees`,plural:!1,selections:ue,storageKey:null},{alias:null,args:null,concreteType:`ComputeSessionConnection`,kind:`LinkedField`,name:`dependents`,plural:!1,selections:ue,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_mode`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`result`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`domain_name`,storageKey:null}],storageKey:null}],storageKey:null},d],storageKey:null},te,ne,re,ie,h]},params:{cacheID:`0a29b137a83496673f20303cb5af2de9`,id:null,metadata:{},name:`AdminComputeSessionListQuery`,operationKind:`query`,text:`query AdminComputeSessionListQuery(
  $first: Int = 20
  $offset: Int = 0
  $filter: String
  $order: String
  $filterForAllCount: String
  $filterForInteractiveCount: String
  $filterForInferenceCount: String
  $filterForBatchCount: String
  $filterForSystemCount: String
) {
  computeSessionNodeResult: compute_session_nodes(first: $first, offset: $offset, filter: $filter, order: $order) {
    edges {
      node {
        id
        name
        ...SessionNodesFragment
        ...TerminateSessionModalFragment
        ...WebMCPSessionListToolsFragment
      }
    }
    count
  }
  all: compute_session_nodes(first: 0, offset: 0, filter: $filterForAllCount) {
    count
  }
  interactive: compute_session_nodes(first: 0, offset: 0, filter: $filterForInteractiveCount) {
    count
  }
  inference: compute_session_nodes(first: 0, offset: 0, filter: $filterForInferenceCount) {
    count
  }
  batch: compute_session_nodes(first: 0, offset: 0, filter: $filterForBatchCount) {
    count
  }
  system: compute_session_nodes(first: 0, offset: 0, filter: $filterForSystemCount) {
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

fragment BAIImageNodeSimpleTagFragment on ImageNode {
  base_image_name
  version
  architecture
  tags {
    key
    value
  }
  labels {
    key
    value
  }
  registry
  namespace
  tag
}

fragment BAISessionAgentIdsFragment on ComputeSessionNode {
  agent_ids
}

fragment BAISessionClusterModeFragment on ComputeSessionNode {
  cluster_mode
  cluster_size
}

fragment BAISessionTypeTokenFragment on ComputeSessionNode {
  type
}

fragment ConnectedKernelListFragment on KernelNode {
  id
  row_id
  cluster_hostname
  cluster_idx
  cluster_role
  status
  status_info
  agent_id
  container_id
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

fragment EditSessionPriorityModalFragment on ComputeSessionNode {
  id
  name
  priority
}

fragment EditableSessionNameFragment on ComputeSessionNode {
  id
  row_id
  name
  priority
  user_id
  status
  project_id
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment MountedVFolderLinksFragment on ComputeSessionNode {
  vfolder_nodes {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
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

fragment SessionAccessKeyFragment on ComputeSessionNode {
  access_key
  user_id
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

fragment SessionDetailContentFragment on ComputeSessionNode {
  id
  row_id
  name
  project_id
  user_id
  owner {
    email
    id
  }
  resource_opts
  status
  vfolder_mounts
  vfolder_nodes {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
      }
    }
    count
  }
  created_at
  terminated_at
  scaling_group
  agent_ids
  requested_slots
  occupied_slots
  tag
  idle_checks
  type
  startup_command
  kernel_nodes {
    edges {
      node {
        image {
          ...BAIImageNodeSimpleTagFragment
          id
        }
        ...ConnectedKernelListFragment
        id
      }
    }
  }
  dependees {
    edges {
      node {
        id
        row_id
        name
        status
      }
    }
    count
  }
  dependents {
    edges {
      node {
        id
        row_id
        name
        status
      }
    }
    count
  }
  ...SessionStatusBadgeFragment
  ...SessionActionButtonsFragment
  ...BAISessionTypeTokenFragment
  ...EditableSessionNameFragment
  ...SessionReservationFragment
  ...ContainerLogModalFragment
  ...SessionUsageMonitorFragment
  ...ContainerCommitModalFragment
  ...SessionIdleChecksNodeFragment
  ...AppLauncherModalFragment
  ...MountedVFolderLinksFragment
  ...BAISessionAgentIdsFragment
  ...BAISessionClusterModeFragment
  ...SessionAccessKeyFragment
}

fragment SessionDetailDrawerFragment on ComputeSessionNode {
  id
  project_id
  ...SessionDetailContentFragment
}

fragment SessionIdleChecksNodeFragment on ComputeSessionNode {
  id
  idle_checks
  ...SessionReclamationStatusCellFragment
}

fragment SessionNodesFragment on ComputeSessionNode {
  id
  row_id
  name
  status
  type
  service_ports
  user_id
  agent_ids
  priority
  ...SessionStatusBadgeFragment
  ...SessionReservationFragment
  ...SessionSlotCellFragment
  ...SessionReclamationStatusCellFragment
  ...SessionUsageMonitorFragment
  ...SessionDetailDrawerFragment
  ...BAISessionAgentIdsFragment
  ...BAISessionTypeTokenFragment
  ...BAISessionClusterModeFragment
  ...AppLauncherModalFragment
  ...TerminateSessionModalFragment
  ...EditSessionPriorityModalFragment
  ...SessionAccessKeyFragment
  kernel_nodes {
    edges {
      node {
        image {
          ...BAIImageNodeSimpleTagFragment
          id
        }
        id
      }
    }
  }
  created_at
  terminated_at
  status_info
  result
  domain_name
  scaling_group
  project_id
  owner {
    email
    id
  }
  dependees {
    edges {
      node {
        row_id
        name
        id
      }
    }
    count
  }
  dependents {
    edges {
      node {
        row_id
        name
        id
      }
    }
    count
  }
}

fragment SessionReclamationStatusCellFragment on ComputeSessionNode {
  id
  idle_checks
  ...SessionReclamationStatusPopoverFragment
}

fragment SessionReclamationStatusPopoverFragment on ComputeSessionNode {
  id
  idle_checks
}

fragment SessionReservationFragment on ComputeSessionNode {
  id
  created_at
  starts_at
  terminated_at
}

fragment SessionSlotCellFragment on ComputeSessionNode {
  id
  status
  occupied_slots
  requested_slots
  tag
  ...useSessionNodeLiveStatSessionFragment
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

fragment SessionUsageMonitorFragment on ComputeSessionNode {
  occupied_slots
  ...useSessionNodeLiveStatSessionFragment
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

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}

fragment WebMCPSessionListToolsFragment on ComputeSessionNode {
  row_id
  name
  status
  status_info
  result
  type
  scaling_group
  created_at
  terminated_at
  domain_name
  project_id
  agent_ids
  owner {
    email
    id
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

fragment useSessionNodeLiveStatSessionFragment on ComputeSessionNode {
  id
  kernel_nodes {
    edges {
      node {
        live_stat
        cluster_role
        id
      }
    }
  }
}
`}}})();Fe.hash=`13eef5f38421397678d5227ad5f9df3d`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Lifts a project condition out of the admin session filter for the grid's
legacy `compute_session_list` query, which has no `project_id` queryfilter
field but does take a `group_id` argument (FR-3571).
*/
var _=e=>{let t=[],n=0,r=!1,i=``;for(let a of e)a===`"`?r=!r:!r&&a===`(`?n+=1:!r&&a===`)`&&--n,a===`&`&&n===0&&!r?(t.push(i),i=``):i+=a;return t.push(i),t.map(e=>e.trim()).filter(Boolean)},v=e=>{let t=0,n=!1;for(let r of e)if(r===`"`)n=!n;else if(!n&&r===`(`)t+=1;else if(!n&&r===`)`)--t;else if(r===`|`&&t===0&&!n)return!0;return!1},y=/^\(*\s*project_id\s*(?:==|ilike)\s*"%?([^"%]+)%?"\s*\)*$/,Ie=e=>{var t;let n={projectId:void 0,remainder:e||void 0};if(!e||v(e))return n;let r=_(e),i=r.filter(e=>y.test(e));if(i.length!==1)return n;let a=r.filter(e=>!y.test(e));return{projectId:(t=y.exec(i[0]))==null?void 0:t[1],remainder:a.join(`&`)||void 0}},Le={name:`name`,domain_name:`domain_name`,access_key:`access_key`},Re=/^\(*\s*([a-z_]+)\s*(==|!=|>=|<=|ilike|like)\s*(?:"([^"]*)"|([^\s")]+))\s*\)*$/,b=(e,t)=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Translates the admin session list's queryfilter minilang string into the
`POST /export/sessions/csv` filter body, so the CSV narrows to the table's
own conditions wherever the export endpoint can express them (FR-3915).
Whatever it cannot express is dropped, leaving the CSV a superset — see
`buildSessionExportFilter` for the conditions that keeps.
*/
switch(e){case`==`:return{equals:t};case`!=`:return{not_equals:t};case`ilike`:case`like`:return/^%[^%]*%$/.test(t)?{i_contains:t.slice(1,-1)}:void 0;default:return}},ze=e=>{let t={};return!e||v(e)||o(_(e),e=>{let n=Re.exec(e);if(!n)return;let[,r,i,a,o]=n,s=a??o;if(l(s)||s===``)return;let c=Le[r];if(c){let e=b(i,s);e&&(t[c]=e)}else if(r===`scaling_group`){let e=b(i,s);e&&(t.scaling_group_name=e)}else if(r===`user_email`){let e=b(i,s);e&&(t.user={email:e})}else if(r===`created_at`||r===`terminated_at`){let e=i===`>=`?`after`:i===`<=`?`before`:void 0;if(!e)return;t[r]={...t[r],[e]:s}}}),t},x=e(n(),1),Be=g(),S=p(),Ve=[`all`,`interactive`,`batch`,`inference`,`system`],C=`status != "TERMINATED" & status != "CANCELLED"`,He=[`UNDEFINED`,`SUCCESS`,`FAILURE`],Ue={all:C,interactive:`${C} & type == "interactive"`,inference:`${C} & type == "inference"`,batch:`${C} & type == "batch"`,system:`${C} & type == "system"`},We=()=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let e=(0,Pe.c)(149),n=ne(),{t:a}=ie(),{message:o}=oe.useApp(),{logger:l}=de(),p=se(),g=ce(),_;e[0]===Symbol.for(`react.memo_cache_sentinel`)?(_=[],e[0]=_):_=e[0];let[v,y]=(0,x.useState)(_),[Le,Re]=(0,x.useState)(!1),[b,We]=te(`table_column_overrides.AdminComputeSessionListPage`),[w]=te(`experimental_session_resource_grid`),{supportedFields:Ye,exportCSV:Xe}=Me(`sessions`),Ze;e[1]===Symbol.for(`react.memo_cache_sentinel`)?(Ze={current:1,pageSize:10},e[1]=Ze):Ze=e[1];let{baiPaginationOption:T,tablePaginationOption:E,setTablePaginationOption:D}=ke(Ze),Qe,$e;e[2]===Symbol.for(`react.memo_cache_sentinel`)?(Qe={order:we(Ae),filter:Ee.withDefault(``),type:we(Ve).withDefault(`all`),statusCategory:we([`running`,`finished`]).withDefault(`running`),view:we([`table`,`grid`]).withDefault(`table`)},$e={history:`replace`},e[2]=Qe,e[3]=$e):(Qe=e[2],$e=e[3]);let[O,k]=Te(Qe,$e),et=O.type,A;e[4]===O?A=e[5]:(A=c(O,[`view`]),e[4]=O,e[5]=A);let j;e[6]!==A||e[7]!==E?(j={queryParams:A,tablePaginationOption:E},e[6]=A,e[7]=E,e[8]=j):j=e[8];let tt;e[9]!==O.type||e[10]!==j?(tt={[et]:j},e[9]=O.type,e[10]=j,e[11]=tt):tt=e[11];let nt=(0,x.useRef)(tt),rt,it;e[12]!==O||e[13]!==E?(rt=()=>{nt.current[O.type]={queryParams:c(O,[`view`]),tablePaginationOption:E}},it=[O,E],e[12]=O,e[13]=E,e[14]=rt,e[15]=it):(rt=e[14],it=e[15]),(0,x.useEffect)(rt,it);let at=O.type===`all`||O.type===void 0?void 0:`type == "${O.type}"`,M=O.statusCategory===`running`||O.statusCategory===void 0?C:`status == "TERMINATED" | status == "CANCELLED"`,ot=Ge,[st,ct]=ue(),lt=T.offset,ut=T.first,N;e[16]!==O.filter||e[17]!==M||e[18]!==at?(N=me([M,O.filter,at]),e[16]=O.filter,e[17]=M,e[18]=at,e[19]=N):N=e[19];let dt=O.order||`-created_at`,ft;e[20]!==T.first||e[21]!==T.offset||e[22]!==N||e[23]!==dt?(ft={offset:lt,first:ut,filter:N,order:dt,filterForAllCount:Ue.all,filterForInteractiveCount:Ue.interactive,filterForInferenceCount:Ue.inference,filterForBatchCount:Ue.batch,filterForSystemCount:Ue.system},e[20]=T.first,e[21]=T.offset,e[22]=N,e[23]=dt,e[24]=ft):ft=e[24];let P=ft,F,pt;if(e[25]!==O.filter||e[26]!==M||e[27]!==at){let{projectId:t,remainder:n}=Ie(O.filter??``);F=t,pt=me([M,n,at]),e[25]=O.filter,e[26]=M,e[27]=at,e[28]=F,e[29]=pt}else F=e[28],pt=e[29];let mt=pt,I=(0,x.useDeferredValue)(P),L=(0,x.useDeferredValue)(st),ht=L===`first`?`store-and-network`:`network-only`,gt;e[30]!==L||e[31]!==ht?(gt={fetchPolicy:ht,fetchKey:L},e[30]=L,e[31]=ht,e[32]=gt):gt=e[32];let _t=(0,Be.useLazyLoadQuery)(Fe,I,gt),R,z;e[33]===_t?(R=e[34],z=e[35]):({computeSessionNodeResult:R,...z}=_t,e[33]=_t,e[34]=R,e[35]=z);let B=R.ok?R.value:null,vt;e[36]===(B==null?void 0:B.edges)?vt=e[37]:(vt=pe(B==null?void 0:B.edges.map(Ke)),e[36]=B==null?void 0:B.edges,e[37]=vt);let yt=vt,bt,xt,St,Ct,wt,Tt,Et;e[38]===Symbol.for(`react.memo_cache_sentinel`)?(bt={hidden:!1},xt={hidden:!1},St={hidden:!1},Ct={hidden:!1},wt={hidden:!1},Tt={hidden:!1},Et={hidden:!1},e[38]=bt,e[39]=xt,e[40]=St,e[41]=Ct,e[42]=wt,e[43]=Tt,e[44]=Et):(bt=e[38],xt=e[39],St=e[40],Ct=e[41],wt=e[42],Tt=e[43],Et=e[44]);let Dt;e[45]===O.statusCategory?Dt=e[46]:(Dt={sessionId:bt,environment:xt,resourceGroup:St,type:Ct,cluster_mode:wt,created_at:Tt,project_id:Et,...O.statusCategory===`finished`?{terminated_at:{hidden:!1}}:{}},e[45]=O.statusCategory,e[46]=Dt);let Ot=Dt,kt=O.type,V;e[47]!==O.view||e[48]!==k||e[49]!==D?(V=e=>{let t=nt.current[e]||{queryParams:{statusCategory:`running`}};k(null),k({...t.queryParams,type:e,view:O.view}),D(t.tablePaginationOption||{current:1}),y([])},e[47]=O.view,e[48]=k,e[49]=D,e[50]=V):V=e[50];let H;if(e[51]!==O.type||e[52]!==z||e[53]!==a){let t;e[55]!==O.type||e[56]!==z?(t=(e,t)=>{var n;let r=((n=z[t])==null?void 0:n.count)??0;return{key:t,label:e,endContent:(0,S.jsx)(ae,{count:r,selected:O.type===t})}},e[55]=O.type,e[56]=z,e[57]=t):t=e[57],H=f({all:a(`general.All`),interactive:a(`session.Interactive`),batch:a(`session.Batch`),inference:a(`session.Inference`),system:a(`session.System`)},t),e[51]=O.type,e[52]=z,e[53]=a,e[54]=H}else H=e[54];let U;e[58]!==O.type||e[59]!==V||e[60]!==H?(U=(0,S.jsx)(Oe,{activeKey:kt,onChange:V,items:H}),e[58]=O.type,e[59]=V,e[60]=H,e[61]=U):U=e[61];let At;e[62]===Symbol.for(`react.memo_cache_sentinel`)?(At={flexShrink:1},e[62]=At):At=e[62];let jt=O.statusCategory,W;e[63]!==k||e[64]!==D?(W=e=>{k({statusCategory:e}),D({current:1}),y([])},e[63]=k,e[64]=D,e[65]=W):W=e[65];let G;e[66]===a?G=e[67]:(G=a(`session.Running`),e[66]=a,e[67]=G);let K;e[68]===G?K=e[69]:(K=(0,S.jsx)(Se,{value:`running`,label:G}),e[68]=G,e[69]=K);let q;e[70]===a?q=e[71]:(q=a(`session.Finished`),e[70]=a,e[71]=q);let J;e[72]===q?J=e[73]:(J=(0,S.jsx)(Se,{value:`finished`,label:q}),e[72]=q,e[73]=J);let Y;e[74]!==O.statusCategory||e[75]!==W||e[76]!==K||e[77]!==J?(Y=(0,S.jsxs)(xe,{value:jt,onChange:W,children:[K,J]}),e[74]=O.statusCategory,e[75]=W,e[76]=K,e[77]=J,e[78]=Y):Y=e[78];let X;e[79]===a?X=e[80]:(X=fe([{key:`id`,propertyLabel:a(`session.SessionId`),type:`uuid`},{key:`project_id`,propertyLabel:a(`data.Project`),type:`string`,defaultOperator:`==`,renderInput:e=>{let{onAddCondition:t,value:n,isDisabled:r}=e;return(0,S.jsx)(Ce,{label:a(`data.Project`),isLabelHidden:!0,value:n,isDisabled:r,onChange:(e,n)=>{var r;t(e,(r=s(n??[])[0])==null?void 0:r.label)}})}},{key:`name`,propertyLabel:a(`session.SessionName`),type:`string`},{key:`scaling_group`,propertyLabel:a(`session.ResourceGroup`),type:`string`},{key:`agent_ids`,propertyLabel:a(`session.Agent`),type:`string`},{key:`user_email`,propertyLabel:a(`session.launcher.OwnerEmail`),type:`string`},{key:`full_name`,propertyLabel:a(`credential.FullName`),type:`string`},{key:`group_name`,propertyLabel:a(`session.ProjectName`),type:`string`},{key:`access_key`,propertyLabel:a(`general.AccessKey`),type:`string`},{key:`images`,propertyLabel:a(`session.launcher.Environments`),type:`string`},{key:`status_info`,propertyLabel:a(`session.StatusInfo`),type:`string`},{key:`result`,propertyLabel:a(`session.Result`),type:`string`,strictSelection:!0,defaultOperator:`==`,options:f(He,qe)},{key:`cluster_mode`,propertyLabel:a(`session.ClusterMode`),type:`string`,strictSelection:!0,defaultOperator:`==`,options:[{label:a(`session.launcher.SingleNode`),value:`single-node`},{label:a(`session.launcher.MultiNode`),value:`multi-node`}]},{key:`priority`,propertyLabel:a(`session.Priority`),type:`number`},{key:`created_at`,propertyLabel:a(`session.CreatedAt`),type:`datetime`},{key:`terminated_at`,propertyLabel:a(`session.TerminatedAt`),type:`datetime`}]),e[79]=a,e[80]=X);let Mt=O.filter||void 0,Z;e[81]!==k||e[82]!==D?(Z=e=>{k({filter:e||``}),D({current:1}),y([])},e[81]=k,e[82]=D,e[83]=Z):Z=e[83];let Nt;e[84]!==X||e[85]!==Mt||e[86]!==Z?(Nt=(0,S.jsx)(he,{filterProperties:X,value:Mt,onChange:Z}),e[84]=X,e[85]=Mt,e[86]=Z,e[87]=Nt):Nt=e[87];let Pt;e[88]!==Y||e[89]!==Nt?(Pt=(0,S.jsxs)(h,{gap:`sm`,align:`start`,style:At,wrap:`wrap`,children:[Y,Nt]}),e[88]=Y,e[89]=Nt,e[90]=Pt):Pt=e[90];let Q;e[91]!==v.length||e[92]!==a?(Q=v.length>0&&(0,S.jsxs)(S.Fragment,{children:[(0,S.jsx)(_e,{count:v.length,onClearSelection:()=>y([])}),(0,S.jsx)(re,{label:a(`session.TerminateSession`),tooltip:a(`session.TerminateSession`),icon:(0,S.jsx)(t,{color:`var(--color-error)`}),onClick:()=>{Re(!0)}})]}),e[91]=v.length,e[92]=a,e[93]=Q):Q=e[93];let Ft;e[94]!==w||e[95]!==O.view||e[96]!==k||e[97]!==a?(Ft=w&&(0,S.jsxs)(xe,{"aria-label":a(`session.resourceGrid.ViewMode`),value:O.view,onChange:e=>k({view:e}),children:[(0,S.jsx)(m,{content:a(`session.resourceGrid.TableView`),children:(0,S.jsx)(Se,{value:`table`,label:a(`session.resourceGrid.TableView`),isLabelHidden:!0,icon:(0,S.jsx)(r,{size:`1em`})})}),(0,S.jsx)(m,{content:a(`session.resourceGrid.GridView`),children:(0,S.jsx)(Se,{value:`grid`,label:a(`session.resourceGrid.GridView`),isLabelHidden:!0,icon:(0,S.jsx)(i,{size:`1em`})})})]}),e[94]=w,e[95]=O.view,e[96]=k,e[97]=a,e[98]=Ft):Ft=e[98];let It=I!==P||L!==st,Lt;e[99]===ct?Lt=e[100]:(Lt=e=>{ct(e)},e[99]=ct,e[100]=Lt);let Rt;e[101]!==st||e[102]!==It||e[103]!==Lt?(Rt=(0,S.jsx)(De,{settingId:`admin-session-list`,defaultAutoUpdateDelay:15e3,loading:It,value:st,onChange:Lt}),e[101]=st,e[102]=It,e[103]=Lt,e[104]=Rt):Rt=e[104];let zt;e[105]!==Q||e[106]!==Ft||e[107]!==Rt?(zt=(0,S.jsxs)(h,{gap:`xs`,children:[Q,Ft,Rt]}),e[105]=Q,e[106]=Ft,e[107]=Rt,e[108]=zt):zt=e[108];let Bt;e[109]!==Pt||e[110]!==zt?(Bt=(0,S.jsxs)(h,{justify:`between`,wrap:`wrap`,gap:`sm`,children:[Pt,zt]}),e[109]=Pt,e[110]=zt,e[111]=Bt):Bt=e[111];let Vt;e[112]!==b||e[113]!==R.ok||e[114]!==(B==null?void 0:B.count)||e[115]!==Ot||e[116]!==L||e[117]!==I||e[118]!==w||e[119]!==Xe||e[120]!==mt||e[121]!==F||e[122]!==g||e[123]!==l||e[124]!==o||e[125]!==O||e[126]!==P||e[127]!==v||e[128]!==yt||e[129]!==We||e[130]!==k||e[131]!==D||e[132]!==Ye||e[133]!==a||e[134]!==E||e[135]!==n||e[136]!==p?(Vt=w&&O.view===`grid`?(0,S.jsx)(x.Suspense,{fallback:(0,S.jsx)(be,{}),children:(0,S.jsx)(ye,{filter:mt,projectId:F,order:P.order??void 0,fetchKey:L,onClickSession:e=>{let t=new URLSearchParams(g.search);t.set(`sessionDetail`,e),p({pathname:g.pathname,hash:g.hash,search:t.toString()})}})},`${mt??``}:${F??``}:${P.order??``}`):R.ok?(0,S.jsxs)(S.Fragment,{children:[(0,S.jsx)(Ne,{sessionsFrgmt:yt,columnOverrides:{...Ot,...b},page:E.current,pageSize:E.pageSize,total:B==null?void 0:B.count,pending:I!==P,viewParams:c(O,`view`)}),(0,S.jsx)(je,{order:O.order,onClickSessionName:e=>{let t=new URLSearchParams(g.search);t.set(`sessionDetail`,e.row_id),p({pathname:g.pathname,hash:g.hash,search:t.toString()},{state:{sessionDetailDrawerFrgmt:e,createdAt:new Date().toISOString()}})},loading:I!==P,rowSelection:{type:`checkbox`,preserveSelectedRowKeys:!0,getCheckboxProps(e){return{disabled:ot(e.status)}},onChange:e=>{le(e,yt,y)},selectedRowKeys:f(v,Je)},sessionsFrgmt:yt,pagination:{pageSize:E.pageSize,current:E.current,total:(B==null?void 0:B.count)??0,onChange:(e,t)=>{u(e)&&u(t)&&D({current:e,pageSize:t})}},onChangeOrder:e=>{k({order:e})},tableSettings:{columnOverrides:b,defaultColumnOverrides:Ot,onColumnOverridesChange:We},exportSettings:!ee(Ye)&&(n===`superadmin`||n===`admin`)?{supportedFields:Ye,onExport:async e=>{let t={};t.status=O.statusCategory===`finished`?[`TERMINATED`,`CANCELLED`]:[`PENDING`,`SCHEDULED`,`PREPARING`,`PREPARED`,`CREATING`,`PULLING`,`RESTARTING`,`RUNNING`,`TERMINATING`,`ERROR`],O.type&&O.type!==`all`&&(t.session_type=[O.type]),d(t,ze(O.filter)),await Xe(e,t).catch(e=>{o.error(a(`general.ErrorOccurred`)),l.error(e)})}}:void 0})]}):(0,S.jsx)(ge,{role:`alert`,status:`error`,title:a(`error.FailedToLoadTableData`)}),e[112]=b,e[113]=R.ok,e[114]=B==null?void 0:B.count,e[115]=Ot,e[116]=L,e[117]=I,e[118]=w,e[119]=Xe,e[120]=mt,e[121]=F,e[122]=g,e[123]=l,e[124]=o,e[125]=O,e[126]=P,e[127]=v,e[128]=yt,e[129]=We,e[130]=k,e[131]=D,e[132]=Ye,e[133]=a,e[134]=E,e[135]=n,e[136]=p,e[137]=Vt):Vt=e[137];let Ht;e[138]!==Bt||e[139]!==Vt?(Ht=(0,S.jsxs)(h,{direction:`column`,align:`stretch`,gap:`sm`,children:[Bt,Vt]}),e[138]=Bt,e[139]=Vt,e[140]=Ht):Ht=e[140];let Ut;e[141]===Symbol.for(`react.memo_cache_sentinel`)?(Ut=e=>{Re(!1),e&&y([])},e[141]=Ut):Ut=e[141];let $;e[142]!==Le||e[143]!==v?($=(0,S.jsx)(ve,{open:Le,sessionFrgmts:v,onRequestClose:Ut}),e[142]=Le,e[143]=v,e[144]=$):$=e[144];let Wt;return e[145]!==U||e[146]!==Ht||e[147]!==$?(Wt=(0,S.jsxs)(h,{direction:`column`,align:`stretch`,gap:`sm`,children:[U,Ht,$]}),e[145]=U,e[146]=Ht,e[147]=$,e[148]=Wt):Wt=e[148],Wt};function Ge(e){return e===`TERMINATED`||e===`CANCELLED`}function Ke(e){return e==null?void 0:e.node}function qe(e){return{label:e,value:e}}function Je(e){return e.id}export{We as default};
