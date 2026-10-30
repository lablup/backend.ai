import{r as y,e as M,c0 as _e,di as Fe,dj as Se,aN as oe,aO as le,dk as ke,c as D,aL as R,d5 as ie,u as ce,n as C,aX as Ie,bS as he,b as be,bt as Ne,dl as Pe,cy as Ke,c9 as Ce}from"./index-CwWAznqi.js";import{f as Ae}from"./TagsInput-B_f8kLOn.js";import{D as $,n as ue,Z as te,u as Ee,_ as Te,m as B,$ as de,q as ae,z as we,b as Le,J as se,f as Re,a0 as Be,r as Ve,l as xe,a1 as Me}from"./lodash-RhKGq0BF.js";import{T as De}from"./Token-B6wppFPd.js";import{R as $e}from"./ResourceAllocationFormItems-t-AZwWay.js";import{r as E}from"./icons-BgdBQS0N.js";import{t as je}from"./BAIVFolderMountConfigInput-Crs_AvaI.js";import{i as re,U as Qe}from"./unifiedAcceleratorSlot-DvOww2Yq.js";const me=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"installed"}],n={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},a=[n,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],r=[{alias:null,args:[{kind:"Variable",name:"is_installed",variableName:"installed"}],concreteType:"Image",kind:"LinkedField",name:"images",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:a,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:a,storageKey:null},{alias:null,args:null,concreteType:"ResourceLimit",kind:"LinkedField",name:"resource_limits",plural:!0,selections:[n,{alias:null,args:null,kind:"ScalarField",name:"min",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"useDefaultImagesWithFallbackQuery",selections:r,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"useDefaultImagesWithFallbackQuery",selections:r},params:{cacheID:"9ab17e1599bcc5bc00de2b9e9bba588d",id:null,metadata:{},name:"useDefaultImagesWithFallbackQuery",operationKind:"query",text:`query useDefaultImagesWithFallbackQuery(
  $installed: Boolean
) {
  images(is_installed: $installed) {
    id
    tag
    registry
    architecture
    namespace
    labels {
      key
      value
    }
    tags {
      key
      value
    }
    resource_limits {
      key
      min
      max
    }
  }
}
`}}})();me.hash="eb58e7ce4ab6b04c3bc41e67418d1142";const j=me,Oe=oe(async()=>{var n,a;const e=await le;return $((n=e._config)==null?void 0:n.defaultFileBrowserImage)||(a=e._config)==null?void 0:a.defaultFileBrowserImage}),ze=oe(async()=>{var n,a;const e=await le;return $((n=e._config)==null?void 0:n.systemSSHImage)||(a=e._config)==null?void 0:a.systemSSHImage}),Ge=ke(),yn=()=>{"use memo";const e=D.c(7),[n,a]=R(Oe),r=y.useRelayEnvironment();let l;e[0]!==n||e[1]!==r||e[2]!==a?(l=()=>{n===void 0&&y.fetchQuery(r,j,{installed:!0},{fetchPolicy:"store-or-network"}).toPromise().then(We).then(async u=>{const i=ue(u);a(i?ie(i):null)}).catch(()=>{a(null)})},e[0]=n,e[1]=r,e[2]=a,e[3]=l):l=e[3];const o=E.useEffectEvent(l);let s;e[4]!==o?(s=()=>{o()},e[4]=o,e[5]=s):s=e[5];let c;return e[6]===Symbol.for("react.memo_cache_sentinel")?(c=[],e[6]=c):c=e[6],E.useEffect(s,c),n},_n=()=>{"use memo";const e=D.c(11),[n,a]=R(ze),[r,l]=R(Ge),o=y.useRelayEnvironment();let s;e[0]!==o||e[1]!==a||e[2]!==l||e[3]!==n?(s=()=>{n===void 0&&y.fetchQuery(o,j,{installed:!0},{fetchPolicy:"store-or-network"}).toPromise().then(Ye).then(async f=>{const p=ue(f);a(p?ie(p):null),l(p||void 0)}).catch(()=>{a(null)})},e[0]=o,e[1]=a,e[2]=l,e[3]=n,e[4]=s):s=e[4];const c=E.useEffectEvent(s);let u;e[5]!==c?(u=()=>{c()},e[5]=c,e[6]=u):u=e[6];let i;e[7]===Symbol.for("react.memo_cache_sentinel")?(i=[],e[7]=i):i=e[7],E.useEffect(u,i);let g;return e[8]!==n||e[9]!==r?(g={systemSSHImage:n,systemSSHImageInfo:r},e[8]=n,e[9]=r,e[10]=g):g=e[10],g},He=()=>{"use memo";var o;const e=y.useRelayEnvironment(),n=M(),{logger:a}=_e(),r=(o=n==null?void 0:n._config)!=null&&o.showNonInstalledImages?{}:{installed:!0};return async s=>{if(!s)return s;const{hasTag:c,hasArch:u}=Fe(s);if(c&&u)return s;try{const i=await y.fetchQuery(e,j,r,{fetchPolicy:"store-or-network"}).toPromise();return Se(s,i==null?void 0:i.images)??s}catch(i){return a.debug("Failed to query images while resolving an image reference; keeping the original value",{imageString:s,error:i}),s}}};function Ue(e){var n;return(e==null?void 0:e.key)==="ai.backend.service-ports"&&((n=e==null?void 0:e.value)==null?void 0:n.toLowerCase().includes("filebrowser"))}function qe(e){var n;return(n=e==null?void 0:e.labels)==null?void 0:n.find(Ue)}function We(e){var n;return(n=e==null?void 0:e.images)==null?void 0:n.filter(qe)}function Xe(e){var n;return(e==null?void 0:e.key)==="ai.backend.role"&&((n=e==null?void 0:e.value)==null?void 0:n.toLowerCase().includes("system"))}function Je(e){var n;return(n=e==null?void 0:e.labels)==null?void 0:n.find(Xe)}function Ye(e){var n;return(n=e==null?void 0:e.images)==null?void 0:n.filter(Je)}const ge=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"}],n=[{kind:"Variable",name:"id",variableName:"id"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"useStartSessionCreationQuery",selections:[{alias:null,args:n,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAINodeNotificationItemFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"useStartSessionCreationQuery",selections:[{alias:null,args:n,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[a,{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[r,l,o,s,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},a,s,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},l],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[o,a],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[r,{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[o],storageKey:null}],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[r,l,s,o],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}]},params:{cacheID:"5a1ffb0d632cf08bed5f7239831f8c3a",id:null,metadata:{},name:"useStartSessionCreationQuery",operationKind:"query",text:`query useStartSessionCreationQuery(
  $id: GlobalIDField!
) {
  compute_session_node(id: $id) {
    ...BAINodeNotificationItemFragment
    id
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
`}}})();ge.hash="7a350248b5a833005f531bd8caa3adec";const V=1024,x=65535,Fn=({name:e="ports",...n})=>{const{t:a}=ce(),r=M();return C.jsx(Ie.Item,{label:a("session.launcher.PreOpenPortTitle"),name:e,tooltip:C.jsx(he,{i18nKey:"session.launcher.DescSetPreOpenPort"}),extra:a("session.launcher.PreOpenPortRangeGuide"),rules:[()=>({validator(l,o){return A(o).length<=r._config.maxCountForPreopenPorts?Promise.resolve():Promise.reject(new Error(a("session.launcher.PreOpenPortMaxCountLimit",{count:r._config.maxCountForPreopenPorts})))}}),()=>({validator(l,o){return te(o,s=>parseInt(s).toString()===s||Q(s))?Promise.resolve():Promise.reject(new Error(a("session.launcher.InvalidPortFormat")))}}),()=>({validator(l,o){const s=A(o);return te(s,c=>c>=V&&c<=x)?Promise.resolve():Promise.reject(new Error(a("session.launcher.PreOpenPortRange")))}}),()=>({validator(l,o){const s=A(o);return Ee(s).length===s.length?Promise.resolve():Promise.reject(new Error(a("session.launcher.DuplicatedPort")))}})],...n,children:C.jsx(Ae,{tokenSeparators:[","," "],"aria-label":a("session.launcher.PreOpenPortTitle"),placeholder:""})})},Sn=({inValid:e,value:n,children:a,...r})=>C.jsx(De,{...r,color:!e&&Ze(n)?"default":"red",label:a??n}),Ze=e=>{if(Q(e)){const n=e.split(":"),[a,r]=n.map(l=>parseInt(l));return a>=V&&r<=x}else if(e===parseInt(e).toString()&&parseInt(e)>=V&&parseInt(e)<=x)return!0;return!1},Q=e=>{const n=e.split(":");if(n.length===2){const[a,r]=n.map(l=>parseInt(l));return a<=r}return!1},ve=e=>{const[n,a]=e.split(":").map(r=>parseInt(r));return de(n,a+1)},A=e=>Te(B(e,n=>Q(n)?ve(n):parseInt(n))),en="session-launcher:",kn=()=>{"use memo";var O;const e=D.c(24),{t:n}=ce(),a=be(),{upsertNotification:r}=Ne(),l=y.useRelayEnvironment(),o=He(),s=M(),[c]=Pe();let u,i,g;e[0]===Symbol.for("react.memo_cache_sentinel")?(u={autoEnabled:!0},i={enabled:!1,command:void 0,scheduleDate:void 0,timeoutEnabled:!1,timeout:void 0,timeoutUnit:"s"},g=[],e[0]=u,e[1]=i,e[2]=g):(u=e[0],i=e[1],g=e[2]);let f;e[3]!==s._config?(f=((O=s._config)==null?void 0:O.default_session_environment)&&{environments:tn(s._config.default_session_environment)},e[3]=s._config,e[4]=f):f=e[4];let p;e[5]===Symbol.for("react.memo_cache_sentinel")?(p=ae($e,["resource"]),e[5]=p):p=e[5];const T=c||void 0;let k;e[6]!==f||e[7]!==T?(k={sessionType:"interactive",allocationPreset:"auto-select",hpcOptimization:u,batch:i,envvars:g,...f,...p,resourceGroup:T},e[6]=f,e[7]=T,e[8]=k):k=e[8];const F=k;let _,S;e[9]!==s||e[10]!==a||e[11]!==F||e[12]!==o||e[13]!==n?(S=t=>{const d=we({},F,t);return _(d)},_=async t=>{var z,G,H,U,q,W,X,J,Y,Z,v,ee;const d=t.environments.manual||await o(t.environments.version||t.environments.environment),[b,L]=(d==null?void 0:d.split("@"))??[],N=b===void 0?"":b,m={sessionName:$(t.sessionName)?nn():t.sessionName,kernelName:N,architecture:L,resources:{enqueueOnly:!0,group_name:t.projectName||a.name||void 0,domain:s._config.domainName,type:t.sessionType,cluster_mode:t.cluster_mode==="multi-node"&&t.cluster_size===1?"single-node":t.cluster_mode,cluster_size:t.cluster_size,maxWaitSeconds:15,reuseIfExists:t.reuseIfExists??!1,...t.sessionType==="batch"?{starts_at:t.batch.enabled?t.batch.scheduleDate:void 0,startupCommand:t.batch.command}:{},...t.bootstrap_script?{bootstrap_script:t.bootstrap_script}:{},...(z=t==null?void 0:t.batch)!=null&&z.timeoutEnabled&&!Ve((G=t==null?void 0:t.batch)==null?void 0:G.timeout)?{batchTimeout:xe(t.batch.timeout)+((H=t==null?void 0:t.batch)==null?void 0:H.timeoutUnit)}:void 0,...t.dependencies&&t.dependencies.length>0?{dependencies:t.dependencies}:{},...re((U=t.resource)==null?void 0:U.acceleratorType)?{tag:`${Qe}${(q=t.resource)==null?void 0:q.acceleratorType}`}:{},config:{...(t==null?void 0:t.resource)&&{resources:{cpu:(W=t==null?void 0:t.resource)==null?void 0:W.cpu,mem:(X=t==null?void 0:t.resource)==null?void 0:X.mem,...(J=t.resource)!=null&&J.acceleratorType&&((Y=t.resource)!=null&&Y.accelerator)&&((Z=t.resource)==null?void 0:Z.accelerator)>0&&!re(t.resource.acceleratorType)?{[t.resource.acceleratorType]:t.resource.accelerator}:void 0}},scaling_group:t.resourceGroup,...(t==null?void 0:t.resource)&&{resource_opts:{shmem:(v=t==null?void 0:t.resource)==null?void 0:v.shmem}},...je(t.vfolderMounts),environ:{...Be(t.envvars.map(an)),...t.hpcOptimization.autoEnabled?{}:ae(t.hpcOptimization,"autoEnabled")},preopen_ports:A(t.ports),...!((ee=s==null?void 0:s._config)!=null&&ee.hideAgents)&&t.agent!==void 0&&!Le(se(t.agent),["auto"])?{agent_list:Re(se(t.agent),sn)}:void 0}}},fe=B(de(t.num_of_sessions||1),pe=>{const ye=(t.num_of_sessions||1)>1?`${m.sessionName}-${Ke()}-${pe}`:m.sessionName;return s.createIfNotExists(m.kernelName,ye,m==null?void 0:m.resources,void 0,m.architecture).then(rn).catch(K=>{var ne;throw(ne=K==null?void 0:K.message)!=null&&ne.includes("The session already exists")?new Error(n("session.launcher.SessionAlreadyExists")):K})});return Promise.allSettled(fe).then(on)},e[9]=s,e[10]=a,e[11]=F,e[12]=o,e[13]=n,e[14]=_,e[15]=S):(_=e[14],S=e[15]);let I;e[16]!==l||e[17]!==r?(I=async(t,d)=>{const b=B(t,L=>{const N=L.value;return y.fetchQuery(l,ge,{id:Ce("ComputeSessionNode",N.sessionId)}).toPromise().then(P=>{const m=(P==null?void 0:P.compute_session_node)??null;m&&r({key:`${en}${N.sessionId}`,node:m,open:!0,duration:0,...d==null?void 0:d[0]},d==null?void 0:d[1])})});return Promise.allSettled(b)},e[16]=l,e[17]=r,e[18]=I):I=e[18];const w=I;let h;return e[19]!==F||e[20]!==_||e[21]!==S||e[22]!==w?(h={startSession:_,startSessionWithDefault:S,defaultFormValues:F,upsertSessionNotification:w},e[19]=F,e[20]=_,e[21]=S,e[22]=w,e[23]=h):h=e[23],h},nn=()=>{let e="";const n="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let a=0;a<8;a++)e+=n.charAt(Math.floor(Math.random()*n.length));return e+"-session"},tn=e=>e.includes(":")?{version:e}:{environment:e};function an(e){return[e.variable,e.value]}function sn(e){return!!e}function rn(e){return e}async function on(e){return Me(e,"status")}export{Sn as P,Fn as a,yn as b,_n as c,kn as u};
//# sourceMappingURL=useStartSession-D5OVeA4A.js.map
