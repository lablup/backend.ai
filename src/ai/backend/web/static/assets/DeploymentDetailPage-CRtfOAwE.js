import{h as Wt,k as We,av as Hn,l as Re,as as Rl,ao as nn,a_ as Al,j as n,bg as El,A as dl,bU as jl,aq as pn,au as Bn,q as $n,u as Je,t as Dl,J as Pl,H as Ol,r as O,aH as Il,aR as Gt,a7 as qn,cm as fn,T as Xe,z as cl,B as te,aQ as wl,W as Ll,Y as kl,aM as xl,G as Wl,V as ll,w as fl,ac as Hl,O as oe,df as Yt,ba as kn,bb as Sn,bj as hn,b4 as cn,aK as zl,L as Qn,N as Xt,a as vn,ab as Cl,$ as ql,E as Tl,v as ml,dg as Jt,Q as Yl,U as Ql,cp as Zt,X as Tn,aX as Dn,P as Bl,bA as gl,b3 as In,dh as ea,di as la,dj as na,dk as ta,_ as Vl,dl as aa,ai as ia,dm as sa,Z as ra,bx as Cn,dn as Xl,bK as Jl,dp as oa,a5 as zn,dq as da,cS as Un,br as ua,o as ca,aV as ma,cJ as ga,a9 as ya,ar as pa,dr as fa,cn as $l,cq as pl,f as Zl,c4 as Wn,an as ka,bD as Ul,al as Fn,b9 as Sa,c6 as xn,c2 as _l,a0 as tn,a1 as Rn,c_ as Gn,ds as Yn,a4 as Xn,de as ha,D as va,b_ as en,F as bn,bR as Jn,am as Zn,dt as ln,cV as Fa,c8 as xa,c1 as Ra,aB as An,d7 as Mn,c9 as ba,du as Ka,aY as Ta,dv as Da,dw as Ia,p as Ln,aj as Ca,dx as Aa,dy as Ma,dz as La,dA as ja,dB as Pa}from"./index-CrFvxZIN.js";import{f as Na,t as Va}from"./parseCliCommand-DLNI3aPC.js";import{R as _a,b as Ea}from"./RuntimeParameterFormSection-gnJTsvV3.js";import{B as jn}from"./BAIVFolderSelect-ZYyoibFb.js";import{F as Pn}from"./folder-open-CRZKyIMX.js";import{B as Oa,P as wa}from"./PrometheusQueryTemplatePreview-ohh0V9FN.js";import{B as et,n as lt,u as nt,a as tt,o as Ha,R as at,S as Ba}from"./SessionDetailDrawer-DlIuxfcr.js";import{S as it}from"./square-pen-CbJIrIOh.js";import{i as hl,a as st,B as $a,D as an,b as qa}from"./DeploymentRevisionDetailDrawer-CoGWrqnO.js";import{B as Gl}from"./BAIGraphQLPropertyFilter-Nw6tLZrH.js";import{B as Nl}from"./BAIId-DDwepSJA.js";import{B as Qa}from"./BooleanTag-By_86yqr.js";import{S as za,a as Ua}from"./ScopedAuditLog-jNEdU5fZ.js";import{F as Wa}from"./FolderLink-BO0tWhos.js";import"./UndoOutlined-CdTczTuT.js";import"./corner-down-left-1tU43fIF.js";import"./zip-C2swOsbQ.js";import"./unzip-mWqiDzDd.js";import"./union-BOoZr1ni.js";import"./WarningOutlined-CBLl6_7b.js";/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ga=[["line",{x1:"15",x2:"15",y1:"12",y2:"18",key:"1p7wdc"}],["line",{x1:"12",x2:"18",y1:"15",y2:"15",key:"1nscbv"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2",key:"17jyea"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",key:"zix9uf"}]],Nn=Wt("copy-plus",Ga),rt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"DeploymentHistory",abstractKey:null};rt.hash="eb0787126d34e31d6d0aa79127c25d2f";const mn=[];[...mn,...mn.map(l=>`-${l}`)];const vl=l=>pn(mn,l),Ya=l=>{"use memo";const e=We.c(23);let a,r,t,i,d;e[0]!==l?({schedulingHistoryFrgmt:i,disableSorter:r,customizeColumns:a,onChangeOrder:t,...d}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5]);const{t:s}=Hn();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=rt,e[6]=u):u=e[6];const o=Re.useFragment(u,i);let y;if(e[7]!==a||e[8]!==r||e[9]!==s){let p;e[11]!==r?(p=R=>r?Bn(R,"sorter"):R,e[11]=r,e[12]=p):p=e[12];const S=Rl(nn([{dataIndex:"updatedAt",title:s("comp:BAIDeploymentSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:Xa,sorter:vl("updated_at")},{dataIndex:"createdAt",title:s("comp:BAIDeploymentSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:Ja,sorter:vl("created_at")},{dataIndex:"phase",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Phase"),key:"phase",sorter:vl("phase")},{dataIndex:"result",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Result"),key:"result",render:Za,sorter:vl("result")},{dataIndex:"category",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Category"),key:"category",sorter:vl("category")},{key:"fromStatus",title:s("comp:BAIDeploymentSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:vl("from_status")},{key:"toStatus",title:s("comp:BAIDeploymentSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:vl("to_status")},{dataIndex:"attempts",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:vl("attempts")},{key:"errorCode",title:s("comp:BAIDeploymentSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:ei,sorter:vl("errorCode")},{key:"message",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:li,render:ni,sorter:vl("message")}]),p);y=a?a(S):S,e[7]=a,e[8]=r,e[9]=s,e[10]=y}else y=e[10];const c=y;let k;e[13]!==o?(k=Al(o),e[13]=o,e[14]=k):k=e[14];let m;e[15]===Symbol.for("react.memo_cache_sentinel")?(m={x:"max-content"},e[15]=m):m=e[15];let g;e[16]!==t?(g=p=>{t==null||t(p||null)},e[16]=t,e[17]=g):g=e[17];let f;return e[18]!==c||e[19]!==k||e[20]!==g||e[21]!==d?(f=n.jsx(El,{rowKey:"id",dataSource:k,columns:c,scroll:m,onChangeOrder:g,...d}),e[18]=c,e[19]=k,e[20]=g,e[21]=d,e[22]=f):f=e[22],f};function Xa(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function Ja(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function Za(l,e){const a=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(et,{result:a})}function ei(l,e){return e.errorCode?n.jsx(jl,{monospace:!0,children:e.errorCode}):"-"}function li(){return{style:{maxWidth:500}}}function ni(l,e){return e.message?n.jsx(jl,{title:e.message,style:{width:"100%"},children:lt(e.message)}):"-"}const ot={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryNodeTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"RouteHistory",abstractKey:null};ot.hash="bd0c64d2e599015d8b9db0afbcb05c7c";const gn=[];[...gn,...gn.map(l=>`-${l}`)];const Fl=l=>pn(gn,l),ti=l=>{"use memo";const e=We.c(23);let a,r,t,i,d;e[0]!==l?({schedulingHistoryFrgmt:i,disableSorter:r,customizeColumns:a,onChangeOrder:t,...d}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5]);const{t:s}=Hn();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=ot,e[6]=u):u=e[6];const o=Re.useFragment(u,i);let y;if(e[7]!==a||e[8]!==r||e[9]!==s){let p;e[11]!==r?(p=R=>r?Bn(R,"sorter"):R,e[11]=r,e[12]=p):p=e[12];const S=Rl(nn([{dataIndex:"updatedAt",title:s("comp:BAIRouteSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:ai,sorter:Fl("updated_at")},{dataIndex:"createdAt",title:s("comp:BAIRouteSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:ii,sorter:Fl("created_at")},{dataIndex:"phase",title:s("comp:BAIRouteSchedulingHistoryNodes.Phase"),key:"phase",sorter:Fl("phase")},{dataIndex:"result",title:s("comp:BAIRouteSchedulingHistoryNodes.Result"),key:"result",render:si,sorter:Fl("result")},{dataIndex:"category",title:s("comp:BAIRouteSchedulingHistoryNodes.Category"),key:"category",sorter:Fl("category")},{key:"fromStatus",title:s("comp:BAIRouteSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Fl("from_status")},{key:"toStatus",title:s("comp:BAIRouteSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Fl("to_status")},{dataIndex:"attempts",title:s("comp:BAIRouteSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Fl("attempts")},{key:"errorCode",title:s("comp:BAIRouteSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:ri,sorter:Fl("errorCode")},{key:"message",title:s("comp:BAIRouteSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:oi,render:di,sorter:Fl("message")}]),p);y=a?a(S):S,e[7]=a,e[8]=r,e[9]=s,e[10]=y}else y=e[10];const c=y;let k;e[13]!==o?(k=Al(o),e[13]=o,e[14]=k):k=e[14];let m;e[15]===Symbol.for("react.memo_cache_sentinel")?(m={x:"max-content"},e[15]=m):m=e[15];let g;e[16]!==t?(g=p=>{t==null||t(p||null)},e[16]=t,e[17]=g):g=e[17];let f;return e[18]!==c||e[19]!==k||e[20]!==g||e[21]!==d?(f=n.jsx(El,{rowKey:"id",dataSource:k,columns:c,scroll:m,onChangeOrder:g,...d}),e[18]=c,e[19]=k,e[20]=g,e[21]=d,e[22]=f):f=e[22],f};function ai(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function ii(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function si(l,e){const a=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(et,{result:a})}function ri(l,e){return e.errorCode?n.jsx(jl,{monospace:!0,children:e.errorCode}):"-"}function oi(){return{style:{maxWidth:500}}}function di(l,e){return e.message?n.jsx(jl,{title:e.message,style:{width:"100%"},children:lt(e.message)}):"-"}const dt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryNodesFragment"}],type:"DeploymentHistory",abstractKey:null};dt.hash="72a9b8118e4f52a97c2ab8996996098d";const ui=l=>{"use memo";const e=We.c(24);let a,r,t,i;e[0]!==l?({schedulingHistoryFrgmt:i,expandMode:a,onExpandModeChange:r,...t}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i):(a=e[1],r=e[2],t=e[3],i=e[4]);let d;e[5]===Symbol.for("react.memo_cache_sentinel")?(d=dt,e[5]=d):d=e[5];const s=Re.useFragment(d,i);let u;e[6]!==s?(u=Al(s),e[6]=s,e[7]=u):u=e[7];const o=u;let y;e[8]!==a||e[9]!==r?(y={mode:a,onModeChange:r},e[8]=a,e[9]=r,e[10]=y):y=e[10];const{expandedRowKeys:c,onExpandedRowsChange:k,expandColumnTitle:m}=nt(o,y);let g,f;e[11]!==o?(g=R=>{var F;return!$n((F=o.find(x=>x.id===R.id))==null?void 0:F.subSteps)},f=R=>{var F;return n.jsx(tt,{resizable:!0,subStepsFrgmt:((F=o.find(x=>x.id===R.id))==null?void 0:F.subSteps)??[],pagination:!1})},e[11]=o,e[12]=g,e[13]=f):(g=e[12],f=e[13]);let p;e[14]!==m||e[15]!==c||e[16]!==k||e[17]!==g||e[18]!==f?(p={columnTitle:m,expandedRowKeys:c,onExpandedRowsChange:k,rowExpandable:g,expandedRowRender:f},e[14]=m,e[15]=c,e[16]=k,e[17]=g,e[18]=f,e[19]=p):p=e[19];let S;return e[20]!==s||e[21]!==t||e[22]!==p?(S=n.jsx(Ya,{schedulingHistoryFrgmt:s,expandable:p,...t}),e[20]=s,e[21]=t,e[22]=p,e[23]=S):S=e[23],S},ut={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryNodeTableFragment"}],type:"RouteHistory",abstractKey:null};ut.hash="7f5f32e6a4ea10ddfc54ff01c8b260b2";const ci=l=>{"use memo";const e=We.c(24);let a,r,t,i;e[0]!==l?({schedulingHistoryFrgmt:i,expandMode:a,onExpandModeChange:r,...t}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i):(a=e[1],r=e[2],t=e[3],i=e[4]);let d;e[5]===Symbol.for("react.memo_cache_sentinel")?(d=ut,e[5]=d):d=e[5];const s=Re.useFragment(d,i);let u;e[6]!==s?(u=Al(s),e[6]=s,e[7]=u):u=e[7];const o=u;let y;e[8]!==a||e[9]!==r?(y={mode:a,onModeChange:r},e[8]=a,e[9]=r,e[10]=y):y=e[10];const{expandedRowKeys:c,onExpandedRowsChange:k,expandColumnTitle:m}=nt(o,y);let g,f;e[11]!==o?(g=R=>{var F;return!$n((F=o.find(x=>x.id===R.id))==null?void 0:F.subSteps)},f=R=>{var F;return n.jsx(tt,{resizable:!0,subStepsFrgmt:((F=o.find(x=>x.id===R.id))==null?void 0:F.subSteps)??[],pagination:!1})},e[11]=o,e[12]=g,e[13]=f):(g=e[12],f=e[13]);let p;e[14]!==m||e[15]!==c||e[16]!==k||e[17]!==g||e[18]!==f?(p={columnTitle:m,expandedRowKeys:c,onExpandedRowsChange:k,rowExpandable:g,expandedRowRender:f},e[14]=m,e[15]=c,e[16]=k,e[17]=g,e[18]=f,e[19]=p):p=e[19];let S;return e[20]!==s||e[21]!==t||e[22]!==p?(S=n.jsx(ti,{schedulingHistoryFrgmt:s,expandable:p,...t}),e[20]=s,e[21]=t,e[22]=p,e[23]=S):S=e[23],S},ct=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},d={alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},s={alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},u=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],o={alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:u,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},y={alias:null,args:null,concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:u,storageKey:null},c=[a],k={alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},f={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,r,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[m,g,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},f],storageKey:null},S={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},F=[r,R],x={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:F,storageKey:null}],storageKey:null}],storageKey:null},D={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},K={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[m,g,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},f],storageKey:null},C={alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[r,a],storageKey:null},_={alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:F,storageKey:null}],storageKey:null},H={alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},R,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},a],storageKey:null}],storageKey:null},z={alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},w={alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},E={alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},$={alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},Y={alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},U={alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},q={alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},B={alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},j={alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},b={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentDetailPageQuery",selections:[{kind:"CatchField",field:{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,t,i],storageKey:null},d,s,o,y,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[k],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentBasicInfoCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentReplicasCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAccessTokensCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAutoScalingCard_deployment"}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,t,i,{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[r],storageKey:null},a],storageKey:null}],storageKey:null},d,s,o,y,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[a,p,S,x,D,K,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},C,_,H,z],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,L,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[w,V,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},T,E,$,Y,U,q],storageKey:null},B,j],storageKey:null}],storageKey:null}],storageKey:null},b,A,P,D,b],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:[a,A,P,S,D,x,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[C,z,_,H],storageKey:null},p,K,b,{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,L,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[w,B,V,j,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[T,$,E,Y,U,q],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[k,a],storageKey:null}],storageKey:null}]},params:{cacheID:"cf0be491960db330acb124fcdb02e651",id:null,metadata:{},name:"DeploymentDetailPageQuery",operationKind:"query",text:`query DeploymentDetailPageQuery(
  $deploymentId: ID!
) {
  deployment(id: $deploymentId) {
    id
    metadata {
      name
      status
      projectId
    }
    networkAccess {
      openToPublic
      endpointUrl
    }
    replicaState {
      desiredReplicaCount
    }
    runningReplicas: replicas(filter: {status: {equals: RUNNING}}) {
      count
    }
    accessTokens {
      count
    }
    currentRevision @since(version: "26.4.3") {
      id
    }
    deployingRevision @since(version: "26.4.3") {
      id
    }
    creator @since(version: "26.4.3") {
      basicInfo {
        email
      }
      id
    }
    ...DeploymentAddRevisionModal_deployment
    ...DeploymentBasicInfoCard_deployment
    ...DeploymentRevisionCard_deployment
    ...DeploymentReplicasCard_deployment
    ...DeploymentAccessTokensCard_deployment
    ...DeploymentAutoScalingCard_deployment
  }
}

fragment BAIDeploymentTagChips_metadata on ModelDeploymentMetadata {
  tags
}

fragment DeploymentAccessTokensCard_deployment on ModelDeployment {
  id
  networkAccess {
    endpointUrl
  }
}

fragment DeploymentAddRevisionModal_deployment on ModelDeployment {
  id
  metadata {
    resourceGroupName
  }
  currentRevision @since(version: "26.4.3") {
    modelMountConfig {
      vfolderId
    }
    ...DeploymentAddRevisionModal_revisionSource
    id
  }
}

fragment DeploymentAddRevisionModal_revisionSource on ModelRevision {
  clusterConfig {
    mode
    size
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  resourceSlots {
    slotName
    quantity
  }
  extraMounts {
    vfolderId
    mountDestination
  }
  modelRuntimeConfig {
    runtimeVariantId
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          enable @since(version: "26.4.4")
          path
          maxRetries
          initialDelay
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
  imageV2 {
    id
    identity {
      canonicalName
      architecture
    }
  }
}

fragment DeploymentAutoScalingCard_deployment on ModelDeployment {
  id
  metadata {
    status
  }
  creator @since(version: "26.4.3") {
    basicInfo {
      email
    }
    id
  }
}

fragment DeploymentBasicInfoCard_deployment on ModelDeployment {
  id
  ...DeploymentSettingModal_deployment
  metadata {
    name
    projectId
    domainName
    status
    resourceGroupName
    projectV2 @since(version: "26.4.3") {
      basicInfo {
        name
      }
      id
    }
    ...BAIDeploymentTagChips_metadata
  }
  networkAccess {
    openToPublic
    endpointUrl
  }
  replicaState {
    desiredReplicaCount
  }
}

fragment DeploymentCurrentRevisionTab_deployment on ModelDeployment {
  id
  currentRevision @since(version: "26.4.3") {
    id
    revisionNumber
    ...DeploymentRevisionDetail_revision
  }
  deployingRevision @since(version: "26.4.3") {
    id
    revisionNumber
    ...DeploymentRevisionDetail_revision
  }
}

fragment DeploymentReplicasCard_deployment on ModelDeployment {
  id
}

fragment DeploymentRevisionCard_deployment on ModelDeployment {
  id
  ...DeploymentCurrentRevisionTab_deployment
  ...DeploymentRevisionHistoryTab_deployment
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
      architecture
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
}

fragment DeploymentRevisionHistoryTab_deployment on ModelDeployment {
  id
  metadata {
    status
  }
  ...DeploymentAddRevisionModal_deployment
}

fragment DeploymentSettingModal_deployment on ModelDeployment {
  id
  metadata {
    name
    tags
    resourceGroupName
  }
  networkAccess {
    openToPublic
  }
  replicaState {
    desiredReplicaCount
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}})();ct.hash="9089d2f31b9601fe2fa64e840ab45300";const mt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAccessTokenPayload",kind:"LinkedField",name:"deleteAccessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardDeleteMutation",selections:e},params:{cacheID:"3001cf022c16a198843b296bca8e75f9",id:null,metadata:{},name:"DeploymentAccessTokensCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensCardDeleteMutation(
  $input: DeleteAccessTokenInput!
) {
  deleteAccessToken(input: $input) {
    id
  }
}
`}}})();mt.hash="6877559748beeee076979bb65393d59f";const gt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:[{kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"CREATED_AT"}]}],concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"AccessTokenEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"node",plural:!1,selections:[a,{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:'accessTokens(orderBy:[{"direction":"DESC","field":"CREATED_AT"}])'};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[r],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[r,a],storageKey:null}]},params:{cacheID:"fe0599e3ca582035a0afb69f61751a53",id:null,metadata:{},name:"DeploymentAccessTokensCardListQuery",operationKind:"query",text:`query DeploymentAccessTokensCardListQuery(
  $deploymentId: ID!
) {
  deployment(id: $deploymentId) {
    accessTokens(orderBy: [{field: CREATED_AT, direction: DESC}]) {
      count
      edges {
        node {
          id
          token
          createdAt
          expiresAt
        }
      }
    }
    id
  }
}
`}}})();gt.hash="b43bdbd02f49d9e5a3e3b15dac4c1b90";const yt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAccessTokenPayload",kind:"LinkedField",name:"createAccessToken",plural:!1,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"accessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardCreateMutation",selections:e},params:{cacheID:"8c08238f7222fe51a04881e736d82b15",id:null,metadata:{},name:"DeploymentAccessTokensCardCreateMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensCardCreateMutation(
  $input: CreateAccessTokenInput!
) {
  createAccessToken(input: $input) {
    accessToken {
      id
      token
      createdAt
      expiresAt
    }
  }
}
`}}})();yt.hash="4ba926c16e8cf928584ec3a34cde8b34";const pt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};pt.hash="e7372d3fa2bb21537f6b39e44698dedf";const mi=l=>{"use memo";var Te;const e=We.c(95);let a,r,t,i,d,s,u;e[0]!==l?({deploymentFrgmt:t,deploymentId:i,isOwnedByCurrentUser:s,isDeploymentDestroying:u,onTokenCreated:d,cardRef:a,...r}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d,e[6]=s,e[7]=u):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5],s=e[6],u=e[7]);const o=s===void 0?!0:s,y=u===void 0?!1:u,{t:c}=Je(),{token:k}=Dl.useToken(),{message:m}=Pl.useApp(),{logger:g}=Ol(),[f,p]=O.useTransition(),[S,R]=Il();let F;e[8]===Symbol.for("react.memo_cache_sentinel")?(F={defaultValue:!1,valuePropName:"isCreateModalOpen",trigger:"onCreateModalOpenChange"},e[8]=F):F=e[8];const[x,D]=Gt(r,F),[K,C]=O.useState(null),_=O.useDeferredValue(S);let H;e[9]===Symbol.for("react.memo_cache_sentinel")?(H=pt,e[9]=H):H=e[9];const z=Re.useFragment(H,t);let L;e[10]===Symbol.for("react.memo_cache_sentinel")?(L=yt,e[10]=L):L=e[10];const w=qn(L);let V;e[11]!==R?(V=()=>{p(()=>{R()})},e[11]=R,e[12]=V):V=e[12];const T=V,E=!!((Te=z.networkAccess)!=null&&Te.endpointUrl),$=y||!o,Y=$||!E;let U;e[13]!==c?(U=c("deployment.tab.AccessTokens"),e[13]=c,e[14]=U):U=e[14];let q;e[15]!==c?(q=c("deployment.tab.description.AccessTokens"),e[15]=c,e[16]=q):q=e[16];let B;e[17]!==k.colorTextDescription?(B=n.jsx(fn,{style:{color:k.colorTextDescription}}),e[17]=k.colorTextDescription,e[18]=B):B=e[18];let j;e[19]!==q||e[20]!==B?(j=n.jsx(cl,{title:q,children:B}),e[19]=q,e[20]=B,e[21]=j):j=e[21];let b;e[22]!==j||e[23]!==U?(b=n.jsxs(te,{gap:"xs",align:"center",children:[U,j]}),e[22]=j,e[23]=U,e[24]=b):b=e[24];let A;e[25]!==T||e[26]!==f?(A=n.jsx(wl,{loading:f,value:"",onChange:T}),e[25]=T,e[26]=f,e[27]=A):A=e[27];let P;e[28]!==E||e[29]!==c?(P=E?"":c("deployment.accessToken.EndpointNotIssuedYet"),e[28]=E,e[29]=c,e[30]=P):P=e[30];let ne;e[31]===Symbol.for("react.memo_cache_sentinel")?(ne=n.jsx(Ll,{}),e[31]=ne):ne=e[31];let le;e[32]!==D?(le=()=>D(!0),e[32]=D,e[33]=le):le=e[33];let I;e[34]!==c?(I=c("deployment.accessToken.Create"),e[34]=c,e[35]=I):I=e[35];let v;e[36]!==Y||e[37]!==le||e[38]!==I?(v=n.jsx(kl,{type:"primary",icon:ne,disabled:Y,onClick:le,children:I}),e[36]=Y,e[37]=le,e[38]=I,e[39]=v):v=e[39];let N;e[40]!==P||e[41]!==v?(N=n.jsx(cl,{title:P,children:v}),e[40]=P,e[41]=v,e[42]=N):N=e[42];let M;e[43]!==A||e[44]!==N?(M=n.jsxs(te,{gap:"xs",align:"center",children:[A,N]}),e[43]=A,e[44]=N,e[45]=M):M=e[45];let W;e[46]===Symbol.for("react.memo_cache_sentinel")?(W={body:{paddingTop:0}},e[46]=W):W=e[46];let J;e[47]===Symbol.for("react.memo_cache_sentinel")?(J=n.jsx(xl,{active:!0}),e[47]=J):J=e[47];let Z;e[48]!==_||e[49]!==i||e[50]!==T||e[51]!==$||e[52]!==f?(Z=n.jsx(O.Suspense,{fallback:J,children:n.jsx(gi,{deploymentId:i,fetchKey:_,isPendingRefetch:f,isDeleteDisabled:$,onAfterDelete:T})}),e[48]=_,e[49]=i,e[50]=T,e[51]=$,e[52]=f,e[53]=Z):Z=e[53];let ee;e[54]!==a||e[55]!==b||e[56]!==M||e[57]!==Z?(ee=n.jsx(Wl,{ref:a,title:b,extra:M,styles:W,children:Z}),e[54]=a,e[55]=b,e[56]=M,e[57]=Z,e[58]=ee):ee=e[58];let Q;e[59]!==w||e[60]!==z.id||e[61]!==T||e[62]!==g||e[63]!==m||e[64]!==d||e[65]!==D||e[66]!==c?(Q=Ae=>{D(!1),Ae&&w({input:{modelDeploymentId:ll(z.id),expiresAt:Ae.expiresAt??new Date("2099-12-31").toISOString()}}).then(Ie=>{var Fe;const ie=(Fe=Ie.createAccessToken)==null?void 0:Fe.accessToken;ie&&C({token:ie.token,expiresAt:ie.expiresAt??null}),m.success({key:"access-token-created",content:c("deployment.accessToken.Created")}),T(),d==null||d()}).catch(Ie=>{const ie=Array.isArray(Ie)?Ie:[Ie];for(const Fe of ie)m.error((Fe==null?void 0:Fe.message)||c("dialog.ErrorOccurred"));g.error(Ie)})},e[59]=w,e[60]=z.id,e[61]=T,e[62]=g,e[63]=m,e[64]=d,e[65]=D,e[66]=c,e[67]=Q):Q=e[67];let ae;e[68]!==x||e[69]!==Q?(ae=n.jsx(fl,{children:n.jsx(yi,{open:x,confirmLoading:!1,onRequestClose:Q})}),e[68]=x,e[69]=Q,e[70]=ae):ae=e[70];const Se=K!==null;let ge;e[71]!==c?(ge=c("deployment.accessToken.Token"),e[71]=c,e[72]=ge):ge=e[72];let ye;e[73]===Symbol.for("react.memo_cache_sentinel")?(ye=()=>C(null),e[73]=ye):ye=e[73];let de;e[74]!==c?(de=c("deployment.accessToken.Created"),e[74]=c,e[75]=de):de=e[75];let pe;e[76]!==de?(pe=n.jsx(Xe.Text,{children:de}),e[76]=de,e[77]=pe):pe=e[77];let ue;e[78]!==K?(ue=K?n.jsx(jl,{copyable:{text:K.token},ellipsis:!0,code:!0,children:K.token}):null,e[78]=K,e[79]=ue):ue=e[79];let fe;e[80]!==K||e[81]!==c?(fe=K!=null&&K.expiresAt?n.jsx(Xe.Text,{type:"secondary",children:`${c("deployment.accessToken.Expiration")}: ${dl(K.expiresAt).format("ll LT")}`}):n.jsx(Xe.Text,{type:"secondary",children:c("deployment.accessToken.NoExpiration")}),e[80]=K,e[81]=c,e[82]=fe):fe=e[82];let ce;e[83]!==pe||e[84]!==ue||e[85]!==fe?(ce=n.jsxs(te,{direction:"column",align:"stretch",gap:"sm",children:[pe,ue,fe]}),e[83]=pe,e[84]=ue,e[85]=fe,e[86]=ce):ce=e[86];let ve;e[87]!==Se||e[88]!==ge||e[89]!==ce?(ve=n.jsx(fl,{children:n.jsx(Hl,{open:Se,destroyOnHidden:!0,title:ge,onCancel:ye,footer:null,width:520,children:ce})}),e[87]=Se,e[88]=ge,e[89]=ce,e[90]=ve):ve=e[90];let Ke;return e[91]!==ee||e[92]!==ae||e[93]!==ve?(Ke=n.jsxs(n.Fragment,{children:[ee,ae,ve]}),e[91]=ee,e[92]=ae,e[93]=ve,e[94]=Ke):Ke=e[94],Ke},gi=l=>{"use memo";var W,J,Z,ee;const e=We.c(71),{deploymentId:a,fetchKey:r,isPendingRefetch:t,isDeleteDisabled:i,onAfterDelete:d}=l,{t:s}=Je(),{message:u}=Pl.useApp(),{logger:o}=Ol(),[y,c]=O.useState(null),k=r===zl;let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=gt,e[0]=m):m=e[0];let g;e[1]!==a?(g={deploymentId:a},e[1]=a,e[2]=g):g=e[2];const f=k?"store-and-network":"network-only";let p;e[3]!==r||e[4]!==f?(p={fetchKey:r,fetchPolicy:f},e[3]=r,e[4]=f,e[5]=p):p=e[5];const{deployment:S}=Re.useLazyLoadQuery(m,g,p);let R;e[6]!==((W=S==null?void 0:S.accessTokens)==null?void 0:W.edges)?(R=Al((Z=(J=S==null?void 0:S.accessTokens)==null?void 0:J.edges)==null?void 0:Z.map(pi)),e[6]=(ee=S==null?void 0:S.accessTokens)==null?void 0:ee.edges,e[7]=R):R=e[7];const F=R;let x;e[8]===Symbol.for("react.memo_cache_sentinel")?(x=mt,e[8]=x):x=e[8];const[D,K]=Re.useMutation(x);let C;e[9]===Symbol.for("react.memo_cache_sentinel")?(C={x:"max-content"},e[9]=C):C=e[9];const _=t||K;let H;e[10]!==s?(H=s("deployment.accessToken.Token"),e[10]=s,e[11]=H):H=e[11];let z;e[12]!==i||e[13]!==s?(z=(Q,ae)=>ae?n.jsx(kn,{title:n.jsx(jl,{copyable:{text:ae.token},ellipsis:!0,style:{maxWidth:200},children:ae.token}),showActions:"always",actions:[{key:"delete",title:s("deployment.accessToken.Delete"),icon:n.jsx(Sn,{}),type:"danger",disabled:i,onClick:()=>c({id:ae.id,token:ae.token??""})}]}):"-",e[12]=i,e[13]=s,e[14]=z):z=e[14];let L;e[15]!==z||e[16]!==H?(L={key:"token",title:H,dataIndex:"token",render:z},e[15]=z,e[16]=H,e[17]=L):L=e[17];let w;e[18]!==s?(w=s("deployment.CreatedAt"),e[18]=s,e[19]=w):w=e[19];let V;e[20]!==w?(V={key:"createdAt",title:w,dataIndex:"createdAt",render:fi},e[20]=w,e[21]=V):V=e[21];let T;e[22]!==s?(T=s("deployment.accessToken.Expiration"),e[22]=s,e[23]=T):T=e[23];let E;e[24]!==s?(E=(Q,ae)=>ae!=null&&ae.expiresAt?dl(ae.expiresAt).format("ll LT"):s("deployment.accessToken.NoExpiration"),e[24]=s,e[25]=E):E=e[25];let $;e[26]!==T||e[27]!==E?($={key:"expiresAt",title:T,dataIndex:"expiresAt",render:E},e[26]=T,e[27]=E,e[28]=$):$=e[28];let Y;e[29]!==L||e[30]!==V||e[31]!==$?(Y=[L,V,$],e[29]=L,e[30]=V,e[31]=$,e[32]=Y):Y=e[32];let U;e[33]!==F||e[34]!==Y||e[35]!==_?(U=n.jsx(El,{scroll:C,rowKey:"id",loading:_,dataSource:F,pagination:!1,resizable:!0,columns:Y}),e[33]=F,e[34]=Y,e[35]=_,e[36]=U):U=e[36];const q=!!y;let B;e[37]!==s?(B=s("deployment.accessToken.Delete"),e[37]=s,e[38]=B):B=e[38];let j;e[39]!==s?(j=s("deployment.AccessToken"),e[39]=s,e[40]=j):j=e[40];let b;e[41]!==y?(b=y?[{key:y.id,label:y.id}]:[],e[41]=y,e[42]=b):b=e[42];let A;e[43]!==s?(A=s("data.folders.DeleteForeverConfirmText"),e[43]=s,e[44]=A):A=e[44];let P;e[45]!==s?(P=s("data.folders.DeleteForeverConfirmText"),e[45]=s,e[46]=P):P=e[46];let ne;e[47]!==P?(ne={placeholder:P},e[47]=P,e[48]=ne):ne=e[48];let le;e[49]!==K?(le={loading:K},e[49]=K,e[50]=le):le=e[50];let I;e[51]!==D||e[52]!==y||e[53]!==o||e[54]!==u||e[55]!==d||e[56]!==s?(I=()=>{y&&D({variables:{input:{id:ll(y.id)??y.id}},onCompleted:(Q,ae)=>{var Se;if(ae&&ae.length>0){o.error(ae[0]),u.error(((Se=ae[0])==null?void 0:Se.message)??s("dialog.ErrorOccurred"));return}u.success(s("deployment.accessToken.Deleted")),c(null),d()},onError:Q=>{o.error(Q),u.error(Q.message??s("dialog.ErrorOccurred"))}})},e[51]=D,e[52]=y,e[53]=o,e[54]=u,e[55]=d,e[56]=s,e[57]=I):I=e[57];let v;e[58]===Symbol.for("react.memo_cache_sentinel")?(v=()=>c(null),e[58]=v):v=e[58];let N;e[59]!==q||e[60]!==B||e[61]!==j||e[62]!==b||e[63]!==A||e[64]!==ne||e[65]!==le||e[66]!==I?(N=n.jsx(hn,{open:q,title:B,target:j,items:b,confirmText:A,requireConfirmInput:!0,inputProps:ne,okButtonProps:le,onOk:I,onCancel:v}),e[59]=q,e[60]=B,e[61]=j,e[62]=b,e[63]=A,e[64]=ne,e[65]=le,e[66]=I,e[67]=N):N=e[67];let M;return e[68]!==U||e[69]!==N?(M=n.jsxs(n.Fragment,{children:[U,N]}),e[68]=U,e[69]=N,e[70]=M):M=e[70],M},yi=l=>{"use memo";const e=We.c(64),{open:a,confirmLoading:r,onRequestClose:t}=l,{t:i}=Je(),[d]=oe.useForm(),s=oe.useWatch("expiryOption",d)??7;let u;e[0]!==d||e[1]!==t?(u=()=>{d.validateFields().then(B=>{let j;B.expiryOption==="none"?j=null:B.expiryOption==="custom"?j=B.datetime.toISOString():j=dl().add(B.expiryOption,"day").toISOString(),t({expiresAt:j})}).catch(ki)},e[0]=d,e[1]=t,e[2]=u):u=e[2];const o=u;let y;e[3]!==i?(y=i("general.Days",{num:7,defaultValue:"7 days"}),e[3]=i,e[4]=y):y=e[4];let c;e[5]!==y?(c={value:7,label:y},e[5]=y,e[6]=c):c=e[6];let k;e[7]!==i?(k=i("general.Days",{num:30,defaultValue:"30 days"}),e[7]=i,e[8]=k):k=e[8];let m;e[9]!==k?(m={value:30,label:k},e[9]=k,e[10]=m):m=e[10];let g;e[11]!==i?(g=i("general.Days",{num:90,defaultValue:"90 days"}),e[11]=i,e[12]=g):g=e[12];let f;e[13]!==g?(f={value:90,label:g},e[13]=g,e[14]=f):f=e[14];let p;e[15]!==i?(p=i("deployment.accessToken.CustomExpiration"),e[15]=i,e[16]=p):p=e[16];let S;e[17]!==p?(S={value:"custom",label:p},e[17]=p,e[18]=S):S=e[18];let R;e[19]!==i?(R=i("deployment.accessToken.NoExpiration"),e[19]=i,e[20]=R):R=e[20];let F;e[21]!==R?(F={value:"none",label:R},e[21]=R,e[22]=F):F=e[22];let x;e[23]!==F||e[24]!==c||e[25]!==m||e[26]!==f||e[27]!==S?(x=[c,m,f,S,F],e[23]=F,e[24]=c,e[25]=m,e[26]=f,e[27]=S,e[28]=x):x=e[28];const D=x;let K;e[29]!==i?(K=i("deployment.accessToken.Create"),e[29]=i,e[30]=K):K=e[30];let C;e[31]!==i?(C=i("deployment.accessToken.Create"),e[31]=i,e[32]=C):C=e[32];let _;e[33]!==t?(_=()=>t(),e[33]=t,e[34]=_):_=e[34];let H,z;e[35]===Symbol.for("react.memo_cache_sentinel")?(H={expiryOption:7,datetime:dl().add(7,"day")},z=["onChange","onBlur"],e[35]=H,e[36]=z):(H=e[35],z=e[36]);let L;e[37]!==i?(L=i("deployment.accessToken.Expiration"),e[37]=i,e[38]=L):L=e[38];let w;e[39]===Symbol.for("react.memo_cache_sentinel")?(w=[{required:!0}],e[39]=w):w=e[39];let V;e[40]===Symbol.for("react.memo_cache_sentinel")?(V={width:200},e[40]=V):V=e[40];let T;e[41]!==d?(T=B=>{typeof B=="number"&&d.setFieldValue("datetime",dl().add(B,"day"))},e[41]=d,e[42]=T):T=e[42];let E;e[43]!==D||e[44]!==T?(E=n.jsx(cn,{style:V,options:D,onChange:T}),e[43]=D,e[44]=T,e[45]=E):E=e[45];let $;e[46]!==L||e[47]!==E?($=n.jsx(oe.Item,{name:"expiryOption",label:L,rules:w,children:E}),e[46]=L,e[47]=E,e[48]=$):$=e[48];let Y;e[49]!==s||e[50]!==i?(Y=s==="custom"&&n.jsx(oe.Item,{name:"datetime",label:i("deployment.accessToken.CustomExpiration"),rules:[{type:"object",required:!0},()=>({validator(B,j){return j&&dl(j).isAfter(dl())?Promise.resolve():Promise.reject(new Error(i("dialog.ErrorOccurred")))}})],children:n.jsx(Yt,{showTime:!0,format:"YYYY-MM-DD HH:mm:ss",style:{width:"100%"}})}),e[49]=s,e[50]=i,e[51]=Y):Y=e[51];let U;e[52]!==d||e[53]!==$||e[54]!==Y?(U=n.jsxs(oe,{form:d,layout:"vertical",initialValues:H,validateTrigger:z,children:[$,Y]}),e[52]=d,e[53]=$,e[54]=Y,e[55]=U):U=e[55];let q;return e[56]!==r||e[57]!==o||e[58]!==a||e[59]!==K||e[60]!==C||e[61]!==_||e[62]!==U?(q=n.jsx(Hl,{open:a,destroyOnHidden:!0,centered:!0,width:420,title:K,okText:C,confirmLoading:r,onOk:o,onCancel:_,children:U}),e[56]=r,e[57]=o,e[58]=a,e[59]=K,e[60]=C,e[61]=_,e[62]=U,e[63]=q):q=e[63],q};function pi(l){return l==null?void 0:l.node}function fi(l,e){return e!=null&&e.createdAt?dl(e.createdAt).format("ll LT"):"-"}function ki(){}const ft=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"architecture"},e={defaultValue:null,kind:"LocalArgument",name:"reference"},a=[{alias:null,args:[{kind:"Variable",name:"architecture",variableName:"architecture"},{kind:"Variable",name:"reference",variableName:"reference"}],concreteType:"Image",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalManualImageQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,l],kind:"Operation",name:"DeploymentAddRevisionModalManualImageQuery",selections:a},params:{cacheID:"6bcc84ae2c2ac9e9606dddd37c2b9d15",id:null,metadata:{},name:"DeploymentAddRevisionModalManualImageQuery",operationKind:"query",text:`query DeploymentAddRevisionModalManualImageQuery(
  $reference: String!
  $architecture: String
) {
  image(reference: $reference, architecture: $architecture) {
    id
  }
}
`}}})();ft.hash="9a966eb2f1a961353ecfc61d58978716";const kt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],a={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"71af54781375e6ee4bceb1c73e74d088",id:null,metadata:{},name:"DeploymentAddRevisionModalImageNameQuery",operationKind:"query",text:`query DeploymentAddRevisionModalImageNameQuery(
  $id: ID!
) {
  imageV2(id: $id) {
    identity {
      canonicalName
      architecture
    }
    id
  }
}
`}}})();kt.hash="7f7c91d5e401085de1ab4d56ffb2ef9b";const St=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},t={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},d=[a,r],s={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},o={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},y={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},m=[c,k],g={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null}],storageKey:null},f={alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,a],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},k,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},a],storageKey:null}],storageKey:null}],storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},R={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},F={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,S,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},R],storageKey:null},x={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[p,S,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},R],storageKey:null},D={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},K={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},C=[a,s,u,o,y,g,f,F,x,D,K];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[a,r,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,t,i,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:d,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[a,s,u,o,y,g,f,F,x,D,K,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,t,i,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:C,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:C,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"97d46eaffe190c0a696e6d7daacc3529",id:null,metadata:{},name:"DeploymentAddRevisionModalAddMutation",operationKind:"mutation",text:`mutation DeploymentAddRevisionModalAddMutation(
  $input: AddRevisionInput!
) {
  addModelRevision(input: $input) {
    revision {
      id
      ...DeploymentRevisionDetail_revision
      deployment @since(version: "26.4.4") {
        id
        currentRevisionId
        deployingRevisionId
        currentRevision @since(version: "26.4.3") {
          id
          ...DeploymentRevisionDetail_revision
        }
        deployingRevision @since(version: "26.4.3") {
          id
          ...DeploymentRevisionDetail_revision
        }
      }
    }
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
      architecture
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}})();St.hash="889773e313c63748043b8294cd2bb0b0";const ht=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},a=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:a},params:{cacheID:"6728695a02d457f55b4cd4d3323823d8",id:null,metadata:{},name:"DeploymentAddRevisionModalSelectedPresetQuery",operationKind:"query",text:`query DeploymentAddRevisionModalSelectedPresetQuery(
  $id: UUID!
) {
  deploymentRevisionPreset(id: $id) {
    id
    runtimeVariantId
    cluster {
      clusterMode
      clusterSize
    }
    execution {
      imageId
      environ {
        key
        value
      }
    }
    resource {
      resourceOpts {
        name
        value
      }
    }
    resourceSlots {
      slotName
      quantity
    }
  }
}
`}}})();ht.hash="e9d60ac2d9540dae9c821fe3abd4b65e";const vt=(function(){var l=[{alias:null,args:[{kind:"Literal",name:"first",value:1},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"RANK"}]}],concreteType:"DeploymentRevisionPresetConnection",kind:"LinkedField",name:"deploymentRevisionPresets",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:'deploymentRevisionPresets(first:1,orderBy:[{"direction":"ASC","field":"RANK"}])'}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetCountQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAddRevisionModalPresetCountQuery",selections:l},params:{cacheID:"edaa5efa78debd74168a24185822d633",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetCountQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetCountQuery {
  deploymentRevisionPresets(orderBy: [{field: RANK, direction: "ASC"}], first: 1) {
    count
  }
}
`}}})();vt.hash="4461df1967b1117642d3190b36d5cb33";const Ft=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},a=[l,e],r={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_revisionSource",selections:[{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:a,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[r,t],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[l],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:a,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[r,t,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelRevision",abstractKey:null}})();Ft.hash="94f9806003b984d4534543e7895a61e8";const xt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],type:"ModelDeployment",abstractKey:null};xt.hash="614548b7fde80b4972dfb192b893b832";const Rt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentPresetDetailModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[a,r,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[a,r],storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startupCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"bootstrapScript",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"image",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[r,t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetDeploymentDefaults",kind:"LinkedField",name:"deploymentDefaults",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"replicaCount",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"revisionHistoryLimit",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentStrategy",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValueEntry",kind:"LinkedField",name:"presetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},t],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"ccd4b84ef4b7bf255f7a95f4bbbacd00",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetDetailQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetDetailQuery(
  $id: UUID!
) {
  deploymentRevisionPreset(id: $id) {
    ...DeploymentPresetDetailModalFragment
    id
  }
}

fragment DeploymentPresetDetailModalFragment on DeploymentRevisionPreset {
  id
  name
  description
  runtimeVariantId
  runtimeVariant {
    id
    name
  }
  cluster {
    clusterMode
    clusterSize
  }
  execution {
    imageId
    startupCommand
    bootstrapScript
    environ {
      key
      value
    }
  }
  image @since(version: "26.4.4") {
    id
    identity {
      canonicalName
    }
  }
  resource {
    resourceOpts {
      name
      value
    }
  }
  resourceSlots {
    slotName
    quantity
  }
  deploymentDefaults {
    openToPublic
    replicaCount
    revisionHistoryLimit
    deploymentStrategy
  }
  presetValues @since(version: "26.4.4rc9") {
    presetId
    value
  }
  modelDefinition {
    models {
      name
      service {
        healthCheck {
          enable @since(version: "26.4.4rc7")
          interval
          path
          maxRetries
          maxWaitTime
          expectedStatusCode
          initialDelay
        }
      }
    }
  }
}
`}}})();Rt.hash="8f60ae6bcf0fa60919e80838391f66f9";const sn=({children:l})=>{const{token:e}=Dl.useToken();return n.jsx(zn,{titlePlacement:"left",children:n.jsx(Xe.Text,{type:"secondary",style:{fontSize:e.fontSizeSM},children:l})})},Si=l=>{"use memo";const e=We.c(6),{presetId:a,onCancel:r}=l;let t;e[0]===Symbol.for("react.memo_cache_sentinel")?(t=Rt,e[0]=t):t=e[0];let i;e[1]!==a?(i={id:a},e[1]=a,e[2]=i):i=e[2];const d=Re.useLazyLoadQuery(t,i);let s;return e[3]!==d.deploymentRevisionPreset||e[4]!==r?(s=n.jsx(da,{open:!0,presetFrgmt:d.deploymentRevisionPreset,onCancel:r}),e[3]=d.deploymentRevisionPreset,e[4]=r,e[5]=s):s=e[5],s},bt=({onRequestClose:l,deploymentFrgmt:e,sourceRevisionFrgmt:a,open:r,...t})=>{"use memo";var Ge,Ye,Ze;const{t:i}=Je(),{token:d}=Dl.useToken(),{message:s}=Pl.useApp(),u=Re.useRelayEnvironment(),o=Re.useFragment(xt,e),y=Ft,c=Re.useFragment(y,(o==null?void 0:o.currentRevision)??null),k=Re.useFragment(y,a??null),{id:m}=Qn(),{logger:g}=Ol(),{open:f}=Xt(),p=vn(),S=p.supports("model-health-check-enable"),R=p.supports("model-runtime-variant-preset-values"),F=O.useRef(null),x=O.useRef(null),[D,K]=O.useState(!1),[C]=oe.useForm(),[_]=oe.useForm(),[H,z]=O.useState(!0),[L,w]=O.useState(!1),[V,T]=Cl("deploymentRevisionCreationMode"),E=V??"preset",[$,Y]=O.useState(!1),[U,q]=O.useState(!1),[B,j]=O.useState(!1),[b,A]=O.useState(null),[P,ne]=O.useState(null),[le,I]=O.useState(null),[v,N]=O.useState({}),M=O.useRef(new Set),W=O.useRef(null),[J,Z]=O.useState(void 0),ee=O.useRef({}),[Q,ae]=O.useState(void 0);O.useEffect(()=>{if(!r)return;let h=!1;return Re.fetchQuery(u,vt,{},{fetchPolicy:"store-or-network"}).toPromise().then(G=>{var X;h||ae((((X=G==null?void 0:G.deploymentRevisionPresets)==null?void 0:X.count)??0)===0)}).catch(()=>{h||ae(!1)}),()=>{h=!0}},[r,u]);const Se=(Ye=(Ge=o==null?void 0:o.currentRevision)==null?void 0:Ge.modelMountConfig)!=null&&Ye.vfolderId?ql("VirtualFolderNode",o.currentRevision.modelMountConfig.vfolderId):void 0,ge=O.useRef(new Map),ye=async h=>{const G=ge.current.get(h);if(G)return G;const X=await Re.fetchQuery(u,ht,{id:h},{fetchPolicy:"store-or-network"}).toPromise(),se=(X==null?void 0:X.deploymentRevisionPreset)??null;return se&&ge.current.set(h,se),se},[de,pe]=Re.useMutation(St),ue=async h=>{var Be,he,we,$e,Qe,_e,qe,el;const G=h.resourceSlots??[],X=G.find(Me=>Me.slotName==="cpu"),se=G.find(Me=>Me.slotName==="mem"),re=G.find(Me=>Me.slotName!=="cpu"&&Me.slotName!=="mem"),me=(((Be=h.resource)==null?void 0:Be.resourceOpts)??[]).find(Me=>Me.name==="shmem"),Ce=((he=h.cluster)==null?void 0:he.clusterMode)==="SINGLE_NODE"?"single-node":"multi-node";let Pe;if((we=h.execution)!=null&&we.imageId)try{const Me=await Re.fetchQuery(u,kt,{id:h.execution.imageId},{fetchPolicy:"store-or-network"}).toPromise(),ze=($e=Me==null?void 0:Me.imageV2)==null?void 0:$e.identity;Pe=ze!=null&&ze.canonicalName?ze.architecture?`${ze.canonicalName}@${ze.architecture}`:ze.canonicalName:void 0}catch{Pe=void 0}const Oe=(((Qe=h.execution)==null?void 0:Qe.environ)??[]).map(Me=>({variable:Me.key,value:Me.value}));return{cluster_mode:Ce,cluster_size:((_e=h.cluster)==null?void 0:_e.clusterSize)??1,allocationPreset:"custom",resource:{cpu:X?Number(X.quantity):0,mem:((qe=Jl(String((se==null?void 0:se.quantity)??"0"),"g",2))==null?void 0:qe.value)??"0g",shmem:((el=Jl((me==null?void 0:me.value)??Xl,"g",2))==null?void 0:el.value)??Xl,...re?{acceleratorType:re.slotName,accelerator:re.slotName==="cuda.shares"?parseFloat(String(re.quantity)):parseInt(String(re.quantity),10)}:{}},enabledAutomaticShmem:!me,runtimeVariantId:h.runtimeVariantId??void 0,environ:Oe,...Pe?{environments:{version:Pe}}:{}}},fe=async h=>{if(h===E)return;if(E==="preset"&&h==="custom"){const se=_.getFieldsValue(),re=se.revisionPresetId;let me={};if(re){const Ce=await ye(re);Ce&&(me=await ue(Ce))}se.modelFolderId&&(me.modelFolderId=se.modelFolderId),A(Object.keys(me).length>0?me:null),T("custom");return}const G=C.getFieldsValue(),X={};G.modelFolderId&&(X.modelFolderId=G.modelFolderId),C.resetFields(),A(null),ne(Object.keys(X).length>0?X:null),T("preset")},ce=h=>{var $e,Qe,_e,qe,el,Me,ze,ul,al,il,sl,ol,be,xe,Le,Ue,Sl,ke,De,rl,Ee,nl,yl,Ml,bl;const G=h.resourceSlots??[],X=G.find(Ne=>Ne.slotName==="cpu"),se=G.find(Ne=>Ne.slotName==="mem"),re=G.find(Ne=>Ne.slotName!=="cpu"&&Ne.slotName!=="mem"),me=(((Qe=($e=h.resourceConfig)==null?void 0:$e.resourceOpts)==null?void 0:Qe.entries)??[]).find(Ne=>Ne.name==="shmem"),Ce=((qe=(_e=h.modelRuntimeConfig)==null?void 0:_e.runtimeVariant)==null?void 0:qe.name)??"",Pe=Ce==="custom",Oe=(el=h.modelRuntimeConfig)==null?void 0:el.runtimeVariantId;Oe&&Ce&&N(Ne=>({...Ne,[Oe]:Ce}));const Ve=(ul=(ze=(Me=h.modelDefinition)==null?void 0:Me.models)==null?void 0:ze[0])==null?void 0:ul.service,Be=(sl=(il=(al=h.modelDefinition)==null?void 0:al.models)==null?void 0:il[0])==null?void 0:sl.modelPath,he=Ve!=null&&Ve.healthCheck&&Ve.healthCheck.enable!==!1?Ve.healthCheck:void 0,we=Pe&&!!Ve&&(((ol=Ve.startCommand)==null?void 0:ol.length)??0)>0;if(ee.current=Cn((h.extraMounts??[]).filter(Ne=>!!Ne.mountDestination).map(Ne=>[Ne.vfolderId.replace(/-/g,""),Ne.mountDestination])),!Pe&&Ce){const Ne=(be=h.modelRuntimeConfig)==null?void 0:be.runtimeVariantPresetValues;Z(Ne&&Ne.length>0?Ne.map(Kn=>({presetId:Kn.presetId,value:Kn.value})):void 0)}C.setFieldsValue({cluster_mode:((xe=h.clusterConfig)==null?void 0:xe.mode)==="SINGLE_NODE"?"single-node":"multi-node",cluster_size:((Le=h.clusterConfig)==null?void 0:Le.size)??1,allocationPreset:"custom",resource:{cpu:X?Number(X.quantity):0,mem:((Ue=Jl(String((se==null?void 0:se.quantity)??"0"),"g",2))==null?void 0:Ue.value)??"0g",shmem:((Sl=Jl((me==null?void 0:me.value)??Xl,"g",2))==null?void 0:Sl.value)??Xl,...re?{acceleratorType:re.slotName,accelerator:re.slotName==="cuda.shares"?parseFloat(String(re.quantity)):parseInt(String(re.quantity),10)}:{}},enabledAutomaticShmem:!me,mount_ids:(h.extraMounts??[]).map(Ne=>Ne.vfolderId.replace(/-/g,"")),mount_id_map:Cn((h.extraMounts??[]).filter(Ne=>!!Ne.mountDestination).map(Ne=>[Ne.vfolderId.replace(/-/g,""),Ne.mountDestination])),runtimeVariantId:((ke=h.modelRuntimeConfig)==null?void 0:ke.runtimeVariantId)??void 0,modelFolderId:(De=h.modelMountConfig)!=null&&De.vfolderId?ql("VirtualFolderNode",h.modelMountConfig.vfolderId):void 0,mountDestination:((rl=h.modelMountConfig)==null?void 0:rl.mountDestination)??"/models",definitionPath:((Ee=h.modelMountConfig)==null?void 0:Ee.definitionPath)??void 0,environments:(yl=(nl=h.imageV2)==null?void 0:nl.identity)!=null&&yl.canonicalName?{version:h.imageV2.identity.architecture?`${h.imageV2.identity.canonicalName}@${h.imageV2.identity.architecture}`:h.imageV2.identity.canonicalName}:void 0,environ:(((bl=(Ml=h.modelRuntimeConfig)==null?void 0:Ml.environ)==null?void 0:bl.entries)??[]).map(Ne=>({variable:Ne.name,value:Ne.value})),commandEnableHealthCheck:!!he,commandHealthCheck:(he==null?void 0:he.path)??void 0,commandInitialDelay:(he==null?void 0:he.initialDelay)??void 0,commandMaxRetries:(he==null?void 0:he.maxRetries)??void 0,commandInterval:(he==null?void 0:he.interval)??void 0,commandMaxWaitTime:(he==null?void 0:he.maxWaitTime)??void 0,commandExpectedStatusCode:(he==null?void 0:he.expectedStatusCode)??void 0,...we&&Ve?{customDefinitionMode:"command",startCommand:Na(Ve.startCommand??[]),commandPort:Ve.port,commandModelMount:Be??"/models"}:Pe?{customDefinitionMode:"file"}:{}})},ve=O.useEffectEvent(()=>{b&&(C.setFieldsValue(b),A(null))}),Ke=O.useEffectEvent(()=>{P&&(_.setFieldsValue(P),ne(null))}),Te=O.useEffectEvent(()=>{U||k&&(ce(k),q(!0))}),Ae=O.useEffectEvent(()=>{B&&c&&(ce(c),j(!1),Y(!0),s.success(i("deployment.CurrentRevisionConfigurationLoaded")))});O.useEffect(()=>{E==="custom"?(ve(),Te(),Ae()):Ke()},[E]);const Ie=()=>{if(c){if(E==="custom"){ce(c),Y(!0),s.success(i("deployment.CurrentRevisionConfigurationLoaded"));return}j(!0),T("custom")}},ie=h=>{const G=W.current;if(!G||!h)return[];const X={};for(const[se,re]of Object.entries(h))re==null||re===""||(X[se]=String(re));return Ea(G,X,M.current)},Fe=()=>{requestAnimationFrame(()=>{const h=document.querySelector(".ant-modal-body .ant-form-item-has-error");h&&h.scrollIntoView({behavior:"smooth",block:"start"})})},je=async h=>{var al,il,sl,ol,be;const G=(xe,Le)=>{C.setFields([{name:xe,errors:[i(Le)]}]),C.scrollToField(xe,{behavior:"smooth",block:"center"})};let X=(il=(al=h.environments)==null?void 0:al.image)==null?void 0:il.id;const se=(ol=(sl=h.environments)==null?void 0:sl.manual)==null?void 0:ol.trim(),re=se?["environments","manual"]:["environments","version"];if(!X&&se){const[xe,Le]=se.split("@");w(!0);try{const Ue=await Re.fetchQuery(u,ft,{reference:xe,architecture:Le||null},{fetchPolicy:"network-only"}).toPromise();X=((be=Ue==null?void 0:Ue.image)==null?void 0:be.id)??void 0}catch(Ue){g.error("[DeploymentAddRevisionModal] failed to resolve manual image reference",Ue),s.error(i("general.ErrorOccurred"));return}finally{w(!1)}if(!X){G(re,"modelService.ManualImageNotFound");return}}if(!X){G(re,"modelService.ImageRequired");return}const me=Vl(X);if(!me){G(re,"modelService.ImageRequired");return}const Ce=[{resourceType:"cpu",quantity:String(h.resource.cpu)},{resourceType:"mem",quantity:h.resource.mem}];h.resource.acceleratorType&&h.resource.accelerator&&h.resource.accelerator>0&&Ce.push({resourceType:h.resource.acceleratorType,quantity:String(h.resource.accelerator)});const Pe=[];h.resource.shmem&&Pe.push({name:"shmem",value:h.resource.shmem});const Oe=h.cluster_mode==="single-node"||h.cluster_mode==="multi-node"&&h.cluster_size===1?"SINGLE_NODE":"MULTI_NODE",Ve=h.vfoldersNameMap??{},Be=(h.mount_ids??[]).map(xe=>{var Ue;const Le=((Ue=h.mount_id_map)==null?void 0:Ue[xe])||ee.current[xe]||(Ve[xe]?`/home/work/${Ve[xe]}`:`/home/work/${xe}`);return{vfolderId:oa(xe),mountDestination:Le}}),we=(v[h.runtimeVariantId]??"")==="custom",$e=h.customDefinitionMode==="command",Qe={};for(const{variable:xe,value:Le}of h.environ??[])xe&&(Qe[xe]=Le);const _e=Object.entries(Qe).map(([xe,Le])=>({name:xe,value:Le})),qe=!!h.commandEnableHealthCheck,el=(()=>{const xe={path:h.commandHealthCheck,interval:h.commandInterval,maxRetries:h.commandMaxRetries,maxWaitTime:h.commandMaxWaitTime,initialDelay:h.commandInitialDelay,expectedStatusCode:h.commandExpectedStatusCode};return S?qe?{enable:!0,...xe}:{enable:!1}:qe?xe:null})(),Me=we||!R?[]:ie(h.runtimeParams),ze=we&&$e&&h.startCommand?{models:[{name:"model",modelPath:h.commandModelMount??"/models",service:{preStartActions:[],startCommand:Va(h.startCommand??""),port:h.commandPort??8e3,healthCheck:el}}]}:qe?{models:[{service:{healthCheck:el}}]}:null,ul=we&&$e?h.commandModelMount??"/models":h.mountDestination||"/models";de({variables:{input:{deploymentId:ll((o==null?void 0:o.id)??"")??(o==null?void 0:o.id)??"",clusterConfig:{mode:Oe,size:h.cluster_size},resourceConfig:{resourceSlots:{entries:Ce},resourceOpts:Pe.length>0?{entries:Pe}:null},image:{id:me},modelRuntimeConfig:{runtimeVariantId:h.runtimeVariantId,environ:_e.length>0?{entries:_e}:null,...R&&{runtimeVariantPresetValues:Me.length>0?Me:null}},modelMountConfig:{vfolderId:ll(h.modelFolderId),mountDestination:ul,definitionPath:h.definitionPath},modelDefinition:ze,extraMounts:Be.length>0?Be:null,options:{autoActivate:H}}},onCompleted:(xe,Le)=>{var Ue,Sl;if(Le&&Le.length>0){const ke=Le[0],De=(Ue=ke==null?void 0:ke.message)==null?void 0:Ue.includes("Another deployment is already in progress");s.error(De?i("deployment.AnotherDeploymentInProgress"):(ke==null?void 0:ke.message)??i("general.ErrorOccurred"));return}C.resetFields(),s.success(i("deployment.RevisionAdded")),l(!0,(Sl=xe.addModelRevision)==null?void 0:Sl.revision)},onError:xe=>{var Ue;const Le=(Ue=xe.message)==null?void 0:Ue.includes("Another deployment is already in progress");s.error(Le?i("deployment.AnotherDeploymentInProgress"):xe.message??i("general.ErrorOccurred"))}})},He=h=>{de({variables:{input:{deploymentId:ll((o==null?void 0:o.id)??"")??(o==null?void 0:o.id)??"",revisionPresetId:h.revisionPresetId,modelMountConfig:{vfolderId:ll(h.modelFolderId),mountDestination:"/models"},options:{autoActivate:H}}},onCompleted:(G,X)=>{var se,re;if(X&&X.length>0){const me=X[0],Ce=(se=me==null?void 0:me.message)==null?void 0:se.includes("Another deployment is already in progress");g.error("[DeploymentAddRevisionModal] addModelRevision (preset) returned errors",X),s.error(Ce?i("deployment.AnotherDeploymentInProgress"):(me==null?void 0:me.message)??i("general.ErrorOccurred"));return}_.resetFields(),s.success(i("deployment.RevisionAdded")),l(!0,(re=G.addModelRevision)==null?void 0:re.revision)},onError:G=>{var se;const X=(se=G.message)==null?void 0:se.includes("Another deployment is already in progress");g.error("[DeploymentAddRevisionModal] addModelRevision (preset) failed",G),s.error(X?i("deployment.AnotherDeploymentInProgress"):G.message??i("general.ErrorOccurred"))}})},tl=async()=>{const h=E==="preset"?_:C;try{await h.validateFields()}catch{Fe();return}h.submit()};return n.jsxs(Hl,{open:r,title:n.jsxs(te,{direction:"row",align:"center",justify:"between",gap:"md",wrap:"wrap",style:{paddingRight:d.paddingLG},children:[n.jsx("span",{children:i("deployment.AddRevision")}),n.jsx(Dn,{value:E,onChange:fe,options:[{label:i("deployment.PresetMode"),value:"preset"},{label:i("deployment.CustomMode"),value:"custom"}],style:{fontWeight:"normal"}})]}),width:720,footer:n.jsxs(te,{direction:"row",align:"center",justify:"between",gap:"sm",children:[n.jsx(In,{checked:H,onChange:h=>z(h.target.checked),disabled:E==="preset"&&Q,children:i("deployment.AutoApply")}),n.jsxs(te,{direction:"row",align:"center",gap:"xs",children:[n.jsx(ml,{onClick:()=>l(),children:i("button.Cancel")}),n.jsx(ml,{type:"primary",loading:pe||L,onClick:tl,disabled:E==="preset"&&Q,children:i("deployment.AddRevision")})]})]}),onCancel:()=>l(),confirmLoading:pe||L,destroyOnHidden:!0,...t,children:[c&&!a&&!$?n.jsx(Tl,{type:"info",showIcon:!0,style:{marginBottom:d.marginMD},title:i("deployment.CurrentRevisionAvailableDescription"),action:n.jsx(ml,{size:"small",onClick:Ie,children:i("deployment.LoadCurrentRevision")})}):null,E==="preset"?Q?n.jsx(Tl,{type:"info",showIcon:!0,style:{marginTop:d.marginXS},title:i("deployment.NoPresetsAvailable"),description:i("deployment.NoPresetsAvailableSwitchToCustom")}):n.jsxs(oe,{form:_,layout:"vertical",style:{marginTop:d.marginXS},onFinish:He,onFinishFailed:Fe,initialValues:{modelFolderId:Se},children:[n.jsx(oe.Item,{label:i("modelStore.Preset"),tooltip:i("modelStore.PresetTooltip"),required:!0,children:n.jsxs(te,{direction:"row",gap:"xs",children:[n.jsx(O.Suspense,{fallback:n.jsx(Yl,{loading:!0,style:{flex:1}}),children:n.jsx(oe.Item,{name:"revisionPresetId",noStyle:!0,rules:[{required:!0}],children:n.jsx(Jt,{style:{flex:1}})})}),n.jsx(oe.Item,{dependencies:["revisionPresetId"],noStyle:!0,children:({getFieldValue:h})=>{const G=h("revisionPresetId");return n.jsx(Ql.Compact,{children:n.jsx(cl,{title:i("modelService.DeploymentPresetDetail"),children:n.jsx(ml,{icon:n.jsx(Zt,{}),disabled:!G,onClick:()=>{G&&I(G)}})})})}})]})}),n.jsx(oe.Item,{label:i("deployment.ModelFolder"),tooltip:i("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(te,{direction:"row",gap:"xs",children:[n.jsx(O.Suspense,{fallback:n.jsx(Yl,{loading:!0,style:{flex:1}}),children:n.jsx(oe.Item,{name:"modelFolderId",label:i("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(jn,{ref:F,currentProjectId:m??void 0,disabled:!m,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(oe.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:h})=>{const G=h("modelFolderId");return n.jsxs(Ql.Compact,{children:[n.jsx(cl,{title:i("modelService.OpenFolder"),children:n.jsx(ml,{icon:n.jsx(Pn,{}),disabled:!G,onClick:()=>{G&&f(ll(G))}})}),n.jsx(cl,{title:i("data.CreateANewStorageFolder"),children:n.jsx(ml,{icon:n.jsx(Ll,{}),onClick:()=>K(!0)})}),n.jsx(cl,{title:i("button.Refresh"),children:n.jsx(ml,{icon:n.jsx(Tn,{}),onClick:()=>{O.startTransition(()=>{var X;(X=F.current)==null||X.refetch()})}})})]})}})]})})]},"preset-form"):n.jsxs(oe,{form:C,layout:"vertical",style:{marginTop:d.marginXS},onFinish:je,onFinishFailed:Fe,initialValues:ia({},sa,{resourceGroup:(Ze=o==null?void 0:o.metadata)==null?void 0:Ze.resourceGroupName,customDefinitionMode:"command",commandEnableHealthCheck:!1,environ:[]}),children:[n.jsx(sn,{children:i("deployment.step.ModelAndRuntime")}),n.jsx(oe.Item,{label:i("deployment.ModelFolder"),tooltip:i("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(te,{direction:"row",gap:"xs",children:[n.jsx(O.Suspense,{fallback:n.jsx(Yl,{loading:!0,style:{flex:1}}),children:n.jsx(oe.Item,{name:"modelFolderId",label:i("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(jn,{ref:x,currentProjectId:m??void 0,disabled:!m,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(oe.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:h})=>{const G=h("modelFolderId");return n.jsxs(Ql.Compact,{children:[n.jsx(cl,{title:i("modelService.OpenFolder"),children:n.jsx(ml,{icon:n.jsx(Pn,{}),disabled:!G,onClick:()=>{G&&f(ll(G))}})}),n.jsx(cl,{title:i("data.CreateANewStorageFolder"),children:n.jsx(ml,{icon:n.jsx(Ll,{}),onClick:()=>K(!0)})}),n.jsx(cl,{title:i("button.Refresh"),children:n.jsx(ml,{icon:n.jsx(Tn,{}),onClick:()=>{O.startTransition(()=>{var X;(X=x.current)==null||X.refetch()})}})})]})}})]})}),n.jsx(O.Suspense,{fallback:n.jsx(Yl,{loading:!0,style:{width:"100%"}}),children:n.jsx(oe.Item,{name:"runtimeVariantId",label:i("deployment.RuntimeVariant"),tooltip:i("deployment.RuntimeVariantTooltip"),rules:[{required:!0},{warningOnly:!0,validator:async(h,G)=>{const X=v[G];return X&&X!=="custom"?Promise.reject(i("modelService.RuntimeVariantDefaultCommandAppliedNote")):Promise.resolve()}}],children:n.jsx(Oa,{onResolvedNamesChange:h=>N(G=>({...G,...h}))})})}),n.jsx(oe.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:h})=>{const G=h("runtimeVariantId"),X=v[G];return!X||X==="custom"?null:n.jsx("div",{style:{marginBottom:d.marginMD},children:n.jsx(O.Suspense,{fallback:null,children:n.jsx(_a,{runtimeVariant:X,onTouchedKeysChange:se=>{M.current=se},onGroupsLoaded:se=>{W.current=se},initialPresetValues:J})})})}}),n.jsx(oe.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:h})=>{const G=h("runtimeVariantId");return v[G]!=="custom"?null:n.jsxs(n.Fragment,{children:[n.jsx(oe.Item,{name:"customDefinitionMode",noStyle:!0,children:n.jsx(Dn,{options:[{label:i("modelService.EnterCommand"),value:"command"},{label:i("modelService.UseConfigFile"),value:"file"}],style:{marginBottom:d.marginMD}})}),n.jsx(oe.Item,{dependencies:["customDefinitionMode"],noStyle:!0,children:({getFieldValue:se})=>se("customDefinitionMode")==="command"?n.jsxs(n.Fragment,{children:[n.jsx(oe.Item,{name:"startCommand",label:i("modelService.StartCommand"),tooltip:i("modelService.StartCommandTooltip"),extra:i("modelService.StartCommandHelperShell"),rules:[{required:!0,whitespace:!0}],children:n.jsx(Bl.TextArea,{placeholder:i("modelService.StartCommandPlaceholder"),autoSize:{minRows:2}})}),n.jsx(oe.Item,{name:"commandModelMount",label:i("modelService.ModelMountDestination"),tooltip:i("modelService.ModelMountTooltip"),children:n.jsx(Bl,{placeholder:"/models",allowClear:!0})}),n.jsx(oe.Item,{name:"commandPort",label:i("modelService.Port"),tooltip:i("modelService.PortTooltip"),children:n.jsx(gl,{min:2,max:65535,placeholder:"8000",style:{width:"100%"}})})]}):n.jsxs(te,{gap:"sm",children:[n.jsx(oe.Item,{name:"mountDestination",label:i("modelService.ModelMountDestination"),tooltip:i("modelService.ModelMountTooltip"),rules:[{required:!0}],style:{flex:1},children:n.jsx(Bl,{allowClear:!0,placeholder:"/models"})}),n.jsx(oe.Item,{name:"definitionPath",label:i("deployment.ModelDefinitionPath"),tooltip:i("modelService.ModelDefinitionPathTooltip"),style:{flex:1},children:n.jsx(Bl,{allowClear:!0,placeholder:"model-definition.yaml"})})]})})]})}}),n.jsx(oe.Item,{name:"commandEnableHealthCheck",valuePropName:"checked",style:{marginBottom:d.marginXS},children:n.jsx(In,{children:i("modelService.EnableHealthCheck")})}),n.jsx(oe.Item,{dependencies:["commandEnableHealthCheck"],noStyle:!0,children:({getFieldValue:h})=>h("commandEnableHealthCheck")?n.jsxs(te,{direction:"column",align:"stretch",gap:"xs",children:[n.jsx(oe.Item,{name:"commandHealthCheck",label:i("adminDeploymentPreset.modelDef.HealthCheckPath"),tooltip:i("modelService.HealthCheckTooltip"),rules:[{required:!0}],children:n.jsx(Bl,{placeholder:i("general.Example",{value:"/health"}),allowClear:!0})}),n.jsxs(te,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(oe.Item,{name:"commandInterval",label:i("adminDeploymentPreset.modelDef.HealthCheckInterval"),tooltip:i("modelService.IntervalTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:1,placeholder:i("general.Example",{value:"10"}),suffix:i("time.Sec"),style:{width:"100%"}})}),n.jsx(oe.Item,{name:"commandMaxRetries",label:i("adminDeploymentPreset.modelDef.HealthCheckMaxRetries"),tooltip:i("modelService.MaxRetriesTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:1,placeholder:i("general.Example",{value:"10"}),style:{width:"100%"}})}),n.jsx(oe.Item,{name:"commandMaxWaitTime",label:i("adminDeploymentPreset.modelDef.HealthCheckMaxWaitTime"),tooltip:i("modelService.MaxWaitTimeTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:1,placeholder:i("general.Example",{value:"15"}),suffix:i("time.Sec"),style:{width:"100%"}})})]}),n.jsxs(te,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(oe.Item,{name:"commandExpectedStatusCode",label:i("adminDeploymentPreset.modelDef.HealthCheckExpectedStatus"),tooltip:i("modelService.ExpectedStatusTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:101,max:599,placeholder:i("general.Example",{value:"200"}),style:{width:"100%"}})}),n.jsx(oe.Item,{name:"commandInitialDelay",label:i("adminDeploymentPreset.modelDef.HealthCheckInitialDelay"),tooltip:i("modelService.InitialDelayTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:0,placeholder:i("general.Example",{value:"60"}),suffix:i("time.Sec"),style:{width:"100%"}})}),n.jsx("div",{style:{flex:1,minWidth:160}})]})]}):null}),n.jsx(sn,{children:i("session.launcher.Environments")}),n.jsx(O.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:2}}),children:n.jsx(ea,{})}),n.jsx(la,{name:"environ",formItemProps:{validateTrigger:["onChange","onBlur"]}}),n.jsx(sn,{children:i("deployment.step.ClusterAndResources")}),n.jsx(O.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:4}}),children:n.jsx(na,{enableResourcePresets:!0,hideResourceGroupFormItem:!0})}),n.jsx(ta,{items:[{key:"advanced",label:i("session.launcher.AdvancedSettings"),children:n.jsx(O.Suspense,{fallback:n.jsx(xl,{active:!0}),children:n.jsx(oe.Item,{noStyle:!0,dependencies:["modelFolderId","mount_id_map","mount_ids"],children:({getFieldValue:h})=>{var se;const G=h("modelFolderId"),X=G?(se=Vl(String(G)))==null?void 0:se.replace(/-/g,""):void 0;return n.jsx(aa,{label:i("modelService.AdditionalMounts"),tooltip:i("modelService.AdditionalMountsTooltip"),rowKey:"id",tableProps:{scroll:{x:"max-content",y:300}},rowFilter:re=>{var me;return re.usage_mode!=="model"&&re.status==="ready"&&!((me=re.name)!=null&&me.startsWith("."))&&re.id!==X}})}})})}]})]},"custom-form"),le&&n.jsx(O.Suspense,{fallback:null,children:n.jsx(Si,{presetId:le,onCancel:()=>I(null)})}),n.jsx(ra,{open:D,initialValues:{usage_mode:"model"},onRequestClose:h=>{if(K(!1),h!=null&&h.id){const G=Vl(h.id);if(!G)return;const X=ql("VirtualFolderNode",G),se=E==="preset"?_:C,re=E==="preset"?F:x;se.setFieldValue("modelFolderId",X),O.startTransition(()=>{var me;(me=re.current)==null||me.refetch()})}}})]})},Kt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAutoScalingRulePayload",kind:"LinkedField",name:"deleteAutoScalingRule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAutoScalingCardDeleteMutation",selections:e},params:{cacheID:"1b7b8f1adf6afd81d338607d63841181",id:null,metadata:{},name:"DeploymentAutoScalingCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAutoScalingCardDeleteMutation(
  $input: DeleteAutoScalingRuleInput!
) {
  deleteAutoScalingRule(input: $input) {
    id
  }
}
`}}})();Kt.hash="051eb6f0b4919363bd328fca5366d60b";const Tt=(function(){var l=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardPresetsQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAutoScalingCardPresetsQuery",selections:l},params:{cacheID:"cc679b7f385bc973b5b68d9964531688",id:null,metadata:{},name:"DeploymentAutoScalingCardPresetsQuery",operationKind:"query",text:`query DeploymentAutoScalingCardPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}})();Tt.hash="6d5f2bbfca84b48a6aa4d1e118d88fdb";const Dt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},i=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,r,t],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardListQuery",selections:[{alias:null,args:i,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[s,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,{args:null,kind:"FragmentSpread",name:"AutoScalingRuleListNodesFragment"},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,r,a,t,e],kind:"Operation",name:"DeploymentAutoScalingCardListQuery",selections:[{alias:null,args:i,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[s,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},u],storageKey:null}]},params:{cacheID:"41c9b35cb41550bd8f8cde32c8b21c1a",id:null,metadata:{},name:"DeploymentAutoScalingCardListQuery",operationKind:"query",text:`query DeploymentAutoScalingCardListQuery(
  $deploymentId: ID!
  $offset: Int
  $limit: Int
  $orderBy: [AutoScalingRuleOrderBy!]
  $filter: AutoScalingRuleFilter
) {
  deployment(id: $deploymentId) {
    autoScalingRules(offset: $offset, limit: $limit, orderBy: $orderBy, filter: $filter) {
      count
      edges {
        node {
          id
          metricName
          ...AutoScalingRuleListNodesFragment
          ...AutoScalingRuleEditorModalFragment
        }
      }
    }
    id
  }
}

fragment AutoScalingRuleEditorModalFragment on AutoScalingRule {
  id
  metricSource
  metricName
  minThreshold
  maxThreshold
  stepSize
  timeWindow
  minReplicas
  maxReplicas
  prometheusQueryPresetId
}

fragment AutoScalingRuleListNodesFragment on AutoScalingRule {
  id
  metricSource
  metricName
  minThreshold
  maxThreshold
  stepSize
  timeWindow
  minReplicas
  maxReplicas
  prometheusQueryPresetId
  createdAt
  lastTriggeredAt
  ...AutoScalingRuleEditorModalFragment
}
`}}})();Dt.hash="56b6637e50dbda972f85edac73bc04b5";const It={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};It.hash="a7ebc88f8233e21188ec26bb29ecdb73";const Ct=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"UpdateAutoScalingRulePayload",kind:"LinkedField",name:"updateAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalUpdateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalUpdateMutation",selections:e},params:{cacheID:"f5194bd994f4693e29536fec36e4f0e4",id:null,metadata:{},name:"AutoScalingRuleEditorModalUpdateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalUpdateMutation(
  $input: UpdateAutoScalingRuleInput!
) {
  updateAutoScalingRule(input: $input) {
    rule {
      id
      metricSource
      metricName
      minThreshold
      maxThreshold
      stepSize
      timeWindow
      minReplicas
      maxReplicas
      prometheusQueryPresetId
    }
  }
}
`}}})();Ct.hash="8e953443e1aa963b955810e5f97de017";const At=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAutoScalingRulePayload",kind:"LinkedField",name:"createAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalCreateMutation",selections:e},params:{cacheID:"c7c250dabfc49b66cf1aebbff6414d44",id:null,metadata:{},name:"AutoScalingRuleEditorModalCreateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalCreateMutation(
  $input: CreateAutoScalingRuleInput!
) {
  createAutoScalingRule(input: $input) {
    rule {
      id
      metricSource
      metricName
      minThreshold
      maxThreshold
      stepSize
      timeWindow
      minReplicas
      maxReplicas
      prometheusQueryPresetId
    }
  }
}
`}}})();At.hash="7afa475334295923b7754d0563a8b919";const Mt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],type:"AutoScalingRule",abstractKey:null};Mt.hash="9dff1f6ce3b17626029eee3484220a7d";const Lt=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},a=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[l,e,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"categoryId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queryTemplate",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,concreteType:"QueryPresetCategory",kind:"LinkedField",name:"category",plural:!1,selections:[l,e],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalPresetsQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleEditorModalPresetsQuery",selections:a},params:{cacheID:"04d06fec5284e709aaee3606d8a4bb53",id:null,metadata:{},name:"AutoScalingRuleEditorModalPresetsQuery",operationKind:"query",text:`query AutoScalingRuleEditorModalPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
        description
        rank
        categoryId
        metricName
        queryTemplate
        timeWindow
        category @since(version: "26.4.3") {
          id
          name
        }
      }
    }
  }
}
`}}})();Lt.hash="6582d4cf067148f5b39755e919c0f4f2";const rn={KERNEL:["cpu_util","mem","net_rx","net_tx"],INFERENCE_FRAMEWORK:[]},Vn=l=>l?l.minThreshold!=null&&l.maxThreshold!=null?"scale_in_out":l.maxThreshold!=null?"scale_out":"scale_in":"scale_out",hi=l=>{"use memo";var Sl;const e=We.c(196),{autoScalingRule:a,formRef:r}=l,{t}=Je(),{token:i}=Dl.useToken(),d=vn(),s=ca();let u;e[0]!==d?(u=d.supports("prometheus-auto-scaling-rule"),e[0]=d,e[1]=u):u=e[1];const o=u;let y,c;e[2]===Symbol.for("react.memo_cache_sentinel")?(y=Lt,c={},e[2]=y,e[3]=c):(y=e[2],c=e[3]);const{prometheusQueryPresets:k}=Re.useLazyLoadQuery(y,c);let m;e[4]!==(k==null?void 0:k.edges)?(m=ma(Rl(k==null?void 0:k.edges,Fi)),e[4]=k==null?void 0:k.edges,e[5]=m):m=e[5];const g=m;let f;e[6]!==a?(f=Vn(a),e[6]=a,e[7]=f):f=e[7];const[p,S]=O.useState(f),[R,F]=O.useState((a==null?void 0:a.metricSource)||"KERNEL");let x;e[8]!==a||e[9]!==g?(x=a!=null&&a.prometheusQueryPresetId?(Sl=g.find(ke=>ll(ke.id)===a.prometheusQueryPresetId))==null?void 0:Sl.id:void 0,e[8]=a,e[9]=g,e[10]=x):x=e[10];const[D,K]=O.useState(x);let C;e[11]!==(a==null?void 0:a.metricSource)?(C=rn[(a==null?void 0:a.metricSource)||"KERNEL"]||[],e[11]=a==null?void 0:a.metricSource,e[12]=C):C=e[12];const[_,H]=O.useState(C);let z;if(e[13]!==g||e[14]!==D){let ke;e[16]!==D?(ke=De=>De.id===D,e[16]=D,e[17]=ke):ke=e[17],z=g.find(ke),e[13]=g,e[14]=D,e[15]=z}else z=e[15];const L=z;let w;if(e[18]!==g){const ke=Ha(g,["rank"],["asc"]),De=ke.filter(xi),rl=ke.filter(Ri),Ee=bi,nl=ga(De,Ki),yl=Object.entries(nl).map(Ml=>{const[bl,Ne]=Ml;return{label:bl,options:Ne.map(Ee)}});w=rl.length>0?[...yl,...rl.map(Ee)]:yl,e[18]=g,e[19]=w}else w=e[19];const V=w;let T;e[20]!==a||e[21]!==D?(T=()=>{if(a){const ke=Vn(a);let De;return ke==="scale_in"&&a.minThreshold!=null?De=Number(a.minThreshold):ke==="scale_out"&&a.maxThreshold!=null&&(De=Number(a.maxThreshold)),{metricSource:a.metricSource,metricName:a.metricName,prometheusQueryPresetId:D,conditionMode:ke,threshold:De,minThreshold:a.minThreshold!=null?Number(a.minThreshold):void 0,maxThreshold:a.maxThreshold!=null?Number(a.maxThreshold):void 0,stepSize:Math.abs(a.stepSize),timeWindow:a.timeWindow,minReplicas:a.minReplicas??void 0,maxReplicas:a.maxReplicas??void 0}}return{metricSource:"KERNEL",conditionMode:"scale_out",stepSize:1,timeWindow:300,minReplicas:0,maxReplicas:5}},e[20]=a,e[21]=D,e[22]=T):T=e[22];const E=T,$=R==="PROMETHEUS";let Y;e[23]!==E?(Y=E(),e[23]=E,e[24]=Y):Y=e[24];let U;e[25]!==t?(U=t("autoScalingRule.MetricSource"),e[25]=t,e[26]=U):U=e[26];let q;e[27]!==t?(q=t("autoScalingRule.MetricSourceTooltip"),e[27]=t,e[28]=q):q=e[28];let B;e[29]===Symbol.for("react.memo_cache_sentinel")?(B=[{required:!0}],e[29]=B):B=e[29];let j;e[30]!==r?(j=ke=>{var De,rl;if(F(ke),(De=r.current)==null||De.setFieldsValue({metricName:void 0}),ke!=="PROMETHEUS")H(rn[ke]||[]),K(void 0);else{const Ee=(rl=r.current)==null?void 0:rl.getFieldValue("prometheusQueryPresetId");Ee&&K(Ee)}},e[30]=r,e[31]=j):j=e[31];let b;e[32]!==t?(b=t("autoScalingRule.MetricSourceKernel"),e[32]=t,e[33]=b):b=e[33];let A;e[34]!==b?(A={label:b,value:"KERNEL"},e[34]=b,e[35]=A):A=e[35];let P;e[36]!==o||e[37]!==t?(P=o?[]:[{label:t("autoScalingRule.MetricSourceInferenceFramework"),value:"INFERENCE_FRAMEWORK"}],e[36]=o,e[37]=t,e[38]=P):P=e[38];let ne;e[39]!==t?(ne=t("autoScalingRule.MetricSourcePrometheus"),e[39]=t,e[40]=ne):ne=e[40];let le;e[41]!==ne?(le={label:ne,value:"PROMETHEUS"},e[41]=ne,e[42]=le):le=e[42];let I;e[43]!==A||e[44]!==P||e[45]!==le?(I=[A,...P,le],e[43]=A,e[44]=P,e[45]=le,e[46]=I):I=e[46];let v;e[47]!==j||e[48]!==I?(v=n.jsx(cn,{onChange:j,options:I}),e[47]=j,e[48]=I,e[49]=v):v=e[49];let N;e[50]!==U||e[51]!==q||e[52]!==v?(N=n.jsx(oe.Item,{label:U,name:"metricSource",tooltip:q,rules:B,children:v}),e[50]=U,e[51]=q,e[52]=v,e[53]=N):N=e[53];let M;e[54]!==t?(M=t("autoScalingRule.MetricName"),e[54]=t,e[55]=M):M=e[55];let W;e[56]!==t?(W=t("autoScalingRule.MetricNameTooltip"),e[56]=t,e[57]=W):W=e[57];const J=!$;let Z;e[58]!==J?(Z=[{required:J}],e[58]=J,e[59]=Z):Z=e[59];let ee;e[60]!==t?(ee=t("autoScalingRule.MetricName"),e[60]=t,e[61]=ee):ee=e[61];let Q;e[62]!==_?(Q=Rl(_,Ti),e[62]=_,e[63]=Q):Q=e[63];let ae;e[64]!==r?(ae={onSearch:ke=>{var rl;const De=((rl=r.current)==null?void 0:rl.getFieldValue("metricSource"))||"KERNEL";H(pa(rn[De]||[],Ee=>Ee.includes(ke)))}},e[64]=r,e[65]=ae):ae=e[65];let Se;e[66]!==ee||e[67]!==Q||e[68]!==ae?(Se=n.jsx(fa,{placeholder:ee,options:Q,showSearch:ae,allowClear:!0,popupMatchSelectWidth:!1}),e[66]=ee,e[67]=Q,e[68]=ae,e[69]=Se):Se=e[69];let ge;e[70]!==$||e[71]!==M||e[72]!==W||e[73]!==Z||e[74]!==Se?(ge=n.jsx(oe.Item,{label:M,name:"metricName",hidden:$,tooltip:W,rules:Z,children:Se}),e[70]=$,e[71]=M,e[72]=W,e[73]=Z,e[74]=Se,e[75]=ge):ge=e[75];let ye;e[76]!==s||e[77]!==r||e[78]!==$||e[79]!==g||e[80]!==V||e[81]!==L||e[82]!==t||e[83]!==i.fontSizeSM?(ye=$&&n.jsx(n.Fragment,{children:n.jsx(oe.Item,{label:`${t("autoScalingRule.MetricName")} (${t("autoScalingRule.PrometheusPreset")})`,name:"prometheusQueryPresetId",tooltip:t("autoScalingRule.PrometheusPresetTooltip"),rules:[{required:!0,message:t("autoScalingRule.PrometheusPresetRequired")}],extra:s==="superadmin"&&L?n.jsx(wa,{queryTemplate:L.queryTemplate},L.id):void 0,children:n.jsx(cn,{onChange:ke=>{var rl,Ee;K(ke);const De=g.find(nl=>nl.id===ke);if(De){(rl=r.current)==null||rl.setFieldsValue({metricName:De.metricName});const nl=De.timeWindow!=null?Number(De.timeWindow):void 0;nl!=null&&!isNaN(nl)&&((Ee=r.current)==null||Ee.setFieldsValue({timeWindow:nl}))}},placeholder:t("autoScalingRule.SelectPrometheusPreset"),showSearch:{filterOption:Di},options:V,optionRender:ke=>n.jsxs(te,{direction:"column",align:"start",children:[ke.label,ke.data.description&&n.jsx(Xe.Text,{type:"secondary",style:{fontSize:i.fontSizeSM},ellipsis:!0,children:ke.data.description})]}),allowClear:!0,onClear:()=>K(void 0)})})}),e[76]=s,e[77]=r,e[78]=$,e[79]=g,e[80]=V,e[81]=L,e[82]=t,e[83]=i.fontSizeSM,e[84]=ye):ye=e[84];let de;e[85]!==t?(de=t("autoScalingRule.Condition"),e[85]=t,e[86]=de):de=e[86];let pe;e[87]!==t?(pe=t("autoScalingRule.ConditionTooltip"),e[87]=t,e[88]=pe):pe=e[88];let ue;e[89]===Symbol.for("react.memo_cache_sentinel")?(ue=ke=>{S(ke.target.value)},e[89]=ue):ue=e[89];let fe;e[90]!==i.marginSM?(fe={marginBottom:i.marginSM},e[90]=i.marginSM,e[91]=fe):fe=e[91];let ce;e[92]!==t?(ce=t("autoScalingRule.ScaleIn"),e[92]=t,e[93]=ce):ce=e[93];let ve;e[94]!==ce?(ve={label:ce,value:"scale_in"},e[94]=ce,e[95]=ve):ve=e[95];let Ke;e[96]!==t?(Ke=t("autoScalingRule.ScaleOut"),e[96]=t,e[97]=Ke):Ke=e[97];let Te;e[98]!==Ke?(Te={label:Ke,value:"scale_out"},e[98]=Ke,e[99]=Te):Te=e[99];let Ae;e[100]!==t?(Ae=t("autoScalingRule.ScaleInAndOut"),e[100]=t,e[101]=Ae):Ae=e[101];let Ie;e[102]!==Ae?(Ie={label:Ae,value:"scale_in_out"},e[102]=Ae,e[103]=Ie):Ie=e[103];let ie;e[104]!==ve||e[105]!==Te||e[106]!==Ie?(ie=[ve,Te,Ie],e[104]=ve,e[105]=Te,e[106]=Ie,e[107]=ie):ie=e[107];let Fe;e[108]!==fe||e[109]!==ie?(Fe=n.jsx(oe.Item,{name:"conditionMode",noStyle:!0,children:n.jsx(ya.Group,{optionType:"button",onChange:ue,style:fe,options:ie})}),e[108]=fe,e[109]=ie,e[110]=Fe):Fe=e[110];let je;e[111]!==p||e[112]!==t?(je=p==="scale_in"&&n.jsxs(te,{align:"center",gap:"xs",children:[n.jsxs(Xe.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(oe.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),e[111]=p,e[112]=t,e[113]=je):je=e[113];let He;e[114]!==p||e[115]!==t?(He=p==="scale_out"&&n.jsxs(te,{align:"center",gap:"xs",children:[n.jsx(oe.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(Xe.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]}),e[114]=p,e[115]=t,e[116]=He):He=e[116];let tl;e[117]!==p||e[118]!==t?(tl=p==="scale_in_out"&&n.jsxs(te,{direction:"column",gap:"xs",align:"stretch",children:[n.jsxs(te,{align:"center",gap:"xs",children:[n.jsxs(Xe.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(oe.Item,{name:"minThreshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.MinThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),n.jsxs(te,{align:"center",gap:"xs",children:[n.jsx(oe.Item,{name:"maxThreshold",noStyle:!0,dependencies:["minThreshold"],rules:[{required:!0,message:t("autoScalingRule.MaxThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")},ke=>{const{getFieldValue:De}=ke;return{validator(rl,Ee){const nl=De("minThreshold");return nl!=null&&Ee!=null&&nl>=Ee?Promise.reject(new Error(t("autoScalingRule.MinMustBeLessThanMax"))):Promise.resolve()}}}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(Xe.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]})]}),e[117]=p,e[118]=t,e[119]=tl):tl=e[119];let Ge;e[120]!==de||e[121]!==pe||e[122]!==Fe||e[123]!==je||e[124]!==He||e[125]!==tl?(Ge=n.jsxs(oe.Item,{label:de,required:!0,tooltip:pe,children:[Fe,je,He,tl]}),e[120]=de,e[121]=pe,e[122]=Fe,e[123]=je,e[124]=He,e[125]=tl,e[126]=Ge):Ge=e[126];let Ye;e[127]!==t?(Ye=t("autoScalingRule.StepSize"),e[127]=t,e[128]=Ye):Ye=e[128];let Ze;e[129]!==t?(Ze=t("autoScalingRule.StepSizeTooltip"),e[129]=t,e[130]=Ze):Ze=e[130];let h,G;e[131]===Symbol.for("react.memo_cache_sentinel")?(h={required:!0},G={type:"number",min:1,max:$l},e[131]=h,e[132]=G):(h=e[131],G=e[132]);let X;e[133]!==t?(X=[h,G,{validator:(ke,De)=>De%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[133]=t,e[134]=X):X=e[134];let se;e[135]===Symbol.for("react.memo_cache_sentinel")?(se={width:"100%"},e[135]=se):se=e[135];const re=p==="scale_in_out"?"±":p==="scale_out"?"+":"−";let me;e[136]!==re?(me=n.jsx(gl,{min:1,step:1,style:se,prefix:n.jsx(Xe.Text,{type:"secondary",children:re})}),e[136]=re,e[137]=me):me=e[137];let Ce;e[138]!==Ye||e[139]!==Ze||e[140]!==X||e[141]!==me?(Ce=n.jsx(oe.Item,{label:Ye,name:"stepSize",tooltip:Ze,rules:X,children:me}),e[138]=Ye,e[139]=Ze,e[140]=X,e[141]=me,e[142]=Ce):Ce=e[142];let Pe;e[143]!==t?(Pe=t("autoScalingRule.CoolDownSeconds"),e[143]=t,e[144]=Pe):Pe=e[144];let Oe;e[145]!==t?(Oe=t("autoScalingRule.CoolDownTooltip"),e[145]=t,e[146]=Oe):Oe=e[146];let Ve,Be;e[147]===Symbol.for("react.memo_cache_sentinel")?(Ve={required:!0},Be={type:"number",min:1},e[147]=Ve,e[148]=Be):(Ve=e[147],Be=e[148]);let he;e[149]!==t?(he=[Ve,Be,{validator:(ke,De)=>De%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[149]=t,e[150]=he):he=e[150];let we;e[151]===Symbol.for("react.memo_cache_sentinel")?(we={width:"100%"},e[151]=we):we=e[151];let $e;e[152]!==t?($e=t("autoScalingRule.Seconds"),e[152]=t,e[153]=$e):$e=e[153];let Qe;e[154]!==$e?(Qe=n.jsx(gl,{min:1,step:1,style:we,suffix:n.jsx(Xe.Text,{type:"secondary",children:$e})}),e[154]=$e,e[155]=Qe):Qe=e[155];let _e;e[156]!==Pe||e[157]!==Oe||e[158]!==he||e[159]!==Qe?(_e=n.jsx(oe.Item,{label:Pe,name:"timeWindow",tooltip:Oe,rules:he,children:Qe}),e[156]=Pe,e[157]=Oe,e[158]=he,e[159]=Qe,e[160]=_e):_e=e[160];let qe;e[161]!==t?(qe=t("autoScalingRule.MinReplicas"),e[161]=t,e[162]=qe):qe=e[162];let el;e[163]!==t?(el=t("autoScalingRule.MinReplicasTooltip"),e[163]=t,e[164]=el):el=e[164];let Me;e[165]===Symbol.for("react.memo_cache_sentinel")?(Me={min:0,max:$l,type:"number"},e[165]=Me):Me=e[165];let ze;e[166]!==t?(ze=[Me,{validator:(ke,De)=>De!=null&&De%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[166]=t,e[167]=ze):ze=e[167];let ul;e[168]===Symbol.for("react.memo_cache_sentinel")?(ul=n.jsx(gl,{min:0,max:$l,style:{width:"100%"}}),e[168]=ul):ul=e[168];let al;e[169]!==qe||e[170]!==el||e[171]!==ze?(al=n.jsx(oe.Item,{label:qe,name:"minReplicas",tooltip:el,rules:ze,children:ul}),e[169]=qe,e[170]=el,e[171]=ze,e[172]=al):al=e[172];let il;e[173]!==t?(il=t("autoScalingRule.MaxReplicas"),e[173]=t,e[174]=il):il=e[174];let sl;e[175]!==t?(sl=t("autoScalingRule.MaxReplicasTooltip"),e[175]=t,e[176]=sl):sl=e[176];let ol;e[177]===Symbol.for("react.memo_cache_sentinel")?(ol={min:0,max:$l,type:"number"},e[177]=ol):ol=e[177];let be;e[178]!==t?(be=[ol,{validator:(ke,De)=>De!=null&&De%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[178]=t,e[179]=be):be=e[179];let xe;e[180]===Symbol.for("react.memo_cache_sentinel")?(xe=n.jsx(gl,{min:0,max:$l,style:{width:"100%"}}),e[180]=xe):xe=e[180];let Le;e[181]!==il||e[182]!==sl||e[183]!==be?(Le=n.jsx(oe.Item,{label:il,name:"maxReplicas",tooltip:sl,rules:be,children:xe}),e[181]=il,e[182]=sl,e[183]=be,e[184]=Le):Le=e[184];let Ue;return e[185]!==r||e[186]!==Y||e[187]!==N||e[188]!==ge||e[189]!==ye||e[190]!==Ge||e[191]!==Ce||e[192]!==_e||e[193]!==al||e[194]!==Le?(Ue=n.jsxs(oe,{ref:r,layout:"vertical",initialValues:Y,children:[N,ge,ye,Ge,Ce,_e,al,Le]}),e[185]=r,e[186]=Y,e[187]=N,e[188]=ge,e[189]=ye,e[190]=Ge,e[191]=Ce,e[192]=_e,e[193]=al,e[194]=Le,e[195]=Ue):Ue=e[195],Ue},vi=l=>{"use memo";const e=We.c(34);let a,r,t,i,d;e[0]!==l?({onRequestClose:d,onComplete:i,modelDeploymentId:t,autoScalingRuleFrgmt:a,...r}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5]);const{t:s}=Je(),{message:u}=Pl.useApp(),{logger:o}=Ol();let y;e[6]===Symbol.for("react.memo_cache_sentinel")?(y=Mt,e[6]=y):y=e[6];const c=Re.useFragment(y,a??null),k=O.useRef(null);let m;e[7]===Symbol.for("react.memo_cache_sentinel")?(m=At,e[7]=m):m=e[7];const[g,f]=Re.useMutation(m);let p;e[8]===Symbol.for("react.memo_cache_sentinel")?(p=Ct,e[8]=p):p=e[8];const[S,R]=Re.useMutation(p);let F;e[9]!==c||e[10]!==g||e[11]!==S||e[12]!==o||e[13]!==u||e[14]!==t||e[15]!==i||e[16]!==d||e[17]!==s?(F=()=>{var V;return(V=k.current)==null?void 0:V.validateFields().then(T=>{let E=null,$=null;T.conditionMode==="scale_in_out"?(E=T.minThreshold??null,$=T.maxThreshold??null):T.conditionMode==="scale_in"?E=T.threshold??null:$=T.threshold??null;const Y=T.metricName,U=T.metricSource==="PROMETHEUS"&&T.prometheusQueryPresetId?ll(T.prometheusQueryPresetId):null;c?S({variables:{input:{id:ll(c.id),metricSource:T.metricSource,metricName:Y,minThreshold:E!=null?String(E):null,maxThreshold:$!=null?String($):null,stepSize:T.stepSize,timeWindow:T.timeWindow,minReplicas:T.minReplicas,maxReplicas:T.maxReplicas,prometheusQueryPresetId:U??void 0}},onCompleted:(q,B)=>{if(B&&B.length>0){const j=Rl(B,Ii);for(const b of j)u.error(b);return}u.success(s("autoScalingRule.SuccessfullyUpdated")),i==null||i(),d(!0)},onError:q=>{u.error(q.message)}}):g({variables:{input:{modelDeploymentId:t,metricSource:T.metricSource,metricName:Y,minThreshold:E!=null?String(E):null,maxThreshold:$!=null?String($):null,stepSize:T.stepSize,timeWindow:T.timeWindow,minReplicas:T.minReplicas,maxReplicas:T.maxReplicas,prometheusQueryPresetId:U??void 0}},onCompleted:(q,B)=>{if(B&&B.length>0){const j=Rl(B,Ci);for(const b of j)u.error(b);return}u.success(s("autoScalingRule.SuccessfullyCreated")),i==null||i(),d(!0)},onError:q=>{u.error(q.message)}})}).catch(T=>{o.error(T)})},e[9]=c,e[10]=g,e[11]=S,e[12]=o,e[13]=u,e[14]=t,e[15]=i,e[16]=d,e[17]=s,e[18]=F):F=e[18];const x=F;let D;e[19]!==d?(D=()=>{d(!1)},e[19]=d,e[20]=D):D=e[20];const K=D;let C;e[21]!==c||e[22]!==s?(C=s(c?"autoScalingRule.EditAutoScalingRule":"autoScalingRule.AddAutoScalingRule"),e[21]=c,e[22]=s,e[23]=C):C=e[23];const _=f||R;let H;e[24]===Symbol.for("react.memo_cache_sentinel")?(H=n.jsx(xl,{active:!0,paragraph:{rows:6}}),e[24]=H):H=e[24];const z=c??null;let L;e[25]!==z?(L=n.jsx(Un,{children:n.jsx(ua.Suspense,{fallback:H,children:n.jsx(hi,{autoScalingRule:z,formRef:k})})}),e[25]=z,e[26]=L):L=e[26];let w;return e[27]!==r||e[28]!==K||e[29]!==x||e[30]!==L||e[31]!==C||e[32]!==_?(w=n.jsx(Hl,{...r,onOk:x,onCancel:K,centered:!0,title:C,confirmLoading:_,children:L}),e[27]=r,e[28]=K,e[29]=x,e[30]=L,e[31]=C,e[32]=_,e[33]=w):w=e[33],w};function Fi(l){return l==null?void 0:l.node}function xi(l){var e;return(e=l.category)==null?void 0:e.name}function Ri(l){var e;return!((e=l.category)!=null&&e.name)}function bi(l){return{label:l.name,value:l.id,description:l.description}}function Ki(l){return l.category.name}function Ti(l){return{label:l,value:l}}function Di(l,e){return String((e==null?void 0:e.label)??"").toLowerCase().includes(l.toLowerCase())}function Ii(l){return l.message}function Ci(l){return l.message}const jt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"AutoScalingRuleListNodesFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],type:"AutoScalingRule",abstractKey:null};jt.hash="54a32b764fc7e506f5bddfe218691cd2";const Ai=(l,e,a)=>{const r=l.metricSource==="PROMETHEUS"&&l.prometheusQueryPresetId?(a==null?void 0:a.get(l.prometheusQueryPresetId))??l.metricName:l.metricName,t=l.minThreshold,i=l.maxThreshold;return t!=null&&i!=null?n.jsxs(te,{direction:"column",gap:"xxs",children:[n.jsxs(te,{gap:"xs",children:[n.jsx(Zl,{children:r})," < ",t]}),n.jsxs(te,{gap:"xs",children:[i," < ",n.jsx(Zl,{children:r})]})]}):i!=null?n.jsxs(te,{gap:"xs",children:[i,n.jsx(cl,{title:e("autoScalingRule.MaxThreshold"),children:"<"}),n.jsx(Zl,{children:r})]}):t!=null?n.jsxs(te,{gap:"xs",children:[n.jsx(Zl,{children:r}),n.jsx(cl,{title:e("autoScalingRule.MinThreshold"),children:"<"}),t]}):"-"},Mi=l=>{"use memo";const e=We.c(103);let a,r,t,i,d,s,u;e[0]!==l?({autoScalingRulesFrgmt:a,presetMap:s,isEndpointDestroying:r,isOwnedByCurrentUser:t,onEditRule:d,onDeleteRule:i,...u}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d,e[6]=s,e[7]=u):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5],s=e[6],u=e[7]);const{t:o}=Je();let y;e[8]===Symbol.for("react.memo_cache_sentinel")?(y=jt,e[8]=y):y=e[8];const c=Re.useFragment(y,a);let k;e[9]!==c?(k=Al(c),e[9]=c,e[10]=k):k=e[10];const m=k;let g;e[11]===Symbol.for("react.memo_cache_sentinel")?(g={x:"max-content"},e[11]=g):g=e[11];let f;e[12]!==o?(f=o("autoScalingRule.MetricSource"),e[12]=o,e[13]=f):f=e[13];let p;e[14]!==o?(p=o("autoScalingRule.MetricSourceTooltip"),e[14]=o,e[15]=p):p=e[15];let S;e[16]!==p?(S=n.jsx(pl,{title:p}),e[16]=p,e[17]=S):S=e[17];let R;e[18]!==f||e[19]!==S?(R={key:"metricSource",title:n.jsxs(te,{gap:"xxs",align:"center",children:[f,S]}),dataIndex:"metricSource",fixed:"left"},e[18]=f,e[19]=S,e[20]=R):R=e[20];let F;e[21]!==o?(F=o("autoScalingRule.Condition"),e[21]=o,e[22]=F):F=e[22];let x;e[23]!==o?(x=o("autoScalingRule.ConditionTooltip"),e[23]=o,e[24]=x):x=e[24];let D;e[25]!==x?(D=n.jsx(pl,{title:x}),e[25]=x,e[26]=D):D=e[26];let K;e[27]!==D||e[28]!==F?(K=n.jsxs(te,{gap:"xxs",align:"center",children:[F,D]}),e[27]=D,e[28]=F,e[29]=K):K=e[29];let C;e[30]!==r||e[31]!==t||e[32]!==i||e[33]!==d||e[34]!==s||e[35]!==o?(C=(ee,Q)=>Q?n.jsx(kn,{title:Ai(Q,o,s),showActions:"always",actions:[{key:"edit",title:o("button.Edit"),icon:n.jsx(it,{}),disabled:r||!t,onClick:()=>d(Q.id)},{key:"delete",title:o("button.Delete"),icon:n.jsx(Sn,{}),type:"danger",disabled:r||!t,onClick:()=>i(Q.id,Q.metricName??"")}]}):"-",e[30]=r,e[31]=t,e[32]=i,e[33]=d,e[34]=s,e[35]=o,e[36]=C):C=e[36];let _;e[37]!==K||e[38]!==C?(_={key:"condition",title:K,fixed:"left",render:C},e[37]=K,e[38]=C,e[39]=_):_=e[39];let H;e[40]!==o?(H=o("autoScalingRule.CoolDownSeconds"),e[40]=o,e[41]=H):H=e[41];let z;e[42]!==o?(z=o("autoScalingRule.CoolDownTooltip"),e[42]=o,e[43]=z):z=e[43];let L;e[44]!==z?(L=n.jsx(pl,{title:z}),e[44]=z,e[45]=L):L=e[45];let w;e[46]!==H||e[47]!==L?(w=n.jsxs(te,{gap:"xxs",align:"center",children:[H,L]}),e[46]=H,e[47]=L,e[48]=w):w=e[48];let V;e[49]!==o?(V=ee=>ee!=null?o("autoScalingRule.CoolDownSecondsValue",{value:ee}):"-",e[49]=o,e[50]=V):V=e[50];let T;e[51]!==w||e[52]!==V?(T={key:"timeWindow",title:w,dataIndex:"timeWindow",render:V},e[51]=w,e[52]=V,e[53]=T):T=e[53];let E;e[54]!==o?(E=o("autoScalingRule.StepSize"),e[54]=o,e[55]=E):E=e[55];let $;e[56]!==o?($=o("autoScalingRule.StepSizeTooltip"),e[56]=o,e[57]=$):$=e[57];let Y;e[58]!==$?(Y=n.jsx(pl,{title:$}),e[58]=$,e[59]=Y):Y=e[59];let U;e[60]!==E||e[61]!==Y?(U={key:"stepSize",title:n.jsxs(te,{gap:"xxs",align:"center",children:[E,Y]}),dataIndex:"stepSize",render:Li},e[60]=E,e[61]=Y,e[62]=U):U=e[62];let q;e[63]!==o?(q=o("autoScalingRule.MIN/MAXReplicas"),e[63]=o,e[64]=q):q=e[64];let B;e[65]!==o?(B=o("autoScalingRule.MinMaxReplicasTooltip"),e[65]=o,e[66]=B):B=e[66];let j;e[67]!==B?(j=n.jsx(pl,{title:B}),e[67]=B,e[68]=j):j=e[68];let b;e[69]!==q||e[70]!==j?(b=n.jsxs(te,{gap:"xxs",align:"center",children:[q,j]}),e[69]=q,e[70]=j,e[71]=b):b=e[71];let A;e[72]!==o?(A=(ee,Q)=>{if(!(Q!=null&&Q.stepSize))return"-";const ae=Q.minThreshold!=null,Se=Q.maxThreshold!=null;return ae&&Se?n.jsxs("span",{children:[o("autoScalingRule.MinReplicasValue",{value:Q==null?void 0:Q.minReplicas})," / ",o("autoScalingRule.MaxReplicasValue",{value:Q==null?void 0:Q.maxReplicas})]}):Se?n.jsx("span",{children:o("autoScalingRule.MaxReplicasValue",{value:Q==null?void 0:Q.maxReplicas})}):n.jsx("span",{children:o("autoScalingRule.MinReplicasValue",{value:Q==null?void 0:Q.minReplicas})})},e[72]=o,e[73]=A):A=e[73];let P;e[74]!==b||e[75]!==A?(P={key:"minMaxReplicas",title:b,render:A},e[74]=b,e[75]=A,e[76]=P):P=e[76];let ne;e[77]!==o?(ne=o("autoScalingRule.CreatedAt"),e[77]=o,e[78]=ne):ne=e[78];let le;e[79]===Symbol.for("react.memo_cache_sentinel")?(le=["descend","ascend"],e[79]=le):le=e[79];let I;e[80]!==ne?(I={key:"createdAt",title:ne,dataIndex:"createdAt",sorter:!0,sortDirections:le,render:ji},e[80]=ne,e[81]=I):I=e[81];let v;e[82]!==o?(v=o("autoScalingRule.LastTriggered"),e[82]=o,e[83]=v):v=e[83];let N;e[84]!==o?(N=o("autoScalingRule.LastTriggeredTooltip"),e[84]=o,e[85]=N):N=e[85];let M;e[86]!==N?(M=n.jsx(pl,{title:N}),e[86]=N,e[87]=M):M=e[87];let W;e[88]!==v||e[89]!==M?(W={key:"lastTriggeredAt",title:n.jsxs(te,{gap:"xxs",align:"center",children:[v,M]}),render:Pi},e[88]=v,e[89]=M,e[90]=W):W=e[90];let J;e[91]!==_||e[92]!==T||e[93]!==U||e[94]!==P||e[95]!==I||e[96]!==W||e[97]!==R?(J=[R,_,T,U,P,I,W],e[91]=_,e[92]=T,e[93]=U,e[94]=P,e[95]=I,e[96]=W,e[97]=R,e[98]=J):J=e[98];let Z;return e[99]!==m||e[100]!==J||e[101]!==u?(Z=n.jsx(El,{scroll:g,rowKey:"id",columns:J,showSorterTooltip:!1,dataSource:m,...u}),e[99]=m,e[100]=J,e[101]=u,e[102]=Z):Z=e[102],Z};function Li(l,e){if(!(e!=null&&e.stepSize))return"-";const a=e.minThreshold!=null,r=e.maxThreshold!=null;if(!a&&!r)return"-";const t=a&&r?"±":r?"+":"−";return n.jsxs(te,{gap:"xs",children:[n.jsx(Xe.Text,{children:t}),n.jsx(Xe.Text,{children:Math.abs(e.stepSize)})]})}function ji(l,e){return n.jsx("span",{children:e!=null&&e.createdAt?dl(e.createdAt).format("ll LT"):"-"})}function Pi(l,e){return n.jsx("span",{children:e!=null&&e.lastTriggeredAt?dl.utc(e.lastTriggeredAt).tz().format("ll LTS"):"-"})}const Ni=l=>{"use memo";var K,C,_;const e=We.c(24),{deploymentFrgmt:a}=l,{t:r}=Je(),{token:t}=Dl.useToken(),[i]=Wn();let d;e[0]===Symbol.for("react.memo_cache_sentinel")?(d=It,e[0]=d):d=e[0];const s=Re.useFragment(d,a);if(!(s!=null&&s.id))return null;const u=(K=s.metadata)==null?void 0:K.status;let o;e[1]!==u?(o=hl(u),e[1]=u,e[2]=o):o=e[2];const y=o,c=((_=(C=s.creator)==null?void 0:C.basicInfo)==null?void 0:_.email)??null,k=!c||c===i.email;let m;e[3]!==r?(m=r("deployment.tab.AutoScaling"),e[3]=r,e[4]=m):m=e[4];let g;e[5]!==r?(g=r("deployment.tab.description.AutoScaling"),e[5]=r,e[6]=g):g=e[6];let f;e[7]!==t.colorTextDescription?(f=n.jsx(fn,{style:{color:t.colorTextDescription}}),e[7]=t.colorTextDescription,e[8]=f):f=e[8];let p;e[9]!==g||e[10]!==f?(p=n.jsx(cl,{title:g,children:f}),e[9]=g,e[10]=f,e[11]=p):p=e[11];let S;e[12]!==m||e[13]!==p?(S=n.jsxs(te,{gap:"xs",align:"center",children:[m,p]}),e[12]=m,e[13]=p,e[14]=S):S=e[14];let R;e[15]===Symbol.for("react.memo_cache_sentinel")?(R={body:{paddingTop:0}},e[15]=R):R=e[15];let F;e[16]===Symbol.for("react.memo_cache_sentinel")?(F=n.jsx(xl,{active:!0}),e[16]=F):F=e[16];let x;e[17]!==s.id||e[18]!==y||e[19]!==k?(x=n.jsx(O.Suspense,{fallback:F,children:n.jsx(Vi,{deploymentId:s.id,isEndpointDestroying:y,isOwnedByCurrentUser:k})}),e[17]=s.id,e[18]=y,e[19]=k,e[20]=x):x=e[20];let D;return e[21]!==x||e[22]!==S?(D=n.jsx(Wl,{title:S,styles:R,children:x}),e[21]=x,e[22]=S,e[23]=D):D=e[23],D},Vi=l=>{"use memo";var el,Me,ze,ul,al,il,sl,ol;const e=We.c(123),{deploymentId:a,isEndpointDestroying:r,isOwnedByCurrentUser:t}=l,{t:i}=Je(),{message:d}=Pl.useApp(),[s,u]=O.useTransition(),[o,y]=Il(),[c,k]=O.useState(null),[m,g]=O.useState(!1),[f,p]=O.useState(null),[S,R]=Cl("table_column_overrides.AutoScalingRuleList");let F,x;e[0]===Symbol.for("react.memo_cache_sentinel")?(F={order:Ul(["createdAt","-createdAt"]).withDefault("-createdAt"),filter:ka(_i)},x={history:"replace"},e[0]=F,e[1]=x):(F=e[0],x=e[1]);const[D,K]=Fn(F,x),C=D.order,_=D.filter??void 0;let H;e[2]===Symbol.for("react.memo_cache_sentinel")?(H={current:1,pageSize:10},e[2]=H):H=e[2];const{baiPaginationOption:z,tablePaginationOption:L,setTablePaginationOption:w}=Sa(H),V=C.startsWith("-")?"DESC":"ASC";let T;e[3]!==V?(T=[{field:"CREATED_AT",direction:V}],e[3]=V,e[4]=T):T=e[4];const E=_??null;let $;e[5]!==z.limit||e[6]!==z.offset||e[7]!==a||e[8]!==T||e[9]!==E?($={deploymentId:a,offset:z.offset,limit:z.limit,orderBy:T,filter:E},e[5]=z.limit,e[6]=z.offset,e[7]=a,e[8]=T,e[9]=E,e[10]=$):$=e[10];const Y=$,U=O.useDeferredValue(Y);let q;e[11]===Symbol.for("react.memo_cache_sentinel")?(q=Dt,e[11]=q):q=e[11];let B;e[12]!==o?(B={fetchPolicy:"store-and-network",fetchKey:o},e[12]=o,e[13]=B):B=e[13];const j=Re.useLazyLoadQuery(q,U,B);let b,A;e[14]===Symbol.for("react.memo_cache_sentinel")?(b=Tt,A={},e[14]=b,e[15]=A):(b=e[14],A=e[15]);const{prometheusQueryPresets:P}=Re.useLazyLoadQuery(b,A);let ne;if(e[16]!==P){if(ne=new Map,P!=null&&P.edges)for(const be of P.edges)be!=null&&be.node&&ne.set(ll(be.node.id),be.node.name);e[16]=P,e[17]=ne}else ne=e[17];const le=ne;let I;e[18]!==((Me=(el=j==null?void 0:j.deployment)==null?void 0:el.autoScalingRules)==null?void 0:Me.edges)?(I=Al(Rl((ul=(ze=j==null?void 0:j.deployment)==null?void 0:ze.autoScalingRules)==null?void 0:ul.edges,"node")),e[18]=(il=(al=j==null?void 0:j.deployment)==null?void 0:al.autoScalingRules)==null?void 0:il.edges,e[19]=I):I=e[19];const v=I,N=((ol=(sl=j==null?void 0:j.deployment)==null?void 0:sl.autoScalingRules)==null?void 0:ol.count)??0;let M;e[20]===Symbol.for("react.memo_cache_sentinel")?(M=Kt,e[20]=M):M=e[20];const W=qn(M);let J;e[21]!==y?(J=()=>{u(()=>{y()})},e[21]=y,e[22]=J):J=e[22];const Z=J;let ee;e[23]===Symbol.for("react.memo_cache_sentinel")?(ee=(be,xe)=>{p({id:be,metricName:xe})},e[23]=ee):ee=e[23];const Q=ee;let ae;e[24]===Symbol.for("react.memo_cache_sentinel")?(ae={flex:1},e[24]=ae):ae=e[24];let Se;e[25]!==i?(Se=i("autoScalingRule.CreatedAt"),e[25]=i,e[26]=Se):Se=e[26];let ge;e[27]===Symbol.for("react.memo_cache_sentinel")?(ge=["after","before"],e[27]=ge):ge=e[27];let ye;e[28]!==Se?(ye={key:"createdAt",propertyLabel:Se,type:"datetime",operators:ge,defaultOperator:"after"},e[28]=Se,e[29]=ye):ye=e[29];let de;e[30]!==i?(de=i("autoScalingRule.LastTriggered"),e[30]=i,e[31]=de):de=e[31];let pe;e[32]===Symbol.for("react.memo_cache_sentinel")?(pe=["after","before"],e[32]=pe):pe=e[32];let ue;e[33]!==de?(ue={key:"lastTriggeredAt",propertyLabel:de,type:"datetime",operators:pe,defaultOperator:"after"},e[33]=de,e[34]=ue):ue=e[34];let fe;e[35]!==ye||e[36]!==ue?(fe=[ye,ue],e[35]=ye,e[36]=ue,e[37]=fe):fe=e[37];let ce;e[38]!==K||e[39]!==w?(ce=be=>{u(()=>{K({filter:be??null}),w({current:1})})},e[38]=K,e[39]=w,e[40]=ce):ce=e[40];let ve;e[41]!==_||e[42]!==fe||e[43]!==ce?(ve=n.jsx(Gl,{style:ae,filterProperties:fe,value:_,onChange:ce}),e[41]=_,e[42]=fe,e[43]=ce,e[44]=ve):ve=e[44];let Ke;e[45]!==y?(Ke=()=>{u(()=>y())},e[45]=y,e[46]=Ke):Ke=e[46];let Te;e[47]!==s||e[48]!==Ke?(Te=n.jsx(wl,{loading:s,value:"",onChange:Ke}),e[47]=s,e[48]=Ke,e[49]=Te):Te=e[49];let Ae;e[50]===Symbol.for("react.memo_cache_sentinel")?(Ae=n.jsx(Ll,{}),e[50]=Ae):Ae=e[50];const Ie=r||!t;let ie;e[51]===Symbol.for("react.memo_cache_sentinel")?(ie=()=>{k(null),g(!0)},e[51]=ie):ie=e[51];let Fe;e[52]!==i?(Fe=i("modelService.AddRules"),e[52]=i,e[53]=Fe):Fe=e[53];let je;e[54]!==Ie||e[55]!==Fe?(je=n.jsx(kl,{type:"primary",icon:Ae,disabled:Ie,onClick:ie,children:Fe}),e[54]=Ie,e[55]=Fe,e[56]=je):je=e[56];let He;e[57]!==ve||e[58]!==Te||e[59]!==je?(He=n.jsxs(te,{align:"center",gap:"xs",children:[ve,Te,je]}),e[57]=ve,e[58]=Te,e[59]=je,e[60]=He):He=e[60];const tl=s||U!==Y;let Ge;e[61]!==S||e[62]!==R?(Ge={columnOverrides:S,onColumnOverridesChange:R},e[61]=S,e[62]=R,e[63]=Ge):Ge=e[63];let Ye;e[64]!==K?(Ye=be=>{u(()=>{K({order:be||null})})},e[64]=K,e[65]=Ye):Ye=e[65];let Ze;e[66]!==w?(Ze=(be,xe)=>{w({current:be,pageSize:xe})},e[66]=w,e[67]=Ze):Ze=e[67];let h;e[68]!==Ze||e[69]!==L.current||e[70]!==L.pageSize||e[71]!==N?(h={pageSize:L.pageSize,current:L.current,total:N,onChange:Ze},e[68]=Ze,e[69]=L.current,e[70]=L.pageSize,e[71]=N,e[72]=h):h=e[72];let G;e[73]===Symbol.for("react.memo_cache_sentinel")?(G=be=>{k(be),g(!0)},e[73]=G):G=e[73];let X;e[74]!==v||e[75]!==r||e[76]!==t||e[77]!==C||e[78]!==le||e[79]!==tl||e[80]!==Ge||e[81]!==Ye||e[82]!==h?(X=n.jsx(Mi,{autoScalingRulesFrgmt:v,presetMap:le,order:C,loading:tl,tableSettings:Ge,onChangeOrder:Ye,pagination:h,isEndpointDestroying:r,isOwnedByCurrentUser:t,onEditRule:G,onDeleteRule:Q}),e[74]=v,e[75]=r,e[76]=t,e[77]=C,e[78]=le,e[79]=tl,e[80]=Ge,e[81]=Ye,e[82]=h,e[83]=X):X=e[83];let se;e[84]!==He||e[85]!==X?(se=n.jsxs(te,{direction:"column",align:"stretch",gap:"sm",children:[He,X]}),e[84]=He,e[85]=X,e[86]=se):se=e[86];let re;e[87]!==a?(re=ll(a),e[87]=a,e[88]=re):re=e[88];let me;e[89]!==v||e[90]!==c?(me=c?v.find(be=>be.id===c)??null:null,e[89]=v,e[90]=c,e[91]=me):me=e[91];let Ce;e[92]!==Z?(Ce=be=>{g(!1),be&&Z()},e[92]=Z,e[93]=Ce):Ce=e[93];let Pe;e[94]===Symbol.for("react.memo_cache_sentinel")?(Pe=()=>{k(null)},e[94]=Pe):Pe=e[94];let Oe;e[95]!==m||e[96]!==re||e[97]!==me||e[98]!==Ce?(Oe=n.jsx(fl,{children:n.jsx(vi,{open:m,modelDeploymentId:re,autoScalingRuleFrgmt:me,onRequestClose:Ce,afterClose:Pe})}),e[95]=m,e[96]=re,e[97]=me,e[98]=Ce,e[99]=Oe):Oe=e[99];const Ve=!!f;let Be;e[100]!==i?(Be=i("autoScalingRule.DeleteAutoScalingRule"),e[100]=i,e[101]=Be):Be=e[101];let he;e[102]!==i?(he=i("autoScalingRule.DeleteConfirmation"),e[102]=i,e[103]=he):he=e[103];let we;e[104]!==f?(we=f?[{key:f.id,label:f.metricName}]:[],e[104]=f,e[105]=we):we=e[105];let $e;e[106]!==W||e[107]!==f||e[108]!==Z||e[109]!==d||e[110]!==i?($e=()=>{if(f)return W({input:{id:ll(f.id)}}).then(()=>{p(null),Z(),d.success({key:"autoscaling-rule-deleted",content:i("autoScalingRule.SuccessfullyDeleted")})}).catch(be=>{const xe=Array.isArray(be)?be:[be];for(const Le of xe)d.error((Le==null?void 0:Le.message)||i("dialog.ErrorOccurred"))})},e[106]=W,e[107]=f,e[108]=Z,e[109]=d,e[110]=i,e[111]=$e):$e=e[111];let Qe;e[112]===Symbol.for("react.memo_cache_sentinel")?(Qe=()=>p(null),e[112]=Qe):Qe=e[112];let _e;e[113]!==Ve||e[114]!==Be||e[115]!==he||e[116]!==we||e[117]!==$e?(_e=n.jsx(hn,{open:Ve,title:Be,description:he,items:we,reversible:!0,onOk:$e,onCancel:Qe}),e[113]=Ve,e[114]=Be,e[115]=he,e[116]=we,e[117]=$e,e[118]=_e):_e=e[118];let qe;return e[119]!==se||e[120]!==Oe||e[121]!==_e?(qe=n.jsxs(n.Fragment,{children:[se,Oe,_e]}),e[119]=se,e[120]=Oe,e[121]=_e,e[122]=qe):qe=e[122],qe};function _i(l){return l}const Pt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentBasicInfoCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentBasicInfoCardDeleteMutation",selections:e},params:{cacheID:"70ed95e6d8ed42187398c9bc2c13f5bb",id:null,metadata:{},name:"DeploymentBasicInfoCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentBasicInfoCardDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Pt.hash="219d6f05b61219aeb47beff89d87a769";const Nt=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentBasicInfoCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[l],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentTagChips_metadata"}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null}})();Nt.hash="25c43526c832d75ea335a66d0e86f3af";const Vt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},i=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,r,t],kind:"Fragment",metadata:null,name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:i,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,r,e,a],kind:"Operation",name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:i,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},s,u,o,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u,o,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"b24d145b426294eb9cc72c268ccd1df2",id:null,metadata:{},name:"DeploymentSchedulingHistoryModalQuery",operationKind:"query",text:`query DeploymentSchedulingHistoryModalQuery(
  $scope: DeploymentScope!
  $filter: DeploymentHistoryFilter
  $orderBy: [DeploymentHistoryOrderBy!]
  $limit: Int
  $offset: Int
) {
  deploymentScopedSchedulingHistories(scope: $scope, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        ...BAIDeploymentSchedulingHistoryTableFragment
        id
      }
    }
  }
}

fragment BAIDeploymentSchedulingHistoryNodesFragment on DeploymentHistory {
  id
  category
  phase
  fromStatus
  toStatus
  result
  errorCode
  message
  attempts
  createdAt
  updatedAt
}

fragment BAIDeploymentSchedulingHistoryTableFragment on DeploymentHistory {
  id
  result
  subSteps {
    ...BAISubStepNodesFragment
  }
  ...BAIDeploymentSchedulingHistoryNodesFragment
}

fragment BAISubStepNodesFragment on SubStepResultGQL {
  step
  result
  errorCode
  message
  startedAt
  endedAt
}
`}}})();Vt.hash="89ec50bb9b1f834e59c642072090d378";const _t=Vt,Ei=l=>{"use memo";var Ke,Te,Ae,Ie;const e=We.c(113);let a,r,t,i,d;e[0]!==l?({open:i,queryRef:d,onReload:t,onCancel:r,...a}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5]);const{t:s}=Je(),[u,o]=Il(),[y,c]=O.useState(),[k,m]=O.useState("-updatedAt"),[g,f]=Cl("schedulingHistoryExpandMode"),[p,S]=Cl("table_column_overrides.DeploymentSchedulingHistory");let R;e[6]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[6]=R):R=e[6];const{tablePaginationOption:F,setTablePaginationOption:x}=xn(R),D=O.useDeferredValue(d),K=D!==d,C=Re.usePreloadedQuery(_t,D);let _;e[7]!==s?(_=s("deployment.DeploymentSchedulingHistory"),e[7]=s,e[8]=_):_=e[8];let H,z;e[9]===Symbol.for("react.memo_cache_sentinel")?(H={maxWidth:1600},z={body:{minHeight:"80vh"}},e[9]=H,e[10]=z):(H=e[9],z=e[10]);let L;e[11]!==t||e[12]!==d.variables||e[13]!==x?(L=ie=>{c(ie),x({current:1}),t({...d.variables,filter:ie,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=d.variables,e[13]=x,e[14]=L):L=e[14];let w;e[15]!==s?(w=s("deployment.ID"),e[15]=s,e[16]=w):w=e[16];let V;e[17]!==w?(V={key:"id",propertyLabel:w,type:"uuid",fixedOperator:"equals"},e[17]=w,e[18]=V):V=e[18];let T;e[19]!==s?(T=s("deployment.Phase"),e[19]=s,e[20]=T):T=e[20];let E;e[21]!==T?(E={key:"phase",propertyLabel:T,type:"string",fixedOperator:"contains"},e[21]=T,e[22]=E):E=e[22];let $;e[23]!==s?($=s("deployment.Result"),e[23]=s,e[24]=$):$=e[24];let Y;e[25]===Symbol.for("react.memo_cache_sentinel")?(Y=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=Y):Y=e[25];let U;e[26]!==$?(U={key:"result",propertyLabel:$,type:"enum",strictSelection:!0,options:Y},e[26]=$,e[27]=U):U=e[27];let q;e[28]!==s?(q=s("deployment.FromStatus"),e[28]=s,e[29]=q):q=e[29];let B;e[30]!==q?(B={key:"fromStatus",propertyLabel:q,type:"string",valueMode:"scalar"},e[30]=q,e[31]=B):B=e[31];let j;e[32]!==s?(j=s("deployment.ToStatus"),e[32]=s,e[33]=j):j=e[33];let b;e[34]!==j?(b={key:"toStatus",propertyLabel:j,type:"string",valueMode:"scalar"},e[34]=j,e[35]=b):b=e[35];let A;e[36]!==s?(A=s("deployment.ErrorCode"),e[36]=s,e[37]=A):A=e[37];let P;e[38]!==A?(P={key:"errorCode",propertyLabel:A,type:"string",fixedOperator:"contains"},e[38]=A,e[39]=P):P=e[39];let ne;e[40]!==s?(ne=s("deployment.Message"),e[40]=s,e[41]=ne):ne=e[41];let le;e[42]!==ne?(le={key:"message",propertyLabel:ne,type:"string",fixedOperator:"contains"},e[42]=ne,e[43]=le):le=e[43];let I;e[44]!==s?(I=s("deployment.CreatedAt"),e[44]=s,e[45]=I):I=e[45];let v;e[46]!==I?(v={key:"createdAt",propertyLabel:I,type:"datetime",defaultOperator:"after"},e[46]=I,e[47]=v):v=e[47];let N;e[48]!==s?(N=s("deployment.UpdatedAt"),e[48]=s,e[49]=N):N=e[49];let M;e[50]!==N?(M={key:"updatedAt",propertyLabel:N,type:"datetime",defaultOperator:"after"},e[50]=N,e[51]=M):M=e[51];let W;e[52]!==U||e[53]!==B||e[54]!==b||e[55]!==P||e[56]!==le||e[57]!==v||e[58]!==M||e[59]!==V||e[60]!==E?(W=[V,E,U,B,b,P,le,v,M],e[52]=U,e[53]=B,e[54]=b,e[55]=P,e[56]=le,e[57]=v,e[58]=M,e[59]=V,e[60]=E,e[61]=W):W=e[61];let J;e[62]!==y||e[63]!==W||e[64]!==L?(J=n.jsx(Gl,{value:y,onChange:L,filterProperties:W}),e[62]=y,e[63]=W,e[64]=L,e[65]=J):J=e[65];let Z;e[66]!==t||e[67]!==d.variables||e[68]!==o?(Z=ie=>{o(ie),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=o,e[69]=Z):Z=e[69];let ee;e[70]!==u||e[71]!==K||e[72]!==Z?(ee=n.jsx(te,{children:n.jsx(wl,{value:u,onChange:Z,loading:K,autoUpdateDelay:null})}),e[70]=u,e[71]=K,e[72]=Z,e[73]=ee):ee=e[73];let Q;e[74]!==J||e[75]!==ee?(Q=n.jsxs(te,{justify:"between",wrap:"wrap",gap:"sm",children:[J,ee]}),e[74]=J,e[75]=ee,e[76]=Q):Q=e[76];const ae=g??void 0;let Se;e[77]!==p||e[78]!==S?(Se={columnOverrides:p,onColumnOverridesChange:S},e[77]=p,e[78]=S,e[79]=Se):Se=e[79];let ge;e[80]!==t||e[81]!==d.variables||e[82]!==x?(ge=ie=>{m(ie),x({current:1}),t({...d.variables,orderBy:_l(ie),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=d.variables,e[82]=x,e[83]=ge):ge=e[83];const ye=((Ke=C.deploymentScopedSchedulingHistories)==null?void 0:Ke.count)??0;let de;e[84]!==t||e[85]!==d.variables||e[86]!==x?(de=(ie,Fe)=>{x({current:ie,pageSize:Fe}),t({...d.variables,limit:Fe,offset:ie>1?(ie-1)*Fe:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=d.variables,e[86]=x,e[87]=de):de=e[87];let pe;e[88]!==ye||e[89]!==de||e[90]!==F.current||e[91]!==F.pageSize?(pe={pageSize:F.pageSize,current:F.current,total:ye,onChange:de},e[88]=ye,e[89]=de,e[90]=F.current,e[91]=F.pageSize,e[92]=pe):pe=e[92];let ue;e[93]!==((Te=C.deploymentScopedSchedulingHistories)==null?void 0:Te.edges)?(ue=Rl((Ae=C.deploymentScopedSchedulingHistories)==null?void 0:Ae.edges,"node"),e[93]=(Ie=C.deploymentScopedSchedulingHistories)==null?void 0:Ie.edges,e[94]=ue):ue=e[94];let fe;e[95]!==K||e[96]!==k||e[97]!==f||e[98]!==ae||e[99]!==Se||e[100]!==ge||e[101]!==pe||e[102]!==ue?(fe=n.jsx(ui,{resizable:!0,loading:K,expandMode:ae,onExpandModeChange:f,tableSettings:Se,order:k,onChangeOrder:ge,pagination:pe,schedulingHistoryFrgmt:ue}),e[95]=K,e[96]=k,e[97]=f,e[98]=ae,e[99]=Se,e[100]=ge,e[101]=pe,e[102]=ue,e[103]=fe):fe=e[103];let ce;e[104]!==Q||e[105]!==fe?(ce=n.jsxs(te,{direction:"column",align:"stretch",gap:"sm",children:[Q,fe]}),e[104]=Q,e[105]=fe,e[106]=ce):ce=e[106];let ve;return e[107]!==a||e[108]!==r||e[109]!==i||e[110]!==_||e[111]!==ce?(ve=n.jsx(Hl,{title:_,open:i,width:"90%",style:H,styles:z,footer:null,onCancel:r,...a,children:ce}),e[107]=a,e[108]=r,e[109]=i,e[110]=_,e[111]=ce,e[112]=ve):ve=e[112],ve},Kl=()=>n.jsx(Xe.Text,{type:"secondary",children:"-"}),Oi=l=>{"use memo";var k,m,g;const e=We.c(26),{deployment:a,onClickSchedulingHistoryAction:r}=l,{t}=Je(),i=tn(),d=Rn(),s=((m=(k=a==null?void 0:a.metadata.projectV2)==null?void 0:k.basicInfo)==null?void 0:m.name)??(a==null?void 0:a.metadata.projectId);let u;if(e[0]!==d||e[1]!==a||e[2]!==r||e[3]!==s||e[4]!==t||e[5]!==i){const f=t("deployment.Visibility"),p=a==null?void 0:a.networkAccess.openToPublic;let S;e[7]!==t?(S=t("deployment.Public"),e[7]=t,e[8]=S):S=e[8];let R;e[9]!==t?(R=t("deployment.Private"),e[9]=t,e[10]=R):R=e[10];let F;e[11]===Symbol.for("react.memo_cache_sentinel")?(F=Kl(),e[11]=F):F=e[11];let x;e[12]!==p||e[13]!==S||e[14]!==R?(x=n.jsx(Qa,{value:p,trueLabel:S,falseLabel:R,fallback:F}),e[12]=p,e[13]=S,e[14]=R,e[15]=x):x=e[15];const D=t("deployment.Tags"),K=(a==null?void 0:a.metadata)??null;let C;e[16]!==d||e[17]!==i?(C=z=>{const L=d("deployments");i({pathname:L,search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:z}})}).toString()})},e[16]=d,e[17]=i,e[18]=C):C=e[18];let _;e[19]===Symbol.for("react.memo_cache_sentinel")?(_=Kl(),e[19]=_):_=e[19];let H;e[20]!==C||e[21]!==K?(H=n.jsx($a,{metadataFrgmt:K,onTagClick:C,fallback:_}),e[20]=C,e[21]=K,e[22]=H):H=e[22],u=nn([{key:"lifecycle",label:t("deployment.Lifecycle"),children:a!=null&&a.metadata.status?n.jsxs(te,{align:"center",gap:"xs",children:[n.jsx(st,{status:a.metadata.status}),r&&n.jsxs(n.Fragment,{children:[n.jsx(zn,{type:"vertical",style:{margin:0}}),n.jsx(kl,{type:"link",size:"small",icon:n.jsx(at,{}),style:{padding:0},action:async()=>{await r()},children:t("deployment.SchedulingHistory")})]})]}):Kl()},{key:"id",label:t("deployment.DeploymentId"),children:a!=null&&a.id?n.jsx(Nl,{globalId:a.id,copyable:!0,ellipsis:!1,style:{maxWidth:"none"}}):Kl()},{key:"project",label:t("deployment.Project"),children:s||Kl()},{key:"domain",label:t("deployment.Domain"),children:(a==null?void 0:a.metadata.domainName)||Kl()},{key:"resource-group",label:t("modelStore.ResourceGroup"),children:(a==null?void 0:a.metadata.resourceGroupName)||Kl()},{key:"endpoint-url",label:t("deployment.EndpointUrl"),children:a!=null&&a.networkAccess.endpointUrl?n.jsx(Xe.Text,{copyable:!0,style:{wordBreak:"break-all"},children:a.networkAccess.endpointUrl}):Kl()},{key:"visibility",label:f,children:x},{key:"desired-replicas",label:t("deployment.DesiredReplicas"),children:((g=a==null?void 0:a.replicaState)==null?void 0:g.desiredReplicaCount)??Kl()},{key:"tags",label:D,children:H}]),e[0]=d,e[1]=a,e[2]=r,e[3]=s,e[4]=t,e[5]=i,e[6]=u}else u=e[6];const o=u;let y;e[23]===Symbol.for("react.memo_cache_sentinel")?(y={xs:1,sm:1,md:2,lg:2,xl:2,xxl:2},e[23]=y):y=e[23];let c;return e[24]!==o?(c=n.jsx(va,{bordered:!0,column:y,items:o}),e[24]=o,e[25]=c):c=e[25],c},wi=l=>{"use memo";const e=We.c(101),{deploymentFrgmt:a,isPendingRefetch:r,onRefetch:t,autoUpdateDelay:i}=l,d=i===void 0?null:i,{t:s}=Je(),{message:u}=Pl.useApp(),{logger:o}=Ol(),y=tn(),c=Rn();let k;e[0]===Symbol.for("react.memo_cache_sentinel")?(k=Nt,e[0]=k):k=e[0];const m=Re.useFragment(k,a),[g,f]=O.useState(!1),[p,S]=O.useState(!1),[R,F]=O.useState(!1),[x,D]=Re.useQueryLoader(_t),K=Gn();let C;e[1]!==K?(C=(K==null?void 0:K.supports("deployment-scheduling-history"))??!1,e[1]=K,e[2]=C):C=e[2];const _=C;let H;e[3]===Symbol.for("react.memo_cache_sentinel")?(H=Pt,e[3]=H):H=e[3];const[z,L]=Re.useMutation(H),w=(m==null?void 0:m.metadata.name)??"",V=m==null?void 0:m.metadata.status;let T;e[4]!==c?(T=c("deployments"),e[4]=c,e[5]=T):T=e[5];const E=T;let $;e[6]!==z||e[7]!==m||e[8]!==E||e[9]!==o||e[10]!==u||e[11]!==s||e[12]!==y?($=()=>{m!=null&&m.id&&z({variables:{input:{id:ll(m.id)??m.id}},onCompleted:(je,He)=>{if(He&&He.length>0){o.error("Failed to delete deployment",He),u.error(s("deployment.FailedToDeleteDeployment"));return}u.success(s("deployment.DeploymentDeleted")),S(!1),y(E)},onError:je=>{o.error("Failed to delete deployment",je),u.error(s("deployment.FailedToDeleteDeployment"))}})},e[6]=z,e[7]=m,e[8]=E,e[9]=o,e[10]=u,e[11]=s,e[12]=y,e[13]=$):$=e[13];const Y=$;let U;e[14]!==s?(U=s("deployment.BasicInformation"),e[14]=s,e[15]=U):U=e[15];let q;e[16]!==d||e[17]!==r||e[18]!==t?(q=n.jsx(wl,{loading:r,value:"",onChange:t,autoUpdateDelay:d}),e[16]=d,e[17]=r,e[18]=t,e[19]=q):q=e[19];let B;e[20]===Symbol.for("react.memo_cache_sentinel")?(B=n.jsx(it,{}),e[20]=B):B=e[20];let j;e[21]!==V?(j=hl(V),e[21]=V,e[22]=j):j=e[22];let b;e[23]===Symbol.for("react.memo_cache_sentinel")?(b=async()=>{f(!0)},e[23]=b):b=e[23];let A;e[24]!==s?(A=s("button.Edit"),e[24]=s,e[25]=A):A=e[25];let P;e[26]!==j||e[27]!==A?(P=n.jsx(kl,{icon:B,disabled:j,action:b,children:A}),e[26]=j,e[27]=A,e[28]=P):P=e[28];let ne;e[29]===Symbol.for("react.memo_cache_sentinel")?(ne=["click"],e[29]=ne):ne=e[29];let le;e[30]!==s?(le=s("deployment.DeleteDeployment"),e[30]=s,e[31]=le):le=e[31];let I;e[32]===Symbol.for("react.memo_cache_sentinel")?(I=n.jsx(Sn,{}),e[32]=I):I=e[32];let v;e[33]!==V||e[34]!==L?(v=hl(V)||L,e[33]=V,e[34]=L,e[35]=v):v=e[35];let N;e[36]===Symbol.for("react.memo_cache_sentinel")?(N=()=>S(!0),e[36]=N):N=e[36];let M;e[37]!==le||e[38]!==v?(M={items:[{key:"delete",label:le,icon:I,danger:!0,disabled:v,onClick:N}]},e[37]=le,e[38]=v,e[39]=M):M=e[39];let W;e[40]===Symbol.for("react.memo_cache_sentinel")?(W=n.jsx(Yn,{}),e[40]=W):W=e[40];let J;e[41]!==s?(J=s("button.More"),e[41]=s,e[42]=J):J=e[42];let Z;e[43]!==J?(Z=n.jsx(ml,{icon:W,"aria-label":J}),e[43]=J,e[44]=Z):Z=e[44];let ee;e[45]!==M||e[46]!==Z?(ee=n.jsx(Xn,{trigger:ne,menu:M,children:Z}),e[45]=M,e[46]=Z,e[47]=ee):ee=e[47];let Q;e[48]!==P||e[49]!==ee?(Q=n.jsxs(Ql.Compact,{children:[P,ee]}),e[48]=P,e[49]=ee,e[50]=Q):Q=e[50];let ae;e[51]!==Q||e[52]!==q?(ae=n.jsxs(te,{gap:"xs",align:"center",children:[q,Q]}),e[51]=Q,e[52]=q,e[53]=ae):ae=e[53];let Se;e[54]===Symbol.for("react.memo_cache_sentinel")?(Se={body:{paddingTop:0}},e[54]=Se):Se=e[54];let ge;e[55]!==m||e[56]!==D||e[57]!==_?(ge=_&&(m!=null&&m.id)?async()=>{const je=m.id;je&&(D({scope:{deploymentId:Vl(je)??je},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),F(!0))}:void 0,e[55]=m,e[56]=D,e[57]=_,e[58]=ge):ge=e[58];let ye;e[59]!==m||e[60]!==ge?(ye=n.jsx(Oi,{deployment:m,onClickSchedulingHistoryAction:ge}),e[59]=m,e[60]=ge,e[61]=ye):ye=e[61];let de;e[62]!==ae||e[63]!==ye||e[64]!==U?(de=n.jsx(Wl,{title:U,extra:ae,styles:Se,children:ye}),e[62]=ae,e[63]=ye,e[64]=U,e[65]=de):de=e[65];let pe;e[66]!==t?(pe=je=>{f(!1),je&&t()},e[66]=t,e[67]=pe):pe=e[67];let ue;e[68]!==m||e[69]!==g||e[70]!==pe?(ue=n.jsx(ha,{open:g,deploymentFrgmt:m,onRequestClose:pe}),e[68]=m,e[69]=g,e[70]=pe,e[71]=ue):ue=e[71];let fe;e[72]!==s?(fe=s("deployment.DeleteDeployment"),e[72]=s,e[73]=fe):fe=e[73];let ce;e[74]!==s?(ce=s("deployment.Deployment"),e[74]=s,e[75]=ce):ce=e[75];let ve;e[76]!==w?(ve=w?[{key:w,label:w}]:[],e[76]=w,e[77]=ve):ve=e[77];let Ke;e[78]!==w?(Ke={placeholder:w},e[78]=w,e[79]=Ke):Ke=e[79];let Te;e[80]!==L?(Te={loading:L},e[80]=L,e[81]=Te):Te=e[81];let Ae;e[82]===Symbol.for("react.memo_cache_sentinel")?(Ae=()=>S(!1),e[82]=Ae):Ae=e[82];let Ie;e[83]!==w||e[84]!==Y||e[85]!==p||e[86]!==fe||e[87]!==ce||e[88]!==ve||e[89]!==Ke||e[90]!==Te?(Ie=n.jsx(hn,{open:p,title:fe,target:ce,items:ve,confirmText:w,requireConfirmInput:!0,inputProps:Ke,okButtonProps:Te,onOk:Y,onCancel:Ae}),e[83]=w,e[84]=Y,e[85]=p,e[86]=fe,e[87]=ce,e[88]=ve,e[89]=Ke,e[90]=Te,e[91]=Ie):Ie=e[91];let ie;e[92]!==x||e[93]!==R||e[94]!==D?(ie=x!=null&&n.jsx(fl,{children:n.jsx(Ei,{open:R,queryRef:x,onReload:D,onCancel:()=>F(!1)})}),e[92]=x,e[93]=R,e[94]=D,e[95]=ie):ie=e[95];let Fe;return e[96]!==de||e[97]!==ue||e[98]!==Ie||e[99]!==ie?(Fe=n.jsxs(n.Fragment,{children:[de,ue,Ie,ie]}),e[96]=de,e[97]=ue,e[98]=Ie,e[99]=ie,e[100]=Fe):Fe=e[100],Fe},Et=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},i=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"sessionId",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"revisionId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"trafficStatus",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"healthStatus",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},S={alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"sessionV2",plural:!1,selections:[u,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[p],storageKey:null}],storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},F=[p,R],x={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},K={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[u,p,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,r,t],kind:"Fragment",metadata:null,name:"DeploymentReplicasCardListQuery",selections:[{alias:null,args:i,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,y,c,k,m,g,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[u,f,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null},S],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,a,r],kind:"Operation",name:"DeploymentReplicasCardListQuery",selections:[{alias:null,args:i,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,y,c,k,m,g,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[u,f,g,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:F,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[p,u],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:F,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},R,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[x,D,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},K],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[x,D,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},K],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},S],storageKey:null}],storageKey:null}],storageKey:null},u],storageKey:null}]},params:{cacheID:"79f688ce3d9ffc3c72881648d7d76eab",id:null,metadata:{},name:"DeploymentReplicasCardListQuery",operationKind:"query",text:`query DeploymentReplicasCardListQuery(
  $deploymentId: ID!
  $filter: ReplicaFilter
  $orderBy: [ReplicaOrderBy!]
  $limit: Int
  $offset: Int
) {
  deployment(id: $deploymentId) {
    replicas(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
      count
      edges {
        node {
          id
          sessionId
          revisionId
          status
          trafficStatus
          healthStatus
          createdAt
          revision {
            id
            revisionNumber
            ...DeploymentRevisionDetail_revision
          }
          sessionV2 @since(version: "26.4.3") {
            id
            metadata {
              name
            }
          }
        }
      }
    }
    id
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
      architecture
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}})();Et.hash="3c889ebaa68c08cff62a842b2869be6a";const Ot={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentReplicasCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};Ot.hash="c535e4dd070869785c37a4074751984b";const Hi={HEALTHY:"success",UNHEALTHY:"error",DEGRADED:"warning",NOT_CHECKED:"default",PROVISIONING:"processing",WARMING_UP:"processing",RUNNING:"success",TERMINATING:"warning",TERMINATED:"default",FAILED_TO_START:"error"},Bi={HEALTHY:"Healthy",UNHEALTHY:"Unhealthy",DEGRADED:"Degraded",NOT_CHECKED:"NotChecked",PROVISIONING:"Provisioning",WARMING_UP:"WarmingUp",RUNNING:"Running",TERMINATING:"Terminating",TERMINATED:"Terminated",FAILED_TO_START:"FailedToStart"},_n=l=>{"use memo";const e=We.c(23);let a,r,t;e[0]!==l?({status:a,showTooltip:r,...t}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t):(a=e[1],r=e[2],t=e[3]);const i=r===void 0?!0:r,{t:d}=Je(),s=Hi[a],u=Bi[a],o=`replicaStatus.${u}`;let y;e[4]!==d||e[5]!==o?(y=d(o),e[4]=d,e[5]=o,e[6]=y):y=e[6];const c=y;let k;e[7]!==u||e[8]!==i||e[9]!==d?(k=i?d(`replicaStatus.tooltip.${u}`,{defaultValue:""}):void 0,e[7]=u,e[8]=i,e[9]=d,e[10]=k):k=e[10];const m=k;let g;e[11]!==a?(g=a==="WARMING_UP"?n.jsx(bn,{spin:!0}):void 0,e[11]=a,e[12]=g):g=e[12];const f=g;let p;e[13]!==s||e[14]!==f||e[15]!==c||e[16]!==t?(p=n.jsx(en,{...t,color:s,icon:f,children:c}),e[13]=s,e[14]=f,e[15]=c,e[16]=t,e[17]=p):p=e[17];const S=p;if(!i||!m)return S;let R;e[18]!==S?(R=n.jsx("span",{children:S}),e[18]=S,e[19]=R):R=e[19];let F;return e[20]!==R||e[21]!==m?(F=n.jsx(cl,{title:m,children:R}),e[20]=R,e[21]=m,e[22]=F):F=e[22],F},wt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},i=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,r,t],kind:"Fragment",metadata:null,name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:i,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,r,e,a],kind:"Operation",name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:i,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},s,u,o,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u,o,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"e02133438de747b29f05fb0c3109339d",id:null,metadata:{},name:"RouteSchedulingHistoryModalQuery",operationKind:"query",text:`query RouteSchedulingHistoryModalQuery(
  $scope: RouteScope!
  $filter: RouteHistoryFilter
  $orderBy: [RouteHistoryOrderBy!]
  $limit: Int
  $offset: Int
) {
  routeScopedSchedulingHistories(scope: $scope, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        ...BAIRouteSchedulingHistoryTableFragment
        id
      }
    }
  }
}

fragment BAIRouteSchedulingHistoryNodeTableFragment on RouteHistory {
  id
  category
  phase
  fromStatus
  toStatus
  result
  errorCode
  message
  attempts
  createdAt
  updatedAt
}

fragment BAIRouteSchedulingHistoryTableFragment on RouteHistory {
  id
  result
  subSteps {
    ...BAISubStepNodesFragment
  }
  ...BAIRouteSchedulingHistoryNodeTableFragment
}

fragment BAISubStepNodesFragment on SubStepResultGQL {
  step
  result
  errorCode
  message
  startedAt
  endedAt
}
`}}})();wt.hash="e770c8de50ced262d1f75ecd5be88c57";const Ht=wt,$i=l=>{"use memo";var Ke,Te,Ae,Ie;const e=We.c(113);let a,r,t,i,d;e[0]!==l?({open:i,queryRef:d,onReload:t,onCancel:r,...a}=l,e[0]=l,e[1]=a,e[2]=r,e[3]=t,e[4]=i,e[5]=d):(a=e[1],r=e[2],t=e[3],i=e[4],d=e[5]);const{t:s}=Je(),[u,o]=Il(),[y,c]=O.useState(),[k,m]=O.useState("-updatedAt"),[g,f]=Cl("schedulingHistoryExpandMode"),[p,S]=Cl("table_column_overrides.RouteSchedulingHistory");let R;e[6]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[6]=R):R=e[6];const{tablePaginationOption:F,setTablePaginationOption:x}=xn(R),D=O.useDeferredValue(d),K=D!==d,C=Re.usePreloadedQuery(Ht,D);let _;e[7]!==s?(_=s("route.RouteSchedulingHistory"),e[7]=s,e[8]=_):_=e[8];let H,z;e[9]===Symbol.for("react.memo_cache_sentinel")?(H={maxWidth:1600},z={body:{minHeight:"80vh"}},e[9]=H,e[10]=z):(H=e[9],z=e[10]);let L;e[11]!==t||e[12]!==d.variables||e[13]!==x?(L=ie=>{c(ie),x({current:1}),t({...d.variables,filter:ie,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=d.variables,e[13]=x,e[14]=L):L=e[14];let w;e[15]!==s?(w=s("route.ID"),e[15]=s,e[16]=w):w=e[16];let V;e[17]!==w?(V={key:"id",propertyLabel:w,type:"uuid",fixedOperator:"equals"},e[17]=w,e[18]=V):V=e[18];let T;e[19]!==s?(T=s("route.Phase"),e[19]=s,e[20]=T):T=e[20];let E;e[21]!==T?(E={key:"phase",propertyLabel:T,type:"string",fixedOperator:"contains"},e[21]=T,e[22]=E):E=e[22];let $;e[23]!==s?($=s("route.Result"),e[23]=s,e[24]=$):$=e[24];let Y;e[25]===Symbol.for("react.memo_cache_sentinel")?(Y=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=Y):Y=e[25];let U;e[26]!==$?(U={key:"result",propertyLabel:$,type:"enum",strictSelection:!0,options:Y},e[26]=$,e[27]=U):U=e[27];let q;e[28]!==s?(q=s("route.FromStatus"),e[28]=s,e[29]=q):q=e[29];let B;e[30]!==q?(B={key:"fromStatus",propertyLabel:q,type:"string",valueMode:"scalar"},e[30]=q,e[31]=B):B=e[31];let j;e[32]!==s?(j=s("route.ToStatus"),e[32]=s,e[33]=j):j=e[33];let b;e[34]!==j?(b={key:"toStatus",propertyLabel:j,type:"string",valueMode:"scalar"},e[34]=j,e[35]=b):b=e[35];let A;e[36]!==s?(A=s("route.ErrorCode"),e[36]=s,e[37]=A):A=e[37];let P;e[38]!==A?(P={key:"errorCode",propertyLabel:A,type:"string",fixedOperator:"contains"},e[38]=A,e[39]=P):P=e[39];let ne;e[40]!==s?(ne=s("route.Message"),e[40]=s,e[41]=ne):ne=e[41];let le;e[42]!==ne?(le={key:"message",propertyLabel:ne,type:"string",fixedOperator:"contains"},e[42]=ne,e[43]=le):le=e[43];let I;e[44]!==s?(I=s("route.CreatedAt"),e[44]=s,e[45]=I):I=e[45];let v;e[46]!==I?(v={key:"createdAt",propertyLabel:I,type:"datetime",defaultOperator:"after"},e[46]=I,e[47]=v):v=e[47];let N;e[48]!==s?(N=s("route.UpdatedAt"),e[48]=s,e[49]=N):N=e[49];let M;e[50]!==N?(M={key:"updatedAt",propertyLabel:N,type:"datetime",defaultOperator:"after"},e[50]=N,e[51]=M):M=e[51];let W;e[52]!==U||e[53]!==B||e[54]!==b||e[55]!==P||e[56]!==le||e[57]!==v||e[58]!==M||e[59]!==V||e[60]!==E?(W=[V,E,U,B,b,P,le,v,M],e[52]=U,e[53]=B,e[54]=b,e[55]=P,e[56]=le,e[57]=v,e[58]=M,e[59]=V,e[60]=E,e[61]=W):W=e[61];let J;e[62]!==y||e[63]!==W||e[64]!==L?(J=n.jsx(Gl,{value:y,onChange:L,filterProperties:W}),e[62]=y,e[63]=W,e[64]=L,e[65]=J):J=e[65];let Z;e[66]!==t||e[67]!==d.variables||e[68]!==o?(Z=ie=>{o(ie),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=o,e[69]=Z):Z=e[69];let ee;e[70]!==u||e[71]!==K||e[72]!==Z?(ee=n.jsx(te,{children:n.jsx(wl,{value:u,onChange:Z,loading:K,autoUpdateDelay:null})}),e[70]=u,e[71]=K,e[72]=Z,e[73]=ee):ee=e[73];let Q;e[74]!==J||e[75]!==ee?(Q=n.jsxs(te,{justify:"between",wrap:"wrap",gap:"sm",children:[J,ee]}),e[74]=J,e[75]=ee,e[76]=Q):Q=e[76];const ae=g??void 0;let Se;e[77]!==p||e[78]!==S?(Se={columnOverrides:p,onColumnOverridesChange:S},e[77]=p,e[78]=S,e[79]=Se):Se=e[79];let ge;e[80]!==t||e[81]!==d.variables||e[82]!==x?(ge=ie=>{m(ie),x({current:1}),t({...d.variables,orderBy:_l(ie),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=d.variables,e[82]=x,e[83]=ge):ge=e[83];const ye=((Ke=C.routeScopedSchedulingHistories)==null?void 0:Ke.count)??0;let de;e[84]!==t||e[85]!==d.variables||e[86]!==x?(de=(ie,Fe)=>{x({current:ie,pageSize:Fe}),t({...d.variables,limit:Fe,offset:ie>1?(ie-1)*Fe:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=d.variables,e[86]=x,e[87]=de):de=e[87];let pe;e[88]!==ye||e[89]!==de||e[90]!==F.current||e[91]!==F.pageSize?(pe={pageSize:F.pageSize,current:F.current,total:ye,onChange:de},e[88]=ye,e[89]=de,e[90]=F.current,e[91]=F.pageSize,e[92]=pe):pe=e[92];let ue;e[93]!==((Te=C.routeScopedSchedulingHistories)==null?void 0:Te.edges)?(ue=Rl((Ae=C.routeScopedSchedulingHistories)==null?void 0:Ae.edges,"node"),e[93]=(Ie=C.routeScopedSchedulingHistories)==null?void 0:Ie.edges,e[94]=ue):ue=e[94];let fe;e[95]!==K||e[96]!==k||e[97]!==f||e[98]!==ae||e[99]!==Se||e[100]!==ge||e[101]!==pe||e[102]!==ue?(fe=n.jsx(ci,{resizable:!0,loading:K,expandMode:ae,onExpandModeChange:f,tableSettings:Se,order:k,onChangeOrder:ge,pagination:pe,schedulingHistoryFrgmt:ue}),e[95]=K,e[96]=k,e[97]=f,e[98]=ae,e[99]=Se,e[100]=ge,e[101]=pe,e[102]=ue,e[103]=fe):fe=e[103];let ce;e[104]!==Q||e[105]!==fe?(ce=n.jsxs(te,{direction:"column",align:"stretch",gap:"sm",children:[Q,fe]}),e[104]=Q,e[105]=fe,e[106]=ce):ce=e[106];let ve;return e[107]!==a||e[108]!==r||e[109]!==i||e[110]!==_||e[111]!==ce?(ve=n.jsx(Hl,{title:_,open:i,width:"90%",style:H,styles:z,footer:null,onCancel:r,...a,children:ce}),e[107]=a,e[108]=r,e[109]=i,e[110]=_,e[111]=ce,e[112]=ve):ve=e[112],ve},En=["TERMINATED","FAILED_TO_START"],qi=l=>l==="terminated"?{status:{in:[...En]}}:{status:{notIn:[...En]}},on=(l,e)=>({...l,...qi(e)}),yn=["createdAt","id"],Qi=[...yn,...yn.map(l=>`-${l}`)],On=l=>pn(yn,l),dn=l=>l??"NOT_CHECKED",zi=l=>{"use memo";const e=We.c(21),{deploymentFrgmt:a,deploymentId:r,replicaFetchKey:t}=l,{t:i}=Je(),{token:d}=Dl.useToken();let s;e[0]!==i?(s=i("deployment.tab.Replicas"),e[0]=i,e[1]=s):s=e[1];let u;e[2]!==i?(u=i("deployment.tab.description.Replicas"),e[2]=i,e[3]=u):u=e[3];let o;e[4]!==d.colorTextDescription?(o=n.jsx(fn,{style:{color:d.colorTextDescription}}),e[4]=d.colorTextDescription,e[5]=o):o=e[5];let y;e[6]!==u||e[7]!==o?(y=n.jsx(cl,{title:u,children:o}),e[6]=u,e[7]=o,e[8]=y):y=e[8];let c;e[9]!==s||e[10]!==y?(c=n.jsxs(te,{gap:"xs",align:"center",children:[s,y]}),e[9]=s,e[10]=y,e[11]=c):c=e[11];let k;e[12]===Symbol.for("react.memo_cache_sentinel")?(k={body:{paddingTop:0}},e[12]=k):k=e[12];let m;e[13]===Symbol.for("react.memo_cache_sentinel")?(m=n.jsx(xl,{active:!0}),e[13]=m):m=e[13];let g;e[14]!==a||e[15]!==r||e[16]!==t?(g=n.jsx(Jn,{children:n.jsx(O.Suspense,{fallback:m,children:n.jsx(Ui,{deploymentFrgmt:a,deploymentId:r,replicaFetchKey:t})})}),e[14]=a,e[15]=r,e[16]=t,e[17]=g):g=e[17];let f;return e[18]!==c||e[19]!==g?(f=n.jsx(Wl,{title:c,styles:k,children:g}),e[18]=c,e[19]=g,e[20]=f):f=e[20],f},Ui=({deploymentFrgmt:l,deploymentId:e,replicaFetchKey:a})=>{"use memo";var U,q,B,j;const{t:r}=Je(),[t,i]=O.useTransition(),[d,s]=Cl("table_column_overrides.DeploymentReplicasTab"),[u,o]=Fn({current:ln.withDefault(1),pageSize:ln.withDefault(10),order:Ul(Qi),rFilter:Zn,rStatusCategory:Ul(["running","terminated"]).withDefault("running")},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rOrder",rFilter:"rFilter",rStatusCategory:"rStatusCategory"}});Re.useFragment(Ot,l);const y=b=>{if(!b)return null;try{const A=JSON.parse(b);return A&&typeof A=="object"&&!Array.isArray(A)?A:null}catch{return null}},c=b=>!b||Object.keys(b).length===0?"":JSON.stringify(b),[k,m]=O.useState(()=>({filter:on(u.rFilter?y(u.rFilter):null,u.rStatusCategory),orderBy:_l(u.order||"-createdAt"),limit:u.pageSize,offset:u.current>1?(u.current-1)*u.pageSize:0})),[g,f]=O.useState(0),p=g===0&&(a===void 0||a===zl),R=Gn().supports("route-scheduling-history"),[F,x]=O.useState(!1),[D,K]=Re.useQueryLoader(Ht),[C,_]=O.useState(null),[H,z]=O.useState(null),{deployment:L}=Re.useLazyLoadQuery(Et,{deploymentId:e,...k},{fetchKey:`${g}-${a??""}`,fetchPolicy:p?"store-and-network":"network-only"}),w=((B=(q=(U=L==null?void 0:L.replicas)==null?void 0:U.edges)==null?void 0:q.map(b=>b==null?void 0:b.node))==null?void 0:B.filter(b=>!!b))??[],V=b=>{i(()=>{m(A=>({...A,...b}))})},T=[{label:r("replicaStatus.Active"),value:"ACTIVE"},{label:r("replicaStatus.Inactive"),value:"INACTIVE"}],E=[{key:"trafficStatus",propertyLabel:r("deployment.TrafficStatus"),type:"enum",options:T,strictSelection:!0}],$=u.rFilter?y(u.rFilter)??void 0:void 0,Y=nn([{key:"id",title:r("deployment.ReplicaId"),dataIndex:"id",fixed:"left",sorter:On("id"),render:b=>n.jsx(Nl,{globalId:b,copyable:!0})},{key:"status",title:n.jsxs(te,{gap:"xxs",align:"center",children:[r("deployment.ReplicaLifecycle"),n.jsx(pl,{title:r("deployment.ReplicaLifecycleStatusTooltip")})]}),dataIndex:"status",render:(b,A)=>n.jsxs(te,{align:"center",gap:"xs",children:[n.jsx(_n,{status:dn(b)}),R&&n.jsx(cl,{title:r("route.RouteSchedulingHistory"),children:n.jsx(kl,{type:"link",icon:n.jsx(at,{}),size:"small",style:{padding:0},action:async()=>{const P=Vl(A.id)??A.id;K({scope:{routeId:P},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),x(!0)}})})]})},{key:"healthStatus",title:n.jsxs(te,{gap:"xxs",align:"center",children:[r("deployment.HealthStatus"),n.jsx(pl,{title:r("deployment.HealthStatusTooltip")})]}),dataIndex:"healthStatus",render:(b,A)=>n.jsx(_n,{status:dn(b),showTooltip:dn(A.status)!=="TERMINATED"})},{key:"trafficStatus",title:n.jsxs(te,{gap:"xxs",align:"center",children:[r("deployment.TrafficStatus"),n.jsx(pl,{title:r("deployment.TrafficStatusTooltip")})]}),dataIndex:"trafficStatus",render:b=>n.jsx(en,{color:b==="ACTIVE"?"success":"default",children:r(b==="ACTIVE"?"replicaStatus.Active":"replicaStatus.Inactive")})},{key:"session",title:r("general.Session"),onCell:()=>({style:{maxWidth:240}}),render:(b,A)=>{var le;const P=A.sessionV2;if(!(P!=null&&P.id))return n.jsx(Xe.Text,{type:"secondary",children:"—"});const ne=(le=P.metadata)==null?void 0:le.name;return ne?n.jsxs(n.Fragment,{children:[n.jsx(Fa,{ellipsis:!0,onClick:()=>_(ll(P.id)),style:{maxWidth:160},children:ne})," ",n.jsxs(Xe.Text,{type:"secondary",children:["(",n.jsx(Nl,{globalId:P.id,type:"secondary"}),")"]})]}):n.jsx(Nl,{globalId:P.id})}},{key:"revision",title:n.jsxs(te,{gap:"xxs",align:"center",children:[r("deployment.RevisionNumberWithID"),n.jsx(pl,{title:r("deployment.RevisionNumberTooltip")})]}),render:(b,A)=>{const P=A.revision;return P!=null&&P.id?n.jsxs(n.Fragment,{children:[n.jsx(Xe.Link,{onClick:()=>z(P),children:P.revisionNumber!=null?`#${P.revisionNumber}`:"-"})," ",n.jsxs(Xe.Text,{type:"secondary",children:["(",n.jsx(Nl,{globalId:P.id,type:"secondary"}),")"]})]}):n.jsx(Xe.Text,{type:"secondary",children:"—"})}},{key:"createdAt",title:r("deployment.CreatedAt"),dataIndex:"createdAt",sorter:On("createdAt"),render:b=>b?dl(b).format("lll"):"-"}]);return n.jsxs(n.Fragment,{children:[n.jsxs(te,{justify:"between",align:"center",gap:"xs",style:{marginBottom:12},children:[n.jsxs(te,{gap:"sm",align:"start",wrap:"wrap",style:{flexShrink:1},children:[n.jsx(xa,{value:u.rStatusCategory,onChange:b=>{const A=b.target.value,P=u.rFilter?y(u.rFilter):null;o({rStatusCategory:A,current:1}),V({filter:on(P,A),offset:0})},options:[{label:r("deployment.Running"),value:"running"},{label:r("deployment.status.Terminated"),value:"terminated"}]}),n.jsx(Gl,{filterProperties:E,value:$,onChange:b=>{const A=c(b);o({rFilter:A||null,current:1}),V({filter:on(b??null,u.rStatusCategory),offset:0})}})]}),n.jsx(Ra,{settingId:"deployment-replicas",defaultAutoUpdateDelay:1e4,loading:t,value:"",onChange:()=>{i(()=>f(b=>b+1))}})]}),n.jsx(El,{rowKey:b=>b.id,dataSource:w,columns:Y,loading:t,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:d,onColumnOverridesChange:s},order:u.order,onChangeOrder:b=>{o({order:b??null}),V({orderBy:_l(b||"-createdAt")})},pagination:{pageSize:u.pageSize,current:u.current,total:((j=L==null?void 0:L.replicas)==null?void 0:j.count)??0,onChange:(b,A)=>{o({current:b,pageSize:A});const P=b>1?(b-1)*A:0;V({limit:A,offset:P})}}}),n.jsx(fl,{children:n.jsx(Ba,{open:!!C,sessionId:C??void 0,onClose:()=>_(null)})}),n.jsx(fl,{children:n.jsx(an,{open:!!H,revisionFrgmt:H,onClose:()=>z(null)})}),D!=null&&n.jsx(fl,{children:n.jsx($i,{open:F,queryRef:D,onReload:K,onCancel:()=>x(!1)})})]})},Bt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentCurrentRevisionTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionHistoryTab_deployment"}],type:"ModelDeployment",abstractKey:null};Bt.hash="2a36e018f7a8b5999cad5c828ae16666";const Wi=l=>{"use memo";const e=We.c(18),{deploymentId:a}=l,[r,t]=Re.useQueryLoader(za);let i;e[0]===Symbol.for("react.memo_cache_sentinel")?(i={current:1,pageSize:10},e[0]=i):i=e[0];const{baiPaginationOption:d,setTablePaginationOption:s}=xn(i);let u;e[1]!==t||e[2]!==s?(u=(S,R)=>{const F=S.limit??10;s({pageSize:F,current:S.offset?Math.floor(S.offset/F)+1:1}),t(S,R)},e[1]=t,e[2]=s,e[3]=u):u=e[3];const o=u;let y;e[4]!==d.limit||e[5]!==d.offset||e[6]!==a||e[7]!==t?(y=()=>{t({scope:{entity:[{entityType:"MODEL_DEPLOYMENT",entityId:Vl(a)??a}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:d.limit,offset:d.offset},{fetchPolicy:"store-and-network"})},e[4]=d.limit,e[5]=d.offset,e[6]=a,e[7]=t,e[8]=y):y=e[8];const c=y;let k;e[9]!==c?(k=()=>{c()},e[9]=c,e[10]=k):k=e[10];const m=O.useEffectEvent(k);let g;e[11]!==m?(g=()=>{m()},e[11]=m,e[12]=g):g=e[12];let f;e[13]!==a?(f=[a],e[13]=a,e[14]=f):f=e[14],O.useEffect(g,f);let p;return e[15]!==r||e[16]!==o?(p=n.jsx(Jn,{children:r?n.jsx(O.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:4}}),children:n.jsx(Ua,{queryRef:r,onReload:o,tableSettings:{}})}):n.jsx(xl,{active:!0,paragraph:{rows:4}})}),e[15]=r,e[16]=o,e[17]=p):p=e[17],p},$t=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e=[l,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentCurrentRevisionTab_deployment",selections:[l,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:e,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:e,storageKey:null}],type:"ModelDeployment",abstractKey:null}})();$t.hash="81029f15aa0beb8289a21e0ca51303ff";const Gi=l=>{"use memo";const e=We.c(21),{deploymentFrgmt:a}=l,{t:r}=Je(),{token:t}=Dl.useToken();let i;e[0]===Symbol.for("react.memo_cache_sentinel")?(i=$t,e[0]=i):i=e[0];const d=Re.useFragment(i,a),[s,u]=O.useState(null);let o;e[1]===Symbol.for("react.memo_cache_sentinel")?(o=(C,_,H)=>{u({revisionFrgmt:C,status:_,title:H})},e[1]=o):o=e[1];const y=o,c=d==null?void 0:d.currentRevision,k=d==null?void 0:d.deployingRevision,m=!!k&&k.id!==(c==null?void 0:c.id);let g;e[2]!==k||e[3]!==m||e[4]!==r||e[5]!==t?(g=m&&n.jsx(Tl,{type:"info",icon:n.jsx(bn,{spin:!0}),showIcon:!0,style:{marginBottom:t.marginMD},title:r("deployment.ApplyingRevision",{revisionNumber:k.revisionNumber!=null?`#${k.revisionNumber}`:ll(k.id)??""}),action:n.jsx(ml,{onClick:()=>y(k,"deploying",r("deployment.ApplyingRevisionDetail")),children:r("deployment.ViewRevision")})}),e[2]=k,e[3]=m,e[4]=r,e[5]=t,e[6]=g):g=e[6];let f;e[7]!==c||e[8]!==m||e[9]!==r?(f=c?n.jsx(qa,{revisionFrgmt:c,status:"current"}):m?null:n.jsx(An,{image:An.PRESENTED_IMAGE_SIMPLE,description:r("deployment.NoCurrentRevisionDeployed")}),e[7]=c,e[8]=m,e[9]=r,e[10]=f):f=e[10];const p=s==null?void 0:s.revisionFrgmt,S=s==null?void 0:s.status,R=s==null?void 0:s.title,F=!!s;let x;e[11]===Symbol.for("react.memo_cache_sentinel")?(x=()=>u(null),e[11]=x):x=e[11];let D;e[12]!==p||e[13]!==S||e[14]!==R||e[15]!==F?(D=n.jsx(fl,{children:n.jsx(an,{revisionFrgmt:p,status:S,title:R,open:F,onClose:x})}),e[12]=p,e[13]=S,e[14]=R,e[15]=F,e[16]=D):D=e[16];let K;return e[17]!==D||e[18]!==g||e[19]!==f?(K=n.jsxs(n.Fragment,{children:[g,f,D]}),e[17]=D,e[18]=g,e[19]=f,e[20]=K):K=e[20],K},qt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},i=[a,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],d={alias:null,args:null,kind:"ScalarField",name:"previousRevisionId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"activatedRevisionId",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},y=[u,o],c={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},m={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,u,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},g=[a,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:y,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[u,a],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:y,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},o,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},a],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[c,k,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},m],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[c,k,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},m],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,r,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:i,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:i,storageKey:null}],storageKey:null},d,s],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,r,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:g,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:g,storageKey:null}],storageKey:null},d,s],storageKey:null}]},params:{cacheID:"484c885f3fb5c0c9f4a4e12f257a49e6",id:null,metadata:{},name:"DeploymentRevisionHistoryTabActivateMutation",operationKind:"mutation",text:`mutation DeploymentRevisionHistoryTabActivateMutation(
  $input: ActivateRevisionInput!
) {
  activateDeploymentRevision(input: $input) {
    deployment {
      id
      currentRevisionId
      deployingRevisionId
      currentRevision @since(version: "26.4.3") {
        id
        ...DeploymentRevisionDetail_revision
      }
      deployingRevision @since(version: "26.4.3") {
        id
        ...DeploymentRevisionDetail_revision
      }
    }
    previousRevisionId
    activatedRevisionId
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
      architecture
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}})();qt.hash="153c096cf78b28827d7a04ef0f1610d4";const Qt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},i=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},m={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,concreteType:"ModelMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[y,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},F=[g,R],x={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[y,g,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},K={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,r,t],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:i,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,s,{alias:null,args:u,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[y,c,k,m,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[g],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[g,f],storageKey:null}],storageKey:null},p,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[S,{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[y,g,{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,a,r],kind:"Operation",name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:i,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,s,{alias:null,args:u,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[y,c,k,m,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[g,y],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:F,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},R,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},y],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[g,f,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},p,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[S,x,D,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},K,{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:F,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[S,D,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},x],storageKey:null},p,K],storageKey:null}],storageKey:null}],storageKey:null},y],storageKey:null}]},params:{cacheID:"33ba9a0de55569323004cce82b1cc474",id:null,metadata:{},name:"DeploymentRevisionHistoryTabListQuery",operationKind:"query",text:`query DeploymentRevisionHistoryTabListQuery(
  $deploymentId: ID!
  $filter: ModelRevisionFilter
  $orderBy: [ModelRevisionOrderBy!]
  $limit: Int
  $offset: Int
) {
  deployment(id: $deploymentId) {
    currentRevisionId
    deployingRevisionId
    revisionHistory(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
      count
      edges {
        node {
          id
          revisionNumber
          createdAt
          clusterConfig {
            mode
            size
          }
          modelRuntimeConfig {
            runtimeVariant {
              name
              id
            }
          }
          modelDefinition {
            models {
              name
              metadata {
                version
              }
            }
          }
          imageV2 {
            id
            identity {
              canonicalName
              architecture
            }
          }
          modelMountConfig {
            vfolderId
            vfolder {
              id
              name
              ...FolderLink_vfolderNode
            }
          }
          ...DeploymentRevisionDetail_revision
          ...DeploymentAddRevisionModal_revisionSource
        }
      }
    }
    id
  }
}

fragment DeploymentAddRevisionModal_revisionSource on ModelRevision {
  clusterConfig {
    mode
    size
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  resourceSlots {
    slotName
    quantity
  }
  extraMounts {
    vfolderId
    mountDestination
  }
  modelRuntimeConfig {
    runtimeVariantId
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          enable @since(version: "26.4.4")
          path
          maxRetries
          initialDelay
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
  imageV2 {
    id
    identity {
      canonicalName
      architecture
    }
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
      architecture
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}})();Qt.hash="dc7544cf74c6e7b71663a4998c4d880c";const zt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"}],type:"ModelDeployment",abstractKey:null};zt.hash="6d00d8056ec0eba0eea404e554242adf";const wn=["revisionNumber","createdAt","clusterMode","runtimeVariantName"],Yi=[...wn,...wn.map(l=>`-${l}`)],Xi=({deploymentFrgmt:l,deploymentId:e,fetchKey:a})=>{"use memo";var le;const{t:r}=Je(),{token:t}=Dl.useToken(),{message:i}=Pl.useApp(),{logger:d}=Ol(),[s,u]=O.useTransition(),[o,y]=O.useState(null),[c,k]=O.useState(null),[m,g]=O.useState(null),[f,p]=Cl("table_column_overrides.DeploymentRevisionHistoryTab"),[S,R]=Fn({current:ln.withDefault(1),pageSize:ln.withDefault(10),order:Ul(Yi),rvFilter:Zn},{history:"replace",urlKeys:{current:"rvCurrent",pageSize:"rvPageSize",order:"rvOrder",rvFilter:"rvFilter"}}),F=Re.useFragment(zt,l),x=(le=F==null?void 0:F.metadata)==null?void 0:le.status,D=I=>{if(!I)return null;try{const v=JSON.parse(I);return v&&typeof v=="object"&&!Array.isArray(v)?v:null}catch{return null}},K=I=>!I||Object.keys(I).length===0?"":JSON.stringify(I),[C,_]=O.useState(()=>({filter:S.rvFilter?D(S.rvFilter):null,orderBy:_l(S.order)??[{field:"REVISION_NUMBER",direction:"DESC"}],limit:S.pageSize,offset:S.current>1?(S.current-1)*S.pageSize:0})),[H,z]=Il(),L=`${a??""}${H}`,w=(a===void 0||a===zl)&&H===zl,{deployment:V}=Re.useLazyLoadQuery(Qt,{deploymentId:e,...C},{fetchKey:L,fetchPolicy:w?"store-and-network":"network-only"}),[T]=Re.useMutation(qt),E=V==null?void 0:V.currentRevisionId,$=V==null?void 0:V.deployingRevisionId,Y=V==null?void 0:V.revisionHistory,U=Al(Rl(Y==null?void 0:Y.edges,"node")),q=I=>{u(()=>{_(v=>({...v,...I}))})},B=()=>{u(()=>z())},j=I=>new Promise(v=>{y(I.id),T({variables:{input:{deploymentId:ll(F.id),revisionId:ll(I.id)}},onCompleted:(N,M)=>{var W;if(y(null),M&&M.length>0){d.error(M[0]),i.error(((W=M[0])==null?void 0:W.message)||r("general.ErrorOccurred")),v(!1);return}i.success(r("deployment.ApplySuccess",{revisionNumber:I.revisionNumber})),B(),v(!0)},onError:N=>{y(null),d.error(N),i.error((N==null?void 0:N.message)||r("general.ErrorOccurred")),v(!1)}})}),b=[{title:n.jsxs(te,{gap:"xxs",align:"center",children:[r("deployment.RevisionNumberWithID"),n.jsx(pl,{title:r("deployment.RevisionNumberTooltip")})]}),dataIndex:"revisionNumber",key:"revisionNumber",fixed:"left",sorter:!0,render:(I,v)=>{const N=ll(v.id),M=N===E,W=N===$,J=M||W?r("deployment.ApplyDisabled"):void 0,Z=M||W||hl(x)||o===v.id;return n.jsx(kn,{title:n.jsxs(te,{gap:"xs",align:"center",wrap:"nowrap",children:[n.jsx(Xe.Link,{onClick:()=>k({frgmt:v,status:M?"current":W?"deploying":"none"}),children:v.revisionNumber!=null?`#${v.revisionNumber}`:"-"}),n.jsxs(te,{gap:0,align:"center",children:["(",n.jsx(Nl,{globalId:v.id}),")"]}),M?n.jsx(en,{color:"success",children:r("deployment.Current")}):null,W&&!M?n.jsx(en,{color:"warning",icon:n.jsx(bn,{spin:!0}),children:r("deployment.Applying")}):null]}),showActions:"always",moreMenuDisabled:hl(x),actions:[{key:"deploy",title:r("deployment.Apply"),icon:n.jsx(Mn,{}),disabled:Z,disabledReason:J,popConfirm:{title:r("deployment.ApplyRevision"),description:r("deployment.ApplyConfirm",{revisionNumber:v.revisionNumber}),okText:r("deployment.Apply"),cancelText:r("button.Cancel"),okButtonProps:{danger:!0},onConfirm:()=>{j(v)}}},{key:"duplicate",title:r("deployment.AddNewRevisionFromThis"),icon:n.jsx(Nn,{size:t.fontSize}),showInMenu:"always",disabled:hl(x),onClick:()=>{g(v)}}]})}},{title:r("general.CreatedAt"),dataIndex:"createdAt",key:"createdAt",sorter:!0,render:I=>I?dl(I).format("lll"):"-"},{title:r("deployment.ModelVersion"),key:"modelVersion",defaultHidden:!0,render:(I,v)=>{var Z,ee,Q;const N=(ee=(Z=v.modelDefinition)==null?void 0:Z.models)==null?void 0:ee[0];if(!N)return"-";const M=N.name??"-",W=(Q=N.metadata)==null?void 0:Q.version,J=typeof W=="string"?W:W!=null?String(W):null;return J?`${M} (${J})`:M}},{title:r("deployment.RuntimeVariant"),key:"runtimeVariantName",dataIndex:"runtimeVariantName",sorter:!0,render:(I,v)=>{var N,M;return((M=(N=v.modelRuntimeConfig)==null?void 0:N.runtimeVariant)==null?void 0:M.name)??"-"}},{title:r("deployment.Image"),key:"image",defaultHidden:!0,render:(I,v)=>{var J,Z,ee,Q;const N=(Z=(J=v.imageV2)==null?void 0:J.identity)==null?void 0:Z.canonicalName,M=(Q=(ee=v.imageV2)==null?void 0:ee.identity)==null?void 0:Q.architecture,W=N&&M?`${N}@${M}`:N;return W?n.jsx(jl,{copyable:{text:W},ellipsis:{tooltip:W},style:{maxWidth:180},children:W}):"-"}},{title:r("deployment.ModelFolder"),key:"modelFolder",defaultHidden:!0,render:(I,v)=>{var W,J;const N=(W=v.modelMountConfig)==null?void 0:W.vfolder,M=(J=v.modelMountConfig)==null?void 0:J.vfolderId;return!N&&!M?"-":N?n.jsx(Wa,{vfolderNodeFragment:N}):n.jsx(Xe.Text,{type:"secondary",children:M})}},{title:n.jsxs(te,{gap:"xxs",align:"center",children:[r("deployment.ClusterMode"),n.jsx(pl,{title:r("deployment.ClusterModeTooltip")})]}),key:"clusterMode",dataIndex:"clusterMode",sorter:!0,render:(I,v)=>{var W,J;const N=(W=v.clusterConfig)==null?void 0:W.mode,M=(J=v.clusterConfig)==null?void 0:J.size;return N==null&&M==null?"-":N==null?`${M}`:M==null?N:`${N} / ${M}`}}],A={message:r("general.InvalidUUID"),validate:I=>Ka(I.toLowerCase())},P=[{key:"revisionNumber",propertyLabel:r("deployment.RevisionNumber"),type:"number"},{key:"createdAt",propertyLabel:r("general.CreatedAt"),type:"datetime",operators:["after","before"],defaultOperator:"after"},{key:"clusterMode",propertyLabel:r("deployment.ClusterMode"),type:"string"},{key:"imageId",propertyLabel:r("deployment.Image"),type:"uuid",fixedOperator:"equals",rule:A},{key:"modelVfolderId",propertyLabel:r("deployment.ModelFolder"),type:"uuid",fixedOperator:"equals",rule:A}],ne=S.rvFilter?D(S.rvFilter)??void 0:void 0;return n.jsxs(n.Fragment,{children:[n.jsx(fl,{children:n.jsx(an,{revisionFrgmt:c==null?void 0:c.frgmt,status:c==null?void 0:c.status,open:!!c,onClose:()=>k(null),extra:c?n.jsxs(Ql.Compact,{children:[n.jsx(ba,{title:r("deployment.ApplyRevision"),description:r("deployment.ApplyConfirm",{revisionNumber:c.frgmt.revisionNumber}),okText:r("deployment.Apply"),cancelText:r("button.Cancel"),okButtonProps:{danger:!0},onConfirm:async()=>{await j(c.frgmt)&&k(null)},children:n.jsx(kl,{type:"primary",icon:n.jsx(Mn,{}),disabled:c.status==="current"||c.status==="deploying"||hl(x)||!!o,children:r("deployment.Apply")})}),n.jsx(Xn,{trigger:["click"],menu:{items:[{key:"duplicate",label:r("deployment.AddNewRevisionFromThis"),icon:n.jsx(Nn,{size:t.fontSize}),disabled:hl(x),onClick:()=>{const I=c.frgmt;k(null),g(I)}}]},children:n.jsx(kl,{type:"primary",icon:n.jsx(Yn,{}),"aria-label":r("button.More"),disabled:hl(x)})})]}):void 0})}),n.jsxs(te,{justify:"between",align:"center",gap:"xs",style:{marginBottom:t.marginSM},wrap:"wrap",children:[n.jsx(Gl,{filterProperties:P,value:ne,onChange:I=>{const v=K(I),N=D(v||null);R({rvFilter:v||null,current:1}),q({filter:N,offset:0})}}),n.jsx(wl,{loading:s,value:"",onChange:()=>B()})]}),n.jsx(El,{rowKey:"id",dataSource:U,columns:b,loading:s,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:f,onColumnOverridesChange:p},order:S.order??void 0,onChangeOrder:I=>{R({order:I??null}),q({orderBy:_l(I||"-revisionNumber")})},pagination:{pageSize:S.pageSize,current:S.current,total:(Y==null?void 0:Y.count)??0,showSizeChanger:!0,onChange:(I,v)=>{const N=I>1?(I-1)*v:0;R({current:I,pageSize:v}),q({limit:v,offset:N})}}}),n.jsx(O.Suspense,{fallback:null,children:n.jsx(fl,{children:n.jsx(bt,{open:!!m,deploymentFrgmt:F,sourceRevisionFrgmt:m,onRequestClose:I=>{g(null),I&&B()}})})})]})},Ji=l=>{"use memo";const e=We.c(49),{deploymentFrgmt:a,revisionFetchKey:r,onAddRevision:t,revisionCardRef:i,isAddRevisionDisabled:d}=l,s=d===void 0?!1:d,{t:u}=Je();let o;e[0]===Symbol.for("react.memo_cache_sentinel")?(o=Bt,e[0]=o):o=e[0];const y=Re.useFragment(o,a);let c;e[1]===Symbol.for("react.memo_cache_sentinel")?(c=Ul(["currentRevision","revisionHistory","auditLog"]).withDefault("currentRevision"),e[1]=c):c=e[1];let k;e[2]===Symbol.for("react.memo_cache_sentinel")?(k={...c,history:"replace",scroll:!1},e[2]=k):k=e[2];const[m,g]=Ta("revisionTab",k);let f;e[3]!==g?(f=E=>{(E==="currentRevision"||E==="revisionHistory"||E==="auditLog")&&g(E)},e[3]=g,e[4]=f):f=e[4];let p;e[5]!==u?(p=u("deployment.CurrentRevision"),e[5]=u,e[6]=p):p=e[6];let S;e[7]!==p?(S={key:"currentRevision",label:p},e[7]=p,e[8]=S):S=e[8];let R;e[9]!==u?(R=u("deployment.RevisionHistory"),e[9]=u,e[10]=R):R=e[10];let F;e[11]!==R?(F={key:"revisionHistory",label:R},e[11]=R,e[12]=F):F=e[12];let x;e[13]!==u?(x=u("auditLog.AuditLog"),e[13]=u,e[14]=x):x=e[14];let D;e[15]!==x?(D={key:"auditLog",label:x},e[15]=x,e[16]=D):D=e[16];let K;e[17]!==D||e[18]!==S||e[19]!==F?(K=[S,F,D],e[17]=D,e[18]=S,e[19]=F,e[20]=K):K=e[20];let C;e[21]===Symbol.for("react.memo_cache_sentinel")?(C=n.jsx(Ll,{}),e[21]=C):C=e[21];let _;e[22]!==t?(_=async()=>{t()},e[22]=t,e[23]=_):_=e[23];let H;e[24]!==u?(H=u("deployment.AddRevision"),e[24]=u,e[25]=H):H=e[25];let z;e[26]!==s||e[27]!==_||e[28]!==H?(z=n.jsx(te,{gap:"xs",align:"center",children:n.jsx(kl,{type:"primary",icon:C,disabled:s,action:_,children:H})}),e[26]=s,e[27]=_,e[28]=H,e[29]=z):z=e[29];let L;e[30]!==m||e[31]!==y?(L=m==="currentRevision"&&n.jsx(Gi,{deploymentFrgmt:y}),e[30]=m,e[31]=y,e[32]=L):L=e[32];let w;e[33]!==m||e[34]!==y||e[35]!==r?(w=m==="revisionHistory"&&y&&n.jsx(Un,{children:n.jsx(O.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:4}}),children:n.jsx(Xi,{deploymentFrgmt:y,deploymentId:y.id,fetchKey:r})})}),e[33]=m,e[34]=y,e[35]=r,e[36]=w):w=e[36];let V;e[37]!==m||e[38]!==y?(V=m==="auditLog"&&y&&n.jsx(Wi,{deploymentId:y.id}),e[37]=m,e[38]=y,e[39]=V):V=e[39];let T;return e[40]!==m||e[41]!==i||e[42]!==K||e[43]!==z||e[44]!==L||e[45]!==w||e[46]!==V||e[47]!==f?(T=n.jsxs(Wl,{ref:i,activeTabKey:m,onTabChange:f,tabList:K,tabBarExtraContent:z,children:[L,w,V]}),e[40]=m,e[41]=i,e[42]=K,e[43]=z,e[44]=L,e[45]=w,e[46]=V,e[47]=f,e[48]=T):T=e[48],T},Ut=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"projectId"}],e=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"projectId"}],concreteType:"GroupNode",kind:"LinkedField",name:"group_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SwitchToProjectButtonQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SwitchToProjectButtonQuery",selections:e},params:{cacheID:"d9b043a52eacadb018a0097fe3c1f3c2",id:null,metadata:{},name:"SwitchToProjectButtonQuery",operationKind:"query",text:`query SwitchToProjectButtonQuery(
  $projectId: String!
) {
  group_node(id: $projectId) @since(version: "24.03.0") {
    id
    name
  }
}
`}}})();Ut.hash="4618e2aed2bc3c75a1d0a91f0b01c28c";const Zi=l=>{"use memo";const e=We.c(20);let a,r;e[0]!==l?({projectId:r,...a}=l,e[0]=l,e[1]=a,e[2]=r):(a=e[1],r=e[2]);const{t}=Je(),[i,d]=O.useTransition(),s=Da();let u;e[3]===Symbol.for("react.memo_cache_sentinel")?(u=Ut,e[3]=u):u=e[3];let o;e[4]!==r?(o=ql("GroupNode",r),e[4]=r,e[5]=o):o=e[5];let y;e[6]!==o?(y={projectId:o},e[6]=o,e[7]=y):y=e[7];const{group_node:c}=Re.useLazyLoadQuery(u,y);let k;e[8]!==(c==null?void 0:c.id)||e[9]!==(c==null?void 0:c.name)||e[10]!==s?(k=()=>{const S=ll((c==null?void 0:c.id)||""),R=c==null?void 0:c.name;S&&R&&d(()=>{s({projectId:S,projectName:R})})},e[8]=c==null?void 0:c.id,e[9]=c==null?void 0:c.name,e[10]=s,e[11]=k):k=e[11];const m=k,g=c==null?void 0:c.name;let f;e[12]!==t||e[13]!==g?(f=t("modelService.SwitchToProject",{projectName:g}),e[12]=t,e[13]=g,e[14]=f):f=e[14];let p;return e[15]!==a||e[16]!==m||e[17]!==i||e[18]!==f?(p=n.jsx(kl,{type:"link",size:"small",loading:i,onClick:m,...a,children:f}),e[15]=a,e[16]=m,e[17]=i,e[18]=f,e[19]=p):p=e[19],p},es=l=>n.jsx(O.Suspense,{fallback:n.jsx(kl,{type:"link",size:"small",loading:!0}),children:n.jsx(Zi,{...l})}),ls=5e3,un=(l,e)=>{l&&(l.style.scrollMarginTop=`${e}px`,l.scrollIntoView({behavior:"smooth",block:"start"}))},Ks=()=>{"use memo";var el,Me,ze,ul,al,il,sl,ol,be,xe,Le,Ue,Sl,ke,De,rl;const l=We.c(122),{t:e}=Je(),{token:a}=Dl.useToken(),[r]=Wn(),t=tn(),i=vn(),d=Qn(),s=Rn();let u;l[0]!==((el=i==null?void 0:i._config)==null?void 0:el.blockList)?(u=(ze=(Me=i==null?void 0:i._config)==null?void 0:Me.blockList)==null?void 0:ze.includes("chat"),l[0]=(ul=i==null?void 0:i._config)==null?void 0:ul.blockList,l[1]=u):u=l[1];const o=!!u,{deploymentId:y}=Ia(),c=y??"";let k;l[2]!==c?(k=ql("ModelDeployment",c),l[2]=c,l[3]=k):k=l[3];const m=k,[g,f]=O.useTransition(),[p,S]=Il(),[R,F]=Il(),[x,D]=Il(),[K,C]=Ln(!1),{setLeft:_,setRight:H}=C,[z,L]=Ln(!1),{setLeft:w,setRight:V}=L,T=O.useRef(null),E=O.useRef(null),{hash:$}=Ca();let Y;l[4]!==$||l[5]!==((al=a.Layout)==null?void 0:al.headerHeight)?(Y=()=>{var nl,yl;un(((nl={"#revisions":T,"#access-tokens":E}[$])==null?void 0:nl.current)??null,((yl=a.Layout)==null?void 0:yl.headerHeight)??60)},l[4]=$,l[5]=(il=a.Layout)==null?void 0:il.headerHeight,l[6]=Y):Y=l[6];const U=O.useEffectEvent(Y);let q;l[7]!==U?(q=()=>{U()},l[7]=U,l[8]=q):q=l[8];let B;l[9]!==$?(B=[$],l[9]=$,l[10]=B):B=l[10],O.useEffect(q,B);const[j,b]=O.useState(null);let A;l[11]===Symbol.for("react.memo_cache_sentinel")?(A=ct,l[11]=A):A=l[11];let P;l[12]!==m?(P={deploymentId:m},l[12]=m,l[13]=P):P=l[13];const ne=p===zl?"store-and-network":"network-only";let le;l[14]!==p||l[15]!==ne?(le={fetchKey:p,fetchPolicy:ne},l[14]=p,l[15]=ne,l[16]=le):le=l[16];const{deployment:I}=Re.useLazyLoadQuery(A,P,le);if(!I.ok){const Ee=I.errors;if(Ee.some(ts)){let bl;return l[17]===Symbol.for("react.memo_cache_sentinel")?(bl=n.jsx(ns,{}),l[17]=bl):bl=l[17],bl}const yl=Ee.map(as).filter(Boolean),Ml=new Error(yl.join("; ")||"DeploymentDetailPageQuery failed.");throw Ml.errors=Ee,Ml}const v=I.value,N=v.metadata.name,M=v.metadata.status,W=M==="READY",J=v.metadata.projectId??null,Z=!!J&&J!==d.id,ee=!v.currentRevision&&!v.deployingRevision,Q=!!v.deployingRevision&&v.deployingRevision.id!==((sl=v.currentRevision)==null?void 0:sl.id),ae=!!v.networkAccess.endpointUrl,Se=(((ol=v.accessTokens)==null?void 0:ol.count)??0)>0;let ge;l[18]!==M?(ge=hl(M),l[18]=M,l[19]=ge):ge=l[19];const ye=ge,de=(((be=v.replicaState)==null?void 0:be.desiredReplicaCount)??0)===0,pe=!de&&(((xe=v.runningReplicas)==null?void 0:xe.count)??0)===0,ue=de||pe,fe=v.networkAccess.openToPublic===!1&&!ye&&ae&&!Se,ce=((Ue=(Le=v.creator)==null?void 0:Le.basicInfo)==null?void 0:Ue.email)??null,ve=!ce||ce===r.email;let Ke;l[20]!==S?(Ke=()=>{f(()=>S())},l[20]=S,l[21]=Ke):Ke=l[21];const Te=Ke;let Ae;l[22]!==_||l[23]!==((Sl=a.Layout)==null?void 0:Sl.headerHeight)||l[24]!==S||l[25]!==D||l[26]!==F?(Ae=(Ee,nl)=>{var yl;_(),Ee&&(nl&&b(nl),f(()=>{S(),F(),D()}),un(T.current,((yl=a.Layout)==null?void 0:yl.headerHeight)??60))},l[22]=_,l[23]=(ke=a.Layout)==null?void 0:ke.headerHeight,l[24]=S,l[25]=D,l[26]=F,l[27]=Ae):Ae=l[27];const Ie=Ae;let ie;l[28]!==de||l[29]!==pe||l[30]!==e?(ie=()=>{if(de)return n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NoDesiredReplicas")});if(pe)return n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NoRunningReplicas")})},l[28]=de,l[29]=pe,l[30]=e,l[31]=ie):ie=l[31];const Fe=ie;let je;l[32]!==J||l[33]!==Z||l[34]!==e?(je=Z&&J&&n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NotInProject"),action:n.jsx(es,{projectId:J})}),l[32]=J,l[33]=Z,l[34]=e,l[35]=je):je=l[35];let He;l[36]!==Fe||l[37]!==ue||l[38]!==ee||l[39]!==ye?(He=ue&&!ee&&!ye&&Fe(),l[36]=Fe,l[37]=ue,l[38]=ee,l[39]=ye,l[40]=He):He=l[40];let tl;l[41]!==s||l[42]!==c||l[43]!==ue||l[44]!==ee||l[45]!==o||l[46]!==W||l[47]!==e||l[48]!==a.fontSizeLG||l[49]!==t?(tl=W&&!ee&&!ue&&n.jsx(Tl,{type:"success",showIcon:!0,title:e("deployment.DeploymentReady"),action:!o&&n.jsx(ml,{type:"primary",icon:n.jsx(Aa,{size:a.fontSizeLG}),onClick:()=>{t({pathname:s("chat",{scope:"project"}),search:new URLSearchParams({endpointId:c}).toString()})},children:e("deployment.StartChatTest")})}),l[41]=s,l[42]=c,l[43]=ue,l[44]=ee,l[45]=o,l[46]=W,l[47]=e,l[48]=a.fontSizeLG,l[49]=t,l[50]=tl):tl=l[50];let Ge;l[51]!==M||l[52]!==ee||l[53]!==Z||l[54]!==H||l[55]!==e?(Ge=ee&&!Z&&!hl(M)&&n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NoCurrentRevisionDeployed"),action:n.jsx(kl,{type:"primary",icon:n.jsx(Ll,{}),action:async()=>{H()},children:e("deployment.AddRevision")})}),l[51]=M,l[52]=ee,l[53]=Z,l[54]=H,l[55]=e,l[56]=Ge):Ge=l[56];let Ye;l[57]!==ye||l[58]!==fe||l[59]!==V||l[60]!==e?(Ye=fe&&n.jsx(Tl,{type:"info",showIcon:!0,title:e("deployment.PrivateDeploymentAlertTitle"),action:n.jsx(kl,{type:"primary",icon:n.jsx(Ll,{}),action:async()=>{V()},disabled:ye,children:e("deployment.AddAccessToken")})}),l[57]=ye,l[58]=fe,l[59]=V,l[60]=e,l[61]=Ye):Ye=l[61];let Ze;l[62]===Symbol.for("react.memo_cache_sentinel")?(Ze={margin:0},l[62]=Ze):Ze=l[62];let h;l[63]!==N?(h=n.jsx(Xe.Title,{level:3,style:Ze,children:N}),l[63]=N,l[64]=h):h=l[64];let G;l[65]!==M?(G=n.jsx(st,{status:M}),l[65]=M,l[66]=G):G=l[66];let X;l[67]!==h||l[68]!==G?(X=n.jsxs(te,{direction:"row",align:"center",gap:"sm",children:[h,G]}),l[67]=h,l[68]=G,l[69]=X):X=l[69];const se=Q?ls:null;let re;l[70]!==v||l[71]!==Te||l[72]!==g||l[73]!==se?(re=n.jsx(wi,{deploymentFrgmt:v,isPendingRefetch:g,onRefetch:Te,autoUpdateDelay:se}),l[70]=v,l[71]=Te,l[72]=g,l[73]=se,l[74]=re):re=l[74];const me=ye||Z;let Ce;l[75]!==v||l[76]!==H||l[77]!==R||l[78]!==me?(Ce=n.jsx(Ji,{deploymentFrgmt:v,revisionFetchKey:R,onAddRevision:H,revisionCardRef:T,isAddRevisionDisabled:me}),l[75]=v,l[76]=H,l[77]=R,l[78]=me,l[79]=Ce):Ce=l[79];let Pe;l[80]!==v||l[81]!==m||l[82]!==x?(Pe=n.jsx(zi,{deploymentFrgmt:v,deploymentId:m,replicaFetchKey:x}),l[80]=v,l[81]=m,l[82]=x,l[83]=Pe):Pe=l[83];let Oe;l[84]!==v?(Oe=n.jsx(Ni,{deploymentFrgmt:v}),l[84]=v,l[85]=Oe):Oe=l[85];let Ve;l[86]!==w||l[87]!==V?(Ve=Ee=>{Ee?V():w()},l[86]=w,l[87]=V,l[88]=Ve):Ve=l[88];let Be;l[89]!==Te||l[90]!==((De=a.Layout)==null?void 0:De.headerHeight)?(Be=()=>{var Ee;Te(),un(E.current,((Ee=a.Layout)==null?void 0:Ee.headerHeight)??60)},l[89]=Te,l[90]=(rl=a.Layout)==null?void 0:rl.headerHeight,l[91]=Be):Be=l[91];let he;l[92]!==z||l[93]!==v||l[94]!==m||l[95]!==ye||l[96]!==ve||l[97]!==Ve||l[98]!==Be?(he=n.jsx(mi,{cardRef:E,deploymentFrgmt:v,deploymentId:m,isOwnedByCurrentUser:ve,isDeploymentDestroying:ye,isCreateModalOpen:z,onCreateModalOpenChange:Ve,onTokenCreated:Be}),l[92]=z,l[93]=v,l[94]=m,l[95]=ye,l[96]=ve,l[97]=Ve,l[98]=Be,l[99]=he):he=l[99];let we;l[100]!==K||l[101]!==v||l[102]!==Ie?(we=n.jsx(fl,{children:n.jsx(bt,{open:K,onRequestClose:Ie,deploymentFrgmt:v})}),l[100]=K,l[101]=v,l[102]=Ie,l[103]=we):we=l[103];const $e=!!j;let Qe;l[104]===Symbol.for("react.memo_cache_sentinel")?(Qe=()=>b(null),l[104]=Qe):Qe=l[104];let _e;l[105]!==j||l[106]!==$e?(_e=n.jsx(fl,{children:n.jsx(an,{revisionFrgmt:j,open:$e,onClose:Qe})}),l[105]=j,l[106]=$e,l[107]=_e):_e=l[107];let qe;return l[108]!==je||l[109]!==He||l[110]!==tl||l[111]!==Ge||l[112]!==Ye||l[113]!==X||l[114]!==re||l[115]!==Ce||l[116]!==Pe||l[117]!==Oe||l[118]!==he||l[119]!==we||l[120]!==_e?(qe=n.jsxs(te,{direction:"column",align:"stretch",gap:"md",children:[je,He,tl,Ge,Ye,X,re,Ce,Pe,Oe,he,we,_e]}),l[108]=je,l[109]=He,l[110]=tl,l[111]=Ge,l[112]=Ye,l[113]=X,l[114]=re,l[115]=Ce,l[116]=Pe,l[117]=Oe,l[118]=he,l[119]=we,l[120]=_e,l[121]=qe):qe=l[121],qe},ns=()=>{"use memo";const l=We.c(40),{t:e}=Je(),a=tn(),{firstAvailableMenuItem:r}=Ma(),t=La();let i;l[0]!==t||l[1]!==r?(i=r?ja(r.key,t):"/start",l[0]=t,l[1]=r,l[2]=i):i=l[2];const d=i;let s,u,o,y,c,k,m,g,f,p,S;if(l[3]!==d||l[4]!==(r==null?void 0:r.labelText)||l[5]!==e||l[6]!==a){const D=(r==null?void 0:r.labelText)??e("webui.menu.FirstPageNameAlias");o=te,l[18]===Symbol.for("react.memo_cache_sentinel")?(f={margin:"auto"},l[18]=f):f=l[18],p="center",S="center",u=Pa,m="warning",l[19]!==e?(g=e("deployment.NotAccessibleOrDeleted"),l[19]=e,l[20]=g):g=l[20],s=ml,y="primary",l[21]!==d||l[22]!==a?(c=()=>{a(d)},l[21]=d,l[22]=a,l[23]=c):c=l[23],k=e("button.GoBackToStartPage",{title:D}),l[3]=d,l[4]=r==null?void 0:r.labelText,l[5]=e,l[6]=a,l[7]=s,l[8]=u,l[9]=o,l[10]=y,l[11]=c,l[12]=k,l[13]=m,l[14]=g,l[15]=f,l[16]=p,l[17]=S}else s=l[7],u=l[8],o=l[9],y=l[10],c=l[11],k=l[12],m=l[13],g=l[14],f=l[15],p=l[16],S=l[17];let R;l[24]!==s||l[25]!==y||l[26]!==c||l[27]!==k?(R=n.jsx(s,{type:y,onClick:c,children:k}),l[24]=s,l[25]=y,l[26]=c,l[27]=k,l[28]=R):R=l[28];let F;l[29]!==u||l[30]!==m||l[31]!==g||l[32]!==R?(F=n.jsx(u,{status:m,title:g,extra:R}),l[29]=u,l[30]=m,l[31]=g,l[32]=R,l[33]=F):F=l[33];let x;return l[34]!==o||l[35]!==F||l[36]!==f||l[37]!==p||l[38]!==S?(x=n.jsx(o,{style:f,justify:p,align:S,children:F}),l[34]=o,l[35]=F,l[36]=f,l[37]=p,l[38]=S,l[39]=x):x=l[39],x};function ts(l){return/Insufficient permission/i.test((l==null?void 0:l.message)??"")}function as(l){return(l==null?void 0:l.message)??""}export{Ks as default};
//# sourceMappingURL=DeploymentDetailPage-CRtfOAwE.js.map
