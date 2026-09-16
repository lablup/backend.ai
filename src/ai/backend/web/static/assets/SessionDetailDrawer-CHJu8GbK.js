import{h as Zn,g0 as el,dq as sn,al as be,dW as nl,j as n,i as ue,bT as Ye,g1 as ll,aA as Ze,r as P,ah as kn,aS as $e,aY as Fn,t as ee,s as Ue,aj as al,aq as Qe,l as j,d4 as bn,a0 as sl,ej as tl,am as ze,fb as tn,a2 as B,V as xn,a8 as qe,g2 as il,u as Ae,K as we,f as _n,g as en,aQ as rl,ao as ol,g3 as dl,g4 as ul,cB as jn,a as He,cI as cl,bp as Ve,C as ml,g5 as gl,aG as pl,F as rn,E as Sl,X as yl,g6 as Kn,c as L,g7 as fl,dX as hl,g8 as kl,B as Fl,g9 as bl,a_ as Cn,e as Nn,M as I,ga as In,dD as xl,dC as _l,ab as jl,aU as Le,aN as Ln,a7 as on,aW as An,aR as Kl,aO as Cl,e1 as Nl,bk as Il,ac as vn,bD as dn,f$ as Ll,f5 as Al,gb as Tn,dm as vl,cg as un,v as Oe,gc as Tl,d as El,gd as wl,d5 as cn,ge as Ml,gf as Dl,gg as Rl,cD as Bl,T as Pl,q as Vl,gh as $l,gi as Hl,gj as zl,et as Ul,d2 as Ol,gk as Ql,dM as mn,dK as ql,dJ as gn,co as Gl,at as Wl,bg as Xl,bA as Yl,bU as Jl,b_ as Zl,cf as ea,dL as na,cz as la}from"./index-DPebpL40.js";import{B as pn}from"./BAIId-oHD2WVBQ.js";import{F as En}from"./FolderLink-rZTSRFdj.js";import{z as aa}from"./zip-dqg4xnl6.js";import{S as sa,a as ta}from"./ScopedAuditLog-Dwul8NSy.js";import{B as ia}from"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import{R as ra}from"./rotate-ccw-clock-CpAeUoLy.js";/**
 * @license lucide-react v1.37.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const oa=[["path",{d:"M15 12h-5",key:"r7krc0"}],["path",{d:"M15 8h-5",key:"1khuty"}],["path",{d:"M19 17V5a2 2 0 0 0-2-2H4",key:"zz82l3"}],["path",{d:"M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3",key:"1ph1d7"}]],da=Zn("scroll-text",oa);function ua(a,e,l,s){return a==null?[]:(sn(e)||(e=e==null?[]:[e]),l=l,sn(l)||(l=l==null?[]:[l]),el(a,e,l))}const ca=(a,e=/(<br\s*\/?>|\n)/)=>be(nl(a,e),(l,s)=>l.match(e)?n.jsx("br",{},s):l),wn={SUCCESS:"success",FAILURE:"error",STALE:"default",NEED_RETRY:"warning",EXPIRED:"error",GIVE_UP:"error",SKIPPED:"default"},ma=a=>{"use memo";const e=ue.c(12);let l,s;e[0]!==a?({result:s,...l}=a,e[0]=a,e[1]=l,e[2]=s):(l=e[1],s=e[2]);let r;e[3]!==s?(r=s?Ye(wn,s):void 0,e[3]=s,e[4]=r):r=e[4];const d=r;let t;e[5]!==l.style?(t={whiteSpace:"nowrap",...l.style},e[5]=l.style,e[6]=t):t=e[6];let o;return e[7]!==l||e[8]!==s||e[9]!==d||e[10]!==t?(o=n.jsx(ll,{...l,color:d,text:s,style:t}),e[7]=l,e[8]=s,e[9]=d,e[10]=t,e[11]=o):o=e[11],o},Mn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null}],type:"SessionSchedulingHistory",abstractKey:null};Mn.hash="a52af4f53e01beb70d74f67b151aa5e0";const Je=[];[...Je,...Je.map(a=>`-${a}`)];const Ie=a=>al(Je,a),ga=a=>{"use memo";const e=ue.c(23);let l,s,r,d,t;e[0]!==a?({schedulingHistoryFrgmt:d,disableSorter:s,customizeColumns:l,onChangeOrder:r,...t}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d,e[5]=t):(l=e[1],s=e[2],r=e[3],d=e[4],t=e[5]);const{t:o}=Ze();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=Mn,e[6]=u):u=e[6];const m=P.useFragment(u,d);let c;if(e[7]!==l||e[8]!==s||e[9]!==o){let h;e[11]!==s?(h=p=>s?Qe(p,"sorter"):p,e[11]=s,e[12]=h):h=e[12];const F=be(kn([{dataIndex:"updatedAt",title:o("comp:BAISchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:pa,sorter:Ie("updated_at")},{dataIndex:"createdAt",title:o("comp:BAISchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:Sa,sorter:Ie("created_at")},{dataIndex:"phase",title:o("comp:BAISchedulingHistoryNodes.Phase"),key:"phase",sorter:Ie("phase")},{dataIndex:"result",title:o("comp:BAISchedulingHistoryNodes.Result"),key:"result",render:ya,sorter:Ie("result")},{key:"fromStatus",title:o("comp:BAISchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Ie("from_status")},{key:"toStatus",title:o("comp:BAISchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Ie("to_status")},{dataIndex:"attempts",title:o("comp:BAISchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Ie("attempts")},{key:"message",title:o("comp:BAISchedulingHistoryNodes.Message"),dataIndex:"message",onCell:fa,render:ha,sorter:Ie("message")}]),h);c=l?l(F):F,e[7]=l,e[8]=s,e[9]=o,e[10]=c}else c=e[10];const S=c;let y;e[13]===Symbol.for("react.memo_cache_sentinel")?(y={x:"max-content"},e[13]=y):y=e[13];let k;e[14]!==m?(k=$e(m),e[14]=m,e[15]=k):k=e[15];let f;e[16]!==r?(f=h=>{r==null||r(h||null)},e[16]=r,e[17]=f):f=e[17];let g;return e[18]!==S||e[19]!==k||e[20]!==f||e[21]!==t?(g=n.jsx(Fn,{scroll:y,rowKey:"id",dataSource:k,columns:S,onChangeOrder:f,...t}),e[18]=S,e[19]=k,e[20]=f,e[21]=t,e[22]=g):g=e[22],g};function pa(a){return n.jsx("span",{children:ee(a).format("ll LTS")})}function Sa(a){return n.jsx("span",{children:ee(a).format("ll LTS")})}function ya(a,e){const l=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(ma,{result:l})}function fa(){return{style:{maxWidth:500}}}function ha(a,e){return e.message?n.jsx(Ue,{title:e.message,style:{width:"100%"},children:ca(e.message)}):"-"}const Dn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryNodesFragment"}],type:"SessionSchedulingHistory",abstractKey:null};Dn.hash="e369227c362b363c91d9f366ac98634d";const ka="errors-only",Fa=a=>!ze(a.subSteps),We=(a,e,l)=>e==="expand-all"?a.filter(l).map(s=>s.id):e==="collapse-all"?[]:a.filter(s=>l(s)&&s.result!=="SUCCESS").map(s=>s.id),ba=(a,e)=>{"use memo";const l=ue.c(28),{t:s}=Ze(),r=(e==null?void 0:e.mode)??ka;let d;l[0]!==e?(d=_=>e!=null&&e.isExpandable?e.isExpandable(_):Fa(_),l[0]=e,l[1]=d):d=l[1];const t=d;let o;l[2]!==a||l[3]!==t||l[4]!==r?(o=()=>We(a,r,t),l[2]=a,l[3]=t,l[4]=r,l[5]=o):o=l[5];const[u,m]=j.useState(o);let c;if(l[6]!==a||l[7]!==t){let _;l[9]!==t?(_=E=>`${E.id}:${E.result??""}:${t(E)?1:0}`,l[9]=t,l[10]=_):_=l[10],c=a.map(_).join("|"),l[6]=a,l[7]=t,l[8]=c}else c=l[8];const S=c,[y,k]=j.useState(S),[f,g]=j.useState(r);(S!==y||r!==f)&&(k(S),g(r),m(We(a,r,t)));let h;l[11]!==a||l[12]!==t?(h=a.filter(t).map(xa),l[11]=a,l[12]=t,l[13]=h):h=l[13];const F=h;let p;l[14]===Symbol.for("react.memo_cache_sentinel")?(p=_=>{m([..._])},l[14]=p):p=l[14];const K=p;let b;if(l[15]!==a||l[16]!==t||l[17]!==e||l[18]!==s){const _={"expand-all":s("comp:BAITable.ExpandAll"),"collapse-all":s("comp:BAITable.CollapseAll"),"errors-only":s("comp:BAITable.ExpandErrorsOnly")},E=N=>{var M;m(We(a,N,t)),(M=e==null?void 0:e.onModeChange)==null||M.call(e,N)};b=["expand-all","collapse-all","errors-only"].map(N=>({label:_[N],onClick:()=>E(N)})),l[15]=a,l[16]=t,l[17]=e,l[18]=s,l[19]=b}else b=l[19];const A=b;let T;l[20]!==F.length||l[21]!==A||l[22]!==s?(T=F.length>0?n.jsx(bn,{justify:"center",children:n.jsx(sl,{items:A,button:{variant:"ghost",size:"sm",isIconOnly:!0,icon:n.jsx(tl,{size:"1em"}),label:s("comp:BAITable.ExpandOptions"),tooltip:s("comp:BAITable.ExpandOptions")},hasChevron:!1})}):null,l[20]=F.length,l[21]=A,l[22]=s,l[23]=T):T=l[23];const C=T;let v;return l[24]!==C||l[25]!==u||l[26]!==r?(v={mode:r,expandedRowKeys:u,onExpandedRowsChange:K,expandColumnTitle:C},l[24]=C,l[25]=u,l[26]=r,l[27]=v):v=l[27],v};function xa(a){return a.id}const Rn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISubStepNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],type:"SubStepResultGQL",abstractKey:null};Rn.hash="b293ef89b3c67ebb0a3733e1c22f6df9";const _a="HH:mm:ss.SSS",ja=(a,e)=>{if(!a||!e)return null;const l=ee(e).diff(ee(a));if(!Number.isFinite(l)||l<0)return null;if(l<1e3)return`${Math.round(l)} ms`;if(l<6e4)return`${(l/1e3).toFixed(2)} s`;const s=Math.round(l/1e3),r=Math.floor(s/60);return r<60?`${r}m ${String(s%60).padStart(2,"0")}s`:`${Math.floor(r/60)}h ${String(r%60).padStart(2,"0")}m`},Sn=a=>a.trim().toLowerCase().replace(/[\s_-]+/g,"-"),Bn=(a,e,l,s)=>e===l-1&&!!s&&Sn(a.step)===Sn(s),Pn=(a,e)=>{const l=$e(a);return l.filter((s,r)=>!Bn(s,r,l.length,e)).length},Ka=a=>(a==null?void 0:a.replace(/\s*\n\s*/g," ").trim())||"-",Ca=a=>a&&a!=="%future added value"?a:null,Na=a=>{"use memo";const e=ue.c(39);let l,s,r,d;e[0]!==a?({subStepsFrgmt:d,parentPhase:r,className:l,...s}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d):(l=e[1],s=e[2],r=e[3],d=e[4]);const{t}=Ze();let o;e[5]===Symbol.for("react.memo_cache_sentinel")?(o=Rn,e[5]=o):o=e[5];const u=P.useFragment(o,d);let m,c,S,y,k,f,g;if(e[6]!==l||e[7]!==s||e[8]!==r||e[9]!==u||e[10]!==t){const b=$e(u);e[18]!==l?(f=tn("bai-substep-panel",l),e[18]=l,e[19]=f):f=e[19],g=s,k="bai-substep-scroll",c="bai-substep-table";let A,T;e[20]===Symbol.for("react.memo_cache_sentinel")?(S=n.jsxs("colgroup",{children:[n.jsx("col",{className:"bai-substep-col-rail"}),n.jsx("col",{className:"bai-substep-col-step"}),n.jsx("col",{className:"bai-substep-col-result"}),n.jsx("col",{className:"bai-substep-col-duration"}),n.jsx("col",{className:"bai-substep-col-time"}),n.jsx("col",{className:"bai-substep-col-code"}),n.jsx("col",{})]}),T=n.jsx("th",{scope:"col"}),A=[["Step",void 0],["Result",void 0],["Duration","bai-substep-num"],["Time",void 0],["ErrorCode",void 0],["Message",void 0]],e[20]=A,e[21]=S,e[22]=T):(A=e[20],S=e[21],T=e[22]),e[23]!==t?(y=n.jsx("thead",{children:n.jsxs("tr",{children:[T,A.map(C=>{const[v,_]=C;return n.jsx("th",{scope:"col",className:_,children:n.jsx(B,{type:"supporting",weight:"medium",children:t(`comp:BAISubStepNodes.${v}`)})},v)})]})}),e[23]=t,e[24]=y):y=e[24],m=b.map((C,v)=>{const _=Ca(C.result),E=Bn(C,v,b.length,r),N=ja(C.startedAt,C.endedAt);return n.jsxs("tr",{className:tn("bai-substep-row",E&&"bai-substep-row--marker"),"data-variant":_?wn[_]:"default",children:[n.jsx("td",{className:"bai-substep-rail-cell"}),n.jsx("td",{children:n.jsx(B,{type:"code",size:"sm",color:E?"secondary":"primary",children:C.step})}),n.jsx("td",{children:_?n.jsx("span",{className:"bai-substep-result",children:n.jsx(B,{type:"supporting",color:"inherit",children:_})}):null}),n.jsx("td",{className:"bai-substep-num",children:!E&&N?n.jsx(B,{type:"code",size:"sm",color:"secondary",children:N}):n.jsx(B,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:C.startedAt?n.jsx(B,{type:"code",size:"sm",color:"secondary",children:ee(C.startedAt).format(_a)}):null}),n.jsx("td",{children:C.errorCode?n.jsx("span",{className:"bai-substep-code",children:n.jsx(B,{type:"code",size:"sm",color:"secondary",children:C.errorCode})}):n.jsx(B,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:n.jsx(B,{type:"supporting",children:E?t("comp:BAISubStepNodes.ResultMarker"):Ka(C.message)})})]},`${C.step}-${v}`)}),e[6]=l,e[7]=s,e[8]=r,e[9]=u,e[10]=t,e[11]=m,e[12]=c,e[13]=S,e[14]=y,e[15]=k,e[16]=f,e[17]=g}else m=e[11],c=e[12],S=e[13],y=e[14],k=e[15],f=e[16],g=e[17];let h;e[25]!==m?(h=n.jsx("tbody",{children:m}),e[25]=m,e[26]=h):h=e[26];let F;e[27]!==c||e[28]!==S||e[29]!==y||e[30]!==h?(F=n.jsxs("table",{className:c,children:[S,y,h]}),e[27]=c,e[28]=S,e[29]=y,e[30]=h,e[31]=F):F=e[31];let p;e[32]!==F||e[33]!==k?(p=n.jsx("div",{className:k,children:F}),e[32]=F,e[33]=k,e[34]=p):p=e[34];let K;return e[35]!==p||e[36]!==f||e[37]!==g?(K=n.jsx("div",{className:f,...g,children:p}),e[35]=p,e[36]=f,e[37]=g,e[38]=K):K=e[38],K},Ia=a=>{"use memo";const e=ue.c(24);let l,s,r,d;e[0]!==a?({schedulingHistoryFrgmt:d,expandMode:l,onExpandModeChange:s,...r}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d):(l=e[1],s=e[2],r=e[3],d=e[4]);let t;e[5]===Symbol.for("react.memo_cache_sentinel")?(t=Dn,e[5]=t):t=e[5];const o=P.useFragment(t,d);let u;e[6]!==o?(u=$e(o),e[6]=o,e[7]=u):u=e[7];const m=u;let c;e[8]!==l||e[9]!==s?(c={mode:l,onModeChange:s,isExpandable:La},e[8]=l,e[9]=s,e[10]=c):c=e[10];const{expandedRowKeys:S,onExpandedRowsChange:y,expandColumnTitle:k}=ba(m,c);let f,g;e[11]!==m?(f=p=>{var K;return Pn(((K=m.find(b=>b.id===p.id))==null?void 0:K.subSteps)??[],p.phase)>0},g=p=>{var K;return n.jsx(Na,{subStepsFrgmt:((K=m.find(b=>b.id===p.id))==null?void 0:K.subSteps)??[],parentPhase:p.phase})},e[11]=m,e[12]=f,e[13]=g):(f=e[12],g=e[13]);let h;e[14]!==k||e[15]!==S||e[16]!==y||e[17]!==f||e[18]!==g?(h={columnTitle:k,expandedRowKeys:S,onExpandedRowsChange:y,rowExpandable:f,expandedRowRender:g},e[14]=k,e[15]=S,e[16]=y,e[17]=f,e[18]=g,e[19]=h):h=e[19];let F;return e[20]!==o||e[21]!==r||e[22]!==h?(F=n.jsx(ga,{schedulingHistoryFrgmt:o,expandable:h,...r}),e[20]=o,e[21]=r,e[22]=h,e[23]=F):F=e[23],F};function La(a){return Pn(a.subSteps??[],a.phase)>0}const Vn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"6cb167705df49d003fee4ee02f1ee82e",id:null,metadata:{},name:"UNSAFELazyUserEmailViewQuery",operationKind:"query",text:`query UNSAFELazyUserEmailViewQuery(
  $uuid: String!
) {
  user_node(id: $uuid) {
    email
    id
  }
}
`}}})();Vn.hash="67caa5daf6f6559a42a344a9b5eadff6";const Aa=({uuid:a,fetchKey:e,...l})=>{const{user_node:s}=P.useLazyLoadQuery(Vn,{uuid:a?xn("UserNode",a):""},{fetchPolicy:a?e===void 0?"store-or-network":"network-only":"store-only",fetchKey:e});return(s==null?void 0:s.email)&&n.jsx(Ue,{...l,children:s==null?void 0:s.email})},$n={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailDrawerFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],type:"ComputeSessionNode",abstractKey:null};$n.hash="eb57207016a6a8cf6abbf348456840de";const Hn=(function(){var a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,e,l,s],storageKey:null}],storageKey:null},r];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailContentFragment",selections:[a,e,l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},s,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},r],storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"ImageNodeSimpleTagFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"ConnectedKernelListFragment"}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:d,storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusTagFragment"},{args:null,kind:"FragmentSpread",name:"SessionActionButtonsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionTypeTagFragment"},{args:null,kind:"FragmentSpread",name:"EditableSessionNameFragment"},{args:null,kind:"FragmentSpread",name:"SessionReservationFragment"},{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionUsageMonitorFragment"},{args:null,kind:"FragmentSpread",name:"ContainerCommitModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionIdleChecksNodeFragment"},{args:null,kind:"FragmentSpread",name:"SessionStatusDetailModalFragment"},{args:null,kind:"FragmentSpread",name:"AppLauncherModalFragment"},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionAgentIdsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionClusterModeFragment"},{args:null,kind:"FragmentSpread",name:"SessionAccessKeyFragment"}],type:"ComputeSessionNode",abstractKey:null}})();Hn.hash="a6ab9f7d99863931c4fa11da127bb44c";const zn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},m=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],c={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},S=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,s,r,d],storageKey:null}],storageKey:null},t];return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[l,s,r,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,r,l],storageKey:null}],storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},o,u,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},r,{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:m,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:m,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},o,l],storageKey:null},l,s,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},d,c,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:S,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:S,storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}]},params:{cacheID:"e61c165d4592ea36e0fe7c0a5174b2da",id:null,metadata:{},name:"SessionDetailContentQuery",operationKind:"query",text:`query SessionDetailContentQuery(
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
`}}})();zn.hash="54a57e1f9b8de6ca1ec280de81b4e986";const va=a=>{"use memo";const e=ue.c(10);let l,s,r;e[0]!==a?({content:l,language:s,...r}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r):(l=e[1],s=e[2],r=e[3]);let d;e[4]!==l||e[5]!==s?(d=n.jsx(il,{language:s,children:l}),e[4]=l,e[5]=s,e[6]=d):d=e[6];let t;return e[7]!==r||e[8]!==d?(t=n.jsx(qe,{...r,children:d}),e[7]=r,e[8]=d,e[9]=t):t=e[9],t},Un={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ConnectedKernelListFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],type:"KernelNode",abstractKey:null};Un.hash="b07dcbdb178c221c667bd2f86f43cbd5";const yn={PREPARING:"blue",BUILDING:"blue",PULLING:"blue",PREPARED:"blue",CREATING:"blue",PENDING:"green",SCHEDULED:"green",RUNNING:"green",RESTARTING:"green",RESIZING:"green",SUSPENDED:"green",TERMINATING:"default",TERMINATED:"default",CANCELLED:"default",ERROR:"red"},Ta=({kernelsFrgmt:a,sessionFrgmtForLogModal:e})=>{const{t:l}=Ae(),[s,r]=j.useState(),d=P.useFragment(Un,a),t=kn([{title:l("kernel.Hostname"),dataIndex:"cluster_hostname",render:(u,m)=>n.jsxs(n.Fragment,{children:[n.jsx(B,{children:u}),n.jsx(we,{variant:"ghost",size:"sm",icon:n.jsx(da,{}),label:l("session.SeeContainerLogs"),tooltip:l("session.SeeContainerLogs"),onClick:()=>{m.row_id&&r(m.row_id)}})]})},{title:l("kernel.Status"),dataIndex:"status",render:(u,m)=>n.jsx(n.Fragment,{children:(m==null?void 0:m.status_info)!==""?n.jsx(_n,{values:[{label:u,color:Ye(yn,u)},{label:m==null?void 0:m.status_info,color:Ye(yn,(m==null?void 0:m.status_info)??"")}]}):n.jsx(en,{variant:rl("kernel",u),label:u})})},{title:l("kernel.AgentId"),dataIndex:"agent_id",render:u=>ze(u)?"-":n.jsx(Ue,{copyable:!0,children:u})},{title:l("kernel.KernelId"),fixed:"left",dataIndex:"row_id",render:u=>ze(u)?"-":n.jsx(pn,{uuid:u})},{title:l("kernel.ContainerId"),dataIndex:"container_id",render:u=>ze(u)?"-":n.jsx(pn,{uuid:u})}]),o=j.useMemo(()=>ua($e(d),["cluster_role","cluster_idx"]),[d]);return n.jsxs(n.Fragment,{children:[n.jsx(Fn,{scroll:{x:"max-content"},bordered:!0,rowKey:"id",columns:t,dataSource:o}),n.jsx(ol,{children:n.jsx(dl,{open:!!s,sessionFrgmt:e||null,defaultKernelId:s,onCancel:()=>{r(void 0)}})})]})},On=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"scope_id"},e={defaultValue:null,kind:"LocalArgument",name:"sessionId"},l=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"sessionId"},{kind:"Variable",name:"scope_id",variableName:"scope_id"}],concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[a,e],kind:"Fragment",metadata:null,name:"EditableSessionNameRefetchQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,a],kind:"Operation",name:"EditableSessionNameRefetchQuery",selections:l},params:{cacheID:"58d69307fe6e70d2c3409231b0279c8b",id:null,metadata:{},name:"EditableSessionNameRefetchQuery",operationKind:"query",text:`query EditableSessionNameRefetchQuery(
  $sessionId: GlobalIDField!
  $scope_id: ScopeField
) {
  compute_session_node(id: $sessionId, scope_id: $scope_id) {
    id
    name
  }
}
`}}})();On.hash="387b0fe2d9acb6f455335434b59c3e6c";const Qn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EditableSessionNameFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},action:"THROW"}],type:"ComputeSessionNode",abstractKey:null};Qn.hash="6dfb2b44bf25b8bfda2fce5ab4cedad8";const Ea=a=>{"use memo";const e=ue.c(28),{sessionFrgmt:l,level:s,editable:r,dimmed:d}=a,t=r===void 0?!1:r,o=d===void 0?!1:d,u=P.useRelayEnvironment();let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=Qn,e[0]=m):m=e[0];const c=P.useFragment(m,l),[S,y]=j.useState(c.name),k=ul(S),[f]=jn(),g=He();let h;e[1]!==g||e[2]!==c.row_id?(h={mutationFn:w=>g.rename(c.row_id,w)},e[1]=g,e[2]=c.row_id,e[3]=h):h=e[3];const F=cl(h),{t:p}=Ae(),{message:K}=yl.useApp(),[b,A]=j.useState(!1),[T,C]=j.useState(!1);let v;e[4]===Symbol.for("react.memo_cache_sentinel")?(v=["RESTARTING","PREPARING","PREPARED","CREATING","PULLING"],e[4]=v):v=e[4];const _=!v.includes(c.status||""),E=t&&f.uuid===c.user_id&&_,N=F.isPending||S!==c.name,M=F.isPending||S!==c.name?S:c.name,D=o||N;let V;e[5]!==T||e[6]!==M||e[7]!==D||e[8]!==b||e[9]!==E||e[10]!==N||e[11]!==s||e[12]!==p?(V=(!b||N)&&n.jsxs(bn,{gap:1,align:"center",children:[s?n.jsx(Ve,{level:s,color:D?"disabled":void 0,children:M}):n.jsx(B,{color:D?"disabled":void 0,children:M}),n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:T?n.jsx(ml,{"aria-hidden":!0}):n.jsx(gl,{"aria-hidden":!0}),label:p("sourceCodeViewer.Copy"),tooltip:p("sourceCodeViewer.Copy"),isDisabled:T,onClick:()=>{var w;(w=navigator.clipboard)==null||w.writeText(M??""),C(!0),setTimeout(()=>C(!1),1500)}}),E&&!N&&n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(pl,{"aria-hidden":!0}),label:p("button.Edit"),tooltip:p("button.Edit"),onClick:()=>A(!0)})]}),e[5]=T,e[6]=M,e[7]=D,e[8]=b,e[9]=E,e[10]=N,e[11]=s,e[12]=p,e[13]=V):V=e[13];let R;e[14]!==b||e[15]!==N||e[16]!==K||e[17]!==u||e[18]!==F||e[19]!==c.id||e[20]!==c.name||e[21]!==c.project_id||e[22]!==p||e[23]!==k?(R=b&&!N&&n.jsx(rn,{onFinish:w=>{A(!1),y(w.sessionName),F.mutate(w.sessionName,{onSuccess:()=>{P.fetchQuery(u,On,{sessionId:c.id,scope_id:`project:${c.project_id}`}).toPromise().catch()},onError:()=>{c.name!==w.sessionName&&K.error(p("session.FailToRenameSession"))}})},initialValues:{sessionName:c.name},style:{flex:1},children:n.jsx(rn.Item,{name:"sessionName",rules:k,children:n.jsx(Sl,{label:p("session.SessionName"),size:"lg",hasAutoFocus:!0,onKeyDown:w=>{w.key==="Escape"&&(w.stopPropagation(),A(!1))}})})}),e[14]=b,e[15]=N,e[16]=K,e[17]=u,e[18]=F,e[19]=c.id,e[20]=c.name,e[21]=c.project_id,e[22]=p,e[23]=k,e[24]=R):R=e[24];let H;return e[25]!==V||e[26]!==R?(H=n.jsxs(n.Fragment,{children:[V,R]}),e[25]=V,e[26]=R,e[27]=H):H=e[27],H},qn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionIdleChecksNodeFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionReclamationStatusCellFragment"}],type:"ComputeSessionNode",abstractKey:null};qn.hash="cd0692b3021358f17c5abea99afd29d2";const wa={warningText:{kMwMTN:"webuis3pv69",$$css:!0}};function Ma(a,e){var l;if(e==="remaining")return!a.remaining||a.remaining<3600?"red":a.remaining<3600*4?"orange":"green";if(a.extra&&(!a.remaining||a.remaining<3600*4))return(l=bl(a.extra.resources,a.extra.thresholds_check_operator))==null?void 0:l.color}const Da=a=>{"use memo";const e=ue.c(24),{checkKey:l,value:s,sessionFrgmt:r}=a,{t:d}=Ae(),t=s.remaining??0;let o;e[0]!==d?(o=b=>d(b==="network_timeout"?"session.NetworkIdleTimeout":b==="session_lifetime"?"session.MaxSessionLifetime":"session.UtilizationIdleTimeout"),e[0]=d,e[1]=o):o=e[1];const u=o;let m;e[2]!==d?(m=b=>d(b==="expire_after"?"session.ExpiresAfter":"session.GracePeriod"),e[2]=d,e[3]=m):m=e[3];const c=m,S=l==="utilization"?"utilization":"remaining";let y;e[4]!==S||e[5]!==s?(y=Ma(s,S),e[4]=S,e[5]=s,e[6]=y):y=e[6];const k=y;let f;e[7]!==t?(f=ee().add(t,"second").toISOString(),e[7]=t,e[8]=f):f=e[8];const g=f;let h;e[9]===Symbol.for("react.memo_cache_sentinel")?(h={flex:1},e[9]=h):h=e[9];let F;e[10]!==l||e[11]!==u||e[12]!==r?(F=n.jsx(L,{gap:"xxs",children:l==="utilization"?n.jsx(fl,{sessionFrgmt:r}):n.jsx(B,{children:u(l)})}),e[10]=l,e[11]=u,e[12]=r,e[13]=F):F=e[13];let p;e[14]!==g||e[15]!==c||e[16]!==t||e[17]!==d||e[18]!==k||e[19]!==s.remaining_time_type?(p=t>=0?n.jsxs(L,{gap:"xxs",align:"center",children:[n.jsx(hl,{delay:1e3,callback:()=>ee(g).diff()>0?kl(ee().toISOString(),g):"00:00:00",render:b=>n.jsx(_n,{values:[{label:c(s.remaining_time_type),color:k},{label:b,color:k}]})}),s.remaining_time_type==="grace_period"&&n.jsx(Fl,{title:n.jsx("div",{style:{whiteSpace:"pre-line"},children:d("session.GracePeriodTooltip")})})]}):n.jsx(B,{xstyle:wa.warningText,children:d("session.ReclamationStatusChecking")}),e[14]=g,e[15]=c,e[16]=t,e[17]=d,e[18]=k,e[19]=s.remaining_time_type,e[20]=p):p=e[20];let K;return e[21]!==F||e[22]!==p?(K=n.jsxs(L,{style:h,direction:"column",align:"stretch",children:[F,p]}),e[21]=F,e[22]=p,e[23]=K):K=e[23],K},Ra=({sessionNodeFrgmt:a=null,direction:e="row"})=>{const l=P.useFragment(qn,a),s=Kn(l==null?void 0:l.idle_checks,{fallbackValue:{}});return n.jsx(L,{direction:e,align:"stretch",gap:"sm",children:be(s,(r,d)=>r.remaining?n.jsx(Da,{checkKey:d,value:r,sessionFrgmt:l},d):null)})},Gn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionStatusDetailModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusTagFragment"}],type:"ComputeSessionNode",abstractKey:null};Gn.hash="9fda416861ce96da9edb0c823baaa6b8";const fn={predicateMsg:{ks0D6T:"webui1dc814f",$$css:!0}},Ba=({sessionFrgmt:a,...e})=>{var o,u,m,c,S,y,k,f;const{t:l}=Ae(),s=Cn(),r=He(),d=P.useFragment(Gn,a),t=JSON.parse(d.status_data||"{}");return n.jsx(qe,{title:n.jsxs(n.Fragment,{children:[l("session.StatusInfo"),n.jsx("span",{style:{fontWeight:"normal"},children:n.jsx(In,{sessionFrgmt:d,showInfo:!0,showQueuePosition:!1})})]}),footer:null,width:450,...e,children:n.jsxs(Nn,{columns:"single",children:[n.jsx(I,{label:l("session.SessionName"),children:n.jsx(Ue,{copyable:!0,ellipsis:{tooltip:!0},children:d.name??""})}),t!=null&&t.kernel?n.jsx(I,{label:l("session.KernelExitCode"),children:t.kernel.exit_code}):null,t!=null&&t.session?n.jsx(I,{label:l("session.SessionStatus"),children:(o=t.session)==null?void 0:o.status}):null,t!=null&&t.scheduler?n.jsxs(n.Fragment,{children:[n.jsx(I,{label:l("session.LastTry"),children:ee((u=t.scheduler)==null?void 0:u.last_try).format("lll")}),n.jsx(I,{label:l("session.TotalRetries"),children:(m=t.scheduler)==null?void 0:m.retries}),((c=t.scheduler)==null?void 0:c.msg)&&n.jsx(I,{label:l("session.Message"),children:(S=t.scheduler)==null?void 0:S.msg}),n.jsx(I,{label:l("session.PredicateChecks"),children:n.jsxs(L,{direction:"column",gap:"md",align:"stretch",children:[be((y=t.scheduler)==null?void 0:y.failed_predicates,g=>n.jsxs(L,{gap:"xs",align:"start",children:[n.jsx(xl,{style:{color:"var(--color-error)",marginTop:4,flexShrink:0},size:16}),n.jsxs(L,{direction:"column",align:"stretch",children:[n.jsx(B,{children:g.name}),n.jsx(B,{color:"secondary",xstyle:fn.predicateMsg,children:g.msg})]})]},g.name)),be((k=t.scheduler)==null?void 0:k.passed_predicates,g=>n.jsxs(L,{gap:"xs",align:"start",children:[n.jsx(_l,{style:{color:"var(--color-success)",marginTop:4,flexShrink:0},size:16}),n.jsxs(L,{direction:"column",align:"stretch",children:[n.jsx(B,{children:g.name}),n.jsx(B,{color:"secondary",xstyle:fn.predicateMsg,children:g.msg})]})]},g.name))]})})]}):null,t!=null&&t.error?be(((f=t==null?void 0:t.error)==null?void 0:f.collection)??t,g=>n.jsxs(j.Fragment,{children:[(s==="superadmin"||!r._config.hideAgents)&&(g==null?void 0:g.agent_id)&&n.jsx(I,{label:l("session.AgentId"),children:g==null?void 0:g.agent_id}),n.jsx(I,{label:l("dialog.error.Error"),children:n.jsx(en,{variant:"error",label:g.name})}),n.jsx(I,{label:l("session.Message"),children:g.repr}),(g==null?void 0:g.traceback)&&n.jsx(I,{label:l("session.Traceback"),children:n.jsx("pre",{children:g==null?void 0:g.traceback})})]},g.name)):null]})})},Pa=({...a})=>{const{t:e}=Ae(),{token:l}=jl.useToken();return n.jsxs(qe,{title:e("session.ReclamationStatus"),footer:null,width:700,...a,children:[n.jsx(B,{children:e("session.IdleChecksDesc")}),n.jsx(Ve,{level:5,children:e("session.MaxSessionLifetime")}),n.jsx("p",{children:e("session.MaxSessionLifetimeDesc")}),n.jsx(Ve,{level:5,children:e("session.NetworkIdleTimeout")}),n.jsx("p",{children:e("session.NetworkIdleTimeoutDesc")}),n.jsx(Ve,{level:5,children:e("session.UtilizationIdleTimeout")}),n.jsx("p",{children:e("session.UtilizationIdleTimeoutDesc")}),n.jsxs(L,{direction:"column",align:"stretch",style:{marginLeft:l.marginMD},children:[n.jsx(Ve,{level:5,style:{margin:0},children:e("session.GracePeriod")}),n.jsx("p",{children:e("session.GracePeriodDesc")}),n.jsx(Ve,{level:5,style:{margin:0},children:e("session.UtilizationThreshold")}),n.jsx("p",{children:e("session.UtilizationThresholdDesc")})]})]})},Wn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"mounts",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"MountedVFolderLinksQuery",selections:[{alias:"legacy_session",args:e,concreteType:"ComputeSession",kind:"LinkedField",name:"compute_session",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"MountedVFolderLinksQuery",selections:[{alias:"legacy_session",args:e,concreteType:"ComputeSession",kind:"LinkedField",name:"compute_session",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"9025af1e54e75a0d3041d0e12150939c",id:null,metadata:{},name:"MountedVFolderLinksQuery",operationKind:"query",text:`query MountedVFolderLinksQuery(
  $uuid: UUID!
) {
  legacy_session: compute_session(id: $uuid) {
    mounts
    id
  }
}
`}}})();Wn.hash="f1e2ef43ac11c6b980313ddac8cd1ec9";const Xn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksLegacyLazyFolderLinkFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null}],type:"ComputeSessionNode",abstractKey:null};Xn.hash="72fda7ec47bcaa5e7fc83cbaabc822c6";const Yn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksLegacyLazyFolderLinkFragment"}],type:"ComputeSessionNode",abstractKey:null};Yn.hash="f26bc04640693f4094c9a072011821b0";const Va=({sessionFrgmt:a})=>{var s;const e=He(),l=P.useFragment(Yn,a);return e.supports("vfolder_nodes_in_session_node")?be((s=l.vfolder_nodes)==null?void 0:s.edges,(r,d)=>(r==null?void 0:r.node)&&n.jsx(En,{vfolderNodeFragment:r.node},`mounted-vfolder-${d}`)):l.row_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx($a,{sessionFrgmt:l})}):null},$a=({sessionFrgmt:a})=>{var r;const e=He(),l=P.useFragment(Xn,a),{legacy_session:s}=P.useLazyLoadQuery(Wn,{uuid:l.row_id||""},{fetchPolicy:l.row_id?"store-and-network":"store-only"});return e.supports("vfolder-mounts")?be(aa(s==null?void 0:s.mounts,l==null?void 0:l.vfolder_mounts),d=>{const[t,o]=d;return n.jsx(En,{folderId:o??"",folderName:t??"",showIcon:!0},o)}):(r=s==null?void 0:s.mounts)==null?void 0:r.join(", ")},Jn=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r={defaultValue:null,kind:"LocalArgument",name:"scope"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],t={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[a,e,l,s,r],kind:"Fragment",metadata:null,name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[t,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,a,s,e,l],kind:"Operation",name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[t,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},o,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"1bfe7bc2611f279e70c35d22c11fb631",id:null,metadata:{},name:"SessionSchedulingHistoryModalQuery",operationKind:"query",text:`query SessionSchedulingHistoryModalQuery(
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
`}}})();Jn.hash="6221439d9cf111e4683277c5e89974db";const Ha=a=>{"use memo";var x,U,Ke,Ee;const e=ue.c(116);let l,s,r,d,t;e[0]!==a?({open:d,loading:l,sessionId:t,onCancel:r,...s}=a,e[0]=a,e[1]=l,e[2]=s,e[3]=r,e[4]=d,e[5]=t):(l=e[1],s=e[2],r=e[3],d=e[4],t=e[5]);const{t:o}=Ae(),[u,m]=Ln(),[c,S]=j.useState(),[y,k]=j.useState("-updatedAt"),[f,g]=on("schedulingHistoryExpandMode"),[h,F]=on("table_column_overrides.SessionSchedulingHistory");let p;e[6]===Symbol.for("react.memo_cache_sentinel")?(p={current:1,pageSize:10},e[6]=p):p=e[6];const{baiPaginationOption:K,tablePaginationOption:b,setTablePaginationOption:A}=An(p),T=j.useDeferredValue(d),C=j.useDeferredValue(u),v=j.useDeferredValue(c),_=j.useDeferredValue(y),E=j.useDeferredValue(K.offset),N=j.useDeferredValue(K.limit);let M;e[7]===Symbol.for("react.memo_cache_sentinel")?(M=Jn,e[7]=M):M=e[7];let D;e[8]!==t?(D={sessionId:t},e[8]=t,e[9]=D):D=e[9];const V=v??void 0;let R;e[10]!==_?(R=Kl(_)??[{field:"UPDATED_AT",direction:"DESC"}],e[10]=_,e[11]=R):R=e[11];let H;e[12]!==N||e[13]!==E||e[14]!==D||e[15]!==V||e[16]!==R?(H={scope:D,filter:V,orderBy:R,limit:N,offset:E},e[12]=N,e[13]=E,e[14]=D,e[15]=V,e[16]=R,e[17]=H):H=e[17];const w=T?"network-only":"store-only";let xe;e[18]!==C||e[19]!==w?(xe={fetchKey:C,fetchPolicy:w},e[18]=C,e[19]=w,e[20]=xe):xe=e[20];const ce=P.useLazyLoadQuery(M,H,xe);let z;e[21]!==o?(z=o("session.SessionSchedulingHistory"),e[21]=o,e[22]=z):z=e[22];const _e=l||T!==d;let ne;e[23]!==A?(ne=Ce=>{S(Ce),A({current:1})},e[23]=A,e[24]=ne):ne=e[24];let O;e[25]!==o?(O=o("session.ID"),e[25]=o,e[26]=O):O=e[26];let je;e[27]!==O?(je={key:"id",propertyLabel:O,type:"uuid",fixedOperator:"equals"},e[27]=O,e[28]=je):je=e[28];let Q;e[29]!==o?(Q=o("session.Phase"),e[29]=o,e[30]=Q):Q=e[30];let i;e[31]!==Q?(i={key:"phase",propertyLabel:Q,type:"string",fixedOperator:"contains"},e[31]=Q,e[32]=i):i=e[32];let q;e[33]!==o?(q=o("session.Result"),e[33]=o,e[34]=q):q=e[34];let le;e[35]===Symbol.for("react.memo_cache_sentinel")?(le=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[35]=le):le=e[35];let ae;e[36]!==q?(ae={key:"result",propertyLabel:q,type:"enum",strictSelection:!0,options:le},e[36]=q,e[37]=ae):ae=e[37];let se;e[38]!==o?(se=o("session.FromStatus"),e[38]=o,e[39]=se):se=e[39];let te;e[40]!==se?(te={key:"fromStatus",propertyLabel:se,type:"string",valueMode:"scalar"},e[40]=se,e[41]=te):te=e[41];let G;e[42]!==o?(G=o("session.ToStatus"),e[42]=o,e[43]=G):G=e[43];let W;e[44]!==G?(W={key:"toStatus",propertyLabel:G,type:"string",valueMode:"scalar"},e[44]=G,e[45]=W):W=e[45];let ie;e[46]!==o?(ie=o("session.ErrorCode"),e[46]=o,e[47]=ie):ie=e[47];let re;e[48]!==ie?(re={key:"errorCode",propertyLabel:ie,type:"string",fixedOperator:"contains"},e[48]=ie,e[49]=re):re=e[49];let X;e[50]!==o?(X=o("session.Message"),e[50]=o,e[51]=X):X=e[51];let oe;e[52]!==X?(oe={key:"message",propertyLabel:X,type:"string",fixedOperator:"contains"},e[52]=X,e[53]=oe):oe=e[53];let Y;e[54]!==o?(Y=o("session.CreatedAt"),e[54]=o,e[55]=Y):Y=e[55];let $;e[56]!==Y?($={key:"createdAt",propertyLabel:Y,type:"datetime",defaultOperator:"after"},e[56]=Y,e[57]=$):$=e[57];let J;e[58]!==o?(J=o("session.UpdatedAt"),e[58]=o,e[59]=J):J=e[59];let ve;e[60]!==J?(ve={key:"updatedAt",propertyLabel:J,type:"datetime",defaultOperator:"after"},e[60]=J,e[61]=ve):ve=e[61];let de;e[62]!==je||e[63]!==i||e[64]!==ae||e[65]!==te||e[66]!==W||e[67]!==re||e[68]!==oe||e[69]!==$||e[70]!==ve?(de=[je,i,ae,te,W,re,oe,$,ve],e[62]=je,e[63]=i,e[64]=ae,e[65]=te,e[66]=W,e[67]=re,e[68]=oe,e[69]=$,e[70]=ve,e[71]=de):de=e[71];let Z;e[72]!==c||e[73]!==ne||e[74]!==de?(Z=n.jsx(ia,{value:c,onChange:ne,filterProperties:de}),e[72]=c,e[73]=ne,e[74]=de,e[75]=Z):Z=e[75];const Me=C!==u;let me;e[76]!==u||e[77]!==Me||e[78]!==m?(me=n.jsx(L,{children:n.jsx(Cl,{value:u,onChange:m,loading:Me,autoUpdateDelay:null})}),e[76]=u,e[77]=Me,e[78]=m,e[79]=me):me=e[79];let ge;e[80]!==Z||e[81]!==me?(ge=n.jsxs(L,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,me]}),e[80]=Z,e[81]=me,e[82]=ge):ge=e[82];const De=C!==u||v!==c||_!==y||E!==K.offset||N!==K.limit;let pe;e[83]!==A?(pe=Ce=>{k(Ce),A({current:1})},e[83]=A,e[84]=pe):pe=e[84];const Re=f??void 0;let Se;e[85]!==h||e[86]!==F?(Se={columnOverrides:h,onColumnOverridesChange:F},e[85]=h,e[86]=F,e[87]=Se):Se=e[87];const Be=((x=ce.sessionScopedSchedulingHistories)==null?void 0:x.count)??0;let ye;e[88]!==A?(ye=(Ce,Ne)=>{A({current:Ce,pageSize:Ne})},e[88]=A,e[89]=ye):ye=e[89];let fe;e[90]!==Be||e[91]!==ye||e[92]!==b.current||e[93]!==b.pageSize?(fe={pageSize:b.pageSize,current:b.current,total:Be,onChange:ye},e[90]=Be,e[91]=ye,e[92]=b.current,e[93]=b.pageSize,e[94]=fe):fe=e[94];let he;e[95]!==((U=ce.sessionScopedSchedulingHistories)==null?void 0:U.edges)?(he=be((Ke=ce.sessionScopedSchedulingHistories)==null?void 0:Ke.edges,"node"),e[95]=(Ee=ce.sessionScopedSchedulingHistories)==null?void 0:Ee.edges,e[96]=he):he=e[96];let ke;e[97]!==y||e[98]!==g||e[99]!==De||e[100]!==pe||e[101]!==Re||e[102]!==Se||e[103]!==fe||e[104]!==he?(ke=n.jsx(Ia,{resizable:!0,loading:De,order:y,onChangeOrder:pe,expandMode:Re,onExpandModeChange:g,tableSettings:Se,pagination:fe,schedulingHistoryFrgmt:he}),e[97]=y,e[98]=g,e[99]=De,e[100]=pe,e[101]=Re,e[102]=Se,e[103]=fe,e[104]=he,e[105]=ke):ke=e[105];let Fe;e[106]!==ge||e[107]!==ke?(Fe=n.jsxs(L,{direction:"column",align:"stretch",gap:"sm",children:[ge,ke]}),e[106]=ge,e[107]=ke,e[108]=Fe):Fe=e[108];let Te;return e[109]!==s||e[110]!==r||e[111]!==d||e[112]!==_e||e[113]!==Fe||e[114]!==z?(Te=n.jsx(qe,{title:z,loading:_e,open:d,variant:"fullscreen",footer:null,onCancel:r,...s,children:Fe}),e[109]=s,e[110]=r,e[111]=d,e[112]=_e,e[113]=Fe,e[114]=z,e[115]=Te):Te=e[115],Te},hn=(a,e)=>{const l=JSON.parse(a||"{}"),s=Tn(e);return s?{...Qe(l,s),acceleratorType:s}:l},Xe=a=>Yl(Jl(JSON.parse(a||"{}"),e=>Zl(e)),e=>e===0),za=a=>{"use memo";var Me,me,ge,De,pe,Re,Se,Be,ye,fe,he,ke,Fe,Te;const e=ue.c(60),{id:l,fetchKey:s,sessionFrgmt:r,project:d}=a,{t}=Ae(),{md:o}=Nl(),{mergedResourceSlots:u}=Il(),m=vn(),[c]=jn(),S=Cn(),y=He();let k;e[0]!==y?(k=y.supports("session-scheduling-history"),e[0]=y,e[1]=k):k=e[1];const f=k,[g,h]=j.useState(!1),[F,p]=j.useState(!1),K="current",[b,A]=j.useState("kernels"),[T,C]=dn(!1),{toggle:v}=C,[_,E]=dn(!1),{toggle:N}=E,[M,D]=P.useQueryLoader(sa);let V;e[2]===Symbol.for("react.memo_cache_sentinel")?(V={current:1,pageSize:10},e[2]=V):V=e[2];const{baiPaginationOption:R,setTablePaginationOption:H}=An(V);let w;e[3]!==D||e[4]!==H?(w=(x,U)=>{const Ke=x.limit??10;H({pageSize:Ke,current:x.offset?Math.floor(x.offset/Ke)+1:1}),D(x,U)},e[3]=D,e[4]=H,e[5]=w):w=e[5];const xe=w;let ce;e[6]===Symbol.for("react.memo_cache_sentinel")?(ce=zn,e[6]=ce):ce=e[6];let z;e[7]!==l?(z=xn("ComputeSessionNode",l),e[7]=l,e[8]=z):z=e[8];let _e;e[9]!==z?(_e={id:z},e[9]=z,e[10]=_e):_e=e[10];const ne=s===Xl?r?"store-only":"store-and-network":"network-only";let O;e[11]!==s||e[12]!==ne?(O={fetchPolicy:ne,fetchKey:s},e[11]=s,e[12]=ne,e[13]=O):O=e[13];const{internalLoadedSession:je}=P.useLazyLoadQuery(ce,_e,O);let Q;e[14]===Symbol.for("react.memo_cache_sentinel")?(Q=Hn,e[14]=Q):Q=e[14];const i=P.useFragment(Q,je||r);let q;e[15]===Symbol.for("react.memo_cache_sentinel")?(q={fallbackValue:{}},e[15]=q):q=e[15];const le=Ll(Al(Kn(i==null?void 0:i.idle_checks,q)).map(Ua).filter(Boolean)),ae=i==null?void 0:i.project_id,se=i==null?void 0:i.requested_slots,te=i==null?void 0:i.tag;let G;e[16]!==se||e[17]!==te?(G=hn(se,te),e[16]=se,e[17]=te,e[18]=G):G=e[18];const W=G,ie=i==null?void 0:i.occupied_slots,re=i==null?void 0:i.tag;let X;e[19]!==ie||e[20]!==re?(X=hn(ie,re),e[19]=ie,e[20]=re,e[21]=X):X=e[21];const oe=X;let Y;e[22]!==(i==null?void 0:i.occupied_slots)?(Y=ze(Xe(i==null?void 0:i.occupied_slots)),e[22]=i==null?void 0:i.occupied_slots,e[23]=Y):Y=e[23];const $=!Y;let J;if(e[24]!==$||e[25]!==u||e[26]!==(i==null?void 0:i.occupied_slots)||e[27]!==(i==null?void 0:i.requested_slots)||e[28]!==(i==null?void 0:i.tag)){const x=Tn(i==null?void 0:i.tag)??"",U=Qe(Xe(i==null?void 0:i.requested_slots),x),Ke=Qe(Xe(i==null?void 0:i.occupied_slots),x);let Ee;e[30]!==u?(Ee=(Ne,Ge)=>{var ln,an;const Pe=(ln=u==null?void 0:u[Ne])==null?void 0:ln.number_format,nn=(Pe==null?void 0:Pe.round_length)||0;return Pe!=null&&Pe.binary?Number((an=ea(Ge.toString(),"g",2,!0))==null?void 0:an.numberFixed):nn>0?Number(Ge.toFixed(nn)):Ge},e[30]=u,e[31]=Ee):Ee=e[31];const Ce=Ee;J=$?vl(un(U),un(Ke)).filter(Ne=>Ce(Ne,Ke[Ne]??0)<Ce(Ne,U[Ne]??0)):[],e[24]=$,e[25]=u,e[26]=i==null?void 0:i.occupied_slots,e[27]=i==null?void 0:i.requested_slots,e[28]=i==null?void 0:i.tag,e[29]=J}else J=e[29];const de=J.length>0;let Z;return e[32]!==b||e[33]!==M||e[34]!==y||e[35]!==R||e[36]!==c||e[37]!==$||e[38]!==de||e[39]!==l||e[40]!==le||e[41]!==D||e[42]!==m||e[43]!==o||e[44]!==oe||e[45]!==T||e[46]!==g||e[47]!==_||e[48]!==F||e[49]!==d||e[50]!==xe||e[51]!==W||e[52]!==ae||e[53]!==i||e[54]!==f||e[55]!==t||e[56]!==v||e[57]!==N||e[58]!==S?(Z=i?n.jsxs(L,{direction:"column",gap:"lg",align:"stretch",children:[d!==null&&ae!==d.id&&n.jsx(Oe,{status:"warning",title:t("session.NotInProject")}),c.uuid!==(i==null?void 0:i.user_id)&&n.jsx(Oe,{status:"warning",title:t("session.AnotherUserSession")}),le&&le<3600&&n.jsx(Oe,{status:"warning",title:t("session.IdleCheckExpirationWarning")}),n.jsxs(L,{direction:"column",gap:"sm",align:"stretch",children:[n.jsxs(L,{direction:"row",justify:"between",align:"start",style:{alignSelf:"stretch"},gap:"sm",children:[n.jsx(Ea,{sessionFrgmt:i,level:3,dimmed:["TERMINATED","CANCELLED"].includes(i.status||""),editable:!["TERMINATED","CANCELLED"].includes(i.status||"")}),n.jsx(Tl,{size:"large",compact:!0,sessionFrgmt:i})]}),n.jsx(El,{children:n.jsxs(Nn,{columns:o?2:1,children:[n.jsx(I,{label:t("session.SessionId"),children:n.jsx(Ue,{code:!0,copyable:!0,ellipsis:{tooltip:!0},children:i.row_id??""})}),(S==="admin"||S==="superadmin")&&n.jsx(I,{label:t("credential.UserID"),children:(Me=i.owner)!=null&&Me.email?i.owner.email:i.user_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Aa,{uuid:i.user_id})}):"-"}),n.jsx(I,{label:t("general.AccessKey"),children:n.jsx(wl,{sessionFrgmt:i,copyable:!0})}),n.jsx(I,{label:t("session.Status"),children:n.jsxs(L,{children:[n.jsx(In,{sessionFrgmt:i,showInfo:!f}),!f&&(i!=null&&i.status_data)&&(i==null?void 0:i.status_data)!=="{}"?n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cn,{size:"1em"}),label:t("button.ClickForMoreDetails"),tooltip:t("button.ClickForMoreDetails"),onClick:()=>{p(!0)}}):null,f&&n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(ra,{size:"1em"}),label:t("session.SessionSchedulingHistory"),tooltip:t("session.SessionSchedulingHistory"),onClick:()=>N()})]})}),n.jsx(I,{label:t("session.SessionType"),children:n.jsxs(L,{children:[n.jsx(Ml,{sessionFrgmt:i}),i.type==="batch"&&i.startup_command&&n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cn,{size:"1em"}),label:t("session.ViewStartupCommand"),tooltip:t("session.ViewStartupCommand"),onClick:()=>v()})]})}),n.jsx(I,{label:t("session.launcher.Environments"),children:(De=(ge=(me=i.kernel_nodes)==null?void 0:me.edges[0])==null?void 0:ge.node)!=null&&De.image?n.jsx(Dl,{imageFrgmt:((Se=(Re=(pe=i.kernel_nodes)==null?void 0:pe.edges[0])==null?void 0:Re.node)==null?void 0:Se.image)||null}):i.row_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Rl,{sessionId:i.row_id})}):null}),n.jsx(I,{label:t("session.launcher.MountedFolders"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:n.jsx(Va,{sessionFrgmt:i})})}),n.jsx(I,{label:t("session.launcher.ResourceAllocation"),children:n.jsxs(L,{gap:"sm",wrap:"wrap",align:"center",children:[de&&n.jsx(Bl,{content:t("session.AllocatedLessThanRequested"),icon:n.jsx(Pl,{size:"1em",style:{color:"var(--color-warning)"}})}),n.jsx(Vl,{content:t("session.ResourceGroup"),children:n.jsx(en,{label:i.scaling_group})}),n.jsx($l,{resource:$?oe:W,comparedResource:$?W:void 0,showDividers:!0})]})}),n.jsx(I,{label:t("session.Agent"),children:n.jsx(Hl,{sessionFrgmt:i})}),n.jsx(I,{label:t("session.Reservation"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:n.jsx(zl,{sessionFrgmt:i})})}),n.jsx(I,{label:t("session.ClusterMode"),children:n.jsx(Ul,{sessionFrgmt:i,showSize:!0})}),y.supports("idle-checks-gql")&&i.status==="RUNNING"&&le?n.jsx(I,{label:t("session.ReclamationStatus"),children:n.jsxs(L,{gap:"xxs",align:"start",children:[n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ra,{sessionNodeFrgmt:i,direction:o?"row":"column"})}),n.jsx(we,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(Ol,{size:"1em"}),label:t("button.ClickForMoreDetails"),tooltip:t("button.ClickForMoreDetails"),onClick:()=>h(!0)})]})}):null,n.jsx(I,{label:t("session.ResourceUsage"),children:n.jsx(Ql,{sessionFrgmt:i,displayTarget:K})}),(((Be=i.dependees)==null?void 0:Be.count)??0)>0&&n.jsx(I,{label:t("session.DependsOn"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:(fe=(ye=i.dependees)==null?void 0:ye.edges)==null?void 0:fe.map(Oa).filter(Boolean).map(x=>{const U=new URLSearchParams(m.search);return x!=null&&x.row_id&&U.set("sessionDetail",x.row_id),n.jsx(mn,{type:"hover",to:{pathname:m.pathname,search:U.toString()},children:x==null?void 0:x.name},x==null?void 0:x.row_id)})})}),(((he=i.dependents)==null?void 0:he.count)??0)>0&&n.jsx(I,{label:t("session.DependedByOthers"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:(Fe=(ke=i.dependents)==null?void 0:ke.edges)==null?void 0:Fe.map(Qa).filter(Boolean).map(x=>{const U=new URLSearchParams(m.search);return x!=null&&x.row_id&&U.set("sessionDetail",x.row_id),n.jsx(mn,{type:"hover",to:{pathname:m.pathname,search:U.toString()},children:x==null?void 0:x.name},x==null?void 0:x.row_id)})})})]})})]}),n.jsxs(L,{direction:"column",align:"stretch",gap:"sm",children:[n.jsxs(ql,{hasDivider:!0,value:b,onChange:x=>{x==="auditLog"&&i.row_id&&!M&&D({scope:{entity:[{entityType:"SESSION",entityId:i.row_id}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:R.limit,offset:R.offset},{fetchPolicy:"store-and-network"}),A(x)},children:[n.jsx(gn,{value:"kernels",label:t("kernel.Kernels")}),i.row_id?n.jsx(gn,{value:"auditLog",label:t("auditLog.AuditLog")}):null]}),b==="kernels"&&n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:n.jsx(Ta,{kernelsFrgmt:$e((Te=i.kernel_nodes)==null?void 0:Te.edges.map(qa)),sessionFrgmtForLogModal:i})}),b==="auditLog"&&i.row_id&&n.jsx(Gl,{children:M?n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:n.jsx(ta,{queryRef:M,onReload:xe,tableSettings:{}})}):n.jsx(Le,{})})]}),n.jsx(Pa,{open:g,onCancel:()=>h(!1)}),n.jsx(va,{open:T,language:"shell",content:i.startup_command||"",title:t("session.StartupCommand"),footer:n.jsx(Wl,{variant:"primary",label:t("button.Close"),onClick:()=>{v()}}),onCancel:v}),n.jsx(Ha,{sessionId:l,open:_,onCancel:N}),n.jsx(Ba,{sessionFrgmt:i,open:F,onCancel:()=>p(!1)})]}):n.jsx(Oe,{status:"error",title:t("session.SessionNotFound"),description:l}),e[32]=b,e[33]=M,e[34]=y,e[35]=R,e[36]=c,e[37]=$,e[38]=de,e[39]=l,e[40]=le,e[41]=D,e[42]=m,e[43]=o,e[44]=oe,e[45]=T,e[46]=g,e[47]=_,e[48]=F,e[49]=d,e[50]=xe,e[51]=W,e[52]=ae,e[53]=i,e[54]=f,e[55]=t,e[56]=v,e[57]=N,e[58]=S,e[59]=Z):Z=e[59],Z};function Ua(a){return a.remaining}function Oa(a){return a==null?void 0:a.node}function Qa(a){return a==null?void 0:a.node}function qa(a){return a==null?void 0:a.node}const ns=({sessionId:a,open:e=!1,onClose:l,project:s})=>{const{t:r}=Ae();He();const[d,t]=j.useTransition(),[o,u]=Ln(),m=vn(),{sessionDetailDrawerFrgmt:c,createdAt:S}=m.state||{},y=P.useFragment($n,c),k=j.useMemo(()=>S&&ee().diff(ee(S),"second")<60?y:null,[]);return n.jsx(na,{open:e,onClose:l,side:"end",size:800,title:r("session.SessionInfo"),extra:n.jsx(la,{settingId:"session-detail",defaultAutoUpdateDelay:1e4,loading:d,value:o,onChange:f=>{t(()=>{u(f)})}}),children:n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:a&&n.jsx(za,{id:a,fetchKey:o,sessionFrgmt:k,project:s})})})};export{ma as B,ns as S,Na as a,Pn as c,ca as n,ua as o,ba as u};
//# sourceMappingURL=SessionDetailDrawer-CHJu8GbK.js.map
