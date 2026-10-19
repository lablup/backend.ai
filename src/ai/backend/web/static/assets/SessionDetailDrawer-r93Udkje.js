import{fz as Mn,gx as Rn,gy as Pn,gz as Vn,ak as Ve,dQ as Hn,j as n,i as oe,bY as $n,fE as Un,az as We,r as V,ag as dn,aT as Me,aZ as un,t as re,s as Oe,ai as zn,aq as ze,l as I,bA as cn,a0 as On,es as Qn,al as Pe,fD as Xe,a2 as U,U as mn,a8 as Ye,gA as qn,u as Ae,c as T,J as De,bu as gn,aR as Qe,aQ as Gn,et as Ze,an as Jn,gB as Wn,gC as Yn,eq as pn,a as Sn,dT as Xn,bt as Be,C as Zn,gD as el,aF as nl,_ as en,E as ll,W as al,gE as yn,gF as sl,dR as tl,gG as il,B as rl,gH as $e,gI as ol,ab as dl,aM as fn,a7 as nn,aX as Fn,aS as ul,b2 as cl,aN as ml,d$ as gl,bo as pl,ac as kn,a$ as Sl,bI as ln,gJ as yl,ef as fl,gK as hn,cn as an,v as Ue,gL as Fl,d as kl,e as hl,M as P,aV as Ie,gM as bl,gN as xl,gO as _l,cM as Kl,gP as jl,gQ as Cl,fb as Il,T as Al,q as Nl,g as Ll,gR as vl,gS as Tl,gT as El,eJ as wl,cK as Bl,gU as Dl,dE as sn,dC as Ml,dB as tn,cu as Rl,at as Pl,bk as Vl,bE as Hl,bZ as $l,c3 as Ul,cm as zl,dD as Ol,dJ as Ql}from"./index-4XAoWQdC.js";import{S as ql}from"./scroll-text-CMSbKmDU.js";import{o as Gl}from"./orderBy-DR_M0o9Z.js";import{F as Jl}from"./FolderLink-B13SaUe_.js";import{S as Wl,a as Yl}from"./ScopedAuditLog-BTAaHqWC.js";import{R as Xl}from"./rotate-ccw-clock-Bp9ZfyAh.js";var Zl=Mn(function(a){return Rn(Pn(a,1,Vn,!0))});const ea=(a,e=/(<br\s*\/?>|\n)/)=>Ve(Hn(a,e),(l,s)=>l.match(e)?n.jsx("br",{},s):l),bn={SUCCESS:"success",FAILURE:"error",STALE:"default",NEED_RETRY:"warning",EXPIRED:"error",GIVE_UP:"error",SKIPPED:"default"},na=a=>{"use memo";const e=oe.c(12);let l,s;e[0]!==a?({result:s,...l}=a,e[0]=a,e[1]=l,e[2]=s):(l=e[1],s=e[2]);let r;e[3]!==s?(r=s?$n(bn,s):void 0,e[3]=s,e[4]=r):r=e[4];const d=r;let t;e[5]!==l.style?(t={whiteSpace:"nowrap",...l.style},e[5]=l.style,e[6]=t):t=e[6];let o;return e[7]!==l||e[8]!==s||e[9]!==d||e[10]!==t?(o=n.jsx(Un,{...l,color:d,text:s,style:t}),e[7]=l,e[8]=s,e[9]=d,e[10]=t,e[11]=o):o=e[11],o},xn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null}],type:"SessionSchedulingHistory",abstractKey:null};xn.hash="a52af4f53e01beb70d74f67b151aa5e0";const Je=[];[...Je,...Je.map(a=>`-${a}`)];const Ke=a=>zn(Je,a),la=a=>{"use memo";const e=oe.c(23);let l,s,r,d,t;e[0]!==a?({schedulingHistoryFrgmt:d,disableSorter:s,customizeColumns:l,onChangeOrder:r,...t}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d,e[5]=t):(l=e[1],s=e[2],r=e[3],d=e[4],t=e[5]);const{t:o}=We();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=xn,e[6]=u):u=e[6];const m=V.useFragment(u,d);let c;if(e[7]!==l||e[8]!==s||e[9]!==o){let p;e[11]!==s?(p=g=>s?ze(g,"sorter"):g,e[11]=s,e[12]=p):p=e[12];const y=Ve(dn([{dataIndex:"updatedAt",title:o("comp:BAISchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:aa,sorter:Ke("updated_at")},{dataIndex:"createdAt",title:o("comp:BAISchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:sa,sorter:Ke("created_at")},{dataIndex:"phase",title:o("comp:BAISchedulingHistoryNodes.Phase"),key:"phase",sorter:Ke("phase")},{dataIndex:"result",title:o("comp:BAISchedulingHistoryNodes.Result"),key:"result",render:ta,sorter:Ke("result")},{key:"fromStatus",title:o("comp:BAISchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Ke("from_status")},{key:"toStatus",title:o("comp:BAISchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Ke("to_status")},{dataIndex:"attempts",title:o("comp:BAISchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Ke("attempts")},{key:"message",title:o("comp:BAISchedulingHistoryNodes.Message"),dataIndex:"message",onCell:ia,render:ra,sorter:Ke("message")}]),p);c=l?l(y):y,e[7]=l,e[8]=s,e[9]=o,e[10]=c}else c=e[10];const F=c;let k;e[13]===Symbol.for("react.memo_cache_sentinel")?(k={x:"max-content"},e[13]=k):k=e[13];let b;e[14]!==m?(b=Me(m),e[14]=m,e[15]=b):b=e[15];let x;e[16]!==r?(x=p=>{r==null||r(p||null)},e[16]=r,e[17]=x):x=e[17];let S;return e[18]!==F||e[19]!==b||e[20]!==x||e[21]!==t?(S=n.jsx(un,{scroll:k,rowKey:"id",dataSource:b,columns:F,onChangeOrder:x,...t}),e[18]=F,e[19]=b,e[20]=x,e[21]=t,e[22]=S):S=e[22],S};function aa(a){return n.jsx("span",{children:re(a).format("ll LTS")})}function sa(a){return n.jsx("span",{children:re(a).format("ll LTS")})}function ta(a,e){const l=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(na,{result:l})}function ia(){return{style:{maxWidth:500}}}function ra(a,e){return e.message?n.jsx(Oe,{title:e.message,style:{width:"100%"},children:ea(e.message)}):"-"}const _n={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryNodesFragment"}],type:"SessionSchedulingHistory",abstractKey:null};_n.hash="e369227c362b363c91d9f366ac98634d";const oa="errors-only",da=a=>!Pe(a.subSteps),qe=(a,e,l)=>e==="expand-all"?a.filter(l).map(s=>s.id):e==="collapse-all"?[]:a.filter(s=>l(s)&&s.result!=="SUCCESS").map(s=>s.id),ua=(a,e)=>{"use memo";const l=oe.c(28),{t:s}=We(),r=(e==null?void 0:e.mode)??oa;let d;l[0]!==e?(d=j=>e!=null&&e.isExpandable?e.isExpandable(j):da(j),l[0]=e,l[1]=d):d=l[1];const t=d;let o;l[2]!==a||l[3]!==t||l[4]!==r?(o=()=>qe(a,r,t),l[2]=a,l[3]=t,l[4]=r,l[5]=o):o=l[5];const[u,m]=I.useState(o);let c;if(l[6]!==a||l[7]!==t){let j;l[9]!==t?(j=L=>`${L.id}:${L.result??""}:${t(L)?1:0}`,l[9]=t,l[10]=j):j=l[10],c=a.map(j).join("|"),l[6]=a,l[7]=t,l[8]=c}else c=l[8];const F=c,[k,b]=I.useState(F),[x,S]=I.useState(r);(F!==k||r!==x)&&(b(F),S(r),m(qe(a,r,t)));let p;l[11]!==a||l[12]!==t?(p=a.filter(t).map(ca),l[11]=a,l[12]=t,l[13]=p):p=l[13];const y=p;let g;l[14]===Symbol.for("react.memo_cache_sentinel")?(g=j=>{m([...j])},l[14]=g):g=l[14];const _=g;let h;if(l[15]!==a||l[16]!==t||l[17]!==e||l[18]!==s){const j={"expand-all":s("comp:BAITable.ExpandAll"),"collapse-all":s("comp:BAITable.CollapseAll"),"errors-only":s("comp:BAITable.ExpandErrorsOnly")},L=C=>{var B;m(qe(a,C,t)),(B=e==null?void 0:e.onModeChange)==null||B.call(e,C)};h=["expand-all","collapse-all","errors-only"].map(C=>({label:j[C],onClick:()=>L(C)})),l[15]=a,l[16]=t,l[17]=e,l[18]=s,l[19]=h}else h=l[19];const N=h;let v;l[20]!==y.length||l[21]!==N||l[22]!==s?(v=y.length>0?n.jsx(cn,{justify:"center",children:n.jsx(On,{items:N,button:{variant:"ghost",size:"sm",isIconOnly:!0,icon:n.jsx(Qn,{size:"1em"}),label:s("comp:BAITable.ExpandOptions"),tooltip:s("comp:BAITable.ExpandOptions")},hasChevron:!1})}):null,l[20]=y.length,l[21]=N,l[22]=s,l[23]=v):v=l[23];const K=v;let A;return l[24]!==K||l[25]!==u||l[26]!==r?(A={mode:r,expandedRowKeys:u,onExpandedRowsChange:_,expandColumnTitle:K},l[24]=K,l[25]=u,l[26]=r,l[27]=A):A=l[27],A};function ca(a){return a.id}const Kn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISubStepNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],type:"SubStepResultGQL",abstractKey:null};Kn.hash="b293ef89b3c67ebb0a3733e1c22f6df9";const ma="HH:mm:ss.SSS",ga=(a,e)=>{if(!a||!e)return null;const l=re(e).diff(re(a));if(!Number.isFinite(l)||l<0)return null;if(l<1e3)return`${Math.round(l)} ms`;if(l<6e4)return`${(l/1e3).toFixed(2)} s`;const s=Math.round(l/1e3),r=Math.floor(s/60);return r<60?`${r}m ${String(s%60).padStart(2,"0")}s`:`${Math.floor(r/60)}h ${String(r%60).padStart(2,"0")}m`},rn=a=>a.trim().toLowerCase().replace(/[\s_-]+/g,"-"),jn=(a,e,l,s)=>e===l-1&&!!s&&rn(a.step)===rn(s),Cn=(a,e)=>{const l=Me(a);return l.filter((s,r)=>!jn(s,r,l.length,e)).length},pa=a=>(a==null?void 0:a.replace(/\s*\n\s*/g," ").trim())||"-",Sa=a=>a&&a!=="%future added value"?a:null,ya=a=>{"use memo";const e=oe.c(39);let l,s,r,d;e[0]!==a?({subStepsFrgmt:d,parentPhase:r,className:l,...s}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d):(l=e[1],s=e[2],r=e[3],d=e[4]);const{t}=We();let o;e[5]===Symbol.for("react.memo_cache_sentinel")?(o=Kn,e[5]=o):o=e[5];const u=V.useFragment(o,d);let m,c,F,k,b,x,S;if(e[6]!==l||e[7]!==s||e[8]!==r||e[9]!==u||e[10]!==t){const h=Me(u);e[18]!==l?(x=Xe("bai-substep-panel",l),e[18]=l,e[19]=x):x=e[19],S=s,b="bai-substep-scroll",c="bai-substep-table";let N,v;e[20]===Symbol.for("react.memo_cache_sentinel")?(F=n.jsxs("colgroup",{children:[n.jsx("col",{className:"bai-substep-col-rail"}),n.jsx("col",{className:"bai-substep-col-step"}),n.jsx("col",{className:"bai-substep-col-result"}),n.jsx("col",{className:"bai-substep-col-duration"}),n.jsx("col",{className:"bai-substep-col-time"}),n.jsx("col",{className:"bai-substep-col-code"}),n.jsx("col",{})]}),v=n.jsx("th",{scope:"col"}),N=[["Step",void 0],["Result",void 0],["Duration","bai-substep-num"],["Time",void 0],["ErrorCode",void 0],["Message",void 0]],e[20]=N,e[21]=F,e[22]=v):(N=e[20],F=e[21],v=e[22]),e[23]!==t?(k=n.jsx("thead",{children:n.jsxs("tr",{children:[v,N.map(K=>{const[A,j]=K;return n.jsx("th",{scope:"col",className:j,children:n.jsx(U,{type:"supporting",weight:"medium",children:t(`comp:BAISubStepNodes.${A}`)})},A)})]})}),e[23]=t,e[24]=k):k=e[24],m=h.map((K,A)=>{const j=Sa(K.result),L=jn(K,A,h.length,r),C=ga(K.startedAt,K.endedAt);return n.jsxs("tr",{className:Xe("bai-substep-row",L&&"bai-substep-row--marker"),"data-variant":j?bn[j]:"default",children:[n.jsx("td",{className:"bai-substep-rail-cell"}),n.jsx("td",{children:n.jsx(U,{type:"code",size:"sm",color:L?"secondary":"primary",children:K.step})}),n.jsx("td",{children:j?n.jsx("span",{className:"bai-substep-result",children:n.jsx(U,{type:"supporting",color:"inherit",children:j})}):null}),n.jsx("td",{className:"bai-substep-num",children:!L&&C?n.jsx(U,{type:"code",size:"sm",color:"secondary",children:C}):n.jsx(U,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:K.startedAt?n.jsx(U,{type:"code",size:"sm",color:"secondary",children:re(K.startedAt).format(ma)}):null}),n.jsx("td",{children:K.errorCode?n.jsx("span",{className:"bai-substep-code",children:n.jsx(U,{type:"code",size:"sm",color:"secondary",children:K.errorCode})}):n.jsx(U,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:n.jsx(U,{type:"supporting",children:L?t("comp:BAISubStepNodes.ResultMarker"):pa(K.message)})})]},`${K.step}-${A}`)}),e[6]=l,e[7]=s,e[8]=r,e[9]=u,e[10]=t,e[11]=m,e[12]=c,e[13]=F,e[14]=k,e[15]=b,e[16]=x,e[17]=S}else m=e[11],c=e[12],F=e[13],k=e[14],b=e[15],x=e[16],S=e[17];let p;e[25]!==m?(p=n.jsx("tbody",{children:m}),e[25]=m,e[26]=p):p=e[26];let y;e[27]!==c||e[28]!==F||e[29]!==k||e[30]!==p?(y=n.jsxs("table",{className:c,children:[F,k,p]}),e[27]=c,e[28]=F,e[29]=k,e[30]=p,e[31]=y):y=e[31];let g;e[32]!==y||e[33]!==b?(g=n.jsx("div",{className:b,children:y}),e[32]=y,e[33]=b,e[34]=g):g=e[34];let _;return e[35]!==g||e[36]!==x||e[37]!==S?(_=n.jsx("div",{className:x,...S,children:g}),e[35]=g,e[36]=x,e[37]=S,e[38]=_):_=e[38],_},fa=a=>{"use memo";const e=oe.c(24);let l,s,r,d;e[0]!==a?({schedulingHistoryFrgmt:d,expandMode:l,onExpandModeChange:s,...r}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d):(l=e[1],s=e[2],r=e[3],d=e[4]);let t;e[5]===Symbol.for("react.memo_cache_sentinel")?(t=_n,e[5]=t):t=e[5];const o=V.useFragment(t,d);let u;e[6]!==o?(u=Me(o),e[6]=o,e[7]=u):u=e[7];const m=u;let c;e[8]!==l||e[9]!==s?(c={mode:l,onModeChange:s,isExpandable:Fa},e[8]=l,e[9]=s,e[10]=c):c=e[10];const{expandedRowKeys:F,onExpandedRowsChange:k,expandColumnTitle:b}=ua(m,c);let x,S;e[11]!==m?(x=g=>{var _;return Cn(((_=m.find(h=>h.id===g.id))==null?void 0:_.subSteps)??[],g.phase)>0},S=g=>{var _;return n.jsx(ya,{subStepsFrgmt:((_=m.find(h=>h.id===g.id))==null?void 0:_.subSteps)??[],parentPhase:g.phase})},e[11]=m,e[12]=x,e[13]=S):(x=e[12],S=e[13]);let p;e[14]!==b||e[15]!==F||e[16]!==k||e[17]!==x||e[18]!==S?(p={columnTitle:b,expandedRowKeys:F,onExpandedRowsChange:k,rowExpandable:x,expandedRowRender:S},e[14]=b,e[15]=F,e[16]=k,e[17]=x,e[18]=S,e[19]=p):p=e[19];let y;return e[20]!==o||e[21]!==r||e[22]!==p?(y=n.jsx(la,{schedulingHistoryFrgmt:o,expandable:p,...r}),e[20]=o,e[21]=r,e[22]=p,e[23]=y):y=e[23],y};function Fa(a){return Cn(a.subSteps??[],a.phase)>0}const In=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"6cb167705df49d003fee4ee02f1ee82e",id:null,metadata:{},name:"UNSAFELazyUserEmailViewQuery",operationKind:"query",text:`query UNSAFELazyUserEmailViewQuery(
  $uuid: String!
) {
  user_node(id: $uuid) {
    email
    id
  }
}
`}}})();In.hash="67caa5daf6f6559a42a344a9b5eadff6";const ka=({uuid:a,fetchKey:e,...l})=>{const{user_node:s}=V.useLazyLoadQuery(In,{uuid:a?mn("UserNode",a):""},{fetchPolicy:a?e===void 0?"store-or-network":"network-only":"store-only",fetchKey:e});return(s==null?void 0:s.email)&&n.jsx(Oe,{...l,children:s==null?void 0:s.email})},An={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailDrawerFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],type:"ComputeSessionNode",abstractKey:null};An.hash="eb57207016a6a8cf6abbf348456840de";const Nn=(function(){var a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,e,l,s],storageKey:null}],storageKey:null},r];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailContentFragment",selections:[a,e,l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},s,{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},r],storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIImageNodeSimpleTagFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"ConnectedKernelListFragment"}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:d,storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusBadgeFragment"},{args:null,kind:"FragmentSpread",name:"SessionActionButtonsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionTypeTokenFragment"},{args:null,kind:"FragmentSpread",name:"EditableSessionNameFragment"},{args:null,kind:"FragmentSpread",name:"SessionReservationFragment"},{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionUsageMonitorFragment"},{args:null,kind:"FragmentSpread",name:"ContainerCommitModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionIdleChecksNodeFragment"},{args:null,kind:"FragmentSpread",name:"AppLauncherModalFragment"},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionAgentIdsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionClusterModeFragment"},{args:null,kind:"FragmentSpread",name:"SessionAccessKeyFragment"}],type:"ComputeSessionNode",abstractKey:null}})();Nn.hash="b79ba853d0304ae3ae731b640b2640d3";const Ln=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},u=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],m={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},c=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,s,r,d],storageKey:null}],storageKey:null},t];return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[l,s,r,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,r,l],storageKey:null}],storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:u,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:u,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},o,l],storageKey:null},l,s,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},d,m,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:c,storageKey:null},m,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null}],storageKey:null}]},params:{cacheID:"44cde2a2c8a89ad4a38e983c5f5fdb88",id:null,metadata:{},name:"SessionDetailContentQuery",operationKind:"query",text:`query SessionDetailContentQuery(
  $id: GlobalIDField!
) {
  internalLoadedSession: compute_session_node(id: $id) {
    ...SessionDetailContentFragment
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

fragment SessionIdleChecksNodeFragment on ComputeSessionNode {
  id
  idle_checks
  ...SessionReclamationStatusCellFragment
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
`}}})();Ln.hash="54a57e1f9b8de6ca1ec280de81b4e986";const ha=a=>{"use memo";const e=oe.c(10);let l,s,r;e[0]!==a?({content:l,language:s,...r}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r):(l=e[1],s=e[2],r=e[3]);let d;e[4]!==l||e[5]!==s?(d=n.jsx(qn,{language:s,children:l}),e[4]=l,e[5]=s,e[6]=d):d=e[6];let t;return e[7]!==r||e[8]!==d?(t=n.jsx(Ye,{...r,children:d}),e[7]=r,e[8]=d,e[9]=t):t=e[9],t},vn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ConnectedKernelListFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],type:"KernelNode",abstractKey:null};vn.hash="b07dcbdb178c221c667bd2f86f43cbd5";const ba=({kernelsFrgmt:a,sessionFrgmtForLogModal:e})=>{const{t:l}=Ae(),[s,r]=I.useState(),d=V.useFragment(vn,a),t=dn([{title:l("kernel.Hostname"),dataIndex:"cluster_hostname",render:(u,m)=>n.jsxs(T,{gap:"xxs",children:[n.jsx(U,{children:u}),n.jsx(De,{variant:"ghost",size:"sm",icon:n.jsx(ql,{}),label:l("session.SeeContainerLogs"),tooltip:l("session.SeeContainerLogs"),onClick:()=>{m.row_id&&r(m.row_id)}})]})},{title:l("kernel.Status"),dataIndex:"status",render:(u,m)=>n.jsx(n.Fragment,{children:(m==null?void 0:m.status_info)!==""?n.jsx(gn,{values:[{label:u,variant:Qe("kernel",u)},{label:(m==null?void 0:m.status_info)??"",variant:Qe("kernel",m==null?void 0:m.status_info)}]}):n.jsx(Gn,{variant:Qe("kernel",u),label:u})})},{title:l("kernel.AgentId"),dataIndex:"agent_id",render:u=>Pe(u)?"-":n.jsx(Oe,{copyable:!0,children:u})},{title:l("kernel.KernelId"),fixed:"left",dataIndex:"row_id",render:u=>Pe(u)?"-":n.jsx(Ze,{uuid:u})},{title:l("kernel.ContainerId"),dataIndex:"container_id",render:u=>Pe(u)?"-":n.jsx(Ze,{uuid:u})}]),o=I.useMemo(()=>Gl(Me(d),["cluster_role","cluster_idx"]),[d]);return n.jsxs(n.Fragment,{children:[n.jsx(un,{scroll:{x:"max-content"},bordered:!0,rowKey:"id",columns:t,dataSource:o}),n.jsx(Jn,{children:n.jsx(Wn,{open:!!s,sessionFrgmt:e||null,defaultKernelId:s,onCancel:()=>{r(void 0)}})})]})},Tn=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"scope_id"},e={defaultValue:null,kind:"LocalArgument",name:"sessionId"},l=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"sessionId"},{kind:"Variable",name:"scope_id",variableName:"scope_id"}],concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[a,e],kind:"Fragment",metadata:null,name:"EditableSessionNameRefetchQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,a],kind:"Operation",name:"EditableSessionNameRefetchQuery",selections:l},params:{cacheID:"58d69307fe6e70d2c3409231b0279c8b",id:null,metadata:{},name:"EditableSessionNameRefetchQuery",operationKind:"query",text:`query EditableSessionNameRefetchQuery(
  $sessionId: GlobalIDField!
  $scope_id: ScopeField
) {
  compute_session_node(id: $sessionId, scope_id: $scope_id) {
    id
    name
  }
}
`}}})();Tn.hash="387b0fe2d9acb6f455335434b59c3e6c";const En={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EditableSessionNameFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},action:"THROW"}],type:"ComputeSessionNode",abstractKey:null};En.hash="6dfb2b44bf25b8bfda2fce5ab4cedad8";const xa=a=>{"use memo";const e=oe.c(28),{sessionFrgmt:l,level:s,editable:r,dimmed:d}=a,t=r===void 0?!1:r,o=d===void 0?!1:d,u=V.useRelayEnvironment();let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=En,e[0]=m):m=e[0];const c=V.useFragment(m,l),[F,k]=I.useState(c.name),b=Yn(F),[x]=pn(),S=Sn();let p;e[1]!==S||e[2]!==c.row_id?(p={mutationFn:w=>S.rename(c.row_id,w)},e[1]=S,e[2]=c.row_id,e[3]=p):p=e[3];const y=Xn(p),{t:g}=Ae(),{message:_}=al.useApp(),[h,N]=I.useState(!1),[v,K]=I.useState(!1);let A;e[4]===Symbol.for("react.memo_cache_sentinel")?(A=["RESTARTING","PREPARING","PREPARED","CREATING","PULLING"],e[4]=A):A=e[4];const j=!A.includes(c.status||""),L=t&&x.uuid===c.user_id&&j,C=y.isPending||F!==c.name,B=y.isPending||F!==c.name?F:c.name,M=o||C;let R;e[5]!==v||e[6]!==B||e[7]!==M||e[8]!==h||e[9]!==L||e[10]!==C||e[11]!==s||e[12]!==g?(R=(!h||C)&&n.jsxs(cn,{gap:1,align:"center",children:[s?n.jsx(Be,{level:s,color:M?"disabled":void 0,children:B}):n.jsx(U,{color:M?"disabled":void 0,children:B}),n.jsx(De,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:v?n.jsx(Zn,{"aria-hidden":!0}):n.jsx(el,{"aria-hidden":!0}),label:g("sourceCodeViewer.Copy"),tooltip:g("sourceCodeViewer.Copy"),isDisabled:v,onClick:()=>{var w;(w=navigator.clipboard)==null||w.writeText(B??""),K(!0),setTimeout(()=>K(!1),1500)}}),L&&!C&&n.jsx(De,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(nl,{"aria-hidden":!0}),label:g("button.Edit"),tooltip:g("button.Edit"),onClick:()=>N(!0)})]}),e[5]=v,e[6]=B,e[7]=M,e[8]=h,e[9]=L,e[10]=C,e[11]=s,e[12]=g,e[13]=R):R=e[13];let E;e[14]!==h||e[15]!==C||e[16]!==_||e[17]!==u||e[18]!==y||e[19]!==c.id||e[20]!==c.name||e[21]!==c.project_id||e[22]!==g||e[23]!==b?(E=h&&!C&&n.jsx(en,{onFinish:w=>{N(!1),k(w.sessionName),y.mutate(w.sessionName,{onSuccess:()=>{V.fetchQuery(u,Tn,{sessionId:c.id,scope_id:`project:${c.project_id}`}).toPromise().catch()},onError:()=>{c.name!==w.sessionName&&_.error(g("session.FailToRenameSession"))}})},initialValues:{sessionName:c.name},style:{flex:1},children:n.jsx(en.Item,{name:"sessionName",rules:b,children:n.jsx(ll,{label:g("session.SessionName"),size:"lg",hasAutoFocus:!0,onKeyDown:w=>{w.key==="Escape"&&(w.stopPropagation(),N(!1))}})})}),e[14]=h,e[15]=C,e[16]=_,e[17]=u,e[18]=y,e[19]=c.id,e[20]=c.name,e[21]=c.project_id,e[22]=g,e[23]=b,e[24]=E):E=e[24];let H;return e[25]!==R||e[26]!==E?(H=n.jsxs(n.Fragment,{children:[R,E]}),e[25]=R,e[26]=E,e[27]=H):H=e[27],H},wn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionIdleChecksNodeFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionReclamationStatusCellFragment"}],type:"ComputeSessionNode",abstractKey:null};wn.hash="cd0692b3021358f17c5abea99afd29d2";const _a={warningText:{kMwMTN:"webuis3pv69",$$css:!0}};function Ka(a,e){var l;return e==="remaining"?!a.remaining||a.remaining<3600?$e("red"):a.remaining<3600*4?$e("orange"):$e("green"):a.extra&&(!a.remaining||a.remaining<3600*4)?$e((l=ol(a.extra.resources,a.extra.thresholds_check_operator))==null?void 0:l.color):"neutral"}const ja=a=>{"use memo";const e=oe.c(24),{checkKey:l,value:s,sessionFrgmt:r}=a,{t:d}=Ae(),t=s.remaining??0;let o;e[0]!==d?(o=h=>d(h==="network_timeout"?"session.NetworkIdleTimeout":h==="session_lifetime"?"session.MaxSessionLifetime":"session.UtilizationIdleTimeout"),e[0]=d,e[1]=o):o=e[1];const u=o;let m;e[2]!==d?(m=h=>d(h==="expire_after"?"session.ExpiresAfter":"session.GracePeriod"),e[2]=d,e[3]=m):m=e[3];const c=m,F=l==="utilization"?"utilization":"remaining";let k;e[4]!==F||e[5]!==s?(k=Ka(s,F),e[4]=F,e[5]=s,e[6]=k):k=e[6];const b=k;let x;e[7]!==t?(x=re().add(t,"second").toISOString(),e[7]=t,e[8]=x):x=e[8];const S=x;let p;e[9]===Symbol.for("react.memo_cache_sentinel")?(p={flex:1},e[9]=p):p=e[9];let y;e[10]!==l||e[11]!==u||e[12]!==r?(y=n.jsx(T,{gap:"xxs",children:l==="utilization"?n.jsx(sl,{sessionFrgmt:r}):n.jsx(U,{children:u(l)})}),e[10]=l,e[11]=u,e[12]=r,e[13]=y):y=e[13];let g;e[14]!==b||e[15]!==S||e[16]!==c||e[17]!==t||e[18]!==d||e[19]!==s.remaining_time_type?(g=t>=0?n.jsxs(T,{gap:"xxs",align:"center",children:[n.jsx(tl,{delay:1e3,callback:()=>re(S).diff()>0?il(re().toISOString(),S):"00:00:00",render:h=>n.jsx(gn,{values:[{label:c(s.remaining_time_type),variant:b},{label:h,variant:b}]})}),s.remaining_time_type==="grace_period"&&n.jsx(rl,{title:n.jsx("div",{style:{whiteSpace:"pre-line"},children:d("session.GracePeriodTooltip")})})]}):n.jsx(U,{xstyle:_a.warningText,children:d("session.ReclamationStatusChecking")}),e[14]=b,e[15]=S,e[16]=c,e[17]=t,e[18]=d,e[19]=s.remaining_time_type,e[20]=g):g=e[20];let _;return e[21]!==y||e[22]!==g?(_=n.jsxs(T,{style:p,direction:"column",align:"stretch",children:[y,g]}),e[21]=y,e[22]=g,e[23]=_):_=e[23],_},Ca=({sessionNodeFrgmt:a=null,direction:e="row"})=>{const l=V.useFragment(wn,a),s=yn(l==null?void 0:l.idle_checks,{fallbackValue:{}});return n.jsx(T,{direction:e,align:"stretch",gap:"sm",children:Ve(s,(r,d)=>r.remaining?n.jsx(ja,{checkKey:d,value:r,sessionFrgmt:l},d):null)})},Ia=({...a})=>{const{t:e}=Ae(),{token:l}=dl();return n.jsxs(Ye,{title:e("session.ReclamationStatus"),footer:null,width:700,...a,children:[n.jsx(U,{children:e("session.IdleChecksDesc")}),n.jsx(Be,{level:5,children:e("session.MaxSessionLifetime")}),n.jsx("p",{children:e("session.MaxSessionLifetimeDesc")}),n.jsx(Be,{level:5,children:e("session.NetworkIdleTimeout")}),n.jsx("p",{children:e("session.NetworkIdleTimeoutDesc")}),n.jsx(Be,{level:5,children:e("session.UtilizationIdleTimeout")}),n.jsx("p",{children:e("session.UtilizationIdleTimeoutDesc")}),n.jsxs(T,{direction:"column",align:"stretch",style:{marginLeft:l("--spacing-5")},children:[n.jsx(Be,{level:5,style:{margin:0},children:e("session.GracePeriod")}),n.jsx("p",{children:e("session.GracePeriodDesc")}),n.jsx(Be,{level:5,style:{margin:0},children:e("session.UtilizationThreshold")}),n.jsx("p",{children:e("session.UtilizationThresholdDesc")})]})]})},Bn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksFragment",selections:[{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"ComputeSessionNode",abstractKey:null};Bn.hash="a556c4be60f823378db9d32add579c15";const Aa=({sessionFrgmt:a})=>{var l;const e=V.useFragment(Bn,a);return Ve((l=e.vfolder_nodes)==null?void 0:l.edges,(s,r)=>(s==null?void 0:s.node)&&n.jsx(Jl,{vfolderNodeFragment:s.node},`mounted-vfolder-${r}`))},Dn=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r={defaultValue:null,kind:"LocalArgument",name:"scope"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[a,e,l,s,r],kind:"Fragment",metadata:null,name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[t,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,a,s,e,l],kind:"Operation",name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[t,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},o,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"1bfe7bc2611f279e70c35d22c11fb631",id:null,metadata:{},name:"SessionSchedulingHistoryModalQuery",operationKind:"query",text:`query SessionSchedulingHistoryModalQuery(
  $scope: SessionScope!
  $filter: SessionSchedulingHistoryFilter
  $orderBy: [SessionSchedulingHistoryOrderBy!]
  $limit: Int
  $offset: Int
) {
  sessionScopedSchedulingHistories(scope: $scope, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        ...BAISchedulingHistoryTableFragment
        id
      }
    }
  }
}

fragment BAISchedulingHistoryNodesFragment on SessionSchedulingHistory {
  id
  attempts
  createdAt
  updatedAt
  fromStatus
  toStatus
  message
  phase
  result
}

fragment BAISchedulingHistoryTableFragment on SessionSchedulingHistory {
  id
  phase
  result
  subSteps {
    step
    ...BAISubStepNodesFragment
  }
  ...BAISchedulingHistoryNodesFragment
}

fragment BAISubStepNodesFragment on SubStepResultGQL {
  step
  result
  errorCode
  message
  startedAt
  endedAt
}
`}}})();Dn.hash="6221439d9cf111e4683277c5e89974db";const Na=a=>{"use memo";var be,we,xe,Re;const e=oe.c(116);let l,s,r,d,t;e[0]!==a?({open:d,loading:l,sessionId:t,onCancel:r,...s}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d,e[5]=t):(l=e[1],s=e[2],r=e[3],d=e[4],t=e[5]);const{t:o}=Ae(),[u,m]=fn(),[c,F]=I.useState(),[k,b]=I.useState("-updatedAt"),[x,S]=nn("schedulingHistoryExpandMode"),[p,y]=nn("table_column_overrides.SessionSchedulingHistory");let g;e[6]===Symbol.for("react.memo_cache_sentinel")?(g={current:1,pageSize:10},e[6]=g):g=e[6];const{baiPaginationOption:_,tablePaginationOption:h,setTablePaginationOption:N}=Fn(g),v=I.useDeferredValue(d),K=I.useDeferredValue(u),A=I.useDeferredValue(c),j=I.useDeferredValue(k),L=I.useDeferredValue(_.offset),C=I.useDeferredValue(_.limit);let B;e[7]===Symbol.for("react.memo_cache_sentinel")?(B=Dn,e[7]=B):B=e[7];let M;e[8]!==t?(M={sessionId:t},e[8]=t,e[9]=M):M=e[9];const R=A??void 0;let E;e[10]!==j?(E=ul(j)??[{field:"UPDATED_AT",direction:"DESC"}],e[10]=j,e[11]=E):E=e[11];let H;e[12]!==C||e[13]!==L||e[14]!==M||e[15]!==R||e[16]!==E?(H={scope:M,filter:R,orderBy:E,limit:C,offset:L},e[12]=C,e[13]=L,e[14]=M,e[15]=R,e[16]=E,e[17]=H):H=e[17];const w=v?"network-only":"store-only";let de;e[18]!==K||e[19]!==w?(de={fetchKey:K,fetchPolicy:w},e[18]=K,e[19]=w,e[20]=de):de=e[20];const Ne=V.useLazyLoadQuery(B,H,de);let Q;e[21]!==o?(Q=o("session.SessionSchedulingHistory"),e[21]=o,e[22]=Q):Q=e[22];const i=l||v!==d;let q;e[23]!==N?(q=_e=>{F(_e),N({current:1})},e[23]=N,e[24]=q):q=e[24];let z;e[25]!==o?(z=o("session.ID"),e[25]=o,e[26]=z):z=e[26];let ee;e[27]!==z?(ee={key:"id",propertyLabel:z,type:"uuid",fixedOperator:"equals"},e[27]=z,e[28]=ee):ee=e[28];let ne;e[29]!==o?(ne=o("session.Phase"),e[29]=o,e[30]=ne):ne=e[30];let le;e[31]!==ne?(le={key:"phase",propertyLabel:ne,type:"string",fixedOperator:"contains"},e[31]=ne,e[32]=le):le=e[32];let G;e[33]!==o?(G=o("session.Result"),e[33]=o,e[34]=G):G=e[34];let ue;e[35]===Symbol.for("react.memo_cache_sentinel")?(ue=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[35]=ue):ue=e[35];let ae;e[36]!==G?(ae={key:"result",propertyLabel:G,type:"enum",strictSelection:!0,options:ue},e[36]=G,e[37]=ae):ae=e[37];let se;e[38]!==o?(se=o("session.FromStatus"),e[38]=o,e[39]=se):se=e[39];let J;e[40]!==se?(J={key:"fromStatus",propertyLabel:se,type:"string",valueMode:"scalar"},e[40]=se,e[41]=J):J=e[41];let te;e[42]!==o?(te=o("session.ToStatus"),e[42]=o,e[43]=te):te=e[43];let W;e[44]!==te?(W={key:"toStatus",propertyLabel:te,type:"string",valueMode:"scalar"},e[44]=te,e[45]=W):W=e[45];let $;e[46]!==o?($=o("session.ErrorCode"),e[46]=o,e[47]=$):$=e[47];let Y;e[48]!==$?(Y={key:"errorCode",propertyLabel:$,type:"string",fixedOperator:"contains"},e[48]=$,e[49]=Y):Y=e[49];let je;e[50]!==o?(je=o("session.Message"),e[50]=o,e[51]=je):je=e[51];let ie;e[52]!==je?(ie={key:"message",propertyLabel:je,type:"string",fixedOperator:"contains"},e[52]=je,e[53]=ie):ie=e[53];let X;e[54]!==o?(X=o("session.CreatedAt"),e[54]=o,e[55]=X):X=e[55];let ce;e[56]!==X?(ce={key:"createdAt",propertyLabel:X,type:"datetime",defaultOperator:"after"},e[56]=X,e[57]=ce):ce=e[57];let me;e[58]!==o?(me=o("session.UpdatedAt"),e[58]=o,e[59]=me):me=e[59];let ge;e[60]!==me?(ge={key:"updatedAt",propertyLabel:me,type:"datetime",defaultOperator:"after"},e[60]=me,e[61]=ge):ge=e[61];let pe;e[62]!==ee||e[63]!==le||e[64]!==ae||e[65]!==J||e[66]!==W||e[67]!==Y||e[68]!==ie||e[69]!==ce||e[70]!==ge?(pe=[ee,le,ae,J,W,Y,ie,ce,ge],e[62]=ee,e[63]=le,e[64]=ae,e[65]=J,e[66]=W,e[67]=Y,e[68]=ie,e[69]=ce,e[70]=ge,e[71]=pe):pe=e[71];let Se;e[72]!==c||e[73]!==q||e[74]!==pe?(Se=n.jsx(cl,{value:c,onChange:q,filterProperties:pe}),e[72]=c,e[73]=q,e[74]=pe,e[75]=Se):Se=e[75];const Le=K!==u;let ye;e[76]!==u||e[77]!==Le||e[78]!==m?(ye=n.jsx(T,{children:n.jsx(ml,{value:u,onChange:m,loading:Le,autoUpdateDelay:null})}),e[76]=u,e[77]=Le,e[78]=m,e[79]=ye):ye=e[79];let fe;e[80]!==Se||e[81]!==ye?(fe=n.jsxs(T,{justify:"between",wrap:"wrap",gap:"sm",children:[Se,ye]}),e[80]=Se,e[81]=ye,e[82]=fe):fe=e[82];const ve=K!==u||A!==c||j!==k||L!==_.offset||C!==_.limit;let Fe;e[83]!==N?(Fe=_e=>{b(_e),N({current:1})},e[83]=N,e[84]=Fe):Fe=e[84];const Te=x??void 0;let ke;e[85]!==p||e[86]!==y?(ke={columnOverrides:p,onColumnOverridesChange:y},e[85]=p,e[86]=y,e[87]=ke):ke=e[87];const Ee=((be=Ne.sessionScopedSchedulingHistories)==null?void 0:be.count)??0;let he;e[88]!==N?(he=(_e,He)=>{N({current:_e,pageSize:He})},e[88]=N,e[89]=he):he=e[89];let f;e[90]!==Ee||e[91]!==he||e[92]!==h.current||e[93]!==h.pageSize?(f={pageSize:h.pageSize,current:h.current,total:Ee,onChange:he},e[90]=Ee,e[91]=he,e[92]=h.current,e[93]=h.pageSize,e[94]=f):f=e[94];let D;e[95]!==((we=Ne.sessionScopedSchedulingHistories)==null?void 0:we.edges)?(D=Ve((xe=Ne.sessionScopedSchedulingHistories)==null?void 0:xe.edges,"node"),e[95]=(Re=Ne.sessionScopedSchedulingHistories)==null?void 0:Re.edges,e[96]=D):D=e[96];let O;e[97]!==k||e[98]!==S||e[99]!==ve||e[100]!==Fe||e[101]!==Te||e[102]!==ke||e[103]!==f||e[104]!==D?(O=n.jsx(fa,{resizable:!0,loading:ve,order:k,onChangeOrder:Fe,expandMode:Te,onExpandModeChange:S,tableSettings:ke,pagination:f,schedulingHistoryFrgmt:D}),e[97]=k,e[98]=S,e[99]=ve,e[100]=Fe,e[101]=Te,e[102]=ke,e[103]=f,e[104]=D,e[105]=O):O=e[105];let Z;e[106]!==fe||e[107]!==O?(Z=n.jsxs(T,{direction:"column",align:"stretch",gap:"sm",children:[fe,O]}),e[106]=fe,e[107]=O,e[108]=Z):Z=e[108];let Ce;return e[109]!==s||e[110]!==r||e[111]!==d||e[112]!==i||e[113]!==Z||e[114]!==Q?(Ce=n.jsx(Ye,{title:Q,loading:i,open:d,variant:"fullscreen",footer:null,onCancel:r,...s,children:Z}),e[109]=s,e[110]=r,e[111]=d,e[112]=i,e[113]=Z,e[114]=Q,e[115]=Ce):Ce=e[115],Ce},on=(a,e)=>{const l=JSON.parse(a||"{}"),s=hn(e);return s?{...ze(l,s),acceleratorType:s}:l},Ge=a=>Hl($l(JSON.parse(a||"{}"),e=>Ul(e)),e=>e===0),La=a=>{"use memo";var ce,me,ge,pe,Se,Le,ye,fe,ve,Fe,Te,ke,Ee,he;const e=oe.c(55),{id:l,fetchKey:s,sessionFrgmt:r,project:d}=a,{t}=Ae(),{md:o}=gl(),{mergedResourceSlots:u}=pl(),m=kn(),[c]=pn(),F=Sl(),[k,b]=I.useState(!1),x="current",[S,p]=I.useState("kernels"),[y,g]=ln(!1),{toggle:_}=g,[h,N]=ln(!1),{toggle:v}=N,[K,A]=V.useQueryLoader(Wl);let j;e[0]===Symbol.for("react.memo_cache_sentinel")?(j={current:1,pageSize:10},e[0]=j):j=e[0];const{baiPaginationOption:L,setTablePaginationOption:C}=Fn(j);let B;e[1]!==A||e[2]!==C?(B=(f,D)=>{const O=f.limit??10;C({pageSize:O,current:f.offset?Math.floor(f.offset/O)+1:1}),A(f,D)},e[1]=A,e[2]=C,e[3]=B):B=e[3];const M=B;let R;e[4]===Symbol.for("react.memo_cache_sentinel")?(R=Ln,e[4]=R):R=e[4];let E;e[5]!==l?(E=mn("ComputeSessionNode",l),e[5]=l,e[6]=E):E=e[6];let H;e[7]!==E?(H={id:E},e[7]=E,e[8]=H):H=e[8];const w=s===Vl?r?"store-only":"store-and-network":"network-only";let de;e[9]!==s||e[10]!==w?(de={fetchPolicy:w,fetchKey:s},e[9]=s,e[10]=w,e[11]=de):de=e[11];const{internalLoadedSession:Ne}=V.useLazyLoadQuery(R,H,de);let Q;e[12]===Symbol.for("react.memo_cache_sentinel")?(Q=Nn,e[12]=Q):Q=e[12];const i=V.useFragment(Q,Ne||r);let q;e[13]===Symbol.for("react.memo_cache_sentinel")?(q={fallbackValue:{}},e[13]=q):q=e[13];const z=yl(fl(yn(i==null?void 0:i.idle_checks,q)).map(va).filter(Boolean)),ee=i==null?void 0:i.project_id,ne=i==null?void 0:i.requested_slots,le=i==null?void 0:i.tag;let G;e[14]!==ne||e[15]!==le?(G=on(ne,le),e[14]=ne,e[15]=le,e[16]=G):G=e[16];const ue=G,ae=i==null?void 0:i.occupied_slots,se=i==null?void 0:i.tag;let J;e[17]!==ae||e[18]!==se?(J=on(ae,se),e[17]=ae,e[18]=se,e[19]=J):J=e[19];const te=J;let W;e[20]!==(i==null?void 0:i.occupied_slots)?(W=Pe(Ge(i==null?void 0:i.occupied_slots)),e[20]=i==null?void 0:i.occupied_slots,e[21]=W):W=e[21];const $=!W;let Y;if(e[22]!==$||e[23]!==u||e[24]!==(i==null?void 0:i.occupied_slots)||e[25]!==(i==null?void 0:i.requested_slots)||e[26]!==(i==null?void 0:i.tag)){const f=hn(i==null?void 0:i.tag)??"",D=ze(Ge(i==null?void 0:i.requested_slots),f),O=ze(Ge(i==null?void 0:i.occupied_slots),f);let Z;e[28]!==u?(Z=(be,we)=>{var _e,He;const xe=(_e=u==null?void 0:u[be])==null?void 0:_e.number_format,Re=(xe==null?void 0:xe.round_length)||0;return xe!=null&&xe.binary?Number((He=zl(we.toString(),"g",2,!0))==null?void 0:He.numberFixed):Re>0?Number(we.toFixed(Re)):we},e[28]=u,e[29]=Z):Z=e[29];const Ce=Z;Y=$?Zl(an(D),an(O)).filter(be=>Ce(be,O[be]??0)<Ce(be,D[be]??0)):[],e[22]=$,e[23]=u,e[24]=i==null?void 0:i.occupied_slots,e[25]=i==null?void 0:i.requested_slots,e[26]=i==null?void 0:i.tag,e[27]=Y}else Y=e[27];const ie=Y.length>0;let X;return e[30]!==S||e[31]!==K||e[32]!==L||e[33]!==c||e[34]!==$||e[35]!==ie||e[36]!==l||e[37]!==z||e[38]!==A||e[39]!==m||e[40]!==o||e[41]!==te||e[42]!==y||e[43]!==k||e[44]!==h||e[45]!==d||e[46]!==M||e[47]!==ue||e[48]!==ee||e[49]!==i||e[50]!==t||e[51]!==_||e[52]!==v||e[53]!==F?(X=i?n.jsxs(T,{direction:"column",gap:"lg",align:"stretch",children:[d!==null&&ee!==d.id&&n.jsx(Ue,{role:"alert",status:"warning",title:t("session.NotInProject")}),c.uuid!==(i==null?void 0:i.user_id)&&n.jsx(Ue,{role:"alert",status:"warning",title:t("session.AnotherUserSession")}),z&&z<3600&&n.jsx(Ue,{role:"alert",status:"warning",title:t("session.IdleCheckExpirationWarning")}),n.jsxs(T,{direction:"column",gap:"sm",align:"stretch",children:[n.jsxs(T,{direction:"row",justify:"between",align:"start",style:{alignSelf:"stretch"},gap:"sm",children:[n.jsx(xa,{sessionFrgmt:i,level:3,dimmed:["TERMINATED","CANCELLED"].includes(i.status||""),editable:!["TERMINATED","CANCELLED"].includes(i.status||"")}),n.jsx(Fl,{size:"large",compact:!0,sessionFrgmt:i})]}),n.jsx(kl,{children:n.jsxs(hl,{columns:o?2:1,children:[n.jsx(P,{label:t("session.SessionId"),children:n.jsx(Oe,{code:!0,copyable:!0,ellipsis:{tooltip:!0},children:i.row_id??""})}),(F==="admin"||F==="superadmin")&&n.jsx(P,{label:t("credential.UserID"),children:(ce=i.owner)!=null&&ce.email?i.owner.email:i.user_id?n.jsx(I.Suspense,{fallback:n.jsx(Ie,{variant:"input",size:"small"}),children:n.jsx(ka,{uuid:i.user_id})}):"-"}),n.jsx(P,{label:t("general.AccessKey"),children:n.jsx(bl,{sessionFrgmt:i,copyable:!0})}),n.jsx(P,{label:t("session.Status"),children:n.jsxs(T,{children:[n.jsx(xl,{sessionFrgmt:i}),n.jsx(De,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(Xl,{size:"1em"}),label:t("session.SessionSchedulingHistory"),tooltip:t("session.SessionSchedulingHistory"),onClick:()=>v()})]})}),n.jsx(P,{label:t("session.SessionType"),children:n.jsxs(T,{children:[n.jsx(_l,{sessionFrgmt:i}),i.type==="batch"&&i.startup_command&&n.jsx(De,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(Kl,{size:"1em"}),label:t("session.ViewStartupCommand"),tooltip:t("session.ViewStartupCommand"),onClick:()=>_()})]})}),n.jsx(P,{label:t("session.launcher.Environments"),children:(pe=(ge=(me=i.kernel_nodes)==null?void 0:me.edges[0])==null?void 0:ge.node)!=null&&pe.image?n.jsx(jl,{imageFrgmt:((ye=(Le=(Se=i.kernel_nodes)==null?void 0:Se.edges[0])==null?void 0:Le.node)==null?void 0:ye.image)||null}):i.row_id?n.jsx(I.Suspense,{fallback:n.jsx(Ie,{variant:"input",size:"small"}),children:n.jsx(Cl,{sessionId:i.row_id})}):null}),n.jsx(P,{label:t("session.launcher.MountedFolders"),children:n.jsx(T,{gap:"xs",wrap:"wrap",children:n.jsx(Aa,{sessionFrgmt:i})})}),n.jsx(P,{label:t("session.launcher.ResourceAllocation"),children:n.jsxs(T,{gap:"sm",wrap:"wrap",align:"center",children:[ie&&n.jsx(Il,{content:t("session.AllocatedLessThanRequested"),icon:n.jsx(Al,{size:"1em",style:{color:"var(--color-warning)"}})}),n.jsx(Nl,{content:t("session.ResourceGroup"),children:n.jsx(Ll,{label:i.scaling_group??""})}),n.jsx(vl,{resource:$?te:ue,comparedResource:$?ue:void 0,showDividers:!0})]})}),n.jsx(P,{label:t("session.Agent"),children:n.jsx(Tl,{sessionFrgmt:i})}),n.jsx(P,{label:t("session.Reservation"),children:n.jsx(T,{gap:"xs",wrap:"wrap",children:n.jsx(El,{sessionFrgmt:i})})}),n.jsx(P,{label:t("session.ClusterMode"),children:n.jsx(wl,{sessionFrgmt:i,showSize:!0})}),i.status==="RUNNING"&&z?n.jsx(P,{label:t("session.ReclamationStatus"),children:n.jsxs(T,{gap:"xxs",align:"start",children:[n.jsx(I.Suspense,{fallback:n.jsx(Ie,{variant:"input",size:"small"}),children:n.jsx(Ca,{sessionNodeFrgmt:i,direction:o?"row":"column"})}),n.jsx(De,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(Bl,{size:"1em"}),label:t("button.ClickForMoreDetails"),tooltip:t("button.ClickForMoreDetails"),onClick:()=>b(!0)})]})}):null,n.jsx(P,{label:t("session.ResourceUsage"),children:n.jsx(Dl,{sessionFrgmt:i,displayTarget:x})}),(((fe=i.dependees)==null?void 0:fe.count)??0)>0&&n.jsx(P,{label:t("session.DependsOn"),children:n.jsx(T,{gap:"xs",wrap:"wrap",children:(Fe=(ve=i.dependees)==null?void 0:ve.edges)==null?void 0:Fe.map(Ta).filter(Boolean).map(f=>{const D=new URLSearchParams(m.search);return f!=null&&f.row_id&&D.set("sessionDetail",f.row_id),n.jsx(sn,{type:"hover",to:{pathname:m.pathname,search:D.toString()},children:f==null?void 0:f.name},f==null?void 0:f.row_id)})})}),(((Te=i.dependents)==null?void 0:Te.count)??0)>0&&n.jsx(P,{label:t("session.DependedByOthers"),children:n.jsx(T,{gap:"xs",wrap:"wrap",children:(Ee=(ke=i.dependents)==null?void 0:ke.edges)==null?void 0:Ee.map(Ea).filter(Boolean).map(f=>{const D=new URLSearchParams(m.search);return f!=null&&f.row_id&&D.set("sessionDetail",f.row_id),n.jsx(sn,{type:"hover",to:{pathname:m.pathname,search:D.toString()},children:f==null?void 0:f.name},f==null?void 0:f.row_id)})})})]})})]}),n.jsxs(T,{direction:"column",align:"stretch",gap:"sm",children:[n.jsxs(Ml,{hasDivider:!0,value:S,onChange:f=>{f==="auditLog"&&i.row_id&&!K&&A({scope:{entity:[{entityType:"SESSION",entityId:i.row_id}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:L.limit,offset:L.offset},{fetchPolicy:"store-and-network"}),p(f)},children:[n.jsx(tn,{value:"kernels",label:t("kernel.Kernels")}),i.row_id?n.jsx(tn,{value:"auditLog",label:t("auditLog.AuditLog")}):null]}),S==="kernels"&&n.jsx(I.Suspense,{fallback:n.jsx(Ie,{}),children:n.jsx(ba,{kernelsFrgmt:Me((he=i.kernel_nodes)==null?void 0:he.edges.map(wa)),sessionFrgmtForLogModal:i})}),S==="auditLog"&&i.row_id&&n.jsx(Rl,{children:K?n.jsx(I.Suspense,{fallback:n.jsx(Ie,{}),children:n.jsx(Yl,{queryRef:K,onReload:M,tableSettings:{}})}):n.jsx(Ie,{})})]}),n.jsx(Ia,{open:k,onCancel:()=>b(!1)}),n.jsx(ha,{open:y,language:"shell",content:i.startup_command||"",title:t("session.StartupCommand"),footer:n.jsx(Pl,{variant:"primary",label:t("button.Close"),onClick:()=>{_()}}),onCancel:_}),n.jsx(Na,{sessionId:l,open:h,onCancel:v})]}):n.jsx(Ue,{role:"alert",status:"error",title:t("session.SessionNotFound"),description:l}),e[30]=S,e[31]=K,e[32]=L,e[33]=c,e[34]=$,e[35]=ie,e[36]=l,e[37]=z,e[38]=A,e[39]=m,e[40]=o,e[41]=te,e[42]=y,e[43]=k,e[44]=h,e[45]=d,e[46]=M,e[47]=ue,e[48]=ee,e[49]=i,e[50]=t,e[51]=_,e[52]=v,e[53]=F,e[54]=X):X=e[54],X};function va(a){return a.remaining}function Ta(a){return a==null?void 0:a.node}function Ea(a){return a==null?void 0:a.node}function wa(a){return a==null?void 0:a.node}const Ha=({sessionId:a,project:e,...l})=>{const{t:s}=Ae();Sn();const[r,d]=I.useTransition(),[t,o]=fn(),u=kn(),{sessionDetailDrawerFrgmt:m,createdAt:c}=u.state||{},F=V.useFragment(An,m),k=I.useMemo(()=>c&&re().diff(re(c),"second")<60?F:null,[]);return n.jsx(Ol,{...l,side:"end",size:800,title:s("session.SessionInfo"),extra:n.jsx(Ql,{settingId:"session-detail",defaultAutoUpdateDelay:1e4,loading:r,value:t,onChange:b=>{d(()=>{o(b)})}}),children:n.jsx(I.Suspense,{fallback:n.jsx(Ie,{}),children:a&&n.jsx(La,{id:a,fetchKey:t,sessionFrgmt:k,project:e})})})};export{na as B,Ha as S,ua as a,ya as b,Cn as c,ea as n,Zl as u};
//# sourceMappingURL=SessionDetailDrawer-r93Udkje.js.map
