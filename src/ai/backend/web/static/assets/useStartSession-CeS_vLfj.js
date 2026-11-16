import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{P as r,R as i}from"./useWebUIConfig-DvlZdUc9.js";import{Ct as a,G as o,Ht as s,Lt as c,P as l,Q as u,St as d,V as f,Wt as p,at as ee,ht as te,mt as m,ot as h,s as g,vt as _,yt as v}from"./lodash-ClfL87UH.js";/* empty css            */import{t as y}from"./jsx-runtime-BapUIyWk.js";import{s as b}from"./DefaultProviders-BFjPhnQa.js";import{r as x}from"./Skeleton-D35z7Ria.js";import{t as S}from"./Form-DK4EItCB.js";import"./form-engine-mhqCLVoE.js";import{D as C,H as w,M as T,k as E,v as D}from"./helper-BWFKT_2Y.js";import{t as O}from"./react-relay-BfoHYpUf.js";import{t as k}from"./useBAILogger-CRaS0DnM.js";import{t as A}from"./ResourceAllocationFormItems-Dmvs9AKP.js";import{i as ne}from"./BAIVFolderMountConfigInput-CXUEoXXm.js";import{S as re,d as ie}from"./helper-DF1Eunoe.js";import{t as j}from"./Token-D5_yAVQ_.js";import{t as M}from"./TagsInput-DGJVnzUY.js";import{n as N,t as P}from"./useCurrentProject-BaleCvMA.js";import{t as F}from"./utils-DCpr9tfC.js";import{yt as I}from"./index-49VU5B_r.js";import{r as L,t as ae}from"./unifiedAcceleratorSlot-Cl6zmIRK.js";var R=n(),z=y(),B=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`installed`}],t={alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},n=[t,{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null}],r=[{alias:null,args:[{kind:`Variable`,name:`is_installed`,variableName:`installed`}],concreteType:`Image`,kind:`LinkedField`,name:`images`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`tag`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`registry`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`namespace`,storageKey:null},{alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`labels`,plural:!0,selections:n,storageKey:null},{alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`tags`,plural:!0,selections:n,storageKey:null},{alias:null,args:null,concreteType:`ResourceLimit`,kind:`LinkedField`,name:`resource_limits`,plural:!0,selections:[t,{alias:null,args:null,kind:`ScalarField`,name:`min`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`max`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useDefaultImagesWithFallbackQuery`,selections:r,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useDefaultImagesWithFallbackQuery`,selections:r},params:{cacheID:`9ab17e1599bcc5bc00de2b9e9bba588d`,id:null,metadata:{},name:`useDefaultImagesWithFallbackQuery`,operationKind:`query`,text:`query useDefaultImagesWithFallbackQuery(
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
`}}})();B.hash=`eb58e7ce4ab6b04c3bc41e67418d1142`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var V=e(t(),1),H=O(),U=B,W=F(async()=>{var e,t;let n=await T;return h((e=n._config)==null?void 0:e.defaultFileBrowserImage)||(t=n._config)==null?void 0:t.defaultFileBrowserImage}),G=F(async()=>{var e,t;let n=await T;return h((e=n._config)==null?void 0:e.systemSSHImage)||(t=n._config)==null?void 0:t.systemSSHImage}),K=i(),q=()=>{"use memo";let e=(0,R.c)(7),[t,n]=r(W),i=(0,H.useRelayEnvironment)(),a;e[0]!==t||e[1]!==i||e[2]!==n?(a=()=>{t===void 0&&(0,H.fetchQuery)(i,U,{installed:!0},{fetchPolicy:`store-or-network`}).toPromise().then(ue).then(async e=>{let t=v(e);n(t?D(t):null)}).catch(()=>{n(null)})},e[0]=t,e[1]=i,e[2]=n,e[3]=a):a=e[3];let o=(0,V.useEffectEvent)(a),s;e[4]===o?s=e[5]:(s=()=>{o()},e[4]=o,e[5]=s);let c;return e[6]===Symbol.for(`react.memo_cache_sentinel`)?(c=[],e[6]=c):c=e[6],(0,V.useEffect)(s,c),t},oe=()=>{"use memo";let e=(0,R.c)(11),[t,n]=r(G),[i,a]=r(K),o=(0,H.useRelayEnvironment)(),s;e[0]!==o||e[1]!==n||e[2]!==a||e[3]!==t?(s=()=>{t===void 0&&(0,H.fetchQuery)(o,U,{installed:!0},{fetchPolicy:`store-or-network`}).toPromise().then(pe).then(async e=>{let t=v(e);n(t?D(t):null),a(t||void 0)}).catch(()=>{n(null)})},e[0]=o,e[1]=n,e[2]=a,e[3]=t,e[4]=s):s=e[4];let c=(0,V.useEffectEvent)(s),l;e[5]===c?l=e[6]:(l=()=>{c()},e[5]=c,e[6]=l);let u;e[7]===Symbol.for(`react.memo_cache_sentinel`)?(u=[],e[7]=u):u=e[7],(0,V.useEffect)(l,u);let d;return e[8]!==t||e[9]!==i?(d={systemSSHImage:t,systemSSHImageInfo:i},e[8]=t,e[9]=i,e[10]=d):d=e[10],d},se=()=>{"use memo";var e;let t=(0,R.c)(6),n=(0,H.useRelayEnvironment)(),r=w(),{logger:i}=k(),a;if(t[0]!==(r==null||(e=r._config)==null?void 0:e.showNonInstalledImages)){var o,s;a=r!=null&&(o=r._config)!=null&&o.showNonInstalledImages?{}:{installed:!0},t[0]=r==null||(s=r._config)==null?void 0:s.showNonInstalledImages,t[1]=a}else a=t[1];let c=a,l;return t[2]!==c||t[3]!==i||t[4]!==n?(l=async e=>{if(!e)return e;let{hasTag:t,hasArch:r}=C(e);if(t&&r)return e;try{let t=await(0,H.fetchQuery)(n,U,c,{fetchPolicy:`store-or-network`}).toPromise();return E(e,t==null?void 0:t.images)??e}catch(t){let n=t;return i.debug(`Failed to query images while resolving an image reference; keeping the original value`,{imageString:e,error:n}),e}},t[2]=c,t[3]=i,t[4]=n,t[5]=l):l=t[5],l};function ce(e){var t;return(e==null?void 0:e.key)===`ai.backend.service-ports`&&(e==null||(t=e.value)==null?void 0:t.toLowerCase().includes(`filebrowser`))}function le(e){var t;return e==null||(t=e.labels)==null?void 0:t.find(ce)}function ue(e){var t;return e==null||(t=e.images)==null?void 0:t.filter(le)}function de(e){var t;return(e==null?void 0:e.key)===`ai.backend.role`&&(e==null||(t=e.value)==null?void 0:t.toLowerCase().includes(`system`))}function fe(e){var t;return e==null||(t=e.labels)==null?void 0:t.find(de)}function pe(e){var t;return e==null||(t=e.images)==null?void 0:t.filter(fe)}var J=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`}],t=[{kind:`Variable`,name:`id`,variableName:`id`}],n={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},i={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},a={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useStartSessionCreationQuery`,selections:[{alias:null,args:t,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`compute_session_node`,plural:!1,selections:[{args:null,kind:`FragmentSpread`,name:`BAINodeNotificationItemFragment`}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useStartSessionCreationQuery`,selections:[{alias:null,args:t,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`compute_session_node`,plural:!1,selections:[n,{kind:`InlineFragment`,selections:[{kind:`InlineFragment`,selections:[r,i,a,o,{alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`user_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`scaling_group`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`project_id`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},n,o,{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`vfolder_mounts`,storageKey:null},{alias:null,args:null,concreteType:`VirtualFolderConnection`,kind:`LinkedField`,name:`vfolder_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`VirtualFolderEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`VirtualFolderNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[a,n],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_size`,storageKey:null}],type:`ComputeSessionNode`,abstractKey:null},{kind:`InlineFragment`,selections:[r,{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[a],storageKey:null}],type:`VFolder`,abstractKey:null},{kind:`InlineFragment`,selections:[r,i,o,a],type:`VirtualFolderNode`,abstractKey:null}],type:`Node`,abstractKey:`__isNode`}],storageKey:null}]},params:{cacheID:`5a1ffb0d632cf08bed5f7239831f8c3a`,id:null,metadata:{},name:`useStartSessionCreationQuery`,operationKind:`query`,text:`query useStartSessionCreationQuery(
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
`}}})();J.hash=`7a350248b5a833005f531bd8caa3adec`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var Y=1024,X=65535,me=({name:e=`ports`,...t})=>{let{t:n}=x(),r=w();return(0,z.jsx)(S.Item,{label:n(`session.launcher.PreOpenPortTitle`),name:e,tooltip:(0,z.jsx)(I,{i18nKey:`session.launcher.DescSetPreOpenPort`}),extra:n(`session.launcher.PreOpenPortRangeGuide`),rules:[()=>({validator(e,t){return Q(t).length<=r._config.maxCountForPreopenPorts?Promise.resolve():Promise.reject(Error(n(`session.launcher.PreOpenPortMaxCountLimit`,{count:r._config.maxCountForPreopenPorts})))}}),()=>({validator(e,t){return a(t,e=>parseInt(e).toString()===e||Z(e))?Promise.resolve():Promise.reject(Error(n(`session.launcher.InvalidPortFormat`)))}}),()=>({validator(e,t){let r=Q(t);return a(r,e=>e>=Y&&e<=X)?Promise.resolve():Promise.reject(Error(n(`session.launcher.PreOpenPortRange`)))}}),()=>({validator(e,t){let r=Q(t);return g(r).length===r.length?Promise.resolve():Promise.reject(Error(n(`session.launcher.DuplicatedPort`)))}})],...t,children:(0,z.jsx)(M,{tokenSeparators:[`,`,` `],"aria-label":n(`session.launcher.PreOpenPortTitle`),placeholder:``})})},he=({inValid:e,value:t,children:n,...r})=>(0,z.jsx)(j,{...r,color:!e&&ge(t)?`default`:`red`,label:n??t}),ge=e=>{if(Z(e)){let[t,n]=e.split(`:`).map(e=>parseInt(e));return t>=Y&&n<=X}return e===parseInt(e).toString()&&parseInt(e)>=Y&&parseInt(e)<=X},Z=e=>{let t=e.split(`:`);if(t.length===2){let[e,n]=t.map(e=>parseInt(e));return e<=n}return!1},_e=e=>{let[t,n]=e.split(`:`).map(e=>parseInt(e));return l(t,n+1)},Q=e=>s(_(e,e=>Z(e)?_e(e):parseInt(e))),$=`session-launcher:`,ve=()=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let e=(0,R.c)(24),{t}=x(),n=P(),{upsertNotification:r}=b(),i=(0,H.useRelayEnvironment)(),a=se(),s=w(),[m]=N(),g,v,y;e[0]===Symbol.for(`react.memo_cache_sentinel`)?(g={autoEnabled:!0},v={enabled:!1,command:void 0,scheduleDate:void 0,timeoutEnabled:!1,timeout:void 0,timeoutUnit:`s`},y=[],e[0]=g,e[1]=v,e[2]=y):(g=e[0],v=e[1],y=e[2]);let S;if(e[3]!==s._config){var C;S=((C=s._config)==null?void 0:C.default_session_environment)&&{environments:be(s._config.default_session_environment)},e[3]=s._config,e[4]=S}else S=e[4];let T;e[5]===Symbol.for(`react.memo_cache_sentinel`)?(T=f(A,[`resource`]),e[5]=T):T=e[5];let E=m||void 0,D;e[6]!==S||e[7]!==E?(D={sessionType:`interactive`,allocationPreset:`auto-select`,hpcOptimization:g,batch:v,envvars:y,...S,...T,resourceGroup:E},e[6]=S,e[7]=E,e[8]=D):D=e[8];let O=D,k,j;e[9]!==s||e[10]!==n||e[11]!==O||e[12]!==a||e[13]!==t?(j=e=>{let t=o({},O,e);return k(t)},k=async e=>{var r,i,o,m,g,v,y,b,x,S,C,w;let T=e.environments.manual||await a(e.environments.version||e.environments.environment),[E,D]=(T==null?void 0:T.split(`@`))??[],O=E===void 0?``:E,k={sessionName:h(e.sessionName)?ye():e.sessionName,kernelName:O,architecture:D,resources:{enqueueOnly:!0,group_name:e.projectName||n.name||void 0,domain:s._config.domainName,type:e.sessionType,cluster_mode:e.cluster_mode===`multi-node`&&e.cluster_size===1?`single-node`:e.cluster_mode,cluster_size:e.cluster_size,maxWaitSeconds:15,reuseIfExists:e.reuseIfExists??!1,...e.sessionType===`batch`?{starts_at:e.batch.enabled?e.batch.scheduleDate:void 0,startupCommand:e.batch.command}:{},...e.bootstrap_script?{bootstrap_script:e.bootstrap_script}:{},...e!=null&&(r=e.batch)!=null&&r.timeoutEnabled&&!u(e==null||(i=e.batch)==null?void 0:i.timeout)?{batchTimeout:p(e.batch.timeout)+(e==null||(o=e.batch)==null?void 0:o.timeoutUnit)}:void 0,...e.dependencies&&e.dependencies.length>0?{dependencies:e.dependencies}:{},...L((m=e.resource)==null?void 0:m.acceleratorType)?{tag:`${ae}${(g=e.resource)==null?void 0:g.acceleratorType}`}:{},config:{...(e==null?void 0:e.resource)&&{resources:{cpu:e==null||(v=e.resource)==null?void 0:v.cpu,mem:e==null||(y=e.resource)==null?void 0:y.mem,...(b=e.resource)!=null&&b.acceleratorType&&(x=e.resource)!=null&&x.accelerator&&((S=e.resource)==null?void 0:S.accelerator)>0&&!L(e.resource.acceleratorType)?{[e.resource.acceleratorType]:e.resource.accelerator}:void 0}},scaling_group:e.resourceGroup,...(e==null?void 0:e.resource)&&{resource_opts:{shmem:e==null||(C=e.resource)==null?void 0:C.shmem}},...ne(e.vfolderMounts),environ:{...te(e.envvars.map(xe)),...e.hpcOptimization.autoEnabled?{}:f(e.hpcOptimization,`autoEnabled`)},preopen_ports:Q(e.ports),...!(s!=null&&(w=s._config)!=null&&w.hideAgents)&&e.agent!==void 0&&!ee(c(e.agent),[`auto`])?{agent_list:d(c(e.agent),Se)}:void 0}}},A=_(l(e.num_of_sessions||1),n=>{let r=(e.num_of_sessions||1)>1?`${k.sessionName}-${ie()}-${n}`:k.sessionName;return s.createIfNotExists(k.kernelName,r,k==null?void 0:k.resources,void 0,k.architecture).then(Ce).catch(e=>{var n;throw e!=null&&(n=e.message)!=null&&n.includes(`The session already exists`)?Error(t(`session.launcher.SessionAlreadyExists`)):e})});return Promise.allSettled(A).then(we)},e[9]=s,e[10]=n,e[11]=O,e[12]=a,e[13]=t,e[14]=k,e[15]=j):(k=e[14],j=e[15]);let M;e[16]!==i||e[17]!==r?(M=async(e,t)=>{let n=_(e,e=>{let n=e.value;return(0,H.fetchQuery)(i,J,{id:re(`ComputeSessionNode`,n.sessionId)}).toPromise().then(e=>{let i=(e==null?void 0:e.compute_session_node)??null;i&&r({key:`${$}${n.sessionId}`,node:i,open:!0,duration:0,...t==null?void 0:t[0]},t==null?void 0:t[1])})});return Promise.allSettled(n)},e[16]=i,e[17]=r,e[18]=M):M=e[18];let F=M,I;return e[19]!==O||e[20]!==k||e[21]!==j||e[22]!==F?(I={startSession:k,startSessionWithDefault:j,defaultFormValues:O,upsertSessionNotification:F},e[19]=O,e[20]=k,e[21]=j,e[22]=F,e[23]=I):I=e[23],I},ye=()=>{let e=``;for(let t=0;t<8;t++)e+=`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789`.charAt(Math.floor(Math.random()*62));return e+`-session`},be=e=>e.includes(`:`)?{version:e}:{environment:e};function xe(e){return[e.variable,e.value]}function Se(e){return!!e}function Ce(e){return e}async function we(e){return m(e,`status`)}export{oe as a,q as i,me as n,he as r,ve as t};
