import{i as Je,a_ as Ze,u as en,X as nn,x as an,Y as tn,ac as sn,l as M,a7 as Ve,eT as ln,bE as rn,c8 as Te,af as on,i3 as dn,ae as un,aq as Be,aN as cn,e3 as De,r as mn,al as Oe,ah as gn,j as s,df as pn,c9 as fn,K as Sn,hR as yn,br as Fn,q as $e,bq as qe,i4 as kn,cc as Cn,aZ as _n,i5 as vn,aX as hn,am as Ln,bL as Ge,aS as Ue,ew as Nn,v as An,bg as Kn,i6 as Tn,aa as bn,cC as In,b0 as wn,c as fe,cz as Rn,i7 as En}from"./index-DPebpL40.js";import{B as Pn}from"./BAIAdminProjectSelect-N8l8_IVM.js";const Qe=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},d={defaultValue:null,kind:"LocalArgument",name:"filterForAllCount"},a={defaultValue:null,kind:"LocalArgument",name:"filterForBatchCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForInferenceCount"},p={defaultValue:null,kind:"LocalArgument",name:"filterForInteractiveCount"},u={defaultValue:null,kind:"LocalArgument",name:"filterForSystemCount"},c={defaultValue:20,kind:"LocalArgument",name:"first"},w={defaultValue:0,kind:"LocalArgument",name:"offset"},f={defaultValue:null,kind:"LocalArgument",name:"order"},k=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],y={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},_={kind:"Literal",name:"first",value:0},S={kind:"Literal",name:"offset",value:0},F=[C],V={alias:"all",args:[{kind:"Variable",name:"filter",variableName:"filterForAllCount"},_,S],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},R={alias:"interactive",args:[{kind:"Variable",name:"filter",variableName:"filterForInteractiveCount"},_,S],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},v={alias:"inference",args:[{kind:"Variable",name:"filter",variableName:"filterForInferenceCount"},_,S],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},g={alias:"batch",args:[{kind:"Variable",name:"filter",variableName:"filterForBatchCount"},_,S],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},m={alias:"system",args:[{kind:"Variable",name:"filter",variableName:"filterForSystemCount"},_,S],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:F,storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},ye={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},L=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],N={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},E=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,h,A,K],storageKey:null}],storageKey:null},C];return{fragment:{argumentDefinitions:[e,d,a,r,p,u,c,w,f],kind:"Fragment",metadata:null,name:"AdminComputeSessionListPageQuery",selections:[{kind:"CatchField",field:{alias:"computeSessionNodeResult",args:k,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:y,action:"THROW"},{kind:"RequiredField",field:A,action:"THROW"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},C],storageKey:null},to:"RESULT"},V,R,v,g,m],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[c,w,e,f,d,p,r,a,u],kind:"Operation",name:"AdminComputeSessionListPageQuery",selections:[{alias:"computeSessionNodeResult",args:k,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,A,h,K,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},n,o,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},ye,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},y,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},A,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:L,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:L,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},ye,y],storageKey:null},h,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},K,o,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},N,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},y],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[h,A,y],storageKey:null}],storageKey:null},C],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},N,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:E,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:E,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},n,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null},C],storageKey:null},V,R,v,g,m]},params:{cacheID:"d37cace9dd11a5cc8108fec4639e0307",id:null,metadata:{},name:"AdminComputeSessionListPageQuery",operationKind:"query",text:`query AdminComputeSessionListPageQuery(
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

fragment ImageNodeSimpleTagFragment on ImageNode {
  base_image_name
  version
  architecture
  name
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
          ...ImageNodeSimpleTagFragment
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
          ...ImageNodeSimpleTagFragment
          id
        }
        id
      }
    }
  }
  created_at
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
`}}})();Qe.hash="7c8dbadc30e34da0dc4a5dd7f6c4a230";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Lifts a project condition out of the admin session filter for the grid's
 legacy `compute_session_list` query, which has no `project_id` queryfilter
 field but does take a `group_id` argument (FR-3571).
 */const jn=e=>{const d=[];let a=0,r=!1,p="";for(const u of e)u==='"'?r=!r:!r&&u==="("?a+=1:!r&&u===")"&&(a-=1),u==="&"&&a===0&&!r?(d.push(p),p=""):p+=u;return d.push(p),d.map(u=>u.trim()).filter(Boolean)},xn=e=>{let d=0,a=!1;for(const r of e)if(r==='"')a=!a;else if(!a&&r==="(")d+=1;else if(!a&&r===")")d-=1;else if(r==="|"&&d===0&&!a)return!0;return!1},xe=/^\(*\s*project_id\s*(?:==|ilike)\s*"%?([^"%]+)%?"\s*\)*$/,Mn=e=>{var u;const d={projectId:void 0,remainder:e||void 0};if(!e||xn(e))return d;const a=jn(e),r=a.filter(c=>xe.test(c));if(r.length!==1)return d;const p=a.filter(c=>!xe.test(c));return{projectId:(u=xe.exec(r[0]))==null?void 0:u[1],remainder:p.join("&")||void 0}},Vn=["all","interactive","batch","inference","system"],ce='status != "TERMINATED" & status != "CANCELLED"',Se={all:ce,interactive:`${ce} & type == "interactive"`,inference:`${ce} & type == "inference"`,batch:`${ce} & type == "batch"`,system:`${ce} & type == "system"`},Un=()=>{"use memo";const e=Je.c(143),d=Ze(),{t:a}=en(),{message:r}=nn.useApp(),{logger:p}=an(),u=tn(),c=sn();let w;e[0]===Symbol.for("react.memo_cache_sentinel")?(w=[],e[0]=w):w=e[0];const[f,k]=M.useState(w),[y,A]=M.useState(!1),[C,_]=Ve("table_column_overrides.AdminComputeSessionListPage"),[S]=Ve("experimental_session_resource_grid"),{supportedFields:F,exportCSV:V}=ln("sessions");let R;e[1]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[1]=R):R=e[1];const{baiPaginationOption:v,tablePaginationOption:g,setTablePaginationOption:m}=rn(R);let h,K;e[2]===Symbol.for("react.memo_cache_sentinel")?(h={order:Te(dn),filter:on.withDefault(""),type:Te(Vn).withDefault("all"),statusCategory:Te(["running","finished"]).withDefault("running"),view:Te(["table","grid"]).withDefault("table")},K={history:"replace"},e[2]=h,e[3]=K):(h=e[2],K=e[3]);const[n,o]=un(h,K),ye=n.type;let L;e[4]!==n?(L=Be(n,["view"]),e[4]=n,e[5]=L):L=e[5];let N;e[6]!==L||e[7]!==g?(N={queryParams:L,tablePaginationOption:g},e[6]=L,e[7]=g,e[8]=N):N=e[8];let E;e[9]!==n.type||e[10]!==N?(E={[ye]:N},e[9]=n.type,e[10]=N,e[11]=E):E=e[11];const Me=M.useRef(E);let Fe,ke;e[12]!==n||e[13]!==g?(Fe=()=>{Me.current[n.type]={queryParams:Be(n,["view"]),tablePaginationOption:g}},ke=[n,g],e[12]=n,e[13]=g,e[14]=Fe,e[15]=ke):(Fe=e[14],ke=e[15]),M.useEffect(Fe,ke);const B=n.type==="all"||n.type===void 0?void 0:`type == "${n.type}"`,D=n.statusCategory==="running"||n.statusCategory===void 0?ce:'status == "TERMINATED" | status == "CANCELLED"',ze=Bn,[me,be]=cn(),He=v.offset,We=v.first;let O;e[16]!==n.filter||e[17]!==D||e[18]!==B?(O=De([D,n.filter,B]),e[16]=n.filter,e[17]=D,e[18]=B,e[19]=O):O=e[19];const Ie=n.order||"-created_at";let Ce;e[20]!==v.first||e[21]!==v.offset||e[22]!==O||e[23]!==Ie?(Ce={offset:He,first:We,filter:O,order:Ie,filterForAllCount:Se.all,filterForInteractiveCount:Se.interactive,filterForInferenceCount:Se.inference,filterForBatchCount:Se.batch,filterForSystemCount:Se.system},e[20]=v.first,e[21]=v.offset,e[22]=O,e[23]=Ie,e[24]=Ce):Ce=e[24];const P=Ce;let j,_e;if(e[25]!==n.filter||e[26]!==D||e[27]!==B){const{projectId:t,remainder:l}=Mn(n.filter??"");j=t,_e=De([D,l,B]),e[25]=n.filter,e[26]=D,e[27]=B,e[28]=j,e[29]=_e}else j=e[28],_e=e[29];const ve=_e,ge=M.useDeferredValue(P),T=M.useDeferredValue(me);let he;e[30]===Symbol.for("react.memo_cache_sentinel")?(he=Qe,e[30]=he):he=e[30];const we=T===Kn?"store-and-network":"network-only";let Le;e[31]!==T||e[32]!==we?(Le={fetchPolicy:we,fetchKey:T},e[31]=T,e[32]=we,e[33]=Le):Le=e[33];const Re=mn.useLazyLoadQuery(he,ge,Le);let b,I;e[34]!==Re?({computeSessionNodeResult:b,...I}=Re,e[34]=Re,e[35]=b,e[36]=I):(b=e[35],I=e[36]);const i=b.ok?b.value:null,Xe=n.type;let $;e[37]!==n.view||e[38]!==o||e[39]!==m?($=t=>{const l=Me.current[t]||{queryParams:{statusCategory:"running"}};o(null),o({...l.queryParams,type:t,view:n.view}),m(l.tablePaginationOption||{current:1}),k([])},e[37]=n.view,e[38]=o,e[39]=m,e[40]=$):$=e[40];let q;if(e[41]!==n.type||e[42]!==I||e[43]!==a){let t;e[45]!==n.type||e[46]!==I?(t=(l,x)=>{var pe;const je=((pe=I[x])==null?void 0:pe.count)??0;return{key:x,label:l,endContent:s.jsx(Tn,{count:je,selected:n.type===x})}},e[45]=n.type,e[46]=I,e[47]=t):t=e[47],q=Oe({all:a("general.All"),interactive:a("session.Interactive"),batch:a("session.Batch"),inference:a("session.Inference"),system:a("session.System")},t),e[41]=n.type,e[42]=I,e[43]=a,e[44]=q}else q=e[44];let G;e[48]!==n.type||e[49]!==$||e[50]!==q?(G=s.jsx(bn,{activeKey:Xe,onChange:$,items:q}),e[48]=n.type,e[49]=$,e[50]=q,e[51]=G):G=e[51];let Ne;e[52]===Symbol.for("react.memo_cache_sentinel")?(Ne={flexShrink:1},e[52]=Ne):Ne=e[52];const Ye=n.statusCategory;let U;e[53]!==o||e[54]!==m?(U=t=>{o({statusCategory:t.target.value}),m({current:1}),k([])},e[53]=o,e[54]=m,e[55]=U):U=e[55];let Q;e[56]!==a?(Q=a("session.Running"),e[56]=a,e[57]=Q):Q=e[57];let z;e[58]!==Q?(z={label:Q,value:"running"},e[58]=Q,e[59]=z):z=e[59];let H;e[60]!==a?(H=a("session.Finished"),e[60]=a,e[61]=H):H=e[61];let W;e[62]!==H?(W={label:H,value:"finished"},e[62]=H,e[63]=W):W=e[63];let X;e[64]!==z||e[65]!==W?(X=[z,W],e[64]=z,e[65]=W,e[66]=X):X=e[66];let Y;e[67]!==n.statusCategory||e[68]!==U||e[69]!==X?(Y=s.jsx(In,{optionType:"button",value:Ye,onChange:U,options:X}),e[67]=n.statusCategory,e[68]=U,e[69]=X,e[70]=Y):Y=e[70];let J;e[71]!==a?(J=gn([{key:"project_id",propertyLabel:a("data.Project"),type:"string",defaultOperator:"==",renderInput:t=>{const{onAddCondition:l}=t;return s.jsx(Pn,{label:a("data.Project"),isLabelHidden:!0,value:null,width:200,onChange:(x,je)=>{var pe;l(x,(pe=pn(je??[])[0])==null?void 0:pe.label)}})}},{key:"name",propertyLabel:a("session.SessionName"),type:"string"},{key:"scaling_group",propertyLabel:a("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:a("session.Agent"),type:"string"},{key:"user_email",propertyLabel:a("session.launcher.OwnerEmail"),type:"string"}]),e[71]=a,e[72]=J):J=e[72];const Ee=n.filter||void 0;let Z;e[73]!==o||e[74]!==m?(Z=t=>{o({filter:t||""}),m({current:1}),k([])},e[73]=o,e[74]=m,e[75]=Z):Z=e[75];let ee;e[76]!==J||e[77]!==Ee||e[78]!==Z?(ee=s.jsx(wn,{filterProperties:J,value:Ee,onChange:Z}),e[76]=J,e[77]=Ee,e[78]=Z,e[79]=ee):ee=e[79];let ne;e[80]!==Y||e[81]!==ee?(ne=s.jsxs(fe,{gap:"sm",align:"start",style:Ne,wrap:"wrap",children:[Y,ee]}),e[80]=Y,e[81]=ee,e[82]=ne):ne=e[82];let ae;e[83]!==f.length||e[84]!==a?(ae=f.length>0&&s.jsxs(s.Fragment,{children:[s.jsx(fn,{count:f.length,onClearSelection:()=>k([])}),s.jsx(Sn,{label:a("session.TerminateSession"),tooltip:a("session.TerminateSession"),icon:s.jsx(yn,{color:"var(--color-error)"}),onClick:()=>{A(!0)}})]}),e[83]=f.length,e[84]=a,e[85]=ae):ae=e[85];let te;e[86]!==S||e[87]!==n.view||e[88]!==o||e[89]!==a?(te=S&&s.jsxs(Fn,{label:a("session.resourceGrid.ViewMode"),value:n.view,onChange:t=>o({view:t}),children:[s.jsx($e,{content:a("session.resourceGrid.TableView"),children:s.jsx(qe,{value:"table",label:a("session.resourceGrid.TableView"),isLabelHidden:!0,icon:s.jsx(kn,{size:"1em"})})}),s.jsx($e,{content:a("session.resourceGrid.GridView"),children:s.jsx(qe,{value:"grid",label:a("session.resourceGrid.GridView"),isLabelHidden:!0,icon:s.jsx(Cn,{size:"1em"})})})]}),e[86]=S,e[87]=n.view,e[88]=o,e[89]=a,e[90]=te):te=e[90];const Pe=ge!==P||T!==me;let se;e[91]!==be?(se=t=>{be(t)},e[91]=be,e[92]=se):se=e[92];let le;e[93]!==me||e[94]!==Pe||e[95]!==se?(le=s.jsx(Rn,{settingId:"admin-session-list",defaultAutoUpdateDelay:15e3,loading:Pe,value:me,onChange:se}),e[93]=me,e[94]=Pe,e[95]=se,e[96]=le):le=e[96];let ie;e[97]!==ae||e[98]!==te||e[99]!==le?(ie=s.jsxs(fe,{gap:"xs",children:[ae,te,le]}),e[97]=ae,e[98]=te,e[99]=le,e[100]=ie):ie=e[100];let re;e[101]!==ne||e[102]!==ie?(re=s.jsxs(fe,{justify:"between",wrap:"wrap",gap:"sm",children:[ne,ie]}),e[101]=ne,e[102]=ie,e[103]=re):re=e[103];let oe;e[104]!==C||e[105]!==b.ok||e[106]!==(i==null?void 0:i.count)||e[107]!==(i==null?void 0:i.edges)||e[108]!==T||e[109]!==ge||e[110]!==S||e[111]!==V||e[112]!==ve||e[113]!==j||e[114]!==c||e[115]!==p||e[116]!==r||e[117]!==n.order||e[118]!==n.statusCategory||e[119]!==n.type||e[120]!==n.view||e[121]!==P||e[122]!==f||e[123]!==_||e[124]!==o||e[125]!==m||e[126]!==F||e[127]!==a||e[128]!==g||e[129]!==d||e[130]!==u?(oe=S&&n.view==="grid"?s.jsx(M.Suspense,{fallback:s.jsx(vn,{}),children:s.jsx(_n,{filter:ve,projectId:j,order:P.order??void 0,fetchKey:T,onClickSession:t=>{const l=new URLSearchParams(c.search);l.set("sessionDetail",t),u({pathname:c.pathname,hash:c.hash,search:l.toString()})}})},`${ve??""}:${j??""}:${P.order??""}`):b.ok?s.jsx(hn,{order:n.order,onClickSessionName:t=>{const l=new URLSearchParams(c.search);l.set("sessionDetail",t.row_id),u({pathname:c.pathname,hash:c.hash,search:l.toString()},{state:{sessionDetailDrawerFrgmt:t,createdAt:new Date().toISOString()}})},loading:ge!==P,rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(t){return{disabled:ze(t.status)}},onChange:t=>{Nn(t,Ue(i==null?void 0:i.edges.map(Dn)),k)},selectedRowKeys:Oe(f,On)},sessionsFrgmt:Ue(i==null?void 0:i.edges.map($n)),pagination:{pageSize:g.pageSize,current:g.current,total:(i==null?void 0:i.count)??0,onChange:(t,l)=>{Ge(t)&&Ge(l)&&m({current:t,pageSize:l})}},onChangeOrder:t=>{o({order:t})},tableSettings:{columnOverrides:C,defaultColumnOverrides:{environment:{hidden:!1},resourceGroup:{hidden:!1},type:{hidden:!1},cluster_mode:{hidden:!1},created_at:{hidden:!1},project_id:{hidden:!1}},onColumnOverridesChange:_},exportSettings:!Ln(F)&&(d==="superadmin"||d==="admin")?{supportedFields:F,onExport:async t=>{const l={};n.statusCategory==="finished"?l.status=["TERMINATED","CANCELLED"]:l.status=["PENDING","SCHEDULED","PREPARING","PREPARED","CREATING","PULLING","RESTARTING","RUNNING","TERMINATING","ERROR"],n.type&&n.type!=="all"&&(l.session_type=[n.type]),await V(t,l).catch(x=>{r.error(a("general.ErrorOccurred")),p.error(x)})}}:void 0}):s.jsx(An,{status:"error",title:a("error.FailedToLoadTableData")}),e[104]=C,e[105]=b.ok,e[106]=i==null?void 0:i.count,e[107]=i==null?void 0:i.edges,e[108]=T,e[109]=ge,e[110]=S,e[111]=V,e[112]=ve,e[113]=j,e[114]=c,e[115]=p,e[116]=r,e[117]=n.order,e[118]=n.statusCategory,e[119]=n.type,e[120]=n.view,e[121]=P,e[122]=f,e[123]=_,e[124]=o,e[125]=m,e[126]=F,e[127]=a,e[128]=g,e[129]=d,e[130]=u,e[131]=oe):oe=e[131];let de;e[132]!==re||e[133]!==oe?(de=s.jsxs(fe,{direction:"column",align:"stretch",gap:"sm",children:[re,oe]}),e[132]=re,e[133]=oe,e[134]=de):de=e[134];let Ae;e[135]===Symbol.for("react.memo_cache_sentinel")?(Ae=t=>{A(!1),t&&k([])},e[135]=Ae):Ae=e[135];let ue;e[136]!==y||e[137]!==f?(ue=s.jsx(En,{open:y,sessionFrgmts:f,onRequestClose:Ae}),e[136]=y,e[137]=f,e[138]=ue):ue=e[138];let Ke;return e[139]!==G||e[140]!==de||e[141]!==ue?(Ke=s.jsxs(fe,{direction:"column",align:"stretch",gap:"sm",children:[G,de,ue]}),e[139]=G,e[140]=de,e[141]=ue,e[142]=Ke):Ke=e[142],Ke};function Bn(e){return e==="TERMINATED"||e==="CANCELLED"}function Dn(e){return e==null?void 0:e.node}function On(e){return e.id}function $n(e){return e==null?void 0:e.node}export{Un as default};
//# sourceMappingURL=AdminComputeSessionListPage-8MyVqpSd.js.map
