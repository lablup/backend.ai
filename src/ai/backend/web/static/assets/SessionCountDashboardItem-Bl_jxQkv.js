import{u as Z,t as ee,r as ne,j as a,B as C,aq as ae,aK as te,k as Ie,aL as Te,l as me,aM as Ke,aN as _,aO as Y,ak as Ae,aP as Ne,al as Re,an as ce,T as be,aG as De,aQ as Ee,aR as xe,aS as Me,af as we,aT as je,L as Be,aU as Ve,w as Pe,ax as Qe,aV as Ue}from"./index-C08xJCnW.js";import{A as qe}from"./AgentList-kq2QUlen.js";import{S as ze}from"./SessionDetailDrawer-BcS-1DiN.js";const We=({fetchKey:s,onChangeFetchKey:e})=>{const{t:n}=Z(),{token:l}=ee.useToken(),[t,u]=ne.useTransition();return a.jsxs(C,{direction:"column",align:"stretch",style:{paddingInline:l.paddingXL,height:"100%"},children:[a.jsx(ae,{title:n("activeAgent.ActiveAgents"),tooltip:n("activeAgent.ActiveAgentsTooltip",{count:5}),extra:a.jsx(te,{size:"small",loading:t,value:"",onChange:i=>{u(()=>{e==null||e(i)})},type:"text",style:{backgroundColor:"transparent"}})}),a.jsx(C,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:l.margin},children:a.jsx(qe,{fetchKey:s,onChangeFetchKey:e,headerProps:{style:{display:"none"}},tableProps:{pagination:{pageSize:3,showSizeChanger:!1}}})})]})},Se={fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AgentStatsRefetchQuery",selections:[{args:null,kind:"FragmentSpread",name:"AgentStatsFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AgentStatsRefetchQuery",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"b2605aadfb3d6bd4a21f3f7887043e31",id:null,metadata:{},name:"AgentStatsRefetchQuery",operationKind:"query",text:`query AgentStatsRefetchQuery {
  ...AgentStatsFragment
}

fragment AgentStatsFragment on Query {
  agentStats @since(version: "25.15.0") {
    totalResource {
      free
      used
      capacity
    }
  }
}
`}};Se.hash="458be767c066ba74fbebc3d9d84638ca";const ke={argumentDefinitions:[],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Se}},name:"AgentStatsFragment",selections:[{alias:null,args:null,concreteType:"AgentStats",kind:"LinkedField",name:"agentStats",plural:!1,selections:[{alias:null,args:null,concreteType:"AgentResource",kind:"LinkedField",name:"totalResource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"free",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"capacity",storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null};ke.hash="458be767c066ba74fbebc3d9d84638ca";const Je=s=>{"use memo";var ge,pe,ye;const e=Ie.c(87);let n,l,t,u;e[0]!==s?({queryRef:u,isRefetching:l,extra:n,...t}=s,e[0]=s,e[1]=n,e[2]=l,e[3]=t,e[4]=u):(n=e[1],l=e[2],t=e[3],u=e[4]);const{t:i}=Z(),{token:o}=ee.useToken(),[S,k]=ne.useTransition();let c;e[5]===Symbol.for("react.memo_cache_sentinel")?(c={defaultValue:"used",trigger:"onDisplayTypeChange",defaultValuePropName:"defaultDisplayType"},e[5]=c):c=e[5];const[r,h]=Te(t,c);let F;e[6]===Symbol.for("react.memo_cache_sentinel")?(F=ke,e[6]=F):F=e[6];const[L,q]=me.useRefetchableFragment(F,u),d=Ke();let se;e:{const U=(ge=L.agentStats)==null?void 0:ge.totalResource;if(!U){let f;e[7]===Symbol.for("react.memo_cache_sentinel")?(f={cpu:null,memory:null,accelerators:[]},e[7]=f):f=e[7],se=f;break e}const g=U.free,p=U.used,m=U.capacity,z=(pe=d==null?void 0:d.resourceSlotsInRG)==null?void 0:pe.cpu,y=(ye=d==null?void 0:d.resourceSlotsInRG)==null?void 0:ye.mem;let G;e[8]!==m||e[9]!==z||e[10]!==g||e[11]!==p?(G=z?{used:{current:_(p.cpu||0),total:_(m.cpu||0)},free:{current:_(g.cpu||0),total:_(m.cpu||0)},metadata:{title:z.human_readable_name,displayUnit:z.display_unit}}:null,e[8]=m,e[9]=z,e[10]=g,e[11]=p,e[12]=G):G=e[12];const oe=G;let O;e[13]!==m||e[14]!==g||e[15]!==y||e[16]!==p?(O=y?{used:{current:Y(p.mem||0,y.display_unit),total:Y(m.mem||0,y.display_unit)},free:{current:Y(g.mem||0,y.display_unit),total:Y(m.mem||0,y.display_unit)},metadata:{title:y.human_readable_name,displayUnit:y.display_unit}}:null,e[13]=m,e[14]=g,e[15]=y,e[16]=p,e[17]=O):O=e[17];const re=O;let W;if(e[18]!==m||e[19]!==g||e[20]!==d.resourceSlotsInRG||e[21]!==p){let f;e[23]!==m||e[24]!==g||e[25]!==p?(f=(ue,H)=>{if(!ue)return null;const Le=g[H]||0,ve=p[H]||0,fe=m[H]||0;return{key:H,used:{current:_(ve),total:_(fe)},free:{current:_(Le),total:_(fe)},metadata:{title:ue.human_readable_name,displayUnit:ue.display_unit}}},e[23]=m,e[24]=g,e[25]=p,e[26]=f):f=e[26],W=Ae(Ne(Re(ce(d==null?void 0:d.resourceSlotsInRG,["cpu","mem"]),f)),$e),e[18]=m,e[19]=g,e[20]=d.resourceSlotsInRG,e[21]=p,e[22]=W}else W=e[22];const de=W;let J;e[27]!==de||e[28]!==oe||e[29]!==re?(J={cpu:oe,memory:re,accelerators:de},e[27]=de,e[28]=oe,e[29]=re,e[30]=J):J=e[30],se=J}const le=se;let v;e[31]!==t.style||e[32]!==o.padding||e[33]!==o.paddingXL?(v={paddingInline:o.paddingXL,paddingBottom:o.padding,...t.style},e[31]=t.style,e[32]=o.padding,e[33]=o.paddingXL,e[34]=v):v=e[34];let I;e[35]!==t?(I=ce(t,["style"]),e[35]=t,e[36]=I):I=e[36];let T;e[37]!==o.fontSizeHeading5||e[38]!==o.fontWeightStrong?(T={fontSize:o.fontSizeHeading5,fontWeight:o.fontWeightStrong},e[37]=o.fontSizeHeading5,e[38]=o.fontWeightStrong,e[39]=T):T=e[39];let K;e[40]!==i?(K=i("agentStats.AgentStats"),e[40]=i,e[41]=K):K=e[41];let A;e[42]!==T||e[43]!==K?(A=a.jsx(be.Text,{style:T,children:K}),e[42]=T,e[43]=K,e[44]=A):A=e[44];let N;e[45]!==i?(N=i("agentStats.AgentStatsDescription"),e[45]=i,e[46]=N):N=e[46];let R;e[47]!==i?(R=i("dashboard.Used"),e[47]=i,e[48]=R):R=e[48];let b;e[49]!==R?(b={label:R,value:"used"},e[49]=R,e[50]=b):b=e[50];let D;e[51]!==i?(D=i("dashboard.Free"),e[51]=i,e[52]=D):D=e[52];let E;e[53]!==D?(E={value:"free",label:D},e[53]=D,e[54]=E):E=e[54];let x;e[55]!==b||e[56]!==E?(x=[b,E],e[55]=b,e[56]=E,e[57]=x):x=e[57];let M;e[58]!==h?(M=U=>h(U),e[58]=h,e[59]=M):M=e[59];let w;e[60]!==r||e[61]!==x||e[62]!==M?(w=a.jsx(xe,{size:"small",options:x,value:r,onChange:M}),e[60]=r,e[61]=x,e[62]=M,e[63]=w):w=e[63];const ie=S||l;let j;e[64]!==q?(j=()=>{k(()=>{q({},{fetchPolicy:"network-only"})})},e[64]=q,e[65]=j):j=e[65];let $;e[66]===Symbol.for("react.memo_cache_sentinel")?($={backgroundColor:"transparent"},e[66]=$):$=e[66];let B;e[67]!==ie||e[68]!==j?(B=a.jsx(te,{size:"small",loading:ie,value:"",onChange:j,type:"text",style:$}),e[67]=ie,e[68]=j,e[69]=B):B=e[69];let V;e[70]!==n||e[71]!==w||e[72]!==B?(V=a.jsxs(C,{gap:"xs",wrap:"wrap",children:[w,B,n]}),e[70]=n,e[71]=w,e[72]=B,e[73]=V):V=e[73];let P;e[74]!==V||e[75]!==A||e[76]!==N?(P=a.jsx(ae,{title:A,tooltip:N,extra:V}),e[74]=V,e[75]=A,e[76]=N,e[77]=P):P=e[77];let Q;e[78]!==le||e[79]!==r||e[80]!==d.isLoading?(Q=d.isLoading?a.jsx(De,{active:!0}):a.jsx(Ee,{resourceData:le,displayType:r==="used"?"used":"free",progressMode:"normal"}),e[78]=le,e[79]=r,e[80]=d.isLoading,e[81]=Q):Q=e[81];let X;return e[82]!==P||e[83]!==Q||e[84]!==v||e[85]!==I?(X=a.jsxs(C,{direction:"column",align:"stretch",style:v,...I,children:[P,Q]}),e[82]=P,e[83]=Q,e[84]=v,e[85]=I,e[86]=X):X=e[86],X};function $e(s){return!!(s.used.current||s.used.total)}const Fe=(function(){var s=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},o=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],S={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,n,l,t],storageKey:null}],storageKey:null},k];return{fragment:{argumentDefinitions:s,kind:"Fragment",metadata:null,name:"RecentlyCreatedSessionRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"RecentlyCreatedSessionFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:s,kind:"Operation",name:"RecentlyCreatedSessionRefetchQuery",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[e,n,l,t,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},i,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},e,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},l,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:o,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:o,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},i,e],storageKey:null},n,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},t,u,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},e],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[n,l,e],storageKey:null}],storageKey:null},k],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},S,{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:c,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"d5404fd0862afa3bee17d36ec2b237eb",id:null,metadata:{},name:"RecentlyCreatedSessionRefetchQuery",operationKind:"query",text:`query RecentlyCreatedSessionRefetchQuery(
  $scopeId: ScopeField
) {
  ...RecentlyCreatedSessionFragment_3vJUag
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

fragment RecentlyCreatedSessionFragment_3vJUag on Query {
  compute_session_nodes(first: 5, order: "-created_at", filter: "status == \\"running\\"", scope_id: $scopeId) {
    edges {
      node {
        id
        ...SessionNodesFragment
      }
    }
  }
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
`}}})();Fe.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const _e={argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Fe}},name:"RecentlyCreatedSessionFragment",selections:[{alias:null,args:[{kind:"Literal",name:"filter",value:'status == "running"'},{kind:"Literal",name:"first",value:5},{kind:"Literal",name:"order",value:"-created_at"},{kind:"Variable",name:"scope_id",variableName:"scopeId"}],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null};_e.hash="aeaa38c05c8fe2c9a07946ed4a3fe214";const He=({queryRef:s,isRefetching:e})=>{var c;const{t:n}=Z(),{token:l}=ee.useToken(),[t,u]=Me("sessionDetail",we.withOptions({history:"push"})),[i,o]=ne.useTransition(),[S,k]=me.useRefetchableFragment(_e,s);return a.jsxs(a.Fragment,{children:[a.jsxs(C,{direction:"column",align:"stretch",style:{paddingInline:l.paddingXL,height:"100%"},children:[a.jsx(ae,{title:n("session.RecentlyCreatedSessions"),tooltip:n("session.RecentlyCreatedSessionsTooltip",{count:5}),extra:a.jsx(te,{size:"small",loading:i||e,value:"",onChange:()=>{o(()=>{k({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),a.jsx(C,{direction:"column",align:"stretch",style:{flex:1,overflowY:"auto",overflowX:"hidden",marginBottom:l.margin},children:a.jsx(je,{sessionsFrgmt:Ve((c=S.compute_session_nodes)==null?void 0:c.edges.map(r=>r==null?void 0:r.node)),onClickSessionName:r=>{u(Be(r.id))},pagination:!1,disableSorter:!0,style:{overflowY:"hidden"}})})]}),a.jsx(Pe,{children:a.jsx(ze,{open:!!t,sessionId:t||void 0,onClose:()=>{u(null)}})})]})},Ce=(function(){var s=[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],e={kind:"Literal",name:"first",value:0},n={kind:"Variable",name:"scope_id",variableName:"scopeId"},l=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{fragment:{argumentDefinitions:s,kind:"Fragment",metadata:null,name:"SessionCountDashboardItemRefetchQuery",selections:[{args:[{kind:"Variable",name:"scopeId",variableName:"scopeId"}],kind:"FragmentSpread",name:"SessionCountDashboardItemFragment"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:s,kind:"Operation",name:"SessionCountDashboardItemRefetchQuery",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},e,n],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:l,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},e,n],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:l,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},e,n],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:l,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},e,n],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:l,storageKey:null}]},params:{cacheID:"4e2a7d64eccfa5e512354e770190e051",id:null,metadata:{},name:"SessionCountDashboardItemRefetchQuery",operationKind:"query",text:`query SessionCountDashboardItemRefetchQuery(
  $scopeId: ScopeField
) {
  ...SessionCountDashboardItemFragment_3vJUag
}

fragment SessionCountDashboardItemFragment_3vJUag on Query {
  myInteractive: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"interactive\\"", scope_id: $scopeId) {
    count
  }
  myBatch: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"batch\\"", scope_id: $scopeId) {
    count
  }
  myInference: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"inference\\"", scope_id: $scopeId) {
    count
  }
  myUpload: compute_session_nodes(first: 0, filter: "status != \\"TERMINATED\\" & status != \\"CANCELLED\\" & type == \\"system\\"", scope_id: $scopeId) {
    count
  }
}
`}}})();Ce.hash="19e666cf346850c01eda18c6889928ae";const he=(function(){var s={kind:"Literal",name:"first",value:0},e={kind:"Variable",name:"scope_id",variableName:"scopeId"},n=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}];return{argumentDefinitions:[{defaultValue:null,kind:"LocalArgument",name:"scopeId"}],kind:"Fragment",metadata:{refetch:{connection:null,fragmentPathInResult:[],operation:Ce}},name:"SessionCountDashboardItemFragment",selections:[{alias:"myInteractive",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "interactive"'},s,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:n,storageKey:null},{alias:"myBatch",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "batch"'},s,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:n,storageKey:null},{alias:"myInference",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "inference"'},s,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:n,storageKey:null},{alias:"myUpload",args:[{kind:"Literal",name:"filter",value:'status != "TERMINATED" & status != "CANCELLED" & type == "system"'},s,e],concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"compute_session_nodes",plural:!1,selections:n,storageKey:null}],type:"Query",abstractKey:null}})();he.hash="19e666cf346850c01eda18c6889928ae";const Ye=({queryRef:s,isRefetching:e,title:n,...l})=>{const{t}=Z(),{token:u}=ee.useToken(),[i,o]=ne.useTransition(),[S,k]=me.useRefetchableFragment(he,s),{myInteractive:c,myBatch:r,myInference:h,myUpload:F}=S||{},L=(q,d)=>a.jsx(Ue,{title:q,current:d,progressMode:"hidden"});return a.jsxs(C,{direction:"column",align:"stretch",style:{paddingInline:u.paddingXL,...l.style},...ce(l,["style"]),children:[a.jsx(ae,{title:n,extra:a.jsx(te,{size:"small",loading:i||e,value:"",onChange:()=>{o(()=>{k({},{fetchPolicy:"network-only"})})},type:"text",style:{backgroundColor:"transparent"}})}),a.jsx(C,{direction:"row",wrap:"wrap",gap:"lg",children:a.jsxs(Qe,{style:{paddingBlock:u.padding},children:[L(t("session.Interactive"),(c==null?void 0:c.count)||0),L(t("session.Batch"),(r==null?void 0:r.count)||0),L(t("session.Inference"),(h==null?void 0:h.count)||0),L(t("session.System"),(F==null?void 0:F.count)||0)]})})]})};export{Je as A,He as R,Ye as S,We as a};
//# sourceMappingURL=SessionCountDashboardItem-Bl_jxQkv.js.map
