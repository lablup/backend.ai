import{c as an,a2 as sn,u as ln,bb as rn,c0 as on,aK as dn,bs as un,g as Oe,i as Ae,p as mn,k as cn,l as gn,r as pn,o as fn,n as l,I as yn,w as $e,aR as qe,B as Ie,q as Ue,y as Sn,bj as Fn,s as kn,C as ce}from"./index-CwWAznqi.js";import{A as _n}from"./AutoUpdateFetchKeyButton-MZ4HY-Ai.js";import{B as Cn}from"./BAITabs-C13WiJ9B.js";import{T as hn}from"./TerminateSessionModal-Bj88xpmv.js";import{S as vn,a as Ln}from"./SessionNodes-DSYGA-eW.js";import{S as Nn,B as bn}from"./SessionResourceGrid-22qzvlVl.js";import{d as An,o as In,q as Ge,m as xe,J as Kn,D as Tn,S as wn,i as Qe}from"./lodash-RhKGq0BF.js";import{u as Rn}from"./reactPaginationQueryOptions-Bt4rkB5i.js";import{u as En}from"./useCSVExport-DWiMiAHP.js";import{r as j,y as Pn,z as jn,G as xn}from"./icons-BgdBQS0N.js";import{m as ze,B as Bn}from"./BAIPropertyFilter-CgtWad1r.js";import{B as Mn}from"./BAIAdminProjectSelect-1toun7Jn.js";import{B as Vn}from"./BAISelectionLabel-DSve7JI4.js";import{B as Dn}from"./BAITabCountBadge-DWn3CrgC.js";import"./BAIFetchKeyButton-DApd5OLT.js";import"./useControllableValue-BmgV_ECW.js";import"./ButtonGroup-DPQvGHtt.js";import"./useBackendAIAppLauncher-Dj1iRGeB.js";import"./BAIMetadataList-BYZUwKjA.js";import"./SourceCodeView-jXLvuWSO.js";import"./CodeBlock-CV2dJgqa.js";import"./useScrollableArea-Bsuw_xFk.js";import"./Grid-BAKellpz.js";import"./TagsInput-B_f8kLOn.js";import"./Tokenizer-Czn8bbzO.js";import"./groupItems-BfxkhRY8.js";import"./characters-DWaYg7k3.js";import"./Token-B6wppFPd.js";import"./CheckboxInput-Dvbz8RhO.js";import"./NumberInput-BX3bbN7A.js";import"./NumberInput-BAShrYzU.js";import"./useLocale-tF6sKPhr.js";import"./usePainKiller-BiH1iwVD.js";import"./BAITokenList-CJlafqP1.js";import"./HoverCard-5uBx5TYH.js";import"./BAIBulkEditFormItem-DkPLVXXQ.js";import"./SessionUsageMonitor-Dj-fxRUF.js";import"./sessionTypeLabel-DAMPaqv3.js";import"./astryxTagVariant-CibgwVXb.js";import"./index-CIBhdd6O.js";import"./BAIImageNodeSimpleTagV2-grs0QBeV.js";import"./BAIDoubleToken-DmnYFlRB.js";import"./BAITextHighlighter-9-PRKuKt.js";import"./useBAIIconPath-kZbqwXZ-.js";import"./useSessionNodeLiveStat-D4fXH5-b.js";import"./BAIProgressWithLabel-CnpA-yWW.js";import"./GridSpan-CXov5J6d.js";import"./SessionStatusBadge-MHSUzVAj.js";import"./unifiedAcceleratorSlot-DvOww2Yq.js";import"./BAIBadge-9d3LJqR4.js";import"./BAITable-BJsxYyy0.js";import"./Table-SIAPvWUk.js";import"./MenuBottomSheetActionList-DfgiyqqP.js";import"./Pagination-cBiGXF8Y.js";import"./BAIId-C7PlhBcJ.js";import"./BAISessionClusterMode-Dx7hBE1h.js";import"./BAINameActionCell-BZc0os_M.js";import"./sessionTypeLabel-BoA-LXO4.js";import"./csv-util-DjAHMT44.js";import"./BAIPowerSearchAdapters-Cpa0dtdE.js";import"./DateRangeInput-BafIu0I7.js";import"./BottomSheet-C7Cy7dyi.js";import"./usePaginatedQuery-D34XeqI8.js";import"./BAIComplexSelect-D8NzXrV7.js";const He=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},s={defaultValue:null,kind:"LocalArgument",name:"filterForAllCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForBatchCount"},i={defaultValue:null,kind:"LocalArgument",name:"filterForInferenceCount"},u={defaultValue:null,kind:"LocalArgument",name:"filterForInteractiveCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForSystemCount"},p={defaultValue:20,kind:"LocalArgument",name:"first"},_={defaultValue:0,kind:"LocalArgument",name:"offset"},c={defaultValue:null,kind:"LocalArgument",name:"order"},S=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},h={kind:"Literal",name:"first",value:0},F={kind:"Literal",name:"offset",value:0},k=[C],x={alias:"all",args:[{kind:"Variable",name:"filter",variableName:"filterForAllCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},w={alias:"interactive",args:[{kind:"Variable",name:"filter",variableName:"filterForInteractiveCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},v={alias:"inference",args:[{kind:"Variable",name:"filter",variableName:"filterForInferenceCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},y={alias:"batch",args:[{kind:"Variable",name:"filter",variableName:"filterForBatchCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},f={alias:"system",args:[{kind:"Variable",name:"filter",variableName:"filterForSystemCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},g=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],pe={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},N=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,L,T,b],storageKey:null}],storageKey:null},C];return{fragment:{argumentDefinitions:[e,s,n,i,u,r,p,_,c],kind:"Fragment",metadata:null,name:"AdminComputeSessionListPageQuery",selections:[{kind:"CatchField",field:{alias:"computeSessionNodeResult",args:S,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:o,action:"THROW"},{kind:"RequiredField",field:T,action:"THROW"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},C],storageKey:null},to:"RESULT"},x,w,v,y,f],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[p,_,e,c,s,u,i,n,r],kind:"Operation",name:"AdminComputeSessionListPageQuery",selections:[{alias:"computeSessionNodeResult",args:S,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,T,L,b,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,b,{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:g,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:g,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},pe,o],storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},pe,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},o],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[L,T,o],storageKey:null}],storageKey:null},C],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:N,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:N,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null},C],storageKey:null},x,w,v,y,f]},params:{cacheID:"a2f90974a74cd533199ccf3394caf5b1",id:null,metadata:{},name:"AdminComputeSessionListPageQuery",operationKind:"query",text:`query AdminComputeSessionListPageQuery(
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
`}}})();He.hash="7c8dbadc30e34da0dc4a5dd7f6c4a230";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Lifts a project condition out of the admin session filter for the grid's
 legacy `compute_session_list` query, which has no `project_id` queryfilter
 field but does take a `group_id` argument (FR-3571).
 */const We=e=>{const s=[];let n=0,i=!1,u="";for(const r of e)r==='"'?i=!i:!i&&r==="("?n+=1:!i&&r===")"&&(n-=1),r==="&"&&n===0&&!i?(s.push(u),u=""):u+=r;return s.push(u),s.map(r=>r.trim()).filter(Boolean)},Je=e=>{let s=0,n=!1;for(const i of e)if(i==='"')n=!n;else if(!n&&i==="(")s+=1;else if(!n&&i===")")s-=1;else if(i==="|"&&s===0&&!n)return!0;return!1},Be=/^\(*\s*project_id\s*(?:==|ilike)\s*"%?([^"%]+)%?"\s*\)*$/,On=e=>{var r;const s={projectId:void 0,remainder:e||void 0};if(!e||Je(e))return s;const n=We(e),i=n.filter(p=>Be.test(p));if(i.length!==1)return s;const u=n.filter(p=>!Be.test(p));return{projectId:(r=Be.exec(i[0]))==null?void 0:r[1],remainder:u.join("&")||void 0}};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Translates the admin session list's queryfilter minilang string into the
 `POST /export/sessions/csv` filter body, so the CSV narrows to the table's
 own conditions wherever the export endpoint can express them (FR-3915).
 Whatever it cannot express is dropped, leaving the CSV a superset — see
 `buildSessionExportFilter` for the conditions that keeps.
 */const $n={name:"name",domain_name:"domain_name",access_key:"access_key"},qn=/^\(*\s*([a-z_]+)\s*(==|!=|>=|<=|ilike|like)\s*(?:"([^"]*)"|([^\s")]+))\s*\)*$/,Me=(e,s)=>{switch(e){case"==":return{equals:s};case"!=":return{not_equals:s};case"ilike":case"like":return/^%[^%]*%$/.test(s)?{i_contains:s.slice(1,-1)}:void 0;default:return}},Un=e=>{const s={};return!e||Je(e)||An(We(e),n=>{const i=qn.exec(n);if(!i)return;const[,u,r,p,_]=i,c=p??_;if(In(c)||c==="")return;const S=$n[u];if(S){const o=Me(r,c);o&&(s[S]=o);return}if(u==="scaling_group"){const o=Me(r,c);o&&(s.scaling_group_name=o);return}if(u==="user_email"){const o=Me(r,c);o&&(s.user={email:o});return}if(u==="created_at"||u==="terminated_at"){const o=r===">="?"after":r==="<="?"before":void 0;if(!o)return;s[u]={...s[u],[o]:c};return}}),s},Gn=["all","interactive","batch","inference","system"],de='status != "TERMINATED" & status != "CANCELLED"',Qn=["UNDEFINED","SUCCESS","FAILURE"],ge={all:de,interactive:`${de} & type == "interactive"`,inference:`${de} & type == "inference"`,batch:`${de} & type == "batch"`,system:`${de} & type == "system"`},oa=()=>{"use memo";const e=an.c(142),s=sn(),{t:n}=ln(),{message:i}=rn.useApp(),{logger:u}=on(),r=dn(),p=un();let _;e[0]===Symbol.for("react.memo_cache_sentinel")?(_=[],e[0]=_):_=e[0];const[c,S]=j.useState(_),[o,T]=j.useState(!1),[C,h]=Oe("table_column_overrides.AdminComputeSessionListPage"),[F]=Oe("experimental_session_resource_grid"),{supportedFields:k,exportCSV:x}=En("sessions");let w;e[1]===Symbol.for("react.memo_cache_sentinel")?(w={current:1,pageSize:10},e[1]=w):w=e[1];const{baiPaginationOption:v,tablePaginationOption:y,setTablePaginationOption:f}=Rn(w);let L,b;e[2]===Symbol.for("react.memo_cache_sentinel")?(L={order:Ae(Ln),filter:mn.withDefault(""),type:Ae(Gn).withDefault("all"),statusCategory:Ae(["running","finished"]).withDefault("running"),view:Ae(["table","grid"]).withDefault("table")},b={history:"replace"},e[2]=L,e[3]=b):(L=e[2],b=e[3]);const[t,g]=cn(L,b),pe=t.type;let N;e[4]!==t?(N=Ge(t,["view"]),e[4]=t,e[5]=N):N=e[5];let B;e[6]!==N||e[7]!==y?(B={queryParams:N,tablePaginationOption:y},e[6]=N,e[7]=y,e[8]=B):B=e[8];let fe;e[9]!==t.type||e[10]!==B?(fe={[pe]:B},e[9]=t.type,e[10]=B,e[11]=fe):fe=e[11];const Ve=j.useRef(fe);let ye,Se;e[12]!==t||e[13]!==y?(ye=()=>{Ve.current[t.type]={queryParams:Ge(t,["view"]),tablePaginationOption:y}},Se=[t,y],e[12]=t,e[13]=y,e[14]=ye,e[15]=Se):(ye=e[14],Se=e[15]),j.useEffect(ye,Se);const M=t.type==="all"||t.type===void 0?void 0:`type == "${t.type}"`,V=t.statusCategory==="running"||t.statusCategory===void 0?de:'status == "TERMINATED" | status == "CANCELLED"',Ye=zn,[ue,Ke]=gn(),Xe=v.offset,Ze=v.first;let D;e[16]!==t.filter||e[17]!==V||e[18]!==M?(D=ze([V,t.filter,M]),e[16]=t.filter,e[17]=V,e[18]=M,e[19]=D):D=e[19];const Te=t.order||"-created_at";let Fe;e[20]!==v.first||e[21]!==v.offset||e[22]!==D||e[23]!==Te?(Fe={offset:Xe,first:Ze,filter:D,order:Te,filterForAllCount:ge.all,filterForInteractiveCount:ge.interactive,filterForInferenceCount:ge.inference,filterForBatchCount:ge.batch,filterForSystemCount:ge.system},e[20]=v.first,e[21]=v.offset,e[22]=D,e[23]=Te,e[24]=Fe):Fe=e[24];const R=Fe;let E,ke;if(e[25]!==t.filter||e[26]!==V||e[27]!==M){const{projectId:a,remainder:d}=On(t.filter??"");E=a,ke=ze([V,d,M]),e[25]=t.filter,e[26]=V,e[27]=M,e[28]=E,e[29]=ke}else E=e[28],ke=e[29];const _e=ke,me=j.useDeferredValue(R),A=j.useDeferredValue(ue);let Ce;e[30]===Symbol.for("react.memo_cache_sentinel")?(Ce=He,e[30]=Ce):Ce=e[30];const we=A===kn?"store-and-network":"network-only";let he;e[31]!==A||e[32]!==we?(he={fetchPolicy:we,fetchKey:A},e[31]=A,e[32]=we,e[33]=he):he=e[33];const Re=pn.useLazyLoadQuery(Ce,me,he);let I,K;e[34]!==Re?({computeSessionNodeResult:I,...K}=Re,e[34]=Re,e[35]=I,e[36]=K):(I=e[35],K=e[36]);const m=I.ok?I.value:null,en=t.type;let O;e[37]!==t.view||e[38]!==g||e[39]!==f?(O=a=>{const d=Ve.current[a]||{queryParams:{statusCategory:"running"}};g(null),g({...d.queryParams,type:a,view:t.view}),f(d.tablePaginationOption||{current:1}),S([])},e[37]=t.view,e[38]=g,e[39]=f,e[40]=O):O=e[40];let $;if(e[41]!==t.type||e[42]!==K||e[43]!==n){let a;e[45]!==t.type||e[46]!==K?(a=(d,P)=>{var be;const je=((be=K[P])==null?void 0:be.count)??0;return{key:P,label:d,endContent:l.jsx(Dn,{count:je,selected:t.type===P})}},e[45]=t.type,e[46]=K,e[47]=a):a=e[47],$=xe({all:n("general.All"),interactive:n("session.Interactive"),batch:n("session.Batch"),inference:n("session.Inference"),system:n("session.System")},a),e[41]=t.type,e[42]=K,e[43]=n,e[44]=$}else $=e[44];let q;e[48]!==t.type||e[49]!==O||e[50]!==$?(q=l.jsx(Cn,{activeKey:en,onChange:O,items:$}),e[48]=t.type,e[49]=O,e[50]=$,e[51]=q):q=e[51];let ve;e[52]===Symbol.for("react.memo_cache_sentinel")?(ve={flexShrink:1},e[52]=ve):ve=e[52];const nn=t.statusCategory;let U;e[53]!==g||e[54]!==f?(U=a=>{g({statusCategory:a}),f({current:1}),S([])},e[53]=g,e[54]=f,e[55]=U):U=e[55];let G;e[56]!==n?(G=n("session.Running"),e[56]=n,e[57]=G):G=e[57];let Q;e[58]!==G?(Q=l.jsx(Ie,{value:"running",label:G}),e[58]=G,e[59]=Q):Q=e[59];let z;e[60]!==n?(z=n("session.Finished"),e[60]=n,e[61]=z):z=e[61];let H;e[62]!==z?(H=l.jsx(Ie,{value:"finished",label:z}),e[62]=z,e[63]=H):H=e[63];let W;e[64]!==t.statusCategory||e[65]!==U||e[66]!==Q||e[67]!==H?(W=l.jsxs($e,{value:nn,onChange:U,children:[Q,H]}),e[64]=t.statusCategory,e[65]=U,e[66]=Q,e[67]=H,e[68]=W):W=e[68];let J;e[69]!==n?(J=fn([{key:"id",propertyLabel:n("session.SessionId"),type:"uuid"},{key:"project_id",propertyLabel:n("data.Project"),type:"string",defaultOperator:"==",renderInput:a=>{const{onAddCondition:d,value:P,isDisabled:je}=a;return l.jsx(Mn,{label:n("data.Project"),isLabelHidden:!0,value:P,isDisabled:je,onChange:(be,tn)=>{var De;d(be,(De=Kn(tn??[])[0])==null?void 0:De.label)}})}},{key:"name",propertyLabel:n("session.SessionName"),type:"string"},{key:"scaling_group",propertyLabel:n("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:n("session.Agent"),type:"string"},{key:"user_email",propertyLabel:n("session.launcher.OwnerEmail"),type:"string"},{key:"full_name",propertyLabel:n("credential.FullName"),type:"string"},{key:"group_name",propertyLabel:n("session.ProjectName"),type:"string"},{key:"access_key",propertyLabel:n("general.AccessKey"),type:"string"},{key:"images",propertyLabel:n("session.launcher.Environments"),type:"string"},{key:"status_info",propertyLabel:n("session.StatusInfo"),type:"string"},{key:"result",propertyLabel:n("session.Result"),type:"string",strictSelection:!0,defaultOperator:"==",options:xe(Qn,Hn)},{key:"cluster_mode",propertyLabel:n("session.ClusterMode"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:n("session.launcher.SingleNode"),value:"single-node"},{label:n("session.launcher.MultiNode"),value:"multi-node"}]},{key:"priority",propertyLabel:n("session.Priority"),type:"number"},{key:"created_at",propertyLabel:n("session.CreatedAt"),type:"datetime"},{key:"terminated_at",propertyLabel:n("session.TerminatedAt"),type:"datetime"}]),e[69]=n,e[70]=J):J=e[70];const Ee=t.filter||void 0;let Y;e[71]!==g||e[72]!==f?(Y=a=>{g({filter:a||""}),f({current:1}),S([])},e[71]=g,e[72]=f,e[73]=Y):Y=e[73];let X;e[74]!==J||e[75]!==Ee||e[76]!==Y?(X=l.jsx(Bn,{filterProperties:J,value:Ee,onChange:Y}),e[74]=J,e[75]=Ee,e[76]=Y,e[77]=X):X=e[77];let Z;e[78]!==W||e[79]!==X?(Z=l.jsxs(ce,{gap:"sm",align:"start",style:ve,wrap:"wrap",children:[W,X]}),e[78]=W,e[79]=X,e[80]=Z):Z=e[80];let ee;e[81]!==c.length||e[82]!==n?(ee=c.length>0&&l.jsxs(l.Fragment,{children:[l.jsx(Vn,{count:c.length,onClearSelection:()=>S([])}),l.jsx(yn,{label:n("session.TerminateSession"),tooltip:n("session.TerminateSession"),icon:l.jsx(Pn,{color:"var(--color-error)"}),onClick:()=>{T(!0)}})]}),e[81]=c.length,e[82]=n,e[83]=ee):ee=e[83];let ne;e[84]!==F||e[85]!==t.view||e[86]!==g||e[87]!==n?(ne=F&&l.jsxs($e,{"aria-label":n("session.resourceGrid.ViewMode"),value:t.view,onChange:a=>g({view:a}),children:[l.jsx(qe,{content:n("session.resourceGrid.TableView"),children:l.jsx(Ie,{value:"table",label:n("session.resourceGrid.TableView"),isLabelHidden:!0,icon:l.jsx(jn,{size:"1em"})})}),l.jsx(qe,{content:n("session.resourceGrid.GridView"),children:l.jsx(Ie,{value:"grid",label:n("session.resourceGrid.GridView"),isLabelHidden:!0,icon:l.jsx(xn,{size:"1em"})})})]}),e[84]=F,e[85]=t.view,e[86]=g,e[87]=n,e[88]=ne):ne=e[88];const Pe=me!==R||A!==ue;let te;e[89]!==Ke?(te=a=>{Ke(a)},e[89]=Ke,e[90]=te):te=e[90];let ae;e[91]!==ue||e[92]!==Pe||e[93]!==te?(ae=l.jsx(_n,{settingId:"admin-session-list",defaultAutoUpdateDelay:15e3,loading:Pe,value:ue,onChange:te}),e[91]=ue,e[92]=Pe,e[93]=te,e[94]=ae):ae=e[94];let se;e[95]!==ee||e[96]!==ne||e[97]!==ae?(se=l.jsxs(ce,{gap:"xs",children:[ee,ne,ae]}),e[95]=ee,e[96]=ne,e[97]=ae,e[98]=se):se=e[98];let le;e[99]!==Z||e[100]!==se?(le=l.jsxs(ce,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,se]}),e[99]=Z,e[100]=se,e[101]=le):le=e[101];let re;e[102]!==C||e[103]!==I.ok||e[104]!==(m==null?void 0:m.count)||e[105]!==(m==null?void 0:m.edges)||e[106]!==A||e[107]!==me||e[108]!==F||e[109]!==x||e[110]!==_e||e[111]!==E||e[112]!==p||e[113]!==u||e[114]!==i||e[115]!==t.filter||e[116]!==t.order||e[117]!==t.statusCategory||e[118]!==t.type||e[119]!==t.view||e[120]!==R||e[121]!==c||e[122]!==h||e[123]!==g||e[124]!==f||e[125]!==k||e[126]!==n||e[127]!==y||e[128]!==s||e[129]!==r?(re=F&&t.view==="grid"?l.jsx(j.Suspense,{fallback:l.jsx(bn,{}),children:l.jsx(Nn,{filter:_e,projectId:E,order:R.order??void 0,fetchKey:A,onClickSession:a=>{const d=new URLSearchParams(p.search);d.set("sessionDetail",a),r({pathname:p.pathname,hash:p.hash,search:d.toString()})}})},`${_e??""}:${E??""}:${R.order??""}`):I.ok?l.jsx(vn,{order:t.order,onClickSessionName:a=>{const d=new URLSearchParams(p.search);d.set("sessionDetail",a.row_id),r({pathname:p.pathname,hash:p.hash,search:d.toString()},{state:{sessionDetailDrawerFrgmt:a,createdAt:new Date().toISOString()}})},loading:me!==R,rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(a){return{disabled:Ye(a.status)}},onChange:a=>{Sn(a,Ue(m==null?void 0:m.edges.map(Wn)),S)},selectedRowKeys:xe(c,Jn)},sessionsFrgmt:Ue(m==null?void 0:m.edges.map(Yn)),pagination:{pageSize:y.pageSize,current:y.current,total:(m==null?void 0:m.count)??0,onChange:(a,d)=>{Qe(a)&&Qe(d)&&f({current:a,pageSize:d})}},onChangeOrder:a=>{g({order:a})},tableSettings:{columnOverrides:C,defaultColumnOverrides:{sessionId:{hidden:!1},environment:{hidden:!1},resourceGroup:{hidden:!1},type:{hidden:!1},cluster_mode:{hidden:!1},created_at:{hidden:!1},project_id:{hidden:!1},...t.statusCategory==="finished"?{terminated_at:{hidden:!1}}:{}},onColumnOverridesChange:h},exportSettings:!Tn(k)&&(s==="superadmin"||s==="admin")?{supportedFields:k,onExport:async a=>{const d={};t.statusCategory==="finished"?d.status=["TERMINATED","CANCELLED"]:d.status=["PENDING","SCHEDULED","PREPARING","PREPARED","CREATING","PULLING","RESTARTING","RUNNING","TERMINATING","ERROR"],t.type&&t.type!=="all"&&(d.session_type=[t.type]),wn(d,Un(t.filter)),await x(a,d).catch(P=>{i.error(n("general.ErrorOccurred")),u.error(P)})}}:void 0}):l.jsx(Fn,{role:"alert",status:"error",title:n("error.FailedToLoadTableData")}),e[102]=C,e[103]=I.ok,e[104]=m==null?void 0:m.count,e[105]=m==null?void 0:m.edges,e[106]=A,e[107]=me,e[108]=F,e[109]=x,e[110]=_e,e[111]=E,e[112]=p,e[113]=u,e[114]=i,e[115]=t.filter,e[116]=t.order,e[117]=t.statusCategory,e[118]=t.type,e[119]=t.view,e[120]=R,e[121]=c,e[122]=h,e[123]=g,e[124]=f,e[125]=k,e[126]=n,e[127]=y,e[128]=s,e[129]=r,e[130]=re):re=e[130];let ie;e[131]!==le||e[132]!==re?(ie=l.jsxs(ce,{direction:"column",align:"stretch",gap:"sm",children:[le,re]}),e[131]=le,e[132]=re,e[133]=ie):ie=e[133];let Le;e[134]===Symbol.for("react.memo_cache_sentinel")?(Le=a=>{T(!1),a&&S([])},e[134]=Le):Le=e[134];let oe;e[135]!==o||e[136]!==c?(oe=l.jsx(hn,{open:o,sessionFrgmts:c,onRequestClose:Le}),e[135]=o,e[136]=c,e[137]=oe):oe=e[137];let Ne;return e[138]!==q||e[139]!==ie||e[140]!==oe?(Ne=l.jsxs(ce,{direction:"column",align:"stretch",gap:"sm",children:[q,ie,oe]}),e[138]=q,e[139]=ie,e[140]=oe,e[141]=Ne):Ne=e[141],Ne};function zn(e){return e==="TERMINATED"||e==="CANCELLED"}function Hn(e){return{label:e,value:e}}function Wn(e){return e==null?void 0:e.node}function Jn(e){return e.id}function Yn(e){return e==null?void 0:e.node}export{oa as default};
//# sourceMappingURL=AdminComputeSessionListPage-DNa9j186.js.map
