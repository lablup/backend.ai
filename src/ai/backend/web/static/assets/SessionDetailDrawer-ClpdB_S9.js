import{al as be,dM as Jn,j as n,i as ue,bV as Zn,ft as el,aA as en,r as V,ah as fn,aT as $e,aZ as hn,t as ee,s as Ue,aj as nl,aq as qe,l as j,cI as Fn,a0 as ll,em as al,am as He,fs as sn,a2 as R,V as kn,a8 as Ge,gm as sl,u as Ae,c as L,K as Ee,dN as bn,aR as Xe,aQ as tl,en as tn,ao as il,gn as rl,go as ol,el as xn,a as ze,dQ as dl,bq as Pe,C as ul,gp as cl,aG as ml,F as rn,E as gl,X as pl,gq as _n,gr as Sl,dO as yl,gs as fl,B as hl,gt as Oe,gu as Fl,a$ as jn,e as Kn,M as N,gv as Cn,dp as kl,dn as bl,g as In,ab as xl,aV as Le,aN as Nn,a7 as on,aX as Ln,aS as _l,aO as jl,dY as Kl,bl as Cl,ac as An,bF as dn,gl as Il,ea as Nl,gw as vn,d1 as Ll,ck as un,v as Qe,gx as Al,d as vl,gy as Tl,cK as cn,gz as wl,gA as El,gB as Ml,f1 as Bl,T as Dl,q as Rl,gC as Vl,gD as Pl,gE as $l,eB as zl,cG as Hl,gF as Ul,dA as mn,dy as Ol,dx as gn,cr as Ql,at as ql,bh as Gl,bB as Wl,bW as Xl,c0 as Yl,cj as Jl,dz as Zl,dF as ea}from"./index-Bg9dLa8r.js";import{S as na}from"./scroll-text-Db3E17ba.js";import{o as la}from"./orderBy-QT1Hxfy3.js";import{F as Tn}from"./FolderLink-QnkTdekF.js";import{z as aa}from"./zip-Be93NaQ4.js";import{S as sa,a as ta}from"./ScopedAuditLog-CzRvOeE_.js";import{B as ia}from"./BAIGraphQLPropertyFilter-CsaKfYKW.js";import{R as ra}from"./rotate-ccw-clock-CSoqZrbz.js";const oa=(a,e=/(<br\s*\/?>|\n)/)=>be(Jn(a,e),(l,t)=>l.match(e)?n.jsx("br",{},t):l),wn={SUCCESS:"success",FAILURE:"error",STALE:"default",NEED_RETRY:"warning",EXPIRED:"error",GIVE_UP:"error",SKIPPED:"default"},da=a=>{"use memo";const e=ue.c(12);let l,t;e[0]!==a?({result:t,...l}=a,e[0]=a,e[1]=l,e[2]=t):(l=e[1],t=e[2]);let r;e[3]!==t?(r=t?Zn(wn,t):void 0,e[3]=t,e[4]=r):r=e[4];const d=r;let s;e[5]!==l.style?(s={whiteSpace:"nowrap",...l.style},e[5]=l.style,e[6]=s):s=e[6];let o;return e[7]!==l||e[8]!==t||e[9]!==d||e[10]!==s?(o=n.jsx(el,{...l,color:d,text:t,style:s}),e[7]=l,e[8]=t,e[9]=d,e[10]=s,e[11]=o):o=e[11],o},En={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null}],type:"SessionSchedulingHistory",abstractKey:null};En.hash="a52af4f53e01beb70d74f67b151aa5e0";const Ze=[];[...Ze,...Ze.map(a=>`-${a}`)];const Ne=a=>nl(Ze,a),ua=a=>{"use memo";const e=ue.c(23);let l,t,r,d,s;e[0]!==a?({schedulingHistoryFrgmt:d,disableSorter:t,customizeColumns:l,onChangeOrder:r,...s}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d,e[5]=s):(l=e[1],t=e[2],r=e[3],d=e[4],s=e[5]);const{t:o}=en();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=En,e[6]=u):u=e[6];const m=V.useFragment(u,d);let c;if(e[7]!==l||e[8]!==t||e[9]!==o){let h;e[11]!==t?(h=p=>t?qe(p,"sorter"):p,e[11]=t,e[12]=h):h=e[12];const k=be(fn([{dataIndex:"updatedAt",title:o("comp:BAISchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:ca,sorter:Ne("updated_at")},{dataIndex:"createdAt",title:o("comp:BAISchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:ma,sorter:Ne("created_at")},{dataIndex:"phase",title:o("comp:BAISchedulingHistoryNodes.Phase"),key:"phase",sorter:Ne("phase")},{dataIndex:"result",title:o("comp:BAISchedulingHistoryNodes.Result"),key:"result",render:ga,sorter:Ne("result")},{key:"fromStatus",title:o("comp:BAISchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Ne("from_status")},{key:"toStatus",title:o("comp:BAISchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Ne("to_status")},{dataIndex:"attempts",title:o("comp:BAISchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Ne("attempts")},{key:"message",title:o("comp:BAISchedulingHistoryNodes.Message"),dataIndex:"message",onCell:pa,render:Sa,sorter:Ne("message")}]),h);c=l?l(k):k,e[7]=l,e[8]=t,e[9]=o,e[10]=c}else c=e[10];const S=c;let y;e[13]===Symbol.for("react.memo_cache_sentinel")?(y={x:"max-content"},e[13]=y):y=e[13];let F;e[14]!==m?(F=$e(m),e[14]=m,e[15]=F):F=e[15];let f;e[16]!==r?(f=h=>{r==null||r(h||null)},e[16]=r,e[17]=f):f=e[17];let g;return e[18]!==S||e[19]!==F||e[20]!==f||e[21]!==s?(g=n.jsx(hn,{scroll:y,rowKey:"id",dataSource:F,columns:S,onChangeOrder:f,...s}),e[18]=S,e[19]=F,e[20]=f,e[21]=s,e[22]=g):g=e[22],g};function ca(a){return n.jsx("span",{children:ee(a).format("ll LTS")})}function ma(a){return n.jsx("span",{children:ee(a).format("ll LTS")})}function ga(a,e){const l=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(da,{result:l})}function pa(){return{style:{maxWidth:500}}}function Sa(a,e){return e.message?n.jsx(Ue,{title:e.message,style:{width:"100%"},children:oa(e.message)}):"-"}const Mn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryNodesFragment"}],type:"SessionSchedulingHistory",abstractKey:null};Mn.hash="e369227c362b363c91d9f366ac98634d";const ya="errors-only",fa=a=>!He(a.subSteps),Ye=(a,e,l)=>e==="expand-all"?a.filter(l).map(t=>t.id):e==="collapse-all"?[]:a.filter(t=>l(t)&&t.result!=="SUCCESS").map(t=>t.id),ha=(a,e)=>{"use memo";const l=ue.c(28),{t}=en(),r=(e==null?void 0:e.mode)??ya;let d;l[0]!==e?(d=_=>e!=null&&e.isExpandable?e.isExpandable(_):fa(_),l[0]=e,l[1]=d):d=l[1];const s=d;let o;l[2]!==a||l[3]!==s||l[4]!==r?(o=()=>Ye(a,r,s),l[2]=a,l[3]=s,l[4]=r,l[5]=o):o=l[5];const[u,m]=j.useState(o);let c;if(l[6]!==a||l[7]!==s){let _;l[9]!==s?(_=w=>`${w.id}:${w.result??""}:${s(w)?1:0}`,l[9]=s,l[10]=_):_=l[10],c=a.map(_).join("|"),l[6]=a,l[7]=s,l[8]=c}else c=l[8];const S=c,[y,F]=j.useState(S),[f,g]=j.useState(r);(S!==y||r!==f)&&(F(S),g(r),m(Ye(a,r,s)));let h;l[11]!==a||l[12]!==s?(h=a.filter(s).map(Fa),l[11]=a,l[12]=s,l[13]=h):h=l[13];const k=h;let p;l[14]===Symbol.for("react.memo_cache_sentinel")?(p=_=>{m([..._])},l[14]=p):p=l[14];const K=p;let b;if(l[15]!==a||l[16]!==s||l[17]!==e||l[18]!==t){const _={"expand-all":t("comp:BAITable.ExpandAll"),"collapse-all":t("comp:BAITable.CollapseAll"),"errors-only":t("comp:BAITable.ExpandErrorsOnly")},w=I=>{var M;m(Ye(a,I,s)),(M=e==null?void 0:e.onModeChange)==null||M.call(e,I)};b=["expand-all","collapse-all","errors-only"].map(I=>({label:_[I],onClick:()=>w(I)})),l[15]=a,l[16]=s,l[17]=e,l[18]=t,l[19]=b}else b=l[19];const A=b;let T;l[20]!==k.length||l[21]!==A||l[22]!==t?(T=k.length>0?n.jsx(Fn,{justify:"center",children:n.jsx(ll,{items:A,button:{variant:"ghost",size:"sm",isIconOnly:!0,icon:n.jsx(al,{size:"1em"}),label:t("comp:BAITable.ExpandOptions"),tooltip:t("comp:BAITable.ExpandOptions")},hasChevron:!1})}):null,l[20]=k.length,l[21]=A,l[22]=t,l[23]=T):T=l[23];const C=T;let v;return l[24]!==C||l[25]!==u||l[26]!==r?(v={mode:r,expandedRowKeys:u,onExpandedRowsChange:K,expandColumnTitle:C},l[24]=C,l[25]=u,l[26]=r,l[27]=v):v=l[27],v};function Fa(a){return a.id}const Bn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAISubStepNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],type:"SubStepResultGQL",abstractKey:null};Bn.hash="b293ef89b3c67ebb0a3733e1c22f6df9";const ka="HH:mm:ss.SSS",ba=(a,e)=>{if(!a||!e)return null;const l=ee(e).diff(ee(a));if(!Number.isFinite(l)||l<0)return null;if(l<1e3)return`${Math.round(l)} ms`;if(l<6e4)return`${(l/1e3).toFixed(2)} s`;const t=Math.round(l/1e3),r=Math.floor(t/60);return r<60?`${r}m ${String(t%60).padStart(2,"0")}s`:`${Math.floor(r/60)}h ${String(r%60).padStart(2,"0")}m`},pn=a=>a.trim().toLowerCase().replace(/[\s_-]+/g,"-"),Dn=(a,e,l,t)=>e===l-1&&!!t&&pn(a.step)===pn(t),Rn=(a,e)=>{const l=$e(a);return l.filter((t,r)=>!Dn(t,r,l.length,e)).length},xa=a=>(a==null?void 0:a.replace(/\s*\n\s*/g," ").trim())||"-",_a=a=>a&&a!=="%future added value"?a:null,ja=a=>{"use memo";const e=ue.c(39);let l,t,r,d;e[0]!==a?({subStepsFrgmt:d,parentPhase:r,className:l,...t}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d):(l=e[1],t=e[2],r=e[3],d=e[4]);const{t:s}=en();let o;e[5]===Symbol.for("react.memo_cache_sentinel")?(o=Bn,e[5]=o):o=e[5];const u=V.useFragment(o,d);let m,c,S,y,F,f,g;if(e[6]!==l||e[7]!==t||e[8]!==r||e[9]!==u||e[10]!==s){const b=$e(u);e[18]!==l?(f=sn("bai-substep-panel",l),e[18]=l,e[19]=f):f=e[19],g=t,F="bai-substep-scroll",c="bai-substep-table";let A,T;e[20]===Symbol.for("react.memo_cache_sentinel")?(S=n.jsxs("colgroup",{children:[n.jsx("col",{className:"bai-substep-col-rail"}),n.jsx("col",{className:"bai-substep-col-step"}),n.jsx("col",{className:"bai-substep-col-result"}),n.jsx("col",{className:"bai-substep-col-duration"}),n.jsx("col",{className:"bai-substep-col-time"}),n.jsx("col",{className:"bai-substep-col-code"}),n.jsx("col",{})]}),T=n.jsx("th",{scope:"col"}),A=[["Step",void 0],["Result",void 0],["Duration","bai-substep-num"],["Time",void 0],["ErrorCode",void 0],["Message",void 0]],e[20]=A,e[21]=S,e[22]=T):(A=e[20],S=e[21],T=e[22]),e[23]!==s?(y=n.jsx("thead",{children:n.jsxs("tr",{children:[T,A.map(C=>{const[v,_]=C;return n.jsx("th",{scope:"col",className:_,children:n.jsx(R,{type:"supporting",weight:"medium",children:s(`comp:BAISubStepNodes.${v}`)})},v)})]})}),e[23]=s,e[24]=y):y=e[24],m=b.map((C,v)=>{const _=_a(C.result),w=Dn(C,v,b.length,r),I=ba(C.startedAt,C.endedAt);return n.jsxs("tr",{className:sn("bai-substep-row",w&&"bai-substep-row--marker"),"data-variant":_?wn[_]:"default",children:[n.jsx("td",{className:"bai-substep-rail-cell"}),n.jsx("td",{children:n.jsx(R,{type:"code",size:"sm",color:w?"secondary":"primary",children:C.step})}),n.jsx("td",{children:_?n.jsx("span",{className:"bai-substep-result",children:n.jsx(R,{type:"supporting",color:"inherit",children:_})}):null}),n.jsx("td",{className:"bai-substep-num",children:!w&&I?n.jsx(R,{type:"code",size:"sm",color:"secondary",children:I}):n.jsx(R,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:C.startedAt?n.jsx(R,{type:"code",size:"sm",color:"secondary",children:ee(C.startedAt).format(ka)}):null}),n.jsx("td",{children:C.errorCode?n.jsx("span",{className:"bai-substep-code",children:n.jsx(R,{type:"code",size:"sm",color:"secondary",children:C.errorCode})}):n.jsx(R,{type:"supporting",color:"disabled",children:"-"})}),n.jsx("td",{children:n.jsx(R,{type:"supporting",children:w?s("comp:BAISubStepNodes.ResultMarker"):xa(C.message)})})]},`${C.step}-${v}`)}),e[6]=l,e[7]=t,e[8]=r,e[9]=u,e[10]=s,e[11]=m,e[12]=c,e[13]=S,e[14]=y,e[15]=F,e[16]=f,e[17]=g}else m=e[11],c=e[12],S=e[13],y=e[14],F=e[15],f=e[16],g=e[17];let h;e[25]!==m?(h=n.jsx("tbody",{children:m}),e[25]=m,e[26]=h):h=e[26];let k;e[27]!==c||e[28]!==S||e[29]!==y||e[30]!==h?(k=n.jsxs("table",{className:c,children:[S,y,h]}),e[27]=c,e[28]=S,e[29]=y,e[30]=h,e[31]=k):k=e[31];let p;e[32]!==k||e[33]!==F?(p=n.jsx("div",{className:F,children:k}),e[32]=k,e[33]=F,e[34]=p):p=e[34];let K;return e[35]!==p||e[36]!==f||e[37]!==g?(K=n.jsx("div",{className:f,...g,children:p}),e[35]=p,e[36]=f,e[37]=g,e[38]=K):K=e[38],K},Ka=a=>{"use memo";const e=ue.c(24);let l,t,r,d;e[0]!==a?({schedulingHistoryFrgmt:d,expandMode:l,onExpandModeChange:t,...r}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d):(l=e[1],t=e[2],r=e[3],d=e[4]);let s;e[5]===Symbol.for("react.memo_cache_sentinel")?(s=Mn,e[5]=s):s=e[5];const o=V.useFragment(s,d);let u;e[6]!==o?(u=$e(o),e[6]=o,e[7]=u):u=e[7];const m=u;let c;e[8]!==l||e[9]!==t?(c={mode:l,onModeChange:t,isExpandable:Ca},e[8]=l,e[9]=t,e[10]=c):c=e[10];const{expandedRowKeys:S,onExpandedRowsChange:y,expandColumnTitle:F}=ha(m,c);let f,g;e[11]!==m?(f=p=>{var K;return Rn(((K=m.find(b=>b.id===p.id))==null?void 0:K.subSteps)??[],p.phase)>0},g=p=>{var K;return n.jsx(ja,{subStepsFrgmt:((K=m.find(b=>b.id===p.id))==null?void 0:K.subSteps)??[],parentPhase:p.phase})},e[11]=m,e[12]=f,e[13]=g):(f=e[12],g=e[13]);let h;e[14]!==F||e[15]!==S||e[16]!==y||e[17]!==f||e[18]!==g?(h={columnTitle:F,expandedRowKeys:S,onExpandedRowsChange:y,rowExpandable:f,expandedRowRender:g},e[14]=F,e[15]=S,e[16]=y,e[17]=f,e[18]=g,e[19]=h):h=e[19];let k;return e[20]!==o||e[21]!==r||e[22]!==h?(k=n.jsx(ua,{schedulingHistoryFrgmt:o,expandable:h,...r}),e[20]=o,e[21]=r,e[22]=h,e[23]=k):k=e[23],k};function Ca(a){return Rn(a.subSteps??[],a.phase)>0}const Vn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"UNSAFELazyUserEmailViewQuery",selections:[{alias:null,args:e,concreteType:"UserNode",kind:"LinkedField",name:"user_node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"6cb167705df49d003fee4ee02f1ee82e",id:null,metadata:{},name:"UNSAFELazyUserEmailViewQuery",operationKind:"query",text:`query UNSAFELazyUserEmailViewQuery(
  $uuid: String!
) {
  user_node(id: $uuid) {
    email
    id
  }
}
`}}})();Vn.hash="67caa5daf6f6559a42a344a9b5eadff6";const Ia=({uuid:a,fetchKey:e,...l})=>{const{user_node:t}=V.useLazyLoadQuery(Vn,{uuid:a?kn("UserNode",a):""},{fetchPolicy:a?e===void 0?"store-or-network":"network-only":"store-only",fetchKey:e});return(t==null?void 0:t.email)&&n.jsx(Ue,{...l,children:t==null?void 0:t.email})},Pn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailDrawerFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],type:"ComputeSessionNode",abstractKey:null};Pn.hash="eb57207016a6a8cf6abbf348456840de";const $n=(function(){var a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,e,l,t],storageKey:null}],storageKey:null},r];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionDetailContentFragment",selections:[a,e,l,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},t,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},r],storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIImageNodeSimpleTagFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"ConnectedKernelListFragment"}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:d,storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusBadgeFragment"},{args:null,kind:"FragmentSpread",name:"SessionActionButtonsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionTypeTokenFragment"},{args:null,kind:"FragmentSpread",name:"EditableSessionNameFragment"},{args:null,kind:"FragmentSpread",name:"SessionReservationFragment"},{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionUsageMonitorFragment"},{args:null,kind:"FragmentSpread",name:"ContainerCommitModalFragment"},{args:null,kind:"FragmentSpread",name:"SessionIdleChecksNodeFragment"},{args:null,kind:"FragmentSpread",name:"SessionStatusDetailModalFragment"},{args:null,kind:"FragmentSpread",name:"AppLauncherModalFragment"},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionAgentIdsFragment"},{args:null,kind:"FragmentSpread",name:"BAISessionClusterModeFragment"},{args:null,kind:"FragmentSpread",name:"SessionAccessKeyFragment"}],type:"ComputeSessionNode",abstractKey:null}})();$n.hash="6fadc80e1af29a6361c08ced0a5c11f8";const zn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},m=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],c={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},S=[{alias:null,args:null,concreteType:"ComputeSessionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,t,r,d],storageKey:null}],storageKey:null},s];return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"SessionDetailContentFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"SessionDetailContentQuery",selections:[{alias:"internalLoadedSession",args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[l,t,r,{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,concreteType:"UserNode",kind:"LinkedField",name:"owner",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},d,{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[t,r,l],storageKey:null}],storageKey:null},s],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"requested_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},o,u,{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startup_command",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:m,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:m,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},o,l],storageKey:null},l,t,{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},d,c,{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"live_stat",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependees",plural:!1,selections:S,storageKey:null},{alias:null,args:null,concreteType:"ComputeSessionConnection",kind:"LinkedField",name:"dependents",plural:!1,selections:S,storageKey:null},c,{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],storageKey:null}]},params:{cacheID:"b41be83f677a380bbb555c860b2e1e10",id:null,metadata:{},name:"SessionDetailContentQuery",operationKind:"query",text:`query SessionDetailContentQuery(
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
  ...SessionStatusBadgeFragment
  ...SessionActionButtonsFragment
  ...BAISessionTypeTokenFragment
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

fragment SessionStatusBadgeFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
}

fragment SessionStatusDetailModalFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  starts_at
  ...SessionStatusBadgeFragment
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
`}}})();zn.hash="54a57e1f9b8de6ca1ec280de81b4e986";const Na=a=>{"use memo";const e=ue.c(10);let l,t,r;e[0]!==a?({content:l,language:t,...r}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r):(l=e[1],t=e[2],r=e[3]);let d;e[4]!==l||e[5]!==t?(d=n.jsx(sl,{language:t,children:l}),e[4]=l,e[5]=t,e[6]=d):d=e[6];let s;return e[7]!==r||e[8]!==d?(s=n.jsx(Ge,{...r,children:d}),e[7]=r,e[8]=d,e[9]=s):s=e[9],s},Hn={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"ConnectedKernelListFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null}],type:"KernelNode",abstractKey:null};Hn.hash="b07dcbdb178c221c667bd2f86f43cbd5";const La=({kernelsFrgmt:a,sessionFrgmtForLogModal:e})=>{const{t:l}=Ae(),[t,r]=j.useState(),d=V.useFragment(Hn,a),s=fn([{title:l("kernel.Hostname"),dataIndex:"cluster_hostname",render:(u,m)=>n.jsxs(L,{gap:"xxs",children:[n.jsx(R,{children:u}),n.jsx(Ee,{variant:"ghost",size:"sm",icon:n.jsx(na,{}),label:l("session.SeeContainerLogs"),tooltip:l("session.SeeContainerLogs"),onClick:()=>{m.row_id&&r(m.row_id)}})]})},{title:l("kernel.Status"),dataIndex:"status",render:(u,m)=>n.jsx(n.Fragment,{children:(m==null?void 0:m.status_info)!==""?n.jsx(bn,{values:[{label:u,variant:Xe("kernel",u)},{label:(m==null?void 0:m.status_info)??"",variant:Xe("kernel",m==null?void 0:m.status_info)}]}):n.jsx(tl,{variant:Xe("kernel",u),label:u})})},{title:l("kernel.AgentId"),dataIndex:"agent_id",render:u=>He(u)?"-":n.jsx(Ue,{copyable:!0,children:u})},{title:l("kernel.KernelId"),fixed:"left",dataIndex:"row_id",render:u=>He(u)?"-":n.jsx(tn,{uuid:u})},{title:l("kernel.ContainerId"),dataIndex:"container_id",render:u=>He(u)?"-":n.jsx(tn,{uuid:u})}]),o=j.useMemo(()=>la($e(d),["cluster_role","cluster_idx"]),[d]);return n.jsxs(n.Fragment,{children:[n.jsx(hn,{scroll:{x:"max-content"},bordered:!0,rowKey:"id",columns:s,dataSource:o}),n.jsx(il,{children:n.jsx(rl,{open:!!t,sessionFrgmt:e||null,defaultKernelId:t,onCancel:()=>{r(void 0)}})})]})},Un=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"scope_id"},e={defaultValue:null,kind:"LocalArgument",name:"sessionId"},l=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"sessionId"},{kind:"Variable",name:"scope_id",variableName:"scope_id"}],concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[a,e],kind:"Fragment",metadata:null,name:"EditableSessionNameRefetchQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,a],kind:"Operation",name:"EditableSessionNameRefetchQuery",selections:l},params:{cacheID:"58d69307fe6e70d2c3409231b0279c8b",id:null,metadata:{},name:"EditableSessionNameRefetchQuery",operationKind:"query",text:`query EditableSessionNameRefetchQuery(
  $sessionId: GlobalIDField!
  $scope_id: ScopeField
) {
  compute_session_node(id: $sessionId, scope_id: $scope_id) {
    id
    name
  }
}
`}}})();Un.hash="387b0fe2d9acb6f455335434b59c3e6c";const On={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"EditableSessionNameFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"priority",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},action:"THROW"}],type:"ComputeSessionNode",abstractKey:null};On.hash="6dfb2b44bf25b8bfda2fce5ab4cedad8";const Aa=a=>{"use memo";const e=ue.c(28),{sessionFrgmt:l,level:t,editable:r,dimmed:d}=a,s=r===void 0?!1:r,o=d===void 0?!1:d,u=V.useRelayEnvironment();let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=On,e[0]=m):m=e[0];const c=V.useFragment(m,l),[S,y]=j.useState(c.name),F=ol(S),[f]=xn(),g=ze();let h;e[1]!==g||e[2]!==c.row_id?(h={mutationFn:E=>g.rename(c.row_id,E)},e[1]=g,e[2]=c.row_id,e[3]=h):h=e[3];const k=dl(h),{t:p}=Ae(),{message:K}=pl.useApp(),[b,A]=j.useState(!1),[T,C]=j.useState(!1);let v;e[4]===Symbol.for("react.memo_cache_sentinel")?(v=["RESTARTING","PREPARING","PREPARED","CREATING","PULLING"],e[4]=v):v=e[4];const _=!v.includes(c.status||""),w=s&&f.uuid===c.user_id&&_,I=k.isPending||S!==c.name,M=k.isPending||S!==c.name?S:c.name,B=o||I;let P;e[5]!==T||e[6]!==M||e[7]!==B||e[8]!==b||e[9]!==w||e[10]!==I||e[11]!==t||e[12]!==p?(P=(!b||I)&&n.jsxs(Fn,{gap:1,align:"center",children:[t?n.jsx(Pe,{level:t,color:B?"disabled":void 0,children:M}):n.jsx(R,{color:B?"disabled":void 0,children:M}),n.jsx(Ee,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:T?n.jsx(ul,{"aria-hidden":!0}):n.jsx(cl,{"aria-hidden":!0}),label:p("sourceCodeViewer.Copy"),tooltip:p("sourceCodeViewer.Copy"),isDisabled:T,onClick:()=>{var E;(E=navigator.clipboard)==null||E.writeText(M??""),C(!0),setTimeout(()=>C(!1),1500)}}),w&&!I&&n.jsx(Ee,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(ml,{"aria-hidden":!0}),label:p("button.Edit"),tooltip:p("button.Edit"),onClick:()=>A(!0)})]}),e[5]=T,e[6]=M,e[7]=B,e[8]=b,e[9]=w,e[10]=I,e[11]=t,e[12]=p,e[13]=P):P=e[13];let D;e[14]!==b||e[15]!==I||e[16]!==K||e[17]!==u||e[18]!==k||e[19]!==c.id||e[20]!==c.name||e[21]!==c.project_id||e[22]!==p||e[23]!==F?(D=b&&!I&&n.jsx(rn,{onFinish:E=>{A(!1),y(E.sessionName),k.mutate(E.sessionName,{onSuccess:()=>{V.fetchQuery(u,Un,{sessionId:c.id,scope_id:`project:${c.project_id}`}).toPromise().catch()},onError:()=>{c.name!==E.sessionName&&K.error(p("session.FailToRenameSession"))}})},initialValues:{sessionName:c.name},style:{flex:1},children:n.jsx(rn.Item,{name:"sessionName",rules:F,children:n.jsx(gl,{label:p("session.SessionName"),size:"lg",hasAutoFocus:!0,onKeyDown:E=>{E.key==="Escape"&&(E.stopPropagation(),A(!1))}})})}),e[14]=b,e[15]=I,e[16]=K,e[17]=u,e[18]=k,e[19]=c.id,e[20]=c.name,e[21]=c.project_id,e[22]=p,e[23]=F,e[24]=D):D=e[24];let z;return e[25]!==P||e[26]!==D?(z=n.jsxs(n.Fragment,{children:[P,D]}),e[25]=P,e[26]=D,e[27]=z):z=e[27],z},Qn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionIdleChecksNodeFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionReclamationStatusCellFragment"}],type:"ComputeSessionNode",abstractKey:null};Qn.hash="cd0692b3021358f17c5abea99afd29d2";const va={warningText:{kMwMTN:"webuis3pv69",$$css:!0}};function Ta(a,e){var l;return e==="remaining"?!a.remaining||a.remaining<3600?Oe("red"):a.remaining<3600*4?Oe("orange"):Oe("green"):a.extra&&(!a.remaining||a.remaining<3600*4)?Oe((l=Fl(a.extra.resources,a.extra.thresholds_check_operator))==null?void 0:l.color):"neutral"}const wa=a=>{"use memo";const e=ue.c(24),{checkKey:l,value:t,sessionFrgmt:r}=a,{t:d}=Ae(),s=t.remaining??0;let o;e[0]!==d?(o=b=>d(b==="network_timeout"?"session.NetworkIdleTimeout":b==="session_lifetime"?"session.MaxSessionLifetime":"session.UtilizationIdleTimeout"),e[0]=d,e[1]=o):o=e[1];const u=o;let m;e[2]!==d?(m=b=>d(b==="expire_after"?"session.ExpiresAfter":"session.GracePeriod"),e[2]=d,e[3]=m):m=e[3];const c=m,S=l==="utilization"?"utilization":"remaining";let y;e[4]!==S||e[5]!==t?(y=Ta(t,S),e[4]=S,e[5]=t,e[6]=y):y=e[6];const F=y;let f;e[7]!==s?(f=ee().add(s,"second").toISOString(),e[7]=s,e[8]=f):f=e[8];const g=f;let h;e[9]===Symbol.for("react.memo_cache_sentinel")?(h={flex:1},e[9]=h):h=e[9];let k;e[10]!==l||e[11]!==u||e[12]!==r?(k=n.jsx(L,{gap:"xxs",children:l==="utilization"?n.jsx(Sl,{sessionFrgmt:r}):n.jsx(R,{children:u(l)})}),e[10]=l,e[11]=u,e[12]=r,e[13]=k):k=e[13];let p;e[14]!==F||e[15]!==g||e[16]!==c||e[17]!==s||e[18]!==d||e[19]!==t.remaining_time_type?(p=s>=0?n.jsxs(L,{gap:"xxs",align:"center",children:[n.jsx(yl,{delay:1e3,callback:()=>ee(g).diff()>0?fl(ee().toISOString(),g):"00:00:00",render:b=>n.jsx(bn,{values:[{label:c(t.remaining_time_type),variant:F},{label:b,variant:F}]})}),t.remaining_time_type==="grace_period"&&n.jsx(hl,{title:n.jsx("div",{style:{whiteSpace:"pre-line"},children:d("session.GracePeriodTooltip")})})]}):n.jsx(R,{xstyle:va.warningText,children:d("session.ReclamationStatusChecking")}),e[14]=F,e[15]=g,e[16]=c,e[17]=s,e[18]=d,e[19]=t.remaining_time_type,e[20]=p):p=e[20];let K;return e[21]!==k||e[22]!==p?(K=n.jsxs(L,{style:h,direction:"column",align:"stretch",children:[k,p]}),e[21]=k,e[22]=p,e[23]=K):K=e[23],K},Ea=({sessionNodeFrgmt:a=null,direction:e="row"})=>{const l=V.useFragment(Qn,a),t=_n(l==null?void 0:l.idle_checks,{fallbackValue:{}});return n.jsx(L,{direction:e,align:"stretch",gap:"sm",children:be(t,(r,d)=>r.remaining?n.jsx(wa,{checkKey:d,value:r,sessionFrgmt:l},d):null)})},qn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"SessionStatusDetailModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionStatusBadgeFragment"}],type:"ComputeSessionNode",abstractKey:null};qn.hash="fc37c9c14fb1727ab998612da8eb5eff";const Sn={predicateMsg:{ks0D6T:"webui1dc814f",$$css:!0}},Ma=({sessionFrgmt:a,...e})=>{var o,u,m,c,S,y,F,f;const{t:l}=Ae(),t=jn(),r=ze(),d=V.useFragment(qn,a),s=JSON.parse(d.status_data||"{}");return n.jsx(Ge,{title:n.jsxs(n.Fragment,{children:[l("session.StatusInfo"),n.jsx("span",{style:{fontWeight:"normal"},children:n.jsx(Cn,{sessionFrgmt:d,showInfo:!0,showQueuePosition:!1})})]}),footer:null,width:450,...e,children:n.jsxs(Kn,{columns:"single",children:[n.jsx(N,{label:l("session.SessionName"),children:n.jsx(Ue,{copyable:!0,ellipsis:{tooltip:!0},children:d.name??""})}),s!=null&&s.kernel?n.jsx(N,{label:l("session.KernelExitCode"),children:s.kernel.exit_code}):null,s!=null&&s.session?n.jsx(N,{label:l("session.SessionStatus"),children:(o=s.session)==null?void 0:o.status}):null,s!=null&&s.scheduler?n.jsxs(n.Fragment,{children:[n.jsx(N,{label:l("session.LastTry"),children:ee((u=s.scheduler)==null?void 0:u.last_try).format("lll")}),n.jsx(N,{label:l("session.TotalRetries"),children:(m=s.scheduler)==null?void 0:m.retries}),((c=s.scheduler)==null?void 0:c.msg)&&n.jsx(N,{label:l("session.Message"),children:(S=s.scheduler)==null?void 0:S.msg}),n.jsx(N,{label:l("session.PredicateChecks"),children:n.jsxs(L,{direction:"column",gap:"md",align:"stretch",children:[be((y=s.scheduler)==null?void 0:y.failed_predicates,g=>n.jsxs(L,{gap:"xs",align:"start",children:[n.jsx(kl,{style:{color:"var(--color-error)",marginTop:4,flexShrink:0},size:16}),n.jsxs(L,{direction:"column",align:"stretch",children:[n.jsx(R,{children:g.name}),n.jsx(R,{color:"secondary",xstyle:Sn.predicateMsg,children:g.msg})]})]},g.name)),be((F=s.scheduler)==null?void 0:F.passed_predicates,g=>n.jsxs(L,{gap:"xs",align:"start",children:[n.jsx(bl,{style:{color:"var(--color-success)",marginTop:4,flexShrink:0},size:16}),n.jsxs(L,{direction:"column",align:"stretch",children:[n.jsx(R,{children:g.name}),n.jsx(R,{color:"secondary",xstyle:Sn.predicateMsg,children:g.msg})]})]},g.name))]})})]}):null,s!=null&&s.error?be(((f=s==null?void 0:s.error)==null?void 0:f.collection)??s,g=>n.jsxs(j.Fragment,{children:[(t==="superadmin"||!r._config.hideAgents)&&(g==null?void 0:g.agent_id)&&n.jsx(N,{label:l("session.AgentId"),children:g==null?void 0:g.agent_id}),n.jsx(N,{label:l("dialog.error.Error"),children:n.jsx(In,{color:"red",label:g.name})}),n.jsx(N,{label:l("session.Message"),children:g.repr}),(g==null?void 0:g.traceback)&&n.jsx(N,{label:l("session.Traceback"),children:n.jsx("pre",{children:g==null?void 0:g.traceback})})]},g.name)):null]})})},Ba=({...a})=>{const{t:e}=Ae(),{token:l}=xl.useToken();return n.jsxs(Ge,{title:e("session.ReclamationStatus"),footer:null,width:700,...a,children:[n.jsx(R,{children:e("session.IdleChecksDesc")}),n.jsx(Pe,{level:5,children:e("session.MaxSessionLifetime")}),n.jsx("p",{children:e("session.MaxSessionLifetimeDesc")}),n.jsx(Pe,{level:5,children:e("session.NetworkIdleTimeout")}),n.jsx("p",{children:e("session.NetworkIdleTimeoutDesc")}),n.jsx(Pe,{level:5,children:e("session.UtilizationIdleTimeout")}),n.jsx("p",{children:e("session.UtilizationIdleTimeoutDesc")}),n.jsxs(L,{direction:"column",align:"stretch",style:{marginLeft:l.marginMD},children:[n.jsx(Pe,{level:5,style:{margin:0},children:e("session.GracePeriod")}),n.jsx("p",{children:e("session.GracePeriodDesc")}),n.jsx(Pe,{level:5,style:{margin:0},children:e("session.UtilizationThreshold")}),n.jsx("p",{children:e("session.UtilizationThresholdDesc")})]})]})},Gn=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"uuid"}],e=[{kind:"Variable",name:"id",variableName:"uuid"}],l={alias:null,args:null,kind:"ScalarField",name:"mounts",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"MountedVFolderLinksQuery",selections:[{alias:"legacy_session",args:e,concreteType:"ComputeSession",kind:"LinkedField",name:"compute_session",plural:!1,selections:[l],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"MountedVFolderLinksQuery",selections:[{alias:"legacy_session",args:e,concreteType:"ComputeSession",kind:"LinkedField",name:"compute_session",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"9025af1e54e75a0d3041d0e12150939c",id:null,metadata:{},name:"MountedVFolderLinksQuery",operationKind:"query",text:`query MountedVFolderLinksQuery(
  $uuid: UUID!
) {
  legacy_session: compute_session(id: $uuid) {
    mounts
    id
  }
}
`}}})();Gn.hash="f1e2ef43ac11c6b980313ddac8cd1ec9";const Wn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksLegacyLazyFolderLinkFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null}],type:"ComputeSessionNode",abstractKey:null};Wn.hash="72fda7ec47bcaa5e7fc83cbaabc822c6";const Xn={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"MountedVFolderLinksFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"MountedVFolderLinksLegacyLazyFolderLinkFragment"}],type:"ComputeSessionNode",abstractKey:null};Xn.hash="f26bc04640693f4094c9a072011821b0";const Da=({sessionFrgmt:a})=>{var t;const e=ze(),l=V.useFragment(Xn,a);return e.supports("vfolder_nodes_in_session_node")?be((t=l.vfolder_nodes)==null?void 0:t.edges,(r,d)=>(r==null?void 0:r.node)&&n.jsx(Tn,{vfolderNodeFragment:r.node},`mounted-vfolder-${d}`)):l.row_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ra,{sessionFrgmt:l})}):null},Ra=({sessionFrgmt:a})=>{var r;const e=ze(),l=V.useFragment(Wn,a),{legacy_session:t}=V.useLazyLoadQuery(Gn,{uuid:l.row_id||""},{fetchPolicy:l.row_id?"store-and-network":"store-only"});return e.supports("vfolder-mounts")?be(aa(t==null?void 0:t.mounts,l==null?void 0:l.vfolder_mounts),d=>{const[s,o]=d;return n.jsx(Tn,{folderId:o??"",folderName:s??"",showIcon:!0},o)}):(r=t==null?void 0:t.mounts)==null?void 0:r.join(", ")},Yn=(function(){var a={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},l={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r={defaultValue:null,kind:"LocalArgument",name:"scope"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[a,e,l,t,r],kind:"Fragment",metadata:null,name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[s,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAISchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[r,a,t,e,l],kind:"Operation",name:"SessionSchedulingHistoryModalQuery",selections:[{alias:null,args:d,concreteType:"SessionSchedulingHistoryConnection",kind:"LinkedField",name:"sessionScopedSchedulingHistories",plural:!1,selections:[s,{alias:null,args:null,concreteType:"SessionSchedulingHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionSchedulingHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},o,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},o,{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},u,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"1bfe7bc2611f279e70c35d22c11fb631",id:null,metadata:{},name:"SessionSchedulingHistoryModalQuery",operationKind:"query",text:`query SessionSchedulingHistoryModalQuery(
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
`}}})();Yn.hash="6221439d9cf111e4683277c5e89974db";const Va=a=>{"use memo";var x,U,Ke,we;const e=ue.c(116);let l,t,r,d,s;e[0]!==a?({open:d,loading:l,sessionId:s,onCancel:r,...t}=a,e[0]=a,e[1]=l,e[2]=t,e[3]=r,e[4]=d,e[5]=s):(l=e[1],t=e[2],r=e[3],d=e[4],s=e[5]);const{t:o}=Ae(),[u,m]=Nn(),[c,S]=j.useState(),[y,F]=j.useState("-updatedAt"),[f,g]=on("schedulingHistoryExpandMode"),[h,k]=on("table_column_overrides.SessionSchedulingHistory");let p;e[6]===Symbol.for("react.memo_cache_sentinel")?(p={current:1,pageSize:10},e[6]=p):p=e[6];const{baiPaginationOption:K,tablePaginationOption:b,setTablePaginationOption:A}=Ln(p),T=j.useDeferredValue(d),C=j.useDeferredValue(u),v=j.useDeferredValue(c),_=j.useDeferredValue(y),w=j.useDeferredValue(K.offset),I=j.useDeferredValue(K.limit);let M;e[7]===Symbol.for("react.memo_cache_sentinel")?(M=Yn,e[7]=M):M=e[7];let B;e[8]!==s?(B={sessionId:s},e[8]=s,e[9]=B):B=e[9];const P=v??void 0;let D;e[10]!==_?(D=_l(_)??[{field:"UPDATED_AT",direction:"DESC"}],e[10]=_,e[11]=D):D=e[11];let z;e[12]!==I||e[13]!==w||e[14]!==B||e[15]!==P||e[16]!==D?(z={scope:B,filter:P,orderBy:D,limit:I,offset:w},e[12]=I,e[13]=w,e[14]=B,e[15]=P,e[16]=D,e[17]=z):z=e[17];const E=T?"network-only":"store-only";let xe;e[18]!==C||e[19]!==E?(xe={fetchKey:C,fetchPolicy:E},e[18]=C,e[19]=E,e[20]=xe):xe=e[20];const ce=V.useLazyLoadQuery(M,z,xe);let H;e[21]!==o?(H=o("session.SessionSchedulingHistory"),e[21]=o,e[22]=H):H=e[22];const _e=l||T!==d;let ne;e[23]!==A?(ne=Ce=>{S(Ce),A({current:1})},e[23]=A,e[24]=ne):ne=e[24];let O;e[25]!==o?(O=o("session.ID"),e[25]=o,e[26]=O):O=e[26];let je;e[27]!==O?(je={key:"id",propertyLabel:O,type:"uuid",fixedOperator:"equals"},e[27]=O,e[28]=je):je=e[28];let Q;e[29]!==o?(Q=o("session.Phase"),e[29]=o,e[30]=Q):Q=e[30];let i;e[31]!==Q?(i={key:"phase",propertyLabel:Q,type:"string",fixedOperator:"contains"},e[31]=Q,e[32]=i):i=e[32];let q;e[33]!==o?(q=o("session.Result"),e[33]=o,e[34]=q):q=e[34];let le;e[35]===Symbol.for("react.memo_cache_sentinel")?(le=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[35]=le):le=e[35];let ae;e[36]!==q?(ae={key:"result",propertyLabel:q,type:"enum",strictSelection:!0,options:le},e[36]=q,e[37]=ae):ae=e[37];let se;e[38]!==o?(se=o("session.FromStatus"),e[38]=o,e[39]=se):se=e[39];let te;e[40]!==se?(te={key:"fromStatus",propertyLabel:se,type:"string",valueMode:"scalar"},e[40]=se,e[41]=te):te=e[41];let G;e[42]!==o?(G=o("session.ToStatus"),e[42]=o,e[43]=G):G=e[43];let W;e[44]!==G?(W={key:"toStatus",propertyLabel:G,type:"string",valueMode:"scalar"},e[44]=G,e[45]=W):W=e[45];let ie;e[46]!==o?(ie=o("session.ErrorCode"),e[46]=o,e[47]=ie):ie=e[47];let re;e[48]!==ie?(re={key:"errorCode",propertyLabel:ie,type:"string",fixedOperator:"contains"},e[48]=ie,e[49]=re):re=e[49];let X;e[50]!==o?(X=o("session.Message"),e[50]=o,e[51]=X):X=e[51];let oe;e[52]!==X?(oe={key:"message",propertyLabel:X,type:"string",fixedOperator:"contains"},e[52]=X,e[53]=oe):oe=e[53];let Y;e[54]!==o?(Y=o("session.CreatedAt"),e[54]=o,e[55]=Y):Y=e[55];let $;e[56]!==Y?($={key:"createdAt",propertyLabel:Y,type:"datetime",defaultOperator:"after"},e[56]=Y,e[57]=$):$=e[57];let J;e[58]!==o?(J=o("session.UpdatedAt"),e[58]=o,e[59]=J):J=e[59];let ve;e[60]!==J?(ve={key:"updatedAt",propertyLabel:J,type:"datetime",defaultOperator:"after"},e[60]=J,e[61]=ve):ve=e[61];let de;e[62]!==je||e[63]!==i||e[64]!==ae||e[65]!==te||e[66]!==W||e[67]!==re||e[68]!==oe||e[69]!==$||e[70]!==ve?(de=[je,i,ae,te,W,re,oe,$,ve],e[62]=je,e[63]=i,e[64]=ae,e[65]=te,e[66]=W,e[67]=re,e[68]=oe,e[69]=$,e[70]=ve,e[71]=de):de=e[71];let Z;e[72]!==c||e[73]!==ne||e[74]!==de?(Z=n.jsx(ia,{value:c,onChange:ne,filterProperties:de}),e[72]=c,e[73]=ne,e[74]=de,e[75]=Z):Z=e[75];const Me=C!==u;let me;e[76]!==u||e[77]!==Me||e[78]!==m?(me=n.jsx(L,{children:n.jsx(jl,{value:u,onChange:m,loading:Me,autoUpdateDelay:null})}),e[76]=u,e[77]=Me,e[78]=m,e[79]=me):me=e[79];let ge;e[80]!==Z||e[81]!==me?(ge=n.jsxs(L,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,me]}),e[80]=Z,e[81]=me,e[82]=ge):ge=e[82];const Be=C!==u||v!==c||_!==y||w!==K.offset||I!==K.limit;let pe;e[83]!==A?(pe=Ce=>{F(Ce),A({current:1})},e[83]=A,e[84]=pe):pe=e[84];const De=f??void 0;let Se;e[85]!==h||e[86]!==k?(Se={columnOverrides:h,onColumnOverridesChange:k},e[85]=h,e[86]=k,e[87]=Se):Se=e[87];const Re=((x=ce.sessionScopedSchedulingHistories)==null?void 0:x.count)??0;let ye;e[88]!==A?(ye=(Ce,Ie)=>{A({current:Ce,pageSize:Ie})},e[88]=A,e[89]=ye):ye=e[89];let fe;e[90]!==Re||e[91]!==ye||e[92]!==b.current||e[93]!==b.pageSize?(fe={pageSize:b.pageSize,current:b.current,total:Re,onChange:ye},e[90]=Re,e[91]=ye,e[92]=b.current,e[93]=b.pageSize,e[94]=fe):fe=e[94];let he;e[95]!==((U=ce.sessionScopedSchedulingHistories)==null?void 0:U.edges)?(he=be((Ke=ce.sessionScopedSchedulingHistories)==null?void 0:Ke.edges,"node"),e[95]=(we=ce.sessionScopedSchedulingHistories)==null?void 0:we.edges,e[96]=he):he=e[96];let Fe;e[97]!==y||e[98]!==g||e[99]!==Be||e[100]!==pe||e[101]!==De||e[102]!==Se||e[103]!==fe||e[104]!==he?(Fe=n.jsx(Ka,{resizable:!0,loading:Be,order:y,onChangeOrder:pe,expandMode:De,onExpandModeChange:g,tableSettings:Se,pagination:fe,schedulingHistoryFrgmt:he}),e[97]=y,e[98]=g,e[99]=Be,e[100]=pe,e[101]=De,e[102]=Se,e[103]=fe,e[104]=he,e[105]=Fe):Fe=e[105];let ke;e[106]!==ge||e[107]!==Fe?(ke=n.jsxs(L,{direction:"column",align:"stretch",gap:"sm",children:[ge,Fe]}),e[106]=ge,e[107]=Fe,e[108]=ke):ke=e[108];let Te;return e[109]!==t||e[110]!==r||e[111]!==d||e[112]!==_e||e[113]!==ke||e[114]!==H?(Te=n.jsx(Ge,{title:H,loading:_e,open:d,variant:"fullscreen",footer:null,onCancel:r,...t,children:ke}),e[109]=t,e[110]=r,e[111]=d,e[112]=_e,e[113]=ke,e[114]=H,e[115]=Te):Te=e[115],Te},yn=(a,e)=>{const l=JSON.parse(a||"{}"),t=vn(e);return t?{...qe(l,t),acceleratorType:t}:l},Je=a=>Wl(Xl(JSON.parse(a||"{}"),e=>Yl(e)),e=>e===0),Pa=a=>{"use memo";var Me,me,ge,Be,pe,De,Se,Re,ye,fe,he,Fe,ke,Te;const e=ue.c(60),{id:l,fetchKey:t,sessionFrgmt:r,project:d}=a,{t:s}=Ae(),{md:o}=Kl(),{mergedResourceSlots:u}=Cl(),m=An(),[c]=xn(),S=jn(),y=ze();let F;e[0]!==y?(F=y.supports("session-scheduling-history"),e[0]=y,e[1]=F):F=e[1];const f=F,[g,h]=j.useState(!1),[k,p]=j.useState(!1),K="current",[b,A]=j.useState("kernels"),[T,C]=dn(!1),{toggle:v}=C,[_,w]=dn(!1),{toggle:I}=w,[M,B]=V.useQueryLoader(sa);let P;e[2]===Symbol.for("react.memo_cache_sentinel")?(P={current:1,pageSize:10},e[2]=P):P=e[2];const{baiPaginationOption:D,setTablePaginationOption:z}=Ln(P);let E;e[3]!==B||e[4]!==z?(E=(x,U)=>{const Ke=x.limit??10;z({pageSize:Ke,current:x.offset?Math.floor(x.offset/Ke)+1:1}),B(x,U)},e[3]=B,e[4]=z,e[5]=E):E=e[5];const xe=E;let ce;e[6]===Symbol.for("react.memo_cache_sentinel")?(ce=zn,e[6]=ce):ce=e[6];let H;e[7]!==l?(H=kn("ComputeSessionNode",l),e[7]=l,e[8]=H):H=e[8];let _e;e[9]!==H?(_e={id:H},e[9]=H,e[10]=_e):_e=e[10];const ne=t===Gl?r?"store-only":"store-and-network":"network-only";let O;e[11]!==t||e[12]!==ne?(O={fetchPolicy:ne,fetchKey:t},e[11]=t,e[12]=ne,e[13]=O):O=e[13];const{internalLoadedSession:je}=V.useLazyLoadQuery(ce,_e,O);let Q;e[14]===Symbol.for("react.memo_cache_sentinel")?(Q=$n,e[14]=Q):Q=e[14];const i=V.useFragment(Q,je||r);let q;e[15]===Symbol.for("react.memo_cache_sentinel")?(q={fallbackValue:{}},e[15]=q):q=e[15];const le=Il(Nl(_n(i==null?void 0:i.idle_checks,q)).map($a).filter(Boolean)),ae=i==null?void 0:i.project_id,se=i==null?void 0:i.requested_slots,te=i==null?void 0:i.tag;let G;e[16]!==se||e[17]!==te?(G=yn(se,te),e[16]=se,e[17]=te,e[18]=G):G=e[18];const W=G,ie=i==null?void 0:i.occupied_slots,re=i==null?void 0:i.tag;let X;e[19]!==ie||e[20]!==re?(X=yn(ie,re),e[19]=ie,e[20]=re,e[21]=X):X=e[21];const oe=X;let Y;e[22]!==(i==null?void 0:i.occupied_slots)?(Y=He(Je(i==null?void 0:i.occupied_slots)),e[22]=i==null?void 0:i.occupied_slots,e[23]=Y):Y=e[23];const $=!Y;let J;if(e[24]!==$||e[25]!==u||e[26]!==(i==null?void 0:i.occupied_slots)||e[27]!==(i==null?void 0:i.requested_slots)||e[28]!==(i==null?void 0:i.tag)){const x=vn(i==null?void 0:i.tag)??"",U=qe(Je(i==null?void 0:i.requested_slots),x),Ke=qe(Je(i==null?void 0:i.occupied_slots),x);let we;e[30]!==u?(we=(Ie,We)=>{var ln,an;const Ve=(ln=u==null?void 0:u[Ie])==null?void 0:ln.number_format,nn=(Ve==null?void 0:Ve.round_length)||0;return Ve!=null&&Ve.binary?Number((an=Jl(We.toString(),"g",2,!0))==null?void 0:an.numberFixed):nn>0?Number(We.toFixed(nn)):We},e[30]=u,e[31]=we):we=e[31];const Ce=we;J=$?Ll(un(U),un(Ke)).filter(Ie=>Ce(Ie,Ke[Ie]??0)<Ce(Ie,U[Ie]??0)):[],e[24]=$,e[25]=u,e[26]=i==null?void 0:i.occupied_slots,e[27]=i==null?void 0:i.requested_slots,e[28]=i==null?void 0:i.tag,e[29]=J}else J=e[29];const de=J.length>0;let Z;return e[32]!==b||e[33]!==M||e[34]!==y||e[35]!==D||e[36]!==c||e[37]!==$||e[38]!==de||e[39]!==l||e[40]!==le||e[41]!==B||e[42]!==m||e[43]!==o||e[44]!==oe||e[45]!==T||e[46]!==g||e[47]!==_||e[48]!==k||e[49]!==d||e[50]!==xe||e[51]!==W||e[52]!==ae||e[53]!==i||e[54]!==f||e[55]!==s||e[56]!==v||e[57]!==I||e[58]!==S?(Z=i?n.jsxs(L,{direction:"column",gap:"lg",align:"stretch",children:[d!==null&&ae!==d.id&&n.jsx(Qe,{status:"warning",title:s("session.NotInProject")}),c.uuid!==(i==null?void 0:i.user_id)&&n.jsx(Qe,{status:"warning",title:s("session.AnotherUserSession")}),le&&le<3600&&n.jsx(Qe,{status:"warning",title:s("session.IdleCheckExpirationWarning")}),n.jsxs(L,{direction:"column",gap:"sm",align:"stretch",children:[n.jsxs(L,{direction:"row",justify:"between",align:"start",style:{alignSelf:"stretch"},gap:"sm",children:[n.jsx(Aa,{sessionFrgmt:i,level:3,dimmed:["TERMINATED","CANCELLED"].includes(i.status||""),editable:!["TERMINATED","CANCELLED"].includes(i.status||"")}),n.jsx(Al,{size:"large",compact:!0,sessionFrgmt:i})]}),n.jsx(vl,{children:n.jsxs(Kn,{columns:o?2:1,children:[n.jsx(N,{label:s("session.SessionId"),children:n.jsx(Ue,{code:!0,copyable:!0,ellipsis:{tooltip:!0},children:i.row_id??""})}),(S==="admin"||S==="superadmin")&&n.jsx(N,{label:s("credential.UserID"),children:(Me=i.owner)!=null&&Me.email?i.owner.email:i.user_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ia,{uuid:i.user_id})}):"-"}),n.jsx(N,{label:s("general.AccessKey"),children:n.jsx(Tl,{sessionFrgmt:i,copyable:!0})}),n.jsx(N,{label:s("session.Status"),children:n.jsxs(L,{children:[n.jsx(Cn,{sessionFrgmt:i,showInfo:!f}),!f&&(i!=null&&i.status_data)&&(i==null?void 0:i.status_data)!=="{}"?n.jsx(Ee,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cn,{size:"1em"}),label:s("button.ClickForMoreDetails"),tooltip:s("button.ClickForMoreDetails"),onClick:()=>{p(!0)}}):null,f&&n.jsx(Ee,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(ra,{size:"1em"}),label:s("session.SessionSchedulingHistory"),tooltip:s("session.SessionSchedulingHistory"),onClick:()=>I()})]})}),n.jsx(N,{label:s("session.SessionType"),children:n.jsxs(L,{children:[n.jsx(wl,{sessionFrgmt:i}),i.type==="batch"&&i.startup_command&&n.jsx(Ee,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(cn,{size:"1em"}),label:s("session.ViewStartupCommand"),tooltip:s("session.ViewStartupCommand"),onClick:()=>v()})]})}),n.jsx(N,{label:s("session.launcher.Environments"),children:(Be=(ge=(me=i.kernel_nodes)==null?void 0:me.edges[0])==null?void 0:ge.node)!=null&&Be.image?n.jsx(El,{imageFrgmt:((Se=(De=(pe=i.kernel_nodes)==null?void 0:pe.edges[0])==null?void 0:De.node)==null?void 0:Se.image)||null}):i.row_id?n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ml,{sessionId:i.row_id})}):null}),n.jsx(N,{label:s("session.launcher.MountedFolders"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:n.jsx(Da,{sessionFrgmt:i})})}),n.jsx(N,{label:s("session.launcher.ResourceAllocation"),children:n.jsxs(L,{gap:"sm",wrap:"wrap",align:"center",children:[de&&n.jsx(Bl,{content:s("session.AllocatedLessThanRequested"),icon:n.jsx(Dl,{size:"1em",style:{color:"var(--color-warning)"}})}),n.jsx(Rl,{content:s("session.ResourceGroup"),children:n.jsx(In,{label:i.scaling_group??""})}),n.jsx(Vl,{resource:$?oe:W,comparedResource:$?W:void 0,showDividers:!0})]})}),n.jsx(N,{label:s("session.Agent"),children:n.jsx(Pl,{sessionFrgmt:i})}),n.jsx(N,{label:s("session.Reservation"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:n.jsx($l,{sessionFrgmt:i})})}),n.jsx(N,{label:s("session.ClusterMode"),children:n.jsx(zl,{sessionFrgmt:i,showSize:!0})}),y.supports("idle-checks-gql")&&i.status==="RUNNING"&&le?n.jsx(N,{label:s("session.ReclamationStatus"),children:n.jsxs(L,{gap:"xxs",align:"start",children:[n.jsx(j.Suspense,{fallback:n.jsx(Le,{variant:"input",size:"small"}),children:n.jsx(Ea,{sessionNodeFrgmt:i,direction:o?"row":"column"})}),n.jsx(Ee,{className:"bai-action-accent",variant:"ghost",size:"sm",icon:n.jsx(Hl,{size:"1em"}),label:s("button.ClickForMoreDetails"),tooltip:s("button.ClickForMoreDetails"),onClick:()=>h(!0)})]})}):null,n.jsx(N,{label:s("session.ResourceUsage"),children:n.jsx(Ul,{sessionFrgmt:i,displayTarget:K})}),(((Re=i.dependees)==null?void 0:Re.count)??0)>0&&n.jsx(N,{label:s("session.DependsOn"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:(fe=(ye=i.dependees)==null?void 0:ye.edges)==null?void 0:fe.map(za).filter(Boolean).map(x=>{const U=new URLSearchParams(m.search);return x!=null&&x.row_id&&U.set("sessionDetail",x.row_id),n.jsx(mn,{type:"hover",to:{pathname:m.pathname,search:U.toString()},children:x==null?void 0:x.name},x==null?void 0:x.row_id)})})}),(((he=i.dependents)==null?void 0:he.count)??0)>0&&n.jsx(N,{label:s("session.DependedByOthers"),children:n.jsx(L,{gap:"xs",wrap:"wrap",children:(ke=(Fe=i.dependents)==null?void 0:Fe.edges)==null?void 0:ke.map(Ha).filter(Boolean).map(x=>{const U=new URLSearchParams(m.search);return x!=null&&x.row_id&&U.set("sessionDetail",x.row_id),n.jsx(mn,{type:"hover",to:{pathname:m.pathname,search:U.toString()},children:x==null?void 0:x.name},x==null?void 0:x.row_id)})})})]})})]}),n.jsxs(L,{direction:"column",align:"stretch",gap:"sm",children:[n.jsxs(Ol,{hasDivider:!0,value:b,onChange:x=>{x==="auditLog"&&i.row_id&&!M&&B({scope:{entity:[{entityType:"SESSION",entityId:i.row_id}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:D.limit,offset:D.offset},{fetchPolicy:"store-and-network"}),A(x)},children:[n.jsx(gn,{value:"kernels",label:s("kernel.Kernels")}),i.row_id?n.jsx(gn,{value:"auditLog",label:s("auditLog.AuditLog")}):null]}),b==="kernels"&&n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:n.jsx(La,{kernelsFrgmt:$e((Te=i.kernel_nodes)==null?void 0:Te.edges.map(Ua)),sessionFrgmtForLogModal:i})}),b==="auditLog"&&i.row_id&&n.jsx(Ql,{children:M?n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:n.jsx(ta,{queryRef:M,onReload:xe,tableSettings:{}})}):n.jsx(Le,{})})]}),n.jsx(Ba,{open:g,onCancel:()=>h(!1)}),n.jsx(Na,{open:T,language:"shell",content:i.startup_command||"",title:s("session.StartupCommand"),footer:n.jsx(ql,{variant:"primary",label:s("button.Close"),onClick:()=>{v()}}),onCancel:v}),n.jsx(Va,{sessionId:l,open:_,onCancel:I}),n.jsx(Ma,{sessionFrgmt:i,open:k,onCancel:()=>p(!1)})]}):n.jsx(Qe,{status:"error",title:s("session.SessionNotFound"),description:l}),e[32]=b,e[33]=M,e[34]=y,e[35]=D,e[36]=c,e[37]=$,e[38]=de,e[39]=l,e[40]=le,e[41]=B,e[42]=m,e[43]=o,e[44]=oe,e[45]=T,e[46]=g,e[47]=_,e[48]=k,e[49]=d,e[50]=xe,e[51]=W,e[52]=ae,e[53]=i,e[54]=f,e[55]=s,e[56]=v,e[57]=I,e[58]=S,e[59]=Z):Z=e[59],Z};function $a(a){return a.remaining}function za(a){return a==null?void 0:a.node}function Ha(a){return a==null?void 0:a.node}function Ua(a){return a==null?void 0:a.node}const Za=({sessionId:a,open:e=!1,onClose:l,project:t})=>{const{t:r}=Ae();ze();const[d,s]=j.useTransition(),[o,u]=Nn(),m=An(),{sessionDetailDrawerFrgmt:c,createdAt:S}=m.state||{},y=V.useFragment(Pn,c),F=j.useMemo(()=>S&&ee().diff(ee(S),"second")<60?y:null,[]);return n.jsx(Zl,{open:e,onClose:l,side:"end",size:800,title:r("session.SessionInfo"),extra:n.jsx(ea,{settingId:"session-detail",defaultAutoUpdateDelay:1e4,loading:d,value:o,onChange:f=>{s(()=>{u(f)})}}),children:n.jsx(j.Suspense,{fallback:n.jsx(Le,{}),children:a&&n.jsx(Pa,{id:a,fetchKey:o,sessionFrgmt:F,project:t})})})};export{da as B,Za as S,ja as a,Rn as c,oa as n,ha as u};
//# sourceMappingURL=SessionDetailDrawer-ClpdB_S9.js.map
