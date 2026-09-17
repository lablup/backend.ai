import{bg as sn,bC as ln,i as rn,a$ as on,a as dn,u as un,Y as cn,y as mn,Z as gn,ad as pn,l as M,a8 as $e,eO as fn,bG as yn,ca as Te,ag as Sn,is as Fn,af as kn,ar as Ue,aO as _n,dL as qe,r as Cn,am as Me,ai as vn,j as s,cU as hn,cb as Ln,N as bn,hR as Nn,bs as An,s as Ge,br as Qe,dM as In,cg as Tn,a_ as Kn,dN as wn,aY as Rn,an as En,bZ as Pn,bN as ze,aT as He,ej as xn,w as jn,bh as Mn,it as Vn,ab as Bn,de as Dn,b1 as On,c as pe,dx as $n,iu as Un}from"./index-B-6GqBhJ.js";import{B as qn}from"./BAIAdminProjectSelect-B2xlnf4n.js";const We=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"filterForAllCount"},l={defaultValue:null,kind:"LocalArgument",name:"filterForBatchCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForInferenceCount"},y={defaultValue:null,kind:"LocalArgument",name:"filterForInteractiveCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForSystemCount"},g={defaultValue:20,kind:"LocalArgument",name:"first"},F={defaultValue:0,kind:"LocalArgument",name:"offset"},_={defaultValue:null,kind:"LocalArgument",name:"order"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],p={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},C={kind:"Literal",name:"first",value:0},v={kind:"Literal",name:"offset",value:0},k=[N],w={alias:"all",args:[{kind:"Variable",name:"filter",variableName:"filterForAllCount"},C,v],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},V={alias:"interactive",args:[{kind:"Variable",name:"filter",variableName:"filterForInteractiveCount"},C,v],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},R={alias:"inference",args:[{kind:"Variable",name:"filter",variableName:"filterForInferenceCount"},C,v],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},h={alias:"batch",args:[{kind:"Variable",name:"filter",variableName:"filterForBatchCount"},C,v],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},S={alias:"system",args:[{kind:"Variable",name:"filter",variableName:"filterForSystemCount"},C,v],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},E={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},ye=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],L={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},b=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[p,f,c,A],storageKey:null}],storageKey:null},N];return{fragment:{argumentDefinitions:[e,i,l,n,y,r,g,F,_],kind:"Fragment",metadata:null,name:"AdminComputeSessionListPageQuery",selections:[{kind:"CatchField",field:{alias:"computeSessionNodeResult",args:u,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:p,action:"THROW"},{kind:"RequiredField",field:c,action:"THROW"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},N],storageKey:null},to:"RESULT"},w,V,R,h,S],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[g,F,e,_,i,y,n,l,r],kind:"Operation",name:"AdminComputeSessionListPageQuery",selections:[{alias:"computeSessionNodeResult",args:u,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[p,c,f,A,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},E,t,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},m,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},p,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:ye,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:ye,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},m,p],storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},A,t,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},p],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[f,c,p],storageKey:null}],storageKey:null},N],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:b,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:b,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},E,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null},N],storageKey:null},w,V,R,h,S]},params:{cacheID:"37e8979c42517e08f411d11a75412e2a",id:null,metadata:{},name:"AdminComputeSessionListPageQuery",operationKind:"query",text:`query AdminComputeSessionListPageQuery(
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

fragment BAISessionTypeTagFragment on ComputeSessionNode {
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
  priority @since(version: "24.09.0")
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
  row_id
  vfolder_nodes @since(version: "25.4.0") {
    edges {
      node {
        ...FolderLink_vfolderNode
        id
      }
    }
  }
  ...MountedVFolderLinksLegacyLazyFolderLinkFragment
}

fragment MountedVFolderLinksLegacyLazyFolderLinkFragment on ComputeSessionNode {
  row_id
  vfolder_mounts
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
  owner @since(version: "25.13.0") {
    email
    id
  }
  resource_opts
  status
  status_data
  vfolder_mounts
  vfolder_nodes @since(version: "25.4.0") {
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
  idle_checks @since(version: "24.12.0")
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
  ...SessionStatusTagFragment
  ...SessionActionButtonsFragment
  ...BAISessionTypeTagFragment
  ...EditableSessionNameFragment
  ...SessionReservationFragment
  ...ContainerLogModalFragment
  ...SessionUsageMonitorFragment
  ...ContainerCommitModalFragment
  ...SessionIdleChecksNodeFragment
  ...SessionStatusDetailModalFragment
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
  priority @since(version: "24.09.0")
  ...SessionStatusTagFragment
  ...SessionReservationFragment
  ...SessionSlotCellFragment
  ...SessionReclamationStatusCellFragment
  ...SessionUsageMonitorFragment
  ...SessionDetailDrawerFragment
  ...BAISessionAgentIdsFragment
  ...BAISessionTypeTagFragment
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
  owner @since(version: "25.13.0") {
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

fragment SessionStatusDetailModalFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  starts_at
  ...SessionStatusTagFragment
}

fragment SessionStatusTagFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
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
`}}})();We.hash="7c8dbadc30e34da0dc4a5dd7f6c4a230";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Lifts a project condition out of the admin session filter for the grid's
 legacy `compute_session_list` query, which has no `project_id` queryfilter
 field but does take a `group_id` argument (FR-3571).
 */const Ye=e=>{const i=[];let l=0,n=!1,y="";for(const r of e)r==='"'?n=!n:!n&&r==="("?l+=1:!n&&r===")"&&(l-=1),r==="&"&&l===0&&!n?(i.push(y),y=""):y+=r;return i.push(y),i.map(r=>r.trim()).filter(Boolean)},Ze=e=>{let i=0,l=!1;for(const n of e)if(n==='"')l=!l;else if(!l&&n==="(")i+=1;else if(!l&&n===")")i-=1;else if(n==="|"&&i===0&&!l)return!0;return!1},Ve=/^\(*\s*project_id\s*(?:==|ilike)\s*"%?([^"%]+)%?"\s*\)*$/,Gn=e=>{var r;const i={projectId:void 0,remainder:e||void 0};if(!e||Ze(e))return i;const l=Ye(e),n=l.filter(g=>Ve.test(g));if(n.length!==1)return i;const y=l.filter(g=>!Ve.test(g));return{projectId:(r=Ve.exec(n[0]))==null?void 0:r[1],remainder:y.join("&")||void 0}};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Translates the admin session list's queryfilter minilang string into the
 `POST /export/sessions/csv` filter body, so the CSV narrows to the table's
 own conditions wherever the export endpoint can express them (FR-3915).
 Whatever it cannot express is dropped, leaving the CSV a superset — see
 `buildSessionExportFilter` for the conditions that keeps.
 */const Qn={name:"name",domain_name:"domain_name",access_key:"access_key"},zn=/^\(*\s*([a-z_]+)\s*(==|!=|>=|<=|ilike|like)\s*(?:"([^"]*)"|([^\s")]+))\s*\)*$/,Be=(e,i)=>{switch(e){case"==":return{equals:i};case"!=":return{not_equals:i};case"ilike":case"like":return/^%[^%]*%$/.test(i)?{i_contains:i.slice(1,-1)}:void 0;default:return}},Hn=(e,{supportsUserFilter:i})=>{const l={};return!e||Ze(e)||sn(Ye(e),n=>{const y=zn.exec(n);if(!y)return;const[,r,g,F,_]=y,u=F??_;if(ln(u)||u==="")return;const p=Qn[r];if(p){const c=Be(g,u);c&&(l[p]=c);return}if(r==="scaling_group"){const c=Be(g,u);c&&(l.scaling_group_name=c);return}if(r==="user_email"&&i){const c=Be(g,u);c&&(l.user={email:c});return}if(r==="created_at"||r==="terminated_at"){const c=g===">="?"after":g==="<="?"before":void 0;if(!c)return;l[r]={...l[r],[c]:u};return}}),l},Wn=["all","interactive","batch","inference","system"],ce='status != "TERMINATED" & status != "CANCELLED"',Yn=["UNDEFINED","SUCCESS","FAILURE"],fe={all:ce,interactive:`${ce} & type == "interactive"`,inference:`${ce} & type == "inference"`,batch:`${ce} & type == "batch"`,system:`${ce} & type == "system"`},st=()=>{"use memo";const e=rn.c(145),i=on(),l=dn(),{t:n}=un(),{message:y}=cn.useApp(),{logger:r}=mn(),g=gn(),F=pn();let _;e[0]===Symbol.for("react.memo_cache_sentinel")?(_=[],e[0]=_):_=e[0];const[u,p]=M.useState(_),[c,N]=M.useState(!1),[C,v]=$e("table_column_overrides.AdminComputeSessionListPage"),[k]=$e("experimental_session_resource_grid"),{supportedFields:w,exportCSV:V}=fn("sessions");let R;e[1]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[1]=R):R=e[1];const{baiPaginationOption:h,tablePaginationOption:S,setTablePaginationOption:f}=yn(R);let A,E;e[2]===Symbol.for("react.memo_cache_sentinel")?(A={order:Te(Fn),filter:Sn.withDefault(""),type:Te(Wn).withDefault("all"),statusCategory:Te(["running","finished"]).withDefault("running"),view:Te(["table","grid"]).withDefault("table")},E={history:"replace"},e[2]=A,e[3]=E):(A=e[2],E=e[3]);const[t,m]=kn(A,E),ye=t.type;let L;e[4]!==t?(L=Ue(t,["view"]),e[4]=t,e[5]=L):L=e[5];let b;e[6]!==L||e[7]!==S?(b={queryParams:L,tablePaginationOption:S},e[6]=L,e[7]=S,e[8]=b):b=e[8];let Se;e[9]!==t.type||e[10]!==b?(Se={[ye]:b},e[9]=t.type,e[10]=b,e[11]=Se):Se=e[11];const De=M.useRef(Se);let Fe,ke;e[12]!==t||e[13]!==S?(Fe=()=>{De.current[t.type]={queryParams:Ue(t,["view"]),tablePaginationOption:S}},ke=[t,S],e[12]=t,e[13]=S,e[14]=Fe,e[15]=ke):(Fe=e[14],ke=e[15]),M.useEffect(Fe,ke);const B=t.type==="all"||t.type===void 0?void 0:`type == "${t.type}"`,D=t.statusCategory==="running"||t.statusCategory===void 0?ce:'status == "TERMINATED" | status == "CANCELLED"',Je=Zn,[me,Ke]=_n(),Xe=h.offset,en=h.first;let O;e[16]!==t.filter||e[17]!==D||e[18]!==B?(O=qe([D,t.filter,B]),e[16]=t.filter,e[17]=D,e[18]=B,e[19]=O):O=e[19];const we=t.order||"-created_at";let _e;e[20]!==h.first||e[21]!==h.offset||e[22]!==O||e[23]!==we?(_e={offset:Xe,first:en,filter:O,order:we,filterForAllCount:fe.all,filterForInteractiveCount:fe.interactive,filterForInferenceCount:fe.inference,filterForBatchCount:fe.batch,filterForSystemCount:fe.system},e[20]=h.first,e[21]=h.offset,e[22]=O,e[23]=we,e[24]=_e):_e=e[24];const P=_e;let x,Ce;if(e[25]!==t.filter||e[26]!==D||e[27]!==B){const{projectId:a,remainder:o}=Gn(t.filter??"");x=a,Ce=qe([D,o,B]),e[25]=t.filter,e[26]=D,e[27]=B,e[28]=x,e[29]=Ce}else x=e[28],Ce=e[29];const ve=Ce,ge=M.useDeferredValue(P),I=M.useDeferredValue(me);let he;e[30]===Symbol.for("react.memo_cache_sentinel")?(he=We,e[30]=he):he=e[30];const Re=I===Mn?"store-and-network":"network-only";let Le;e[31]!==I||e[32]!==Re?(Le={fetchPolicy:Re,fetchKey:I},e[31]=I,e[32]=Re,e[33]=Le):Le=e[33];const Ee=Cn.useLazyLoadQuery(he,ge,Le);let T,K;e[34]!==Ee?({computeSessionNodeResult:T,...K}=Ee,e[34]=Ee,e[35]=T,e[36]=K):(T=e[35],K=e[36]);const d=T.ok?T.value:null,nn=t.type;let $;e[37]!==t.view||e[38]!==m||e[39]!==f?($=a=>{const o=De.current[a]||{queryParams:{statusCategory:"running"}};m(null),m({...o.queryParams,type:a,view:t.view}),f(o.tablePaginationOption||{current:1}),p([])},e[37]=t.view,e[38]=m,e[39]=f,e[40]=$):$=e[40];let U;if(e[41]!==t.type||e[42]!==K||e[43]!==n){let a;e[45]!==t.type||e[46]!==K?(a=(o,j)=>{var Ie;const je=((Ie=K[j])==null?void 0:Ie.count)??0;return{key:j,label:o,endContent:s.jsx(Vn,{count:je,selected:t.type===j})}},e[45]=t.type,e[46]=K,e[47]=a):a=e[47],U=Me({all:n("general.All"),interactive:n("session.Interactive"),batch:n("session.Batch"),inference:n("session.Inference"),system:n("session.System")},a),e[41]=t.type,e[42]=K,e[43]=n,e[44]=U}else U=e[44];let q;e[48]!==t.type||e[49]!==$||e[50]!==U?(q=s.jsx(Bn,{activeKey:nn,onChange:$,items:U}),e[48]=t.type,e[49]=$,e[50]=U,e[51]=q):q=e[51];let be;e[52]===Symbol.for("react.memo_cache_sentinel")?(be={flexShrink:1},e[52]=be):be=e[52];const tn=t.statusCategory;let G;e[53]!==m||e[54]!==f?(G=a=>{m({statusCategory:a.target.value}),f({current:1}),p([])},e[53]=m,e[54]=f,e[55]=G):G=e[55];let Q;e[56]!==n?(Q=n("session.Running"),e[56]=n,e[57]=Q):Q=e[57];let z;e[58]!==Q?(z={label:Q,value:"running"},e[58]=Q,e[59]=z):z=e[59];let H;e[60]!==n?(H=n("session.Finished"),e[60]=n,e[61]=H):H=e[61];let W;e[62]!==H?(W={label:H,value:"finished"},e[62]=H,e[63]=W):W=e[63];let Y;e[64]!==z||e[65]!==W?(Y=[z,W],e[64]=z,e[65]=W,e[66]=Y):Y=e[66];let Z;e[67]!==t.statusCategory||e[68]!==G||e[69]!==Y?(Z=s.jsx(Dn,{optionType:"button",value:tn,onChange:G,options:Y}),e[67]=t.statusCategory,e[68]=G,e[69]=Y,e[70]=Z):Z=e[70];let J;e[71]!==n?(J=vn([{key:"id",propertyLabel:n("session.SessionId"),type:"uuid"},{key:"project_id",propertyLabel:n("data.Project"),type:"string",defaultOperator:"==",renderInput:a=>{const{onAddCondition:o,value:j,isDisabled:je}=a;return s.jsx(qn,{label:n("data.Project"),isLabelHidden:!0,value:j,isDisabled:je,onChange:(Ie,an)=>{var Oe;o(Ie,(Oe=hn(an??[])[0])==null?void 0:Oe.label)}})}},{key:"name",propertyLabel:n("session.SessionName"),type:"string"},{key:"scaling_group",propertyLabel:n("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:n("session.Agent"),type:"string"},{key:"user_email",propertyLabel:n("session.launcher.OwnerEmail"),type:"string"},{key:"full_name",propertyLabel:n("credential.FullName"),type:"string"},{key:"group_name",propertyLabel:n("session.ProjectName"),type:"string"},{key:"domain_name",propertyLabel:n("session.Domain"),type:"string"},{key:"access_key",propertyLabel:n("general.AccessKey"),type:"string"},{key:"images",propertyLabel:n("session.launcher.Environments"),type:"string"},{key:"status_info",propertyLabel:n("session.StatusInfo"),type:"string"},{key:"result",propertyLabel:n("session.Result"),type:"string",strictSelection:!0,defaultOperator:"==",options:Me(Yn,Jn)},{key:"cluster_mode",propertyLabel:n("session.ClusterMode"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:n("session.launcher.SingleNode"),value:"single-node"},{label:n("session.launcher.MultiNode"),value:"multi-node"}]},{key:"priority",propertyLabel:n("session.Priority"),type:"number"},{key:"created_at",propertyLabel:n("session.CreatedAt"),type:"datetime"},{key:"terminated_at",propertyLabel:n("session.TerminatedAt"),type:"datetime"}]),e[71]=n,e[72]=J):J=e[72];const Pe=t.filter||void 0;let X;e[73]!==m||e[74]!==f?(X=a=>{m({filter:a||""}),f({current:1}),p([])},e[73]=m,e[74]=f,e[75]=X):X=e[75];let ee;e[76]!==J||e[77]!==Pe||e[78]!==X?(ee=s.jsx(On,{filterProperties:J,value:Pe,onChange:X}),e[76]=J,e[77]=Pe,e[78]=X,e[79]=ee):ee=e[79];let ne;e[80]!==Z||e[81]!==ee?(ne=s.jsxs(pe,{gap:"sm",align:"start",style:be,wrap:"wrap",children:[Z,ee]}),e[80]=Z,e[81]=ee,e[82]=ne):ne=e[82];let te;e[83]!==u.length||e[84]!==n?(te=u.length>0&&s.jsxs(s.Fragment,{children:[s.jsx(Ln,{count:u.length,onClearSelection:()=>p([])}),s.jsx(bn,{label:n("session.TerminateSession"),tooltip:n("session.TerminateSession"),icon:s.jsx(Nn,{color:"var(--color-error)"}),onClick:()=>{N(!0)}})]}),e[83]=u.length,e[84]=n,e[85]=te):te=e[85];let ae;e[86]!==k||e[87]!==t.view||e[88]!==m||e[89]!==n?(ae=k&&s.jsxs(An,{label:n("session.resourceGrid.ViewMode"),value:t.view,onChange:a=>m({view:a}),children:[s.jsx(Ge,{content:n("session.resourceGrid.TableView"),children:s.jsx(Qe,{value:"table",label:n("session.resourceGrid.TableView"),isLabelHidden:!0,icon:s.jsx(In,{size:"1em"})})}),s.jsx(Ge,{content:n("session.resourceGrid.GridView"),children:s.jsx(Qe,{value:"grid",label:n("session.resourceGrid.GridView"),isLabelHidden:!0,icon:s.jsx(Tn,{size:"1em"})})})]}),e[86]=k,e[87]=t.view,e[88]=m,e[89]=n,e[90]=ae):ae=e[90];const xe=ge!==P||I!==me;let se;e[91]!==Ke?(se=a=>{Ke(a)},e[91]=Ke,e[92]=se):se=e[92];let le;e[93]!==me||e[94]!==xe||e[95]!==se?(le=s.jsx($n,{settingId:"admin-session-list",defaultAutoUpdateDelay:15e3,loading:xe,value:me,onChange:se}),e[93]=me,e[94]=xe,e[95]=se,e[96]=le):le=e[96];let ie;e[97]!==te||e[98]!==ae||e[99]!==le?(ie=s.jsxs(pe,{gap:"xs",children:[te,ae,le]}),e[97]=te,e[98]=ae,e[99]=le,e[100]=ie):ie=e[100];let re;e[101]!==ne||e[102]!==ie?(re=s.jsxs(pe,{justify:"between",wrap:"wrap",gap:"sm",children:[ne,ie]}),e[101]=ne,e[102]=ie,e[103]=re):re=e[103];let oe;e[104]!==l||e[105]!==C||e[106]!==T.ok||e[107]!==(d==null?void 0:d.count)||e[108]!==(d==null?void 0:d.edges)||e[109]!==I||e[110]!==ge||e[111]!==k||e[112]!==V||e[113]!==ve||e[114]!==x||e[115]!==F||e[116]!==r||e[117]!==y||e[118]!==t.filter||e[119]!==t.order||e[120]!==t.statusCategory||e[121]!==t.type||e[122]!==t.view||e[123]!==P||e[124]!==u||e[125]!==v||e[126]!==m||e[127]!==f||e[128]!==w||e[129]!==n||e[130]!==S||e[131]!==i||e[132]!==g?(oe=k&&t.view==="grid"?s.jsx(M.Suspense,{fallback:s.jsx(wn,{}),children:s.jsx(Kn,{filter:ve,projectId:x,order:P.order??void 0,fetchKey:I,onClickSession:a=>{const o=new URLSearchParams(F.search);o.set("sessionDetail",a),g({pathname:F.pathname,hash:F.hash,search:o.toString()})}})},`${ve??""}:${x??""}:${P.order??""}`):T.ok?s.jsx(Rn,{order:t.order,onClickSessionName:a=>{const o=new URLSearchParams(F.search);o.set("sessionDetail",a.row_id),g({pathname:F.pathname,hash:F.hash,search:o.toString()},{state:{sessionDetailDrawerFrgmt:a,createdAt:new Date().toISOString()}})},loading:ge!==P,rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(a){return{disabled:Je(a.status)}},onChange:a=>{xn(a,He(d==null?void 0:d.edges.map(Xn)),p)},selectedRowKeys:Me(u,et)},sessionsFrgmt:He(d==null?void 0:d.edges.map(nt)),pagination:{pageSize:S.pageSize,current:S.current,total:(d==null?void 0:d.count)??0,onChange:(a,o)=>{ze(a)&&ze(o)&&f({current:a,pageSize:o})}},onChangeOrder:a=>{m({order:a})},tableSettings:{columnOverrides:C,defaultColumnOverrides:{sessionId:{hidden:!1},environment:{hidden:!1},resourceGroup:{hidden:!1},type:{hidden:!1},cluster_mode:{hidden:!1},created_at:{hidden:!1},project_id:{hidden:!1},...t.statusCategory==="finished"?{terminated_at:{hidden:!1}}:{}},onColumnOverridesChange:v},exportSettings:!En(w)&&(i==="superadmin"||i==="admin")?{supportedFields:w,onExport:async a=>{const o={};t.statusCategory==="finished"?o.status=["TERMINATED","CANCELLED"]:o.status=["PENDING","SCHEDULED","PREPARING","PREPARED","CREATING","PULLING","RESTARTING","RUNNING","TERMINATING","ERROR"],t.type&&t.type!=="all"&&(o.session_type=[t.type]),Pn(o,Hn(t.filter,{supportsUserFilter:l.supports("session-export-user-filter")})),await V(a,o).catch(j=>{y.error(n("general.ErrorOccurred")),r.error(j)})}}:void 0}):s.jsx(jn,{status:"error",title:n("error.FailedToLoadTableData")}),e[104]=l,e[105]=C,e[106]=T.ok,e[107]=d==null?void 0:d.count,e[108]=d==null?void 0:d.edges,e[109]=I,e[110]=ge,e[111]=k,e[112]=V,e[113]=ve,e[114]=x,e[115]=F,e[116]=r,e[117]=y,e[118]=t.filter,e[119]=t.order,e[120]=t.statusCategory,e[121]=t.type,e[122]=t.view,e[123]=P,e[124]=u,e[125]=v,e[126]=m,e[127]=f,e[128]=w,e[129]=n,e[130]=S,e[131]=i,e[132]=g,e[133]=oe):oe=e[133];let de;e[134]!==re||e[135]!==oe?(de=s.jsxs(pe,{direction:"column",align:"stretch",gap:"sm",children:[re,oe]}),e[134]=re,e[135]=oe,e[136]=de):de=e[136];let Ne;e[137]===Symbol.for("react.memo_cache_sentinel")?(Ne=a=>{N(!1),a&&p([])},e[137]=Ne):Ne=e[137];let ue;e[138]!==c||e[139]!==u?(ue=s.jsx(Un,{open:c,sessionFrgmts:u,onRequestClose:Ne}),e[138]=c,e[139]=u,e[140]=ue):ue=e[140];let Ae;return e[141]!==q||e[142]!==de||e[143]!==ue?(Ae=s.jsxs(pe,{direction:"column",align:"stretch",gap:"sm",children:[q,de,ue]}),e[141]=q,e[142]=de,e[143]=ue,e[144]=Ae):Ae=e[144],Ae};function Zn(e){return e==="TERMINATED"||e==="CANCELLED"}function Jn(e){return{label:e,value:e}}function Xn(e){return e==null?void 0:e.node}function et(e){return e.id}function nt(e){return e==null?void 0:e.node}export{st as default};
//# sourceMappingURL=AdminComputeSessionListPage-B4Dompuo.js.map
