import{am as be,dD as Yn,j as n,i as ue,bV as Xe,fb as Zn,aB as Ze,r as P,ai as hn,aT as $e,aZ as Fn,v as ee,t as Ue,ak as el,ar as Qe,l as j,cI as kn,a1 as nl,e5 as ll,an as ze,fa as sn,a3 as B,W as bn,a9 as qe,g5 as al,u as Ae,N as we,f as xn,g as en,aR as sl,e6 as tn,ap as tl,g6 as il,g7 as rl,e4 as _n,a as He,dG as ol,bq as Ve,C as dl,g8 as ul,aH as cl,F as rn,H as ml,Y as gl,g9 as jn,c as L,ga as pl,dE as Sl,gb as yl,B as fl,gc as hl,a$ as Kn,e as Cn,M as N,gd as In,di as Fl,dh as kl,ac as bl,aV as Le,aO as Nn,a8 as on,aX as Ln,aS as xl,aP as _l,dO as jl,bl as Kl,ad as An,bF as dn,g4 as Cl,f4 as Il,ge as vn,c$ as Nl,ck as un,w as Oe,gf as Ll,d as Al,gg as vl,cJ as cn,gh as Tl,gi as El,gj as wl,eJ as Ml,T as Dl,s as Rl,gk as Bl,gl as Pl,gm as Vl,eg as $l,cG as Hl,gn as zl,ds as mn,dq as Ul,dp as gn,cr as Ol,au as Ql,bh as ql,bB as Gl,bW as Wl,c0 as Jl,cj as Xl,dr as Yl,dx as Zl}from"./index-B-6GqBhJ.js";import{S as ea}from"./scroll-text-CncKp3rA.js";import{o as na}from"./orderBy-BcAKhHRm.js";import{F as Tn}from"./FolderLink-BixUYyr6.js";import{z as la}from"./zip-DUWDYNfS.js";import{S as aa,a as sa}from"./ScopedAuditLog-D4HOQVjA.js";import{B as ta}from"./BAIGraphQLPropertyFilter-Bp1GJNAy.js";import{R as ia}from"./rotate-ccw-clock-DIhz6B-L.js";const ra=(a,e=/(<br\s*\/?>|\n)/)=>be(Yn(a,e),(l,t)=>l.match(e)?n.jsx("br",{},t):l),En={SUCCESS:"success",FAILURE:"error",STALE:"default",NEED_RETRY:"warning",EXPIRED:"error",GIVE_UP:"error",SKIPPED:"default"},oa=a=>{"use memo";const e=ue.c(12);let l,t;e[0]!==a?({result:t,...l}=a,e[0]=a,e[1]=l,e[2]=t):(l=e[1],t=e[2]);let r;e[3]!==t?(r=t?Xe(En,t):void 0,e[3]=t,e[4]=r):r=e[4];const d=r;let s;e[5]!==l.style?(s={whiteSpace:"nowrap",...l.style},e[5]=l.style,e[6]=s):s=e[6];let o;return e[7]!==l||e[8]!==t||e[9]!==d||e[10]!==s?(o=n.jsx(Zn,{...l,color:d,text:t,style:s}),e[7]=l,e[8]=t,e[9]=d,e[10]=s,e[11]=o):o=e[11],o},wn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null}],type:"SessionSchedulingHistory",abstractKey:null};wn.hash="a52af4f53e01beb70d74f67b151aa5e0";const Ye=[];[...Ye,...Ye.map(a=>`-${a}`)];const Ne=a=>el(Ye,a),da=a=>{"use memo";const e=ue.c(23);let l,t,r,d,s;e[0]!==a?({schedulingHistoryFrgmt:d,disableSorter:t,customizeColumns:l,onChangeOrder:r,...s}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d,e[5]=s):(l=e[1],t=e[2],r=e[3],d=e[4],s=e[5]);const{t:o}=Ze();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=wn,e[6]=u):u=e[6];const m=P.useFragment(u,d);let c;if(e[7]!==l||e[8]!==t||e[9]!==o){let h;e[11]!==t?(h=p=>t?Qe(p,"sorter"):p,e[11]=t,e[12]=h):h=e[12];const k=be(hn([{dataIndex:"updatedAt",title:o("comp:BAISchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:ua,sorter:Ne("updated_at")},{dataIndex:"createdAt",title:o("comp:BAISchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:ca,sorter:Ne("created_at")},{dataIndex:"phase",title:o("comp:BAISchedulingHistoryNodes.Phase"),key:"phase",sorter:Ne("phase")},{dataIndex:"result",title:o("comp:BAISchedulingHistoryNodes.Result"),key:"result",render:ma,sorter:Ne("result")},{key:"fromStatus",title:o("comp:BAISchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Ne("from_status")},{key:"toStatus",title:o("comp:BAISchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Ne("to_status")},{dataIndex:"attempts",title:o("comp:BAISchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Ne("attempts")},{key:"message",title:o("comp:BAISchedulingHistoryNodes.Message"),dataIndex:"message",onCell:ga,render:pa,sorter:Ne("message")}]),h);c=l?l(k):k,e[7]=l,e[8]=t,e[9]=o,e[10]=c}else c=e[10];const S=c;let y;e[13]===Symbol.for("react.memo_cache_sentinel")?(y={x:"max-content"},e[13]=y):y=e[13];let F;e[14]!==m?(F=$e(m),e[14]=m,e[15]=F):F=e[15];let f;e[16]!==r?(f=h=>{r==null||r(h||null)},e[16]=r,e[17]=f):f=e[17];let g;return e[18]!==S||e[19]!==F||e[20]!==f||e[21]!==s?(g=n.jsx(Fn,{scroll:y,rowKey:"id",dataSource:F,columns:S,onChangeOrder:f,...s}),e[18]=S,e[19]=F,e[20]=f,e[21]=s,e[22]=g):g=e[22],g};function ua(a){return n.jsx("span",{children:ee(a).format("ll LTS")})}function ca(a){return n.jsx("span",{children:ee(a).format("ll LTS")})}function ma(a,e){const l=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(oa,{result:l})}function ga(){return{style:{maxWidth:500}}}function pa(a,e){return e.message?n.jsx(Ue,{title:e.message,style:{width:"100%"},children:ra(e.message)}):"-"}const Mn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryNodesFragment"}],type:"SessionSchedulingHistory",abstractKey:null};Mn.hash="e369227c362b363c91d9f366ac98634d";const Sa="errors-only",ya=a=>!ze(a.subSteps),We=(a,e,l)=>e==="expand-all"?a.filter(l).map(t=>t.id):e==="collapse-all"?[]:a.filter(t=>l(t)&&t.result!=="SUCCESS").map(t=>t.id),fa=(a,e)=>{"use memo";const l=ue.c(28),{t}=Ze(),r=(e==null?void 0:e.mode)??Sa;let d;l[0]!==e?(d=_=>e!=null&&e.isExpandable?e.isExpandable(_):ya(_),l[0]=e,l[1]=d):d=l[1];const s=d;let o;l[2]!==a||l[3]!==s||l[4]!==r?(o=()=>We(a,r,s),l[2]=a,l[3]=s,l[4]=r,l[5]=o):o=l[5];const[u,m]=j.useState(o);let c;if(l[6]!==a||l[7]!==s){let _;l[9]!==s?(_=E=>`${E.id}:${E.result??""}:${s(E)?1:0}`,l[9]=s,l[10]=_):_=l[10],c=a.map(_).join("|"),l[6]=a,l[7]=s,l[8]=c}else c=l[8];const S=c,[y,F]=j.useState(S),[f,g]=j.useState(r);(S!==y||r!==f)&&(F(S),g(r),m(We(a,r,s)));let h;l[11]!==a||l[12]!==s?(h=a.filter(s).map(ha),l[11]=a,l[12]=s,l[13]=h):h=l[13];const k=h;let p;l[14]===Symbol.for("react.memo_cache_sentinel")?(p=_=>{m([..._])},l[14]=p):p=l[14];const K=p;let b;if(l[15]!==a||l[16]!==s||l[17]!==e||l[18]!==t){const _={"expand-all":t("comp:BAITable.ExpandAll"),"collapse-all":t("comp:BAITable.CollapseAll"),"errors-only":t("comp:BAITable.ExpandErrorsOnly")},E=I=>{var M;m(We(a,I,s)),(M=e==null?void 0:e.onModeChange)==null||M.call(e,I)};b=["expand-all","collapse-all","errors-only"].map(I=>({label:_[I],onClick:()=>E(I)})),l[15]=a,l[16]=s,l[17]=e,l[18]=t,l[19]=b}else b=l[19];const A=b;let T;l[20]!==k.length||l[21]!==A||l[22]!==t?(T=k.length>0?n.jsx(kn,{justify:"center",children:n.jsx(nl,{items:A,button:{variant:"ghost",size:"sm",isIconOnly:!0,icon:n.jsx(ll,{size:"1em"}),label:t("comp:BAITable.ExpandOptions"),tooltip:t("comp:BAITable.ExpandOptions")},hasChevron:!1})}):null,l[20]=k.length,l[21]=A,l[22]=t,l[23]=T):T=l[23];const C=T;let v;return l[24]!==C||l[25]!==u||l[26]!==r?(v={mode:r,expandedRowKeys:u,onExpandedRowsChange:K,expandColumnTitle:C},l[24]=C,l[25]=u,l[26]=r,l[27]=v):v=l[27],v};function ha(a){return a.id}const Dn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISubStepNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],type:"SubStepResultGQL",abstractKey:null};Dn.hash="b293ef89b3c67ebb0a3733e1c22f6df9";const Fa="HH:mm:ss.SSS",ka=(a,e)=>{if(!a||!e)return null;const l=ee(e).diff(ee(a));if(!Number.isFinite(l)||l<0)return null;if(l<1e3)return`${Math.round(l)} ms`;if(l<6e4)return`${(l/1e3).toFixed(2)} s`;const t=Math.round(l/1e3),r=Math.floor(t/60);return r<60?`${r}m ${String(t%60).padStart(2,"0")}s`:`${Math.floor(r/60)}h ${String(r%60).padStart(2,"0")}m`},pn=a=>a.trim().toLowerCase().replace(/[\s_-]+/g,"-"),Rn=(a,e,l,t)=>e===l-1&&!!t&&pn(a.step)===pn(t),Bn=(a,e)=>{const l=$e(a);return l.filter((t,r)=>!Rn(t,r,l.length,e)).length},ba=a=>(a==null?void 0:a.replace(/\s*\n\s*/g," ").trim())||"-",xa=a=>a&&a!=="%future added value"?a:null,_a=a=>{"use memo";const e=ue.c(39);let l,t,r,d;e[0]!==a?({subStepsFrgmt:d,parentPhase:r,className:l,...t}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d):(l=e[1],t=e[2],r=e[3],d=e[4]);const{t:s}=Ze();let o;e[5]===Symbol.for("react.memo_cache_sentinel")?(o=Dn,e[5]=o):o=e[5];const u=P.useFragment(o,d);let m,c,S,y,F,f,g;if(e[6]!==l||e[7]!==t||e[8]!==r||e[9]!==u||e[10]!==s){const b=$e(u);e[18]!==l?(f=sn("bai-substep-panel",l),e[18]=l,e[19]=f):f=e[19],g=t,F="bai-substep-scroll",c="bai-substep-table";let A,T;e[20]===Symbol.for("react.memo_cache_sentinel")?(S=n.jsxs("colgroup",{children:[n.jsx("col",{className:"bai-substep-col-rail"}),n.jsx("col",{className:"bai-substep-col-step"}),n.jsx("col",{className:"bai-substep-col-result"}),n.jsx("col",{className:"bai-substep-col-duration"}),n.jsx("col",{className:"bai-substep-col-time"}),n.jsx("col",{className:"bai-substep-col-code"}),n.jsx("col",{})]}),T=n.jsx("th",{scope:"col"}),A=[["Step",void 0],["Result",void 0],["Duration","bai-substep-num"],["Time",void 0],["ErrorCode",void 0],["Message",void 0]],e[20]=A,e[21]=S,e[22]=T):(A=e[20],S=e[21],T=e[22]),e[23]!==s?(y=n.jsx("thead",{children:n.jsxs("tr",{children:[T,A.map(C=>{const[v,_]=C;return n.jsx("th",{scope:"col",className:_,children:n.jsx(B,{type:"supporting",weight:"medium",children:s(`comp:BAISubStepNodes.${v}`)})},v)})]})}),e[23]=s,e[24]=y):y=e[24],m=b.map((C,v)=>{const _=xa(C.result),E=Rn(C,v,b.length,r),I=ka(C.startedAt,C.endedAt);return n.jsxs("tr",{className:sn("bai-substep-row",E&&"bai-substep-row--marker"),"data-variant":_?En[_]:"default",children:[n.jsx("td",{className:"bai-substep-rail-cell"}),n.jsx("td",{children:n.jsx(B,{type:"code",size:"sm",color:E?"secondary":"primary",children:C.step})}),n.jsx("td",{children:_?n.jsx("span",{className:"bai-substep-result",children:n.jsx(B,{type:"supporting",color:"inherit",children:_})}):null}),n.jsx("td",{className:"bai-substep-num",children:!E&&I?n.jsx(B,{type:"code",size:"sm",color:"secondary",children:I}):n.jsx(B,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:C.startedAt?n.jsx(B,{type:"code",size:"sm",color:"secondary",children:ee(C.startedAt).format(Fa)}):null}),n.jsx("td",{children:C.errorCode?n.jsx("span",{className:"bai-substep-code",children:n.jsx(B,{type:"code",size:"sm",color:"secondary",children:C.errorCode})}):n.jsx(B,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:n.jsx(B,{type:"supporting",children:E?s("comp:BAISubStepNodes.ResultMarker"):ba(C.message)})})]},`${C.step}-${v}`)}),e[6]=l,e[7]=t,e[8]=r,e[9]=u,e[10]=s,e[11]=m,e[12]=c,e[13]=S,e[14]=y,e[15]=F,e[16]=f,e[17]=g}else m=e[11],c=e[12],S=e[13],y=e[14],F=e[15],f=e[16],g=e[17];let h;e[25]!==m?(h=n.jsx("tbody",{children:m}),e[25]=m,e[26]=h):h=e[26];let k;e[27]!==c||e[28]!==S||e[29]!==y||e[30]!==h?(k=n.jsxs("table",{className:c,children:[S,y,h]}),e[27]=c,e[28]=S,e[29]=y,e[30]=h,e[31]=k):k=e[31];let p;e[32]!==k||e[33]!==F?(p=n.jsx("div",{className:F,children:k}),e[32]=k,e[33]=F,e[34]=p):p=e[34];let K;return e[35]!==p||e[36]!==f||e[37]!==g?(K=n.jsx("div",{className:f,...g,children:p}),e[35]=p,e[36]=f,e[37]=g,e[38]=K):K=e[38],K},ja=a=>{"use memo";const e=ue.c(24);let l,t,r,d;e[0]!==a?({schedulingHistoryFrgmt:d,expandMode:l,onExpandModeChange:t,...r}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d):(l=e[1],t=e[2],r=e[3],d=e[4]);let s;e[5]===Symbol.for("react.memo_cache_sentinel")?(s=Mn,e[5]=s):s=e[5];const o=P.useFragment(s,d);let u;e[6]!==o?(u=$e(o),e[6]=o,e[7]=u):u=e[7];const m=u;let c;e[8]!==l||e[9]!==t?(c={mode:l,onModeChange:t,isExpandable:Ka},e[8]=l,e[9]=t,e[10]=c):c=e[10];const{expandedRowKeys:S,onExpandedRowsChange:y,expandColumnTitle:F}=fa(m,c);let f,g;e[11]!==m?(f=p=>{var K;return Bn(((K=m.find(b=>b.id===p.id))==null?void 0:K.subSteps)??[],p.phase)>0},g=p=>{var K;return n.jsx(_a,{subStepsFrgmt:((K=m.find(b=>b.id===p.id))==null?void 0:K.subSteps)??[],parentPhase:p.phase})},e[11]=m,e[12]=f,e[13]=g):(f=e[12],g=e[13]);let h;e[14]!==F||e[15]!==S||e[16]!==y||e[17]!==f||e[18]!==g?(h={columnTitle:F,expandedRowKeys:S,onExpandedRowsChange:y,rowExpandable:f,expandedRowRender:g},e[14]=F,e[15]=S,e[16]=y,e[17]=f,e[18]=g,e[19]=h):h=e[19];let k;return e[20]!==o||e[21]!==r||e[22]!==h?(k=n.jsx(da,{schedulingHistoryFrgmt:o,expandable:h,...r}),e[20]=o,e[21]=r,e[22]=h,e[23]=k):k=e[23],k};function Ka(a){return Bn(a.subSteps??[],a.phase)>0}const Pn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"6cb167705df49d003fee4ee02f1ee82e",id:null,metadata:{},name:"UNSAFELazyUserEmailViewQuery",operationKind:"query",text:`query UNSAFELazyUserEmailViewQuery(
  $uuid: String!
) {
  user_node(id: $uuid) {
    email
    id
  }
}
`}}})();Pn.hash="67caa5daf6f6559a42a344a9b5eadff6";const Ca=({uuid:a,fetchKey:e,...l})=>{const{user_node:t}=P.useLazyLoadQuery(Pn,{uuid:a?bn("UserNode",a):""},{fetchPolicy:a?e===void 0?"store-or-network":"network-only":"store-only",fetchKey:e});return(t==null?void 0:t.email)&&n.jsx(Ue,{...l,children:t==null?void 0:t.email})},Vn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailDrawerFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],type:"ComputeSessionNode",abstractKey:null};Vn.hash="eb57207016a6a8cf6abbf348456840de";const $n=(function(){var a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,e,l,t],storageKey:null}],storageKey:null},r];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailContentFragment",selections:[a,e,l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},r],storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIImageNodeSimpleTagFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"ConnectedKernelListFragment"}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:d,storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusTagFragment"},{args:null,kind:"FragmentSpread",name:"SessionActionButtonsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionTypeTagFragment"},{args:null,kind:"FragmentSpread",name:"EditableSessionNameFragment"},{args:null,kind:"FragmentSpread",name:"SessionReservationFragment"},{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionUsageMonitorFragment"},{args:null,kind:"FragmentSpread",name:"ContainerCommitModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionIdleChecksNodeFragment"},{args:null,kind:"FragmentSpread",name:"SessionStatusDetailModalFragment"},{args:null,kind:"FragmentSpread",name:"AppLauncherModalFragment"},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionAgentIdsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionClusterModeFragment"},{args:null,kind:"FragmentSpread",name:"SessionAccessKeyFragment"}],type:"ComputeSessionNode",abstractKey:null}})();$n.hash="2d8bdb2a78858803c038b1435d8f8798";const Hn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},m=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],c={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},S=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,t,r,d],storageKey:null}],storageKey:null},s];return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[l,t,r,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[t,r,l],storageKey:null}],storageKey:null},s],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},o,u,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:m,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:m,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},o,l],storageKey:null},l,t,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},d,c,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:S,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:S,storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}]},params:{cacheID:"de1206313d8dcbb1eb44c68956e9a041",id:null,metadata:{},name:"SessionDetailContentQuery",operationKind:"query",text:`query SessionDetailContentQuery(
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
`}}})();Hn.hash="54a57e1f9b8de6ca1ec280de81b4e986";const Ia=a=>{"use memo";const e=ue.c(10);let l,t,r;e[0]!==a?({content:l,language:t,...r}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r):(l=e[1],t=e[2],r=e[3]);let d;e[4]!==l||e[5]!==t?(d=n.jsx(al,{language:t,children:l}),e[4]=l,e[5]=t,e[6]=d):d=e[6];let s;return e[7]!==r||e[8]!==d?(s=n.jsx(qe,{...r,children:d}),e[7]=r,e[8]=d,e[9]=s):s=e[9],s},zn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ConnectedKernelListFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],type:"KernelNode",abstractKey:null};zn.hash="b07dcbdb178c221c667bd2f86f43cbd5";const Sn={PREPARING:"blue",BUILDING:"blue",PULLING:"blue",PREPARED:"blue",CREATING:"blue",PENDING:"green",SCHEDULED:"green",RUNNING:"green",RESTARTING:"green",RESIZING:"green",SUSPENDED:"green",TERMINATING:"default",TERMINATED:"default",CANCELLED:"default",ERROR:"red"},Na=({kernelsFrgmt:a,sessionFrgmtForLogModal:e})=>{const{t:l}=Ae(),[t,r]=j.useState(),d=P.useFragment(zn,a),s=hn([{title:l("kernel.Hostname"),dataIndex:"cluster_hostname",render:(u,m)=>n.jsxs(n.Fragment,{children:[n.jsx(B,{children:u}),n.jsx(we,{variant:"ghost",size:"sm",icon:n.jsx(ea,{}),label:l("session.SeeContainerLogs"),tooltip:l("session.SeeContainerLogs"),onClick:()=>{m.row_id&&r(m.row_id)}})]})},{title:l("kernel.Status"),dataIndex:"status",render:(u,m)=>n.jsx(n.Fragment,{children:(m==null?void 0:m.status_info)!==""?n.jsx(xn,{values:[{label:u,color:Xe(Sn,u)},{label:m==null?void 0:m.status_info,color:Xe(Sn,(m==null?void 0:m.status_info)??"")}]}):n.jsx(en,{variant:sl("kernel",u),label:u})})},{title:l("kernel.AgentId"),dataIndex:"agent_id",render:u=>ze(u)?"-":n.jsx(Ue,{copyable:!0,children:u})},{title:l("kernel.KernelId"),fixed:"left",dataIndex:"row_id",render:u=>ze(u)?"-":n.jsx(tn,{uuid:u})},{title:l("kernel.ContainerId"),dataIndex:"container_id",render:u=>ze(u)?"-":n.jsx(tn,{uuid:u})}]),o=j.useMemo(()=>na($e(d),["cluster_role","cluster_idx"]),[d]);return n.jsxs(n.Fragment,{children:[n.jsx(Fn,{scroll:{x:"max-content"},bordered:!0,rowKey:"id",columns:s,dataSource:o}),n.jsx(tl,{children:n.jsx(il,{open:!!t,sessionFrgmt:e||null,defaultKernelId:t,onCancel:()=>{r(void 0)}})})]})},Un=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"scope_id"},e={defaultValue:null,kind:"LocalArgument",name:"sessionId"},l=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"sessionId"},{kind:"Variable",name:"scope_id",variableName:"scope_id"}],concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[a,e],kind:"Fragment",metadata:null,name:"EditableSessionNameRefetchQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,a],kind:"Operation",name:"EditableSessionNameRefetchQuery",selections:l},params:{cacheID:"58d69307fe6e70d2c3409231b0279c8b",id:null,metadata:{},name:"EditableSessionNameRefetchQuery",operationKind:"query",text:`query EditableSessionNameRefetchQuery(
  $sessionId: GlobalIDField!
  $scope_id: ScopeField
) {
  compute_session_node(id: $sessionId, scope_id: $scope_id) {
    id
    name
  }
}
`}}})();Un.hash="387b0fe2d9acb6f455335434b59c3e6c";const On={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EditableSessionNameFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},action:"THROW"}],type:"ComputeSessionNode",abstractKey:null};On.hash="6dfb2b44bf25b8bfda2fce5ab4cedad8";const La=a=>{"use memo";const e=ue.c(28),{sessionFrgmt:l,level:t,editable:r,dimmed:d}=a,s=r===void 0?!1:r,o=d===void 0?!1:d,u=P.useRelayEnvironment();let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=On,e[0]=m):m=e[0];const c=P.useFragment(m,l),[S,y]=j.useState(c.name),F=rl(S),[f]=_n(),g=He();let h;e[1]!==g||e[2]!==c.row_id?(h={mutationFn:w=>g.rename(c.row_id,w)},e[1]=g,e[2]=c.row_id,e[3]=h):h=e[3];const k=ol(h),{t:p}=Ae(),{message:K}=gl.useApp(),[b,A]=j.useState(!1),[T,C]=j.useState(!1);let v;e[4]===Symbol.for("react.memo_cache_sentinel")?(v=["RESTARTING","PREPARING","PREPARED","CREATING","PULLING"],e[4]=v):v=e[4];const _=!v.includes(c.status||""),E=s&&f.uuid===c.user_id&&_,I=k.isPending||S!==c.name,M=k.isPending||S!==c.name?S:c.name,D=o||I;let V;e[5]!==T||e[6]!==M||e[7]!==D||e[8]!==b||e[9]!==E||e[10]!==I||e[11]!==t||e[12]!==p?(V=(!b||I)&&n.jsxs(kn,{gap:1,align:"center",children:[t?n.jsx(Ve,{level:t,color:D?"disabled":void 0,children:M}):n.jsx(B,{color:D?"disabled":void 0,children:M}),n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:T?n.jsx(dl,{"aria-hidden":!0}):n.jsx(ul,{"aria-hidden":!0}),label:p("sourceCodeViewer.Copy"),tooltip:p("sourceCodeViewer.Copy"),isDisabled:T,onClick:()=>{var w;(w=navigator.clipboard)==null||w.writeText(M??""),C(!0),setTimeout(()=>C(!1),1500)}}),E&&!I&&n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cl,{"aria-hidden":!0}),label:p("button.Edit"),tooltip:p("button.Edit"),onClick:()=>A(!0)})]}),e[5]=T,e[6]=M,e[7]=D,e[8]=b,e[9]=E,e[10]=I,e[11]=t,e[12]=p,e[13]=V):V=e[13];let R;e[14]!==b||e[15]!==I||e[16]!==K||e[17]!==u||e[18]!==k||e[19]!==c.id||e[20]!==c.name||e[21]!==c.project_id||e[22]!==p||e[23]!==F?(R=b&&!I&&n.jsx(rn,{onFinish:w=>{A(!1),y(w.sessionName),k.mutate(w.sessionName,{onSuccess:()=>{P.fetchQuery(u,Un,{sessionId:c.id,scope_id:`project:${c.project_id}`}).toPromise().catch()},onError:()=>{c.name!==w.sessionName&&K.error(p("session.FailToRenameSession"))}})},initialValues:{sessionName:c.name},style:{flex:1},children:n.jsx(rn.Item,{name:"sessionName",rules:F,children:n.jsx(ml,{label:p("session.SessionName"),size:"lg",hasAutoFocus:!0,onKeyDown:w=>{w.key==="Escape"&&(w.stopPropagation(),A(!1))}})})}),e[14]=b,e[15]=I,e[16]=K,e[17]=u,e[18]=k,e[19]=c.id,e[20]=c.name,e[21]=c.project_id,e[22]=p,e[23]=F,e[24]=R):R=e[24];let H;return e[25]!==V||e[26]!==R?(H=n.jsxs(n.Fragment,{children:[V,R]}),e[25]=V,e[26]=R,e[27]=H):H=e[27],H},Qn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionIdleChecksNodeFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionReclamationStatusCellFragment"}],type:"ComputeSessionNode",abstractKey:null};Qn.hash="cd0692b3021358f17c5abea99afd29d2";const Aa={warningText:{kMwMTN:"webuis3pv69",$$css:!0}};function va(a,e){var l;if(e==="remaining")return!a.remaining||a.remaining<3600?"red":a.remaining<3600*4?"orange":"green";if(a.extra&&(!a.remaining||a.remaining<3600*4))return(l=hl(a.extra.resources,a.extra.thresholds_check_operator))==null?void 0:l.color}const Ta=a=>{"use memo";const e=ue.c(24),{checkKey:l,value:t,sessionFrgmt:r}=a,{t:d}=Ae(),s=t.remaining??0;let o;e[0]!==d?(o=b=>d(b==="network_timeout"?"session.NetworkIdleTimeout":b==="session_lifetime"?"session.MaxSessionLifetime":"session.UtilizationIdleTimeout"),e[0]=d,e[1]=o):o=e[1];const u=o;let m;e[2]!==d?(m=b=>d(b==="expire_after"?"session.ExpiresAfter":"session.GracePeriod"),e[2]=d,e[3]=m):m=e[3];const c=m,S=l==="utilization"?"utilization":"remaining";let y;e[4]!==S||e[5]!==t?(y=va(t,S),e[4]=S,e[5]=t,e[6]=y):y=e[6];const F=y;let f;e[7]!==s?(f=ee().add(s,"second").toISOString(),e[7]=s,e[8]=f):f=e[8];const g=f;let h;e[9]===Symbol.for("react.memo_cache_sentinel")?(h={flex:1},e[9]=h):h=e[9];let k;e[10]!==l||e[11]!==u||e[12]!==r?(k=n.jsx(L,{gap:"xxs",children:l==="utilization"?n.jsx(pl,{sessionFrgmt:r}):n.jsx(B,{children:u(l)})}),e[10]=l,e[11]=u,e[12]=r,e[13]=k):k=e[13];let p;e[14]!==g||e[15]!==c||e[16]!==s||e[17]!==d||e[18]!==F||e[19]!==t.remaining_time_type?(p=s>=0?n.jsxs(L,{gap:"xxs",align:"center",children:[n.jsx(Sl,{delay:1e3,callback:()=>ee(g).diff()>0?yl(ee().toISOString(),g):"00:00:00",render:b=>n.jsx(xn,{values:[{label:c(t.remaining_time_type),color:F},{label:b,color:F}]})}),t.remaining_time_type==="grace_period"&&n.jsx(fl,{title:n.jsx("div",{style:{whiteSpace:"pre-line"},children:d("session.GracePeriodTooltip")})})]}):n.jsx(B,{xstyle:Aa.warningText,children:d("session.ReclamationStatusChecking")}),e[14]=g,e[15]=c,e[16]=s,e[17]=d,e[18]=F,e[19]=t.remaining_time_type,e[20]=p):p=e[20];let K;return e[21]!==k||e[22]!==p?(K=n.jsxs(L,{style:h,direction:"column",align:"stretch",children:[k,p]}),e[21]=k,e[22]=p,e[23]=K):K=e[23],K},Ea=({sessionNodeFrgmt:a=null,direction:e="row"})=>{const l=P.useFragment(Qn,a),t=jn(l==null?void 0:l.idle_checks,{fallbackValue:{}});return n.jsx(L,{direction:e,align:"stretch",gap:"sm",children:be(t,(r,d)=>r.remaining?n.jsx(Ta,{checkKey:d,value:r,sessionFrgmt:l},d):null)})},qn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionStatusDetailModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusTagFragment"}],type:"ComputeSessionNode",abstractKey:null};qn.hash="9fda416861ce96da9edb0c823baaa6b8";const yn={predicateMsg:{ks0D6T:"webui1dc814f",$$css:!0}},wa=({sessionFrgmt:a,...e})=>{var o,u,m,c,S,y,F,f;const{t:l}=Ae(),t=Kn(),r=He(),d=P.useFragment(qn,a),s=JSON.parse(d.status_data||"{}");return n.jsx(qe,{title:n.jsxs(n.Fragment,{children:[l("session.StatusInfo"),n.jsx("span",{style:{fontWeight:"normal"},children:n.jsx(In,{sessionFrgmt:d,showInfo:!0,showQueuePosition:!1})})]}),footer:null,width:450,...e,children:n.jsxs(Cn,{columns:"single",children:[n.jsx(N,{label:l("session.SessionName"),children:n.jsx(Ue,{copyable:!0,ellipsis:{tooltip:!0},children:d.name??""})}),s!=null&&s.kernel?n.jsx(N,{label:l("session.KernelExitCode"),children:s.kernel.exit_code}):null,s!=null&&s.session?n.jsx(N,{label:l("session.SessionStatus"),children:(o=s.session)==null?void 0:o.status}):null,s!=null&&s.scheduler?n.jsxs(n.Fragment,{children:[n.jsx(N,{label:l("session.LastTry"),children:ee((u=s.scheduler)==null?void 0:u.last_try).format("lll")}),n.jsx(N,{label:l("session.TotalRetries"),children:(m=s.scheduler)==null?void 0:m.retries}),((c=s.scheduler)==null?void 0:c.msg)&&n.jsx(N,{label:l("session.Message"),children:(S=s.scheduler)==null?void 0:S.msg}),n.jsx(N,{label:l("session.PredicateChecks"),children:n.jsxs(L,{direction:"column",gap:"md",align:"stretch",children:[be((y=s.scheduler)==null?void 0:y.failed_predicates,g=>n.jsxs(L,{gap:"xs",align:"start",children:[n.jsx(Fl,{style:{color:"var(--color-error)",marginTop:4,flexShrink:0},size:16}),n.jsxs(L,{direction:"column",align:"stretch",children:[n.jsx(B,{children:g.name}),n.jsx(B,{color:"secondary",xstyle:yn.predicateMsg,children:g.msg})]})]},g.name)),be((F=s.scheduler)==null?void 0:F.passed_predicates,g=>n.jsxs(L,{gap:"xs",align:"start",children:[n.jsx(kl,{style:{color:"var(--color-success)",marginTop:4,flexShrink:0},size:16}),n.jsxs(L,{direction:"column",align:"stretch",children:[n.jsx(B,{children:g.name}),n.jsx(B,{color:"secondary",xstyle:yn.predicateMsg,children:g.msg})]})]},g.name))]})})]}):null,s!=null&&s.error?be(((f=s==null?void 0:s.error)==null?void 0:f.collection)??s,g=>n.jsxs(j.Fragment,{children:[(t==="superadmin"||!r._config.hideAgents)&&(g==null?void 0:g.agent_id)&&n.jsx(N,{label:l("session.AgentId"),children:g==null?void 0:g.agent_id}),n.jsx(N,{label:l("dialog.error.Error"),children:n.jsx(en,{variant:"error",label:g.name})}),n.jsx(N,{label:l("session.Message"),children:g.repr}),(g==null?void 0:g.traceback)&&n.jsx(N,{label:l("session.Traceback"),children:n.jsx("pre",{children:g==null?void 0:g.traceback})})]},g.name)):null]})})},Ma=({...a})=>{const{t:e}=Ae(),{token:l}=bl.useToken();return n.jsxs(qe,{title:e("session.ReclamationStatus"),footer:null,width:700,...a,children:[n.jsx(B,{children:e("session.IdleChecksDesc")}),n.jsx(Ve,{level:5,children:e("session.MaxSessionLifetime")}),n.jsx("p",{children:e("session.MaxSessionLifetimeDesc")}),n.jsx(Ve,{level:5,children:e("session.NetworkIdleTimeout")}),n.jsx("p",{children:e("session.NetworkIdleTimeoutDesc")}),n.jsx(Ve,{level:5,children:e("session.UtilizationIdleTimeout")}),n.jsx("p",{children:e("session.UtilizationIdleTimeoutDesc")}),n.jsxs(L,{direction:"column",align:"stretch",style:{marginLeft:l.marginMD},children:[n.jsx(Ve,{level:5,style:{margin:0},children:e("session.GracePeriod")}),n.jsx("p",{children:e("session.GracePeriodDesc")}),n.jsx(Ve,{level:5,style:{margin:0},children:e("session.UtilizationThreshold")}),n.jsx("p",{children:e("session.UtilizationThresholdDesc")})]})]})},Gn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"mounts",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"MountedVFolderLinksQuery",selections:[{alias:"legacy_session",args:e,concreteType:"ComputeSession",kind:"LinkedField",name:"compute_session",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"MountedVFolderLinksQuery",selections:[{alias:"legacy_session",args:e,concreteType:"ComputeSession",kind:"LinkedField",name:"compute_session",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"9025af1e54e75a0d3041d0e12150939c",id:null,metadata:{},name:"MountedVFolderLinksQuery",operationKind:"query",text:`query MountedVFolderLinksQuery(
  $uuid: UUID!
) {
  legacy_session: compute_session(id: $uuid) {
    mounts
    id
  }
}
`}}})();Gn.hash="f1e2ef43ac11c6b980313ddac8cd1ec9";const Wn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksLegacyLazyFolderLinkFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null}],type:"ComputeSessionNode",abstractKey:null};Wn.hash="72fda7ec47bcaa5e7fc83cbaabc822c6";const Jn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksLegacyLazyFolderLinkFragment"}],type:"ComputeSessionNode",abstractKey:null};Jn.hash="f26bc04640693f4094c9a072011821b0";const Da=({sessionFrgmt:a})=>{var t;const e=He(),l=P.useFragment(Jn,a);return e.supports("vfolder_nodes_in_session_node")?be((t=l.vfolder_nodes)==null?void 0:t.edges,(r,d)=>(r==null?void 0:r.node)&&n.jsx(Tn,{vfolderNodeFragment:r.node},`mounted-vfolder-${d}`)):l.row_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ra,{sessionFrgmt:l})}):null},Ra=({sessionFrgmt:a})=>{var r;const e=He(),l=P.useFragment(Wn,a),{legacy_session:t}=P.useLazyLoadQuery(Gn,{uuid:l.row_id||""},{fetchPolicy:l.row_id?"store-and-network":"store-only"});return e.supports("vfolder-mounts")?be(la(t==null?void 0:t.mounts,l==null?void 0:l.vfolder_mounts),d=>{const[s,o]=d;return n.jsx(Tn,{folderId:o??"",folderName:s??"",showIcon:!0},o)}):(r=t==null?void 0:t.mounts)==null?void 0:r.join(", ")},Xn=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r={defaultValue:null,kind:"LocalArgument",name:"scope"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[a,e,l,t,r],kind:"Fragment",metadata:null,name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[s,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,a,t,e,l],kind:"Operation",name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[s,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},o,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"1bfe7bc2611f279e70c35d22c11fb631",id:null,metadata:{},name:"SessionSchedulingHistoryModalQuery",operationKind:"query",text:`query SessionSchedulingHistoryModalQuery(
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
`}}})();Xn.hash="6221439d9cf111e4683277c5e89974db";const Ba=a=>{"use memo";var x,U,Ke,Ee;const e=ue.c(116);let l,t,r,d,s;e[0]!==a?({open:d,loading:l,sessionId:s,onCancel:r,...t}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d,e[5]=s):(l=e[1],t=e[2],r=e[3],d=e[4],s=e[5]);const{t:o}=Ae(),[u,m]=Nn(),[c,S]=j.useState(),[y,F]=j.useState("-updatedAt"),[f,g]=on("schedulingHistoryExpandMode"),[h,k]=on("table_column_overrides.SessionSchedulingHistory");let p;e[6]===Symbol.for("react.memo_cache_sentinel")?(p={current:1,pageSize:10},e[6]=p):p=e[6];const{baiPaginationOption:K,tablePaginationOption:b,setTablePaginationOption:A}=Ln(p),T=j.useDeferredValue(d),C=j.useDeferredValue(u),v=j.useDeferredValue(c),_=j.useDeferredValue(y),E=j.useDeferredValue(K.offset),I=j.useDeferredValue(K.limit);let M;e[7]===Symbol.for("react.memo_cache_sentinel")?(M=Xn,e[7]=M):M=e[7];let D;e[8]!==s?(D={sessionId:s},e[8]=s,e[9]=D):D=e[9];const V=v??void 0;let R;e[10]!==_?(R=xl(_)??[{field:"UPDATED_AT",direction:"DESC"}],e[10]=_,e[11]=R):R=e[11];let H;e[12]!==I||e[13]!==E||e[14]!==D||e[15]!==V||e[16]!==R?(H={scope:D,filter:V,orderBy:R,limit:I,offset:E},e[12]=I,e[13]=E,e[14]=D,e[15]=V,e[16]=R,e[17]=H):H=e[17];const w=T?"network-only":"store-only";let xe;e[18]!==C||e[19]!==w?(xe={fetchKey:C,fetchPolicy:w},e[18]=C,e[19]=w,e[20]=xe):xe=e[20];const ce=P.useLazyLoadQuery(M,H,xe);let z;e[21]!==o?(z=o("session.SessionSchedulingHistory"),e[21]=o,e[22]=z):z=e[22];const _e=l||T!==d;let ne;e[23]!==A?(ne=Ce=>{S(Ce),A({current:1})},e[23]=A,e[24]=ne):ne=e[24];let O;e[25]!==o?(O=o("session.ID"),e[25]=o,e[26]=O):O=e[26];let je;e[27]!==O?(je={key:"id",propertyLabel:O,type:"uuid",fixedOperator:"equals"},e[27]=O,e[28]=je):je=e[28];let Q;e[29]!==o?(Q=o("session.Phase"),e[29]=o,e[30]=Q):Q=e[30];let i;e[31]!==Q?(i={key:"phase",propertyLabel:Q,type:"string",fixedOperator:"contains"},e[31]=Q,e[32]=i):i=e[32];let q;e[33]!==o?(q=o("session.Result"),e[33]=o,e[34]=q):q=e[34];let le;e[35]===Symbol.for("react.memo_cache_sentinel")?(le=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[35]=le):le=e[35];let ae;e[36]!==q?(ae={key:"result",propertyLabel:q,type:"enum",strictSelection:!0,options:le},e[36]=q,e[37]=ae):ae=e[37];let se;e[38]!==o?(se=o("session.FromStatus"),e[38]=o,e[39]=se):se=e[39];let te;e[40]!==se?(te={key:"fromStatus",propertyLabel:se,type:"string",valueMode:"scalar"},e[40]=se,e[41]=te):te=e[41];let G;e[42]!==o?(G=o("session.ToStatus"),e[42]=o,e[43]=G):G=e[43];let W;e[44]!==G?(W={key:"toStatus",propertyLabel:G,type:"string",valueMode:"scalar"},e[44]=G,e[45]=W):W=e[45];let ie;e[46]!==o?(ie=o("session.ErrorCode"),e[46]=o,e[47]=ie):ie=e[47];let re;e[48]!==ie?(re={key:"errorCode",propertyLabel:ie,type:"string",fixedOperator:"contains"},e[48]=ie,e[49]=re):re=e[49];let J;e[50]!==o?(J=o("session.Message"),e[50]=o,e[51]=J):J=e[51];let oe;e[52]!==J?(oe={key:"message",propertyLabel:J,type:"string",fixedOperator:"contains"},e[52]=J,e[53]=oe):oe=e[53];let X;e[54]!==o?(X=o("session.CreatedAt"),e[54]=o,e[55]=X):X=e[55];let $;e[56]!==X?($={key:"createdAt",propertyLabel:X,type:"datetime",defaultOperator:"after"},e[56]=X,e[57]=$):$=e[57];let Y;e[58]!==o?(Y=o("session.UpdatedAt"),e[58]=o,e[59]=Y):Y=e[59];let ve;e[60]!==Y?(ve={key:"updatedAt",propertyLabel:Y,type:"datetime",defaultOperator:"after"},e[60]=Y,e[61]=ve):ve=e[61];let de;e[62]!==je||e[63]!==i||e[64]!==ae||e[65]!==te||e[66]!==W||e[67]!==re||e[68]!==oe||e[69]!==$||e[70]!==ve?(de=[je,i,ae,te,W,re,oe,$,ve],e[62]=je,e[63]=i,e[64]=ae,e[65]=te,e[66]=W,e[67]=re,e[68]=oe,e[69]=$,e[70]=ve,e[71]=de):de=e[71];let Z;e[72]!==c||e[73]!==ne||e[74]!==de?(Z=n.jsx(ta,{value:c,onChange:ne,filterProperties:de}),e[72]=c,e[73]=ne,e[74]=de,e[75]=Z):Z=e[75];const Me=C!==u;let me;e[76]!==u||e[77]!==Me||e[78]!==m?(me=n.jsx(L,{children:n.jsx(_l,{value:u,onChange:m,loading:Me,autoUpdateDelay:null})}),e[76]=u,e[77]=Me,e[78]=m,e[79]=me):me=e[79];let ge;e[80]!==Z||e[81]!==me?(ge=n.jsxs(L,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,me]}),e[80]=Z,e[81]=me,e[82]=ge):ge=e[82];const De=C!==u||v!==c||_!==y||E!==K.offset||I!==K.limit;let pe;e[83]!==A?(pe=Ce=>{F(Ce),A({current:1})},e[83]=A,e[84]=pe):pe=e[84];const Re=f??void 0;let Se;e[85]!==h||e[86]!==k?(Se={columnOverrides:h,onColumnOverridesChange:k},e[85]=h,e[86]=k,e[87]=Se):Se=e[87];const Be=((x=ce.sessionScopedSchedulingHistories)==null?void 0:x.count)??0;let ye;e[88]!==A?(ye=(Ce,Ie)=>{A({current:Ce,pageSize:Ie})},e[88]=A,e[89]=ye):ye=e[89];let fe;e[90]!==Be||e[91]!==ye||e[92]!==b.current||e[93]!==b.pageSize?(fe={pageSize:b.pageSize,current:b.current,total:Be,onChange:ye},e[90]=Be,e[91]=ye,e[92]=b.current,e[93]=b.pageSize,e[94]=fe):fe=e[94];let he;e[95]!==((U=ce.sessionScopedSchedulingHistories)==null?void 0:U.edges)?(he=be((Ke=ce.sessionScopedSchedulingHistories)==null?void 0:Ke.edges,"node"),e[95]=(Ee=ce.sessionScopedSchedulingHistories)==null?void 0:Ee.edges,e[96]=he):he=e[96];let Fe;e[97]!==y||e[98]!==g||e[99]!==De||e[100]!==pe||e[101]!==Re||e[102]!==Se||e[103]!==fe||e[104]!==he?(Fe=n.jsx(ja,{resizable:!0,loading:De,order:y,onChangeOrder:pe,expandMode:Re,onExpandModeChange:g,tableSettings:Se,pagination:fe,schedulingHistoryFrgmt:he}),e[97]=y,e[98]=g,e[99]=De,e[100]=pe,e[101]=Re,e[102]=Se,e[103]=fe,e[104]=he,e[105]=Fe):Fe=e[105];let ke;e[106]!==ge||e[107]!==Fe?(ke=n.jsxs(L,{direction:"column",align:"stretch",gap:"sm",children:[ge,Fe]}),e[106]=ge,e[107]=Fe,e[108]=ke):ke=e[108];let Te;return e[109]!==t||e[110]!==r||e[111]!==d||e[112]!==_e||e[113]!==ke||e[114]!==z?(Te=n.jsx(qe,{title:z,loading:_e,open:d,variant:"fullscreen",footer:null,onCancel:r,...t,children:ke}),e[109]=t,e[110]=r,e[111]=d,e[112]=_e,e[113]=ke,e[114]=z,e[115]=Te):Te=e[115],Te},fn=(a,e)=>{const l=JSON.parse(a||"{}"),t=vn(e);return t?{...Qe(l,t),acceleratorType:t}:l},Je=a=>Gl(Wl(JSON.parse(a||"{}"),e=>Jl(e)),e=>e===0),Pa=a=>{"use memo";var Me,me,ge,De,pe,Re,Se,Be,ye,fe,he,Fe,ke,Te;const e=ue.c(60),{id:l,fetchKey:t,sessionFrgmt:r,project:d}=a,{t:s}=Ae(),{md:o}=jl(),{mergedResourceSlots:u}=Kl(),m=An(),[c]=_n(),S=Kn(),y=He();let F;e[0]!==y?(F=y.supports("session-scheduling-history"),e[0]=y,e[1]=F):F=e[1];const f=F,[g,h]=j.useState(!1),[k,p]=j.useState(!1),K="current",[b,A]=j.useState("kernels"),[T,C]=dn(!1),{toggle:v}=C,[_,E]=dn(!1),{toggle:I}=E,[M,D]=P.useQueryLoader(aa);let V;e[2]===Symbol.for("react.memo_cache_sentinel")?(V={current:1,pageSize:10},e[2]=V):V=e[2];const{baiPaginationOption:R,setTablePaginationOption:H}=Ln(V);let w;e[3]!==D||e[4]!==H?(w=(x,U)=>{const Ke=x.limit??10;H({pageSize:Ke,current:x.offset?Math.floor(x.offset/Ke)+1:1}),D(x,U)},e[3]=D,e[4]=H,e[5]=w):w=e[5];const xe=w;let ce;e[6]===Symbol.for("react.memo_cache_sentinel")?(ce=Hn,e[6]=ce):ce=e[6];let z;e[7]!==l?(z=bn("ComputeSessionNode",l),e[7]=l,e[8]=z):z=e[8];let _e;e[9]!==z?(_e={id:z},e[9]=z,e[10]=_e):_e=e[10];const ne=t===ql?r?"store-only":"store-and-network":"network-only";let O;e[11]!==t||e[12]!==ne?(O={fetchPolicy:ne,fetchKey:t},e[11]=t,e[12]=ne,e[13]=O):O=e[13];const{internalLoadedSession:je}=P.useLazyLoadQuery(ce,_e,O);let Q;e[14]===Symbol.for("react.memo_cache_sentinel")?(Q=$n,e[14]=Q):Q=e[14];const i=P.useFragment(Q,je||r);let q;e[15]===Symbol.for("react.memo_cache_sentinel")?(q={fallbackValue:{}},e[15]=q):q=e[15];const le=Cl(Il(jn(i==null?void 0:i.idle_checks,q)).map(Va).filter(Boolean)),ae=i==null?void 0:i.project_id,se=i==null?void 0:i.requested_slots,te=i==null?void 0:i.tag;let G;e[16]!==se||e[17]!==te?(G=fn(se,te),e[16]=se,e[17]=te,e[18]=G):G=e[18];const W=G,ie=i==null?void 0:i.occupied_slots,re=i==null?void 0:i.tag;let J;e[19]!==ie||e[20]!==re?(J=fn(ie,re),e[19]=ie,e[20]=re,e[21]=J):J=e[21];const oe=J;let X;e[22]!==(i==null?void 0:i.occupied_slots)?(X=ze(Je(i==null?void 0:i.occupied_slots)),e[22]=i==null?void 0:i.occupied_slots,e[23]=X):X=e[23];const $=!X;let Y;if(e[24]!==$||e[25]!==u||e[26]!==(i==null?void 0:i.occupied_slots)||e[27]!==(i==null?void 0:i.requested_slots)||e[28]!==(i==null?void 0:i.tag)){const x=vn(i==null?void 0:i.tag)??"",U=Qe(Je(i==null?void 0:i.requested_slots),x),Ke=Qe(Je(i==null?void 0:i.occupied_slots),x);let Ee;e[30]!==u?(Ee=(Ie,Ge)=>{var ln,an;const Pe=(ln=u==null?void 0:u[Ie])==null?void 0:ln.number_format,nn=(Pe==null?void 0:Pe.round_length)||0;return Pe!=null&&Pe.binary?Number((an=Xl(Ge.toString(),"g",2,!0))==null?void 0:an.numberFixed):nn>0?Number(Ge.toFixed(nn)):Ge},e[30]=u,e[31]=Ee):Ee=e[31];const Ce=Ee;Y=$?Nl(un(U),un(Ke)).filter(Ie=>Ce(Ie,Ke[Ie]??0)<Ce(Ie,U[Ie]??0)):[],e[24]=$,e[25]=u,e[26]=i==null?void 0:i.occupied_slots,e[27]=i==null?void 0:i.requested_slots,e[28]=i==null?void 0:i.tag,e[29]=Y}else Y=e[29];const de=Y.length>0;let Z;return e[32]!==b||e[33]!==M||e[34]!==y||e[35]!==R||e[36]!==c||e[37]!==$||e[38]!==de||e[39]!==l||e[40]!==le||e[41]!==D||e[42]!==m||e[43]!==o||e[44]!==oe||e[45]!==T||e[46]!==g||e[47]!==_||e[48]!==k||e[49]!==d||e[50]!==xe||e[51]!==W||e[52]!==ae||e[53]!==i||e[54]!==f||e[55]!==s||e[56]!==v||e[57]!==I||e[58]!==S?(Z=i?n.jsxs(L,{direction:"column",gap:"lg",align:"stretch",children:[d!==null&&ae!==d.id&&n.jsx(Oe,{status:"warning",title:s("session.NotInProject")}),c.uuid!==(i==null?void 0:i.user_id)&&n.jsx(Oe,{status:"warning",title:s("session.AnotherUserSession")}),le&&le<3600&&n.jsx(Oe,{status:"warning",title:s("session.IdleCheckExpirationWarning")}),n.jsxs(L,{direction:"column",gap:"sm",align:"stretch",children:[n.jsxs(L,{direction:"row",justify:"between",align:"start",style:{alignSelf:"stretch"},gap:"sm",children:[n.jsx(La,{sessionFrgmt:i,level:3,dimmed:["TERMINATED","CANCELLED"].includes(i.status||""),editable:!["TERMINATED","CANCELLED"].includes(i.status||"")}),n.jsx(Ll,{size:"large",compact:!0,sessionFrgmt:i})]}),n.jsx(Al,{children:n.jsxs(Cn,{columns:o?2:1,children:[n.jsx(N,{label:s("session.SessionId"),children:n.jsx(Ue,{code:!0,copyable:!0,ellipsis:{tooltip:!0},children:i.row_id??""})}),(S==="admin"||S==="superadmin")&&n.jsx(N,{label:s("credential.UserID"),children:(Me=i.owner)!=null&&Me.email?i.owner.email:i.user_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ca,{uuid:i.user_id})}):"-"}),n.jsx(N,{label:s("general.AccessKey"),children:n.jsx(vl,{sessionFrgmt:i,copyable:!0})}),n.jsx(N,{label:s("session.Status"),children:n.jsxs(L,{children:[n.jsx(In,{sessionFrgmt:i,showInfo:!f}),!f&&(i!=null&&i.status_data)&&(i==null?void 0:i.status_data)!=="{}"?n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cn,{size:"1em"}),label:s("button.ClickForMoreDetails"),tooltip:s("button.ClickForMoreDetails"),onClick:()=>{p(!0)}}):null,f&&n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(ia,{size:"1em"}),label:s("session.SessionSchedulingHistory"),tooltip:s("session.SessionSchedulingHistory"),onClick:()=>I()})]})}),n.jsx(N,{label:s("session.SessionType"),children:n.jsxs(L,{children:[n.jsx(Tl,{sessionFrgmt:i}),i.type==="batch"&&i.startup_command&&n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cn,{size:"1em"}),label:s("session.ViewStartupCommand"),tooltip:s("session.ViewStartupCommand"),onClick:()=>v()})]})}),n.jsx(N,{label:s("session.launcher.Environments"),children:(De=(ge=(me=i.kernel_nodes)==null?void 0:me.edges[0])==null?void 0:ge.node)!=null&&De.image?n.jsx(El,{imageFrgmt:((Se=(Re=(pe=i.kernel_nodes)==null?void 0:pe.edges[0])==null?void 0:Re.node)==null?void 0:Se.image)||null}):i.row_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(wl,{sessionId:i.row_id})}):null}),n.jsx(N,{label:s("session.launcher.MountedFolders"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:n.jsx(Da,{sessionFrgmt:i})})}),n.jsx(N,{label:s("session.launcher.ResourceAllocation"),children:n.jsxs(L,{gap:"sm",wrap:"wrap",align:"center",children:[de&&n.jsx(Ml,{content:s("session.AllocatedLessThanRequested"),icon:n.jsx(Dl,{size:"1em",style:{color:"var(--color-warning)"}})}),n.jsx(Rl,{content:s("session.ResourceGroup"),children:n.jsx(en,{label:i.scaling_group})}),n.jsx(Bl,{resource:$?oe:W,comparedResource:$?W:void 0,showDividers:!0})]})}),n.jsx(N,{label:s("session.Agent"),children:n.jsx(Pl,{sessionFrgmt:i})}),n.jsx(N,{label:s("session.Reservation"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:n.jsx(Vl,{sessionFrgmt:i})})}),n.jsx(N,{label:s("session.ClusterMode"),children:n.jsx($l,{sessionFrgmt:i,showSize:!0})}),y.supports("idle-checks-gql")&&i.status==="RUNNING"&&le?n.jsx(N,{label:s("session.ReclamationStatus"),children:n.jsxs(L,{gap:"xxs",align:"start",children:[n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ea,{sessionNodeFrgmt:i,direction:o?"row":"column"})}),n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(Hl,{size:"1em"}),label:s("button.ClickForMoreDetails"),tooltip:s("button.ClickForMoreDetails"),onClick:()=>h(!0)})]})}):null,n.jsx(N,{label:s("session.ResourceUsage"),children:n.jsx(zl,{sessionFrgmt:i,displayTarget:K})}),(((Be=i.dependees)==null?void 0:Be.count)??0)>0&&n.jsx(N,{label:s("session.DependsOn"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:(fe=(ye=i.dependees)==null?void 0:ye.edges)==null?void 0:fe.map($a).filter(Boolean).map(x=>{const U=new URLSearchParams(m.search);return x!=null&&x.row_id&&U.set("sessionDetail",x.row_id),n.jsx(mn,{type:"hover",to:{pathname:m.pathname,search:U.toString()},children:x==null?void 0:x.name},x==null?void 0:x.row_id)})})}),(((he=i.dependents)==null?void 0:he.count)??0)>0&&n.jsx(N,{label:s("session.DependedByOthers"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:(ke=(Fe=i.dependents)==null?void 0:Fe.edges)==null?void 0:ke.map(Ha).filter(Boolean).map(x=>{const U=new URLSearchParams(m.search);return x!=null&&x.row_id&&U.set("sessionDetail",x.row_id),n.jsx(mn,{type:"hover",to:{pathname:m.pathname,search:U.toString()},children:x==null?void 0:x.name},x==null?void 0:x.row_id)})})})]})})]}),n.jsxs(L,{direction:"column",align:"stretch",gap:"sm",children:[n.jsxs(Ul,{hasDivider:!0,value:b,onChange:x=>{x==="auditLog"&&i.row_id&&!M&&D({scope:{entity:[{entityType:"SESSION",entityId:i.row_id}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:R.limit,offset:R.offset},{fetchPolicy:"store-and-network"}),A(x)},children:[n.jsx(gn,{value:"kernels",label:s("kernel.Kernels")}),i.row_id?n.jsx(gn,{value:"auditLog",label:s("auditLog.AuditLog")}):null]}),b==="kernels"&&n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:n.jsx(Na,{kernelsFrgmt:$e((Te=i.kernel_nodes)==null?void 0:Te.edges.map(za)),sessionFrgmtForLogModal:i})}),b==="auditLog"&&i.row_id&&n.jsx(Ol,{children:M?n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:n.jsx(sa,{queryRef:M,onReload:xe,tableSettings:{}})}):n.jsx(Le,{})})]}),n.jsx(Ma,{open:g,onCancel:()=>h(!1)}),n.jsx(Ia,{open:T,language:"shell",content:i.startup_command||"",title:s("session.StartupCommand"),footer:n.jsx(Ql,{variant:"primary",label:s("button.Close"),onClick:()=>{v()}}),onCancel:v}),n.jsx(Ba,{sessionId:l,open:_,onCancel:I}),n.jsx(wa,{sessionFrgmt:i,open:k,onCancel:()=>p(!1)})]}):n.jsx(Oe,{status:"error",title:s("session.SessionNotFound"),description:l}),e[32]=b,e[33]=M,e[34]=y,e[35]=R,e[36]=c,e[37]=$,e[38]=de,e[39]=l,e[40]=le,e[41]=D,e[42]=m,e[43]=o,e[44]=oe,e[45]=T,e[46]=g,e[47]=_,e[48]=k,e[49]=d,e[50]=xe,e[51]=W,e[52]=ae,e[53]=i,e[54]=f,e[55]=s,e[56]=v,e[57]=I,e[58]=S,e[59]=Z):Z=e[59],Z};function Va(a){return a.remaining}function $a(a){return a==null?void 0:a.node}function Ha(a){return a==null?void 0:a.node}function za(a){return a==null?void 0:a.node}const Ya=({sessionId:a,open:e=!1,onClose:l,project:t})=>{const{t:r}=Ae();He();const[d,s]=j.useTransition(),[o,u]=Nn(),m=An(),{sessionDetailDrawerFrgmt:c,createdAt:S}=m.state||{},y=P.useFragment(Vn,c),F=j.useMemo(()=>S&&ee().diff(ee(S),"second")<60?y:null,[]);return n.jsx(Yl,{open:e,onClose:l,side:"end",size:800,title:r("session.SessionInfo"),extra:n.jsx(Zl,{settingId:"session-detail",defaultAutoUpdateDelay:1e4,loading:d,value:o,onChange:f=>{s(()=>{u(f)})}}),children:n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:a&&n.jsx(Pa,{id:a,fetchKey:o,sessionFrgmt:F,project:t})})})};export{oa as B,Ya as S,_a as a,Bn as c,ra as n,fa as u};
//# sourceMappingURL=SessionDetailDrawer-_Qk8OrZd.js.map
