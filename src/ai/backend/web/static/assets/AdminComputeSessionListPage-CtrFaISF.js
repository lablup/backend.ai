import{bj as an,bF as sn,i as ln,a$ as rn,u as on,W as dn,x as un,X as cn,ac as mn,l as P,a7 as Oe,fh as gn,bJ as pn,ce as Ie,ao as fn,ae as yn,aq as $e,aM as Sn,dY as qe,r as Fn,ak as xe,ag as kn,j as l,dz as _n,cf as Cn,J as hn,h_ as vn,bw as Ln,q as Ue,bv as Ge,dZ as bn,cj as Nn,a_ as An,d_ as In,aY as Kn,al as Tn,c0 as wn,bQ as Qe,aT as ze,eO as Rn,v as En,bk as jn,iL as Pn,aa as xn,dj as Mn,b1 as Bn,c as ge,dJ as Vn,iM as Dn,iN as On}from"./index-4XAoWQdC.js";import{B as $n}from"./BAIAdminProjectSelect-oLGLqaw6.js";const He=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},s={defaultValue:null,kind:"LocalArgument",name:"filterForAllCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForBatchCount"},i={defaultValue:null,kind:"LocalArgument",name:"filterForInferenceCount"},u={defaultValue:null,kind:"LocalArgument",name:"filterForInteractiveCount"},r={defaultValue:null,kind:"LocalArgument",name:"filterForSystemCount"},p={defaultValue:20,kind:"LocalArgument",name:"first"},_={defaultValue:0,kind:"LocalArgument",name:"offset"},m={defaultValue:null,kind:"LocalArgument",name:"order"},S=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},h={kind:"Literal",name:"first",value:0},F={kind:"Literal",name:"offset",value:0},k=[C],x={alias:"all",args:[{kind:"Variable",name:"filter",variableName:"filterForAllCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},w={alias:"interactive",args:[{kind:"Variable",name:"filter",variableName:"filterForInteractiveCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},v={alias:"inference",args:[{kind:"Variable",name:"filter",variableName:"filterForInferenceCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},y={alias:"batch",args:[{kind:"Variable",name:"filter",variableName:"filterForBatchCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},f={alias:"system",args:[{kind:"Variable",name:"filter",variableName:"filterForSystemCount"},h,F],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:k,storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},g=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],fe={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},b=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,L,T,N],storageKey:null}],storageKey:null},C];return{fragment:{argumentDefinitions:[e,s,n,i,u,r,p,_,m],kind:"Fragment",metadata:null,name:"AdminComputeSessionListPageQuery",selections:[{kind:"CatchField",field:{alias:"computeSessionNodeResult",args:S,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:o,action:"THROW"},{kind:"RequiredField",field:T,action:"THROW"},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},C],storageKey:null},to:"RESULT"},x,w,v,y,f],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[p,_,e,m,s,u,i,n,r],kind:"Operation",name:"AdminComputeSessionListPageQuery",selections:[{alias:"computeSessionNodeResult",args:S,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,T,L,N,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,N,{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:g,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:g,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},fe,o],storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},fe,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},o],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[L,T,o],storageKey:null}],storageKey:null},C],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:b,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:b,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domain_name",storageKey:null}],storageKey:null}],storageKey:null},C],storageKey:null},x,w,v,y,f]},params:{cacheID:"a2f90974a74cd533199ccf3394caf5b1",id:null,metadata:{},name:"AdminComputeSessionListPageQuery",operationKind:"query",text:`query AdminComputeSessionListPageQuery(
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
 */const We=e=>{const s=[];let n=0,i=!1,u="";for(const r of e)r==='"'?i=!i:!i&&r==="("?n+=1:!i&&r===")"&&(n-=1),r==="&"&&n===0&&!i?(s.push(u),u=""):u+=r;return s.push(u),s.map(r=>r.trim()).filter(Boolean)},Je=e=>{let s=0,n=!1;for(const i of e)if(i==='"')n=!n;else if(!n&&i==="(")s+=1;else if(!n&&i===")")s-=1;else if(i==="|"&&s===0&&!n)return!0;return!1},Me=/^\(*\s*project_id\s*(?:==|ilike)\s*"%?([^"%]+)%?"\s*\)*$/,qn=e=>{var r;const s={projectId:void 0,remainder:e||void 0};if(!e||Je(e))return s;const n=We(e),i=n.filter(p=>Me.test(p));if(i.length!==1)return s;const u=n.filter(p=>!Me.test(p));return{projectId:(r=Me.exec(i[0]))==null?void 0:r[1],remainder:u.join("&")||void 0}};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 Translates the admin session list's queryfilter minilang string into the
 `POST /export/sessions/csv` filter body, so the CSV narrows to the table's
 own conditions wherever the export endpoint can express them (FR-3915).
 Whatever it cannot express is dropped, leaving the CSV a superset — see
 `buildSessionExportFilter` for the conditions that keeps.
 */const Un={name:"name",domain_name:"domain_name",access_key:"access_key"},Gn=/^\(*\s*([a-z_]+)\s*(==|!=|>=|<=|ilike|like)\s*(?:"([^"]*)"|([^\s")]+))\s*\)*$/,Be=(e,s)=>{switch(e){case"==":return{equals:s};case"!=":return{not_equals:s};case"ilike":case"like":return/^%[^%]*%$/.test(s)?{i_contains:s.slice(1,-1)}:void 0;default:return}},Qn=e=>{const s={};return!e||Je(e)||an(We(e),n=>{const i=Gn.exec(n);if(!i)return;const[,u,r,p,_]=i,m=p??_;if(sn(m)||m==="")return;const S=Un[u];if(S){const o=Be(r,m);o&&(s[S]=o);return}if(u==="scaling_group"){const o=Be(r,m);o&&(s.scaling_group_name=o);return}if(u==="user_email"){const o=Be(r,m);o&&(s.user={email:o});return}if(u==="created_at"||u==="terminated_at"){const o=r===">="?"after":r==="<="?"before":void 0;if(!o)return;s[u]={...s[u],[o]:m};return}}),s},zn=["all","interactive","batch","inference","system"],ue='status != "TERMINATED" & status != "CANCELLED"',Hn=["UNDEFINED","SUCCESS","FAILURE"],pe={all:ue,interactive:`${ue} & type == "interactive"`,inference:`${ue} & type == "inference"`,batch:`${ue} & type == "batch"`,system:`${ue} & type == "system"`},tt=()=>{"use memo";const e=ln.c(144),s=rn(),{t:n}=on(),{message:i}=dn.useApp(),{logger:u}=un(),r=cn(),p=mn();let _;e[0]===Symbol.for("react.memo_cache_sentinel")?(_=[],e[0]=_):_=e[0];const[m,S]=P.useState(_),[o,T]=P.useState(!1),[C,h]=Oe("table_column_overrides.AdminComputeSessionListPage"),[F]=Oe("experimental_session_resource_grid"),{supportedFields:k,exportCSV:x}=gn("sessions");let w;e[1]===Symbol.for("react.memo_cache_sentinel")?(w={current:1,pageSize:10},e[1]=w):w=e[1];const{baiPaginationOption:v,tablePaginationOption:y,setTablePaginationOption:f}=pn(w);let L,N;e[2]===Symbol.for("react.memo_cache_sentinel")?(L={order:Ie(On),filter:fn.withDefault(""),type:Ie(zn).withDefault("all"),statusCategory:Ie(["running","finished"]).withDefault("running"),view:Ie(["table","grid"]).withDefault("table")},N={history:"replace"},e[2]=L,e[3]=N):(L=e[2],N=e[3]);const[t,g]=yn(L,N),fe=t.type;let b;e[4]!==t?(b=$e(t,["view"]),e[4]=t,e[5]=b):b=e[5];let M;e[6]!==b||e[7]!==y?(M={queryParams:b,tablePaginationOption:y},e[6]=b,e[7]=y,e[8]=M):M=e[8];let ye;e[9]!==t.type||e[10]!==M?(ye={[fe]:M},e[9]=t.type,e[10]=M,e[11]=ye):ye=e[11];const Ve=P.useRef(ye);let Se,Fe;e[12]!==t||e[13]!==y?(Se=()=>{Ve.current[t.type]={queryParams:$e(t,["view"]),tablePaginationOption:y}},Fe=[t,y],e[12]=t,e[13]=y,e[14]=Se,e[15]=Fe):(Se=e[14],Fe=e[15]),P.useEffect(Se,Fe);const B=t.type==="all"||t.type===void 0?void 0:`type == "${t.type}"`,V=t.statusCategory==="running"||t.statusCategory===void 0?ue:'status == "TERMINATED" | status == "CANCELLED"',Ye=Wn,[ce,Ke]=Sn(),Xe=v.offset,Ze=v.first;let D;e[16]!==t.filter||e[17]!==V||e[18]!==B?(D=qe([V,t.filter,B]),e[16]=t.filter,e[17]=V,e[18]=B,e[19]=D):D=e[19];const Te=t.order||"-created_at";let ke;e[20]!==v.first||e[21]!==v.offset||e[22]!==D||e[23]!==Te?(ke={offset:Xe,first:Ze,filter:D,order:Te,filterForAllCount:pe.all,filterForInteractiveCount:pe.interactive,filterForInferenceCount:pe.inference,filterForBatchCount:pe.batch,filterForSystemCount:pe.system},e[20]=v.first,e[21]=v.offset,e[22]=D,e[23]=Te,e[24]=ke):ke=e[24];const R=ke;let E,_e;if(e[25]!==t.filter||e[26]!==V||e[27]!==B){const{projectId:a,remainder:d}=qn(t.filter??"");E=a,_e=qe([V,d,B]),e[25]=t.filter,e[26]=V,e[27]=B,e[28]=E,e[29]=_e}else E=e[28],_e=e[29];const Ce=_e,me=P.useDeferredValue(R),A=P.useDeferredValue(ce);let he;e[30]===Symbol.for("react.memo_cache_sentinel")?(he=He,e[30]=he):he=e[30];const we=A===jn?"store-and-network":"network-only";let ve;e[31]!==A||e[32]!==we?(ve={fetchPolicy:we,fetchKey:A},e[31]=A,e[32]=we,e[33]=ve):ve=e[33];const Re=Fn.useLazyLoadQuery(he,me,ve);let I,K;e[34]!==Re?({computeSessionNodeResult:I,...K}=Re,e[34]=Re,e[35]=I,e[36]=K):(I=e[35],K=e[36]);const c=I.ok?I.value:null,en=t.type;let O;e[37]!==t.view||e[38]!==g||e[39]!==f?(O=a=>{const d=Ve.current[a]||{queryParams:{statusCategory:"running"}};g(null),g({...d.queryParams,type:a,view:t.view}),f(d.tablePaginationOption||{current:1}),S([])},e[37]=t.view,e[38]=g,e[39]=f,e[40]=O):O=e[40];let $;if(e[41]!==t.type||e[42]!==K||e[43]!==n){let a;e[45]!==t.type||e[46]!==K?(a=(d,j)=>{var Ae;const Pe=((Ae=K[j])==null?void 0:Ae.count)??0;return{key:j,label:d,endContent:l.jsx(Pn,{count:Pe,selected:t.type===j})}},e[45]=t.type,e[46]=K,e[47]=a):a=e[47],$=xe({all:n("general.All"),interactive:n("session.Interactive"),batch:n("session.Batch"),inference:n("session.Inference"),system:n("session.System")},a),e[41]=t.type,e[42]=K,e[43]=n,e[44]=$}else $=e[44];let q;e[48]!==t.type||e[49]!==O||e[50]!==$?(q=l.jsx(xn,{activeKey:en,onChange:O,items:$}),e[48]=t.type,e[49]=O,e[50]=$,e[51]=q):q=e[51];let Le;e[52]===Symbol.for("react.memo_cache_sentinel")?(Le={flexShrink:1},e[52]=Le):Le=e[52];const nn=t.statusCategory;let U;e[53]!==g||e[54]!==f?(U=a=>{g({statusCategory:a.target.value}),f({current:1}),S([])},e[53]=g,e[54]=f,e[55]=U):U=e[55];let G;e[56]!==n?(G=n("session.Running"),e[56]=n,e[57]=G):G=e[57];let Q;e[58]!==G?(Q={label:G,value:"running"},e[58]=G,e[59]=Q):Q=e[59];let z;e[60]!==n?(z=n("session.Finished"),e[60]=n,e[61]=z):z=e[61];let H;e[62]!==z?(H={label:z,value:"finished"},e[62]=z,e[63]=H):H=e[63];let W;e[64]!==Q||e[65]!==H?(W=[Q,H],e[64]=Q,e[65]=H,e[66]=W):W=e[66];let J;e[67]!==t.statusCategory||e[68]!==U||e[69]!==W?(J=l.jsx(Mn,{optionType:"button",value:nn,onChange:U,options:W}),e[67]=t.statusCategory,e[68]=U,e[69]=W,e[70]=J):J=e[70];let Y;e[71]!==n?(Y=kn([{key:"id",propertyLabel:n("session.SessionId"),type:"uuid"},{key:"project_id",propertyLabel:n("data.Project"),type:"string",defaultOperator:"==",renderInput:a=>{const{onAddCondition:d,value:j,isDisabled:Pe}=a;return l.jsx($n,{label:n("data.Project"),isLabelHidden:!0,value:j,isDisabled:Pe,onChange:(Ae,tn)=>{var De;d(Ae,(De=_n(tn??[])[0])==null?void 0:De.label)}})}},{key:"name",propertyLabel:n("session.SessionName"),type:"string"},{key:"scaling_group",propertyLabel:n("session.ResourceGroup"),type:"string"},{key:"agent_ids",propertyLabel:n("session.Agent"),type:"string"},{key:"user_email",propertyLabel:n("session.launcher.OwnerEmail"),type:"string"},{key:"full_name",propertyLabel:n("credential.FullName"),type:"string"},{key:"group_name",propertyLabel:n("session.ProjectName"),type:"string"},{key:"access_key",propertyLabel:n("general.AccessKey"),type:"string"},{key:"images",propertyLabel:n("session.launcher.Environments"),type:"string"},{key:"status_info",propertyLabel:n("session.StatusInfo"),type:"string"},{key:"result",propertyLabel:n("session.Result"),type:"string",strictSelection:!0,defaultOperator:"==",options:xe(Hn,Jn)},{key:"cluster_mode",propertyLabel:n("session.ClusterMode"),type:"string",strictSelection:!0,defaultOperator:"==",options:[{label:n("session.launcher.SingleNode"),value:"single-node"},{label:n("session.launcher.MultiNode"),value:"multi-node"}]},{key:"priority",propertyLabel:n("session.Priority"),type:"number"},{key:"created_at",propertyLabel:n("session.CreatedAt"),type:"datetime"},{key:"terminated_at",propertyLabel:n("session.TerminatedAt"),type:"datetime"}]),e[71]=n,e[72]=Y):Y=e[72];const Ee=t.filter||void 0;let X;e[73]!==g||e[74]!==f?(X=a=>{g({filter:a||""}),f({current:1}),S([])},e[73]=g,e[74]=f,e[75]=X):X=e[75];let Z;e[76]!==Y||e[77]!==Ee||e[78]!==X?(Z=l.jsx(Bn,{filterProperties:Y,value:Ee,onChange:X}),e[76]=Y,e[77]=Ee,e[78]=X,e[79]=Z):Z=e[79];let ee;e[80]!==J||e[81]!==Z?(ee=l.jsxs(ge,{gap:"sm",align:"start",style:Le,wrap:"wrap",children:[J,Z]}),e[80]=J,e[81]=Z,e[82]=ee):ee=e[82];let ne;e[83]!==m.length||e[84]!==n?(ne=m.length>0&&l.jsxs(l.Fragment,{children:[l.jsx(Cn,{count:m.length,onClearSelection:()=>S([])}),l.jsx(hn,{label:n("session.TerminateSession"),tooltip:n("session.TerminateSession"),icon:l.jsx(vn,{color:"var(--color-error)"}),onClick:()=>{T(!0)}})]}),e[83]=m.length,e[84]=n,e[85]=ne):ne=e[85];let te;e[86]!==F||e[87]!==t.view||e[88]!==g||e[89]!==n?(te=F&&l.jsxs(Ln,{label:n("session.resourceGrid.ViewMode"),value:t.view,onChange:a=>g({view:a}),children:[l.jsx(Ue,{content:n("session.resourceGrid.TableView"),children:l.jsx(Ge,{value:"table",label:n("session.resourceGrid.TableView"),isLabelHidden:!0,icon:l.jsx(bn,{size:"1em"})})}),l.jsx(Ue,{content:n("session.resourceGrid.GridView"),children:l.jsx(Ge,{value:"grid",label:n("session.resourceGrid.GridView"),isLabelHidden:!0,icon:l.jsx(Nn,{size:"1em"})})})]}),e[86]=F,e[87]=t.view,e[88]=g,e[89]=n,e[90]=te):te=e[90];const je=me!==R||A!==ce;let ae;e[91]!==Ke?(ae=a=>{Ke(a)},e[91]=Ke,e[92]=ae):ae=e[92];let se;e[93]!==ce||e[94]!==je||e[95]!==ae?(se=l.jsx(Vn,{settingId:"admin-session-list",defaultAutoUpdateDelay:15e3,loading:je,value:ce,onChange:ae}),e[93]=ce,e[94]=je,e[95]=ae,e[96]=se):se=e[96];let le;e[97]!==ne||e[98]!==te||e[99]!==se?(le=l.jsxs(ge,{gap:"xs",children:[ne,te,se]}),e[97]=ne,e[98]=te,e[99]=se,e[100]=le):le=e[100];let re;e[101]!==ee||e[102]!==le?(re=l.jsxs(ge,{justify:"between",wrap:"wrap",gap:"sm",children:[ee,le]}),e[101]=ee,e[102]=le,e[103]=re):re=e[103];let ie;e[104]!==C||e[105]!==I.ok||e[106]!==(c==null?void 0:c.count)||e[107]!==(c==null?void 0:c.edges)||e[108]!==A||e[109]!==me||e[110]!==F||e[111]!==x||e[112]!==Ce||e[113]!==E||e[114]!==p||e[115]!==u||e[116]!==i||e[117]!==t.filter||e[118]!==t.order||e[119]!==t.statusCategory||e[120]!==t.type||e[121]!==t.view||e[122]!==R||e[123]!==m||e[124]!==h||e[125]!==g||e[126]!==f||e[127]!==k||e[128]!==n||e[129]!==y||e[130]!==s||e[131]!==r?(ie=F&&t.view==="grid"?l.jsx(P.Suspense,{fallback:l.jsx(In,{}),children:l.jsx(An,{filter:Ce,projectId:E,order:R.order??void 0,fetchKey:A,onClickSession:a=>{const d=new URLSearchParams(p.search);d.set("sessionDetail",a),r({pathname:p.pathname,hash:p.hash,search:d.toString()})}})},`${Ce??""}:${E??""}:${R.order??""}`):I.ok?l.jsx(Kn,{order:t.order,onClickSessionName:a=>{const d=new URLSearchParams(p.search);d.set("sessionDetail",a.row_id),r({pathname:p.pathname,hash:p.hash,search:d.toString()},{state:{sessionDetailDrawerFrgmt:a,createdAt:new Date().toISOString()}})},loading:me!==R,rowSelection:{type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(a){return{disabled:Ye(a.status)}},onChange:a=>{Rn(a,ze(c==null?void 0:c.edges.map(Yn)),S)},selectedRowKeys:xe(m,Xn)},sessionsFrgmt:ze(c==null?void 0:c.edges.map(Zn)),pagination:{pageSize:y.pageSize,current:y.current,total:(c==null?void 0:c.count)??0,onChange:(a,d)=>{Qe(a)&&Qe(d)&&f({current:a,pageSize:d})}},onChangeOrder:a=>{g({order:a})},tableSettings:{columnOverrides:C,defaultColumnOverrides:{sessionId:{hidden:!1},environment:{hidden:!1},resourceGroup:{hidden:!1},type:{hidden:!1},cluster_mode:{hidden:!1},created_at:{hidden:!1},project_id:{hidden:!1},...t.statusCategory==="finished"?{terminated_at:{hidden:!1}}:{}},onColumnOverridesChange:h},exportSettings:!Tn(k)&&(s==="superadmin"||s==="admin")?{supportedFields:k,onExport:async a=>{const d={};t.statusCategory==="finished"?d.status=["TERMINATED","CANCELLED"]:d.status=["PENDING","SCHEDULED","PREPARING","PREPARED","CREATING","PULLING","RESTARTING","RUNNING","TERMINATING","ERROR"],t.type&&t.type!=="all"&&(d.session_type=[t.type]),wn(d,Qn(t.filter)),await x(a,d).catch(j=>{i.error(n("general.ErrorOccurred")),u.error(j)})}}:void 0}):l.jsx(En,{role:"alert",status:"error",title:n("error.FailedToLoadTableData")}),e[104]=C,e[105]=I.ok,e[106]=c==null?void 0:c.count,e[107]=c==null?void 0:c.edges,e[108]=A,e[109]=me,e[110]=F,e[111]=x,e[112]=Ce,e[113]=E,e[114]=p,e[115]=u,e[116]=i,e[117]=t.filter,e[118]=t.order,e[119]=t.statusCategory,e[120]=t.type,e[121]=t.view,e[122]=R,e[123]=m,e[124]=h,e[125]=g,e[126]=f,e[127]=k,e[128]=n,e[129]=y,e[130]=s,e[131]=r,e[132]=ie):ie=e[132];let oe;e[133]!==re||e[134]!==ie?(oe=l.jsxs(ge,{direction:"column",align:"stretch",gap:"sm",children:[re,ie]}),e[133]=re,e[134]=ie,e[135]=oe):oe=e[135];let be;e[136]===Symbol.for("react.memo_cache_sentinel")?(be=a=>{T(!1),a&&S([])},e[136]=be):be=e[136];let de;e[137]!==o||e[138]!==m?(de=l.jsx(Dn,{open:o,sessionFrgmts:m,onRequestClose:be}),e[137]=o,e[138]=m,e[139]=de):de=e[139];let Ne;return e[140]!==q||e[141]!==oe||e[142]!==de?(Ne=l.jsxs(ge,{direction:"column",align:"stretch",gap:"sm",children:[q,oe,de]}),e[140]=q,e[141]=oe,e[142]=de,e[143]=Ne):Ne=e[143],Ne};function Wn(e){return e==="TERMINATED"||e==="CANCELLED"}function Jn(e){return{label:e,value:e}}function Yn(e){return e==null?void 0:e.node}function Xn(e){return e.id}function Zn(e){return e==null?void 0:e.node}export{tt as default};
//# sourceMappingURL=AdminComputeSessionListPage-CtrFaISF.js.map
