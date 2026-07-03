import{bS as lt,h as tl,ad as Kn,r as M,aB as vn,ck as ia,ar as Il,d2 as nt,b8 as Wl,i as Le,cl as sa,a6 as bl,bT as ra,ac as In,bi as On,j as n,aw as Fl,b6 as oa,cn as da,bA as Xl,N as ll,m as Dn,ca as ua,cm as ca,a$ as ma,a1 as gn,aK as Al,b5 as ql,bW as cl,bM as Pl,a3 as An,u as rl,t as Cl,A as Nl,v as zl,K as tt,cb as Cn,T as nl,am as ml,B as ie,aA as Vl,b4 as jl,z as Sl,bI as en,a7 as kl,P as Ul,F as ge,d3 as ga,aX as Mn,aZ as Ln,b7 as jn,aQ as Fn,aj as Pn,d4 as ya,a as Nn,a4 as Dl,d5 as Jl,bV as Ll,b2 as gl,d6 as pa,w as Zl,ce as fa,b3 as $n,aG as wn,y as Gl,bp as yl,aP as Hn,d7 as ka,d8 as Sa,d9 as ha,da as va,db as Bl,dc as Fa,Y as ba,dd as xa,a8 as Ra,bm as Bn,de as rn,bC as on,H as at,df as Ta,cD as it,bf as Ka,aF as Ia,dg as Da,M as Aa,a5 as Ca,dh as Ma,cc as Yl,c$ as La,bt as ln,bu as Vn,bs as ja,di as pl,aY as Pa,f as dn,bX as st,cY as rt,dj as cn,b_ as Ql,dk as Qn,cC as mn,bU as _n,c1 as Na,G as ot,dl as dt,au as bn,dm as Va,bZ as En,p as yn,Z as ut,dn as _a,cL as ct,av as Ea,ai as qn,d0 as Oa,bJ as mt,d1 as $a,D as wa,cG as Ha,c0 as Ba,dp as Qa,dq as qa,aV as zn,dr as za,ds as Ua,dt as Wa,du as Ga}from"./index-r5M52Un8.js";import{f as Ya,t as Xa}from"./parseCliCommand-DLNI3aPC.js";import{R as Ja,b as Za}from"./RuntimeParameterFormSection-B3vyuB7F.js";import{B as Un}from"./BAIVFolderSelect-G38HWPyf.js";import{P as ei}from"./PrometheusQueryTemplatePreview-DnCJ7olI.js";import{B as gt,n as yt,u as pt,a as ft,o as li,R as kt,S as ni}from"./SessionDetailDrawer-DaYr_a4L.js";import{B as nn}from"./BAIGraphQLPropertyFilter-CGIFK1tA.js";import{i as fl,D as pn,a as ti,b as St,B as ai}from"./DeploymentRevisionDetailDrawer-v9Kfvuq9.js";import{F as ii}from"./FolderLink-CVus6lm-.js";import{B as Hl}from"./BAIId-DYp9TwD-.js";import{S as si,a as ri}from"./ScopedAuditLog-GhAcxAyr.js";import{B as oi}from"./BooleanTag-B3quKU6d.js";import"./UndoOutlined-BWC6N9Tx.js";import"./corner-down-left-BAQMMY0X.js";import"./zip-D5nKRYgG.js";import"./unzip-CowBifeB.js";/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const di=[["line",{x1:"15",x2:"15",y1:"12",y2:"18",key:"1p7wdc"}],["line",{x1:"12",x2:"18",y1:"15",y2:"15",key:"1nscbv"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2",key:"17jyea"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",key:"zix9uf"}]],Wn=lt("copy-plus",di);/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ui=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",key:"usdka0"}]],Gn=lt("folder-open",ui),ht=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},s=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"NAME"}]}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e,i],kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectPaginatedQuery",selections:s,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[i,e,l],kind:"Operation",name:"BAIRuntimeVariantSelectPaginatedQuery",selections:s},params:{cacheID:"e8d20623434b823880b9543cf3297c3f",id:null,metadata:{},name:"BAIRuntimeVariantSelectPaginatedQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $filter: RuntimeVariantFilter
) {
  runtimeVariants(offset: $offset, limit: $limit, filter: $filter, orderBy: [{field: NAME, direction: "ASC"}]) {
    count
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();ht.hash="65da05baef2fee7bd3840fc61e39a8d8";const vt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"},{defaultValue:null,kind:"LocalArgument",name:"skip"}],e=[{condition:"skip",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectValueQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIRuntimeVariantSelectValueQuery",selections:e},params:{cacheID:"f029b9c8b12e9bc799f1ff1caaebd031",id:null,metadata:{},name:"BAIRuntimeVariantSelectValueQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectValueQuery(
  $id: UUID!
  $skip: Boolean!
) {
  runtimeVariant(id: $id) @skip(if: $skip) {
    id
    name
  }
}
`}}}();vt.hash="f7c1435633aeb06ecc9eafe324f06550";const ci=l=>{"use memo";var we;const e=tl.c(74);let i,s,t,a;e[0]!==l?({loading:i,onResolvedNamesChange:s,ref:t,...a}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a):(i=e[1],s=e[2],t=e[3],a=e[4]);const{t:u}=Kn(),r=M.useRef(null),[o,d]=vn(a);let g;e[5]===Symbol.for("react.memo_cache_sentinel")?(g={valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"},e[5]=g):g=e[5];const[c,k]=vn(a,g),h=M.useDeferredValue(c),[S,p]=M.useState(),m=ia(S),[f,R]=M.useOptimistic(S),[x,F]=M.useTransition(),[I,D]=Il(),C=M.useDeferredValue(I),A=M.useDeferredValue(o);let z;e[6]!==A?(z=A?nt(Wl(A)):"",e[6]=A,e[7]=z):z=e[7];const U=z;let w;e[8]===Symbol.for("react.memo_cache_sentinel")?(w=vt,e[8]=w):w=e[8];const Q=!U;let P;e[9]!==U||e[10]!==Q?(P={id:U,skip:Q},e[9]=U,e[10]=Q,e[11]=P):P=e[11];const L=U?"store-or-network":"store-only";let E;e[12]!==C||e[13]!==L?(E={fetchPolicy:L,fetchKey:C},e[12]=C,e[13]=L,e[14]=E):E=e[14];const{runtimeVariant:j}=Le.useLazyLoadQuery(w,P,E);let Y;e[15]!==m?(Y=m?{name:{iContains:m}}:null,e[15]=m,e[16]=Y):Y=e[16];const W=Y;let q,V;e[17]===Symbol.for("react.memo_cache_sentinel")?(V=ht,q={limit:20},e[17]=q,e[18]=V):(q=e[17],V=e[18]);let v;e[19]!==W?(v={filter:W},e[19]=W,e[20]=v):v=e[20];const b=h?"network-only":"store-only";let _;e[21]!==C||e[22]!==b?(_={fetchPolicy:b,fetchKey:C},e[21]=C,e[22]=b,e[23]=_):_=e[23];let J;e[24]===Symbol.for("react.memo_cache_sentinel")?(J={getTotal:mi,getItem:yi,getId:pi},e[24]=J):J=e[24];const{paginationData:Z,result:ne,loadNext:K,isLoadingNext:T}=sa(V,q,v,_,J);let N,H;e[25]!==D?(N=()=>({refetch:()=>{F(()=>{D()})}}),H=[D,F],e[25]=D,e[26]=N,e[27]=H):(N=e[26],H=e[27]),M.useImperativeHandle(t,N,H);let G;e[28]!==s||e[29]!==Z||e[30]!==j?(G=()=>{if(!s)return;const De={};if(j!=null&&j.id&&j.name){const xe=ll(j.id);xe&&(De[xe]=j.name)}for(const xe of Z??[])if(xe!=null&&xe.id&&xe.name){const He=ll(xe.id);He&&(De[He]=xe.name)}Dn(De)||s(De)},e[28]=s,e[29]=Z,e[30]=j,e[31]=G):G=e[31];const ee=M.useEffectEvent(G);let le;e[32]!==ee?(le=()=>{ee()},e[32]=ee,e[33]=le):le=e[33];let $;e[34]!==Z||e[35]!==j?($=[j,Z],e[34]=Z,e[35]=j,e[36]=$):$=e[36],M.useEffect(le,$);let O;e[37]!==Z?(O=bl(Z,fi),e[37]=Z,e[38]=O):O=e[38];const Fe=O,ke=j==null?void 0:j.name;let me;e[39]!==A||e[40]!==ke?(me=A?{label:ke??Wl(A),value:Wl(A)}:void 0,e[39]=A,e[40]=ke,e[41]=me):me=e[41];const Me=me,[ye,pe]=M.useState(Me);let ue;e[42]!==u?(ue=u("comp:BAIRuntimeVariantSelect.SelectRuntimeVariant"),e[42]=u,e[43]=ue):ue=e[43];const de=i||o!==A||S!==m||x;let se;e[44]!==a||e[45]!==R?(se=async De=>{var xe;R(De),p(De),await((xe=a.searchAction)==null?void 0:xe.call(a,De))},e[44]=a,e[45]=R,e[46]=se):se=e[46];let ce;e[47]!==f||e[48]!==a.showSearch?(ce=a.showSearch===!1?!1:{searchValue:f,autoClearSearchValue:!0,...ra(a.showSearch)?In(a.showSearch,["searchValue"]):{},filterOption:!1},e[47]=f,e[48]=a.showSearch,e[49]=ce):ce=e[49];const be=o!==A?ye:Me;let ve;e[50]!==Fe||e[51]!==d?(ve=(De,xe)=>{var X;if(On(De)||ua(De)){pe(void 0),d(void 0,xe);return}const He=ca(De)[0],B={label:ma(He.label)?He.label:((X=Fe.find(te=>te.value===He.value))==null?void 0:X.label)??Wl(He.value),value:Wl(He.value)};pe(B),d(B.value,xe)},e[50]=Fe,e[51]=d,e[52]=ve):ve=e[52];let Ke;e[53]!==K?(Ke=()=>{K()},e[53]=K,e[54]=Ke):Ke=e[54];let Se;e[55]!==Z?(Se=On(Z)?n.jsx(Fl.Input,{active:!0,size:"small",block:!0}):void 0,e[55]=Z,e[56]=Se):Se=e[56];let ae;e[57]!==T||e[58]!==ne.runtimeVariants?(ae=oa((we=ne.runtimeVariants)==null?void 0:we.count)&&ne.runtimeVariants.count>0?n.jsx(da,{loading:T,total:ne.runtimeVariants.count}):void 0,e[57]=T,e[58]=ne.runtimeVariants,e[59]=ae):ae=e[59];let fe;return e[60]!==Fe||e[61]!==c||e[62]!==a||e[63]!==k||e[64]!==ue||e[65]!==de||e[66]!==se||e[67]!==ce||e[68]!==be||e[69]!==ve||e[70]!==Ke||e[71]!==Se||e[72]!==ae?(fe=n.jsx(Xl,{ref:r,placeholder:ue,loading:de,...a,searchAction:se,showSearch:ce,value:be,labelInValue:!0,onChange:ve,options:Fe,endReached:Ke,open:c,onOpenChange:k,notFoundContent:Se,footer:ae}),e[60]=Fe,e[61]=c,e[62]=a,e[63]=k,e[64]=ue,e[65]=de,e[66]=se,e[67]=ce,e[68]=be,e[69]=ve,e[70]=Ke,e[71]=Se,e[72]=ae,e[73]=fe):fe=e[73],fe};function mi(l){var e;return((e=l.runtimeVariants)==null?void 0:e.count)??void 0}function gi(l){return l==null?void 0:l.node}function yi(l){var e,i;return(i=(e=l.runtimeVariants)==null?void 0:e.edges)==null?void 0:i.map(gi)}function pi(l){return l==null?void 0:l.id}function fi(l){return{label:l==null?void 0:l.name,value:l!=null&&l.id?ll(l.id):void 0}}const Ft={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"DeploymentHistory",abstractKey:null};Ft.hash="eb0787126d34e31d6d0aa79127c25d2f";const xn=[];[...xn,...xn.map(l=>`-${l}`)];const Rl=l=>An(xn,l),ki=l=>{"use memo";const e=tl.c(23);let i,s,t,a,u;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:s,customizeColumns:i,onChangeOrder:t,...u}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5]);const{t:r}=Kn();let o;e[6]===Symbol.for("react.memo_cache_sentinel")?(o=Ft,e[6]=o):o=e[6];const d=Le.useFragment(o,a);let g;if(e[7]!==i||e[8]!==s||e[9]!==r){let m;e[11]!==s?(m=R=>s?In(R,"sorter"):R,e[11]=s,e[12]=m):m=e[12];const f=bl(gn([{dataIndex:"updatedAt",title:r("comp:BAIDeploymentSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:Si,sorter:Rl("updated_at")},{dataIndex:"createdAt",title:r("comp:BAIDeploymentSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:hi,sorter:Rl("created_at")},{dataIndex:"phase",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Phase"),key:"phase",sorter:Rl("phase")},{dataIndex:"result",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Result"),key:"result",render:vi,sorter:Rl("result")},{dataIndex:"category",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Category"),key:"category",sorter:Rl("category")},{key:"fromStatus",title:r("comp:BAIDeploymentSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Rl("from_status")},{key:"toStatus",title:r("comp:BAIDeploymentSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Rl("to_status")},{dataIndex:"attempts",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Rl("attempts")},{key:"errorCode",title:r("comp:BAIDeploymentSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Fi,sorter:Rl("errorCode")},{key:"message",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:bi,render:xi,sorter:Rl("message")}]),m);g=i?i(f):f,e[7]=i,e[8]=s,e[9]=r,e[10]=g}else g=e[10];const c=g;let k;e[13]!==d?(k=Al(d),e[13]=d,e[14]=k):k=e[14];let h;e[15]===Symbol.for("react.memo_cache_sentinel")?(h={x:"max-content"},e[15]=h):h=e[15];let S;e[16]!==t?(S=m=>{t==null||t(m||null)},e[16]=t,e[17]=S):S=e[17];let p;return e[18]!==c||e[19]!==k||e[20]!==S||e[21]!==u?(p=n.jsx(ql,{rowKey:"id",dataSource:k,columns:c,scroll:h,onChangeOrder:S,...u}),e[18]=c,e[19]=k,e[20]=S,e[21]=u,e[22]=p):p=e[22],p};function Si(l){return n.jsx("span",{children:cl(l).format("ll LTS")})}function hi(l){return n.jsx("span",{children:cl(l).format("ll LTS")})}function vi(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(gt,{result:i})}function Fi(l,e){return e.errorCode?n.jsx(Pl,{monospace:!0,children:e.errorCode}):"-"}function bi(){return{style:{maxWidth:500}}}function xi(l,e){return e.message?n.jsx(Pl,{title:e.message,style:{width:"100%"},children:yt(e.message)}):"-"}const bt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryNodeTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"RouteHistory",abstractKey:null};bt.hash="bd0c64d2e599015d8b9db0afbcb05c7c";const Rn=[];[...Rn,...Rn.map(l=>`-${l}`)];const Tl=l=>An(Rn,l),Ri=l=>{"use memo";const e=tl.c(23);let i,s,t,a,u;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:s,customizeColumns:i,onChangeOrder:t,...u}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5]);const{t:r}=Kn();let o;e[6]===Symbol.for("react.memo_cache_sentinel")?(o=bt,e[6]=o):o=e[6];const d=Le.useFragment(o,a);let g;if(e[7]!==i||e[8]!==s||e[9]!==r){let m;e[11]!==s?(m=R=>s?In(R,"sorter"):R,e[11]=s,e[12]=m):m=e[12];const f=bl(gn([{dataIndex:"updatedAt",title:r("comp:BAIRouteSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:Ti,sorter:Tl("updated_at")},{dataIndex:"createdAt",title:r("comp:BAIRouteSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:Ki,sorter:Tl("created_at")},{dataIndex:"phase",title:r("comp:BAIRouteSchedulingHistoryNodes.Phase"),key:"phase",sorter:Tl("phase")},{dataIndex:"result",title:r("comp:BAIRouteSchedulingHistoryNodes.Result"),key:"result",render:Ii,sorter:Tl("result")},{dataIndex:"category",title:r("comp:BAIRouteSchedulingHistoryNodes.Category"),key:"category",sorter:Tl("category")},{key:"fromStatus",title:r("comp:BAIRouteSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Tl("from_status")},{key:"toStatus",title:r("comp:BAIRouteSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Tl("to_status")},{dataIndex:"attempts",title:r("comp:BAIRouteSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Tl("attempts")},{key:"errorCode",title:r("comp:BAIRouteSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Di,sorter:Tl("errorCode")},{key:"message",title:r("comp:BAIRouteSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:Ai,render:Ci,sorter:Tl("message")}]),m);g=i?i(f):f,e[7]=i,e[8]=s,e[9]=r,e[10]=g}else g=e[10];const c=g;let k;e[13]!==d?(k=Al(d),e[13]=d,e[14]=k):k=e[14];let h;e[15]===Symbol.for("react.memo_cache_sentinel")?(h={x:"max-content"},e[15]=h):h=e[15];let S;e[16]!==t?(S=m=>{t==null||t(m||null)},e[16]=t,e[17]=S):S=e[17];let p;return e[18]!==c||e[19]!==k||e[20]!==S||e[21]!==u?(p=n.jsx(ql,{rowKey:"id",dataSource:k,columns:c,scroll:h,onChangeOrder:S,...u}),e[18]=c,e[19]=k,e[20]=S,e[21]=u,e[22]=p):p=e[22],p};function Ti(l){return n.jsx("span",{children:cl(l).format("ll LTS")})}function Ki(l){return n.jsx("span",{children:cl(l).format("ll LTS")})}function Ii(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(gt,{result:i})}function Di(l,e){return e.errorCode?n.jsx(Pl,{monospace:!0,children:e.errorCode}):"-"}function Ai(){return{style:{maxWidth:500}}}function Ci(l,e){return e.message?n.jsx(Pl,{title:e.message,style:{width:"100%"},children:yt(e.message)}):"-"}const xt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryNodesFragment"}],type:"DeploymentHistory",abstractKey:null};xt.hash="72a9b8118e4f52a97c2ab8996996098d";const Mi=l=>{"use memo";const e=tl.c(26);let i,s,t,a;e[0]!==l?({schedulingHistoryFrgmt:a,expandMode:i,onExpandModeChange:s,...t}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a):(i=e[1],s=e[2],t=e[3],a=e[4]);let u;e[5]===Symbol.for("react.memo_cache_sentinel")?(u=xt,e[5]=u):u=e[5];const r=Le.useFragment(u,a);let o;e[6]!==r?(o=Al(r),e[6]=r,e[7]=o):o=e[7];const d=o;let g;e[8]!==i||e[9]!==s?(g={mode:i,onModeChange:s},e[8]=i,e[9]=s,e[10]=g):g=e[10];const{mode:c,expandedRowKeys:k,onExpandedRowsChange:h,expandColumnTitle:S}=pt(d,g);let p;e[11]!==d?(p=x=>{var F;return!Dn((F=d.find(I=>I.id===x.id))==null?void 0:F.subSteps)},e[11]=d,e[12]=p):p=e[12];let m;e[13]!==d||e[14]!==c?(m=x=>{var F;return n.jsx(ft,{resizable:!0,subStepsFrgmt:((F=d.find(I=>I.id===x.id))==null?void 0:F.subSteps)??[],pagination:!1,errorsOnly:c==="errors-only"})},e[13]=d,e[14]=c,e[15]=m):m=e[15];let f;e[16]!==S||e[17]!==k||e[18]!==h||e[19]!==p||e[20]!==m?(f={columnTitle:S,expandedRowKeys:k,onExpandedRowsChange:h,rowExpandable:p,expandedRowRender:m},e[16]=S,e[17]=k,e[18]=h,e[19]=p,e[20]=m,e[21]=f):f=e[21];let R;return e[22]!==r||e[23]!==t||e[24]!==f?(R=n.jsx(ki,{schedulingHistoryFrgmt:r,expandable:f,...t}),e[22]=r,e[23]=t,e[24]=f,e[25]=R):R=e[25],R},Rt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryNodeTableFragment"}],type:"RouteHistory",abstractKey:null};Rt.hash="7f5f32e6a4ea10ddfc54ff01c8b260b2";const Li=l=>{"use memo";const e=tl.c(26);let i,s,t,a;e[0]!==l?({schedulingHistoryFrgmt:a,expandMode:i,onExpandModeChange:s,...t}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a):(i=e[1],s=e[2],t=e[3],a=e[4]);let u;e[5]===Symbol.for("react.memo_cache_sentinel")?(u=Rt,e[5]=u):u=e[5];const r=Le.useFragment(u,a);let o;e[6]!==r?(o=Al(r),e[6]=r,e[7]=o):o=e[7];const d=o;let g;e[8]!==i||e[9]!==s?(g={mode:i,onModeChange:s},e[8]=i,e[9]=s,e[10]=g):g=e[10];const{mode:c,expandedRowKeys:k,onExpandedRowsChange:h,expandColumnTitle:S}=pt(d,g);let p;e[11]!==d?(p=x=>{var F;return!Dn((F=d.find(I=>I.id===x.id))==null?void 0:F.subSteps)},e[11]=d,e[12]=p):p=e[12];let m;e[13]!==d||e[14]!==c?(m=x=>{var F;return n.jsx(ft,{resizable:!0,subStepsFrgmt:((F=d.find(I=>I.id===x.id))==null?void 0:F.subSteps)??[],pagination:!1,errorsOnly:c==="errors-only"})},e[13]=d,e[14]=c,e[15]=m):m=e[15];let f;e[16]!==S||e[17]!==k||e[18]!==h||e[19]!==p||e[20]!==m?(f={columnTitle:S,expandedRowKeys:k,onExpandedRowsChange:h,rowExpandable:p,expandedRowRender:m},e[16]=S,e[17]=k,e[18]=h,e[19]=p,e[20]=m,e[21]=f):f=e[21];let R;return e[22]!==r||e[23]!==t||e[24]!==f?(R=n.jsx(Ri,{schedulingHistoryFrgmt:r,expandable:f,...t}),e[22]=r,e[23]=t,e[24]=f,e[25]=R):R=e[25],R},Tt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},u={alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},r={alias:null,args:null,concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:null},o=[i],d={alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},k={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,s,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},h={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[g,c,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},k],storageKey:null},S={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},m=[s,p],f={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null}],storageKey:null},R={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},x={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[g,c,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},k],storageKey:null},F={alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[s,i],storageKey:null},I={alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null},D={alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},p,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[s,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},z={alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},U={alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},w={alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},Q={alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},E={alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},Y={alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},W={alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},q={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentDetailPageQuery",selections:[{kind:"CatchField",field:{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[s,t,a],storageKey:null},u,r,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:o,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:o,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[d],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentConfigurationSection_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentReplicasTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAccessTokensTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAutoScalingTab_deployment"}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[s,t,a,{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[s],storageKey:null},i],storageKey:null}],storageKey:null},u,r,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,h,S,f,R,x,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},F,I,D,C],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[s,A,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[z,U,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},w,Q,P,L,E,j],storageKey:null},Y,W],storageKey:null}],storageKey:null}],storageKey:null},q,V,v,R,q],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:[i,V,v,S,R,f,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[F,C,I,D],storageKey:null},h,x,q,{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[s,A,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[z,Y,U,W,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[w,P,Q,L,E,j],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[d,i],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"5cf08f03aee172e06f329eff9fc80643",id:null,metadata:{},name:"DeploymentDetailPageQuery",operationKind:"query",text:`query DeploymentDetailPageQuery(
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
    ...DeploymentConfigurationSection_deployment
    ...DeploymentReplicasTab_deployment
    ...DeploymentAccessTokensTab_deployment
    ...DeploymentAutoScalingTab_deployment
  }
}

fragment BAIDeploymentTagChips_metadata on ModelDeploymentMetadata {
  tags
}

fragment DeploymentAccessTokensTab_deployment on ModelDeployment {
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

fragment DeploymentAutoScalingTab_deployment on ModelDeployment {
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

fragment DeploymentConfigurationSection_deployment on ModelDeployment {
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
  ...DeploymentRevisionHistoryTab_deployment
}

fragment DeploymentReplicasTab_deployment on ModelDeployment {
  id
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
`}}}();Tt.hash="2d2ffabcc8d5601d5443ec9e7163704b";const Kt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAccessTokenPayload",kind:"LinkedField",name:"deleteAccessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabDeleteMutation",selections:e},params:{cacheID:"a511c067913c62224123dba5853f9c55",id:null,metadata:{},name:"DeploymentAccessTokensTabDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensTabDeleteMutation(
  $input: DeleteAccessTokenInput!
) {
  deleteAccessToken(input: $input) {
    id
  }
}
`}}}();Kt.hash="a82f98c3e592ea37497b90c70d69d6b4";const It=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:[{kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"CREATED_AT"}]}],concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"AccessTokenEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:'accessTokens(orderBy:[{"direction":"DESC","field":"CREATED_AT"}])'};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[s],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[s,i],storageKey:null}]},params:{cacheID:"cb48b0e9b4930dfa44b7157fc8f289da",id:null,metadata:{},name:"DeploymentAccessTokensTabListQuery",operationKind:"query",text:`query DeploymentAccessTokensTabListQuery(
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
`}}}();It.hash="4e84247d3aa97d220f9a949a56d396e1";const Dt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAccessTokenPayload",kind:"LinkedField",name:"createAccessToken",plural:!1,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"accessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabCreateMutation",selections:e},params:{cacheID:"ad0b1632c09adadb34c59dfacd183923",id:null,metadata:{},name:"DeploymentAccessTokensTabCreateMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensTabCreateMutation(
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
`}}}();Dt.hash="df1b417c9205070e2bf82168815c312e";const At={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};At.hash="48a180522415b103a2e930a5abc7a973";const ji=l=>{"use memo";var ve;const e=tl.c(91);let i,s,t,a,u,r,o;e[0]!==l?({deploymentFrgmt:t,deploymentId:a,isOwnedByCurrentUser:r,isDeploymentDestroying:o,onTokenCreated:u,cardRef:i,...s}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u,e[6]=r,e[7]=o):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5],r=e[6],o=e[7]);const d=r===void 0?!0:r,g=o===void 0?!1:o,{t:c}=rl(),{token:k}=Cl.useToken(),{message:h}=Nl.useApp(),{logger:S}=zl(),[p,m]=M.useTransition(),[f,R]=M.useState(0);let x;e[8]===Symbol.for("react.memo_cache_sentinel")?(x={defaultValue:!1,valuePropName:"isCreateModalOpen",trigger:"onCreateModalOpenChange"},e[8]=x):x=e[8];const[F,I]=vn(s,x),[D,C]=M.useState(null),A=M.useDeferredValue(f);let z;e[9]===Symbol.for("react.memo_cache_sentinel")?(z=At,e[9]=z):z=e[9];const U=Le.useFragment(z,t);let w;e[10]===Symbol.for("react.memo_cache_sentinel")?(w=Dt,e[10]=w):w=e[10];const Q=tt(w);let P;e[11]===Symbol.for("react.memo_cache_sentinel")?(P=()=>{m(()=>{R(Vi)})},e[11]=P):P=e[11];const L=P,E=!!((ve=U.networkAccess)!=null&&ve.endpointUrl),j=g||!d,Y=j||!E;let W;e[12]!==c?(W=c("deployment.tab.AccessTokens"),e[12]=c,e[13]=W):W=e[13];let q;e[14]!==c?(q=c("deployment.tab.description.AccessTokens"),e[14]=c,e[15]=q):q=e[15];let V;e[16]!==k.colorTextDescription?(V=n.jsx(Cn,{style:{color:k.colorTextDescription}}),e[16]=k.colorTextDescription,e[17]=V):V=e[17];let v;e[18]!==q||e[19]!==V?(v=n.jsx(ml,{title:q,children:V}),e[18]=q,e[19]=V,e[20]=v):v=e[20];let b;e[21]!==v||e[22]!==W?(b=n.jsxs(ie,{gap:"xs",align:"center",children:[W,v]}),e[21]=v,e[22]=W,e[23]=b):b=e[23];let _;e[24]!==p?(_=n.jsx(Vl,{loading:p,value:"",onChange:L}),e[24]=p,e[25]=_):_=e[25];let J;e[26]!==E||e[27]!==c?(J=E?"":c("deployment.accessToken.EndpointNotIssuedYet"),e[26]=E,e[27]=c,e[28]=J):J=e[28];let Z;e[29]===Symbol.for("react.memo_cache_sentinel")?(Z=n.jsx(jl,{}),e[29]=Z):Z=e[29];let ne;e[30]!==I?(ne=()=>I(!0),e[30]=I,e[31]=ne):ne=e[31];let K;e[32]!==c?(K=c("deployment.accessToken.Create"),e[32]=c,e[33]=K):K=e[33];let T;e[34]!==Y||e[35]!==ne||e[36]!==K?(T=n.jsx(Sl,{type:"primary",icon:Z,disabled:Y,onClick:ne,children:K}),e[34]=Y,e[35]=ne,e[36]=K,e[37]=T):T=e[37];let N;e[38]!==J||e[39]!==T?(N=n.jsx(ml,{title:J,children:T}),e[38]=J,e[39]=T,e[40]=N):N=e[40];let H;e[41]!==_||e[42]!==N?(H=n.jsxs(ie,{gap:"xs",align:"center",children:[_,N]}),e[41]=_,e[42]=N,e[43]=H):H=e[43];let G;e[44]===Symbol.for("react.memo_cache_sentinel")?(G={body:{paddingTop:0}},e[44]=G):G=e[44];let ee;e[45]===Symbol.for("react.memo_cache_sentinel")?(ee=n.jsx(Fl,{active:!0}),e[45]=ee):ee=e[45];let le;e[46]!==A||e[47]!==a||e[48]!==j||e[49]!==p?(le=n.jsx(M.Suspense,{fallback:ee,children:n.jsx(Pi,{deploymentId:a,fetchKey:A,isPendingRefetch:p,isDeleteDisabled:j,onAfterDelete:L})}),e[46]=A,e[47]=a,e[48]=j,e[49]=p,e[50]=le):le=e[50];let $;e[51]!==i||e[52]!==b||e[53]!==H||e[54]!==le?($=n.jsx(en,{ref:i,title:b,extra:H,styles:G,children:le}),e[51]=i,e[52]=b,e[53]=H,e[54]=le,e[55]=$):$=e[55];let O;e[56]!==Q||e[57]!==U.id||e[58]!==S||e[59]!==h||e[60]!==u||e[61]!==I||e[62]!==c?(O=Ke=>{I(!1),Ke&&Q({input:{modelDeploymentId:ll(U.id),expiresAt:Ke.expiresAt??new Date("2099-12-31").toISOString()}}).then(Se=>{var fe;const ae=(fe=Se.createAccessToken)==null?void 0:fe.accessToken;ae&&C({token:ae.token,expiresAt:ae.expiresAt??null}),h.success({key:"access-token-created",content:c("deployment.accessToken.Created")}),L(),u==null||u()}).catch(Se=>{const ae=Array.isArray(Se)?Se:[Se];for(const fe of ae)h.error((fe==null?void 0:fe.message)||c("dialog.ErrorOccurred"));S.error(Se)})},e[56]=Q,e[57]=U.id,e[58]=S,e[59]=h,e[60]=u,e[61]=I,e[62]=c,e[63]=O):O=e[63];let Fe;e[64]!==F||e[65]!==O?(Fe=n.jsx(kl,{children:n.jsx(Ni,{open:F,confirmLoading:!1,onRequestClose:O})}),e[64]=F,e[65]=O,e[66]=Fe):Fe=e[66];const ke=D!==null;let me;e[67]!==c?(me=c("deployment.accessToken.Token"),e[67]=c,e[68]=me):me=e[68];let Me;e[69]===Symbol.for("react.memo_cache_sentinel")?(Me=()=>C(null),e[69]=Me):Me=e[69];let ye;e[70]!==c?(ye=c("deployment.accessToken.Created"),e[70]=c,e[71]=ye):ye=e[71];let pe;e[72]!==ye?(pe=n.jsx(nl.Text,{children:ye}),e[72]=ye,e[73]=pe):pe=e[73];let ue;e[74]!==D?(ue=D?n.jsx(Pl,{copyable:{text:D.token},ellipsis:!0,code:!0,children:D.token}):null,e[74]=D,e[75]=ue):ue=e[75];let de;e[76]!==D||e[77]!==c?(de=D!=null&&D.expiresAt?n.jsx(nl.Text,{type:"secondary",children:`${c("deployment.accessToken.Expiration")}: ${cl(D.expiresAt).format("ll LT")}`}):n.jsx(nl.Text,{type:"secondary",children:c("deployment.accessToken.NoExpiration")}),e[76]=D,e[77]=c,e[78]=de):de=e[78];let se;e[79]!==pe||e[80]!==ue||e[81]!==de?(se=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[pe,ue,de]}),e[79]=pe,e[80]=ue,e[81]=de,e[82]=se):se=e[82];let ce;e[83]!==ke||e[84]!==me||e[85]!==se?(ce=n.jsx(kl,{children:n.jsx(Ul,{open:ke,destroyOnHidden:!0,title:me,onCancel:Me,footer:null,width:520,children:se})}),e[83]=ke,e[84]=me,e[85]=se,e[86]=ce):ce=e[86];let be;return e[87]!==$||e[88]!==Fe||e[89]!==ce?(be=n.jsxs(n.Fragment,{children:[$,Fe,ce]}),e[87]=$,e[88]=Fe,e[89]=ce,e[90]=be):be=e[90],be},Pi=l=>{"use memo";var N,H,G,ee;const e=tl.c(70),{deploymentId:i,fetchKey:s,isPendingRefetch:t,isDeleteDisabled:a,onAfterDelete:u}=l,{t:r}=rl(),{message:o}=Nl.useApp(),{logger:d}=zl(),[g,c]=M.useState(null);let k;e[0]===Symbol.for("react.memo_cache_sentinel")?(k=It,e[0]=k):k=e[0];let h;e[1]!==i?(h={deploymentId:i},e[1]=i,e[2]=h):h=e[2];let S;e[3]!==s?(S={fetchKey:s,fetchPolicy:"network-only"},e[3]=s,e[4]=S):S=e[4];const{deployment:p}=Le.useLazyLoadQuery(k,h,S);let m;e[5]!==((N=p==null?void 0:p.accessTokens)==null?void 0:N.edges)?(m=Al((G=(H=p==null?void 0:p.accessTokens)==null?void 0:H.edges)==null?void 0:G.map(_i)),e[5]=(ee=p==null?void 0:p.accessTokens)==null?void 0:ee.edges,e[6]=m):m=e[6];const f=m;let R;e[7]===Symbol.for("react.memo_cache_sentinel")?(R=Kt,e[7]=R):R=e[7];const[x,F]=Le.useMutation(R);let I;e[8]===Symbol.for("react.memo_cache_sentinel")?(I={x:"max-content"},e[8]=I):I=e[8];const D=t||F;let C;e[9]!==r?(C=r("deployment.accessToken.Token"),e[9]=r,e[10]=C):C=e[10];let A;e[11]!==a||e[12]!==r?(A=(le,$)=>$?n.jsx(Mn,{title:n.jsx(Pl,{copyable:{text:$.token},ellipsis:!0,style:{maxWidth:200},children:$.token}),showActions:"always",actions:[{key:"delete",title:r("deployment.accessToken.Delete"),icon:n.jsx(Ln,{}),type:"danger",disabled:a,onClick:()=>c({id:$.id,token:$.token??""})}]}):"-",e[11]=a,e[12]=r,e[13]=A):A=e[13];let z;e[14]!==C||e[15]!==A?(z={key:"token",title:C,dataIndex:"token",render:A},e[14]=C,e[15]=A,e[16]=z):z=e[16];let U;e[17]!==r?(U=r("deployment.CreatedAt"),e[17]=r,e[18]=U):U=e[18];let w;e[19]!==U?(w={key:"createdAt",title:U,dataIndex:"createdAt",render:Ei},e[19]=U,e[20]=w):w=e[20];let Q;e[21]!==r?(Q=r("deployment.accessToken.Expiration"),e[21]=r,e[22]=Q):Q=e[22];let P;e[23]!==r?(P=(le,$)=>$!=null&&$.expiresAt?cl($.expiresAt).format("ll LT"):r("deployment.accessToken.NoExpiration"),e[23]=r,e[24]=P):P=e[24];let L;e[25]!==Q||e[26]!==P?(L={key:"expiresAt",title:Q,dataIndex:"expiresAt",render:P},e[25]=Q,e[26]=P,e[27]=L):L=e[27];let E;e[28]!==z||e[29]!==w||e[30]!==L?(E=[z,w,L],e[28]=z,e[29]=w,e[30]=L,e[31]=E):E=e[31];let j;e[32]!==f||e[33]!==E||e[34]!==D?(j=n.jsx(ql,{scroll:I,rowKey:"id",loading:D,dataSource:f,pagination:!1,resizable:!0,columns:E}),e[32]=f,e[33]=E,e[34]=D,e[35]=j):j=e[35];const Y=!!g;let W;e[36]!==r?(W=r("deployment.accessToken.Delete"),e[36]=r,e[37]=W):W=e[37];let q;e[38]!==r?(q=r("deployment.AccessToken"),e[38]=r,e[39]=q):q=e[39];let V;e[40]!==g?(V=g?[{key:g.id,label:g.id}]:[],e[40]=g,e[41]=V):V=e[41];let v;e[42]!==r?(v=r("data.folders.DeleteForeverConfirmText"),e[42]=r,e[43]=v):v=e[43];let b;e[44]!==r?(b=r("data.folders.DeleteForeverConfirmText"),e[44]=r,e[45]=b):b=e[45];let _;e[46]!==b?(_={placeholder:b},e[46]=b,e[47]=_):_=e[47];let J;e[48]!==F?(J={loading:F},e[48]=F,e[49]=J):J=e[49];let Z;e[50]!==x||e[51]!==g||e[52]!==d||e[53]!==o||e[54]!==u||e[55]!==r?(Z=()=>{g&&x({variables:{input:{id:ll(g.id)??g.id}},onCompleted:(le,$)=>{var O;if($&&$.length>0){d.error($[0]),o.error(((O=$[0])==null?void 0:O.message)??r("dialog.ErrorOccurred"));return}o.success(r("deployment.accessToken.Deleted")),c(null),u()},onError:le=>{d.error(le),o.error(le.message??r("dialog.ErrorOccurred"))}})},e[50]=x,e[51]=g,e[52]=d,e[53]=o,e[54]=u,e[55]=r,e[56]=Z):Z=e[56];let ne;e[57]===Symbol.for("react.memo_cache_sentinel")?(ne=()=>c(null),e[57]=ne):ne=e[57];let K;e[58]!==Y||e[59]!==W||e[60]!==q||e[61]!==V||e[62]!==v||e[63]!==_||e[64]!==J||e[65]!==Z?(K=n.jsx(jn,{open:Y,title:W,target:q,items:V,confirmText:v,requireConfirmInput:!0,inputProps:_,okButtonProps:J,onOk:Z,onCancel:ne}),e[58]=Y,e[59]=W,e[60]=q,e[61]=V,e[62]=v,e[63]=_,e[64]=J,e[65]=Z,e[66]=K):K=e[66];let T;return e[67]!==j||e[68]!==K?(T=n.jsxs(n.Fragment,{children:[j,K]}),e[67]=j,e[68]=K,e[69]=T):T=e[69],T},Ni=l=>{"use memo";const e=tl.c(64),{open:i,confirmLoading:s,onRequestClose:t}=l,{t:a}=rl(),[u]=ge.useForm(),r=ge.useWatch("expiryOption",u)??7;let o;e[0]!==u||e[1]!==t?(o=()=>{u.validateFields().then(V=>{let v;V.expiryOption==="none"?v=null:V.expiryOption==="custom"?v=V.datetime.toISOString():v=cl().add(V.expiryOption,"day").toISOString(),t({expiresAt:v})}).catch(Oi)},e[0]=u,e[1]=t,e[2]=o):o=e[2];const d=o;let g;e[3]!==a?(g=a("general.Days",{num:7,defaultValue:"7 days"}),e[3]=a,e[4]=g):g=e[4];let c;e[5]!==g?(c={value:7,label:g},e[5]=g,e[6]=c):c=e[6];let k;e[7]!==a?(k=a("general.Days",{num:30,defaultValue:"30 days"}),e[7]=a,e[8]=k):k=e[8];let h;e[9]!==k?(h={value:30,label:k},e[9]=k,e[10]=h):h=e[10];let S;e[11]!==a?(S=a("general.Days",{num:90,defaultValue:"90 days"}),e[11]=a,e[12]=S):S=e[12];let p;e[13]!==S?(p={value:90,label:S},e[13]=S,e[14]=p):p=e[14];let m;e[15]!==a?(m=a("deployment.accessToken.CustomExpiration"),e[15]=a,e[16]=m):m=e[16];let f;e[17]!==m?(f={value:"custom",label:m},e[17]=m,e[18]=f):f=e[18];let R;e[19]!==a?(R=a("deployment.accessToken.NoExpiration"),e[19]=a,e[20]=R):R=e[20];let x;e[21]!==R?(x={value:"none",label:R},e[21]=R,e[22]=x):x=e[22];let F;e[23]!==x||e[24]!==c||e[25]!==h||e[26]!==p||e[27]!==f?(F=[c,h,p,f,x],e[23]=x,e[24]=c,e[25]=h,e[26]=p,e[27]=f,e[28]=F):F=e[28];const I=F;let D;e[29]!==a?(D=a("deployment.accessToken.Create"),e[29]=a,e[30]=D):D=e[30];let C;e[31]!==a?(C=a("deployment.accessToken.Create"),e[31]=a,e[32]=C):C=e[32];let A;e[33]!==t?(A=()=>t(),e[33]=t,e[34]=A):A=e[34];let z,U;e[35]===Symbol.for("react.memo_cache_sentinel")?(z={expiryOption:7,datetime:cl().add(7,"day")},U=["onChange","onBlur"],e[35]=z,e[36]=U):(z=e[35],U=e[36]);let w;e[37]!==a?(w=a("deployment.accessToken.Expiration"),e[37]=a,e[38]=w):w=e[38];let Q;e[39]===Symbol.for("react.memo_cache_sentinel")?(Q=[{required:!0}],e[39]=Q):Q=e[39];let P;e[40]===Symbol.for("react.memo_cache_sentinel")?(P={width:200},e[40]=P):P=e[40];let L;e[41]!==u?(L=V=>{typeof V=="number"&&u.setFieldValue("datetime",cl().add(V,"day"))},e[41]=u,e[42]=L):L=e[42];let E;e[43]!==I||e[44]!==L?(E=n.jsx(Fn,{style:P,options:I,onChange:L}),e[43]=I,e[44]=L,e[45]=E):E=e[45];let j;e[46]!==w||e[47]!==E?(j=n.jsx(ge.Item,{name:"expiryOption",label:w,rules:Q,children:E}),e[46]=w,e[47]=E,e[48]=j):j=e[48];let Y;e[49]!==r||e[50]!==a?(Y=r==="custom"&&n.jsx(ge.Item,{name:"datetime",label:a("deployment.accessToken.CustomExpiration"),rules:[{type:"object",required:!0},()=>({validator(V,v){return v&&cl(v).isAfter(cl())?Promise.resolve():Promise.reject(new Error(a("dialog.ErrorOccurred")))}})],children:n.jsx(ga,{showTime:!0,format:"YYYY-MM-DD HH:mm:ss",style:{width:"100%"}})}),e[49]=r,e[50]=a,e[51]=Y):Y=e[51];let W;e[52]!==u||e[53]!==j||e[54]!==Y?(W=n.jsxs(ge,{form:u,layout:"vertical",initialValues:z,validateTrigger:U,children:[j,Y]}),e[52]=u,e[53]=j,e[54]=Y,e[55]=W):W=e[55];let q;return e[56]!==s||e[57]!==d||e[58]!==i||e[59]!==D||e[60]!==C||e[61]!==A||e[62]!==W?(q=n.jsx(Ul,{open:i,destroyOnHidden:!0,centered:!0,width:420,title:D,okText:C,confirmLoading:s,onOk:d,onCancel:A,children:W}),e[56]=s,e[57]=d,e[58]=i,e[59]=D,e[60]=C,e[61]=A,e[62]=W,e[63]=q):q=e[63],q};function Vi(l){return l+1}function _i(l){return l==null?void 0:l.node}function Ei(l,e){return e!=null&&e.createdAt?cl(e.createdAt).format("ll LT"):"-"}function Oi(){}const Ct=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"71af54781375e6ee4bceb1c73e74d088",id:null,metadata:{},name:"DeploymentAddRevisionModalImageNameQuery",operationKind:"query",text:`query DeploymentAddRevisionModalImageNameQuery(
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
`}}}();Ct.hash="7f7c91d5e401085de1ab4d56ffb2ef9b";const Mt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},t={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},u=[i,s],r={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},d={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},g={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},h=[c,k],S={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:h,storageKey:null}],storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:h,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},k,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},R={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},x={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[m,f,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},R],storageKey:null},F={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[m,f,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},R],storageKey:null},I={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},D={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},C=[i,r,o,d,g,S,p,x,F,I,D];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,s,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:u,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:u,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,r,o,d,g,S,p,x,F,I,D,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:C,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:C,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"97d46eaffe190c0a696e6d7daacc3529",id:null,metadata:{},name:"DeploymentAddRevisionModalAddMutation",operationKind:"mutation",text:`mutation DeploymentAddRevisionModalAddMutation(
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
`}}}();Mt.hash="889773e313c63748043b8294cd2bb0b0";const Lt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i},params:{cacheID:"6728695a02d457f55b4cd4d3323823d8",id:null,metadata:{},name:"DeploymentAddRevisionModalSelectedPresetQuery",operationKind:"query",text:`query DeploymentAddRevisionModalSelectedPresetQuery(
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
`}}}();Lt.hash="e9d60ac2d9540dae9c821fe3abd4b65e";const jt=function(){var l=[{alias:null,args:[{kind:"Literal",name:"first",value:1},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"RANK"}]}],concreteType:"DeploymentRevisionPresetConnection",kind:"LinkedField",name:"deploymentRevisionPresets",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:'deploymentRevisionPresets(first:1,orderBy:[{"direction":"ASC","field":"RANK"}])'}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetCountQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAddRevisionModalPresetCountQuery",selections:l},params:{cacheID:"edaa5efa78debd74168a24185822d633",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetCountQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetCountQuery {
  deploymentRevisionPresets(orderBy: [{field: RANK, direction: "ASC"}], first: 1) {
    count
  }
}
`}}}();jt.hash="4461df1967b1117642d3190b36d5cb33";const Pt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[l,e],s={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_revisionSource",selections:[{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:i,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[s,t],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[l],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:i,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[s,t,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelRevision",abstractKey:null}}();Pt.hash="94f9806003b984d4534543e7895a61e8";const Nt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Nt.hash="614548b7fde80b4972dfb192b893b832";const Vt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentPresetDetailModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[i,s,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,s],storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startupCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"bootstrapScript",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[s,t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetDeploymentDefaults",kind:"LinkedField",name:"deploymentDefaults",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"replicaCount",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"revisionHistoryLimit",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentStrategy",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetValueEntry",kind:"LinkedField",name:"presetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},t],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[s,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"81ad2a7db4a7e88c60d295aec28d761d",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetDetailQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetDetailQuery(
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
`}}}();Vt.hash="8f60ae6bcf0fa60919e80838391f66f9";const fn=({children:l})=>{const{token:e}=Cl.useToken();return n.jsx(at,{titlePlacement:"left",children:n.jsx(nl.Text,{type:"secondary",style:{fontSize:e.fontSizeSM},children:l})})},$i=l=>{"use memo";const e=tl.c(6),{presetId:i,onCancel:s}=l;let t;e[0]===Symbol.for("react.memo_cache_sentinel")?(t=Vt,e[0]=t):t=e[0];let a;e[1]!==i?(a={id:i},e[1]=i,e[2]=a):a=e[2];const u=Le.useLazyLoadQuery(t,a);let r;return e[3]!==u.deploymentRevisionPreset||e[4]!==s?(r=n.jsx(Ta,{open:!0,presetFrgmt:u.deploymentRevisionPreset,onCancel:s}),e[3]=u.deploymentRevisionPreset,e[4]=s,e[5]=r):r=e[5],r},_t=({onRequestClose:l,deploymentFrgmt:e,sourceRevisionFrgmt:i,open:s,...t})=>{"use memo";var De,xe,He;const{t:a}=rl(),{token:u}=Cl.useToken(),{message:r}=Nl.useApp(),o=Le.useRelayEnvironment(),d=Le.useFragment(Nt,e),g=Pt,c=Le.useFragment(g,(d==null?void 0:d.currentRevision)??null),k=Le.useFragment(g,i??null),{id:h}=Pn(),{logger:S}=zl(),{open:p}=ya(),m=Nn(),f=m.supports("model-health-check-enable"),R=m.supports("model-runtime-variant-preset-values"),x=M.useRef(null),F=M.useRef(null),[I,D]=M.useState(!1),[C]=ge.useForm(),[A]=ge.useForm(),[z,U]=M.useState(!0),[w,Q]=Dl("deploymentRevisionCreationMode"),P=w??"preset",[L,E]=M.useState(!1),[j,Y]=M.useState(!1),[W,q]=M.useState(!1),[V,v]=M.useState(null),[b,_]=M.useState(null),[J,Z]=M.useState(null),[ne,K]=M.useState({}),T=M.useRef(new Set),N=M.useRef(null),[H,G]=M.useState(void 0),ee=M.useRef({}),[le,$]=M.useState(void 0);M.useEffect(()=>{if(!s)return;let y=!1;return Le.fetchQuery(o,jt,{},{fetchPolicy:"store-or-network"}).toPromise().then(B=>{var X;y||$((((X=B==null?void 0:B.deploymentRevisionPresets)==null?void 0:X.count)??0)===0)}).catch(()=>{y||$(!1)}),()=>{y=!0}},[s,o]);const O=(xe=(De=d==null?void 0:d.currentRevision)==null?void 0:De.modelMountConfig)!=null&&xe.vfolderId?Jl("VirtualFolderNode",d.currentRevision.modelMountConfig.vfolderId):void 0,Fe=M.useRef(new Map),ke=async y=>{const B=Fe.current.get(y);if(B)return B;const X=await Le.fetchQuery(o,Lt,{id:y},{fetchPolicy:"store-or-network"}).toPromise(),te=(X==null?void 0:X.deploymentRevisionPreset)??null;return te&&Fe.current.set(y,te),te},[me,Me]=Le.useMutation(Mt),ye=async y=>{var ze,he,Ge,Ue,Oe,Be,Qe,We;const B=y.resourceSlots??[],X=B.find(Re=>Re.slotName==="cpu"),te=B.find(Re=>Re.slotName==="mem"),re=B.find(Re=>Re.slotName!=="cpu"&&Re.slotName!=="mem"),oe=(((ze=y.resource)==null?void 0:ze.resourceOpts)??[]).find(Re=>Re.name==="shmem"),Ae=((he=y.cluster)==null?void 0:he.clusterMode)==="SINGLE_NODE"?"single-node":"multi-node";let Ve;if((Ge=y.execution)!=null&&Ge.imageId)try{const Re=await Le.fetchQuery(o,Ct,{id:y.execution.imageId},{fetchPolicy:"store-or-network"}).toPromise(),$e=(Ue=Re==null?void 0:Re.imageV2)==null?void 0:Ue.identity;Ve=$e!=null&&$e.canonicalName?$e.architecture?`${$e.canonicalName}@${$e.architecture}`:$e.canonicalName:void 0}catch{Ve=void 0}const Ee=(((Oe=y.execution)==null?void 0:Oe.environ)??[]).map(Re=>({variable:Re.key,value:Re.value}));return{cluster_mode:Ae,cluster_size:((Be=y.cluster)==null?void 0:Be.clusterSize)??1,allocationPreset:"custom",resource:{cpu:X?Number(X.quantity):0,mem:((Qe=on(String((te==null?void 0:te.quantity)??"0"),"g",2))==null?void 0:Qe.value)??"0g",shmem:((We=on((oe==null?void 0:oe.value)??rn,"g",2))==null?void 0:We.value)??rn,...re?{acceleratorType:re.slotName,accelerator:re.slotName==="cuda.shares"?parseFloat(String(re.quantity)):parseInt(String(re.quantity),10)}:{}},enabledAutomaticShmem:!oe,runtimeVariantId:y.runtimeVariantId??void 0,environ:Ee,...Ve?{environments:{version:Ve}}:{}}},pe=async y=>{if(y===P)return;if(P==="preset"&&y==="custom"){const te=A.getFieldsValue(),re=te.revisionPresetId;let oe={};if(re){const Ae=await ke(re);Ae&&(oe=await ye(Ae))}te.modelFolderId&&(oe.modelFolderId=te.modelFolderId),v(Object.keys(oe).length>0?oe:null),Q("custom");return}const B=C.getFieldsValue(),X={};B.modelFolderId&&(X.modelFolderId=B.modelFolderId),C.resetFields(),v(null),_(Object.keys(X).length>0?X:null),Q("preset")},ue=y=>{var Ue,Oe,Be,Qe,We,Re,$e,Ze,Pe,Ie,qe,Ye,Xe,Je,ol,Ce,al,ul,Te,_e,sl,il,dl,xl,hl;const B=y.resourceSlots??[],X=B.find(Ne=>Ne.slotName==="cpu"),te=B.find(Ne=>Ne.slotName==="mem"),re=B.find(Ne=>Ne.slotName!=="cpu"&&Ne.slotName!=="mem"),oe=(((Oe=(Ue=y.resourceConfig)==null?void 0:Ue.resourceOpts)==null?void 0:Oe.entries)??[]).find(Ne=>Ne.name==="shmem"),Ae=((Qe=(Be=y.modelRuntimeConfig)==null?void 0:Be.runtimeVariant)==null?void 0:Qe.name)??"",Ve=Ae==="custom",Ee=(We=y.modelRuntimeConfig)==null?void 0:We.runtimeVariantId;Ee&&Ae&&K(Ne=>({...Ne,[Ee]:Ae}));const je=(Ze=($e=(Re=y.modelDefinition)==null?void 0:Re.models)==null?void 0:$e[0])==null?void 0:Ze.service,ze=(qe=(Ie=(Pe=y.modelDefinition)==null?void 0:Pe.models)==null?void 0:Ie[0])==null?void 0:qe.modelPath,he=je!=null&&je.healthCheck&&je.healthCheck.enable!==!1?je.healthCheck:void 0,Ge=Ve&&!!je&&(((Ye=je.startCommand)==null?void 0:Ye.length)??0)>0;if(ee.current=Bn((y.extraMounts??[]).filter(Ne=>!!Ne.mountDestination).map(Ne=>[Ne.vfolderId.replace(/-/g,""),Ne.mountDestination])),!Ve&&Ae){const Ne=(Xe=y.modelRuntimeConfig)==null?void 0:Xe.runtimeVariantPresetValues;G(Ne&&Ne.length>0?Ne.map(vl=>({presetId:vl.presetId,value:vl.value})):void 0)}C.setFieldsValue({cluster_mode:((Je=y.clusterConfig)==null?void 0:Je.mode)==="SINGLE_NODE"?"single-node":"multi-node",cluster_size:((ol=y.clusterConfig)==null?void 0:ol.size)??1,allocationPreset:"custom",resource:{cpu:X?Number(X.quantity):0,mem:((Ce=on(String((te==null?void 0:te.quantity)??"0"),"g",2))==null?void 0:Ce.value)??"0g",shmem:((al=on((oe==null?void 0:oe.value)??rn,"g",2))==null?void 0:al.value)??rn,...re?{acceleratorType:re.slotName,accelerator:re.slotName==="cuda.shares"?parseFloat(String(re.quantity)):parseInt(String(re.quantity),10)}:{}},enabledAutomaticShmem:!oe,mount_ids:(y.extraMounts??[]).map(Ne=>Ne.vfolderId.replace(/-/g,"")),mount_id_map:Bn((y.extraMounts??[]).filter(Ne=>!!Ne.mountDestination).map(Ne=>[Ne.vfolderId.replace(/-/g,""),Ne.mountDestination])),runtimeVariantId:((ul=y.modelRuntimeConfig)==null?void 0:ul.runtimeVariantId)??void 0,modelFolderId:(Te=y.modelMountConfig)!=null&&Te.vfolderId?Jl("VirtualFolderNode",y.modelMountConfig.vfolderId):void 0,mountDestination:((_e=y.modelMountConfig)==null?void 0:_e.mountDestination)??"/models",definitionPath:((sl=y.modelMountConfig)==null?void 0:sl.definitionPath)??void 0,environments:(dl=(il=y.imageV2)==null?void 0:il.identity)!=null&&dl.canonicalName?{version:y.imageV2.identity.architecture?`${y.imageV2.identity.canonicalName}@${y.imageV2.identity.architecture}`:y.imageV2.identity.canonicalName}:void 0,environ:(((hl=(xl=y.modelRuntimeConfig)==null?void 0:xl.environ)==null?void 0:hl.entries)??[]).map(Ne=>({variable:Ne.name,value:Ne.value})),commandEnableHealthCheck:!!he,commandHealthCheck:(he==null?void 0:he.path)??void 0,commandInitialDelay:(he==null?void 0:he.initialDelay)??void 0,commandMaxRetries:(he==null?void 0:he.maxRetries)??void 0,commandInterval:(he==null?void 0:he.interval)??void 0,commandMaxWaitTime:(he==null?void 0:he.maxWaitTime)??void 0,commandExpectedStatusCode:(he==null?void 0:he.expectedStatusCode)??void 0,...Ge&&je?{customDefinitionMode:"command",startCommand:Ya(je.startCommand??[]),commandPort:je.port,commandModelMount:ze??"/models"}:Ve?{customDefinitionMode:"file"}:{}})},de=M.useEffectEvent(()=>{V&&(C.setFieldsValue(V),v(null))}),se=M.useEffectEvent(()=>{b&&(A.setFieldsValue(b),_(null))}),ce=M.useEffectEvent(()=>{j||k&&(ue(k),Y(!0))}),be=M.useEffectEvent(()=>{W&&c&&(ue(c),q(!1),E(!0),r.success(a("deployment.CurrentRevisionConfigurationLoaded")))});M.useEffect(()=>{P==="custom"?(de(),ce(),be()):se()},[P]);const ve=()=>{if(c){if(P==="custom"){ue(c),E(!0),r.success(a("deployment.CurrentRevisionConfigurationLoaded"));return}q(!0),Q("custom")}},Ke=y=>{const B=N.current;if(!B||!y)return[];const X={};for(const[te,re]of Object.entries(y))re==null||re===""||(X[te]=String(re));return Za(B,X,T.current)},Se=y=>{var $e,Ze;const B=()=>{C.setFields([{name:["environments","version"],errors:[a("modelService.ImageRequired")]}]),C.scrollToField(["environments","version"],{behavior:"smooth",block:"center"})},X=(Ze=($e=y.environments)==null?void 0:$e.image)==null?void 0:Ze.id;if(!X){B();return}const te=Bl(X);if(!te){B();return}const re=[{resourceType:"cpu",quantity:String(y.resource.cpu)},{resourceType:"mem",quantity:y.resource.mem}];y.resource.acceleratorType&&y.resource.accelerator&&y.resource.accelerator>0&&re.push({resourceType:y.resource.acceleratorType,quantity:String(y.resource.accelerator)});const oe=[];y.resource.shmem&&oe.push({name:"shmem",value:y.resource.shmem});const Ae=y.cluster_mode==="single-node"||y.cluster_mode==="multi-node"&&y.cluster_size===1?"SINGLE_NODE":"MULTI_NODE",Ve=y.vfoldersNameMap??{},Ee=(y.mount_ids??[]).map(Pe=>{var qe;const Ie=((qe=y.mount_id_map)==null?void 0:qe[Pe])||ee.current[Pe]||(Ve[Pe]?`/home/work/${Ve[Pe]}`:`/home/work/${Pe}`);return{vfolderId:nt(Pe),mountDestination:Ie}}),ze=(ne[y.runtimeVariantId]??"")==="custom",he=y.customDefinitionMode==="command",Ge={};for(const{variable:Pe,value:Ie}of y.environ??[])Pe&&(Ge[Pe]=Ie);const Ue=Object.entries(Ge).map(([Pe,Ie])=>({name:Pe,value:Ie})),Oe=!!y.commandEnableHealthCheck,Be=(()=>{const Pe={path:y.commandHealthCheck,interval:y.commandInterval,maxRetries:y.commandMaxRetries,maxWaitTime:y.commandMaxWaitTime,initialDelay:y.commandInitialDelay,expectedStatusCode:y.commandExpectedStatusCode};return f?Oe?{enable:!0,...Pe}:{enable:!1}:Oe?Pe:null})(),Qe=ze||!R?[]:Ke(y.runtimeParams),We=ze&&he&&y.startCommand?{models:[{name:"model",modelPath:y.commandModelMount??"/models",service:{preStartActions:[],startCommand:Xa(y.startCommand??""),port:y.commandPort??8e3,healthCheck:Be}}]}:Oe?{models:[{service:{healthCheck:Be}}]}:null,Re=ze&&he?y.commandModelMount??"/models":y.mountDestination||"/models";me({variables:{input:{deploymentId:ll((d==null?void 0:d.id)??"")??(d==null?void 0:d.id)??"",clusterConfig:{mode:Ae,size:y.cluster_size},resourceConfig:{resourceSlots:{entries:re},resourceOpts:oe.length>0?{entries:oe}:null},image:{id:te},modelRuntimeConfig:{runtimeVariantId:y.runtimeVariantId,environ:Ue.length>0?{entries:Ue}:null,...R&&{runtimeVariantPresetValues:Qe.length>0?Qe:null}},modelMountConfig:{vfolderId:ll(y.modelFolderId),mountDestination:Re,definitionPath:y.definitionPath},modelDefinition:We,extraMounts:Ee.length>0?Ee:null,options:{autoActivate:z}}},onCompleted:(Pe,Ie)=>{var qe,Ye;if(Ie&&Ie.length>0){const Xe=Ie[0],Je=(qe=Xe==null?void 0:Xe.message)==null?void 0:qe.includes("Another deployment is already in progress");r.error(Je?a("deployment.AnotherDeploymentInProgress"):(Xe==null?void 0:Xe.message)??a("general.ErrorOccurred"));return}C.resetFields(),r.success(a("deployment.RevisionAdded")),l(!0,(Ye=Pe.addModelRevision)==null?void 0:Ye.revision)},onError:Pe=>{var qe;const Ie=(qe=Pe.message)==null?void 0:qe.includes("Another deployment is already in progress");r.error(Ie?a("deployment.AnotherDeploymentInProgress"):Pe.message??a("general.ErrorOccurred"))}})},ae=y=>{me({variables:{input:{deploymentId:ll((d==null?void 0:d.id)??"")??(d==null?void 0:d.id)??"",revisionPresetId:y.revisionPresetId,modelMountConfig:{vfolderId:ll(y.modelFolderId),mountDestination:"/models"},options:{autoActivate:z}}},onCompleted:(B,X)=>{var te,re;if(X&&X.length>0){const oe=X[0],Ae=(te=oe==null?void 0:oe.message)==null?void 0:te.includes("Another deployment is already in progress");S.error("[DeploymentAddRevisionModal] addModelRevision (preset) returned errors",X),r.error(Ae?a("deployment.AnotherDeploymentInProgress"):(oe==null?void 0:oe.message)??a("general.ErrorOccurred"));return}A.resetFields(),r.success(a("deployment.RevisionAdded")),l(!0,(re=B.addModelRevision)==null?void 0:re.revision)},onError:B=>{var te;const X=(te=B.message)==null?void 0:te.includes("Another deployment is already in progress");S.error("[DeploymentAddRevisionModal] addModelRevision (preset) failed",B),r.error(X?a("deployment.AnotherDeploymentInProgress"):B.message??a("general.ErrorOccurred"))}})},fe=()=>{requestAnimationFrame(()=>{const y=document.querySelector(".ant-modal-body .ant-form-item-has-error");y&&y.scrollIntoView({behavior:"smooth",block:"start"})})},we=async()=>{const y=P==="preset"?A:C;try{await y.validateFields()}catch{fe();return}y.submit()};return n.jsxs(Ul,{open:s,title:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"md",wrap:"wrap",style:{paddingRight:u.paddingLG},children:[n.jsx("span",{children:a("deployment.AddRevision")}),n.jsx(wn,{value:P,onChange:pe,options:[{label:a("deployment.PresetMode"),value:"preset"},{label:a("deployment.CustomMode"),value:"custom"}],style:{fontWeight:"normal"}})]}),width:720,footer:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"sm",children:[n.jsx(Hn,{checked:z,onChange:y=>U(y.target.checked),disabled:P==="preset"&&le,children:a("deployment.AutoApply")}),n.jsxs(ie,{direction:"row",align:"center",gap:"xs",children:[n.jsx(gl,{onClick:()=>l(),children:a("button.Cancel")}),n.jsx(gl,{type:"primary",loading:Me,onClick:we,disabled:P==="preset"&&le,children:a("deployment.AddRevision")})]})]}),onCancel:()=>l(),confirmLoading:Me,destroyOnHidden:!0,...t,children:[c&&!i&&!L?n.jsx(Ll,{type:"info",showIcon:!0,style:{marginBottom:u.marginMD},title:a("deployment.CurrentRevisionAvailableDescription"),action:n.jsx(gl,{size:"small",onClick:ve,children:a("deployment.LoadCurrentRevision")})}):null,P==="preset"?le?n.jsx(Ll,{type:"info",showIcon:!0,style:{marginTop:u.marginXS},title:a("deployment.NoPresetsAvailable"),description:a("deployment.NoPresetsAvailableSwitchToCustom")}):n.jsxs(ge,{form:A,layout:"vertical",style:{marginTop:u.marginXS},onFinish:ae,onFinishFailed:fe,initialValues:{modelFolderId:O},children:[n.jsx(ge.Item,{label:a("modelStore.Preset"),tooltip:a("modelStore.PresetTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(M.Suspense,{fallback:n.jsx(Xl,{loading:!0,style:{flex:1}}),children:n.jsx(ge.Item,{name:"revisionPresetId",noStyle:!0,rules:[{required:!0}],children:n.jsx(pa,{style:{flex:1}})})}),n.jsx(ge.Item,{dependencies:["revisionPresetId"],noStyle:!0,children:({getFieldValue:y})=>{const B=y("revisionPresetId");return n.jsx(Zl.Compact,{children:n.jsx(ml,{title:a("modelService.DeploymentPresetDetail"),children:n.jsx(gl,{icon:n.jsx(fa,{}),disabled:!B,onClick:()=>{B&&Z(B)}})})})}})]})}),n.jsx(ge.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(M.Suspense,{fallback:n.jsx(Xl,{loading:!0,style:{flex:1}}),children:n.jsx(ge.Item,{name:"modelFolderId",label:a("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(Un,{ref:x,currentProjectId:h??void 0,disabled:!h,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(ge.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:y})=>{const B=y("modelFolderId");return n.jsxs(Zl.Compact,{children:[n.jsx(ml,{title:a("modelService.OpenFolder"),children:n.jsx(gl,{icon:n.jsx(Gn,{}),disabled:!B,onClick:()=>{B&&p(ll(B))}})}),n.jsx(ml,{title:a("data.CreateANewStorageFolder"),children:n.jsx(gl,{icon:n.jsx(jl,{}),onClick:()=>D(!0)})}),n.jsx(ml,{title:a("button.Refresh"),children:n.jsx(gl,{icon:n.jsx($n,{}),onClick:()=>{M.startTransition(()=>{var X;(X=x.current)==null||X.refetch()})}})})]})}})]})})]},"preset-form"):n.jsxs(ge,{form:C,layout:"vertical",style:{marginTop:u.marginXS},onFinish:Se,onFinishFailed:fe,initialValues:ba({},xa,{resourceGroup:(He=d==null?void 0:d.metadata)==null?void 0:He.resourceGroupName,customDefinitionMode:"command",commandEnableHealthCheck:!1,environ:[]}),children:[n.jsx(fn,{children:a("deployment.step.ModelAndRuntime")}),n.jsx(ge.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(M.Suspense,{fallback:n.jsx(Xl,{loading:!0,style:{flex:1}}),children:n.jsx(ge.Item,{name:"modelFolderId",label:a("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(Un,{ref:F,currentProjectId:h??void 0,disabled:!h,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(ge.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:y})=>{const B=y("modelFolderId");return n.jsxs(Zl.Compact,{children:[n.jsx(ml,{title:a("modelService.OpenFolder"),children:n.jsx(gl,{icon:n.jsx(Gn,{}),disabled:!B,onClick:()=>{B&&p(ll(B))}})}),n.jsx(ml,{title:a("data.CreateANewStorageFolder"),children:n.jsx(gl,{icon:n.jsx(jl,{}),onClick:()=>D(!0)})}),n.jsx(ml,{title:a("button.Refresh"),children:n.jsx(gl,{icon:n.jsx($n,{}),onClick:()=>{M.startTransition(()=>{var X;(X=F.current)==null||X.refetch()})}})})]})}})]})}),n.jsx(M.Suspense,{fallback:n.jsx(Xl,{loading:!0,style:{width:"100%"}}),children:n.jsx(ge.Item,{name:"runtimeVariantId",label:a("deployment.RuntimeVariant"),tooltip:a("deployment.RuntimeVariantTooltip"),rules:[{required:!0},{warningOnly:!0,validator:async(y,B)=>{const X=ne[B];return X&&X!=="custom"?Promise.reject(a("modelService.RuntimeVariantDefaultCommandAppliedNote")):Promise.resolve()}}],children:n.jsx(ci,{onResolvedNamesChange:y=>K(B=>({...B,...y}))})})}),n.jsx(ge.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:y})=>{const B=y("runtimeVariantId"),X=ne[B];return!X||X==="custom"?null:n.jsx("div",{style:{marginBottom:u.marginMD},children:n.jsx(M.Suspense,{fallback:null,children:n.jsx(Ja,{runtimeVariant:X,onTouchedKeysChange:te=>{T.current=te},onGroupsLoaded:te=>{N.current=te},initialPresetValues:H})})})}}),n.jsx(ge.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:y})=>{const B=y("runtimeVariantId");return ne[B]!=="custom"?null:n.jsxs(n.Fragment,{children:[n.jsx(ge.Item,{name:"customDefinitionMode",noStyle:!0,children:n.jsx(wn,{options:[{label:a("modelService.EnterCommand"),value:"command"},{label:a("modelService.UseConfigFile"),value:"file"}],style:{marginBottom:u.marginMD}})}),n.jsx(ge.Item,{dependencies:["customDefinitionMode"],noStyle:!0,children:({getFieldValue:te})=>te("customDefinitionMode")==="command"?n.jsxs(n.Fragment,{children:[n.jsx(ge.Item,{name:"startCommand",label:a("modelService.StartCommand"),tooltip:a("modelService.StartCommandTooltip"),extra:a("modelService.StartCommandHelperShell"),rules:[{required:!0,whitespace:!0}],children:n.jsx(Gl.TextArea,{placeholder:a("modelService.StartCommandPlaceholder"),autoSize:{minRows:2}})}),n.jsx(ge.Item,{name:"commandModelMount",label:a("modelService.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),children:n.jsx(Gl,{placeholder:"/models",allowClear:!0})}),n.jsx(ge.Item,{name:"commandPort",label:a("modelService.Port"),tooltip:a("modelService.PortTooltip"),children:n.jsx(yl,{min:2,max:65535,placeholder:"8000",style:{width:"100%"}})})]}):n.jsxs(ie,{gap:"sm",children:[n.jsx(ge.Item,{name:"mountDestination",label:a("deployment.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),rules:[{required:!0}],style:{flex:1},children:n.jsx(Gl,{allowClear:!0,placeholder:"/models"})}),n.jsx(ge.Item,{name:"definitionPath",label:a("deployment.ModelDefinitionPath"),tooltip:a("modelService.ModelDefinitionPathTooltip"),style:{flex:1},children:n.jsx(Gl,{allowClear:!0,placeholder:"model-definition.yaml"})})]})})]})}}),n.jsx(ge.Item,{name:"commandEnableHealthCheck",valuePropName:"checked",style:{marginBottom:u.marginXS},children:n.jsx(Hn,{children:a("modelService.EnableHealthCheck")})}),n.jsx(ge.Item,{dependencies:["commandEnableHealthCheck"],noStyle:!0,children:({getFieldValue:y})=>y("commandEnableHealthCheck")?n.jsxs(ie,{direction:"column",align:"stretch",gap:"xs",children:[n.jsx(ge.Item,{name:"commandHealthCheck",label:a("adminDeploymentPreset.modelDef.HealthCheckPath"),tooltip:a("modelService.HealthCheckTooltip"),rules:[{required:!0}],children:n.jsx(Gl,{placeholder:a("general.Example",{value:"/health"}),allowClear:!0})}),n.jsxs(ie,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(ge.Item,{name:"commandInterval",label:a("adminDeploymentPreset.modelDef.HealthCheckInterval"),tooltip:a("modelService.IntervalTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(yl,{min:1,placeholder:a("general.Example",{value:"10"}),suffix:a("time.Sec"),style:{width:"100%"}})}),n.jsx(ge.Item,{name:"commandMaxRetries",label:a("adminDeploymentPreset.modelDef.HealthCheckMaxRetries"),tooltip:a("modelService.MaxRetriesTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(yl,{min:1,placeholder:a("general.Example",{value:"10"}),style:{width:"100%"}})}),n.jsx(ge.Item,{name:"commandMaxWaitTime",label:a("adminDeploymentPreset.modelDef.HealthCheckMaxWaitTime"),tooltip:a("modelService.MaxWaitTimeTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(yl,{min:1,placeholder:a("general.Example",{value:"15"}),suffix:a("time.Sec"),style:{width:"100%"}})})]}),n.jsxs(ie,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(ge.Item,{name:"commandExpectedStatusCode",label:a("adminDeploymentPreset.modelDef.HealthCheckExpectedStatus"),tooltip:a("modelService.ExpectedStatusTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(yl,{min:101,max:599,placeholder:a("general.Example",{value:"200"}),style:{width:"100%"}})}),n.jsx(ge.Item,{name:"commandInitialDelay",label:a("adminDeploymentPreset.modelDef.HealthCheckInitialDelay"),tooltip:a("modelService.InitialDelayTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(yl,{min:0,placeholder:a("general.Example",{value:"60"}),suffix:a("time.Sec"),style:{width:"100%"}})}),n.jsx("div",{style:{flex:1,minWidth:160}})]})]}):null}),n.jsx(fn,{children:a("session.launcher.Environments")}),n.jsx(M.Suspense,{fallback:n.jsx(Fl,{active:!0,paragraph:{rows:2}}),children:n.jsx(ka,{})}),n.jsx(Sa,{name:"environ",formItemProps:{validateTrigger:["onChange","onBlur"]}}),n.jsx(fn,{children:a("deployment.step.ClusterAndResources")}),n.jsx(M.Suspense,{fallback:n.jsx(Fl,{active:!0,paragraph:{rows:4}}),children:n.jsx(ha,{enableResourcePresets:!0,hideResourceGroupFormItem:!0})}),n.jsx(va,{items:[{key:"advanced",label:a("session.launcher.AdvancedSettings"),children:n.jsx(M.Suspense,{fallback:n.jsx(Fl,{active:!0}),children:n.jsx(ge.Item,{noStyle:!0,dependencies:["modelFolderId","mount_id_map","mount_ids"],children:({getFieldValue:y})=>{var te;const B=y("modelFolderId"),X=B?(te=Bl(String(B)))==null?void 0:te.replace(/-/g,""):void 0;return n.jsx(Fa,{label:a("modelService.AdditionalMounts"),tooltip:a("modelService.AdditionalMountsTooltip"),rowKey:"id",tableProps:{scroll:{x:"max-content",y:300}},rowFilter:re=>{var oe;return re.usage_mode!=="model"&&re.status==="ready"&&!((oe=re.name)!=null&&oe.startsWith("."))&&re.id!==X}})}})})}]})]},"custom-form"),J&&n.jsx(M.Suspense,{fallback:null,children:n.jsx($i,{presetId:J,onCancel:()=>Z(null)})}),n.jsx(Ra,{open:I,initialValues:{usage_mode:"model"},onRequestClose:y=>{if(D(!1),y!=null&&y.id){const B=Bl(y.id);if(!B)return;const X=Jl("VirtualFolderNode",B),te=P==="preset"?A:C,re=P==="preset"?x:F;te.setFieldValue("modelFolderId",X),M.startTransition(()=>{var oe;(oe=re.current)==null||oe.refetch()})}}})]})},Et={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Et.hash="129d74dafb7ab8394c47065f3b9af25e";const Ot=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAutoScalingRulePayload",kind:"LinkedField",name:"deleteAutoScalingRule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleListDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleListDeleteMutation",selections:e},params:{cacheID:"84fac37f17347340ba1f6a7991bc3624",id:null,metadata:{},name:"AutoScalingRuleListDeleteMutation",operationKind:"mutation",text:`mutation AutoScalingRuleListDeleteMutation(
  $input: DeleteAutoScalingRuleInput!
) {
  deleteAutoScalingRule(input: $input) {
    id
  }
}
`}}}();Ot.hash="c0d22df767771306d1fc0a431e5d177b";const $t=function(){var l=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleListPresetsQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleListPresetsQuery",selections:l},params:{cacheID:"9b99973a6bf38ac02bd91f644c8cb1a1",id:null,metadata:{},name:"AutoScalingRuleListPresetsQuery",operationKind:"query",text:`query AutoScalingRuleListPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();$t.hash="7f4c998b34def6faefe25959c5cb64e2";const wt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"AutoScalingRuleListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:u,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[r,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[o,d,{args:null,kind:"FragmentSpread",name:"AutoScalingRuleListNodesFragment"},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,s,i,t,e],kind:"Operation",name:"AutoScalingRuleListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:u,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[r,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[o,d,{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},o],storageKey:null}]},params:{cacheID:"79f124acac426955bf7fe564f6d9a5c1",id:null,metadata:{},name:"AutoScalingRuleListQuery",operationKind:"query",text:`query AutoScalingRuleListQuery(
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
`}}}();wt.hash="bfa849a7cb503e04b249b2f73510b568";const Ht={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"AutoScalingRuleListNodesFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],type:"AutoScalingRule",abstractKey:null};Ht.hash="54a32b764fc7e506f5bddfe218691cd2";const Bt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"UpdateAutoScalingRulePayload",kind:"LinkedField",name:"updateAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalUpdateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalUpdateMutation",selections:e},params:{cacheID:"f5194bd994f4693e29536fec36e4f0e4",id:null,metadata:{},name:"AutoScalingRuleEditorModalUpdateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalUpdateMutation(
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
`}}}();Bt.hash="8e953443e1aa963b955810e5f97de017";const Qt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAutoScalingRulePayload",kind:"LinkedField",name:"createAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalCreateMutation",selections:e},params:{cacheID:"c7c250dabfc49b66cf1aebbff6414d44",id:null,metadata:{},name:"AutoScalingRuleEditorModalCreateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalCreateMutation(
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
`}}}();Qt.hash="7afa475334295923b7754d0563a8b919";const qt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],type:"AutoScalingRule",abstractKey:null};qt.hash="9dff1f6ce3b17626029eee3484220a7d";const zt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[l,e,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"categoryId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queryTemplate",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,concreteType:"QueryPresetCategory",kind:"LinkedField",name:"category",plural:!1,selections:[l,e],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalPresetsQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleEditorModalPresetsQuery",selections:i},params:{cacheID:"04d06fec5284e709aaee3606d8a4bb53",id:null,metadata:{},name:"AutoScalingRuleEditorModalPresetsQuery",operationKind:"query",text:`query AutoScalingRuleEditorModalPresetsQuery {
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
`}}}();zt.hash="6582d4cf067148f5b39755e919c0f4f2";const kn={KERNEL:["cpu_util","mem","net_rx","net_tx"],INFERENCE_FRAMEWORK:[]},Yn=l=>l?l.minThreshold!=null&&l.maxThreshold!=null?"scale_in_out":l.maxThreshold!=null?"scale_out":"scale_in":"scale_out",wi=l=>{"use memo";var ul;const e=tl.c(195),{autoScalingRule:i,formRef:s}=l,{t}=rl(),{token:a}=Cl.useToken(),u=Nn();let r;e[0]!==u?(r=u.supports("prometheus-auto-scaling-rule"),e[0]=u,e[1]=r):r=e[1];const o=r;let d,g;e[2]===Symbol.for("react.memo_cache_sentinel")?(d=zt,g={},e[2]=d,e[3]=g):(d=e[2],g=e[3]);const{prometheusQueryPresets:c}=Le.useLazyLoadQuery(d,g);let k;e[4]!==(c==null?void 0:c.edges)?(k=Ia(bl(c==null?void 0:c.edges,Bi)),e[4]=c==null?void 0:c.edges,e[5]=k):k=e[5];const h=k;let S;e[6]!==i?(S=Yn(i),e[6]=i,e[7]=S):S=e[7];const[p,m]=M.useState(S),[f,R]=M.useState((i==null?void 0:i.metricSource)||"KERNEL");let x;e[8]!==i||e[9]!==h?(x=i!=null&&i.prometheusQueryPresetId?(ul=h.find(Te=>ll(Te.id)===i.prometheusQueryPresetId))==null?void 0:ul.id:void 0,e[8]=i,e[9]=h,e[10]=x):x=e[10];const[F,I]=M.useState(x);let D;e[11]!==(i==null?void 0:i.metricSource)?(D=kn[(i==null?void 0:i.metricSource)||"KERNEL"]||[],e[11]=i==null?void 0:i.metricSource,e[12]=D):D=e[12];const[C,A]=M.useState(D);let z;if(e[13]!==h||e[14]!==F){let Te;e[16]!==F?(Te=_e=>_e.id===F,e[16]=F,e[17]=Te):Te=e[17],z=h.find(Te),e[13]=h,e[14]=F,e[15]=z}else z=e[15];const U=z;let w;if(e[18]!==h){const Te=li(h,["rank"],["asc"]),_e=Te.filter(Qi),sl=Te.filter(qi),il=zi,dl=Da(_e,Ui),xl=Object.entries(dl).map(hl=>{const[Ne,vl]=hl;return{label:Ne,options:vl.map(il)}});w=sl.length>0?[...xl,...sl.map(il)]:xl,e[18]=h,e[19]=w}else w=e[19];const Q=w;let P;e[20]!==i||e[21]!==F?(P=()=>{if(i){const Te=Yn(i);let _e;return Te==="scale_in"&&i.minThreshold!=null?_e=Number(i.minThreshold):Te==="scale_out"&&i.maxThreshold!=null&&(_e=Number(i.maxThreshold)),{metricSource:i.metricSource,metricName:i.metricName,prometheusQueryPresetId:F,conditionMode:Te,threshold:_e,minThreshold:i.minThreshold!=null?Number(i.minThreshold):void 0,maxThreshold:i.maxThreshold!=null?Number(i.maxThreshold):void 0,stepSize:Math.abs(i.stepSize),timeWindow:i.timeWindow,minReplicas:i.minReplicas??void 0,maxReplicas:i.maxReplicas??void 0}}return{metricSource:"KERNEL",conditionMode:"scale_out",stepSize:1,timeWindow:300,minReplicas:0,maxReplicas:5}},e[20]=i,e[21]=F,e[22]=P):P=e[22];const L=P,E=f==="PROMETHEUS";let j;e[23]!==L?(j=L(),e[23]=L,e[24]=j):j=e[24];let Y;e[25]!==t?(Y=t("autoScalingRule.MetricSource"),e[25]=t,e[26]=Y):Y=e[26];let W;e[27]!==t?(W=t("autoScalingRule.MetricSourceTooltip"),e[27]=t,e[28]=W):W=e[28];let q;e[29]===Symbol.for("react.memo_cache_sentinel")?(q=[{required:!0}],e[29]=q):q=e[29];let V;e[30]!==s?(V=Te=>{var _e,sl;if(R(Te),(_e=s.current)==null||_e.setFieldsValue({metricName:void 0}),Te!=="PROMETHEUS")A(kn[Te]||[]),I(void 0);else{const il=(sl=s.current)==null?void 0:sl.getFieldValue("prometheusQueryPresetId");il&&I(il)}},e[30]=s,e[31]=V):V=e[31];let v;e[32]!==t?(v=t("autoScalingRule.MetricSourceKernel"),e[32]=t,e[33]=v):v=e[33];let b;e[34]!==v?(b={label:v,value:"KERNEL"},e[34]=v,e[35]=b):b=e[35];let _;e[36]!==o||e[37]!==t?(_=o?[]:[{label:t("autoScalingRule.MetricSourceInferenceFramework"),value:"INFERENCE_FRAMEWORK"}],e[36]=o,e[37]=t,e[38]=_):_=e[38];let J;e[39]!==t?(J=t("autoScalingRule.MetricSourcePrometheus"),e[39]=t,e[40]=J):J=e[40];let Z;e[41]!==J?(Z={label:J,value:"PROMETHEUS"},e[41]=J,e[42]=Z):Z=e[42];let ne;e[43]!==b||e[44]!==_||e[45]!==Z?(ne=[b,..._,Z],e[43]=b,e[44]=_,e[45]=Z,e[46]=ne):ne=e[46];let K;e[47]!==V||e[48]!==ne?(K=n.jsx(Fn,{onChange:V,options:ne}),e[47]=V,e[48]=ne,e[49]=K):K=e[49];let T;e[50]!==Y||e[51]!==W||e[52]!==K?(T=n.jsx(ge.Item,{label:Y,name:"metricSource",tooltip:W,rules:q,children:K}),e[50]=Y,e[51]=W,e[52]=K,e[53]=T):T=e[53];let N;e[54]!==t?(N=t("autoScalingRule.MetricName"),e[54]=t,e[55]=N):N=e[55];let H;e[56]!==t?(H=t("autoScalingRule.MetricNameTooltip"),e[56]=t,e[57]=H):H=e[57];const G=!E;let ee;e[58]!==G?(ee=[{required:G}],e[58]=G,e[59]=ee):ee=e[59];let le;e[60]!==t?(le=t("autoScalingRule.MetricName"),e[60]=t,e[61]=le):le=e[61];let $;e[62]!==C?($=bl(C,Wi),e[62]=C,e[63]=$):$=e[63];let O;e[64]!==s?(O={onSearch:Te=>{var sl;const _e=((sl=s.current)==null?void 0:sl.getFieldValue("metricSource"))||"KERNEL";A(Ca(kn[_e]||[],il=>il.includes(Te)))}},e[64]=s,e[65]=O):O=e[65];let Fe;e[66]!==le||e[67]!==$||e[68]!==O?(Fe=n.jsx(Ma,{placeholder:le,options:$,showSearch:O,allowClear:!0,popupMatchSelectWidth:!1}),e[66]=le,e[67]=$,e[68]=O,e[69]=Fe):Fe=e[69];let ke;e[70]!==E||e[71]!==N||e[72]!==H||e[73]!==ee||e[74]!==Fe?(ke=n.jsx(ge.Item,{label:N,name:"metricName",hidden:E,tooltip:H,rules:ee,children:Fe}),e[70]=E,e[71]=N,e[72]=H,e[73]=ee,e[74]=Fe,e[75]=ke):ke=e[75];let me;e[76]!==s||e[77]!==E||e[78]!==h||e[79]!==Q||e[80]!==U||e[81]!==t||e[82]!==a.fontSizeSM?(me=E&&n.jsx(n.Fragment,{children:n.jsx(ge.Item,{label:`${t("autoScalingRule.MetricName")} (${t("autoScalingRule.PrometheusPreset")})`,name:"prometheusQueryPresetId",tooltip:t("autoScalingRule.PrometheusPresetTooltip"),rules:[{required:!0,message:t("autoScalingRule.PrometheusPresetRequired")}],extra:U?n.jsx(ei,{queryTemplate:U.queryTemplate},U.id):void 0,children:n.jsx(Fn,{onChange:Te=>{var sl,il;I(Te);const _e=h.find(dl=>dl.id===Te);if(_e){(sl=s.current)==null||sl.setFieldsValue({metricName:_e.metricName});const dl=_e.timeWindow!=null?Number(_e.timeWindow):void 0;dl!=null&&!isNaN(dl)&&((il=s.current)==null||il.setFieldsValue({timeWindow:dl}))}},placeholder:t("autoScalingRule.SelectPrometheusPreset"),showSearch:{filterOption:Gi},options:Q,optionRender:Te=>n.jsxs(ie,{direction:"column",align:"start",children:[Te.label,Te.data.description&&n.jsx(nl.Text,{type:"secondary",style:{fontSize:a.fontSizeSM},ellipsis:!0,children:Te.data.description})]}),allowClear:!0,onClear:()=>I(void 0)})})}),e[76]=s,e[77]=E,e[78]=h,e[79]=Q,e[80]=U,e[81]=t,e[82]=a.fontSizeSM,e[83]=me):me=e[83];let Me;e[84]!==t?(Me=t("autoScalingRule.Condition"),e[84]=t,e[85]=Me):Me=e[85];let ye;e[86]!==t?(ye=t("autoScalingRule.ConditionTooltip"),e[86]=t,e[87]=ye):ye=e[87];let pe;e[88]===Symbol.for("react.memo_cache_sentinel")?(pe=Te=>{m(Te.target.value)},e[88]=pe):pe=e[88];let ue;e[89]!==a.marginSM?(ue={marginBottom:a.marginSM},e[89]=a.marginSM,e[90]=ue):ue=e[90];let de;e[91]!==t?(de=t("autoScalingRule.ScaleIn"),e[91]=t,e[92]=de):de=e[92];let se;e[93]!==de?(se={label:de,value:"scale_in"},e[93]=de,e[94]=se):se=e[94];let ce;e[95]!==t?(ce=t("autoScalingRule.ScaleOut"),e[95]=t,e[96]=ce):ce=e[96];let be;e[97]!==ce?(be={label:ce,value:"scale_out"},e[97]=ce,e[98]=be):be=e[98];let ve;e[99]!==t?(ve=t("autoScalingRule.ScaleInAndOut"),e[99]=t,e[100]=ve):ve=e[100];let Ke;e[101]!==ve?(Ke={label:ve,value:"scale_in_out"},e[101]=ve,e[102]=Ke):Ke=e[102];let Se;e[103]!==se||e[104]!==be||e[105]!==Ke?(Se=[se,be,Ke],e[103]=se,e[104]=be,e[105]=Ke,e[106]=Se):Se=e[106];let ae;e[107]!==ue||e[108]!==Se?(ae=n.jsx(ge.Item,{name:"conditionMode",noStyle:!0,children:n.jsx(Aa.Group,{optionType:"button",onChange:pe,style:ue,options:Se})}),e[107]=ue,e[108]=Se,e[109]=ae):ae=e[109];let fe;e[110]!==p||e[111]!==t?(fe=p==="scale_in"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(nl.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ge.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),e[110]=p,e[111]=t,e[112]=fe):fe=e[112];let we;e[113]!==p||e[114]!==t?(we=p==="scale_out"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ge.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(nl.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]}),e[113]=p,e[114]=t,e[115]=we):we=e[115];let De;e[116]!==p||e[117]!==t?(De=p==="scale_in_out"&&n.jsxs(ie,{direction:"column",gap:"xs",align:"stretch",children:[n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(nl.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ge.Item,{name:"minThreshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.MinThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ge.Item,{name:"maxThreshold",noStyle:!0,dependencies:["minThreshold"],rules:[{required:!0,message:t("autoScalingRule.MaxThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")},Te=>{const{getFieldValue:_e}=Te;return{validator(sl,il){const dl=_e("minThreshold");return dl!=null&&il!=null&&dl>=il?Promise.reject(new Error(t("autoScalingRule.MinMustBeLessThanMax"))):Promise.resolve()}}}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(nl.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]})]}),e[116]=p,e[117]=t,e[118]=De):De=e[118];let xe;e[119]!==Me||e[120]!==ye||e[121]!==ae||e[122]!==fe||e[123]!==we||e[124]!==De?(xe=n.jsxs(ge.Item,{label:Me,required:!0,tooltip:ye,children:[ae,fe,we,De]}),e[119]=Me,e[120]=ye,e[121]=ae,e[122]=fe,e[123]=we,e[124]=De,e[125]=xe):xe=e[125];let He;e[126]!==t?(He=t("autoScalingRule.StepSize"),e[126]=t,e[127]=He):He=e[127];let y;e[128]!==t?(y=t("autoScalingRule.StepSizeTooltip"),e[128]=t,e[129]=y):y=e[129];let B,X;e[130]===Symbol.for("react.memo_cache_sentinel")?(B={required:!0},X={type:"number",min:1,max:Yl},e[130]=B,e[131]=X):(B=e[130],X=e[131]);let te;e[132]!==t?(te=[B,X,{validator:(Te,_e)=>_e%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[132]=t,e[133]=te):te=e[133];let re;e[134]===Symbol.for("react.memo_cache_sentinel")?(re={width:"100%"},e[134]=re):re=e[134];const oe=p==="scale_in_out"?"±":p==="scale_out"?"+":"−";let Ae;e[135]!==oe?(Ae=n.jsx(yl,{min:1,step:1,style:re,prefix:n.jsx(nl.Text,{type:"secondary",children:oe})}),e[135]=oe,e[136]=Ae):Ae=e[136];let Ve;e[137]!==He||e[138]!==y||e[139]!==te||e[140]!==Ae?(Ve=n.jsx(ge.Item,{label:He,name:"stepSize",tooltip:y,rules:te,children:Ae}),e[137]=He,e[138]=y,e[139]=te,e[140]=Ae,e[141]=Ve):Ve=e[141];let Ee;e[142]!==t?(Ee=t("autoScalingRule.CoolDownSeconds"),e[142]=t,e[143]=Ee):Ee=e[143];let je;e[144]!==t?(je=t("autoScalingRule.CoolDownTooltip"),e[144]=t,e[145]=je):je=e[145];let ze,he;e[146]===Symbol.for("react.memo_cache_sentinel")?(ze={required:!0},he={type:"number",min:1},e[146]=ze,e[147]=he):(ze=e[146],he=e[147]);let Ge;e[148]!==t?(Ge=[ze,he,{validator:(Te,_e)=>_e%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[148]=t,e[149]=Ge):Ge=e[149];let Ue;e[150]===Symbol.for("react.memo_cache_sentinel")?(Ue={width:"100%"},e[150]=Ue):Ue=e[150];let Oe;e[151]!==t?(Oe=t("autoScalingRule.Seconds"),e[151]=t,e[152]=Oe):Oe=e[152];let Be;e[153]!==Oe?(Be=n.jsx(yl,{min:1,step:1,style:Ue,suffix:n.jsx(nl.Text,{type:"secondary",children:Oe})}),e[153]=Oe,e[154]=Be):Be=e[154];let Qe;e[155]!==Ee||e[156]!==je||e[157]!==Ge||e[158]!==Be?(Qe=n.jsx(ge.Item,{label:Ee,name:"timeWindow",tooltip:je,rules:Ge,children:Be}),e[155]=Ee,e[156]=je,e[157]=Ge,e[158]=Be,e[159]=Qe):Qe=e[159];let We;e[160]!==t?(We=t("autoScalingRule.MinReplicas"),e[160]=t,e[161]=We):We=e[161];let Re;e[162]!==t?(Re=t("autoScalingRule.MinReplicasTooltip"),e[162]=t,e[163]=Re):Re=e[163];let $e;e[164]===Symbol.for("react.memo_cache_sentinel")?($e={min:0,max:Yl,type:"number"},e[164]=$e):$e=e[164];let Ze;e[165]!==t?(Ze=[$e,{validator:(Te,_e)=>_e!=null&&_e%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[165]=t,e[166]=Ze):Ze=e[166];let Pe;e[167]===Symbol.for("react.memo_cache_sentinel")?(Pe=n.jsx(yl,{min:0,max:Yl,style:{width:"100%"}}),e[167]=Pe):Pe=e[167];let Ie;e[168]!==We||e[169]!==Re||e[170]!==Ze?(Ie=n.jsx(ge.Item,{label:We,name:"minReplicas",tooltip:Re,rules:Ze,children:Pe}),e[168]=We,e[169]=Re,e[170]=Ze,e[171]=Ie):Ie=e[171];let qe;e[172]!==t?(qe=t("autoScalingRule.MaxReplicas"),e[172]=t,e[173]=qe):qe=e[173];let Ye;e[174]!==t?(Ye=t("autoScalingRule.MaxReplicasTooltip"),e[174]=t,e[175]=Ye):Ye=e[175];let Xe;e[176]===Symbol.for("react.memo_cache_sentinel")?(Xe={min:0,max:Yl,type:"number"},e[176]=Xe):Xe=e[176];let Je;e[177]!==t?(Je=[Xe,{validator:(Te,_e)=>_e!=null&&_e%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[177]=t,e[178]=Je):Je=e[178];let ol;e[179]===Symbol.for("react.memo_cache_sentinel")?(ol=n.jsx(yl,{min:0,max:Yl,style:{width:"100%"}}),e[179]=ol):ol=e[179];let Ce;e[180]!==qe||e[181]!==Ye||e[182]!==Je?(Ce=n.jsx(ge.Item,{label:qe,name:"maxReplicas",tooltip:Ye,rules:Je,children:ol}),e[180]=qe,e[181]=Ye,e[182]=Je,e[183]=Ce):Ce=e[183];let al;return e[184]!==s||e[185]!==j||e[186]!==T||e[187]!==ke||e[188]!==me||e[189]!==xe||e[190]!==Ve||e[191]!==Qe||e[192]!==Ie||e[193]!==Ce?(al=n.jsxs(ge,{ref:s,layout:"vertical",initialValues:j,children:[T,ke,me,xe,Ve,Qe,Ie,Ce]}),e[184]=s,e[185]=j,e[186]=T,e[187]=ke,e[188]=me,e[189]=xe,e[190]=Ve,e[191]=Qe,e[192]=Ie,e[193]=Ce,e[194]=al):al=e[194],al},Hi=l=>{"use memo";const e=tl.c(34);let i,s,t,a,u;e[0]!==l?({onRequestClose:u,onComplete:a,modelDeploymentId:t,autoScalingRuleFrgmt:i,...s}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5]);const{t:r}=rl(),{message:o}=Nl.useApp(),{logger:d}=zl();let g;e[6]===Symbol.for("react.memo_cache_sentinel")?(g=qt,e[6]=g):g=e[6];const c=Le.useFragment(g,i??null),k=M.useRef(null);let h;e[7]===Symbol.for("react.memo_cache_sentinel")?(h=Qt,e[7]=h):h=e[7];const[S,p]=Le.useMutation(h);let m;e[8]===Symbol.for("react.memo_cache_sentinel")?(m=Bt,e[8]=m):m=e[8];const[f,R]=Le.useMutation(m);let x;e[9]!==c||e[10]!==S||e[11]!==f||e[12]!==d||e[13]!==o||e[14]!==t||e[15]!==a||e[16]!==u||e[17]!==r?(x=()=>{var P;return(P=k.current)==null?void 0:P.validateFields().then(L=>{let E=null,j=null;L.conditionMode==="scale_in_out"?(E=L.minThreshold??null,j=L.maxThreshold??null):L.conditionMode==="scale_in"?E=L.threshold??null:j=L.threshold??null;const Y=L.metricName,W=L.metricSource==="PROMETHEUS"&&L.prometheusQueryPresetId?ll(L.prometheusQueryPresetId):null;c?f({variables:{input:{id:ll(c.id),metricSource:L.metricSource,metricName:Y,minThreshold:E!=null?String(E):null,maxThreshold:j!=null?String(j):null,stepSize:L.stepSize,timeWindow:L.timeWindow,minReplicas:L.minReplicas,maxReplicas:L.maxReplicas,prometheusQueryPresetId:W??void 0}},onCompleted:(q,V)=>{if(V&&V.length>0){const v=bl(V,Yi);for(const b of v)o.error(b);return}o.success(r("autoScalingRule.SuccessfullyUpdated")),a==null||a(),u(!0)},onError:q=>{o.error(q.message)}}):S({variables:{input:{modelDeploymentId:t,metricSource:L.metricSource,metricName:Y,minThreshold:E!=null?String(E):null,maxThreshold:j!=null?String(j):null,stepSize:L.stepSize,timeWindow:L.timeWindow,minReplicas:L.minReplicas,maxReplicas:L.maxReplicas,prometheusQueryPresetId:W??void 0}},onCompleted:(q,V)=>{if(V&&V.length>0){const v=bl(V,Xi);for(const b of v)o.error(b);return}o.success(r("autoScalingRule.SuccessfullyCreated")),a==null||a(),u(!0)},onError:q=>{o.error(q.message)}})}).catch(L=>{d.error(L)})},e[9]=c,e[10]=S,e[11]=f,e[12]=d,e[13]=o,e[14]=t,e[15]=a,e[16]=u,e[17]=r,e[18]=x):x=e[18];const F=x;let I;e[19]!==u?(I=()=>{u(!1)},e[19]=u,e[20]=I):I=e[20];const D=I;let C;e[21]!==c||e[22]!==r?(C=r(c?"autoScalingRule.EditAutoScalingRule":"autoScalingRule.AddAutoScalingRule"),e[21]=c,e[22]=r,e[23]=C):C=e[23];const A=p||R;let z;e[24]===Symbol.for("react.memo_cache_sentinel")?(z=n.jsx(Fl,{active:!0,paragraph:{rows:6}}),e[24]=z):z=e[24];const U=c??null;let w;e[25]!==U?(w=n.jsx(it,{children:n.jsx(Ka.Suspense,{fallback:z,children:n.jsx(wi,{autoScalingRule:U,formRef:k})})}),e[25]=U,e[26]=w):w=e[26];let Q;return e[27]!==s||e[28]!==D||e[29]!==F||e[30]!==w||e[31]!==C||e[32]!==A?(Q=n.jsx(Ul,{...s,onOk:F,onCancel:D,centered:!0,title:C,confirmLoading:A,children:w}),e[27]=s,e[28]=D,e[29]=F,e[30]=w,e[31]=C,e[32]=A,e[33]=Q):Q=e[33],Q};function Bi(l){return l==null?void 0:l.node}function Qi(l){var e;return(e=l.category)==null?void 0:e.name}function qi(l){var e;return!((e=l.category)!=null&&e.name)}function zi(l){return{label:l.name,value:l.id,description:l.description}}function Ui(l){return l.category.name}function Wi(l){return{label:l,value:l}}function Gi(l,e){return String((e==null?void 0:e.label)??"").toLowerCase().includes(l.toLowerCase())}function Yi(l){return l.message}function Xi(l){return l.message}const Ji=(l,e,i)=>{const s=l.metricSource==="PROMETHEUS"&&l.prometheusQueryPresetId?(i==null?void 0:i.get(l.prometheusQueryPresetId))??l.metricName:l.metricName,t=l.minThreshold,a=l.maxThreshold;return t!=null&&a!=null?n.jsxs(ie,{direction:"column",gap:"xxs",children:[n.jsxs(ie,{gap:"xs",children:[n.jsx(dn,{children:s})," < ",t]}),n.jsxs(ie,{gap:"xs",children:[a," < ",n.jsx(dn,{children:s})]})]}):a!=null?n.jsxs(ie,{gap:"xs",children:[a,n.jsx(ml,{title:e("autoScalingRule.MaxThreshold"),children:"<"}),n.jsx(dn,{children:s})]}):t!=null?n.jsxs(ie,{gap:"xs",children:[n.jsx(dn,{children:s}),n.jsx(ml,{title:e("autoScalingRule.MinThreshold"),children:"<"}),t]}):"-"},un=l=>{const e={};return l.createdAt&&(e.createdAt=l.createdAt),l.lastTriggeredAt&&(e.lastTriggeredAt=l.lastTriggeredAt),Array.isArray(l.AND)&&(e.AND=l.AND.map(un)),Array.isArray(l.OR)&&(e.OR=l.OR.map(un)),Array.isArray(l.NOT)&&(e.NOT=l.NOT.map(un)),e},Zi=l=>{"use memo";const e=tl.c(103);let i,s,t,a,u,r,o;e[0]!==l?({autoScalingRulesFrgmt:i,presetMap:r,isEndpointDestroying:s,isOwnedByCurrentUser:t,onEditRule:u,onDeleteRule:a,...o}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u,e[6]=r,e[7]=o):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5],r=e[6],o=e[7]);const{t:d}=rl();let g;e[8]===Symbol.for("react.memo_cache_sentinel")?(g=Ht,e[8]=g):g=e[8];const c=Le.useFragment(g,i);let k;e[9]!==c?(k=Al(c),e[9]=c,e[10]=k):k=e[10];const h=k;let S;e[11]===Symbol.for("react.memo_cache_sentinel")?(S={x:"max-content"},e[11]=S):S=e[11];let p;e[12]!==d?(p=d("autoScalingRule.MetricSource"),e[12]=d,e[13]=p):p=e[13];let m;e[14]!==d?(m=d("autoScalingRule.MetricSourceTooltip"),e[14]=d,e[15]=m):m=e[15];let f;e[16]!==m?(f=n.jsx(pl,{title:m}),e[16]=m,e[17]=f):f=e[17];let R;e[18]!==p||e[19]!==f?(R={key:"metricSource",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[p,f]}),dataIndex:"metricSource",fixed:"left"},e[18]=p,e[19]=f,e[20]=R):R=e[20];let x;e[21]!==d?(x=d("autoScalingRule.Condition"),e[21]=d,e[22]=x):x=e[22];let F;e[23]!==d?(F=d("autoScalingRule.ConditionTooltip"),e[23]=d,e[24]=F):F=e[24];let I;e[25]!==F?(I=n.jsx(pl,{title:F}),e[25]=F,e[26]=I):I=e[26];let D;e[27]!==I||e[28]!==x?(D=n.jsxs(ie,{gap:"xxs",align:"center",children:[x,I]}),e[27]=I,e[28]=x,e[29]=D):D=e[29];let C;e[30]!==s||e[31]!==t||e[32]!==a||e[33]!==u||e[34]!==r||e[35]!==d?(C=($,O)=>O?n.jsx(Mn,{title:Ji(O,d,r),showActions:"always",actions:[{key:"edit",title:d("button.Edit"),icon:n.jsx(Pa,{}),disabled:s||!t,onClick:()=>u(O.id)},{key:"delete",title:d("button.Delete"),icon:n.jsx(Ln,{}),type:"danger",disabled:s||!t,onClick:()=>a(O.id,O.metricName??"")}]}):"-",e[30]=s,e[31]=t,e[32]=a,e[33]=u,e[34]=r,e[35]=d,e[36]=C):C=e[36];let A;e[37]!==D||e[38]!==C?(A={key:"condition",title:D,fixed:"left",render:C},e[37]=D,e[38]=C,e[39]=A):A=e[39];let z;e[40]!==d?(z=d("autoScalingRule.CoolDownSeconds"),e[40]=d,e[41]=z):z=e[41];let U;e[42]!==d?(U=d("autoScalingRule.CoolDownTooltip"),e[42]=d,e[43]=U):U=e[43];let w;e[44]!==U?(w=n.jsx(pl,{title:U}),e[44]=U,e[45]=w):w=e[45];let Q;e[46]!==z||e[47]!==w?(Q=n.jsxs(ie,{gap:"xxs",align:"center",children:[z,w]}),e[46]=z,e[47]=w,e[48]=Q):Q=e[48];let P;e[49]!==d?(P=$=>$!=null?d("autoScalingRule.CoolDownSecondsValue",{value:$}):"-",e[49]=d,e[50]=P):P=e[50];let L;e[51]!==Q||e[52]!==P?(L={key:"timeWindow",title:Q,dataIndex:"timeWindow",render:P},e[51]=Q,e[52]=P,e[53]=L):L=e[53];let E;e[54]!==d?(E=d("autoScalingRule.StepSize"),e[54]=d,e[55]=E):E=e[55];let j;e[56]!==d?(j=d("autoScalingRule.StepSizeTooltip"),e[56]=d,e[57]=j):j=e[57];let Y;e[58]!==j?(Y=n.jsx(pl,{title:j}),e[58]=j,e[59]=Y):Y=e[59];let W;e[60]!==E||e[61]!==Y?(W={key:"stepSize",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[E,Y]}),dataIndex:"stepSize",render:ls},e[60]=E,e[61]=Y,e[62]=W):W=e[62];let q;e[63]!==d?(q=d("autoScalingRule.MIN/MAXReplicas"),e[63]=d,e[64]=q):q=e[64];let V;e[65]!==d?(V=d("autoScalingRule.MinMaxReplicasTooltip"),e[65]=d,e[66]=V):V=e[66];let v;e[67]!==V?(v=n.jsx(pl,{title:V}),e[67]=V,e[68]=v):v=e[68];let b;e[69]!==q||e[70]!==v?(b=n.jsxs(ie,{gap:"xxs",align:"center",children:[q,v]}),e[69]=q,e[70]=v,e[71]=b):b=e[71];let _;e[72]!==d?(_=($,O)=>{if(!(O!=null&&O.stepSize))return"-";const Fe=O.minThreshold!=null,ke=O.maxThreshold!=null;return Fe&&ke?n.jsxs("span",{children:[d("autoScalingRule.MinReplicasValue",{value:O==null?void 0:O.minReplicas})," / ",d("autoScalingRule.MaxReplicasValue",{value:O==null?void 0:O.maxReplicas})]}):ke?n.jsx("span",{children:d("autoScalingRule.MaxReplicasValue",{value:O==null?void 0:O.maxReplicas})}):n.jsx("span",{children:d("autoScalingRule.MinReplicasValue",{value:O==null?void 0:O.minReplicas})})},e[72]=d,e[73]=_):_=e[73];let J;e[74]!==b||e[75]!==_?(J={key:"minMaxReplicas",title:b,render:_},e[74]=b,e[75]=_,e[76]=J):J=e[76];let Z;e[77]!==d?(Z=d("autoScalingRule.CreatedAt"),e[77]=d,e[78]=Z):Z=e[78];let ne;e[79]===Symbol.for("react.memo_cache_sentinel")?(ne=["descend","ascend"],e[79]=ne):ne=e[79];let K;e[80]!==Z?(K={key:"createdAt",title:Z,dataIndex:"createdAt",sorter:!0,sortDirections:ne,render:ns},e[80]=Z,e[81]=K):K=e[81];let T;e[82]!==d?(T=d("autoScalingRule.LastTriggered"),e[82]=d,e[83]=T):T=e[83];let N;e[84]!==d?(N=d("autoScalingRule.LastTriggeredTooltip"),e[84]=d,e[85]=N):N=e[85];let H;e[86]!==N?(H=n.jsx(pl,{title:N}),e[86]=N,e[87]=H):H=e[87];let G;e[88]!==T||e[89]!==H?(G={key:"lastTriggeredAt",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[T,H]}),render:ts},e[88]=T,e[89]=H,e[90]=G):G=e[90];let ee;e[91]!==A||e[92]!==L||e[93]!==W||e[94]!==J||e[95]!==K||e[96]!==G||e[97]!==R?(ee=[R,A,L,W,J,K,G],e[91]=A,e[92]=L,e[93]=W,e[94]=J,e[95]=K,e[96]=G,e[97]=R,e[98]=ee):ee=e[98];let le;return e[99]!==h||e[100]!==ee||e[101]!==o?(le=n.jsx(ql,{scroll:S,rowKey:"id",columns:ee,showSorterTooltip:!1,dataSource:h,...o}),e[99]=h,e[100]=ee,e[101]=o,e[102]=le):le=e[102],le},es=l=>{"use memo";var Ze,Pe,Ie,qe,Ye,Xe,Je,ol;const e=tl.c(125),{deploymentId:i,isEndpointDestroying:s,isOwnedByCurrentUser:t}=l,{t:a}=rl(),{message:u}=Nl.useApp(),[r,o]=M.useTransition(),[d,g]=Il(),[c,k]=M.useState(null),[h,S]=M.useState(!1),[p,m]=M.useState(null),[f,R]=Dl("table_column_overrides.AutoScalingRuleList");let x,F;e[0]===Symbol.for("react.memo_cache_sentinel")?(x={order:ln(["createdAt","-createdAt"]).withDefault("-createdAt"),filter:La(as)},F={history:"replace"},e[0]=x,e[1]=F):(x=e[0],F=e[1]);const[I,D]=Vn(x,F),C=I.order,A=I.filter??void 0;let z;e[2]===Symbol.for("react.memo_cache_sentinel")?(z={current:1,pageSize:10},e[2]=z):z=e[2];const{baiPaginationOption:U,tablePaginationOption:w,setTablePaginationOption:Q}=ja(z);let P;e[3]!==A?(P=A?un(A):null,e[3]=A,e[4]=P):P=e[4];const L=P,E=C.startsWith("-")?"DESC":"ASC";let j;e[5]!==E?(j=[{field:"CREATED_AT",direction:E}],e[5]=E,e[6]=j):j=e[6];let Y;e[7]!==U.limit||e[8]!==U.offset||e[9]!==i||e[10]!==L||e[11]!==j?(Y={deploymentId:i,offset:U.offset,limit:U.limit,orderBy:j,filter:L},e[7]=U.limit,e[8]=U.offset,e[9]=i,e[10]=L,e[11]=j,e[12]=Y):Y=e[12];const W=Y,q=M.useDeferredValue(W);let V;e[13]===Symbol.for("react.memo_cache_sentinel")?(V=wt,e[13]=V):V=e[13];let v;e[14]!==d?(v={fetchPolicy:"store-and-network",fetchKey:d},e[14]=d,e[15]=v):v=e[15];const b=Le.useLazyLoadQuery(V,q,v);let _,J;e[16]===Symbol.for("react.memo_cache_sentinel")?(_=$t,J={},e[16]=_,e[17]=J):(_=e[16],J=e[17]);const{prometheusQueryPresets:Z}=Le.useLazyLoadQuery(_,J);let ne;if(e[18]!==Z){if(ne=new Map,Z!=null&&Z.edges)for(const Ce of Z.edges)Ce!=null&&Ce.node&&ne.set(ll(Ce.node.id),Ce.node.name);e[18]=Z,e[19]=ne}else ne=e[19];const K=ne;let T;e[20]!==((Pe=(Ze=b==null?void 0:b.deployment)==null?void 0:Ze.autoScalingRules)==null?void 0:Pe.edges)?(T=Al(bl((qe=(Ie=b==null?void 0:b.deployment)==null?void 0:Ie.autoScalingRules)==null?void 0:qe.edges,"node")),e[20]=(Xe=(Ye=b==null?void 0:b.deployment)==null?void 0:Ye.autoScalingRules)==null?void 0:Xe.edges,e[21]=T):T=e[21];const N=T,H=((ol=(Je=b==null?void 0:b.deployment)==null?void 0:Je.autoScalingRules)==null?void 0:ol.count)??0;let G;e[22]===Symbol.for("react.memo_cache_sentinel")?(G=Ot,e[22]=G):G=e[22];const ee=tt(G);let le;e[23]!==g?(le=()=>{o(()=>{g()})},e[23]=g,e[24]=le):le=e[24];const $=le;let O;e[25]===Symbol.for("react.memo_cache_sentinel")?(O=(Ce,al)=>{m({id:Ce,metricName:al})},e[25]=O):O=e[25];const Fe=O;let ke;e[26]===Symbol.for("react.memo_cache_sentinel")?(ke={flex:1},e[26]=ke):ke=e[26];let me;e[27]!==a?(me=a("autoScalingRule.CreatedAt"),e[27]=a,e[28]=me):me=e[28];let Me;e[29]===Symbol.for("react.memo_cache_sentinel")?(Me=["after","before"],e[29]=Me):Me=e[29];let ye;e[30]!==me?(ye={key:"createdAt",propertyLabel:me,type:"datetime",operators:Me,defaultOperator:"after"},e[30]=me,e[31]=ye):ye=e[31];let pe;e[32]!==a?(pe=a("autoScalingRule.LastTriggered"),e[32]=a,e[33]=pe):pe=e[33];let ue;e[34]===Symbol.for("react.memo_cache_sentinel")?(ue=["after","before"],e[34]=ue):ue=e[34];let de;e[35]!==pe?(de={key:"lastTriggeredAt",propertyLabel:pe,type:"datetime",operators:ue,defaultOperator:"after"},e[35]=pe,e[36]=de):de=e[36];let se;e[37]!==ye||e[38]!==de?(se=[ye,de],e[37]=ye,e[38]=de,e[39]=se):se=e[39];let ce;e[40]!==D||e[41]!==Q?(ce=Ce=>{o(()=>{D({filter:Ce??null}),Q({current:1})})},e[40]=D,e[41]=Q,e[42]=ce):ce=e[42];let be;e[43]!==A||e[44]!==se||e[45]!==ce?(be=n.jsx(nn,{style:ke,filterProperties:se,value:A,onChange:ce}),e[43]=A,e[44]=se,e[45]=ce,e[46]=be):be=e[46];let ve;e[47]!==g?(ve=()=>{o(()=>g())},e[47]=g,e[48]=ve):ve=e[48];let Ke;e[49]!==r||e[50]!==ve?(Ke=n.jsx(Vl,{loading:r,value:"",onChange:ve}),e[49]=r,e[50]=ve,e[51]=Ke):Ke=e[51];let Se;e[52]===Symbol.for("react.memo_cache_sentinel")?(Se=n.jsx(jl,{}),e[52]=Se):Se=e[52];const ae=s||!t;let fe;e[53]===Symbol.for("react.memo_cache_sentinel")?(fe=()=>{k(null),S(!0)},e[53]=fe):fe=e[53];let we;e[54]!==a?(we=a("modelService.AddRules"),e[54]=a,e[55]=we):we=e[55];let De;e[56]!==ae||e[57]!==we?(De=n.jsx(Sl,{type:"primary",icon:Se,disabled:ae,onClick:fe,children:we}),e[56]=ae,e[57]=we,e[58]=De):De=e[58];let xe;e[59]!==be||e[60]!==Ke||e[61]!==De?(xe=n.jsxs(ie,{align:"center",gap:"sm",children:[be,Ke,De]}),e[59]=be,e[60]=Ke,e[61]=De,e[62]=xe):xe=e[62];const He=r||q!==W;let y;e[63]!==f||e[64]!==R?(y={columnOverrides:f,onColumnOverridesChange:R},e[63]=f,e[64]=R,e[65]=y):y=e[65];let B;e[66]!==D?(B=Ce=>{o(()=>{D({order:Ce||null})})},e[66]=D,e[67]=B):B=e[67];let X;e[68]!==Q?(X=(Ce,al)=>{Q({current:Ce,pageSize:al})},e[68]=Q,e[69]=X):X=e[69];let te;e[70]!==X||e[71]!==w.current||e[72]!==w.pageSize||e[73]!==H?(te={pageSize:w.pageSize,current:w.current,total:H,onChange:X},e[70]=X,e[71]=w.current,e[72]=w.pageSize,e[73]=H,e[74]=te):te=e[74];let re;e[75]===Symbol.for("react.memo_cache_sentinel")?(re=Ce=>{k(Ce),S(!0)},e[75]=re):re=e[75];let oe;e[76]!==N||e[77]!==s||e[78]!==t||e[79]!==C||e[80]!==K||e[81]!==He||e[82]!==y||e[83]!==B||e[84]!==te?(oe=n.jsx(Zi,{autoScalingRulesFrgmt:N,presetMap:K,order:C,loading:He,tableSettings:y,onChangeOrder:B,pagination:te,isEndpointDestroying:s,isOwnedByCurrentUser:t,onEditRule:re,onDeleteRule:Fe}),e[76]=N,e[77]=s,e[78]=t,e[79]=C,e[80]=K,e[81]=He,e[82]=y,e[83]=B,e[84]=te,e[85]=oe):oe=e[85];let Ae;e[86]!==xe||e[87]!==oe?(Ae=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[xe,oe]}),e[86]=xe,e[87]=oe,e[88]=Ae):Ae=e[88];let Ve;e[89]!==i?(Ve=ll(i),e[89]=i,e[90]=Ve):Ve=e[90];let Ee;e[91]!==N||e[92]!==c?(Ee=c?N.find(Ce=>Ce.id===c)??null:null,e[91]=N,e[92]=c,e[93]=Ee):Ee=e[93];let je;e[94]!==$?(je=Ce=>{S(!1),Ce&&$()},e[94]=$,e[95]=je):je=e[95];let ze;e[96]===Symbol.for("react.memo_cache_sentinel")?(ze=()=>{k(null)},e[96]=ze):ze=e[96];let he;e[97]!==h||e[98]!==Ve||e[99]!==Ee||e[100]!==je?(he=n.jsx(kl,{children:n.jsx(Hi,{open:h,modelDeploymentId:Ve,autoScalingRuleFrgmt:Ee,onRequestClose:je,afterClose:ze})}),e[97]=h,e[98]=Ve,e[99]=Ee,e[100]=je,e[101]=he):he=e[101];const Ge=!!p;let Ue;e[102]!==a?(Ue=a("autoScalingRule.DeleteAutoScalingRule"),e[102]=a,e[103]=Ue):Ue=e[103];let Oe;e[104]!==a?(Oe=a("autoScalingRule.DeleteConfirmation"),e[104]=a,e[105]=Oe):Oe=e[105];let Be;e[106]!==p?(Be=p?[{key:p.id,label:p.metricName}]:[],e[106]=p,e[107]=Be):Be=e[107];let Qe;e[108]!==ee||e[109]!==p||e[110]!==$||e[111]!==u||e[112]!==a?(Qe=()=>{if(p)return ee({input:{id:ll(p.id)}}).then(()=>{m(null),$(),u.success({key:"autoscaling-rule-deleted",content:a("autoScalingRule.SuccessfullyDeleted")})}).catch(Ce=>{const al=Array.isArray(Ce)?Ce:[Ce];for(const ul of al)u.error((ul==null?void 0:ul.message)||a("dialog.ErrorOccurred"))})},e[108]=ee,e[109]=p,e[110]=$,e[111]=u,e[112]=a,e[113]=Qe):Qe=e[113];let We;e[114]===Symbol.for("react.memo_cache_sentinel")?(We=()=>m(null),e[114]=We):We=e[114];let Re;e[115]!==Ge||e[116]!==Ue||e[117]!==Oe||e[118]!==Be||e[119]!==Qe?(Re=n.jsx(jn,{open:Ge,title:Ue,description:Oe,items:Be,reversible:!0,onOk:Qe,onCancel:We}),e[115]=Ge,e[116]=Ue,e[117]=Oe,e[118]=Be,e[119]=Qe,e[120]=Re):Re=e[120];let $e;return e[121]!==Ae||e[122]!==he||e[123]!==Re?($e=n.jsxs(n.Fragment,{children:[Ae,he,Re]}),e[121]=Ae,e[122]=he,e[123]=Re,e[124]=$e):$e=e[124],$e};function ls(l,e){if(!(e!=null&&e.stepSize))return"-";const i=e.minThreshold!=null,s=e.maxThreshold!=null;if(!i&&!s)return"-";const t=i&&s?"±":s?"+":"−";return n.jsxs(ie,{gap:"xs",children:[n.jsx(nl.Text,{children:t}),n.jsx(nl.Text,{children:Math.abs(e.stepSize)})]})}function ns(l,e){return n.jsx("span",{children:e!=null&&e.createdAt?cl(e.createdAt).format("ll LT"):"-"})}function ts(l,e){return n.jsx("span",{children:e!=null&&e.lastTriggeredAt?cl.utc(e.lastTriggeredAt).tz().format("ll LTS"):"-"})}function as(l){return l}const is=l=>{"use memo";var D,C,A;const e=tl.c(24),{deploymentFrgmt:i}=l,{t:s}=rl(),{token:t}=Cl.useToken(),[a]=st();let u;e[0]===Symbol.for("react.memo_cache_sentinel")?(u=Et,e[0]=u):u=e[0];const r=Le.useFragment(u,i);if(!(r!=null&&r.id))return null;const o=(D=r.metadata)==null?void 0:D.status,d=((A=(C=r.creator)==null?void 0:C.basicInfo)==null?void 0:A.email)??null,g=!d||d===a.email;let c;e[1]!==s?(c=s("deployment.tab.AutoScaling"),e[1]=s,e[2]=c):c=e[2];let k;e[3]!==s?(k=s("deployment.tab.description.AutoScaling"),e[3]=s,e[4]=k):k=e[4];let h;e[5]!==t.colorTextDescription?(h=n.jsx(Cn,{style:{color:t.colorTextDescription}}),e[5]=t.colorTextDescription,e[6]=h):h=e[6];let S;e[7]!==k||e[8]!==h?(S=n.jsx(ml,{title:k,children:h}),e[7]=k,e[8]=h,e[9]=S):S=e[9];let p;e[10]!==c||e[11]!==S?(p=n.jsxs(ie,{gap:"xs",align:"center",children:[c,S]}),e[10]=c,e[11]=S,e[12]=p):p=e[12];let m;e[13]===Symbol.for("react.memo_cache_sentinel")?(m={body:{paddingTop:0}},e[13]=m):m=e[13];let f;e[14]===Symbol.for("react.memo_cache_sentinel")?(f=n.jsx(Fl,{active:!0}),e[14]=f):f=e[14];const R=r.id;let x;e[15]!==o?(x=fl(o),e[15]=o,e[16]=x):x=e[16];let F;e[17]!==r.id||e[18]!==g||e[19]!==x?(F=n.jsx(M.Suspense,{fallback:f,children:n.jsx(es,{deploymentId:R,isEndpointDestroying:x,isOwnedByCurrentUser:g})}),e[17]=r.id,e[18]=g,e[19]=x,e[20]=F):F=e[20];let I;return e[21]!==F||e[22]!==p?(I=n.jsx(en,{title:p,styles:m,children:F}),e[21]=F,e[22]=p,e[23]=I):I=e[23],I},Ut=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentConfigurationSectionDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentConfigurationSectionDeleteMutation",selections:e},params:{cacheID:"ccb2e618fc149ec819f2dbee3d35c7a1",id:null,metadata:{},name:"DeploymentConfigurationSectionDeleteMutation",operationKind:"mutation",text:`mutation DeploymentConfigurationSectionDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();Ut.hash="739b8de15b5a7bdec89ece3d8628621f";const Wt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i=[l,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentConfigurationSection_deployment",selections:[l,{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[e],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentTagChips_metadata"}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:i,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:i,storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionHistoryTab_deployment"}],type:"ModelDeployment",abstractKey:null}}();Wt.hash="021c9e11d0201fb948249c5b903b8992";const Gt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},a=[i,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],u={alias:null,args:null,kind:"ScalarField",name:"previousRevisionId",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"activatedRevisionId",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},g=[o,d],c={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},h={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,o,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},S=[i,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[o,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},d,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[o,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[c,k,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},h],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[c,k,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},h],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[o,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,s,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:a,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:a,storageKey:null}],storageKey:null},u,r],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,s,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:S,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:S,storageKey:null}],storageKey:null},u,r],storageKey:null}]},params:{cacheID:"484c885f3fb5c0c9f4a4e12f257a49e6",id:null,metadata:{},name:"DeploymentRevisionHistoryTabActivateMutation",operationKind:"mutation",text:`mutation DeploymentRevisionHistoryTabActivateMutation(
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
`}}}();Gt.hash="153c096cf78b28827d7a04ef0f1610d4";const Yt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],u={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},o=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},h={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},p={alias:null,args:null,concreteType:"ModelMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],storageKey:null},m={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[g,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},x=[S,R],F={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[g,S,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},D={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[u,r,{alias:null,args:o,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[g,c,k,h,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[S],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[S,p],storageKey:null}],storageKey:null},m,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[f,{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[g,S,{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,s],kind:"Operation",name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[u,r,{alias:null,args:o,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[g,c,k,h,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[S,g],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},R,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[S,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},g],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[S,p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},m,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[f,F,I,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},D,{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[f,I,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},F],storageKey:null},m,D],storageKey:null}],storageKey:null}],storageKey:null},g],storageKey:null}]},params:{cacheID:"33ba9a0de55569323004cce82b1cc474",id:null,metadata:{},name:"DeploymentRevisionHistoryTabListQuery",operationKind:"query",text:`query DeploymentRevisionHistoryTabListQuery(
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
`}}}();Yt.hash="dc7544cf74c6e7b71663a4998c4d880c";const Xt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"}],type:"ModelDeployment",abstractKey:null};Xt.hash="6d00d8056ec0eba0eea404e554242adf";const Xn=["revisionNumber","createdAt","clusterMode","runtimeVariantName"],ss=[...Xn,...Xn.map(l=>`-${l}`)],rs=({deploymentFrgmt:l,deploymentId:e,fetchKey:i})=>{"use memo";var ne;const{t:s}=rl(),{token:t}=Cl.useToken(),{message:a}=Nl.useApp(),{logger:u}=zl(),[r,o]=M.useTransition(),[d,g]=M.useState(null),[c,k]=M.useState(null),[h,S]=M.useState(null),[p,m]=Dl("table_column_overrides.DeploymentRevisionHistoryTab"),[f,R]=Vn({current:cn.withDefault(1),pageSize:cn.withDefault(10),order:ln(ss),rvFilter:rt},{history:"replace",urlKeys:{current:"rvCurrent",pageSize:"rvPageSize",order:"rvOrder",rvFilter:"rvFilter"}}),x=Le.useFragment(Xt,l),F=(ne=x==null?void 0:x.metadata)==null?void 0:ne.status,I=K=>{if(!K)return null;try{const T=JSON.parse(K);return T&&typeof T=="object"&&!Array.isArray(T)?T:null}catch{return null}},D=K=>!K||Object.keys(K).length===0?"":JSON.stringify(K),[C,A]=M.useState(()=>({filter:f.rvFilter?I(f.rvFilter):null,orderBy:Ql(f.order)??[{field:"REVISION_NUMBER",direction:"DESC"}],limit:f.pageSize,offset:f.current>1?(f.current-1)*f.pageSize:0})),[z,U]=Il(),w=`${i??""}${z}`,Q=(i===void 0||i===bn)&&z===bn,{deployment:P}=Le.useLazyLoadQuery(Yt,{deploymentId:e,...C},{fetchKey:w,fetchPolicy:Q?"store-and-network":"network-only"}),[L]=Le.useMutation(Gt),E=P==null?void 0:P.currentRevisionId,j=P==null?void 0:P.deployingRevisionId,Y=P==null?void 0:P.revisionHistory,W=Al(bl(Y==null?void 0:Y.edges,"node")),q=K=>{o(()=>{A(T=>({...T,...K}))})},V=()=>{o(()=>U())},v=K=>new Promise(T=>{g(K.id),L({variables:{input:{deploymentId:ll(x.id),revisionId:ll(K.id)}},onCompleted:(N,H)=>{var G;if(g(null),H&&H.length>0){u.error(H[0]),a.error(((G=H[0])==null?void 0:G.message)||s("general.ErrorOccurred")),T(!1);return}a.success(s("deployment.ApplySuccess",{revisionNumber:K.revisionNumber})),V(),T(!0)},onError:N=>{g(null),u.error(N),a.error((N==null?void 0:N.message)||s("general.ErrorOccurred")),T(!1)}})}),b=[{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.RevisionNumberWithID"),n.jsx(pl,{title:s("deployment.RevisionNumberTooltip")})]}),dataIndex:"revisionNumber",key:"revisionNumber",fixed:"left",sorter:!0,render:(K,T)=>{const N=ll(T.id),H=N===E,G=N===j,ee=H||G?s("deployment.ApplyDisabled"):void 0,le=H||G||fl(F)||d===T.id;return n.jsx(Mn,{title:n.jsxs(ie,{gap:"xs",align:"center",wrap:"nowrap",children:[n.jsx(nl.Link,{onClick:()=>k({frgmt:T,status:H?"current":G?"deploying":"none"}),children:T.revisionNumber!=null?`#${T.revisionNumber}`:"-"}),n.jsxs(ie,{gap:0,align:"center",children:["(",n.jsx(Hl,{globalId:T.id}),")"]}),H?n.jsx(mn,{color:"success",children:s("deployment.Current")}):null,G&&!H?n.jsx(mn,{color:"warning",icon:n.jsx(_n,{spin:!0}),children:s("deployment.Applying")}):null]}),showActions:"always",moreMenuDisabled:fl(F),actions:[{key:"deploy",title:s("deployment.Apply"),icon:n.jsx(Qn,{}),disabled:le,disabledReason:ee,popConfirm:{title:s("deployment.ApplyRevision"),description:s("deployment.ApplyConfirm",{revisionNumber:T.revisionNumber}),okText:s("deployment.Apply"),cancelText:s("button.Cancel"),okButtonProps:{danger:!0},onConfirm:()=>{v(T)}}},{key:"duplicate",title:s("deployment.AddNewRevisionFromThis"),icon:n.jsx(Wn,{size:t.fontSize}),showInMenu:"always",disabled:fl(F),onClick:()=>{S(T)}}]})}},{title:s("general.CreatedAt"),dataIndex:"createdAt",key:"createdAt",sorter:!0,render:K=>K?cl(K).format("lll"):"-"},{title:s("deployment.ModelVersion"),key:"modelVersion",defaultHidden:!0,render:(K,T)=>{var le,$,O;const N=($=(le=T.modelDefinition)==null?void 0:le.models)==null?void 0:$[0];if(!N)return"-";const H=N.name??"-",G=(O=N.metadata)==null?void 0:O.version,ee=typeof G=="string"?G:G!=null?String(G):null;return ee?`${H} (${ee})`:H}},{title:s("deployment.RuntimeVariant"),key:"runtimeVariantName",dataIndex:"runtimeVariantName",sorter:!0,render:(K,T)=>{var N,H;return((H=(N=T.modelRuntimeConfig)==null?void 0:N.runtimeVariant)==null?void 0:H.name)??"-"}},{title:s("deployment.Image"),key:"image",defaultHidden:!0,render:(K,T)=>{var ee,le,$,O;const N=(le=(ee=T.imageV2)==null?void 0:ee.identity)==null?void 0:le.canonicalName,H=(O=($=T.imageV2)==null?void 0:$.identity)==null?void 0:O.architecture,G=N&&H?`${N}@${H}`:N;return G?n.jsx(Pl,{copyable:{text:G},ellipsis:{tooltip:G},style:{maxWidth:180},children:G}):"-"}},{title:s("deployment.ModelFolder"),key:"modelFolder",defaultHidden:!0,render:(K,T)=>{var G,ee;const N=(G=T.modelMountConfig)==null?void 0:G.vfolder,H=(ee=T.modelMountConfig)==null?void 0:ee.vfolderId;return!N&&!H?"-":N?n.jsx(ii,{vfolderNodeFragment:N}):n.jsx(nl.Text,{type:"secondary",children:H})}},{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.ClusterMode"),n.jsx(pl,{title:s("deployment.ClusterModeTooltip")})]}),key:"clusterMode",dataIndex:"clusterMode",sorter:!0,render:(K,T)=>{var G,ee;const N=(G=T.clusterConfig)==null?void 0:G.mode,H=(ee=T.clusterConfig)==null?void 0:ee.size;return N==null&&H==null?"-":N==null?`${H}`:H==null?N:`${N} / ${H}`}}],_={message:s("general.InvalidUUID"),validate:K=>Va(K.toLowerCase())},J=[{key:"revisionNumber",propertyLabel:s("deployment.RevisionNumber"),type:"number"},{key:"createdAt",propertyLabel:s("general.CreatedAt"),type:"datetime",operators:["after","before"],defaultOperator:"after"},{key:"clusterMode",propertyLabel:s("deployment.ClusterMode"),type:"string"},{key:"imageId",propertyLabel:s("deployment.Image"),type:"uuid",fixedOperator:"equals",rule:_},{key:"modelVfolderId",propertyLabel:s("deployment.ModelFolder"),type:"uuid",fixedOperator:"equals",rule:_}],Z=f.rvFilter?I(f.rvFilter)??void 0:void 0;return n.jsxs(n.Fragment,{children:[n.jsx(kl,{children:n.jsx(pn,{revisionFrgmt:c==null?void 0:c.frgmt,status:c==null?void 0:c.status,open:!!c,onClose:()=>k(null),extra:c?n.jsxs(Zl.Compact,{children:[n.jsx(Na,{title:s("deployment.ApplyRevision"),description:s("deployment.ApplyConfirm",{revisionNumber:c.frgmt.revisionNumber}),okText:s("deployment.Apply"),cancelText:s("button.Cancel"),okButtonProps:{danger:!0},onConfirm:async()=>{await v(c.frgmt)&&k(null)},children:n.jsx(Sl,{type:"primary",icon:n.jsx(Qn,{}),disabled:c.status==="current"||c.status==="deploying"||fl(F)||!!d,children:s("deployment.Apply")})}),n.jsx(ot,{trigger:["click"],menu:{items:[{key:"duplicate",label:s("deployment.AddNewRevisionFromThis"),icon:n.jsx(Wn,{size:t.fontSize}),disabled:fl(F),onClick:()=>{const K=c.frgmt;k(null),S(K)}}]},children:n.jsx(Sl,{type:"primary",icon:n.jsx(dt,{}),"aria-label":s("button.More"),disabled:fl(F)})})]}):void 0})}),n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:t.marginSM},wrap:"wrap",children:[n.jsx(nn,{filterProperties:J,value:Z,onChange:K=>{const T=D(K),N=I(T||null);R({rvFilter:T||null,current:1}),q({filter:N,offset:0})}}),n.jsx(Vl,{loading:r,value:"",onChange:()=>V()})]}),n.jsx(ql,{rowKey:"id",dataSource:W,columns:b,loading:r,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:p,onColumnOverridesChange:m},order:f.order??void 0,onChangeOrder:K=>{R({order:K}),q({orderBy:Ql(K)})},pagination:{pageSize:f.pageSize,current:f.current,total:(Y==null?void 0:Y.count)??0,showSizeChanger:!0,onChange:(K,T)=>{const N=K>1?(K-1)*T:0;R({current:K,pageSize:T}),q({limit:T,offset:N})}}}),n.jsx(M.Suspense,{fallback:null,children:n.jsx(kl,{children:n.jsx(_t,{open:!!h,deploymentFrgmt:x,sourceRevisionFrgmt:h,onRequestClose:K=>{S(null),K&&V()}})})})]})},Jt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[u,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,s,e,i],kind:"Operation",name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[u,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},r,o,d,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},o,d,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"b24d145b426294eb9cc72c268ccd1df2",id:null,metadata:{},name:"DeploymentSchedulingHistoryModalQuery",operationKind:"query",text:`query DeploymentSchedulingHistoryModalQuery(
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
`}}}();Jt.hash="89ec50bb9b1f834e59c642072090d378";const Zt=Jt,os=l=>{"use memo";var be,ve,Ke,Se;const e=tl.c(113);let i,s,t,a,u;e[0]!==l?({open:a,queryRef:u,onReload:t,onCancel:s,...i}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5]);const{t:r}=rl(),[o,d]=Il(),[g,c]=M.useState(),[k,h]=M.useState("-updatedAt"),[S,p]=Dl("schedulingHistoryExpandMode"),[m,f]=Dl("table_column_overrides.DeploymentSchedulingHistory");let R;e[6]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[6]=R):R=e[6];const{tablePaginationOption:x,setTablePaginationOption:F}=En(R),I=M.useDeferredValue(u),D=I!==u,C=Le.usePreloadedQuery(Zt,I);let A;e[7]!==r?(A=r("deployment.DeploymentSchedulingHistory"),e[7]=r,e[8]=A):A=e[8];let z,U;e[9]===Symbol.for("react.memo_cache_sentinel")?(z={maxWidth:1600},U={body:{minHeight:"80vh"}},e[9]=z,e[10]=U):(z=e[9],U=e[10]);let w;e[11]!==t||e[12]!==u.variables||e[13]!==F?(w=ae=>{c(ae),F({current:1}),t({...u.variables,filter:ae,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=u.variables,e[13]=F,e[14]=w):w=e[14];let Q;e[15]!==r?(Q=r("deployment.ID"),e[15]=r,e[16]=Q):Q=e[16];let P;e[17]!==Q?(P={key:"id",propertyLabel:Q,type:"uuid",fixedOperator:"equals"},e[17]=Q,e[18]=P):P=e[18];let L;e[19]!==r?(L=r("deployment.Phase"),e[19]=r,e[20]=L):L=e[20];let E;e[21]!==L?(E={key:"phase",propertyLabel:L,type:"string",fixedOperator:"contains"},e[21]=L,e[22]=E):E=e[22];let j;e[23]!==r?(j=r("deployment.Result"),e[23]=r,e[24]=j):j=e[24];let Y;e[25]===Symbol.for("react.memo_cache_sentinel")?(Y=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=Y):Y=e[25];let W;e[26]!==j?(W={key:"result",propertyLabel:j,type:"enum",strictSelection:!0,options:Y},e[26]=j,e[27]=W):W=e[27];let q;e[28]!==r?(q=r("deployment.FromStatus"),e[28]=r,e[29]=q):q=e[29];let V;e[30]!==q?(V={key:"fromStatus",propertyLabel:q,type:"string",valueMode:"scalar"},e[30]=q,e[31]=V):V=e[31];let v;e[32]!==r?(v=r("deployment.ToStatus"),e[32]=r,e[33]=v):v=e[33];let b;e[34]!==v?(b={key:"toStatus",propertyLabel:v,type:"string",valueMode:"scalar"},e[34]=v,e[35]=b):b=e[35];let _;e[36]!==r?(_=r("deployment.ErrorCode"),e[36]=r,e[37]=_):_=e[37];let J;e[38]!==_?(J={key:"errorCode",propertyLabel:_,type:"string",fixedOperator:"contains"},e[38]=_,e[39]=J):J=e[39];let Z;e[40]!==r?(Z=r("deployment.Message"),e[40]=r,e[41]=Z):Z=e[41];let ne;e[42]!==Z?(ne={key:"message",propertyLabel:Z,type:"string",fixedOperator:"contains"},e[42]=Z,e[43]=ne):ne=e[43];let K;e[44]!==r?(K=r("deployment.CreatedAt"),e[44]=r,e[45]=K):K=e[45];let T;e[46]!==K?(T={key:"createdAt",propertyLabel:K,type:"datetime",defaultOperator:"after"},e[46]=K,e[47]=T):T=e[47];let N;e[48]!==r?(N=r("deployment.UpdatedAt"),e[48]=r,e[49]=N):N=e[49];let H;e[50]!==N?(H={key:"updatedAt",propertyLabel:N,type:"datetime",defaultOperator:"after"},e[50]=N,e[51]=H):H=e[51];let G;e[52]!==W||e[53]!==V||e[54]!==b||e[55]!==J||e[56]!==ne||e[57]!==T||e[58]!==H||e[59]!==P||e[60]!==E?(G=[P,E,W,V,b,J,ne,T,H],e[52]=W,e[53]=V,e[54]=b,e[55]=J,e[56]=ne,e[57]=T,e[58]=H,e[59]=P,e[60]=E,e[61]=G):G=e[61];let ee;e[62]!==g||e[63]!==G||e[64]!==w?(ee=n.jsx(nn,{value:g,onChange:w,filterProperties:G}),e[62]=g,e[63]=G,e[64]=w,e[65]=ee):ee=e[65];let le;e[66]!==t||e[67]!==u.variables||e[68]!==d?(le=ae=>{d(ae),t(u.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=u.variables,e[68]=d,e[69]=le):le=e[69];let $;e[70]!==o||e[71]!==D||e[72]!==le?($=n.jsx(ie,{children:n.jsx(Vl,{value:o,onChange:le,loading:D,autoUpdateDelay:null})}),e[70]=o,e[71]=D,e[72]=le,e[73]=$):$=e[73];let O;e[74]!==ee||e[75]!==$?(O=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[ee,$]}),e[74]=ee,e[75]=$,e[76]=O):O=e[76];const Fe=S??void 0;let ke;e[77]!==m||e[78]!==f?(ke={columnOverrides:m,onColumnOverridesChange:f},e[77]=m,e[78]=f,e[79]=ke):ke=e[79];let me;e[80]!==t||e[81]!==u.variables||e[82]!==F?(me=ae=>{h(ae),F({current:1}),t({...u.variables,orderBy:Ql(ae),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=u.variables,e[82]=F,e[83]=me):me=e[83];const Me=((be=C.deploymentScopedSchedulingHistories)==null?void 0:be.count)??0;let ye;e[84]!==t||e[85]!==u.variables||e[86]!==F?(ye=(ae,fe)=>{F({current:ae,pageSize:fe}),t({...u.variables,limit:fe,offset:ae>1?(ae-1)*fe:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=u.variables,e[86]=F,e[87]=ye):ye=e[87];let pe;e[88]!==Me||e[89]!==ye||e[90]!==x.current||e[91]!==x.pageSize?(pe={pageSize:x.pageSize,current:x.current,total:Me,onChange:ye},e[88]=Me,e[89]=ye,e[90]=x.current,e[91]=x.pageSize,e[92]=pe):pe=e[92];let ue;e[93]!==((ve=C.deploymentScopedSchedulingHistories)==null?void 0:ve.edges)?(ue=bl((Ke=C.deploymentScopedSchedulingHistories)==null?void 0:Ke.edges,"node"),e[93]=(Se=C.deploymentScopedSchedulingHistories)==null?void 0:Se.edges,e[94]=ue):ue=e[94];let de;e[95]!==D||e[96]!==k||e[97]!==p||e[98]!==Fe||e[99]!==ke||e[100]!==me||e[101]!==pe||e[102]!==ue?(de=n.jsx(Mi,{resizable:!0,loading:D,expandMode:Fe,onExpandModeChange:p,tableSettings:ke,order:k,onChangeOrder:me,pagination:pe,schedulingHistoryFrgmt:ue}),e[95]=D,e[96]=k,e[97]=p,e[98]=Fe,e[99]=ke,e[100]=me,e[101]=pe,e[102]=ue,e[103]=de):de=e[103];let se;e[104]!==O||e[105]!==de?(se=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[O,de]}),e[104]=O,e[105]=de,e[106]=se):se=e[106];let ce;return e[107]!==i||e[108]!==s||e[109]!==a||e[110]!==A||e[111]!==se?(ce=n.jsx(Ul,{title:A,open:a,width:"90%",style:z,styles:U,footer:null,onCancel:s,...i,children:se}),e[107]=i,e[108]=s,e[109]=a,e[110]=A,e[111]=se,e[112]=ce):ce=e[112],ce},Kl=()=>n.jsx(nl.Text,{type:"secondary",children:"-"}),ds=l=>{"use memo";var k,h,S;const e=tl.c(26),{deployment:i,onClickSchedulingHistoryAction:s}=l,{t}=rl(),a=yn(),u=ut(),r=((h=(k=i==null?void 0:i.metadata.projectV2)==null?void 0:k.basicInfo)==null?void 0:h.name)??(i==null?void 0:i.metadata.projectId);let o;if(e[0]!==i||e[1]!==u.pathname||e[2]!==s||e[3]!==r||e[4]!==t||e[5]!==a){const p=t("deployment.Visibility"),m=i==null?void 0:i.networkAccess.openToPublic;let f;e[7]!==t?(f=t("deployment.Public"),e[7]=t,e[8]=f):f=e[8];let R;e[9]!==t?(R=t("deployment.Private"),e[9]=t,e[10]=R):R=e[10];let x;e[11]===Symbol.for("react.memo_cache_sentinel")?(x=Kl(),e[11]=x):x=e[11];let F;e[12]!==m||e[13]!==f||e[14]!==R?(F=n.jsx(oi,{value:m,trueLabel:f,falseLabel:R,fallback:x}),e[12]=m,e[13]=f,e[14]=R,e[15]=F):F=e[15];const I=t("deployment.Tags"),D=(i==null?void 0:i.metadata)??null;let C;e[16]!==u.pathname||e[17]!==a?(C=U=>{const w=u.pathname.startsWith("/admin-deployments")?"/admin-deployments":u.pathname.startsWith("/project-admin-deployments")?"/project-admin-deployments":"/deployments";a({pathname:w,search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:U}})}).toString()})},e[16]=u.pathname,e[17]=a,e[18]=C):C=e[18];let A;e[19]===Symbol.for("react.memo_cache_sentinel")?(A=Kl(),e[19]=A):A=e[19];let z;e[20]!==C||e[21]!==D?(z=n.jsx(ai,{metadataFrgmt:D,onTagClick:C,fallback:A}),e[20]=C,e[21]=D,e[22]=z):z=e[22],o=gn([{key:"lifecycle",label:t("deployment.Lifecycle"),children:i!=null&&i.metadata.status?n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(St,{status:i.metadata.status}),s&&n.jsxs(n.Fragment,{children:[n.jsx(at,{type:"vertical",style:{margin:0}}),n.jsx(Sl,{type:"link",size:"small",icon:n.jsx(kt,{}),style:{padding:0},action:async()=>{await s()},children:t("deployment.SchedulingHistory")})]})]}):Kl()},{key:"id",label:t("deployment.DeploymentId"),children:i!=null&&i.id?n.jsx(Hl,{globalId:i.id,copyable:!0,ellipsis:!1,style:{maxWidth:"none"}}):Kl()},{key:"project",label:t("deployment.Project"),children:r||Kl()},{key:"domain",label:t("deployment.Domain"),children:(i==null?void 0:i.metadata.domainName)||Kl()},{key:"resource-group",label:t("modelStore.ResourceGroup"),children:(i==null?void 0:i.metadata.resourceGroupName)||Kl()},{key:"endpoint-url",label:t("deployment.EndpointUrl"),children:i!=null&&i.networkAccess.endpointUrl?n.jsx(nl.Text,{copyable:!0,style:{wordBreak:"break-all"},children:i.networkAccess.endpointUrl}):Kl()},{key:"visibility",label:p,children:F},{key:"desired-replicas",label:t("deployment.DesiredReplicas"),children:((S=i==null?void 0:i.replicaState)==null?void 0:S.desiredReplicaCount)??Kl()},{key:"tags",label:I,children:z}]),e[0]=i,e[1]=u.pathname,e[2]=s,e[3]=r,e[4]=t,e[5]=a,e[6]=o}else o=e[6];const d=o;let g;e[23]===Symbol.for("react.memo_cache_sentinel")?(g={xs:1,sm:1,md:2,lg:2,xl:2,xxl:2},e[23]=g):g=e[23];let c;return e[24]!==d?(c=n.jsx(wa,{bordered:!0,column:g,items:d}),e[24]=d,e[25]=c):c=e[25],c},us=l=>{"use memo";const e=tl.c(181),{deploymentFrgmt:i,revisionFetchKey:s,isPendingRefetch:t,onRefetch:a,onAddRevision:u,revisionCardRef:r}=l,{t:o}=rl(),{token:d}=Cl.useToken(),{message:g}=Nl.useApp(),{logger:c}=zl(),k=yn(),h=ut(),S=Pn();let p;e[0]===Symbol.for("react.memo_cache_sentinel")?(p=Wt,e[0]=p):p=e[0];const m=Le.useFragment(p,i),[f,R]=M.useState(null);let x;e[1]===Symbol.for("react.memo_cache_sentinel")?(x=ln(["currentRevision","revisionHistory","auditLog"]).withDefault("currentRevision"),e[1]=x):x=e[1];let F;e[2]===Symbol.for("react.memo_cache_sentinel")?(F={...x,history:"replace",scroll:!1},e[2]=F):F=e[2];const[I,D]=_a("revisionTab",F),[C,A]=M.useState(!1),[z,U]=M.useState(!1),[w,Q]=M.useState(!1),[P,L]=Le.useQueryLoader(Zt),[E,j]=Le.useQueryLoader(si);let Y;e[3]===Symbol.for("react.memo_cache_sentinel")?(Y={current:1,pageSize:10},e[3]=Y):Y=e[3];const{baiPaginationOption:W,setTablePaginationOption:q}=En(Y);let V;e[4]!==j||e[5]!==q?(V=(el,Ml)=>{const sn=el.limit??10;q({pageSize:sn,current:el.offset?Math.floor(el.offset/sn)+1:1}),j(el,Ml)},e[4]=j,e[5]=q,e[6]=V):V=e[6];const v=V;let b;e[7]!==W||e[8]!==m||e[9]!==j?(b=()=>{if(!(m!=null&&m.id))return;const el=m.id;j({scope:{entity:[{entityType:"MODEL_DEPLOYMENT",entityId:Bl(el)??el}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:W.limit,offset:W.offset},{fetchPolicy:"store-and-network"})},e[7]=W,e[8]=m,e[9]=j,e[10]=b):b=e[10];const _=b;let J;e[11]!==I||e[12]!==E||e[13]!==_?(J=()=>{I==="auditLog"&&E==null&&_()},e[11]=I,e[12]=E,e[13]=_,e[14]=J):J=e[14];const Z=M.useEffectEvent(J);let ne;e[15]!==Z?(ne=function(){Z()},e[15]=Z,e[16]=ne):ne=e[16];let K;e[17]===Symbol.for("react.memo_cache_sentinel")?(K=[],e[17]=K):K=e[17],M.useEffect(ne,K);const T=ct();let N;e[18]!==T?(N=(T==null?void 0:T.supports("deployment-scheduling-history"))??!1,e[18]=T,e[19]=N):N=e[19];const H=N;let G;e[20]===Symbol.for("react.memo_cache_sentinel")?(G=Ut,e[20]=G):G=e[20];const[ee,le]=Le.useMutation(G),$=(m==null?void 0:m.metadata.name)??"",O=m==null?void 0:m.metadata.status,Fe=h.pathname.startsWith("/admin-deployments")?"/admin-deployments":h.pathname.startsWith("/project-admin-deployments")?"/project-admin-deployments":"/deployments",ke=(m==null?void 0:m.metadata.projectId)??null,me=!!ke&&ke!==S.id;let Me;e[21]!==ee||e[22]!==m||e[23]!==Fe||e[24]!==c||e[25]!==g||e[26]!==o||e[27]!==k?(Me=()=>{m!=null&&m.id&&ee({variables:{input:{id:ll(m.id)??m.id}},onCompleted:(el,Ml)=>{if(Ml&&Ml.length>0){c.error("Failed to delete deployment",Ml),g.error(o("deployment.FailedToDeleteDeployment"));return}g.success(o("deployment.DeploymentDeleted")),U(!1),k(Fe)},onError:el=>{c.error("Failed to delete deployment",el),g.error(o("deployment.FailedToDeleteDeployment"))}})},e[21]=ee,e[22]=m,e[23]=Fe,e[24]=c,e[25]=g,e[26]=o,e[27]=k,e[28]=Me):Me=e[28];const ye=Me;let pe;e[29]===Symbol.for("react.memo_cache_sentinel")?(pe=(el,Ml,sn)=>{R({revisionFrgmt:el,status:Ml,title:sn})},e[29]=pe):pe=e[29];const ue=pe,de=m==null?void 0:m.currentRevision,se=m==null?void 0:m.deployingRevision,ce=!!se&&se.id!==(de==null?void 0:de.id);Ea(a,ce?5e3:null);let be;e[30]!==o?(be=o("deployment.BasicInformation"),e[30]=o,e[31]=be):be=e[31];let ve;e[32]!==t||e[33]!==a?(ve=n.jsx(Vl,{loading:t,value:"",onChange:a}),e[32]=t,e[33]=a,e[34]=ve):ve=e[34];let Ke;e[35]===Symbol.for("react.memo_cache_sentinel")?(Ke=n.jsx(Oa,{}),e[35]=Ke):Ke=e[35];let Se;e[36]!==O?(Se=fl(O),e[36]=O,e[37]=Se):Se=e[37];let ae;e[38]===Symbol.for("react.memo_cache_sentinel")?(ae=async()=>{A(!0)},e[38]=ae):ae=e[38];let fe;e[39]!==o?(fe=o("button.Edit"),e[39]=o,e[40]=fe):fe=e[40];let we;e[41]!==Se||e[42]!==fe?(we=n.jsx(Sl,{icon:Ke,disabled:Se,action:ae,children:fe}),e[41]=Se,e[42]=fe,e[43]=we):we=e[43];let De;e[44]===Symbol.for("react.memo_cache_sentinel")?(De=["click"],e[44]=De):De=e[44];let xe;e[45]!==o?(xe=o("deployment.DeleteDeployment"),e[45]=o,e[46]=xe):xe=e[46];let He;e[47]===Symbol.for("react.memo_cache_sentinel")?(He=n.jsx(Ln,{}),e[47]=He):He=e[47];let y;e[48]!==O||e[49]!==le?(y=fl(O)||le,e[48]=O,e[49]=le,e[50]=y):y=e[50];let B;e[51]===Symbol.for("react.memo_cache_sentinel")?(B=()=>U(!0),e[51]=B):B=e[51];let X;e[52]!==xe||e[53]!==y?(X={items:[{key:"delete",label:xe,icon:He,danger:!0,disabled:y,onClick:B}]},e[52]=xe,e[53]=y,e[54]=X):X=e[54];let te;e[55]===Symbol.for("react.memo_cache_sentinel")?(te=n.jsx(dt,{}),e[55]=te):te=e[55];let re;e[56]!==o?(re=o("button.More"),e[56]=o,e[57]=re):re=e[57];let oe;e[58]!==re?(oe=n.jsx(gl,{icon:te,"aria-label":re}),e[58]=re,e[59]=oe):oe=e[59];let Ae;e[60]!==X||e[61]!==oe?(Ae=n.jsx(ot,{trigger:De,menu:X,children:oe}),e[60]=X,e[61]=oe,e[62]=Ae):Ae=e[62];let Ve;e[63]!==we||e[64]!==Ae?(Ve=n.jsxs(Zl.Compact,{children:[we,Ae]}),e[63]=we,e[64]=Ae,e[65]=Ve):Ve=e[65];let Ee;e[66]!==ve||e[67]!==Ve?(Ee=n.jsxs(ie,{gap:"xs",align:"center",children:[ve,Ve]}),e[66]=ve,e[67]=Ve,e[68]=Ee):Ee=e[68];let je;e[69]===Symbol.for("react.memo_cache_sentinel")?(je={body:{paddingTop:0}},e[69]=je):je=e[69];let ze;e[70]!==m||e[71]!==L||e[72]!==H?(ze=H&&(m!=null&&m.id)?async()=>{const el=m.id;el&&(L({scope:{deploymentId:Bl(el)??el},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),Q(!0))}:void 0,e[70]=m,e[71]=L,e[72]=H,e[73]=ze):ze=e[73];let he;e[74]!==m||e[75]!==ze?(he=n.jsx(ds,{deployment:m,onClickSchedulingHistoryAction:ze}),e[74]=m,e[75]=ze,e[76]=he):he=e[76];let Ge;e[77]!==be||e[78]!==Ee||e[79]!==he?(Ge=n.jsx(en,{title:be,extra:Ee,styles:je,children:he}),e[77]=be,e[78]=Ee,e[79]=he,e[80]=Ge):Ge=e[80];let Ue;e[81]!==E||e[82]!==_||e[83]!==D?(Ue=el=>{(el==="currentRevision"||el==="revisionHistory"||el==="auditLog")&&(el==="auditLog"&&E==null&&_(),D(el))},e[81]=E,e[82]=_,e[83]=D,e[84]=Ue):Ue=e[84];let Oe;e[85]!==o?(Oe=o("deployment.CurrentRevision"),e[85]=o,e[86]=Oe):Oe=e[86];let Be;e[87]!==Oe?(Be={key:"currentRevision",label:Oe},e[87]=Oe,e[88]=Be):Be=e[88];let Qe;e[89]!==o?(Qe=o("deployment.RevisionHistory"),e[89]=o,e[90]=Qe):Qe=e[90];let We;e[91]!==Qe?(We={key:"revisionHistory",label:Qe},e[91]=Qe,e[92]=We):We=e[92];let Re;e[93]!==o?(Re=o("auditLog.AuditLog"),e[93]=o,e[94]=Re):Re=e[94];let $e;e[95]!==Re?($e={key:"auditLog",label:Re},e[95]=Re,e[96]=$e):$e=e[96];let Ze;e[97]!==Be||e[98]!==We||e[99]!==$e?(Ze=[Be,We,$e],e[97]=Be,e[98]=We,e[99]=$e,e[100]=Ze):Ze=e[100];let Pe;e[101]===Symbol.for("react.memo_cache_sentinel")?(Pe=n.jsx(jl,{}),e[101]=Pe):Pe=e[101];let Ie;e[102]!==O||e[103]!==me?(Ie=fl(O)||me,e[102]=O,e[103]=me,e[104]=Ie):Ie=e[104];let qe;e[105]!==u?(qe=async()=>{u()},e[105]=u,e[106]=qe):qe=e[106];let Ye;e[107]!==o?(Ye=o("deployment.AddRevision"),e[107]=o,e[108]=Ye):Ye=e[108];let Xe;e[109]!==Ie||e[110]!==qe||e[111]!==Ye?(Xe=n.jsx(ie,{gap:"xs",align:"center",children:n.jsx(Sl,{type:"primary",icon:Pe,disabled:Ie,action:qe,children:Ye})}),e[109]=Ie,e[110]=qe,e[111]=Ye,e[112]=Xe):Xe=e[112];let Je;e[113]!==I||e[114]!==de||e[115]!==se||e[116]!==ce||e[117]!==o||e[118]!==d?(Je=I==="currentRevision"&&n.jsxs(n.Fragment,{children:[ce&&n.jsx(Ll,{type:"info",icon:n.jsx(_n,{spin:!0}),showIcon:!0,style:{marginBottom:d.marginMD},title:o("deployment.ApplyingRevision",{revisionNumber:se.revisionNumber!=null?`#${se.revisionNumber}`:ll(se.id)??""}),action:n.jsx(gl,{onClick:()=>ue(se,"deploying",o("deployment.ApplyingRevisionDetail")),children:o("deployment.ViewRevision")})}),de?n.jsx(ti,{revisionFrgmt:de,status:"current"}):ce?null:n.jsx(qn,{image:qn.PRESENTED_IMAGE_SIMPLE,description:o("deployment.NoCurrentRevisionDeployed")})]}),e[113]=I,e[114]=de,e[115]=se,e[116]=ce,e[117]=o,e[118]=d,e[119]=Je):Je=e[119];let ol;e[120]!==I||e[121]!==m||e[122]!==s?(ol=I==="revisionHistory"&&m&&n.jsx(it,{children:n.jsx(M.Suspense,{fallback:n.jsx(Fl,{active:!0,paragraph:{rows:4}}),children:n.jsx(rs,{deploymentFrgmt:m,deploymentId:m.id,fetchKey:s})})}),e[120]=I,e[121]=m,e[122]=s,e[123]=ol):ol=e[123];let Ce;e[124]!==I||e[125]!==E||e[126]!==m||e[127]!==v?(Ce=I==="auditLog"&&m&&n.jsx(mt,{children:E?n.jsx(M.Suspense,{fallback:n.jsx(Fl,{active:!0,paragraph:{rows:4}}),children:n.jsx(ri,{queryRef:E,onReload:v,tableSettings:{}})}):n.jsx(Fl,{active:!0,paragraph:{rows:4}})}),e[124]=I,e[125]=E,e[126]=m,e[127]=v,e[128]=Ce):Ce=e[128];let al;e[129]!==I||e[130]!==r||e[131]!==Ue||e[132]!==Ze||e[133]!==Xe||e[134]!==Je||e[135]!==ol||e[136]!==Ce?(al=n.jsxs(en,{ref:r,activeTabKey:I,onTabChange:Ue,tabList:Ze,tabBarExtraContent:Xe,children:[Je,ol,Ce]}),e[129]=I,e[130]=r,e[131]=Ue,e[132]=Ze,e[133]=Xe,e[134]=Je,e[135]=ol,e[136]=Ce,e[137]=al):al=e[137];let ul;e[138]!==a?(ul=el=>{A(!1),el&&a()},e[138]=a,e[139]=ul):ul=e[139];let Te;e[140]!==m||e[141]!==C||e[142]!==ul?(Te=n.jsx($a,{open:C,deploymentFrgmt:m,onRequestClose:ul}),e[140]=m,e[141]=C,e[142]=ul,e[143]=Te):Te=e[143];const _e=f==null?void 0:f.revisionFrgmt,sl=f==null?void 0:f.status,il=f==null?void 0:f.title,dl=!!f;let xl;e[144]===Symbol.for("react.memo_cache_sentinel")?(xl=()=>R(null),e[144]=xl):xl=e[144];let hl;e[145]!==_e||e[146]!==sl||e[147]!==il||e[148]!==dl?(hl=n.jsx(kl,{children:n.jsx(pn,{revisionFrgmt:_e,status:sl,title:il,open:dl,onClose:xl})}),e[145]=_e,e[146]=sl,e[147]=il,e[148]=dl,e[149]=hl):hl=e[149];let Ne;e[150]!==o?(Ne=o("deployment.DeleteDeployment"),e[150]=o,e[151]=Ne):Ne=e[151];let vl;e[152]!==o?(vl=o("deployment.Deployment"),e[152]=o,e[153]=vl):vl=e[153];let _l;e[154]!==$?(_l=$?[{key:$,label:$}]:[],e[154]=$,e[155]=_l):_l=e[155];let El;e[156]!==$?(El={placeholder:$},e[156]=$,e[157]=El):El=e[157];let Ol;e[158]!==le?(Ol={loading:le},e[158]=le,e[159]=Ol):Ol=e[159];let tn;e[160]===Symbol.for("react.memo_cache_sentinel")?(tn=()=>U(!1),e[160]=tn):tn=e[160];let $l;e[161]!==$||e[162]!==ye||e[163]!==z||e[164]!==Ne||e[165]!==vl||e[166]!==_l||e[167]!==El||e[168]!==Ol?($l=n.jsx(jn,{open:z,title:Ne,target:vl,items:_l,confirmText:$,requireConfirmInput:!0,inputProps:El,okButtonProps:Ol,onOk:ye,onCancel:tn}),e[161]=$,e[162]=ye,e[163]=z,e[164]=Ne,e[165]=vl,e[166]=_l,e[167]=El,e[168]=Ol,e[169]=$l):$l=e[169];let wl;e[170]!==P||e[171]!==w||e[172]!==L?(wl=P!=null&&n.jsx(kl,{children:n.jsx(os,{open:w,queryRef:P,onReload:L,onCancel:()=>Q(!1)})}),e[170]=P,e[171]=w,e[172]=L,e[173]=wl):wl=e[173];let an;return e[174]!==Ge||e[175]!==al||e[176]!==Te||e[177]!==hl||e[178]!==$l||e[179]!==wl?(an=n.jsxs(n.Fragment,{children:[Ge,al,Te,hl,$l,wl]}),e[174]=Ge,e[175]=al,e[176]=Te,e[177]=hl,e[178]=$l,e[179]=wl,e[180]=an):an=e[180],an},ea=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"sessionId",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"revisionId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"trafficStatus",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"healthStatus",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"sessionV2",plural:!1,selections:[o,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[m],storageKey:null}],storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},x=[m,R],F={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},D={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[o,m,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"DeploymentReplicasTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:u,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[o,d,g,c,k,h,S,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[o,p,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null},f],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,s],kind:"Operation",name:"DeploymentReplicasTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:u,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[o,d,g,c,k,h,S,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[o,p,S,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[m,o],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},R,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[m,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},o],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[F,I,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},D],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[F,I,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},D],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[m,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},f],storageKey:null}],storageKey:null}],storageKey:null},o],storageKey:null}]},params:{cacheID:"c1d73b2e83c2845707ec164df7d4e706",id:null,metadata:{},name:"DeploymentReplicasTabListQuery",operationKind:"query",text:`query DeploymentReplicasTabListQuery(
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
`}}}();ea.hash="26b1dbb98e07f4bdd28168cb4a306efd";const la={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentReplicasTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};la.hash="6134739d7e3addb802e0658f5858bcea";const cs={HEALTHY:"success",UNHEALTHY:"error",DEGRADED:"warning",NOT_CHECKED:"default",PROVISIONING:"info",WARMING_UP:"info",RUNNING:"success",TERMINATING:"warning",TERMINATED:"default",FAILED_TO_START:"error"},ms={HEALTHY:"Healthy",UNHEALTHY:"Unhealthy",DEGRADED:"Degraded",NOT_CHECKED:"NotChecked",PROVISIONING:"Provisioning",WARMING_UP:"WarmingUp",RUNNING:"Running",TERMINATING:"Terminating",TERMINATED:"Terminated",FAILED_TO_START:"FailedToStart"},Jn=l=>{"use memo";const e=tl.c(23);let i,s,t;e[0]!==l?({status:i,showTooltip:s,...t}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t):(i=e[1],s=e[2],t=e[3]);const a=s===void 0?!0:s,{t:u}=rl(),r=cs[i],o=ms[i],d=`replicaStatus.${o}`;let g;e[4]!==u||e[5]!==d?(g=u(d),e[4]=u,e[5]=d,e[6]=g):g=e[6];const c=g;let k;e[7]!==o||e[8]!==a||e[9]!==u?(k=a?u(`replicaStatus.tooltip.${o}`,{defaultValue:""}):void 0,e[7]=o,e[8]=a,e[9]=u,e[10]=k):k=e[10];const h=k;let S;e[11]!==i?(S=i==="WARMING_UP"?n.jsx(_n,{spin:!0}):void 0,e[11]=i,e[12]=S):S=e[12];const p=S;let m;e[13]!==r||e[14]!==p||e[15]!==c||e[16]!==t?(m=n.jsx(mn,{...t,color:r,icon:p,children:c}),e[13]=r,e[14]=p,e[15]=c,e[16]=t,e[17]=m):m=e[17];const f=m;if(!a||!h)return f;let R;e[18]!==f?(R=n.jsx("span",{children:f}),e[18]=f,e[19]=R):R=e[19];let x;return e[20]!==R||e[21]!==h?(x=n.jsx(ml,{title:h,children:R}),e[20]=R,e[21]=h,e[22]=x):x=e[22],x},na=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[u,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,s,e,i],kind:"Operation",name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[u,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},r,o,d,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},o,d,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"e02133438de747b29f05fb0c3109339d",id:null,metadata:{},name:"RouteSchedulingHistoryModalQuery",operationKind:"query",text:`query RouteSchedulingHistoryModalQuery(
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
`}}}();na.hash="e770c8de50ced262d1f75ecd5be88c57";const ta=na,gs=l=>{"use memo";var be,ve,Ke,Se;const e=tl.c(113);let i,s,t,a,u;e[0]!==l?({open:a,queryRef:u,onReload:t,onCancel:s,...i}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=u):(i=e[1],s=e[2],t=e[3],a=e[4],u=e[5]);const{t:r}=rl(),[o,d]=Il(),[g,c]=M.useState(),[k,h]=M.useState("-updatedAt"),[S,p]=Dl("schedulingHistoryExpandMode"),[m,f]=Dl("table_column_overrides.RouteSchedulingHistory");let R;e[6]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[6]=R):R=e[6];const{tablePaginationOption:x,setTablePaginationOption:F}=En(R),I=M.useDeferredValue(u),D=I!==u,C=Le.usePreloadedQuery(ta,I);let A;e[7]!==r?(A=r("route.RouteSchedulingHistory"),e[7]=r,e[8]=A):A=e[8];let z,U;e[9]===Symbol.for("react.memo_cache_sentinel")?(z={maxWidth:1600},U={body:{minHeight:"80vh"}},e[9]=z,e[10]=U):(z=e[9],U=e[10]);let w;e[11]!==t||e[12]!==u.variables||e[13]!==F?(w=ae=>{c(ae),F({current:1}),t({...u.variables,filter:ae,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=u.variables,e[13]=F,e[14]=w):w=e[14];let Q;e[15]!==r?(Q=r("route.ID"),e[15]=r,e[16]=Q):Q=e[16];let P;e[17]!==Q?(P={key:"id",propertyLabel:Q,type:"uuid",fixedOperator:"equals"},e[17]=Q,e[18]=P):P=e[18];let L;e[19]!==r?(L=r("route.Phase"),e[19]=r,e[20]=L):L=e[20];let E;e[21]!==L?(E={key:"phase",propertyLabel:L,type:"string",fixedOperator:"contains"},e[21]=L,e[22]=E):E=e[22];let j;e[23]!==r?(j=r("route.Result"),e[23]=r,e[24]=j):j=e[24];let Y;e[25]===Symbol.for("react.memo_cache_sentinel")?(Y=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=Y):Y=e[25];let W;e[26]!==j?(W={key:"result",propertyLabel:j,type:"enum",strictSelection:!0,options:Y},e[26]=j,e[27]=W):W=e[27];let q;e[28]!==r?(q=r("route.FromStatus"),e[28]=r,e[29]=q):q=e[29];let V;e[30]!==q?(V={key:"fromStatus",propertyLabel:q,type:"string",valueMode:"scalar"},e[30]=q,e[31]=V):V=e[31];let v;e[32]!==r?(v=r("route.ToStatus"),e[32]=r,e[33]=v):v=e[33];let b;e[34]!==v?(b={key:"toStatus",propertyLabel:v,type:"string",valueMode:"scalar"},e[34]=v,e[35]=b):b=e[35];let _;e[36]!==r?(_=r("route.ErrorCode"),e[36]=r,e[37]=_):_=e[37];let J;e[38]!==_?(J={key:"errorCode",propertyLabel:_,type:"string",fixedOperator:"contains"},e[38]=_,e[39]=J):J=e[39];let Z;e[40]!==r?(Z=r("route.Message"),e[40]=r,e[41]=Z):Z=e[41];let ne;e[42]!==Z?(ne={key:"message",propertyLabel:Z,type:"string",fixedOperator:"contains"},e[42]=Z,e[43]=ne):ne=e[43];let K;e[44]!==r?(K=r("route.CreatedAt"),e[44]=r,e[45]=K):K=e[45];let T;e[46]!==K?(T={key:"createdAt",propertyLabel:K,type:"datetime",defaultOperator:"after"},e[46]=K,e[47]=T):T=e[47];let N;e[48]!==r?(N=r("route.UpdatedAt"),e[48]=r,e[49]=N):N=e[49];let H;e[50]!==N?(H={key:"updatedAt",propertyLabel:N,type:"datetime",defaultOperator:"after"},e[50]=N,e[51]=H):H=e[51];let G;e[52]!==W||e[53]!==V||e[54]!==b||e[55]!==J||e[56]!==ne||e[57]!==T||e[58]!==H||e[59]!==P||e[60]!==E?(G=[P,E,W,V,b,J,ne,T,H],e[52]=W,e[53]=V,e[54]=b,e[55]=J,e[56]=ne,e[57]=T,e[58]=H,e[59]=P,e[60]=E,e[61]=G):G=e[61];let ee;e[62]!==g||e[63]!==G||e[64]!==w?(ee=n.jsx(nn,{value:g,onChange:w,filterProperties:G}),e[62]=g,e[63]=G,e[64]=w,e[65]=ee):ee=e[65];let le;e[66]!==t||e[67]!==u.variables||e[68]!==d?(le=ae=>{d(ae),t(u.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=u.variables,e[68]=d,e[69]=le):le=e[69];let $;e[70]!==o||e[71]!==D||e[72]!==le?($=n.jsx(ie,{children:n.jsx(Vl,{value:o,onChange:le,loading:D,autoUpdateDelay:null})}),e[70]=o,e[71]=D,e[72]=le,e[73]=$):$=e[73];let O;e[74]!==ee||e[75]!==$?(O=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[ee,$]}),e[74]=ee,e[75]=$,e[76]=O):O=e[76];const Fe=S??void 0;let ke;e[77]!==m||e[78]!==f?(ke={columnOverrides:m,onColumnOverridesChange:f},e[77]=m,e[78]=f,e[79]=ke):ke=e[79];let me;e[80]!==t||e[81]!==u.variables||e[82]!==F?(me=ae=>{h(ae),F({current:1}),t({...u.variables,orderBy:Ql(ae),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=u.variables,e[82]=F,e[83]=me):me=e[83];const Me=((be=C.routeScopedSchedulingHistories)==null?void 0:be.count)??0;let ye;e[84]!==t||e[85]!==u.variables||e[86]!==F?(ye=(ae,fe)=>{F({current:ae,pageSize:fe}),t({...u.variables,limit:fe,offset:ae>1?(ae-1)*fe:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=u.variables,e[86]=F,e[87]=ye):ye=e[87];let pe;e[88]!==Me||e[89]!==ye||e[90]!==x.current||e[91]!==x.pageSize?(pe={pageSize:x.pageSize,current:x.current,total:Me,onChange:ye},e[88]=Me,e[89]=ye,e[90]=x.current,e[91]=x.pageSize,e[92]=pe):pe=e[92];let ue;e[93]!==((ve=C.routeScopedSchedulingHistories)==null?void 0:ve.edges)?(ue=bl((Ke=C.routeScopedSchedulingHistories)==null?void 0:Ke.edges,"node"),e[93]=(Se=C.routeScopedSchedulingHistories)==null?void 0:Se.edges,e[94]=ue):ue=e[94];let de;e[95]!==D||e[96]!==k||e[97]!==p||e[98]!==Fe||e[99]!==ke||e[100]!==me||e[101]!==pe||e[102]!==ue?(de=n.jsx(Li,{resizable:!0,loading:D,expandMode:Fe,onExpandModeChange:p,tableSettings:ke,order:k,onChangeOrder:me,pagination:pe,schedulingHistoryFrgmt:ue}),e[95]=D,e[96]=k,e[97]=p,e[98]=Fe,e[99]=ke,e[100]=me,e[101]=pe,e[102]=ue,e[103]=de):de=e[103];let se;e[104]!==O||e[105]!==de?(se=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[O,de]}),e[104]=O,e[105]=de,e[106]=se):se=e[106];let ce;return e[107]!==i||e[108]!==s||e[109]!==a||e[110]!==A||e[111]!==se?(ce=n.jsx(Ul,{title:A,open:a,width:"90%",style:z,styles:U,footer:null,onCancel:s,...i,children:se}),e[107]=i,e[108]=s,e[109]=a,e[110]=A,e[111]=se,e[112]=ce):ce=e[112],ce},Zn=["TERMINATED","FAILED_TO_START"],ys=l=>l==="terminated"?{status:{in:[...Zn]}}:{status:{notIn:[...Zn]}},Sn=(l,e)=>({...l,...ys(e)}),Tn=["createdAt","id"],ps=[...Tn,...Tn.map(l=>`-${l}`)],et=l=>An(Tn,l),hn=l=>l??"NOT_CHECKED",fs=({deploymentFrgmt:l,deploymentId:e,replicaFetchKey:i})=>{"use memo";var Y,W,q,V;const{t:s}=rl(),[t,a]=M.useTransition(),[u,r]=Dl("table_column_overrides.DeploymentReplicasTab"),[o,d]=Vn({current:cn.withDefault(1),pageSize:cn.withDefault(10),order:ln(ps),rFilter:rt,rStatusCategory:ln(["running","terminated"]).withDefault("running")},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rOrder",rFilter:"rFilter",rStatusCategory:"rStatusCategory"}});Le.useFragment(la,l);const g=v=>{if(!v)return null;try{const b=JSON.parse(v);return b&&typeof b=="object"&&!Array.isArray(b)?b:null}catch{return null}},c=v=>!v||Object.keys(v).length===0?"":JSON.stringify(v),[k,h]=M.useState(()=>({filter:Sn(o.rFilter?g(o.rFilter):null,o.rStatusCategory),orderBy:Ql(o.order||"-createdAt"),limit:o.pageSize,offset:o.current>1?(o.current-1)*o.pageSize:0})),[S,p]=M.useState(0),f=ct().supports("route-scheduling-history"),[R,x]=M.useState(!1),[F,I]=Le.useQueryLoader(ta),[D,C]=M.useState(null),[A,z]=M.useState(null),{deployment:U}=Le.useLazyLoadQuery(ea,{deploymentId:e,...k},{fetchKey:`${S}-${i??""}`,fetchPolicy:"network-only"}),w=((q=(W=(Y=U==null?void 0:U.replicas)==null?void 0:Y.edges)==null?void 0:W.map(v=>v==null?void 0:v.node))==null?void 0:q.filter(v=>!!v))??[],Q=v=>{a(()=>{h(b=>({...b,...v}))})},P=[{label:s("replicaStatus.Active"),value:"ACTIVE"},{label:s("replicaStatus.Inactive"),value:"INACTIVE"}],L=[{key:"trafficStatus",propertyLabel:s("deployment.TrafficStatus"),type:"enum",options:P,strictSelection:!0}],E=o.rFilter?g(o.rFilter)??void 0:void 0,j=gn([{key:"id",title:s("deployment.ReplicaId"),dataIndex:"id",fixed:"left",sorter:et("id"),render:v=>n.jsx(Hl,{globalId:v,copyable:!0})},{key:"status",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.ReplicaLifecycle"),n.jsx(pl,{title:s("deployment.ReplicaLifecycleStatusTooltip")})]}),dataIndex:"status",render:(v,b)=>n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(Jn,{status:hn(v)}),f&&n.jsx(ml,{title:s("route.RouteSchedulingHistory"),children:n.jsx(Sl,{type:"link",icon:n.jsx(kt,{}),size:"small",style:{padding:0},action:async()=>{const _=Bl(b.id)??b.id;I({scope:{routeId:_},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),x(!0)}})})]})},{key:"healthStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.HealthStatus"),n.jsx(pl,{title:s("deployment.HealthStatusTooltip")})]}),dataIndex:"healthStatus",render:(v,b)=>n.jsx(Jn,{status:hn(v),showTooltip:hn(b.status)!=="TERMINATED"})},{key:"trafficStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.TrafficStatus"),n.jsx(pl,{title:s("deployment.TrafficStatusTooltip")})]}),dataIndex:"trafficStatus",render:v=>n.jsx(mn,{color:v==="ACTIVE"?"success":"default",children:s(v==="ACTIVE"?"replicaStatus.Active":"replicaStatus.Inactive")})},{key:"session",title:s("general.Session"),onCell:()=>({style:{maxWidth:240}}),render:(v,b)=>{var Z;const _=b.sessionV2;if(!(_!=null&&_.id))return n.jsx(nl.Text,{type:"secondary",children:"—"});const J=(Z=_.metadata)==null?void 0:Z.name;return J?n.jsxs(n.Fragment,{children:[n.jsx(Ha,{ellipsis:!0,onClick:()=>C(ll(_.id)),style:{maxWidth:160},children:J})," ",n.jsxs(nl.Text,{type:"secondary",children:["(",n.jsx(Hl,{globalId:_.id,type:"secondary"}),")"]})]}):n.jsx(Hl,{globalId:_.id})}},{key:"revision",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.RevisionNumberWithID"),n.jsx(pl,{title:s("deployment.RevisionNumberTooltip")})]}),render:(v,b)=>{const _=b.revision;return _!=null&&_.id?n.jsxs(n.Fragment,{children:[n.jsx(nl.Link,{onClick:()=>z(_),children:_.revisionNumber!=null?`#${_.revisionNumber}`:"-"})," ",n.jsxs(nl.Text,{type:"secondary",children:["(",n.jsx(Hl,{globalId:_.id,type:"secondary"}),")"]})]}):n.jsx(nl.Text,{type:"secondary",children:"—"})}},{key:"createdAt",title:s("deployment.CreatedAt"),dataIndex:"createdAt",sorter:et("createdAt"),render:v=>v?cl(v).format("lll"):"-"}]);return n.jsxs(n.Fragment,{children:[n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:12},children:[n.jsxs(ie,{gap:"sm",align:"start",wrap:"wrap",style:{flexShrink:1},children:[n.jsx(Ba,{value:o.rStatusCategory,onChange:v=>{const b=v.target.value,_=o.rFilter?g(o.rFilter):null;d({rStatusCategory:b,current:1}),Q({filter:Sn(_,b),offset:0})},options:[{label:s("deployment.Running"),value:"running"},{label:s("deployment.status.Terminated"),value:"terminated"}]}),n.jsx(nn,{filterProperties:L,value:E,onChange:v=>{const b=c(v);d({rFilter:b||null,current:1}),Q({filter:Sn(v??null,o.rStatusCategory),offset:0})}})]}),n.jsx(Vl,{loading:t,value:"",onChange:()=>{a(()=>p(v=>v+1))}})]}),n.jsx(ql,{rowKey:v=>v.id,dataSource:w,columns:j,loading:t,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:u,onColumnOverridesChange:r},order:o.order,onChangeOrder:v=>{d({order:v??null}),Q({orderBy:Ql(v||"-createdAt")})},pagination:{pageSize:o.pageSize,current:o.current,total:((V=U==null?void 0:U.replicas)==null?void 0:V.count)??0,onChange:(v,b)=>{d({current:v,pageSize:b});const _=v>1?(v-1)*b:0;Q({limit:b,offset:_})}}}),n.jsx(kl,{children:n.jsx(ni,{open:!!D,sessionId:D??void 0,onClose:()=>C(null)})}),n.jsx(kl,{children:n.jsx(pn,{open:!!A,revisionFrgmt:A,onClose:()=>z(null)})}),F!=null&&n.jsx(kl,{children:n.jsx(gs,{open:R,queryRef:F,onReload:I,onCancel:()=>x(!1)})})]})},aa=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"projectId"}],e=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"projectId"}],concreteType:"GroupNode",kind:"LinkedField",name:"group_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SwitchToProjectButtonQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SwitchToProjectButtonQuery",selections:e},params:{cacheID:"d9b043a52eacadb018a0097fe3c1f3c2",id:null,metadata:{},name:"SwitchToProjectButtonQuery",operationKind:"query",text:`query SwitchToProjectButtonQuery(
  $projectId: String!
) {
  group_node(id: $projectId) @since(version: "24.03.0") {
    id
    name
  }
}
`}}}();aa.hash="4618e2aed2bc3c75a1d0a91f0b01c28c";const ks=l=>{"use memo";const e=tl.c(20);let i,s;e[0]!==l?({projectId:s,...i}=l,e[0]=l,e[1]=i,e[2]=s):(i=e[1],s=e[2]);const{t}=rl(),a=Qa(),[u,r]=M.useTransition();let o;e[3]===Symbol.for("react.memo_cache_sentinel")?(o=aa,e[3]=o):o=e[3];let d;e[4]!==s?(d=Jl("GroupNode",s),e[4]=s,e[5]=d):d=e[5];let g;e[6]!==d?(g={projectId:d},e[6]=d,e[7]=g):g=e[7];const{group_node:c}=Le.useLazyLoadQuery(o,g);let k;e[8]!==(c==null?void 0:c.id)||e[9]!==(c==null?void 0:c.name)||e[10]!==a?(k=()=>{const f=ll((c==null?void 0:c.id)||""),R=c==null?void 0:c.name;f&&R&&r(()=>{a({projectId:f,projectName:R})})},e[8]=c==null?void 0:c.id,e[9]=c==null?void 0:c.name,e[10]=a,e[11]=k):k=e[11];const h=k,S=c==null?void 0:c.name;let p;e[12]!==t||e[13]!==S?(p=t("modelService.SwitchToProject",{projectName:S}),e[12]=t,e[13]=S,e[14]=p):p=e[14];let m;return e[15]!==i||e[16]!==h||e[17]!==u||e[18]!==p?(m=n.jsx(Sl,{type:"link",size:"small",loading:u,onClick:h,...i,children:p}),e[15]=i,e[16]=h,e[17]=u,e[18]=p,e[19]=m):m=e[19],m},Ss=l=>n.jsx(M.Suspense,{fallback:n.jsx(Sl,{type:"link",size:"small",loading:!0}),children:n.jsx(ks,{...l})}),Es=()=>{"use memo";var he,Ge,Ue,Oe,Be,Qe,We,Re,$e,Ze,Pe;const l=tl.c(115),{t:e}=rl(),{token:i}=Cl.useToken(),[s]=st(),t=yn(),a=Nn(),u=Pn();let r;l[0]!==((he=a==null?void 0:a._config)==null?void 0:he.blockList)?(r=(Ue=(Ge=a==null?void 0:a._config)==null?void 0:Ge.blockList)==null?void 0:Ue.includes("chat"),l[0]=(Oe=a==null?void 0:a._config)==null?void 0:Oe.blockList,l[1]=r):r=l[1];const o=!!r,{deploymentId:d}=qa(),g=d??"";let c;l[2]!==g?(c=Jl("ModelDeployment",g),l[2]=g,l[3]=c):c=l[3];const k=c,[h,S]=M.useTransition(),[p,m]=Il(),[f,R]=Il(),[x,F]=Il(),[I,D]=zn(!1),{setLeft:C,setRight:A}=D,[z,U]=zn(!1),{setLeft:w,setRight:Q}=U,P=M.useRef(null),L=M.useRef(null),[E,j]=M.useState(null);let Y;l[4]===Symbol.for("react.memo_cache_sentinel")?(Y=Tt,l[4]=Y):Y=l[4];let W;l[5]!==k?(W={deploymentId:k},l[5]=k,l[6]=W):W=l[6];const q=p===bn?"store-and-network":"network-only";let V;l[7]!==p||l[8]!==q?(V={fetchKey:p,fetchPolicy:q},l[7]=p,l[8]=q,l[9]=V):V=l[9];const{deployment:v}=Le.useLazyLoadQuery(Y,W,V);if(!v.ok){const Ie=v.errors;if(Ie.some(vs)){let Je;return l[10]===Symbol.for("react.memo_cache_sentinel")?(Je=n.jsx(hs,{}),l[10]=Je):Je=l[10],Je}const Ye=Ie.map(Fs).filter(Boolean),Xe=new Error(Ye.join("; ")||"DeploymentDetailPageQuery failed.");throw Xe.errors=Ie,Xe}const b=v.value,_=b.metadata.name,J=b.metadata.status,Z=J==="READY",ne=b.metadata.projectId??null,K=!!ne&&ne!==u.id,T=!b.currentRevision&&!b.deployingRevision,N=!!b.networkAccess.endpointUrl,H=(((Be=b.accessTokens)==null?void 0:Be.count)??0)>0;let G;l[11]!==J?(G=fl(J),l[11]=J,l[12]=G):G=l[12];const ee=G,le=b.networkAccess.openToPublic===!1&&!ee&&N&&!H,$=((We=(Qe=b.creator)==null?void 0:Qe.basicInfo)==null?void 0:We.email)??null,O=!$||$===s.email;let Fe;l[13]!==m?(Fe=()=>{S(()=>m())},l[13]=m,l[14]=Fe):Fe=l[14];const ke=Fe;let me;l[15]!==C||l[16]!==((Re=i.Layout)==null?void 0:Re.headerHeight)||l[17]!==m||l[18]!==F||l[19]!==R?(me=(Ie,qe)=>{var Ye;C(),Ie&&(qe&&j(qe),S(()=>{m(),R(),F()}),P.current&&(P.current.style.scrollMarginTop=`${((Ye=i.Layout)==null?void 0:Ye.headerHeight)??60}px`,P.current.scrollIntoView({behavior:"smooth",block:"start"})))},l[15]=C,l[16]=($e=i.Layout)==null?void 0:$e.headerHeight,l[17]=m,l[18]=F,l[19]=R,l[20]=me):me=l[20];const Me=me;let ye;l[21]!==ne||l[22]!==K||l[23]!==e?(ye=K&&ne&&n.jsx(Ll,{type:"warning",showIcon:!0,title:e("deployment.NotInProject"),action:n.jsx(Ss,{projectId:ne})}),l[21]=ne,l[22]=K,l[23]=e,l[24]=ye):ye=l[24];let pe;l[25]!==g||l[26]!==T||l[27]!==o||l[28]!==Z||l[29]!==e||l[30]!==i.fontSizeLG||l[31]!==t?(pe=Z&&!T&&n.jsx(Ll,{type:"success",showIcon:!0,title:e("deployment.DeploymentReady"),action:!o&&n.jsx(gl,{type:"primary",icon:n.jsx(za,{size:i.fontSizeLG}),onClick:()=>{t({pathname:"/chat",search:new URLSearchParams({endpointId:g}).toString()})},children:e("deployment.StartChatTest")})}),l[25]=g,l[26]=T,l[27]=o,l[28]=Z,l[29]=e,l[30]=i.fontSizeLG,l[31]=t,l[32]=pe):pe=l[32];let ue;l[33]!==J||l[34]!==T||l[35]!==K||l[36]!==A||l[37]!==e?(ue=T&&!K&&!fl(J)&&n.jsx(Ll,{type:"warning",showIcon:!0,title:e("deployment.NoCurrentRevisionDeployed"),action:n.jsx(Sl,{type:"primary",icon:n.jsx(jl,{}),action:async()=>{A()},children:e("deployment.AddRevision")})}),l[33]=J,l[34]=T,l[35]=K,l[36]=A,l[37]=e,l[38]=ue):ue=l[38];let de;l[39]!==ee||l[40]!==le||l[41]!==Q||l[42]!==e?(de=le&&n.jsx(Ll,{type:"info",showIcon:!0,title:e("deployment.PrivateDeploymentAlertTitle"),action:n.jsx(Sl,{type:"primary",icon:n.jsx(jl,{}),action:async()=>{Q()},disabled:ee,children:e("deployment.AddAccessToken")})}),l[39]=ee,l[40]=le,l[41]=Q,l[42]=e,l[43]=de):de=l[43];let se;l[44]===Symbol.for("react.memo_cache_sentinel")?(se={margin:0},l[44]=se):se=l[44];let ce;l[45]!==_?(ce=n.jsx(nl.Title,{level:3,style:se,children:_}),l[45]=_,l[46]=ce):ce=l[46];let be;l[47]!==J?(be=n.jsx(St,{status:J}),l[47]=J,l[48]=be):be=l[48];let ve;l[49]!==ce||l[50]!==be?(ve=n.jsxs(ie,{direction:"row",align:"center",gap:"sm",children:[ce,be]}),l[49]=ce,l[50]=be,l[51]=ve):ve=l[51];let Ke;l[52]!==b||l[53]!==ke||l[54]!==h||l[55]!==A||l[56]!==f?(Ke=n.jsx(us,{deploymentFrgmt:b,revisionFetchKey:f,isPendingRefetch:h,onRefetch:ke,onAddRevision:A,revisionCardRef:P}),l[52]=b,l[53]=ke,l[54]=h,l[55]=A,l[56]=f,l[57]=Ke):Ke=l[57];let Se;l[58]!==e?(Se=e("deployment.tab.Replicas"),l[58]=e,l[59]=Se):Se=l[59];let ae;l[60]!==e?(ae=e("deployment.tab.description.Replicas"),l[60]=e,l[61]=ae):ae=l[61];let fe;l[62]!==i.colorTextDescription?(fe=n.jsx(Cn,{style:{color:i.colorTextDescription}}),l[62]=i.colorTextDescription,l[63]=fe):fe=l[63];let we;l[64]!==ae||l[65]!==fe?(we=n.jsx(ml,{title:ae,children:fe}),l[64]=ae,l[65]=fe,l[66]=we):we=l[66];let De;l[67]!==Se||l[68]!==we?(De=n.jsxs(ie,{gap:"xs",align:"center",children:[Se,we]}),l[67]=Se,l[68]=we,l[69]=De):De=l[69];let xe;l[70]===Symbol.for("react.memo_cache_sentinel")?(xe={body:{paddingTop:0}},l[70]=xe):xe=l[70];let He;l[71]===Symbol.for("react.memo_cache_sentinel")?(He=n.jsx(Fl,{active:!0}),l[71]=He):He=l[71];let y;l[72]!==b||l[73]!==k||l[74]!==x?(y=n.jsx(mt,{children:n.jsx(M.Suspense,{fallback:He,children:n.jsx(fs,{deploymentFrgmt:b,deploymentId:k,replicaFetchKey:x})})}),l[72]=b,l[73]=k,l[74]=x,l[75]=y):y=l[75];let B;l[76]!==De||l[77]!==y?(B=n.jsx(en,{title:De,styles:xe,children:y}),l[76]=De,l[77]=y,l[78]=B):B=l[78];let X;l[79]!==b?(X=n.jsx(is,{deploymentFrgmt:b}),l[79]=b,l[80]=X):X=l[80];let te;l[81]!==w||l[82]!==Q?(te=Ie=>{Ie?Q():w()},l[81]=w,l[82]=Q,l[83]=te):te=l[83];let re;l[84]!==ke||l[85]!==((Ze=i.Layout)==null?void 0:Ze.headerHeight)?(re=()=>{var Ie;ke(),L.current&&(L.current.style.scrollMarginTop=`${((Ie=i.Layout)==null?void 0:Ie.headerHeight)??60}px`,L.current.scrollIntoView({behavior:"smooth",block:"start"}))},l[84]=ke,l[85]=(Pe=i.Layout)==null?void 0:Pe.headerHeight,l[86]=re):re=l[86];let oe;l[87]!==z||l[88]!==b||l[89]!==k||l[90]!==ee||l[91]!==O||l[92]!==te||l[93]!==re?(oe=n.jsx(ji,{cardRef:L,deploymentFrgmt:b,deploymentId:k,isOwnedByCurrentUser:O,isDeploymentDestroying:ee,isCreateModalOpen:z,onCreateModalOpenChange:te,onTokenCreated:re}),l[87]=z,l[88]=b,l[89]=k,l[90]=ee,l[91]=O,l[92]=te,l[93]=re,l[94]=oe):oe=l[94];let Ae;l[95]!==I||l[96]!==b||l[97]!==Me?(Ae=n.jsx(kl,{children:n.jsx(_t,{open:I,onRequestClose:Me,deploymentFrgmt:b})}),l[95]=I,l[96]=b,l[97]=Me,l[98]=Ae):Ae=l[98];const Ve=!!E;let Ee;l[99]===Symbol.for("react.memo_cache_sentinel")?(Ee=()=>j(null),l[99]=Ee):Ee=l[99];let je;l[100]!==E||l[101]!==Ve?(je=n.jsx(kl,{children:n.jsx(pn,{revisionFrgmt:E,open:Ve,onClose:Ee})}),l[100]=E,l[101]=Ve,l[102]=je):je=l[102];let ze;return l[103]!==ye||l[104]!==pe||l[105]!==ue||l[106]!==de||l[107]!==ve||l[108]!==Ke||l[109]!==B||l[110]!==X||l[111]!==oe||l[112]!==Ae||l[113]!==je?(ze=n.jsxs(ie,{direction:"column",align:"stretch",gap:"md",children:[ye,pe,ue,de,ve,Ke,B,X,oe,Ae,je]}),l[103]=ye,l[104]=pe,l[105]=ue,l[106]=de,l[107]=ve,l[108]=Ke,l[109]=B,l[110]=X,l[111]=oe,l[112]=Ae,l[113]=je,l[114]=ze):ze=l[114],ze},hs=()=>{"use memo";const l=tl.c(39),{t:e}=rl(),i=yn(),{firstAvailableMenuItem:s}=Ua();let t;l[0]!==s?(t=s?Wa(s.key):"/start",l[0]=s,l[1]=t):t=l[1];const a=t;let u,r,o,d,g,c,k,h,S,p,m;if(l[2]!==a||l[3]!==(s==null?void 0:s.labelText)||l[4]!==e||l[5]!==i){const F=(s==null?void 0:s.labelText)??e("webui.menu.FirstPageNameAlias");o=ie,l[17]===Symbol.for("react.memo_cache_sentinel")?(S={margin:"auto"},l[17]=S):S=l[17],p="center",m="center",r=Ga,k="warning",l[18]!==e?(h=e("deployment.NotAccessibleOrDeleted"),l[18]=e,l[19]=h):h=l[19],u=gl,d="primary",l[20]!==a||l[21]!==i?(g=()=>{i(a)},l[20]=a,l[21]=i,l[22]=g):g=l[22],c=e("button.GoBackToStartPage",{title:F}),l[2]=a,l[3]=s==null?void 0:s.labelText,l[4]=e,l[5]=i,l[6]=u,l[7]=r,l[8]=o,l[9]=d,l[10]=g,l[11]=c,l[12]=k,l[13]=h,l[14]=S,l[15]=p,l[16]=m}else u=l[6],r=l[7],o=l[8],d=l[9],g=l[10],c=l[11],k=l[12],h=l[13],S=l[14],p=l[15],m=l[16];let f;l[23]!==u||l[24]!==d||l[25]!==g||l[26]!==c?(f=n.jsx(u,{type:d,onClick:g,children:c}),l[23]=u,l[24]=d,l[25]=g,l[26]=c,l[27]=f):f=l[27];let R;l[28]!==r||l[29]!==k||l[30]!==h||l[31]!==f?(R=n.jsx(r,{status:k,title:h,extra:f}),l[28]=r,l[29]=k,l[30]=h,l[31]=f,l[32]=R):R=l[32];let x;return l[33]!==o||l[34]!==R||l[35]!==S||l[36]!==p||l[37]!==m?(x=n.jsx(o,{style:S,justify:p,align:m,children:R}),l[33]=o,l[34]=R,l[35]=S,l[36]=p,l[37]=m,l[38]=x):x=l[38],x};function vs(l){return/Insufficient permission/i.test((l==null?void 0:l.message)??"")}function Fs(l){return(l==null?void 0:l.message)??""}export{Es as default};
//# sourceMappingURL=DeploymentDetailPage-B4vsXDkV.js.map
