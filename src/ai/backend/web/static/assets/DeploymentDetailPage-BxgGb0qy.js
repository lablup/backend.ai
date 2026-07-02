import{bS as Qn,h as Be,ad as fn,r as V,aB as cn,cl as Jt,ar as Rl,d2 as qn,b8 as $l,i as Ke,cm as Zt,a6 as hl,bT as ea,ac as kn,bi as In,j as n,aw as Sl,b6 as la,co as na,bA as Hl,N as Ye,m as Sn,cb as ta,cn as aa,a$ as ia,a1 as tn,aK as Dl,b5 as Pl,bV as il,bM as Cl,a3 as hn,u as Ze,t as Kl,A as Al,v as Vl,K as zn,cc as vn,T as Xe,am as dl,B as ie,aA as Ml,b4 as Il,z as yl,bI as Wl,a7 as pl,P as _l,F as pe,d3 as sa,aX as Fn,aZ as xn,b7 as bn,aQ as mn,au as zl,aj as Un,d4 as ra,a as Rn,a4 as Tl,d5 as Ql,bg as bl,b2 as ul,d6 as oa,w as ql,cf as da,b3 as Cn,aG as An,y as wl,bp as cl,aP as Mn,d7 as ua,d8 as ca,d9 as ma,da as ga,db as jl,dc as pa,Y as ya,dd as fa,a8 as ka,bm as Ln,de as Xl,bC as Jl,H as Wn,df as Sa,cD as Gn,bf as ha,aq as va,aF as Fa,dg as xa,M as ba,a5 as Ra,dh as Ka,cd as Bl,di as gl,aY as Ta,f as Zl,bZ as Yn,c$ as Da,bt as Ul,bu as Kn,bs as Ia,b$ as Tn,bX as Nl,p as an,Z as Xn,cL as Jn,d0 as Ca,dj as Zn,G as et,d1 as Aa,D as Ma,bW as ln,bU as Dn,bJ as lt,cY as nt,dk as nn,cG as La,c1 as ja,ai as jn,dl as Nn,c2 as Na,dm as Pa,dn as Va,dp as _a,dq as Ea,aV as Pn,dr as Oa,ds as $a,dt as wa,du as Ba}from"./index-DLl5_15D.js";import{f as Ha,t as Qa}from"./parseCliCommand-DLNI3aPC.js";import{R as qa,b as za}from"./RuntimeParameterFormSection-BShOZudV.js";import{B as Vn}from"./BAIVFolderSelect-D03J9hbe.js";import{P as Ua}from"./PrometheusQueryTemplatePreview-BcLUYf78.js";import{B as tt,n as at,u as it,a as st,o as Wa,R as rt,S as Ga}from"./SessionDetailDrawer-BekQ3rgv.js";import{B as Gl}from"./BAIGraphQLPropertyFilter-BVY69KXO.js";import{i as kl,a as ot,B as Ya,D as sn,b as Xa}from"./DeploymentRevisionDetailDrawer-yvw1W0py.js";import{B as Ll}from"./BAIId-CUEnOS4w.js";import{B as Ja}from"./BooleanTag-Ca7dIHjt.js";import{S as Za,a as ei}from"./ScopedAuditLog-CBMDUmPr.js";import{F as li}from"./FolderLink-C2HMK66Z.js";import"./UndoOutlined-CIuBdUX1.js";import"./corner-down-left-CAJyc4A5.js";import"./zip-DsMATQHn.js";import"./unzip-ML45z091.js";import"./WarningOutlined-BSgfKkny.js";import"./camelCase-psNhqco0.js";/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ni=[["line",{x1:"15",x2:"15",y1:"12",y2:"18",key:"1p7wdc"}],["line",{x1:"12",x2:"18",y1:"15",y2:"15",key:"1nscbv"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2",key:"17jyea"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",key:"zix9uf"}]],_n=Qn("copy-plus",ni);/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ti=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",key:"usdka0"}]],En=Qn("folder-open",ti),dt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},r=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"NAME"}]}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e,i],kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectPaginatedQuery",selections:r,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[i,e,l],kind:"Operation",name:"BAIRuntimeVariantSelectPaginatedQuery",selections:r},params:{cacheID:"e8d20623434b823880b9543cf3297c3f",id:null,metadata:{},name:"BAIRuntimeVariantSelectPaginatedQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectPaginatedQuery(
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
`}}}();dt.hash="65da05baef2fee7bd3840fc61e39a8d8";const ut=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"},{defaultValue:null,kind:"LocalArgument",name:"skip"}],e=[{condition:"skip",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectValueQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIRuntimeVariantSelectValueQuery",selections:e},params:{cacheID:"f029b9c8b12e9bc799f1ff1caaebd031",id:null,metadata:{},name:"BAIRuntimeVariantSelectValueQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectValueQuery(
  $id: UUID!
  $skip: Boolean!
) {
  runtimeVariant(id: $id) @skip(if: $skip) {
    id
    name
  }
}
`}}}();ut.hash="f7c1435633aeb06ecc9eafe324f06550";const ai=l=>{"use memo";var Ee;const e=Be.c(74);let i,r,t,a;e[0]!==l?({loading:i,onResolvedNamesChange:r,ref:t,...a}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a):(i=e[1],r=e[2],t=e[3],a=e[4]);const{t:d}=fn(),s=V.useRef(null),[u,o]=cn(a);let m;e[5]===Symbol.for("react.memo_cache_sentinel")?(m={valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"},e[5]=m):m=e[5];const[c,f]=cn(a,m),g=V.useDeferredValue(c),[y,S]=V.useState(),p=Jt(y),[h,F]=V.useOptimistic(y),[b,x]=V.useTransition(),[K,R]=Rl(),A=V.useDeferredValue(K),D=V.useDeferredValue(u);let $;e[6]!==D?($=D?qn($l(D)):"",e[6]=D,e[7]=$):$=e[7];const q=$;let L;e[8]===Symbol.for("react.memo_cache_sentinel")?(L=ut,e[8]=L):L=e[8];const _=!q;let C;e[9]!==q||e[10]!==_?(C={id:q,skip:_},e[9]=q,e[10]=_,e[11]=C):C=e[11];const M=q?"store-or-network":"store-only";let Q;e[12]!==A||e[13]!==M?(Q={fetchPolicy:M,fetchKey:A},e[12]=A,e[13]=M,e[14]=Q):Q=e[14];const{runtimeVariant:E}=Ke.useLazyLoadQuery(L,C,Q);let z;e[15]!==p?(z=p?{name:{iContains:p}}:null,e[15]=p,e[16]=z):z=e[16];const U=z;let G,O;e[17]===Symbol.for("react.memo_cache_sentinel")?(O=dt,G={limit:20},e[17]=G,e[18]=O):(G=e[17],O=e[18]);let B;e[19]!==U?(B={filter:U},e[19]=U,e[20]=B):B=e[20];const k=g?"network-only":"store-only";let P;e[21]!==A||e[22]!==k?(P={fetchPolicy:k,fetchKey:A},e[21]=A,e[22]=k,e[23]=P):P=e[23];let N;e[24]===Symbol.for("react.memo_cache_sentinel")?(N={getTotal:ii,getItem:ri,getId:oi},e[24]=N):N=e[24];const{paginationData:Y,result:Z,loadNext:I,isLoadingNext:T}=Zt(O,G,B,P,N);let j,H;e[25]!==R?(j=()=>({refetch:()=>{x(()=>{R()})}}),H=[R,x],e[25]=R,e[26]=j,e[27]=H):(j=e[26],H=e[27]),V.useImperativeHandle(t,j,H);let W;e[28]!==r||e[29]!==Y||e[30]!==E?(W=()=>{if(!r)return;const Ce={};if(E!=null&&E.id&&E.name){const Te=Ye(E.id);Te&&(Ce[Te]=E.name)}for(const Te of Y??[])if(Te!=null&&Te.id&&Te.name){const we=Ye(Te.id);we&&(Ce[we]=Te.name)}Sn(Ce)||r(Ce)},e[28]=r,e[29]=Y,e[30]=E,e[31]=W):W=e[31];const ee=V.useEffectEvent(W);let X;e[32]!==ee?(X=()=>{ee()},e[32]=ee,e[33]=X):X=e[33];let le;e[34]!==Y||e[35]!==E?(le=[E,Y],e[34]=Y,e[35]=E,e[36]=le):le=e[36],V.useEffect(X,le);let w;e[37]!==Y?(w=hl(Y,di),e[37]=Y,e[38]=w):w=e[38];const te=w,ue=E==null?void 0:E.name;let ce;e[39]!==D||e[40]!==ue?(ce=D?{label:ue??$l(D),value:$l(D)}:void 0,e[39]=D,e[40]=ue,e[41]=ce):ce=e[41];const Re=ce,[ye,oe]=V.useState(Re);let de;e[42]!==d?(de=d("comp:BAIRuntimeVariantSelect.SelectRuntimeVariant"),e[42]=d,e[43]=de):de=e[43];const me=i||u!==D||y!==p||b;let re;e[44]!==a||e[45]!==F?(re=async Ce=>{var Te;F(Ce),S(Ce),await((Te=a.searchAction)==null?void 0:Te.call(a,Ce))},e[44]=a,e[45]=F,e[46]=re):re=e[46];let fe;e[47]!==h||e[48]!==a.showSearch?(fe=a.showSearch===!1?!1:{searchValue:h,autoClearSearchValue:!0,...ea(a.showSearch)?kn(a.showSearch,["searchValue"]):{},filterOption:!1},e[47]=h,e[48]=a.showSearch,e[49]=fe):fe=e[49];const Fe=u!==D?ye:Re;let be;e[50]!==te||e[51]!==o?(be=(Ce,Te)=>{var ne;if(In(Ce)||ta(Ce)){oe(void 0),o(void 0,Te);return}const we=aa(Ce)[0],J={label:ia(we.label)?we.label:((ne=te.find(se=>se.value===we.value))==null?void 0:ne.label)??$l(we.value),value:$l(we.value)};oe(J),o(J.value,Te)},e[50]=te,e[51]=o,e[52]=be):be=e[52];let ve;e[53]!==I?(ve=()=>{I()},e[53]=I,e[54]=ve):ve=e[54];let he;e[55]!==Y?(he=In(Y)?n.jsx(Sl.Input,{active:!0,size:"small",block:!0}):void 0,e[55]=Y,e[56]=he):he=e[56];let ae;e[57]!==T||e[58]!==Z.runtimeVariants?(ae=la((Ee=Z.runtimeVariants)==null?void 0:Ee.count)&&Z.runtimeVariants.count>0?n.jsx(na,{loading:T,total:Z.runtimeVariants.count}):void 0,e[57]=T,e[58]=Z.runtimeVariants,e[59]=ae):ae=e[59];let Se;return e[60]!==te||e[61]!==c||e[62]!==a||e[63]!==f||e[64]!==de||e[65]!==me||e[66]!==re||e[67]!==fe||e[68]!==Fe||e[69]!==be||e[70]!==ve||e[71]!==he||e[72]!==ae?(Se=n.jsx(Hl,{ref:s,placeholder:de,loading:me,...a,searchAction:re,showSearch:fe,value:Fe,labelInValue:!0,onChange:be,options:te,endReached:ve,open:c,onOpenChange:f,notFoundContent:he,footer:ae}),e[60]=te,e[61]=c,e[62]=a,e[63]=f,e[64]=de,e[65]=me,e[66]=re,e[67]=fe,e[68]=Fe,e[69]=be,e[70]=ve,e[71]=he,e[72]=ae,e[73]=Se):Se=e[73],Se};function ii(l){var e;return((e=l.runtimeVariants)==null?void 0:e.count)??void 0}function si(l){return l==null?void 0:l.node}function ri(l){var e,i;return(i=(e=l.runtimeVariants)==null?void 0:e.edges)==null?void 0:i.map(si)}function oi(l){return l==null?void 0:l.id}function di(l){return{label:l==null?void 0:l.name,value:l!=null&&l.id?Ye(l.id):void 0}}const ct={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"DeploymentHistory",abstractKey:null};ct.hash="eb0787126d34e31d6d0aa79127c25d2f";const gn=[];[...gn,...gn.map(l=>`-${l}`)];const vl=l=>hn(gn,l),ui=l=>{"use memo";const e=Be.c(23);let i,r,t,a,d;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:r,customizeColumns:i,onChangeOrder:t,...d}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=fn();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=ct,e[6]=u):u=e[6];const o=Ke.useFragment(u,a);let m;if(e[7]!==i||e[8]!==r||e[9]!==s){let p;e[11]!==r?(p=F=>r?kn(F,"sorter"):F,e[11]=r,e[12]=p):p=e[12];const h=hl(tn([{dataIndex:"updatedAt",title:s("comp:BAIDeploymentSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:ci,sorter:vl("updated_at")},{dataIndex:"createdAt",title:s("comp:BAIDeploymentSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:mi,sorter:vl("created_at")},{dataIndex:"phase",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Phase"),key:"phase",sorter:vl("phase")},{dataIndex:"result",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Result"),key:"result",render:gi,sorter:vl("result")},{dataIndex:"category",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Category"),key:"category",sorter:vl("category")},{key:"fromStatus",title:s("comp:BAIDeploymentSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:vl("from_status")},{key:"toStatus",title:s("comp:BAIDeploymentSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:vl("to_status")},{dataIndex:"attempts",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:vl("attempts")},{key:"errorCode",title:s("comp:BAIDeploymentSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:pi,sorter:vl("errorCode")},{key:"message",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:yi,render:fi,sorter:vl("message")}]),p);m=i?i(h):h,e[7]=i,e[8]=r,e[9]=s,e[10]=m}else m=e[10];const c=m;let f;e[13]!==o?(f=Dl(o),e[13]=o,e[14]=f):f=e[14];let g;e[15]===Symbol.for("react.memo_cache_sentinel")?(g={x:"max-content"},e[15]=g):g=e[15];let y;e[16]!==t?(y=p=>{t==null||t(p||null)},e[16]=t,e[17]=y):y=e[17];let S;return e[18]!==c||e[19]!==f||e[20]!==y||e[21]!==d?(S=n.jsx(Pl,{rowKey:"id",dataSource:f,columns:c,scroll:g,onChangeOrder:y,...d}),e[18]=c,e[19]=f,e[20]=y,e[21]=d,e[22]=S):S=e[22],S};function ci(l){return n.jsx("span",{children:il(l).format("ll LTS")})}function mi(l){return n.jsx("span",{children:il(l).format("ll LTS")})}function gi(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(tt,{result:i})}function pi(l,e){return e.errorCode?n.jsx(Cl,{monospace:!0,children:e.errorCode}):"-"}function yi(){return{style:{maxWidth:500}}}function fi(l,e){return e.message?n.jsx(Cl,{title:e.message,style:{width:"100%"},children:at(e.message)}):"-"}const mt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryNodeTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"RouteHistory",abstractKey:null};mt.hash="bd0c64d2e599015d8b9db0afbcb05c7c";const pn=[];[...pn,...pn.map(l=>`-${l}`)];const Fl=l=>hn(pn,l),ki=l=>{"use memo";const e=Be.c(23);let i,r,t,a,d;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:r,customizeColumns:i,onChangeOrder:t,...d}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=fn();let u;e[6]===Symbol.for("react.memo_cache_sentinel")?(u=mt,e[6]=u):u=e[6];const o=Ke.useFragment(u,a);let m;if(e[7]!==i||e[8]!==r||e[9]!==s){let p;e[11]!==r?(p=F=>r?kn(F,"sorter"):F,e[11]=r,e[12]=p):p=e[12];const h=hl(tn([{dataIndex:"updatedAt",title:s("comp:BAIRouteSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:Si,sorter:Fl("updated_at")},{dataIndex:"createdAt",title:s("comp:BAIRouteSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:hi,sorter:Fl("created_at")},{dataIndex:"phase",title:s("comp:BAIRouteSchedulingHistoryNodes.Phase"),key:"phase",sorter:Fl("phase")},{dataIndex:"result",title:s("comp:BAIRouteSchedulingHistoryNodes.Result"),key:"result",render:vi,sorter:Fl("result")},{dataIndex:"category",title:s("comp:BAIRouteSchedulingHistoryNodes.Category"),key:"category",sorter:Fl("category")},{key:"fromStatus",title:s("comp:BAIRouteSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Fl("from_status")},{key:"toStatus",title:s("comp:BAIRouteSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Fl("to_status")},{dataIndex:"attempts",title:s("comp:BAIRouteSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Fl("attempts")},{key:"errorCode",title:s("comp:BAIRouteSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Fi,sorter:Fl("errorCode")},{key:"message",title:s("comp:BAIRouteSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:xi,render:bi,sorter:Fl("message")}]),p);m=i?i(h):h,e[7]=i,e[8]=r,e[9]=s,e[10]=m}else m=e[10];const c=m;let f;e[13]!==o?(f=Dl(o),e[13]=o,e[14]=f):f=e[14];let g;e[15]===Symbol.for("react.memo_cache_sentinel")?(g={x:"max-content"},e[15]=g):g=e[15];let y;e[16]!==t?(y=p=>{t==null||t(p||null)},e[16]=t,e[17]=y):y=e[17];let S;return e[18]!==c||e[19]!==f||e[20]!==y||e[21]!==d?(S=n.jsx(Pl,{rowKey:"id",dataSource:f,columns:c,scroll:g,onChangeOrder:y,...d}),e[18]=c,e[19]=f,e[20]=y,e[21]=d,e[22]=S):S=e[22],S};function Si(l){return n.jsx("span",{children:il(l).format("ll LTS")})}function hi(l){return n.jsx("span",{children:il(l).format("ll LTS")})}function vi(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(tt,{result:i})}function Fi(l,e){return e.errorCode?n.jsx(Cl,{monospace:!0,children:e.errorCode}):"-"}function xi(){return{style:{maxWidth:500}}}function bi(l,e){return e.message?n.jsx(Cl,{title:e.message,style:{width:"100%"},children:at(e.message)}):"-"}const gt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryNodesFragment"}],type:"DeploymentHistory",abstractKey:null};gt.hash="72a9b8118e4f52a97c2ab8996996098d";const Ri=l=>{"use memo";const e=Be.c(26);let i,r,t,a;e[0]!==l?({schedulingHistoryFrgmt:a,expandMode:i,onExpandModeChange:r,...t}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a):(i=e[1],r=e[2],t=e[3],a=e[4]);let d;e[5]===Symbol.for("react.memo_cache_sentinel")?(d=gt,e[5]=d):d=e[5];const s=Ke.useFragment(d,a);let u;e[6]!==s?(u=Dl(s),e[6]=s,e[7]=u):u=e[7];const o=u;let m;e[8]!==i||e[9]!==r?(m={mode:i,onModeChange:r},e[8]=i,e[9]=r,e[10]=m):m=e[10];const{mode:c,expandedRowKeys:f,onExpandedRowsChange:g,expandColumnTitle:y}=it(o,m);let S;e[11]!==o?(S=b=>{var x;return!Sn((x=o.find(K=>K.id===b.id))==null?void 0:x.subSteps)},e[11]=o,e[12]=S):S=e[12];let p;e[13]!==o||e[14]!==c?(p=b=>{var x;return n.jsx(st,{resizable:!0,subStepsFrgmt:((x=o.find(K=>K.id===b.id))==null?void 0:x.subSteps)??[],pagination:!1,errorsOnly:c==="errors-only"})},e[13]=o,e[14]=c,e[15]=p):p=e[15];let h;e[16]!==y||e[17]!==f||e[18]!==g||e[19]!==S||e[20]!==p?(h={columnTitle:y,expandedRowKeys:f,onExpandedRowsChange:g,rowExpandable:S,expandedRowRender:p},e[16]=y,e[17]=f,e[18]=g,e[19]=S,e[20]=p,e[21]=h):h=e[21];let F;return e[22]!==s||e[23]!==t||e[24]!==h?(F=n.jsx(ui,{schedulingHistoryFrgmt:s,expandable:h,...t}),e[22]=s,e[23]=t,e[24]=h,e[25]=F):F=e[25],F},pt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryNodeTableFragment"}],type:"RouteHistory",abstractKey:null};pt.hash="7f5f32e6a4ea10ddfc54ff01c8b260b2";const Ki=l=>{"use memo";const e=Be.c(26);let i,r,t,a;e[0]!==l?({schedulingHistoryFrgmt:a,expandMode:i,onExpandModeChange:r,...t}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a):(i=e[1],r=e[2],t=e[3],a=e[4]);let d;e[5]===Symbol.for("react.memo_cache_sentinel")?(d=pt,e[5]=d):d=e[5];const s=Ke.useFragment(d,a);let u;e[6]!==s?(u=Dl(s),e[6]=s,e[7]=u):u=e[7];const o=u;let m;e[8]!==i||e[9]!==r?(m={mode:i,onModeChange:r},e[8]=i,e[9]=r,e[10]=m):m=e[10];const{mode:c,expandedRowKeys:f,onExpandedRowsChange:g,expandColumnTitle:y}=it(o,m);let S;e[11]!==o?(S=b=>{var x;return!Sn((x=o.find(K=>K.id===b.id))==null?void 0:x.subSteps)},e[11]=o,e[12]=S):S=e[12];let p;e[13]!==o||e[14]!==c?(p=b=>{var x;return n.jsx(st,{resizable:!0,subStepsFrgmt:((x=o.find(K=>K.id===b.id))==null?void 0:x.subSteps)??[],pagination:!1,errorsOnly:c==="errors-only"})},e[13]=o,e[14]=c,e[15]=p):p=e[15];let h;e[16]!==y||e[17]!==f||e[18]!==g||e[19]!==S||e[20]!==p?(h={columnTitle:y,expandedRowKeys:f,onExpandedRowsChange:g,rowExpandable:S,expandedRowRender:p},e[16]=y,e[17]=f,e[18]=g,e[19]=S,e[20]=p,e[21]=h):h=e[21];let F;return e[22]!==s||e[23]!==t||e[24]!==h?(F=n.jsx(ki,{schedulingHistoryFrgmt:s,expandable:h,...t}),e[22]=s,e[23]=t,e[24]=h,e[25]=F):F=e[25],F},yt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},d={alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},s={alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},u=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],o={alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:u,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},m={alias:null,args:null,concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:u,storageKey:null},c=[i],f={alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},S={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,r,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[g,y,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},S],storageKey:null},h={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},b=[r,F],x={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null}],storageKey:null},K={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},R={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[g,y,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},S],storageKey:null},A={alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[r,i],storageKey:null},D={alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null},$={alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},F,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null},q={alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},M={alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},Q={alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},E={alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},z={alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},U={alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},G={alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},O={alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},B={alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},k={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentDetailPageQuery",selections:[{kind:"CatchField",field:{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,t,a],storageKey:null},d,s,o,m,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[f],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentBasicInfoCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentReplicasCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAccessTokensCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAutoScalingCard_deployment"}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,t,a,{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[r],storageKey:null},i],storageKey:null}],storageKey:null},d,s,o,m,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,p,h,x,K,R,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},A,D,$,q],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,L,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[_,C,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},M,Q,E,z,U,G],storageKey:null},O,B],storageKey:null}],storageKey:null}],storageKey:null},k,P,N,K,k],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:[i,P,N,h,K,x,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[A,q,D,$],storageKey:null},p,R,k,{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,L,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[_,O,C,B,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[M,E,Q,z,U,G],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[f,i],storageKey:null}],storageKey:null}]},params:{cacheID:"cf0be491960db330acb124fcdb02e651",id:null,metadata:{},name:"DeploymentDetailPageQuery",operationKind:"query",text:`query DeploymentDetailPageQuery(
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
`}}}();yt.hash="9089d2f31b9601fe2fa64e840ab45300";const ft=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAccessTokenPayload",kind:"LinkedField",name:"deleteAccessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardDeleteMutation",selections:e},params:{cacheID:"3001cf022c16a198843b296bca8e75f9",id:null,metadata:{},name:"DeploymentAccessTokensCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensCardDeleteMutation(
  $input: DeleteAccessTokenInput!
) {
  deleteAccessToken(input: $input) {
    id
  }
}
`}}}();ft.hash="6877559748beeee076979bb65393d59f";const kt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:[{kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"CREATED_AT"}]}],concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"AccessTokenEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:'accessTokens(orderBy:[{"direction":"DESC","field":"CREATED_AT"}])'};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[r],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[r,i],storageKey:null}]},params:{cacheID:"fe0599e3ca582035a0afb69f61751a53",id:null,metadata:{},name:"DeploymentAccessTokensCardListQuery",operationKind:"query",text:`query DeploymentAccessTokensCardListQuery(
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
`}}}();kt.hash="b43bdbd02f49d9e5a3e3b15dac4c1b90";const St=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAccessTokenPayload",kind:"LinkedField",name:"createAccessToken",plural:!1,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"accessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardCreateMutation",selections:e},params:{cacheID:"8c08238f7222fe51a04881e736d82b15",id:null,metadata:{},name:"DeploymentAccessTokensCardCreateMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensCardCreateMutation(
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
`}}}();St.hash="4ba926c16e8cf928584ec3a34cde8b34";const ht={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};ht.hash="e7372d3fa2bb21537f6b39e44698dedf";const Ti=l=>{"use memo";var be;const e=Be.c(95);let i,r,t,a,d,s,u;e[0]!==l?({deploymentFrgmt:t,deploymentId:a,isOwnedByCurrentUser:s,isDeploymentDestroying:u,onTokenCreated:d,cardRef:i,...r}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d,e[6]=s,e[7]=u):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5],s=e[6],u=e[7]);const o=s===void 0?!0:s,m=u===void 0?!1:u,{t:c}=Ze(),{token:f}=Kl.useToken(),{message:g}=Al.useApp(),{logger:y}=Vl(),[S,p]=V.useTransition(),[h,F]=Rl();let b;e[8]===Symbol.for("react.memo_cache_sentinel")?(b={defaultValue:!1,valuePropName:"isCreateModalOpen",trigger:"onCreateModalOpenChange"},e[8]=b):b=e[8];const[x,K]=cn(r,b),[R,A]=V.useState(null),D=V.useDeferredValue(h);let $;e[9]===Symbol.for("react.memo_cache_sentinel")?($=ht,e[9]=$):$=e[9];const q=Ke.useFragment($,t);let L;e[10]===Symbol.for("react.memo_cache_sentinel")?(L=St,e[10]=L):L=e[10];const _=zn(L);let C;e[11]!==F?(C=()=>{p(()=>{F()})},e[11]=F,e[12]=C):C=e[12];const M=C,Q=!!((be=q.networkAccess)!=null&&be.endpointUrl),E=m||!o,z=E||!Q;let U;e[13]!==c?(U=c("deployment.tab.AccessTokens"),e[13]=c,e[14]=U):U=e[14];let G;e[15]!==c?(G=c("deployment.tab.description.AccessTokens"),e[15]=c,e[16]=G):G=e[16];let O;e[17]!==f.colorTextDescription?(O=n.jsx(vn,{style:{color:f.colorTextDescription}}),e[17]=f.colorTextDescription,e[18]=O):O=e[18];let B;e[19]!==G||e[20]!==O?(B=n.jsx(dl,{title:G,children:O}),e[19]=G,e[20]=O,e[21]=B):B=e[21];let k;e[22]!==B||e[23]!==U?(k=n.jsxs(ie,{gap:"xs",align:"center",children:[U,B]}),e[22]=B,e[23]=U,e[24]=k):k=e[24];let P;e[25]!==M||e[26]!==S?(P=n.jsx(Ml,{loading:S,value:"",onChange:M}),e[25]=M,e[26]=S,e[27]=P):P=e[27];let N;e[28]!==Q||e[29]!==c?(N=Q?"":c("deployment.accessToken.EndpointNotIssuedYet"),e[28]=Q,e[29]=c,e[30]=N):N=e[30];let Y;e[31]===Symbol.for("react.memo_cache_sentinel")?(Y=n.jsx(Il,{}),e[31]=Y):Y=e[31];let Z;e[32]!==K?(Z=()=>K(!0),e[32]=K,e[33]=Z):Z=e[33];let I;e[34]!==c?(I=c("deployment.accessToken.Create"),e[34]=c,e[35]=I):I=e[35];let T;e[36]!==z||e[37]!==Z||e[38]!==I?(T=n.jsx(yl,{type:"primary",icon:Y,disabled:z,onClick:Z,children:I}),e[36]=z,e[37]=Z,e[38]=I,e[39]=T):T=e[39];let j;e[40]!==N||e[41]!==T?(j=n.jsx(dl,{title:N,children:T}),e[40]=N,e[41]=T,e[42]=j):j=e[42];let H;e[43]!==P||e[44]!==j?(H=n.jsxs(ie,{gap:"xs",align:"center",children:[P,j]}),e[43]=P,e[44]=j,e[45]=H):H=e[45];let W;e[46]===Symbol.for("react.memo_cache_sentinel")?(W={body:{paddingTop:0}},e[46]=W):W=e[46];let ee;e[47]===Symbol.for("react.memo_cache_sentinel")?(ee=n.jsx(Sl,{active:!0}),e[47]=ee):ee=e[47];let X;e[48]!==D||e[49]!==a||e[50]!==M||e[51]!==E||e[52]!==S?(X=n.jsx(V.Suspense,{fallback:ee,children:n.jsx(Di,{deploymentId:a,fetchKey:D,isPendingRefetch:S,isDeleteDisabled:E,onAfterDelete:M})}),e[48]=D,e[49]=a,e[50]=M,e[51]=E,e[52]=S,e[53]=X):X=e[53];let le;e[54]!==i||e[55]!==k||e[56]!==H||e[57]!==X?(le=n.jsx(Wl,{ref:i,title:k,extra:H,styles:W,children:X}),e[54]=i,e[55]=k,e[56]=H,e[57]=X,e[58]=le):le=e[58];let w;e[59]!==_||e[60]!==q.id||e[61]!==M||e[62]!==y||e[63]!==g||e[64]!==d||e[65]!==K||e[66]!==c?(w=ve=>{K(!1),ve&&_({input:{modelDeploymentId:Ye(q.id),expiresAt:ve.expiresAt??new Date("2099-12-31").toISOString()}}).then(he=>{var Se;const ae=(Se=he.createAccessToken)==null?void 0:Se.accessToken;ae&&A({token:ae.token,expiresAt:ae.expiresAt??null}),g.success({key:"access-token-created",content:c("deployment.accessToken.Created")}),M(),d==null||d()}).catch(he=>{const ae=Array.isArray(he)?he:[he];for(const Se of ae)g.error((Se==null?void 0:Se.message)||c("dialog.ErrorOccurred"));y.error(he)})},e[59]=_,e[60]=q.id,e[61]=M,e[62]=y,e[63]=g,e[64]=d,e[65]=K,e[66]=c,e[67]=w):w=e[67];let te;e[68]!==x||e[69]!==w?(te=n.jsx(pl,{children:n.jsx(Ii,{open:x,confirmLoading:!1,onRequestClose:w})}),e[68]=x,e[69]=w,e[70]=te):te=e[70];const ue=R!==null;let ce;e[71]!==c?(ce=c("deployment.accessToken.Token"),e[71]=c,e[72]=ce):ce=e[72];let Re;e[73]===Symbol.for("react.memo_cache_sentinel")?(Re=()=>A(null),e[73]=Re):Re=e[73];let ye;e[74]!==c?(ye=c("deployment.accessToken.Created"),e[74]=c,e[75]=ye):ye=e[75];let oe;e[76]!==ye?(oe=n.jsx(Xe.Text,{children:ye}),e[76]=ye,e[77]=oe):oe=e[77];let de;e[78]!==R?(de=R?n.jsx(Cl,{copyable:{text:R.token},ellipsis:!0,code:!0,children:R.token}):null,e[78]=R,e[79]=de):de=e[79];let me;e[80]!==R||e[81]!==c?(me=R!=null&&R.expiresAt?n.jsx(Xe.Text,{type:"secondary",children:`${c("deployment.accessToken.Expiration")}: ${il(R.expiresAt).format("ll LT")}`}):n.jsx(Xe.Text,{type:"secondary",children:c("deployment.accessToken.NoExpiration")}),e[80]=R,e[81]=c,e[82]=me):me=e[82];let re;e[83]!==oe||e[84]!==de||e[85]!==me?(re=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[oe,de,me]}),e[83]=oe,e[84]=de,e[85]=me,e[86]=re):re=e[86];let fe;e[87]!==ue||e[88]!==ce||e[89]!==re?(fe=n.jsx(pl,{children:n.jsx(_l,{open:ue,destroyOnHidden:!0,title:ce,onCancel:Re,footer:null,width:520,children:re})}),e[87]=ue,e[88]=ce,e[89]=re,e[90]=fe):fe=e[90];let Fe;return e[91]!==le||e[92]!==te||e[93]!==fe?(Fe=n.jsxs(n.Fragment,{children:[le,te,fe]}),e[91]=le,e[92]=te,e[93]=fe,e[94]=Fe):Fe=e[94],Fe},Di=l=>{"use memo";var W,ee,X,le;const e=Be.c(71),{deploymentId:i,fetchKey:r,isPendingRefetch:t,isDeleteDisabled:a,onAfterDelete:d}=l,{t:s}=Ze(),{message:u}=Al.useApp(),{logger:o}=Vl(),[m,c]=V.useState(null),f=r===zl;let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g=kt,e[0]=g):g=e[0];let y;e[1]!==i?(y={deploymentId:i},e[1]=i,e[2]=y):y=e[2];const S=f?"store-and-network":"network-only";let p;e[3]!==r||e[4]!==S?(p={fetchKey:r,fetchPolicy:S},e[3]=r,e[4]=S,e[5]=p):p=e[5];const{deployment:h}=Ke.useLazyLoadQuery(g,y,p);let F;e[6]!==((W=h==null?void 0:h.accessTokens)==null?void 0:W.edges)?(F=Dl((X=(ee=h==null?void 0:h.accessTokens)==null?void 0:ee.edges)==null?void 0:X.map(Ci)),e[6]=(le=h==null?void 0:h.accessTokens)==null?void 0:le.edges,e[7]=F):F=e[7];const b=F;let x;e[8]===Symbol.for("react.memo_cache_sentinel")?(x=ft,e[8]=x):x=e[8];const[K,R]=Ke.useMutation(x);let A;e[9]===Symbol.for("react.memo_cache_sentinel")?(A={x:"max-content"},e[9]=A):A=e[9];const D=t||R;let $;e[10]!==s?($=s("deployment.accessToken.Token"),e[10]=s,e[11]=$):$=e[11];let q;e[12]!==a||e[13]!==s?(q=(w,te)=>te?n.jsx(Fn,{title:n.jsx(Cl,{copyable:{text:te.token},ellipsis:!0,style:{maxWidth:200},children:te.token}),showActions:"always",actions:[{key:"delete",title:s("deployment.accessToken.Delete"),icon:n.jsx(xn,{}),type:"danger",disabled:a,onClick:()=>c({id:te.id,token:te.token??""})}]}):"-",e[12]=a,e[13]=s,e[14]=q):q=e[14];let L;e[15]!==q||e[16]!==$?(L={key:"token",title:$,dataIndex:"token",render:q},e[15]=q,e[16]=$,e[17]=L):L=e[17];let _;e[18]!==s?(_=s("deployment.CreatedAt"),e[18]=s,e[19]=_):_=e[19];let C;e[20]!==_?(C={key:"createdAt",title:_,dataIndex:"createdAt",render:Ai},e[20]=_,e[21]=C):C=e[21];let M;e[22]!==s?(M=s("deployment.accessToken.Expiration"),e[22]=s,e[23]=M):M=e[23];let Q;e[24]!==s?(Q=(w,te)=>te!=null&&te.expiresAt?il(te.expiresAt).format("ll LT"):s("deployment.accessToken.NoExpiration"),e[24]=s,e[25]=Q):Q=e[25];let E;e[26]!==M||e[27]!==Q?(E={key:"expiresAt",title:M,dataIndex:"expiresAt",render:Q},e[26]=M,e[27]=Q,e[28]=E):E=e[28];let z;e[29]!==L||e[30]!==C||e[31]!==E?(z=[L,C,E],e[29]=L,e[30]=C,e[31]=E,e[32]=z):z=e[32];let U;e[33]!==b||e[34]!==z||e[35]!==D?(U=n.jsx(Pl,{scroll:A,rowKey:"id",loading:D,dataSource:b,pagination:!1,resizable:!0,columns:z}),e[33]=b,e[34]=z,e[35]=D,e[36]=U):U=e[36];const G=!!m;let O;e[37]!==s?(O=s("deployment.accessToken.Delete"),e[37]=s,e[38]=O):O=e[38];let B;e[39]!==s?(B=s("deployment.AccessToken"),e[39]=s,e[40]=B):B=e[40];let k;e[41]!==m?(k=m?[{key:m.id,label:m.id}]:[],e[41]=m,e[42]=k):k=e[42];let P;e[43]!==s?(P=s("data.folders.DeleteForeverConfirmText"),e[43]=s,e[44]=P):P=e[44];let N;e[45]!==s?(N=s("data.folders.DeleteForeverConfirmText"),e[45]=s,e[46]=N):N=e[46];let Y;e[47]!==N?(Y={placeholder:N},e[47]=N,e[48]=Y):Y=e[48];let Z;e[49]!==R?(Z={loading:R},e[49]=R,e[50]=Z):Z=e[50];let I;e[51]!==K||e[52]!==m||e[53]!==o||e[54]!==u||e[55]!==d||e[56]!==s?(I=()=>{m&&K({variables:{input:{id:Ye(m.id)??m.id}},onCompleted:(w,te)=>{var ue;if(te&&te.length>0){o.error(te[0]),u.error(((ue=te[0])==null?void 0:ue.message)??s("dialog.ErrorOccurred"));return}u.success(s("deployment.accessToken.Deleted")),c(null),d()},onError:w=>{o.error(w),u.error(w.message??s("dialog.ErrorOccurred"))}})},e[51]=K,e[52]=m,e[53]=o,e[54]=u,e[55]=d,e[56]=s,e[57]=I):I=e[57];let T;e[58]===Symbol.for("react.memo_cache_sentinel")?(T=()=>c(null),e[58]=T):T=e[58];let j;e[59]!==G||e[60]!==O||e[61]!==B||e[62]!==k||e[63]!==P||e[64]!==Y||e[65]!==Z||e[66]!==I?(j=n.jsx(bn,{open:G,title:O,target:B,items:k,confirmText:P,requireConfirmInput:!0,inputProps:Y,okButtonProps:Z,onOk:I,onCancel:T}),e[59]=G,e[60]=O,e[61]=B,e[62]=k,e[63]=P,e[64]=Y,e[65]=Z,e[66]=I,e[67]=j):j=e[67];let H;return e[68]!==U||e[69]!==j?(H=n.jsxs(n.Fragment,{children:[U,j]}),e[68]=U,e[69]=j,e[70]=H):H=e[70],H},Ii=l=>{"use memo";const e=Be.c(64),{open:i,confirmLoading:r,onRequestClose:t}=l,{t:a}=Ze(),[d]=pe.useForm(),s=pe.useWatch("expiryOption",d)??7;let u;e[0]!==d||e[1]!==t?(u=()=>{d.validateFields().then(O=>{let B;O.expiryOption==="none"?B=null:O.expiryOption==="custom"?B=O.datetime.toISOString():B=il().add(O.expiryOption,"day").toISOString(),t({expiresAt:B})}).catch(Mi)},e[0]=d,e[1]=t,e[2]=u):u=e[2];const o=u;let m;e[3]!==a?(m=a("general.Days",{num:7,defaultValue:"7 days"}),e[3]=a,e[4]=m):m=e[4];let c;e[5]!==m?(c={value:7,label:m},e[5]=m,e[6]=c):c=e[6];let f;e[7]!==a?(f=a("general.Days",{num:30,defaultValue:"30 days"}),e[7]=a,e[8]=f):f=e[8];let g;e[9]!==f?(g={value:30,label:f},e[9]=f,e[10]=g):g=e[10];let y;e[11]!==a?(y=a("general.Days",{num:90,defaultValue:"90 days"}),e[11]=a,e[12]=y):y=e[12];let S;e[13]!==y?(S={value:90,label:y},e[13]=y,e[14]=S):S=e[14];let p;e[15]!==a?(p=a("deployment.accessToken.CustomExpiration"),e[15]=a,e[16]=p):p=e[16];let h;e[17]!==p?(h={value:"custom",label:p},e[17]=p,e[18]=h):h=e[18];let F;e[19]!==a?(F=a("deployment.accessToken.NoExpiration"),e[19]=a,e[20]=F):F=e[20];let b;e[21]!==F?(b={value:"none",label:F},e[21]=F,e[22]=b):b=e[22];let x;e[23]!==b||e[24]!==c||e[25]!==g||e[26]!==S||e[27]!==h?(x=[c,g,S,h,b],e[23]=b,e[24]=c,e[25]=g,e[26]=S,e[27]=h,e[28]=x):x=e[28];const K=x;let R;e[29]!==a?(R=a("deployment.accessToken.Create"),e[29]=a,e[30]=R):R=e[30];let A;e[31]!==a?(A=a("deployment.accessToken.Create"),e[31]=a,e[32]=A):A=e[32];let D;e[33]!==t?(D=()=>t(),e[33]=t,e[34]=D):D=e[34];let $,q;e[35]===Symbol.for("react.memo_cache_sentinel")?($={expiryOption:7,datetime:il().add(7,"day")},q=["onChange","onBlur"],e[35]=$,e[36]=q):($=e[35],q=e[36]);let L;e[37]!==a?(L=a("deployment.accessToken.Expiration"),e[37]=a,e[38]=L):L=e[38];let _;e[39]===Symbol.for("react.memo_cache_sentinel")?(_=[{required:!0}],e[39]=_):_=e[39];let C;e[40]===Symbol.for("react.memo_cache_sentinel")?(C={width:200},e[40]=C):C=e[40];let M;e[41]!==d?(M=O=>{typeof O=="number"&&d.setFieldValue("datetime",il().add(O,"day"))},e[41]=d,e[42]=M):M=e[42];let Q;e[43]!==K||e[44]!==M?(Q=n.jsx(mn,{style:C,options:K,onChange:M}),e[43]=K,e[44]=M,e[45]=Q):Q=e[45];let E;e[46]!==L||e[47]!==Q?(E=n.jsx(pe.Item,{name:"expiryOption",label:L,rules:_,children:Q}),e[46]=L,e[47]=Q,e[48]=E):E=e[48];let z;e[49]!==s||e[50]!==a?(z=s==="custom"&&n.jsx(pe.Item,{name:"datetime",label:a("deployment.accessToken.CustomExpiration"),rules:[{type:"object",required:!0},()=>({validator(O,B){return B&&il(B).isAfter(il())?Promise.resolve():Promise.reject(new Error(a("dialog.ErrorOccurred")))}})],children:n.jsx(sa,{showTime:!0,format:"YYYY-MM-DD HH:mm:ss",style:{width:"100%"}})}),e[49]=s,e[50]=a,e[51]=z):z=e[51];let U;e[52]!==d||e[53]!==E||e[54]!==z?(U=n.jsxs(pe,{form:d,layout:"vertical",initialValues:$,validateTrigger:q,children:[E,z]}),e[52]=d,e[53]=E,e[54]=z,e[55]=U):U=e[55];let G;return e[56]!==r||e[57]!==o||e[58]!==i||e[59]!==R||e[60]!==A||e[61]!==D||e[62]!==U?(G=n.jsx(_l,{open:i,destroyOnHidden:!0,centered:!0,width:420,title:R,okText:A,confirmLoading:r,onOk:o,onCancel:D,children:U}),e[56]=r,e[57]=o,e[58]=i,e[59]=R,e[60]=A,e[61]=D,e[62]=U,e[63]=G):G=e[63],G};function Ci(l){return l==null?void 0:l.node}function Ai(l,e){return e!=null&&e.createdAt?il(e.createdAt).format("ll LT"):"-"}function Mi(){}const vt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"71af54781375e6ee4bceb1c73e74d088",id:null,metadata:{},name:"DeploymentAddRevisionModalImageNameQuery",operationKind:"query",text:`query DeploymentAddRevisionModalImageNameQuery(
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
`}}}();vt.hash="7f7c91d5e401085de1ab4d56ffb2ef9b";const Ft=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},t={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},d=[i,r],s={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},o={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},m={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},g=[c,f],y={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null}],storageKey:null},S={alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},f,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},F={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},b={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,h,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},F],storageKey:null},x={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[p,h,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},F],storageKey:null},K={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},R={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},A=[i,s,u,o,m,y,S,b,x,K,R];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,r,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:d,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,s,u,o,m,y,S,b,x,K,R,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:A,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:A,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"97d46eaffe190c0a696e6d7daacc3529",id:null,metadata:{},name:"DeploymentAddRevisionModalAddMutation",operationKind:"mutation",text:`mutation DeploymentAddRevisionModalAddMutation(
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
`}}}();Ft.hash="889773e313c63748043b8294cd2bb0b0";const xt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i},params:{cacheID:"6728695a02d457f55b4cd4d3323823d8",id:null,metadata:{},name:"DeploymentAddRevisionModalSelectedPresetQuery",operationKind:"query",text:`query DeploymentAddRevisionModalSelectedPresetQuery(
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
`}}}();xt.hash="e9d60ac2d9540dae9c821fe3abd4b65e";const bt=function(){var l=[{alias:null,args:[{kind:"Literal",name:"first",value:1},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"RANK"}]}],concreteType:"DeploymentRevisionPresetConnection",kind:"LinkedField",name:"deploymentRevisionPresets",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:'deploymentRevisionPresets(first:1,orderBy:[{"direction":"ASC","field":"RANK"}])'}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetCountQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAddRevisionModalPresetCountQuery",selections:l},params:{cacheID:"edaa5efa78debd74168a24185822d633",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetCountQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetCountQuery {
  deploymentRevisionPresets(orderBy: [{field: RANK, direction: "ASC"}], first: 1) {
    count
  }
}
`}}}();bt.hash="4461df1967b1117642d3190b36d5cb33";const Rt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[l,e],r={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_revisionSource",selections:[{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:i,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[r,t],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[l],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:i,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[r,t,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelRevision",abstractKey:null}}();Rt.hash="94f9806003b984d4534543e7895a61e8";const Kt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Kt.hash="614548b7fde80b4972dfb192b893b832";const Tt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentPresetDetailModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[i,r,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,r],storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startupCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"bootstrapScript",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"image",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[r,t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetDeploymentDefaults",kind:"LinkedField",name:"deploymentDefaults",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"replicaCount",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"revisionHistoryLimit",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentStrategy",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValueEntry",kind:"LinkedField",name:"presetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},t],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"ccd4b84ef4b7bf255f7a95f4bbbacd00",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetDetailQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetDetailQuery(
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
`}}}();Tt.hash="8f60ae6bcf0fa60919e80838391f66f9";const rn=({children:l})=>{const{token:e}=Kl.useToken();return n.jsx(Wn,{titlePlacement:"left",children:n.jsx(Xe.Text,{type:"secondary",style:{fontSize:e.fontSizeSM},children:l})})},Li=l=>{"use memo";const e=Be.c(6),{presetId:i,onCancel:r}=l;let t;e[0]===Symbol.for("react.memo_cache_sentinel")?(t=Tt,e[0]=t):t=e[0];let a;e[1]!==i?(a={id:i},e[1]=i,e[2]=a):a=e[2];const d=Ke.useLazyLoadQuery(t,a);let s;return e[3]!==d.deploymentRevisionPreset||e[4]!==r?(s=n.jsx(Sa,{open:!0,presetFrgmt:d.deploymentRevisionPreset,onCancel:r}),e[3]=d.deploymentRevisionPreset,e[4]=r,e[5]=s):s=e[5],s},Dt=({onRequestClose:l,deploymentFrgmt:e,sourceRevisionFrgmt:i,open:r,...t})=>{"use memo";var Ce,Te,we;const{t:a}=Ze(),{token:d}=Kl.useToken(),{message:s}=Al.useApp(),u=Ke.useRelayEnvironment(),o=Ke.useFragment(Kt,e),m=Rt,c=Ke.useFragment(m,(o==null?void 0:o.currentRevision)??null),f=Ke.useFragment(m,i??null),{id:g}=Un(),{logger:y}=Vl(),{open:S}=ra(),p=Rn(),h=p.supports("model-health-check-enable"),F=p.supports("model-runtime-variant-preset-values"),b=V.useRef(null),x=V.useRef(null),[K,R]=V.useState(!1),[A]=pe.useForm(),[D]=pe.useForm(),[$,q]=V.useState(!0),[L,_]=Tl("deploymentRevisionCreationMode"),C=L??"preset",[M,Q]=V.useState(!1),[E,z]=V.useState(!1),[U,G]=V.useState(!1),[O,B]=V.useState(null),[k,P]=V.useState(null),[N,Y]=V.useState(null),[Z,I]=V.useState({}),T=V.useRef(new Set),j=V.useRef(null),[H,W]=V.useState(void 0),ee=V.useRef({}),[X,le]=V.useState(void 0);V.useEffect(()=>{if(!r)return;let v=!1;return Ke.fetchQuery(u,bt,{},{fetchPolicy:"store-or-network"}).toPromise().then(J=>{var ne;v||le((((ne=J==null?void 0:J.deploymentRevisionPresets)==null?void 0:ne.count)??0)===0)}).catch(()=>{v||le(!1)}),()=>{v=!0}},[r,u]);const w=(Te=(Ce=o==null?void 0:o.currentRevision)==null?void 0:Ce.modelMountConfig)!=null&&Te.vfolderId?Ql("VirtualFolderNode",o.currentRevision.modelMountConfig.vfolderId):void 0,te=V.useRef(new Map),ue=async v=>{const J=te.current.get(v);if(J)return J;const ne=await Ke.fetchQuery(u,xt,{id:v},{fetchPolicy:"store-or-network"}).toPromise(),se=(ne==null?void 0:ne.deploymentRevisionPreset)??null;return se&&te.current.set(v,se),se},[ce,Re]=Ke.useMutation(Ft),ye=async v=>{var He,xe,el,Qe,We,qe,ze,Je;const J=v.resourceSlots??[],ne=J.find(De=>De.slotName==="cpu"),se=J.find(De=>De.slotName==="mem"),ge=J.find(De=>De.slotName!=="cpu"&&De.slotName!=="mem"),ke=(((He=v.resource)==null?void 0:He.resourceOpts)??[]).find(De=>De.name==="shmem"),Pe=((xe=v.cluster)==null?void 0:xe.clusterMode)==="SINGLE_NODE"?"single-node":"multi-node";let Me;if((el=v.execution)!=null&&el.imageId)try{const De=await Ke.fetchQuery(u,vt,{id:v.execution.imageId},{fetchPolicy:"store-or-network"}).toPromise(),$e=(Qe=De==null?void 0:De.imageV2)==null?void 0:Qe.identity;Me=$e!=null&&$e.canonicalName?$e.architecture?`${$e.canonicalName}@${$e.architecture}`:$e.canonicalName:void 0}catch{Me=void 0}const Oe=(((We=v.execution)==null?void 0:We.environ)??[]).map(De=>({variable:De.key,value:De.value}));return{cluster_mode:Pe,cluster_size:((qe=v.cluster)==null?void 0:qe.clusterSize)??1,allocationPreset:"custom",resource:{cpu:ne?Number(ne.quantity):0,mem:((ze=Jl(String((se==null?void 0:se.quantity)??"0"),"g",2))==null?void 0:ze.value)??"0g",shmem:((Je=Jl((ke==null?void 0:ke.value)??Xl,"g",2))==null?void 0:Je.value)??Xl,...ge?{acceleratorType:ge.slotName,accelerator:ge.slotName==="cuda.shares"?parseFloat(String(ge.quantity)):parseInt(String(ge.quantity),10)}:{}},enabledAutomaticShmem:!ke,runtimeVariantId:v.runtimeVariantId??void 0,environ:Oe,...Me?{environments:{version:Me}}:{}}},oe=async v=>{if(v===C)return;if(C==="preset"&&v==="custom"){const se=D.getFieldsValue(),ge=se.revisionPresetId;let ke={};if(ge){const Pe=await ue(ge);Pe&&(ke=await ye(Pe))}se.modelFolderId&&(ke.modelFolderId=se.modelFolderId),B(Object.keys(ke).length>0?ke:null),_("custom");return}const J=A.getFieldsValue(),ne={};J.modelFolderId&&(ne.modelFolderId=J.modelFolderId),A.resetFields(),B(null),P(Object.keys(ne).length>0?ne:null),_("preset")},de=v=>{var Qe,We,qe,ze,Je,De,$e,tl,Ae,Ue,Le,ll,Ge,sl,nl,je,rl,fl,El,Ie,Ne,ol,al,ml,Ol;const J=v.resourceSlots??[],ne=J.find(Ve=>Ve.slotName==="cpu"),se=J.find(Ve=>Ve.slotName==="mem"),ge=J.find(Ve=>Ve.slotName!=="cpu"&&Ve.slotName!=="mem"),ke=(((We=(Qe=v.resourceConfig)==null?void 0:Qe.resourceOpts)==null?void 0:We.entries)??[]).find(Ve=>Ve.name==="shmem"),Pe=((ze=(qe=v.modelRuntimeConfig)==null?void 0:qe.runtimeVariant)==null?void 0:ze.name)??"",Me=Pe==="custom",Oe=(Je=v.modelRuntimeConfig)==null?void 0:Je.runtimeVariantId;Oe&&Pe&&I(Ve=>({...Ve,[Oe]:Pe}));const _e=(tl=($e=(De=v.modelDefinition)==null?void 0:De.models)==null?void 0:$e[0])==null?void 0:tl.service,He=(Le=(Ue=(Ae=v.modelDefinition)==null?void 0:Ae.models)==null?void 0:Ue[0])==null?void 0:Le.modelPath,xe=_e!=null&&_e.healthCheck&&_e.healthCheck.enable!==!1?_e.healthCheck:void 0,el=Me&&!!_e&&(((ll=_e.startCommand)==null?void 0:ll.length)??0)>0;if(ee.current=Ln((v.extraMounts??[]).filter(Ve=>!!Ve.mountDestination).map(Ve=>[Ve.vfolderId.replace(/-/g,""),Ve.mountDestination])),!Me&&Pe){const Ve=(Ge=v.modelRuntimeConfig)==null?void 0:Ge.runtimeVariantPresetValues;W(Ve&&Ve.length>0?Ve.map(Yl=>({presetId:Yl.presetId,value:Yl.value})):void 0)}A.setFieldsValue({cluster_mode:((sl=v.clusterConfig)==null?void 0:sl.mode)==="SINGLE_NODE"?"single-node":"multi-node",cluster_size:((nl=v.clusterConfig)==null?void 0:nl.size)??1,allocationPreset:"custom",resource:{cpu:ne?Number(ne.quantity):0,mem:((je=Jl(String((se==null?void 0:se.quantity)??"0"),"g",2))==null?void 0:je.value)??"0g",shmem:((rl=Jl((ke==null?void 0:ke.value)??Xl,"g",2))==null?void 0:rl.value)??Xl,...ge?{acceleratorType:ge.slotName,accelerator:ge.slotName==="cuda.shares"?parseFloat(String(ge.quantity)):parseInt(String(ge.quantity),10)}:{}},enabledAutomaticShmem:!ke,mount_ids:(v.extraMounts??[]).map(Ve=>Ve.vfolderId.replace(/-/g,"")),mount_id_map:Ln((v.extraMounts??[]).filter(Ve=>!!Ve.mountDestination).map(Ve=>[Ve.vfolderId.replace(/-/g,""),Ve.mountDestination])),runtimeVariantId:((fl=v.modelRuntimeConfig)==null?void 0:fl.runtimeVariantId)??void 0,modelFolderId:(El=v.modelMountConfig)!=null&&El.vfolderId?Ql("VirtualFolderNode",v.modelMountConfig.vfolderId):void 0,mountDestination:((Ie=v.modelMountConfig)==null?void 0:Ie.mountDestination)??"/models",definitionPath:((Ne=v.modelMountConfig)==null?void 0:Ne.definitionPath)??void 0,environments:(al=(ol=v.imageV2)==null?void 0:ol.identity)!=null&&al.canonicalName?{version:v.imageV2.identity.architecture?`${v.imageV2.identity.canonicalName}@${v.imageV2.identity.architecture}`:v.imageV2.identity.canonicalName}:void 0,environ:(((Ol=(ml=v.modelRuntimeConfig)==null?void 0:ml.environ)==null?void 0:Ol.entries)??[]).map(Ve=>({variable:Ve.name,value:Ve.value})),commandEnableHealthCheck:!!xe,commandHealthCheck:(xe==null?void 0:xe.path)??void 0,commandInitialDelay:(xe==null?void 0:xe.initialDelay)??void 0,commandMaxRetries:(xe==null?void 0:xe.maxRetries)??void 0,commandInterval:(xe==null?void 0:xe.interval)??void 0,commandMaxWaitTime:(xe==null?void 0:xe.maxWaitTime)??void 0,commandExpectedStatusCode:(xe==null?void 0:xe.expectedStatusCode)??void 0,...el&&_e?{customDefinitionMode:"command",startCommand:Ha(_e.startCommand??[]),commandPort:_e.port,commandModelMount:He??"/models"}:Me?{customDefinitionMode:"file"}:{}})},me=V.useEffectEvent(()=>{O&&(A.setFieldsValue(O),B(null))}),re=V.useEffectEvent(()=>{k&&(D.setFieldsValue(k),P(null))}),fe=V.useEffectEvent(()=>{E||f&&(de(f),z(!0))}),Fe=V.useEffectEvent(()=>{U&&c&&(de(c),G(!1),Q(!0),s.success(a("deployment.CurrentRevisionConfigurationLoaded")))});V.useEffect(()=>{C==="custom"?(me(),fe(),Fe()):re()},[C]);const be=()=>{if(c){if(C==="custom"){de(c),Q(!0),s.success(a("deployment.CurrentRevisionConfigurationLoaded"));return}G(!0),_("custom")}},ve=v=>{const J=j.current;if(!J||!v)return[];const ne={};for(const[se,ge]of Object.entries(v))ge==null||ge===""||(ne[se]=String(ge));return za(J,ne,T.current)},he=v=>{var $e,tl;const J=()=>{A.setFields([{name:["environments","version"],errors:[a("modelService.ImageRequired")]}]),A.scrollToField(["environments","version"],{behavior:"smooth",block:"center"})},ne=(tl=($e=v.environments)==null?void 0:$e.image)==null?void 0:tl.id;if(!ne){J();return}const se=jl(ne);if(!se){J();return}const ge=[{resourceType:"cpu",quantity:String(v.resource.cpu)},{resourceType:"mem",quantity:v.resource.mem}];v.resource.acceleratorType&&v.resource.accelerator&&v.resource.accelerator>0&&ge.push({resourceType:v.resource.acceleratorType,quantity:String(v.resource.accelerator)});const ke=[];v.resource.shmem&&ke.push({name:"shmem",value:v.resource.shmem});const Pe=v.cluster_mode==="single-node"||v.cluster_mode==="multi-node"&&v.cluster_size===1?"SINGLE_NODE":"MULTI_NODE",Me=v.vfoldersNameMap??{},Oe=(v.mount_ids??[]).map(Ae=>{var Le;const Ue=((Le=v.mount_id_map)==null?void 0:Le[Ae])||ee.current[Ae]||(Me[Ae]?`/home/work/${Me[Ae]}`:`/home/work/${Ae}`);return{vfolderId:qn(Ae),mountDestination:Ue}}),He=(Z[v.runtimeVariantId]??"")==="custom",xe=v.customDefinitionMode==="command",el={};for(const{variable:Ae,value:Ue}of v.environ??[])Ae&&(el[Ae]=Ue);const Qe=Object.entries(el).map(([Ae,Ue])=>({name:Ae,value:Ue})),We=!!v.commandEnableHealthCheck,qe=(()=>{const Ae={path:v.commandHealthCheck,interval:v.commandInterval,maxRetries:v.commandMaxRetries,maxWaitTime:v.commandMaxWaitTime,initialDelay:v.commandInitialDelay,expectedStatusCode:v.commandExpectedStatusCode};return h?We?{enable:!0,...Ae}:{enable:!1}:We?Ae:null})(),ze=He||!F?[]:ve(v.runtimeParams),Je=He&&xe&&v.startCommand?{models:[{name:"model",modelPath:v.commandModelMount??"/models",service:{preStartActions:[],startCommand:Qa(v.startCommand??""),port:v.commandPort??8e3,healthCheck:qe}}]}:We?{models:[{service:{healthCheck:qe}}]}:null,De=He&&xe?v.commandModelMount??"/models":v.mountDestination||"/models";ce({variables:{input:{deploymentId:Ye((o==null?void 0:o.id)??"")??(o==null?void 0:o.id)??"",clusterConfig:{mode:Pe,size:v.cluster_size},resourceConfig:{resourceSlots:{entries:ge},resourceOpts:ke.length>0?{entries:ke}:null},image:{id:se},modelRuntimeConfig:{runtimeVariantId:v.runtimeVariantId,environ:Qe.length>0?{entries:Qe}:null,...F&&{runtimeVariantPresetValues:ze.length>0?ze:null}},modelMountConfig:{vfolderId:Ye(v.modelFolderId),mountDestination:De,definitionPath:v.definitionPath},modelDefinition:Je,extraMounts:Oe.length>0?Oe:null,options:{autoActivate:$}}},onCompleted:(Ae,Ue)=>{var Le,ll;if(Ue&&Ue.length>0){const Ge=Ue[0],sl=(Le=Ge==null?void 0:Ge.message)==null?void 0:Le.includes("Another deployment is already in progress");s.error(sl?a("deployment.AnotherDeploymentInProgress"):(Ge==null?void 0:Ge.message)??a("general.ErrorOccurred"));return}A.resetFields(),s.success(a("deployment.RevisionAdded")),l(!0,(ll=Ae.addModelRevision)==null?void 0:ll.revision)},onError:Ae=>{var Le;const Ue=(Le=Ae.message)==null?void 0:Le.includes("Another deployment is already in progress");s.error(Ue?a("deployment.AnotherDeploymentInProgress"):Ae.message??a("general.ErrorOccurred"))}})},ae=v=>{ce({variables:{input:{deploymentId:Ye((o==null?void 0:o.id)??"")??(o==null?void 0:o.id)??"",revisionPresetId:v.revisionPresetId,modelMountConfig:{vfolderId:Ye(v.modelFolderId),mountDestination:"/models"},options:{autoActivate:$}}},onCompleted:(J,ne)=>{var se,ge;if(ne&&ne.length>0){const ke=ne[0],Pe=(se=ke==null?void 0:ke.message)==null?void 0:se.includes("Another deployment is already in progress");y.error("[DeploymentAddRevisionModal] addModelRevision (preset) returned errors",ne),s.error(Pe?a("deployment.AnotherDeploymentInProgress"):(ke==null?void 0:ke.message)??a("general.ErrorOccurred"));return}D.resetFields(),s.success(a("deployment.RevisionAdded")),l(!0,(ge=J.addModelRevision)==null?void 0:ge.revision)},onError:J=>{var se;const ne=(se=J.message)==null?void 0:se.includes("Another deployment is already in progress");y.error("[DeploymentAddRevisionModal] addModelRevision (preset) failed",J),s.error(ne?a("deployment.AnotherDeploymentInProgress"):J.message??a("general.ErrorOccurred"))}})},Se=()=>{requestAnimationFrame(()=>{const v=document.querySelector(".ant-modal-body .ant-form-item-has-error");v&&v.scrollIntoView({behavior:"smooth",block:"start"})})},Ee=async()=>{const v=C==="preset"?D:A;try{await v.validateFields()}catch{Se();return}v.submit()};return n.jsxs(_l,{open:r,title:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"md",wrap:"wrap",style:{paddingRight:d.paddingLG},children:[n.jsx("span",{children:a("deployment.AddRevision")}),n.jsx(An,{value:C,onChange:oe,options:[{label:a("deployment.PresetMode"),value:"preset"},{label:a("deployment.CustomMode"),value:"custom"}],style:{fontWeight:"normal"}})]}),width:720,footer:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"sm",children:[n.jsx(Mn,{checked:$,onChange:v=>q(v.target.checked),disabled:C==="preset"&&X,children:a("deployment.AutoApply")}),n.jsxs(ie,{direction:"row",align:"center",gap:"xs",children:[n.jsx(ul,{onClick:()=>l(),children:a("button.Cancel")}),n.jsx(ul,{type:"primary",loading:Re,onClick:Ee,disabled:C==="preset"&&X,children:a("deployment.AddRevision")})]})]}),onCancel:()=>l(),confirmLoading:Re,destroyOnHidden:!0,...t,children:[c&&!i&&!M?n.jsx(bl,{type:"info",showIcon:!0,style:{marginBottom:d.marginMD},title:a("deployment.CurrentRevisionAvailableDescription"),action:n.jsx(ul,{size:"small",onClick:be,children:a("deployment.LoadCurrentRevision")})}):null,C==="preset"?X?n.jsx(bl,{type:"info",showIcon:!0,style:{marginTop:d.marginXS},title:a("deployment.NoPresetsAvailable"),description:a("deployment.NoPresetsAvailableSwitchToCustom")}):n.jsxs(pe,{form:D,layout:"vertical",style:{marginTop:d.marginXS},onFinish:ae,onFinishFailed:Se,initialValues:{modelFolderId:w},children:[n.jsx(pe.Item,{label:a("modelStore.Preset"),tooltip:a("modelStore.PresetTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(V.Suspense,{fallback:n.jsx(Hl,{loading:!0,style:{flex:1}}),children:n.jsx(pe.Item,{name:"revisionPresetId",noStyle:!0,rules:[{required:!0}],children:n.jsx(oa,{style:{flex:1}})})}),n.jsx(pe.Item,{dependencies:["revisionPresetId"],noStyle:!0,children:({getFieldValue:v})=>{const J=v("revisionPresetId");return n.jsx(ql.Compact,{children:n.jsx(dl,{title:a("modelService.DeploymentPresetDetail"),children:n.jsx(ul,{icon:n.jsx(da,{}),disabled:!J,onClick:()=>{J&&Y(J)}})})})}})]})}),n.jsx(pe.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(V.Suspense,{fallback:n.jsx(Hl,{loading:!0,style:{flex:1}}),children:n.jsx(pe.Item,{name:"modelFolderId",label:a("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(Vn,{ref:b,currentProjectId:g??void 0,disabled:!g,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(pe.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:v})=>{const J=v("modelFolderId");return n.jsxs(ql.Compact,{children:[n.jsx(dl,{title:a("modelService.OpenFolder"),children:n.jsx(ul,{icon:n.jsx(En,{}),disabled:!J,onClick:()=>{J&&S(Ye(J))}})}),n.jsx(dl,{title:a("data.CreateANewStorageFolder"),children:n.jsx(ul,{icon:n.jsx(Il,{}),onClick:()=>R(!0)})}),n.jsx(dl,{title:a("button.Refresh"),children:n.jsx(ul,{icon:n.jsx(Cn,{}),onClick:()=>{V.startTransition(()=>{var ne;(ne=b.current)==null||ne.refetch()})}})})]})}})]})})]},"preset-form"):n.jsxs(pe,{form:A,layout:"vertical",style:{marginTop:d.marginXS},onFinish:he,onFinishFailed:Se,initialValues:ya({},fa,{resourceGroup:(we=o==null?void 0:o.metadata)==null?void 0:we.resourceGroupName,customDefinitionMode:"command",commandEnableHealthCheck:!1,environ:[]}),children:[n.jsx(rn,{children:a("deployment.step.ModelAndRuntime")}),n.jsx(pe.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(V.Suspense,{fallback:n.jsx(Hl,{loading:!0,style:{flex:1}}),children:n.jsx(pe.Item,{name:"modelFolderId",label:a("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(Vn,{ref:x,currentProjectId:g??void 0,disabled:!g,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(pe.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:v})=>{const J=v("modelFolderId");return n.jsxs(ql.Compact,{children:[n.jsx(dl,{title:a("modelService.OpenFolder"),children:n.jsx(ul,{icon:n.jsx(En,{}),disabled:!J,onClick:()=>{J&&S(Ye(J))}})}),n.jsx(dl,{title:a("data.CreateANewStorageFolder"),children:n.jsx(ul,{icon:n.jsx(Il,{}),onClick:()=>R(!0)})}),n.jsx(dl,{title:a("button.Refresh"),children:n.jsx(ul,{icon:n.jsx(Cn,{}),onClick:()=>{V.startTransition(()=>{var ne;(ne=x.current)==null||ne.refetch()})}})})]})}})]})}),n.jsx(V.Suspense,{fallback:n.jsx(Hl,{loading:!0,style:{width:"100%"}}),children:n.jsx(pe.Item,{name:"runtimeVariantId",label:a("deployment.RuntimeVariant"),tooltip:a("deployment.RuntimeVariantTooltip"),rules:[{required:!0},{warningOnly:!0,validator:async(v,J)=>{const ne=Z[J];return ne&&ne!=="custom"?Promise.reject(a("modelService.RuntimeVariantDefaultCommandAppliedNote")):Promise.resolve()}}],children:n.jsx(ai,{onResolvedNamesChange:v=>I(J=>({...J,...v}))})})}),n.jsx(pe.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:v})=>{const J=v("runtimeVariantId"),ne=Z[J];return!ne||ne==="custom"?null:n.jsx("div",{style:{marginBottom:d.marginMD},children:n.jsx(V.Suspense,{fallback:null,children:n.jsx(qa,{runtimeVariant:ne,onTouchedKeysChange:se=>{T.current=se},onGroupsLoaded:se=>{j.current=se},initialPresetValues:H})})})}}),n.jsx(pe.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:v})=>{const J=v("runtimeVariantId");return Z[J]!=="custom"?null:n.jsxs(n.Fragment,{children:[n.jsx(pe.Item,{name:"customDefinitionMode",noStyle:!0,children:n.jsx(An,{options:[{label:a("modelService.EnterCommand"),value:"command"},{label:a("modelService.UseConfigFile"),value:"file"}],style:{marginBottom:d.marginMD}})}),n.jsx(pe.Item,{dependencies:["customDefinitionMode"],noStyle:!0,children:({getFieldValue:se})=>se("customDefinitionMode")==="command"?n.jsxs(n.Fragment,{children:[n.jsx(pe.Item,{name:"startCommand",label:a("modelService.StartCommand"),tooltip:a("modelService.StartCommandTooltip"),extra:a("modelService.StartCommandHelperShell"),rules:[{required:!0,whitespace:!0}],children:n.jsx(wl.TextArea,{placeholder:a("modelService.StartCommandPlaceholder"),autoSize:{minRows:2}})}),n.jsx(pe.Item,{name:"commandModelMount",label:a("modelService.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),children:n.jsx(wl,{placeholder:"/models",allowClear:!0})}),n.jsx(pe.Item,{name:"commandPort",label:a("modelService.Port"),tooltip:a("modelService.PortTooltip"),children:n.jsx(cl,{min:2,max:65535,placeholder:"8000",style:{width:"100%"}})})]}):n.jsxs(ie,{gap:"sm",children:[n.jsx(pe.Item,{name:"mountDestination",label:a("deployment.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),rules:[{required:!0}],style:{flex:1},children:n.jsx(wl,{allowClear:!0,placeholder:"/models"})}),n.jsx(pe.Item,{name:"definitionPath",label:a("deployment.ModelDefinitionPath"),tooltip:a("modelService.ModelDefinitionPathTooltip"),style:{flex:1},children:n.jsx(wl,{allowClear:!0,placeholder:"model-definition.yaml"})})]})})]})}}),n.jsx(pe.Item,{name:"commandEnableHealthCheck",valuePropName:"checked",style:{marginBottom:d.marginXS},children:n.jsx(Mn,{children:a("modelService.EnableHealthCheck")})}),n.jsx(pe.Item,{dependencies:["commandEnableHealthCheck"],noStyle:!0,children:({getFieldValue:v})=>v("commandEnableHealthCheck")?n.jsxs(ie,{direction:"column",align:"stretch",gap:"xs",children:[n.jsx(pe.Item,{name:"commandHealthCheck",label:a("adminDeploymentPreset.modelDef.HealthCheckPath"),tooltip:a("modelService.HealthCheckTooltip"),rules:[{required:!0}],children:n.jsx(wl,{placeholder:a("general.Example",{value:"/health"}),allowClear:!0})}),n.jsxs(ie,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(pe.Item,{name:"commandInterval",label:a("adminDeploymentPreset.modelDef.HealthCheckInterval"),tooltip:a("modelService.IntervalTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(cl,{min:1,placeholder:a("general.Example",{value:"10"}),suffix:a("time.Sec"),style:{width:"100%"}})}),n.jsx(pe.Item,{name:"commandMaxRetries",label:a("adminDeploymentPreset.modelDef.HealthCheckMaxRetries"),tooltip:a("modelService.MaxRetriesTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(cl,{min:1,placeholder:a("general.Example",{value:"10"}),style:{width:"100%"}})}),n.jsx(pe.Item,{name:"commandMaxWaitTime",label:a("adminDeploymentPreset.modelDef.HealthCheckMaxWaitTime"),tooltip:a("modelService.MaxWaitTimeTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(cl,{min:1,placeholder:a("general.Example",{value:"15"}),suffix:a("time.Sec"),style:{width:"100%"}})})]}),n.jsxs(ie,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(pe.Item,{name:"commandExpectedStatusCode",label:a("adminDeploymentPreset.modelDef.HealthCheckExpectedStatus"),tooltip:a("modelService.ExpectedStatusTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(cl,{min:101,max:599,placeholder:a("general.Example",{value:"200"}),style:{width:"100%"}})}),n.jsx(pe.Item,{name:"commandInitialDelay",label:a("adminDeploymentPreset.modelDef.HealthCheckInitialDelay"),tooltip:a("modelService.InitialDelayTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(cl,{min:0,placeholder:a("general.Example",{value:"60"}),suffix:a("time.Sec"),style:{width:"100%"}})}),n.jsx("div",{style:{flex:1,minWidth:160}})]})]}):null}),n.jsx(rn,{children:a("session.launcher.Environments")}),n.jsx(V.Suspense,{fallback:n.jsx(Sl,{active:!0,paragraph:{rows:2}}),children:n.jsx(ua,{})}),n.jsx(ca,{name:"environ",formItemProps:{validateTrigger:["onChange","onBlur"]}}),n.jsx(rn,{children:a("deployment.step.ClusterAndResources")}),n.jsx(V.Suspense,{fallback:n.jsx(Sl,{active:!0,paragraph:{rows:4}}),children:n.jsx(ma,{enableResourcePresets:!0,hideResourceGroupFormItem:!0})}),n.jsx(ga,{items:[{key:"advanced",label:a("session.launcher.AdvancedSettings"),children:n.jsx(V.Suspense,{fallback:n.jsx(Sl,{active:!0}),children:n.jsx(pe.Item,{noStyle:!0,dependencies:["modelFolderId","mount_id_map","mount_ids"],children:({getFieldValue:v})=>{var se;const J=v("modelFolderId"),ne=J?(se=jl(String(J)))==null?void 0:se.replace(/-/g,""):void 0;return n.jsx(pa,{label:a("modelService.AdditionalMounts"),tooltip:a("modelService.AdditionalMountsTooltip"),rowKey:"id",tableProps:{scroll:{x:"max-content",y:300}},rowFilter:ge=>{var ke;return ge.usage_mode!=="model"&&ge.status==="ready"&&!((ke=ge.name)!=null&&ke.startsWith("."))&&ge.id!==ne}})}})})}]})]},"custom-form"),N&&n.jsx(V.Suspense,{fallback:null,children:n.jsx(Li,{presetId:N,onCancel:()=>Y(null)})}),n.jsx(ka,{open:K,initialValues:{usage_mode:"model"},onRequestClose:v=>{if(R(!1),v!=null&&v.id){const J=jl(v.id);if(!J)return;const ne=Ql("VirtualFolderNode",J),se=C==="preset"?D:A,ge=C==="preset"?b:x;se.setFieldValue("modelFolderId",ne),V.startTransition(()=>{var ke;(ke=ge.current)==null||ke.refetch()})}}})]})},It=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAutoScalingRulePayload",kind:"LinkedField",name:"deleteAutoScalingRule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAutoScalingCardDeleteMutation",selections:e},params:{cacheID:"1b7b8f1adf6afd81d338607d63841181",id:null,metadata:{},name:"DeploymentAutoScalingCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAutoScalingCardDeleteMutation(
  $input: DeleteAutoScalingRuleInput!
) {
  deleteAutoScalingRule(input: $input) {
    id
  }
}
`}}}();It.hash="051eb6f0b4919363bd328fca5366d60b";const Ct=function(){var l=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardPresetsQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAutoScalingCardPresetsQuery",selections:l},params:{cacheID:"cc679b7f385bc973b5b68d9964531688",id:null,metadata:{},name:"DeploymentAutoScalingCardPresetsQuery",operationKind:"query",text:`query DeploymentAutoScalingCardPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();Ct.hash="6d5f2bbfca84b48a6aa4d1e118d88fdb";const At=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[s,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,{args:null,kind:"FragmentSpread",name:"AutoScalingRuleListNodesFragment"},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,r,i,t,e],kind:"Operation",name:"DeploymentAutoScalingCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[s,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},u],storageKey:null}]},params:{cacheID:"41c9b35cb41550bd8f8cde32c8b21c1a",id:null,metadata:{},name:"DeploymentAutoScalingCardListQuery",operationKind:"query",text:`query DeploymentAutoScalingCardListQuery(
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
`}}}();At.hash="56b6637e50dbda972f85edac73bc04b5";const Mt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Mt.hash="a7ebc88f8233e21188ec26bb29ecdb73";const Lt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"UpdateAutoScalingRulePayload",kind:"LinkedField",name:"updateAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalUpdateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalUpdateMutation",selections:e},params:{cacheID:"f5194bd994f4693e29536fec36e4f0e4",id:null,metadata:{},name:"AutoScalingRuleEditorModalUpdateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalUpdateMutation(
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
`}}}();Lt.hash="8e953443e1aa963b955810e5f97de017";const jt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAutoScalingRulePayload",kind:"LinkedField",name:"createAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalCreateMutation",selections:e},params:{cacheID:"c7c250dabfc49b66cf1aebbff6414d44",id:null,metadata:{},name:"AutoScalingRuleEditorModalCreateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalCreateMutation(
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
`}}}();jt.hash="7afa475334295923b7754d0563a8b919";const Nt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],type:"AutoScalingRule",abstractKey:null};Nt.hash="9dff1f6ce3b17626029eee3484220a7d";const Pt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[l,e,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"categoryId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queryTemplate",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,concreteType:"QueryPresetCategory",kind:"LinkedField",name:"category",plural:!1,selections:[l,e],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalPresetsQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleEditorModalPresetsQuery",selections:i},params:{cacheID:"04d06fec5284e709aaee3606d8a4bb53",id:null,metadata:{},name:"AutoScalingRuleEditorModalPresetsQuery",operationKind:"query",text:`query AutoScalingRuleEditorModalPresetsQuery {
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
`}}}();Pt.hash="6582d4cf067148f5b39755e919c0f4f2";const on={KERNEL:["cpu_util","mem","net_rx","net_tx"],INFERENCE_FRAMEWORK:[]},On=l=>l?l.minThreshold!=null&&l.maxThreshold!=null?"scale_in_out":l.maxThreshold!=null?"scale_out":"scale_in":"scale_out",ji=l=>{"use memo";var El;const e=Be.c(196),{autoScalingRule:i,formRef:r}=l,{t}=Ze(),{token:a}=Kl.useToken(),d=Rn(),s=va();let u;e[0]!==d?(u=d.supports("prometheus-auto-scaling-rule"),e[0]=d,e[1]=u):u=e[1];const o=u;let m,c;e[2]===Symbol.for("react.memo_cache_sentinel")?(m=Pt,c={},e[2]=m,e[3]=c):(m=e[2],c=e[3]);const{prometheusQueryPresets:f}=Ke.useLazyLoadQuery(m,c);let g;e[4]!==(f==null?void 0:f.edges)?(g=Fa(hl(f==null?void 0:f.edges,Pi)),e[4]=f==null?void 0:f.edges,e[5]=g):g=e[5];const y=g;let S;e[6]!==i?(S=On(i),e[6]=i,e[7]=S):S=e[7];const[p,h]=V.useState(S),[F,b]=V.useState((i==null?void 0:i.metricSource)||"KERNEL");let x;e[8]!==i||e[9]!==y?(x=i!=null&&i.prometheusQueryPresetId?(El=y.find(Ie=>Ye(Ie.id)===i.prometheusQueryPresetId))==null?void 0:El.id:void 0,e[8]=i,e[9]=y,e[10]=x):x=e[10];const[K,R]=V.useState(x);let A;e[11]!==(i==null?void 0:i.metricSource)?(A=on[(i==null?void 0:i.metricSource)||"KERNEL"]||[],e[11]=i==null?void 0:i.metricSource,e[12]=A):A=e[12];const[D,$]=V.useState(A);let q;if(e[13]!==y||e[14]!==K){let Ie;e[16]!==K?(Ie=Ne=>Ne.id===K,e[16]=K,e[17]=Ie):Ie=e[17],q=y.find(Ie),e[13]=y,e[14]=K,e[15]=q}else q=e[15];const L=q;let _;if(e[18]!==y){const Ie=Wa(y,["rank"],["asc"]),Ne=Ie.filter(Vi),ol=Ie.filter(_i),al=Ei,ml=xa(Ne,Oi),Ol=Object.entries(ml).map(Ve=>{const[Yl,Xt]=Ve;return{label:Yl,options:Xt.map(al)}});_=ol.length>0?[...Ol,...ol.map(al)]:Ol,e[18]=y,e[19]=_}else _=e[19];const C=_;let M;e[20]!==i||e[21]!==K?(M=()=>{if(i){const Ie=On(i);let Ne;return Ie==="scale_in"&&i.minThreshold!=null?Ne=Number(i.minThreshold):Ie==="scale_out"&&i.maxThreshold!=null&&(Ne=Number(i.maxThreshold)),{metricSource:i.metricSource,metricName:i.metricName,prometheusQueryPresetId:K,conditionMode:Ie,threshold:Ne,minThreshold:i.minThreshold!=null?Number(i.minThreshold):void 0,maxThreshold:i.maxThreshold!=null?Number(i.maxThreshold):void 0,stepSize:Math.abs(i.stepSize),timeWindow:i.timeWindow,minReplicas:i.minReplicas??void 0,maxReplicas:i.maxReplicas??void 0}}return{metricSource:"KERNEL",conditionMode:"scale_out",stepSize:1,timeWindow:300,minReplicas:0,maxReplicas:5}},e[20]=i,e[21]=K,e[22]=M):M=e[22];const Q=M,E=F==="PROMETHEUS";let z;e[23]!==Q?(z=Q(),e[23]=Q,e[24]=z):z=e[24];let U;e[25]!==t?(U=t("autoScalingRule.MetricSource"),e[25]=t,e[26]=U):U=e[26];let G;e[27]!==t?(G=t("autoScalingRule.MetricSourceTooltip"),e[27]=t,e[28]=G):G=e[28];let O;e[29]===Symbol.for("react.memo_cache_sentinel")?(O=[{required:!0}],e[29]=O):O=e[29];let B;e[30]!==r?(B=Ie=>{var Ne,ol;if(b(Ie),(Ne=r.current)==null||Ne.setFieldsValue({metricName:void 0}),Ie!=="PROMETHEUS")$(on[Ie]||[]),R(void 0);else{const al=(ol=r.current)==null?void 0:ol.getFieldValue("prometheusQueryPresetId");al&&R(al)}},e[30]=r,e[31]=B):B=e[31];let k;e[32]!==t?(k=t("autoScalingRule.MetricSourceKernel"),e[32]=t,e[33]=k):k=e[33];let P;e[34]!==k?(P={label:k,value:"KERNEL"},e[34]=k,e[35]=P):P=e[35];let N;e[36]!==o||e[37]!==t?(N=o?[]:[{label:t("autoScalingRule.MetricSourceInferenceFramework"),value:"INFERENCE_FRAMEWORK"}],e[36]=o,e[37]=t,e[38]=N):N=e[38];let Y;e[39]!==t?(Y=t("autoScalingRule.MetricSourcePrometheus"),e[39]=t,e[40]=Y):Y=e[40];let Z;e[41]!==Y?(Z={label:Y,value:"PROMETHEUS"},e[41]=Y,e[42]=Z):Z=e[42];let I;e[43]!==P||e[44]!==N||e[45]!==Z?(I=[P,...N,Z],e[43]=P,e[44]=N,e[45]=Z,e[46]=I):I=e[46];let T;e[47]!==B||e[48]!==I?(T=n.jsx(mn,{onChange:B,options:I}),e[47]=B,e[48]=I,e[49]=T):T=e[49];let j;e[50]!==U||e[51]!==G||e[52]!==T?(j=n.jsx(pe.Item,{label:U,name:"metricSource",tooltip:G,rules:O,children:T}),e[50]=U,e[51]=G,e[52]=T,e[53]=j):j=e[53];let H;e[54]!==t?(H=t("autoScalingRule.MetricName"),e[54]=t,e[55]=H):H=e[55];let W;e[56]!==t?(W=t("autoScalingRule.MetricNameTooltip"),e[56]=t,e[57]=W):W=e[57];const ee=!E;let X;e[58]!==ee?(X=[{required:ee}],e[58]=ee,e[59]=X):X=e[59];let le;e[60]!==t?(le=t("autoScalingRule.MetricName"),e[60]=t,e[61]=le):le=e[61];let w;e[62]!==D?(w=hl(D,$i),e[62]=D,e[63]=w):w=e[63];let te;e[64]!==r?(te={onSearch:Ie=>{var ol;const Ne=((ol=r.current)==null?void 0:ol.getFieldValue("metricSource"))||"KERNEL";$(Ra(on[Ne]||[],al=>al.includes(Ie)))}},e[64]=r,e[65]=te):te=e[65];let ue;e[66]!==le||e[67]!==w||e[68]!==te?(ue=n.jsx(Ka,{placeholder:le,options:w,showSearch:te,allowClear:!0,popupMatchSelectWidth:!1}),e[66]=le,e[67]=w,e[68]=te,e[69]=ue):ue=e[69];let ce;e[70]!==E||e[71]!==H||e[72]!==W||e[73]!==X||e[74]!==ue?(ce=n.jsx(pe.Item,{label:H,name:"metricName",hidden:E,tooltip:W,rules:X,children:ue}),e[70]=E,e[71]=H,e[72]=W,e[73]=X,e[74]=ue,e[75]=ce):ce=e[75];let Re;e[76]!==s||e[77]!==r||e[78]!==E||e[79]!==y||e[80]!==C||e[81]!==L||e[82]!==t||e[83]!==a.fontSizeSM?(Re=E&&n.jsx(n.Fragment,{children:n.jsx(pe.Item,{label:`${t("autoScalingRule.MetricName")} (${t("autoScalingRule.PrometheusPreset")})`,name:"prometheusQueryPresetId",tooltip:t("autoScalingRule.PrometheusPresetTooltip"),rules:[{required:!0,message:t("autoScalingRule.PrometheusPresetRequired")}],extra:s==="superadmin"&&L?n.jsx(Ua,{queryTemplate:L.queryTemplate},L.id):void 0,children:n.jsx(mn,{onChange:Ie=>{var ol,al;R(Ie);const Ne=y.find(ml=>ml.id===Ie);if(Ne){(ol=r.current)==null||ol.setFieldsValue({metricName:Ne.metricName});const ml=Ne.timeWindow!=null?Number(Ne.timeWindow):void 0;ml!=null&&!isNaN(ml)&&((al=r.current)==null||al.setFieldsValue({timeWindow:ml}))}},placeholder:t("autoScalingRule.SelectPrometheusPreset"),showSearch:{filterOption:wi},options:C,optionRender:Ie=>n.jsxs(ie,{direction:"column",align:"start",children:[Ie.label,Ie.data.description&&n.jsx(Xe.Text,{type:"secondary",style:{fontSize:a.fontSizeSM},ellipsis:!0,children:Ie.data.description})]}),allowClear:!0,onClear:()=>R(void 0)})})}),e[76]=s,e[77]=r,e[78]=E,e[79]=y,e[80]=C,e[81]=L,e[82]=t,e[83]=a.fontSizeSM,e[84]=Re):Re=e[84];let ye;e[85]!==t?(ye=t("autoScalingRule.Condition"),e[85]=t,e[86]=ye):ye=e[86];let oe;e[87]!==t?(oe=t("autoScalingRule.ConditionTooltip"),e[87]=t,e[88]=oe):oe=e[88];let de;e[89]===Symbol.for("react.memo_cache_sentinel")?(de=Ie=>{h(Ie.target.value)},e[89]=de):de=e[89];let me;e[90]!==a.marginSM?(me={marginBottom:a.marginSM},e[90]=a.marginSM,e[91]=me):me=e[91];let re;e[92]!==t?(re=t("autoScalingRule.ScaleIn"),e[92]=t,e[93]=re):re=e[93];let fe;e[94]!==re?(fe={label:re,value:"scale_in"},e[94]=re,e[95]=fe):fe=e[95];let Fe;e[96]!==t?(Fe=t("autoScalingRule.ScaleOut"),e[96]=t,e[97]=Fe):Fe=e[97];let be;e[98]!==Fe?(be={label:Fe,value:"scale_out"},e[98]=Fe,e[99]=be):be=e[99];let ve;e[100]!==t?(ve=t("autoScalingRule.ScaleInAndOut"),e[100]=t,e[101]=ve):ve=e[101];let he;e[102]!==ve?(he={label:ve,value:"scale_in_out"},e[102]=ve,e[103]=he):he=e[103];let ae;e[104]!==fe||e[105]!==be||e[106]!==he?(ae=[fe,be,he],e[104]=fe,e[105]=be,e[106]=he,e[107]=ae):ae=e[107];let Se;e[108]!==me||e[109]!==ae?(Se=n.jsx(pe.Item,{name:"conditionMode",noStyle:!0,children:n.jsx(ba.Group,{optionType:"button",onChange:de,style:me,options:ae})}),e[108]=me,e[109]=ae,e[110]=Se):Se=e[110];let Ee;e[111]!==p||e[112]!==t?(Ee=p==="scale_in"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(Xe.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(pe.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(cl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),e[111]=p,e[112]=t,e[113]=Ee):Ee=e[113];let Ce;e[114]!==p||e[115]!==t?(Ce=p==="scale_out"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(pe.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(cl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(Xe.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]}),e[114]=p,e[115]=t,e[116]=Ce):Ce=e[116];let Te;e[117]!==p||e[118]!==t?(Te=p==="scale_in_out"&&n.jsxs(ie,{direction:"column",gap:"xs",align:"stretch",children:[n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(Xe.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(pe.Item,{name:"minThreshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.MinThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(cl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(pe.Item,{name:"maxThreshold",noStyle:!0,dependencies:["minThreshold"],rules:[{required:!0,message:t("autoScalingRule.MaxThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")},Ie=>{const{getFieldValue:Ne}=Ie;return{validator(ol,al){const ml=Ne("minThreshold");return ml!=null&&al!=null&&ml>=al?Promise.reject(new Error(t("autoScalingRule.MinMustBeLessThanMax"))):Promise.resolve()}}}],children:n.jsx(cl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(Xe.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]})]}),e[117]=p,e[118]=t,e[119]=Te):Te=e[119];let we;e[120]!==ye||e[121]!==oe||e[122]!==Se||e[123]!==Ee||e[124]!==Ce||e[125]!==Te?(we=n.jsxs(pe.Item,{label:ye,required:!0,tooltip:oe,children:[Se,Ee,Ce,Te]}),e[120]=ye,e[121]=oe,e[122]=Se,e[123]=Ee,e[124]=Ce,e[125]=Te,e[126]=we):we=e[126];let v;e[127]!==t?(v=t("autoScalingRule.StepSize"),e[127]=t,e[128]=v):v=e[128];let J;e[129]!==t?(J=t("autoScalingRule.StepSizeTooltip"),e[129]=t,e[130]=J):J=e[130];let ne,se;e[131]===Symbol.for("react.memo_cache_sentinel")?(ne={required:!0},se={type:"number",min:1,max:Bl},e[131]=ne,e[132]=se):(ne=e[131],se=e[132]);let ge;e[133]!==t?(ge=[ne,se,{validator:(Ie,Ne)=>Ne%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[133]=t,e[134]=ge):ge=e[134];let ke;e[135]===Symbol.for("react.memo_cache_sentinel")?(ke={width:"100%"},e[135]=ke):ke=e[135];const Pe=p==="scale_in_out"?"±":p==="scale_out"?"+":"−";let Me;e[136]!==Pe?(Me=n.jsx(cl,{min:1,step:1,style:ke,prefix:n.jsx(Xe.Text,{type:"secondary",children:Pe})}),e[136]=Pe,e[137]=Me):Me=e[137];let Oe;e[138]!==v||e[139]!==J||e[140]!==ge||e[141]!==Me?(Oe=n.jsx(pe.Item,{label:v,name:"stepSize",tooltip:J,rules:ge,children:Me}),e[138]=v,e[139]=J,e[140]=ge,e[141]=Me,e[142]=Oe):Oe=e[142];let _e;e[143]!==t?(_e=t("autoScalingRule.CoolDownSeconds"),e[143]=t,e[144]=_e):_e=e[144];let He;e[145]!==t?(He=t("autoScalingRule.CoolDownTooltip"),e[145]=t,e[146]=He):He=e[146];let xe,el;e[147]===Symbol.for("react.memo_cache_sentinel")?(xe={required:!0},el={type:"number",min:1},e[147]=xe,e[148]=el):(xe=e[147],el=e[148]);let Qe;e[149]!==t?(Qe=[xe,el,{validator:(Ie,Ne)=>Ne%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[149]=t,e[150]=Qe):Qe=e[150];let We;e[151]===Symbol.for("react.memo_cache_sentinel")?(We={width:"100%"},e[151]=We):We=e[151];let qe;e[152]!==t?(qe=t("autoScalingRule.Seconds"),e[152]=t,e[153]=qe):qe=e[153];let ze;e[154]!==qe?(ze=n.jsx(cl,{min:1,step:1,style:We,suffix:n.jsx(Xe.Text,{type:"secondary",children:qe})}),e[154]=qe,e[155]=ze):ze=e[155];let Je;e[156]!==_e||e[157]!==He||e[158]!==Qe||e[159]!==ze?(Je=n.jsx(pe.Item,{label:_e,name:"timeWindow",tooltip:He,rules:Qe,children:ze}),e[156]=_e,e[157]=He,e[158]=Qe,e[159]=ze,e[160]=Je):Je=e[160];let De;e[161]!==t?(De=t("autoScalingRule.MinReplicas"),e[161]=t,e[162]=De):De=e[162];let $e;e[163]!==t?($e=t("autoScalingRule.MinReplicasTooltip"),e[163]=t,e[164]=$e):$e=e[164];let tl;e[165]===Symbol.for("react.memo_cache_sentinel")?(tl={min:0,max:Bl,type:"number"},e[165]=tl):tl=e[165];let Ae;e[166]!==t?(Ae=[tl,{validator:(Ie,Ne)=>Ne!=null&&Ne%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[166]=t,e[167]=Ae):Ae=e[167];let Ue;e[168]===Symbol.for("react.memo_cache_sentinel")?(Ue=n.jsx(cl,{min:0,max:Bl,style:{width:"100%"}}),e[168]=Ue):Ue=e[168];let Le;e[169]!==De||e[170]!==$e||e[171]!==Ae?(Le=n.jsx(pe.Item,{label:De,name:"minReplicas",tooltip:$e,rules:Ae,children:Ue}),e[169]=De,e[170]=$e,e[171]=Ae,e[172]=Le):Le=e[172];let ll;e[173]!==t?(ll=t("autoScalingRule.MaxReplicas"),e[173]=t,e[174]=ll):ll=e[174];let Ge;e[175]!==t?(Ge=t("autoScalingRule.MaxReplicasTooltip"),e[175]=t,e[176]=Ge):Ge=e[176];let sl;e[177]===Symbol.for("react.memo_cache_sentinel")?(sl={min:0,max:Bl,type:"number"},e[177]=sl):sl=e[177];let nl;e[178]!==t?(nl=[sl,{validator:(Ie,Ne)=>Ne!=null&&Ne%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[178]=t,e[179]=nl):nl=e[179];let je;e[180]===Symbol.for("react.memo_cache_sentinel")?(je=n.jsx(cl,{min:0,max:Bl,style:{width:"100%"}}),e[180]=je):je=e[180];let rl;e[181]!==ll||e[182]!==Ge||e[183]!==nl?(rl=n.jsx(pe.Item,{label:ll,name:"maxReplicas",tooltip:Ge,rules:nl,children:je}),e[181]=ll,e[182]=Ge,e[183]=nl,e[184]=rl):rl=e[184];let fl;return e[185]!==r||e[186]!==z||e[187]!==j||e[188]!==ce||e[189]!==Re||e[190]!==we||e[191]!==Oe||e[192]!==Je||e[193]!==Le||e[194]!==rl?(fl=n.jsxs(pe,{ref:r,layout:"vertical",initialValues:z,children:[j,ce,Re,we,Oe,Je,Le,rl]}),e[185]=r,e[186]=z,e[187]=j,e[188]=ce,e[189]=Re,e[190]=we,e[191]=Oe,e[192]=Je,e[193]=Le,e[194]=rl,e[195]=fl):fl=e[195],fl},Ni=l=>{"use memo";const e=Be.c(34);let i,r,t,a,d;e[0]!==l?({onRequestClose:d,onComplete:a,modelDeploymentId:t,autoScalingRuleFrgmt:i,...r}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=Ze(),{message:u}=Al.useApp(),{logger:o}=Vl();let m;e[6]===Symbol.for("react.memo_cache_sentinel")?(m=Nt,e[6]=m):m=e[6];const c=Ke.useFragment(m,i??null),f=V.useRef(null);let g;e[7]===Symbol.for("react.memo_cache_sentinel")?(g=jt,e[7]=g):g=e[7];const[y,S]=Ke.useMutation(g);let p;e[8]===Symbol.for("react.memo_cache_sentinel")?(p=Lt,e[8]=p):p=e[8];const[h,F]=Ke.useMutation(p);let b;e[9]!==c||e[10]!==y||e[11]!==h||e[12]!==o||e[13]!==u||e[14]!==t||e[15]!==a||e[16]!==d||e[17]!==s?(b=()=>{var C;return(C=f.current)==null?void 0:C.validateFields().then(M=>{let Q=null,E=null;M.conditionMode==="scale_in_out"?(Q=M.minThreshold??null,E=M.maxThreshold??null):M.conditionMode==="scale_in"?Q=M.threshold??null:E=M.threshold??null;const z=M.metricName,U=M.metricSource==="PROMETHEUS"&&M.prometheusQueryPresetId?Ye(M.prometheusQueryPresetId):null;c?h({variables:{input:{id:Ye(c.id),metricSource:M.metricSource,metricName:z,minThreshold:Q!=null?String(Q):null,maxThreshold:E!=null?String(E):null,stepSize:M.stepSize,timeWindow:M.timeWindow,minReplicas:M.minReplicas,maxReplicas:M.maxReplicas,prometheusQueryPresetId:U??void 0}},onCompleted:(G,O)=>{if(O&&O.length>0){const B=hl(O,Bi);for(const k of B)u.error(k);return}u.success(s("autoScalingRule.SuccessfullyUpdated")),a==null||a(),d(!0)},onError:G=>{u.error(G.message)}}):y({variables:{input:{modelDeploymentId:t,metricSource:M.metricSource,metricName:z,minThreshold:Q!=null?String(Q):null,maxThreshold:E!=null?String(E):null,stepSize:M.stepSize,timeWindow:M.timeWindow,minReplicas:M.minReplicas,maxReplicas:M.maxReplicas,prometheusQueryPresetId:U??void 0}},onCompleted:(G,O)=>{if(O&&O.length>0){const B=hl(O,Hi);for(const k of B)u.error(k);return}u.success(s("autoScalingRule.SuccessfullyCreated")),a==null||a(),d(!0)},onError:G=>{u.error(G.message)}})}).catch(M=>{o.error(M)})},e[9]=c,e[10]=y,e[11]=h,e[12]=o,e[13]=u,e[14]=t,e[15]=a,e[16]=d,e[17]=s,e[18]=b):b=e[18];const x=b;let K;e[19]!==d?(K=()=>{d(!1)},e[19]=d,e[20]=K):K=e[20];const R=K;let A;e[21]!==c||e[22]!==s?(A=s(c?"autoScalingRule.EditAutoScalingRule":"autoScalingRule.AddAutoScalingRule"),e[21]=c,e[22]=s,e[23]=A):A=e[23];const D=S||F;let $;e[24]===Symbol.for("react.memo_cache_sentinel")?($=n.jsx(Sl,{active:!0,paragraph:{rows:6}}),e[24]=$):$=e[24];const q=c??null;let L;e[25]!==q?(L=n.jsx(Gn,{children:n.jsx(ha.Suspense,{fallback:$,children:n.jsx(ji,{autoScalingRule:q,formRef:f})})}),e[25]=q,e[26]=L):L=e[26];let _;return e[27]!==r||e[28]!==R||e[29]!==x||e[30]!==L||e[31]!==A||e[32]!==D?(_=n.jsx(_l,{...r,onOk:x,onCancel:R,centered:!0,title:A,confirmLoading:D,children:L}),e[27]=r,e[28]=R,e[29]=x,e[30]=L,e[31]=A,e[32]=D,e[33]=_):_=e[33],_};function Pi(l){return l==null?void 0:l.node}function Vi(l){var e;return(e=l.category)==null?void 0:e.name}function _i(l){var e;return!((e=l.category)!=null&&e.name)}function Ei(l){return{label:l.name,value:l.id,description:l.description}}function Oi(l){return l.category.name}function $i(l){return{label:l,value:l}}function wi(l,e){return String((e==null?void 0:e.label)??"").toLowerCase().includes(l.toLowerCase())}function Bi(l){return l.message}function Hi(l){return l.message}const Vt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"AutoScalingRuleListNodesFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],type:"AutoScalingRule",abstractKey:null};Vt.hash="54a32b764fc7e506f5bddfe218691cd2";const Qi=(l,e,i)=>{const r=l.metricSource==="PROMETHEUS"&&l.prometheusQueryPresetId?(i==null?void 0:i.get(l.prometheusQueryPresetId))??l.metricName:l.metricName,t=l.minThreshold,a=l.maxThreshold;return t!=null&&a!=null?n.jsxs(ie,{direction:"column",gap:"xxs",children:[n.jsxs(ie,{gap:"xs",children:[n.jsx(Zl,{children:r})," < ",t]}),n.jsxs(ie,{gap:"xs",children:[a," < ",n.jsx(Zl,{children:r})]})]}):a!=null?n.jsxs(ie,{gap:"xs",children:[a,n.jsx(dl,{title:e("autoScalingRule.MaxThreshold"),children:"<"}),n.jsx(Zl,{children:r})]}):t!=null?n.jsxs(ie,{gap:"xs",children:[n.jsx(Zl,{children:r}),n.jsx(dl,{title:e("autoScalingRule.MinThreshold"),children:"<"}),t]}):"-"},en=l=>{const e={};return l.createdAt&&(e.createdAt=l.createdAt),l.lastTriggeredAt&&(e.lastTriggeredAt=l.lastTriggeredAt),Array.isArray(l.AND)&&(e.AND=l.AND.map(en)),Array.isArray(l.OR)&&(e.OR=l.OR.map(en)),Array.isArray(l.NOT)&&(e.NOT=l.NOT.map(en)),e},qi=l=>{"use memo";const e=Be.c(103);let i,r,t,a,d,s,u;e[0]!==l?({autoScalingRulesFrgmt:i,presetMap:s,isEndpointDestroying:r,isOwnedByCurrentUser:t,onEditRule:d,onDeleteRule:a,...u}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d,e[6]=s,e[7]=u):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5],s=e[6],u=e[7]);const{t:o}=Ze();let m;e[8]===Symbol.for("react.memo_cache_sentinel")?(m=Vt,e[8]=m):m=e[8];const c=Ke.useFragment(m,i);let f;e[9]!==c?(f=Dl(c),e[9]=c,e[10]=f):f=e[10];const g=f;let y;e[11]===Symbol.for("react.memo_cache_sentinel")?(y={x:"max-content"},e[11]=y):y=e[11];let S;e[12]!==o?(S=o("autoScalingRule.MetricSource"),e[12]=o,e[13]=S):S=e[13];let p;e[14]!==o?(p=o("autoScalingRule.MetricSourceTooltip"),e[14]=o,e[15]=p):p=e[15];let h;e[16]!==p?(h=n.jsx(gl,{title:p}),e[16]=p,e[17]=h):h=e[17];let F;e[18]!==S||e[19]!==h?(F={key:"metricSource",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[S,h]}),dataIndex:"metricSource",fixed:"left"},e[18]=S,e[19]=h,e[20]=F):F=e[20];let b;e[21]!==o?(b=o("autoScalingRule.Condition"),e[21]=o,e[22]=b):b=e[22];let x;e[23]!==o?(x=o("autoScalingRule.ConditionTooltip"),e[23]=o,e[24]=x):x=e[24];let K;e[25]!==x?(K=n.jsx(gl,{title:x}),e[25]=x,e[26]=K):K=e[26];let R;e[27]!==K||e[28]!==b?(R=n.jsxs(ie,{gap:"xxs",align:"center",children:[b,K]}),e[27]=K,e[28]=b,e[29]=R):R=e[29];let A;e[30]!==r||e[31]!==t||e[32]!==a||e[33]!==d||e[34]!==s||e[35]!==o?(A=(le,w)=>w?n.jsx(Fn,{title:Qi(w,o,s),showActions:"always",actions:[{key:"edit",title:o("button.Edit"),icon:n.jsx(Ta,{}),disabled:r||!t,onClick:()=>d(w.id)},{key:"delete",title:o("button.Delete"),icon:n.jsx(xn,{}),type:"danger",disabled:r||!t,onClick:()=>a(w.id,w.metricName??"")}]}):"-",e[30]=r,e[31]=t,e[32]=a,e[33]=d,e[34]=s,e[35]=o,e[36]=A):A=e[36];let D;e[37]!==R||e[38]!==A?(D={key:"condition",title:R,fixed:"left",render:A},e[37]=R,e[38]=A,e[39]=D):D=e[39];let $;e[40]!==o?($=o("autoScalingRule.CoolDownSeconds"),e[40]=o,e[41]=$):$=e[41];let q;e[42]!==o?(q=o("autoScalingRule.CoolDownTooltip"),e[42]=o,e[43]=q):q=e[43];let L;e[44]!==q?(L=n.jsx(gl,{title:q}),e[44]=q,e[45]=L):L=e[45];let _;e[46]!==$||e[47]!==L?(_=n.jsxs(ie,{gap:"xxs",align:"center",children:[$,L]}),e[46]=$,e[47]=L,e[48]=_):_=e[48];let C;e[49]!==o?(C=le=>le!=null?o("autoScalingRule.CoolDownSecondsValue",{value:le}):"-",e[49]=o,e[50]=C):C=e[50];let M;e[51]!==_||e[52]!==C?(M={key:"timeWindow",title:_,dataIndex:"timeWindow",render:C},e[51]=_,e[52]=C,e[53]=M):M=e[53];let Q;e[54]!==o?(Q=o("autoScalingRule.StepSize"),e[54]=o,e[55]=Q):Q=e[55];let E;e[56]!==o?(E=o("autoScalingRule.StepSizeTooltip"),e[56]=o,e[57]=E):E=e[57];let z;e[58]!==E?(z=n.jsx(gl,{title:E}),e[58]=E,e[59]=z):z=e[59];let U;e[60]!==Q||e[61]!==z?(U={key:"stepSize",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[Q,z]}),dataIndex:"stepSize",render:zi},e[60]=Q,e[61]=z,e[62]=U):U=e[62];let G;e[63]!==o?(G=o("autoScalingRule.MIN/MAXReplicas"),e[63]=o,e[64]=G):G=e[64];let O;e[65]!==o?(O=o("autoScalingRule.MinMaxReplicasTooltip"),e[65]=o,e[66]=O):O=e[66];let B;e[67]!==O?(B=n.jsx(gl,{title:O}),e[67]=O,e[68]=B):B=e[68];let k;e[69]!==G||e[70]!==B?(k=n.jsxs(ie,{gap:"xxs",align:"center",children:[G,B]}),e[69]=G,e[70]=B,e[71]=k):k=e[71];let P;e[72]!==o?(P=(le,w)=>{if(!(w!=null&&w.stepSize))return"-";const te=w.minThreshold!=null,ue=w.maxThreshold!=null;return te&&ue?n.jsxs("span",{children:[o("autoScalingRule.MinReplicasValue",{value:w==null?void 0:w.minReplicas})," / ",o("autoScalingRule.MaxReplicasValue",{value:w==null?void 0:w.maxReplicas})]}):ue?n.jsx("span",{children:o("autoScalingRule.MaxReplicasValue",{value:w==null?void 0:w.maxReplicas})}):n.jsx("span",{children:o("autoScalingRule.MinReplicasValue",{value:w==null?void 0:w.minReplicas})})},e[72]=o,e[73]=P):P=e[73];let N;e[74]!==k||e[75]!==P?(N={key:"minMaxReplicas",title:k,render:P},e[74]=k,e[75]=P,e[76]=N):N=e[76];let Y;e[77]!==o?(Y=o("autoScalingRule.CreatedAt"),e[77]=o,e[78]=Y):Y=e[78];let Z;e[79]===Symbol.for("react.memo_cache_sentinel")?(Z=["descend","ascend"],e[79]=Z):Z=e[79];let I;e[80]!==Y?(I={key:"createdAt",title:Y,dataIndex:"createdAt",sorter:!0,sortDirections:Z,render:Ui},e[80]=Y,e[81]=I):I=e[81];let T;e[82]!==o?(T=o("autoScalingRule.LastTriggered"),e[82]=o,e[83]=T):T=e[83];let j;e[84]!==o?(j=o("autoScalingRule.LastTriggeredTooltip"),e[84]=o,e[85]=j):j=e[85];let H;e[86]!==j?(H=n.jsx(gl,{title:j}),e[86]=j,e[87]=H):H=e[87];let W;e[88]!==T||e[89]!==H?(W={key:"lastTriggeredAt",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[T,H]}),render:Wi},e[88]=T,e[89]=H,e[90]=W):W=e[90];let ee;e[91]!==D||e[92]!==M||e[93]!==U||e[94]!==N||e[95]!==I||e[96]!==W||e[97]!==F?(ee=[F,D,M,U,N,I,W],e[91]=D,e[92]=M,e[93]=U,e[94]=N,e[95]=I,e[96]=W,e[97]=F,e[98]=ee):ee=e[98];let X;return e[99]!==g||e[100]!==ee||e[101]!==u?(X=n.jsx(Pl,{scroll:y,rowKey:"id",columns:ee,showSorterTooltip:!1,dataSource:g,...u}),e[99]=g,e[100]=ee,e[101]=u,e[102]=X):X=e[102],X};function zi(l,e){if(!(e!=null&&e.stepSize))return"-";const i=e.minThreshold!=null,r=e.maxThreshold!=null;if(!i&&!r)return"-";const t=i&&r?"±":r?"+":"−";return n.jsxs(ie,{gap:"xs",children:[n.jsx(Xe.Text,{children:t}),n.jsx(Xe.Text,{children:Math.abs(e.stepSize)})]})}function Ui(l,e){return n.jsx("span",{children:e!=null&&e.createdAt?il(e.createdAt).format("ll LT"):"-"})}function Wi(l,e){return n.jsx("span",{children:e!=null&&e.lastTriggeredAt?il.utc(e.lastTriggeredAt).tz().format("ll LTS"):"-"})}const Gi=l=>{"use memo";var R,A,D;const e=Be.c(24),{deploymentFrgmt:i}=l,{t:r}=Ze(),{token:t}=Kl.useToken(),[a]=Yn();let d;e[0]===Symbol.for("react.memo_cache_sentinel")?(d=Mt,e[0]=d):d=e[0];const s=Ke.useFragment(d,i);if(!(s!=null&&s.id))return null;const u=(R=s.metadata)==null?void 0:R.status;let o;e[1]!==u?(o=kl(u),e[1]=u,e[2]=o):o=e[2];const m=o,c=((D=(A=s.creator)==null?void 0:A.basicInfo)==null?void 0:D.email)??null,f=!c||c===a.email;let g;e[3]!==r?(g=r("deployment.tab.AutoScaling"),e[3]=r,e[4]=g):g=e[4];let y;e[5]!==r?(y=r("deployment.tab.description.AutoScaling"),e[5]=r,e[6]=y):y=e[6];let S;e[7]!==t.colorTextDescription?(S=n.jsx(vn,{style:{color:t.colorTextDescription}}),e[7]=t.colorTextDescription,e[8]=S):S=e[8];let p;e[9]!==y||e[10]!==S?(p=n.jsx(dl,{title:y,children:S}),e[9]=y,e[10]=S,e[11]=p):p=e[11];let h;e[12]!==g||e[13]!==p?(h=n.jsxs(ie,{gap:"xs",align:"center",children:[g,p]}),e[12]=g,e[13]=p,e[14]=h):h=e[14];let F;e[15]===Symbol.for("react.memo_cache_sentinel")?(F={body:{paddingTop:0}},e[15]=F):F=e[15];let b;e[16]===Symbol.for("react.memo_cache_sentinel")?(b=n.jsx(Sl,{active:!0}),e[16]=b):b=e[16];let x;e[17]!==s.id||e[18]!==m||e[19]!==f?(x=n.jsx(V.Suspense,{fallback:b,children:n.jsx(Yi,{deploymentId:s.id,isEndpointDestroying:m,isOwnedByCurrentUser:f})}),e[17]=s.id,e[18]=m,e[19]=f,e[20]=x):x=e[20];let K;return e[21]!==x||e[22]!==h?(K=n.jsx(Wl,{title:h,styles:F,children:x}),e[21]=x,e[22]=h,e[23]=K):K=e[23],K},Yi=l=>{"use memo";var tl,Ae,Ue,Le,ll,Ge,sl,nl;const e=Be.c(125),{deploymentId:i,isEndpointDestroying:r,isOwnedByCurrentUser:t}=l,{t:a}=Ze(),{message:d}=Al.useApp(),[s,u]=V.useTransition(),[o,m]=Rl(),[c,f]=V.useState(null),[g,y]=V.useState(!1),[S,p]=V.useState(null),[h,F]=Tl("table_column_overrides.AutoScalingRuleList");let b,x;e[0]===Symbol.for("react.memo_cache_sentinel")?(b={order:Ul(["createdAt","-createdAt"]).withDefault("-createdAt"),filter:Da(Xi)},x={history:"replace"},e[0]=b,e[1]=x):(b=e[0],x=e[1]);const[K,R]=Kn(b,x),A=K.order,D=K.filter??void 0;let $;e[2]===Symbol.for("react.memo_cache_sentinel")?($={current:1,pageSize:10},e[2]=$):$=e[2];const{baiPaginationOption:q,tablePaginationOption:L,setTablePaginationOption:_}=Ia($);let C;e[3]!==D?(C=D?en(D):null,e[3]=D,e[4]=C):C=e[4];const M=C,Q=A.startsWith("-")?"DESC":"ASC";let E;e[5]!==Q?(E=[{field:"CREATED_AT",direction:Q}],e[5]=Q,e[6]=E):E=e[6];let z;e[7]!==q.limit||e[8]!==q.offset||e[9]!==i||e[10]!==M||e[11]!==E?(z={deploymentId:i,offset:q.offset,limit:q.limit,orderBy:E,filter:M},e[7]=q.limit,e[8]=q.offset,e[9]=i,e[10]=M,e[11]=E,e[12]=z):z=e[12];const U=z,G=V.useDeferredValue(U);let O;e[13]===Symbol.for("react.memo_cache_sentinel")?(O=At,e[13]=O):O=e[13];let B;e[14]!==o?(B={fetchPolicy:"store-and-network",fetchKey:o},e[14]=o,e[15]=B):B=e[15];const k=Ke.useLazyLoadQuery(O,G,B);let P,N;e[16]===Symbol.for("react.memo_cache_sentinel")?(P=Ct,N={},e[16]=P,e[17]=N):(P=e[16],N=e[17]);const{prometheusQueryPresets:Y}=Ke.useLazyLoadQuery(P,N);let Z;if(e[18]!==Y){if(Z=new Map,Y!=null&&Y.edges)for(const je of Y.edges)je!=null&&je.node&&Z.set(Ye(je.node.id),je.node.name);e[18]=Y,e[19]=Z}else Z=e[19];const I=Z;let T;e[20]!==((Ae=(tl=k==null?void 0:k.deployment)==null?void 0:tl.autoScalingRules)==null?void 0:Ae.edges)?(T=Dl(hl((Le=(Ue=k==null?void 0:k.deployment)==null?void 0:Ue.autoScalingRules)==null?void 0:Le.edges,"node")),e[20]=(Ge=(ll=k==null?void 0:k.deployment)==null?void 0:ll.autoScalingRules)==null?void 0:Ge.edges,e[21]=T):T=e[21];const j=T,H=((nl=(sl=k==null?void 0:k.deployment)==null?void 0:sl.autoScalingRules)==null?void 0:nl.count)??0;let W;e[22]===Symbol.for("react.memo_cache_sentinel")?(W=It,e[22]=W):W=e[22];const ee=zn(W);let X;e[23]!==m?(X=()=>{u(()=>{m()})},e[23]=m,e[24]=X):X=e[24];const le=X;let w;e[25]===Symbol.for("react.memo_cache_sentinel")?(w=(je,rl)=>{p({id:je,metricName:rl})},e[25]=w):w=e[25];const te=w;let ue;e[26]===Symbol.for("react.memo_cache_sentinel")?(ue={flex:1},e[26]=ue):ue=e[26];let ce;e[27]!==a?(ce=a("autoScalingRule.CreatedAt"),e[27]=a,e[28]=ce):ce=e[28];let Re;e[29]===Symbol.for("react.memo_cache_sentinel")?(Re=["after","before"],e[29]=Re):Re=e[29];let ye;e[30]!==ce?(ye={key:"createdAt",propertyLabel:ce,type:"datetime",operators:Re,defaultOperator:"after"},e[30]=ce,e[31]=ye):ye=e[31];let oe;e[32]!==a?(oe=a("autoScalingRule.LastTriggered"),e[32]=a,e[33]=oe):oe=e[33];let de;e[34]===Symbol.for("react.memo_cache_sentinel")?(de=["after","before"],e[34]=de):de=e[34];let me;e[35]!==oe?(me={key:"lastTriggeredAt",propertyLabel:oe,type:"datetime",operators:de,defaultOperator:"after"},e[35]=oe,e[36]=me):me=e[36];let re;e[37]!==ye||e[38]!==me?(re=[ye,me],e[37]=ye,e[38]=me,e[39]=re):re=e[39];let fe;e[40]!==R||e[41]!==_?(fe=je=>{u(()=>{R({filter:je??null}),_({current:1})})},e[40]=R,e[41]=_,e[42]=fe):fe=e[42];let Fe;e[43]!==D||e[44]!==re||e[45]!==fe?(Fe=n.jsx(Gl,{style:ue,filterProperties:re,value:D,onChange:fe}),e[43]=D,e[44]=re,e[45]=fe,e[46]=Fe):Fe=e[46];let be;e[47]!==m?(be=()=>{u(()=>m())},e[47]=m,e[48]=be):be=e[48];let ve;e[49]!==s||e[50]!==be?(ve=n.jsx(Ml,{loading:s,value:"",onChange:be}),e[49]=s,e[50]=be,e[51]=ve):ve=e[51];let he;e[52]===Symbol.for("react.memo_cache_sentinel")?(he=n.jsx(Il,{}),e[52]=he):he=e[52];const ae=r||!t;let Se;e[53]===Symbol.for("react.memo_cache_sentinel")?(Se=()=>{f(null),y(!0)},e[53]=Se):Se=e[53];let Ee;e[54]!==a?(Ee=a("modelService.AddRules"),e[54]=a,e[55]=Ee):Ee=e[55];let Ce;e[56]!==ae||e[57]!==Ee?(Ce=n.jsx(yl,{type:"primary",icon:he,disabled:ae,onClick:Se,children:Ee}),e[56]=ae,e[57]=Ee,e[58]=Ce):Ce=e[58];let Te;e[59]!==Fe||e[60]!==ve||e[61]!==Ce?(Te=n.jsxs(ie,{align:"center",gap:"sm",children:[Fe,ve,Ce]}),e[59]=Fe,e[60]=ve,e[61]=Ce,e[62]=Te):Te=e[62];const we=s||G!==U;let v;e[63]!==h||e[64]!==F?(v={columnOverrides:h,onColumnOverridesChange:F},e[63]=h,e[64]=F,e[65]=v):v=e[65];let J;e[66]!==R?(J=je=>{u(()=>{R({order:je||null})})},e[66]=R,e[67]=J):J=e[67];let ne;e[68]!==_?(ne=(je,rl)=>{_({current:je,pageSize:rl})},e[68]=_,e[69]=ne):ne=e[69];let se;e[70]!==ne||e[71]!==L.current||e[72]!==L.pageSize||e[73]!==H?(se={pageSize:L.pageSize,current:L.current,total:H,onChange:ne},e[70]=ne,e[71]=L.current,e[72]=L.pageSize,e[73]=H,e[74]=se):se=e[74];let ge;e[75]===Symbol.for("react.memo_cache_sentinel")?(ge=je=>{f(je),y(!0)},e[75]=ge):ge=e[75];let ke;e[76]!==j||e[77]!==r||e[78]!==t||e[79]!==A||e[80]!==I||e[81]!==we||e[82]!==v||e[83]!==J||e[84]!==se?(ke=n.jsx(qi,{autoScalingRulesFrgmt:j,presetMap:I,order:A,loading:we,tableSettings:v,onChangeOrder:J,pagination:se,isEndpointDestroying:r,isOwnedByCurrentUser:t,onEditRule:ge,onDeleteRule:te}),e[76]=j,e[77]=r,e[78]=t,e[79]=A,e[80]=I,e[81]=we,e[82]=v,e[83]=J,e[84]=se,e[85]=ke):ke=e[85];let Pe;e[86]!==Te||e[87]!==ke?(Pe=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[Te,ke]}),e[86]=Te,e[87]=ke,e[88]=Pe):Pe=e[88];let Me;e[89]!==i?(Me=Ye(i),e[89]=i,e[90]=Me):Me=e[90];let Oe;e[91]!==j||e[92]!==c?(Oe=c?j.find(je=>je.id===c)??null:null,e[91]=j,e[92]=c,e[93]=Oe):Oe=e[93];let _e;e[94]!==le?(_e=je=>{y(!1),je&&le()},e[94]=le,e[95]=_e):_e=e[95];let He;e[96]===Symbol.for("react.memo_cache_sentinel")?(He=()=>{f(null)},e[96]=He):He=e[96];let xe;e[97]!==g||e[98]!==Me||e[99]!==Oe||e[100]!==_e?(xe=n.jsx(pl,{children:n.jsx(Ni,{open:g,modelDeploymentId:Me,autoScalingRuleFrgmt:Oe,onRequestClose:_e,afterClose:He})}),e[97]=g,e[98]=Me,e[99]=Oe,e[100]=_e,e[101]=xe):xe=e[101];const el=!!S;let Qe;e[102]!==a?(Qe=a("autoScalingRule.DeleteAutoScalingRule"),e[102]=a,e[103]=Qe):Qe=e[103];let We;e[104]!==a?(We=a("autoScalingRule.DeleteConfirmation"),e[104]=a,e[105]=We):We=e[105];let qe;e[106]!==S?(qe=S?[{key:S.id,label:S.metricName}]:[],e[106]=S,e[107]=qe):qe=e[107];let ze;e[108]!==ee||e[109]!==S||e[110]!==le||e[111]!==d||e[112]!==a?(ze=()=>{if(S)return ee({input:{id:Ye(S.id)}}).then(()=>{p(null),le(),d.success({key:"autoscaling-rule-deleted",content:a("autoScalingRule.SuccessfullyDeleted")})}).catch(je=>{const rl=Array.isArray(je)?je:[je];for(const fl of rl)d.error((fl==null?void 0:fl.message)||a("dialog.ErrorOccurred"))})},e[108]=ee,e[109]=S,e[110]=le,e[111]=d,e[112]=a,e[113]=ze):ze=e[113];let Je;e[114]===Symbol.for("react.memo_cache_sentinel")?(Je=()=>p(null),e[114]=Je):Je=e[114];let De;e[115]!==el||e[116]!==Qe||e[117]!==We||e[118]!==qe||e[119]!==ze?(De=n.jsx(bn,{open:el,title:Qe,description:We,items:qe,reversible:!0,onOk:ze,onCancel:Je}),e[115]=el,e[116]=Qe,e[117]=We,e[118]=qe,e[119]=ze,e[120]=De):De=e[120];let $e;return e[121]!==Pe||e[122]!==xe||e[123]!==De?($e=n.jsxs(n.Fragment,{children:[Pe,xe,De]}),e[121]=Pe,e[122]=xe,e[123]=De,e[124]=$e):$e=e[124],$e};function Xi(l){return l}const _t=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentBasicInfoCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentBasicInfoCardDeleteMutation",selections:e},params:{cacheID:"70ed95e6d8ed42187398c9bc2c13f5bb",id:null,metadata:{},name:"DeploymentBasicInfoCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentBasicInfoCardDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();_t.hash="219d6f05b61219aeb47beff89d87a769";const Et=function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentBasicInfoCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[l],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentTagChips_metadata"}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null}}();Et.hash="25c43526c832d75ea335a66d0e86f3af";const Ot=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,r,e,i],kind:"Operation",name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},s,u,o,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u,o,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"b24d145b426294eb9cc72c268ccd1df2",id:null,metadata:{},name:"DeploymentSchedulingHistoryModalQuery",operationKind:"query",text:`query DeploymentSchedulingHistoryModalQuery(
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
`}}}();Ot.hash="89ec50bb9b1f834e59c642072090d378";const $t=Ot,Ji=l=>{"use memo";var Fe,be,ve,he;const e=Be.c(113);let i,r,t,a,d;e[0]!==l?({open:a,queryRef:d,onReload:t,onCancel:r,...i}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=Ze(),[u,o]=Rl(),[m,c]=V.useState(),[f,g]=V.useState("-updatedAt"),[y,S]=Tl("schedulingHistoryExpandMode"),[p,h]=Tl("table_column_overrides.DeploymentSchedulingHistory");let F;e[6]===Symbol.for("react.memo_cache_sentinel")?(F={current:1,pageSize:10},e[6]=F):F=e[6];const{tablePaginationOption:b,setTablePaginationOption:x}=Tn(F),K=V.useDeferredValue(d),R=K!==d,A=Ke.usePreloadedQuery($t,K);let D;e[7]!==s?(D=s("deployment.DeploymentSchedulingHistory"),e[7]=s,e[8]=D):D=e[8];let $,q;e[9]===Symbol.for("react.memo_cache_sentinel")?($={maxWidth:1600},q={body:{minHeight:"80vh"}},e[9]=$,e[10]=q):($=e[9],q=e[10]);let L;e[11]!==t||e[12]!==d.variables||e[13]!==x?(L=ae=>{c(ae),x({current:1}),t({...d.variables,filter:ae,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=d.variables,e[13]=x,e[14]=L):L=e[14];let _;e[15]!==s?(_=s("deployment.ID"),e[15]=s,e[16]=_):_=e[16];let C;e[17]!==_?(C={key:"id",propertyLabel:_,type:"uuid",fixedOperator:"equals"},e[17]=_,e[18]=C):C=e[18];let M;e[19]!==s?(M=s("deployment.Phase"),e[19]=s,e[20]=M):M=e[20];let Q;e[21]!==M?(Q={key:"phase",propertyLabel:M,type:"string",fixedOperator:"contains"},e[21]=M,e[22]=Q):Q=e[22];let E;e[23]!==s?(E=s("deployment.Result"),e[23]=s,e[24]=E):E=e[24];let z;e[25]===Symbol.for("react.memo_cache_sentinel")?(z=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=z):z=e[25];let U;e[26]!==E?(U={key:"result",propertyLabel:E,type:"enum",strictSelection:!0,options:z},e[26]=E,e[27]=U):U=e[27];let G;e[28]!==s?(G=s("deployment.FromStatus"),e[28]=s,e[29]=G):G=e[29];let O;e[30]!==G?(O={key:"fromStatus",propertyLabel:G,type:"string",valueMode:"scalar"},e[30]=G,e[31]=O):O=e[31];let B;e[32]!==s?(B=s("deployment.ToStatus"),e[32]=s,e[33]=B):B=e[33];let k;e[34]!==B?(k={key:"toStatus",propertyLabel:B,type:"string",valueMode:"scalar"},e[34]=B,e[35]=k):k=e[35];let P;e[36]!==s?(P=s("deployment.ErrorCode"),e[36]=s,e[37]=P):P=e[37];let N;e[38]!==P?(N={key:"errorCode",propertyLabel:P,type:"string",fixedOperator:"contains"},e[38]=P,e[39]=N):N=e[39];let Y;e[40]!==s?(Y=s("deployment.Message"),e[40]=s,e[41]=Y):Y=e[41];let Z;e[42]!==Y?(Z={key:"message",propertyLabel:Y,type:"string",fixedOperator:"contains"},e[42]=Y,e[43]=Z):Z=e[43];let I;e[44]!==s?(I=s("deployment.CreatedAt"),e[44]=s,e[45]=I):I=e[45];let T;e[46]!==I?(T={key:"createdAt",propertyLabel:I,type:"datetime",defaultOperator:"after"},e[46]=I,e[47]=T):T=e[47];let j;e[48]!==s?(j=s("deployment.UpdatedAt"),e[48]=s,e[49]=j):j=e[49];let H;e[50]!==j?(H={key:"updatedAt",propertyLabel:j,type:"datetime",defaultOperator:"after"},e[50]=j,e[51]=H):H=e[51];let W;e[52]!==U||e[53]!==O||e[54]!==k||e[55]!==N||e[56]!==Z||e[57]!==T||e[58]!==H||e[59]!==C||e[60]!==Q?(W=[C,Q,U,O,k,N,Z,T,H],e[52]=U,e[53]=O,e[54]=k,e[55]=N,e[56]=Z,e[57]=T,e[58]=H,e[59]=C,e[60]=Q,e[61]=W):W=e[61];let ee;e[62]!==m||e[63]!==W||e[64]!==L?(ee=n.jsx(Gl,{value:m,onChange:L,filterProperties:W}),e[62]=m,e[63]=W,e[64]=L,e[65]=ee):ee=e[65];let X;e[66]!==t||e[67]!==d.variables||e[68]!==o?(X=ae=>{o(ae),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=o,e[69]=X):X=e[69];let le;e[70]!==u||e[71]!==R||e[72]!==X?(le=n.jsx(ie,{children:n.jsx(Ml,{value:u,onChange:X,loading:R,autoUpdateDelay:null})}),e[70]=u,e[71]=R,e[72]=X,e[73]=le):le=e[73];let w;e[74]!==ee||e[75]!==le?(w=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[ee,le]}),e[74]=ee,e[75]=le,e[76]=w):w=e[76];const te=y??void 0;let ue;e[77]!==p||e[78]!==h?(ue={columnOverrides:p,onColumnOverridesChange:h},e[77]=p,e[78]=h,e[79]=ue):ue=e[79];let ce;e[80]!==t||e[81]!==d.variables||e[82]!==x?(ce=ae=>{g(ae),x({current:1}),t({...d.variables,orderBy:Nl(ae),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=d.variables,e[82]=x,e[83]=ce):ce=e[83];const Re=((Fe=A.deploymentScopedSchedulingHistories)==null?void 0:Fe.count)??0;let ye;e[84]!==t||e[85]!==d.variables||e[86]!==x?(ye=(ae,Se)=>{x({current:ae,pageSize:Se}),t({...d.variables,limit:Se,offset:ae>1?(ae-1)*Se:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=d.variables,e[86]=x,e[87]=ye):ye=e[87];let oe;e[88]!==Re||e[89]!==ye||e[90]!==b.current||e[91]!==b.pageSize?(oe={pageSize:b.pageSize,current:b.current,total:Re,onChange:ye},e[88]=Re,e[89]=ye,e[90]=b.current,e[91]=b.pageSize,e[92]=oe):oe=e[92];let de;e[93]!==((be=A.deploymentScopedSchedulingHistories)==null?void 0:be.edges)?(de=hl((ve=A.deploymentScopedSchedulingHistories)==null?void 0:ve.edges,"node"),e[93]=(he=A.deploymentScopedSchedulingHistories)==null?void 0:he.edges,e[94]=de):de=e[94];let me;e[95]!==R||e[96]!==f||e[97]!==S||e[98]!==te||e[99]!==ue||e[100]!==ce||e[101]!==oe||e[102]!==de?(me=n.jsx(Ri,{resizable:!0,loading:R,expandMode:te,onExpandModeChange:S,tableSettings:ue,order:f,onChangeOrder:ce,pagination:oe,schedulingHistoryFrgmt:de}),e[95]=R,e[96]=f,e[97]=S,e[98]=te,e[99]=ue,e[100]=ce,e[101]=oe,e[102]=de,e[103]=me):me=e[103];let re;e[104]!==w||e[105]!==me?(re=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[w,me]}),e[104]=w,e[105]=me,e[106]=re):re=e[106];let fe;return e[107]!==i||e[108]!==r||e[109]!==a||e[110]!==D||e[111]!==re?(fe=n.jsx(_l,{title:D,open:a,width:"90%",style:$,styles:q,footer:null,onCancel:r,...i,children:re}),e[107]=i,e[108]=r,e[109]=a,e[110]=D,e[111]=re,e[112]=fe):fe=e[112],fe},xl=()=>n.jsx(Xe.Text,{type:"secondary",children:"-"}),Zi=l=>{"use memo";var f,g,y;const e=Be.c(26),{deployment:i,onClickSchedulingHistoryAction:r}=l,{t}=Ze(),a=an(),d=Xn(),s=((g=(f=i==null?void 0:i.metadata.projectV2)==null?void 0:f.basicInfo)==null?void 0:g.name)??(i==null?void 0:i.metadata.projectId);let u;if(e[0]!==i||e[1]!==d.pathname||e[2]!==r||e[3]!==s||e[4]!==t||e[5]!==a){const S=t("deployment.Visibility"),p=i==null?void 0:i.networkAccess.openToPublic;let h;e[7]!==t?(h=t("deployment.Public"),e[7]=t,e[8]=h):h=e[8];let F;e[9]!==t?(F=t("deployment.Private"),e[9]=t,e[10]=F):F=e[10];let b;e[11]===Symbol.for("react.memo_cache_sentinel")?(b=xl(),e[11]=b):b=e[11];let x;e[12]!==p||e[13]!==h||e[14]!==F?(x=n.jsx(Ja,{value:p,trueLabel:h,falseLabel:F,fallback:b}),e[12]=p,e[13]=h,e[14]=F,e[15]=x):x=e[15];const K=t("deployment.Tags"),R=(i==null?void 0:i.metadata)??null;let A;e[16]!==d.pathname||e[17]!==a?(A=q=>{const L=d.pathname.startsWith("/admin-deployments")?"/admin-deployments":d.pathname.startsWith("/project-admin-deployments")?"/project-admin-deployments":"/deployments";a({pathname:L,search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:q}})}).toString()})},e[16]=d.pathname,e[17]=a,e[18]=A):A=e[18];let D;e[19]===Symbol.for("react.memo_cache_sentinel")?(D=xl(),e[19]=D):D=e[19];let $;e[20]!==A||e[21]!==R?($=n.jsx(Ya,{metadataFrgmt:R,onTagClick:A,fallback:D}),e[20]=A,e[21]=R,e[22]=$):$=e[22],u=tn([{key:"lifecycle",label:t("deployment.Lifecycle"),children:i!=null&&i.metadata.status?n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ot,{status:i.metadata.status}),r&&n.jsxs(n.Fragment,{children:[n.jsx(Wn,{type:"vertical",style:{margin:0}}),n.jsx(yl,{type:"link",size:"small",icon:n.jsx(rt,{}),style:{padding:0},action:async()=>{await r()},children:t("deployment.SchedulingHistory")})]})]}):xl()},{key:"id",label:t("deployment.DeploymentId"),children:i!=null&&i.id?n.jsx(Ll,{globalId:i.id,copyable:!0,ellipsis:!1,style:{maxWidth:"none"}}):xl()},{key:"project",label:t("deployment.Project"),children:s||xl()},{key:"domain",label:t("deployment.Domain"),children:(i==null?void 0:i.metadata.domainName)||xl()},{key:"resource-group",label:t("modelStore.ResourceGroup"),children:(i==null?void 0:i.metadata.resourceGroupName)||xl()},{key:"endpoint-url",label:t("deployment.EndpointUrl"),children:i!=null&&i.networkAccess.endpointUrl?n.jsx(Xe.Text,{copyable:!0,style:{wordBreak:"break-all"},children:i.networkAccess.endpointUrl}):xl()},{key:"visibility",label:S,children:x},{key:"desired-replicas",label:t("deployment.DesiredReplicas"),children:((y=i==null?void 0:i.replicaState)==null?void 0:y.desiredReplicaCount)??xl()},{key:"tags",label:K,children:$}]),e[0]=i,e[1]=d.pathname,e[2]=r,e[3]=s,e[4]=t,e[5]=a,e[6]=u}else u=e[6];const o=u;let m;e[23]===Symbol.for("react.memo_cache_sentinel")?(m={xs:1,sm:1,md:2,lg:2,xl:2,xxl:2},e[23]=m):m=e[23];let c;return e[24]!==o?(c=n.jsx(Ma,{bordered:!0,column:m,items:o}),e[24]=o,e[25]=c):c=e[25],c},es=l=>{"use memo";const e=Be.c(99),{deploymentFrgmt:i,isPendingRefetch:r,onRefetch:t,autoUpdateDelay:a}=l,d=a===void 0?null:a,{t:s}=Ze(),{message:u}=Al.useApp(),{logger:o}=Vl(),m=an(),c=Xn();let f;e[0]===Symbol.for("react.memo_cache_sentinel")?(f=Et,e[0]=f):f=e[0];const g=Ke.useFragment(f,i),[y,S]=V.useState(!1),[p,h]=V.useState(!1),[F,b]=V.useState(!1),[x,K]=Ke.useQueryLoader($t),R=Jn();let A;e[1]!==R?(A=(R==null?void 0:R.supports("deployment-scheduling-history"))??!1,e[1]=R,e[2]=A):A=e[2];const D=A;let $;e[3]===Symbol.for("react.memo_cache_sentinel")?($=_t,e[3]=$):$=e[3];const[q,L]=Ke.useMutation($),_=(g==null?void 0:g.metadata.name)??"",C=g==null?void 0:g.metadata.status,M=c.pathname.startsWith("/admin-deployments")?"/admin-deployments":c.pathname.startsWith("/project-admin-deployments")?"/project-admin-deployments":"/deployments";let Q;e[4]!==q||e[5]!==g||e[6]!==M||e[7]!==o||e[8]!==u||e[9]!==s||e[10]!==m?(Q=()=>{g!=null&&g.id&&q({variables:{input:{id:Ye(g.id)??g.id}},onCompleted:(Se,Ee)=>{if(Ee&&Ee.length>0){o.error("Failed to delete deployment",Ee),u.error(s("deployment.FailedToDeleteDeployment"));return}u.success(s("deployment.DeploymentDeleted")),h(!1),m(M)},onError:Se=>{o.error("Failed to delete deployment",Se),u.error(s("deployment.FailedToDeleteDeployment"))}})},e[4]=q,e[5]=g,e[6]=M,e[7]=o,e[8]=u,e[9]=s,e[10]=m,e[11]=Q):Q=e[11];const E=Q;let z;e[12]!==s?(z=s("deployment.BasicInformation"),e[12]=s,e[13]=z):z=e[13];let U;e[14]!==d||e[15]!==r||e[16]!==t?(U=n.jsx(Ml,{loading:r,value:"",onChange:t,autoUpdateDelay:d}),e[14]=d,e[15]=r,e[16]=t,e[17]=U):U=e[17];let G;e[18]===Symbol.for("react.memo_cache_sentinel")?(G=n.jsx(Ca,{}),e[18]=G):G=e[18];let O;e[19]!==C?(O=kl(C),e[19]=C,e[20]=O):O=e[20];let B;e[21]===Symbol.for("react.memo_cache_sentinel")?(B=async()=>{S(!0)},e[21]=B):B=e[21];let k;e[22]!==s?(k=s("button.Edit"),e[22]=s,e[23]=k):k=e[23];let P;e[24]!==k||e[25]!==O?(P=n.jsx(yl,{icon:G,disabled:O,action:B,children:k}),e[24]=k,e[25]=O,e[26]=P):P=e[26];let N;e[27]===Symbol.for("react.memo_cache_sentinel")?(N=["click"],e[27]=N):N=e[27];let Y;e[28]!==s?(Y=s("deployment.DeleteDeployment"),e[28]=s,e[29]=Y):Y=e[29];let Z;e[30]===Symbol.for("react.memo_cache_sentinel")?(Z=n.jsx(xn,{}),e[30]=Z):Z=e[30];let I;e[31]!==C||e[32]!==L?(I=kl(C)||L,e[31]=C,e[32]=L,e[33]=I):I=e[33];let T;e[34]===Symbol.for("react.memo_cache_sentinel")?(T=()=>h(!0),e[34]=T):T=e[34];let j;e[35]!==Y||e[36]!==I?(j={items:[{key:"delete",label:Y,icon:Z,danger:!0,disabled:I,onClick:T}]},e[35]=Y,e[36]=I,e[37]=j):j=e[37];let H;e[38]===Symbol.for("react.memo_cache_sentinel")?(H=n.jsx(Zn,{}),e[38]=H):H=e[38];let W;e[39]!==s?(W=s("button.More"),e[39]=s,e[40]=W):W=e[40];let ee;e[41]!==W?(ee=n.jsx(ul,{icon:H,"aria-label":W}),e[41]=W,e[42]=ee):ee=e[42];let X;e[43]!==j||e[44]!==ee?(X=n.jsx(et,{trigger:N,menu:j,children:ee}),e[43]=j,e[44]=ee,e[45]=X):X=e[45];let le;e[46]!==P||e[47]!==X?(le=n.jsxs(ql.Compact,{children:[P,X]}),e[46]=P,e[47]=X,e[48]=le):le=e[48];let w;e[49]!==le||e[50]!==U?(w=n.jsxs(ie,{gap:"xs",align:"center",children:[U,le]}),e[49]=le,e[50]=U,e[51]=w):w=e[51];let te;e[52]===Symbol.for("react.memo_cache_sentinel")?(te={body:{paddingTop:0}},e[52]=te):te=e[52];let ue;e[53]!==g||e[54]!==K||e[55]!==D?(ue=D&&(g!=null&&g.id)?async()=>{const Se=g.id;Se&&(K({scope:{deploymentId:jl(Se)??Se},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),b(!0))}:void 0,e[53]=g,e[54]=K,e[55]=D,e[56]=ue):ue=e[56];let ce;e[57]!==g||e[58]!==ue?(ce=n.jsx(Zi,{deployment:g,onClickSchedulingHistoryAction:ue}),e[57]=g,e[58]=ue,e[59]=ce):ce=e[59];let Re;e[60]!==w||e[61]!==ce||e[62]!==z?(Re=n.jsx(Wl,{title:z,extra:w,styles:te,children:ce}),e[60]=w,e[61]=ce,e[62]=z,e[63]=Re):Re=e[63];let ye;e[64]!==t?(ye=Se=>{S(!1),Se&&t()},e[64]=t,e[65]=ye):ye=e[65];let oe;e[66]!==g||e[67]!==y||e[68]!==ye?(oe=n.jsx(Aa,{open:y,deploymentFrgmt:g,onRequestClose:ye}),e[66]=g,e[67]=y,e[68]=ye,e[69]=oe):oe=e[69];let de;e[70]!==s?(de=s("deployment.DeleteDeployment"),e[70]=s,e[71]=de):de=e[71];let me;e[72]!==s?(me=s("deployment.Deployment"),e[72]=s,e[73]=me):me=e[73];let re;e[74]!==_?(re=_?[{key:_,label:_}]:[],e[74]=_,e[75]=re):re=e[75];let fe;e[76]!==_?(fe={placeholder:_},e[76]=_,e[77]=fe):fe=e[77];let Fe;e[78]!==L?(Fe={loading:L},e[78]=L,e[79]=Fe):Fe=e[79];let be;e[80]===Symbol.for("react.memo_cache_sentinel")?(be=()=>h(!1),e[80]=be):be=e[80];let ve;e[81]!==_||e[82]!==E||e[83]!==p||e[84]!==de||e[85]!==me||e[86]!==re||e[87]!==fe||e[88]!==Fe?(ve=n.jsx(bn,{open:p,title:de,target:me,items:re,confirmText:_,requireConfirmInput:!0,inputProps:fe,okButtonProps:Fe,onOk:E,onCancel:be}),e[81]=_,e[82]=E,e[83]=p,e[84]=de,e[85]=me,e[86]=re,e[87]=fe,e[88]=Fe,e[89]=ve):ve=e[89];let he;e[90]!==x||e[91]!==F||e[92]!==K?(he=x!=null&&n.jsx(pl,{children:n.jsx(Ji,{open:F,queryRef:x,onReload:K,onCancel:()=>b(!1)})}),e[90]=x,e[91]=F,e[92]=K,e[93]=he):he=e[93];let ae;return e[94]!==Re||e[95]!==oe||e[96]!==ve||e[97]!==he?(ae=n.jsxs(n.Fragment,{children:[Re,oe,ve,he]}),e[94]=Re,e[95]=oe,e[96]=ve,e[97]=he,e[98]=ae):ae=e[98],ae},wt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"sessionId",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"revisionId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"trafficStatus",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"healthStatus",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},h={alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"sessionV2",plural:!1,selections:[u,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[p],storageKey:null}],storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},b=[p,F],x={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},R={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[u,p,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentReplicasCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,m,c,f,g,y,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[u,S,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null},h],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,r],kind:"Operation",name:"DeploymentReplicasCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[u,o,m,c,f,g,y,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[u,S,y,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[p,u],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},F,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[x,K,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},R],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[x,K,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},R],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},h],storageKey:null}],storageKey:null}],storageKey:null},u],storageKey:null}]},params:{cacheID:"79f688ce3d9ffc3c72881648d7d76eab",id:null,metadata:{},name:"DeploymentReplicasCardListQuery",operationKind:"query",text:`query DeploymentReplicasCardListQuery(
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
`}}}();wt.hash="3c889ebaa68c08cff62a842b2869be6a";const Bt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentReplicasCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};Bt.hash="c535e4dd070869785c37a4074751984b";const ls={HEALTHY:"success",UNHEALTHY:"error",DEGRADED:"warning",NOT_CHECKED:"default",PROVISIONING:"info",WARMING_UP:"info",RUNNING:"success",TERMINATING:"warning",TERMINATED:"default",FAILED_TO_START:"error"},ns={HEALTHY:"Healthy",UNHEALTHY:"Unhealthy",DEGRADED:"Degraded",NOT_CHECKED:"NotChecked",PROVISIONING:"Provisioning",WARMING_UP:"WarmingUp",RUNNING:"Running",TERMINATING:"Terminating",TERMINATED:"Terminated",FAILED_TO_START:"FailedToStart"},$n=l=>{"use memo";const e=Be.c(23);let i,r,t;e[0]!==l?({status:i,showTooltip:r,...t}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t):(i=e[1],r=e[2],t=e[3]);const a=r===void 0?!0:r,{t:d}=Ze(),s=ls[i],u=ns[i],o=`replicaStatus.${u}`;let m;e[4]!==d||e[5]!==o?(m=d(o),e[4]=d,e[5]=o,e[6]=m):m=e[6];const c=m;let f;e[7]!==u||e[8]!==a||e[9]!==d?(f=a?d(`replicaStatus.tooltip.${u}`,{defaultValue:""}):void 0,e[7]=u,e[8]=a,e[9]=d,e[10]=f):f=e[10];const g=f;let y;e[11]!==i?(y=i==="WARMING_UP"?n.jsx(Dn,{spin:!0}):void 0,e[11]=i,e[12]=y):y=e[12];const S=y;let p;e[13]!==s||e[14]!==S||e[15]!==c||e[16]!==t?(p=n.jsx(ln,{...t,color:s,icon:S,children:c}),e[13]=s,e[14]=S,e[15]=c,e[16]=t,e[17]=p):p=e[17];const h=p;if(!a||!g)return h;let F;e[18]!==h?(F=n.jsx("span",{children:h}),e[18]=h,e[19]=F):F=e[19];let b;return e[20]!==F||e[21]!==g?(b=n.jsx(dl,{title:g,children:F}),e[20]=F,e[21]=g,e[22]=b):b=e[22],b},Ht=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,r,e,i],kind:"Operation",name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},s,u,o,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},u,o,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"e02133438de747b29f05fb0c3109339d",id:null,metadata:{},name:"RouteSchedulingHistoryModalQuery",operationKind:"query",text:`query RouteSchedulingHistoryModalQuery(
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
`}}}();Ht.hash="e770c8de50ced262d1f75ecd5be88c57";const Qt=Ht,ts=l=>{"use memo";var Fe,be,ve,he;const e=Be.c(113);let i,r,t,a,d;e[0]!==l?({open:a,queryRef:d,onReload:t,onCancel:r,...i}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=Ze(),[u,o]=Rl(),[m,c]=V.useState(),[f,g]=V.useState("-updatedAt"),[y,S]=Tl("schedulingHistoryExpandMode"),[p,h]=Tl("table_column_overrides.RouteSchedulingHistory");let F;e[6]===Symbol.for("react.memo_cache_sentinel")?(F={current:1,pageSize:10},e[6]=F):F=e[6];const{tablePaginationOption:b,setTablePaginationOption:x}=Tn(F),K=V.useDeferredValue(d),R=K!==d,A=Ke.usePreloadedQuery(Qt,K);let D;e[7]!==s?(D=s("route.RouteSchedulingHistory"),e[7]=s,e[8]=D):D=e[8];let $,q;e[9]===Symbol.for("react.memo_cache_sentinel")?($={maxWidth:1600},q={body:{minHeight:"80vh"}},e[9]=$,e[10]=q):($=e[9],q=e[10]);let L;e[11]!==t||e[12]!==d.variables||e[13]!==x?(L=ae=>{c(ae),x({current:1}),t({...d.variables,filter:ae,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=d.variables,e[13]=x,e[14]=L):L=e[14];let _;e[15]!==s?(_=s("route.ID"),e[15]=s,e[16]=_):_=e[16];let C;e[17]!==_?(C={key:"id",propertyLabel:_,type:"uuid",fixedOperator:"equals"},e[17]=_,e[18]=C):C=e[18];let M;e[19]!==s?(M=s("route.Phase"),e[19]=s,e[20]=M):M=e[20];let Q;e[21]!==M?(Q={key:"phase",propertyLabel:M,type:"string",fixedOperator:"contains"},e[21]=M,e[22]=Q):Q=e[22];let E;e[23]!==s?(E=s("route.Result"),e[23]=s,e[24]=E):E=e[24];let z;e[25]===Symbol.for("react.memo_cache_sentinel")?(z=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=z):z=e[25];let U;e[26]!==E?(U={key:"result",propertyLabel:E,type:"enum",strictSelection:!0,options:z},e[26]=E,e[27]=U):U=e[27];let G;e[28]!==s?(G=s("route.FromStatus"),e[28]=s,e[29]=G):G=e[29];let O;e[30]!==G?(O={key:"fromStatus",propertyLabel:G,type:"string",valueMode:"scalar"},e[30]=G,e[31]=O):O=e[31];let B;e[32]!==s?(B=s("route.ToStatus"),e[32]=s,e[33]=B):B=e[33];let k;e[34]!==B?(k={key:"toStatus",propertyLabel:B,type:"string",valueMode:"scalar"},e[34]=B,e[35]=k):k=e[35];let P;e[36]!==s?(P=s("route.ErrorCode"),e[36]=s,e[37]=P):P=e[37];let N;e[38]!==P?(N={key:"errorCode",propertyLabel:P,type:"string",fixedOperator:"contains"},e[38]=P,e[39]=N):N=e[39];let Y;e[40]!==s?(Y=s("route.Message"),e[40]=s,e[41]=Y):Y=e[41];let Z;e[42]!==Y?(Z={key:"message",propertyLabel:Y,type:"string",fixedOperator:"contains"},e[42]=Y,e[43]=Z):Z=e[43];let I;e[44]!==s?(I=s("route.CreatedAt"),e[44]=s,e[45]=I):I=e[45];let T;e[46]!==I?(T={key:"createdAt",propertyLabel:I,type:"datetime",defaultOperator:"after"},e[46]=I,e[47]=T):T=e[47];let j;e[48]!==s?(j=s("route.UpdatedAt"),e[48]=s,e[49]=j):j=e[49];let H;e[50]!==j?(H={key:"updatedAt",propertyLabel:j,type:"datetime",defaultOperator:"after"},e[50]=j,e[51]=H):H=e[51];let W;e[52]!==U||e[53]!==O||e[54]!==k||e[55]!==N||e[56]!==Z||e[57]!==T||e[58]!==H||e[59]!==C||e[60]!==Q?(W=[C,Q,U,O,k,N,Z,T,H],e[52]=U,e[53]=O,e[54]=k,e[55]=N,e[56]=Z,e[57]=T,e[58]=H,e[59]=C,e[60]=Q,e[61]=W):W=e[61];let ee;e[62]!==m||e[63]!==W||e[64]!==L?(ee=n.jsx(Gl,{value:m,onChange:L,filterProperties:W}),e[62]=m,e[63]=W,e[64]=L,e[65]=ee):ee=e[65];let X;e[66]!==t||e[67]!==d.variables||e[68]!==o?(X=ae=>{o(ae),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=o,e[69]=X):X=e[69];let le;e[70]!==u||e[71]!==R||e[72]!==X?(le=n.jsx(ie,{children:n.jsx(Ml,{value:u,onChange:X,loading:R,autoUpdateDelay:null})}),e[70]=u,e[71]=R,e[72]=X,e[73]=le):le=e[73];let w;e[74]!==ee||e[75]!==le?(w=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[ee,le]}),e[74]=ee,e[75]=le,e[76]=w):w=e[76];const te=y??void 0;let ue;e[77]!==p||e[78]!==h?(ue={columnOverrides:p,onColumnOverridesChange:h},e[77]=p,e[78]=h,e[79]=ue):ue=e[79];let ce;e[80]!==t||e[81]!==d.variables||e[82]!==x?(ce=ae=>{g(ae),x({current:1}),t({...d.variables,orderBy:Nl(ae),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=d.variables,e[82]=x,e[83]=ce):ce=e[83];const Re=((Fe=A.routeScopedSchedulingHistories)==null?void 0:Fe.count)??0;let ye;e[84]!==t||e[85]!==d.variables||e[86]!==x?(ye=(ae,Se)=>{x({current:ae,pageSize:Se}),t({...d.variables,limit:Se,offset:ae>1?(ae-1)*Se:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=d.variables,e[86]=x,e[87]=ye):ye=e[87];let oe;e[88]!==Re||e[89]!==ye||e[90]!==b.current||e[91]!==b.pageSize?(oe={pageSize:b.pageSize,current:b.current,total:Re,onChange:ye},e[88]=Re,e[89]=ye,e[90]=b.current,e[91]=b.pageSize,e[92]=oe):oe=e[92];let de;e[93]!==((be=A.routeScopedSchedulingHistories)==null?void 0:be.edges)?(de=hl((ve=A.routeScopedSchedulingHistories)==null?void 0:ve.edges,"node"),e[93]=(he=A.routeScopedSchedulingHistories)==null?void 0:he.edges,e[94]=de):de=e[94];let me;e[95]!==R||e[96]!==f||e[97]!==S||e[98]!==te||e[99]!==ue||e[100]!==ce||e[101]!==oe||e[102]!==de?(me=n.jsx(Ki,{resizable:!0,loading:R,expandMode:te,onExpandModeChange:S,tableSettings:ue,order:f,onChangeOrder:ce,pagination:oe,schedulingHistoryFrgmt:de}),e[95]=R,e[96]=f,e[97]=S,e[98]=te,e[99]=ue,e[100]=ce,e[101]=oe,e[102]=de,e[103]=me):me=e[103];let re;e[104]!==w||e[105]!==me?(re=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[w,me]}),e[104]=w,e[105]=me,e[106]=re):re=e[106];let fe;return e[107]!==i||e[108]!==r||e[109]!==a||e[110]!==D||e[111]!==re?(fe=n.jsx(_l,{title:D,open:a,width:"90%",style:$,styles:q,footer:null,onCancel:r,...i,children:re}),e[107]=i,e[108]=r,e[109]=a,e[110]=D,e[111]=re,e[112]=fe):fe=e[112],fe},wn=["TERMINATED","FAILED_TO_START"],as=l=>l==="terminated"?{status:{in:[...wn]}}:{status:{notIn:[...wn]}},dn=(l,e)=>({...l,...as(e)}),yn=["createdAt","id"],is=[...yn,...yn.map(l=>`-${l}`)],Bn=l=>hn(yn,l),un=l=>l??"NOT_CHECKED",ss=l=>{"use memo";const e=Be.c(21),{deploymentFrgmt:i,deploymentId:r,replicaFetchKey:t}=l,{t:a}=Ze(),{token:d}=Kl.useToken();let s;e[0]!==a?(s=a("deployment.tab.Replicas"),e[0]=a,e[1]=s):s=e[1];let u;e[2]!==a?(u=a("deployment.tab.description.Replicas"),e[2]=a,e[3]=u):u=e[3];let o;e[4]!==d.colorTextDescription?(o=n.jsx(vn,{style:{color:d.colorTextDescription}}),e[4]=d.colorTextDescription,e[5]=o):o=e[5];let m;e[6]!==u||e[7]!==o?(m=n.jsx(dl,{title:u,children:o}),e[6]=u,e[7]=o,e[8]=m):m=e[8];let c;e[9]!==s||e[10]!==m?(c=n.jsxs(ie,{gap:"xs",align:"center",children:[s,m]}),e[9]=s,e[10]=m,e[11]=c):c=e[11];let f;e[12]===Symbol.for("react.memo_cache_sentinel")?(f={body:{paddingTop:0}},e[12]=f):f=e[12];let g;e[13]===Symbol.for("react.memo_cache_sentinel")?(g=n.jsx(Sl,{active:!0}),e[13]=g):g=e[13];let y;e[14]!==i||e[15]!==r||e[16]!==t?(y=n.jsx(lt,{children:n.jsx(V.Suspense,{fallback:g,children:n.jsx(rs,{deploymentFrgmt:i,deploymentId:r,replicaFetchKey:t})})}),e[14]=i,e[15]=r,e[16]=t,e[17]=y):y=e[17];let S;return e[18]!==c||e[19]!==y?(S=n.jsx(Wl,{title:c,styles:f,children:y}),e[18]=c,e[19]=y,e[20]=S):S=e[20],S},rs=({deploymentFrgmt:l,deploymentId:e,replicaFetchKey:i})=>{"use memo";var U,G,O,B;const{t:r}=Ze(),[t,a]=V.useTransition(),[d,s]=Tl("table_column_overrides.DeploymentReplicasTab"),[u,o]=Kn({current:nn.withDefault(1),pageSize:nn.withDefault(10),order:Ul(is),rFilter:nt,rStatusCategory:Ul(["running","terminated"]).withDefault("running")},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rOrder",rFilter:"rFilter",rStatusCategory:"rStatusCategory"}});Ke.useFragment(Bt,l);const m=k=>{if(!k)return null;try{const P=JSON.parse(k);return P&&typeof P=="object"&&!Array.isArray(P)?P:null}catch{return null}},c=k=>!k||Object.keys(k).length===0?"":JSON.stringify(k),[f,g]=V.useState(()=>({filter:dn(u.rFilter?m(u.rFilter):null,u.rStatusCategory),orderBy:Nl(u.order||"-createdAt"),limit:u.pageSize,offset:u.current>1?(u.current-1)*u.pageSize:0})),[y,S]=V.useState(0),p=y===0&&(i===void 0||i===zl),F=Jn().supports("route-scheduling-history"),[b,x]=V.useState(!1),[K,R]=Ke.useQueryLoader(Qt),[A,D]=V.useState(null),[$,q]=V.useState(null),{deployment:L}=Ke.useLazyLoadQuery(wt,{deploymentId:e,...f},{fetchKey:`${y}-${i??""}`,fetchPolicy:p?"store-and-network":"network-only"}),_=((O=(G=(U=L==null?void 0:L.replicas)==null?void 0:U.edges)==null?void 0:G.map(k=>k==null?void 0:k.node))==null?void 0:O.filter(k=>!!k))??[],C=k=>{a(()=>{g(P=>({...P,...k}))})},M=[{label:r("replicaStatus.Active"),value:"ACTIVE"},{label:r("replicaStatus.Inactive"),value:"INACTIVE"}],Q=[{key:"trafficStatus",propertyLabel:r("deployment.TrafficStatus"),type:"enum",options:M,strictSelection:!0}],E=u.rFilter?m(u.rFilter)??void 0:void 0,z=tn([{key:"id",title:r("deployment.ReplicaId"),dataIndex:"id",fixed:"left",sorter:Bn("id"),render:k=>n.jsx(Ll,{globalId:k,copyable:!0})},{key:"status",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.ReplicaLifecycle"),n.jsx(gl,{title:r("deployment.ReplicaLifecycleStatusTooltip")})]}),dataIndex:"status",render:(k,P)=>n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx($n,{status:un(k)}),F&&n.jsx(dl,{title:r("route.RouteSchedulingHistory"),children:n.jsx(yl,{type:"link",icon:n.jsx(rt,{}),size:"small",style:{padding:0},action:async()=>{const N=jl(P.id)??P.id;R({scope:{routeId:N},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),x(!0)}})})]})},{key:"healthStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.HealthStatus"),n.jsx(gl,{title:r("deployment.HealthStatusTooltip")})]}),dataIndex:"healthStatus",render:(k,P)=>n.jsx($n,{status:un(k),showTooltip:un(P.status)!=="TERMINATED"})},{key:"trafficStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.TrafficStatus"),n.jsx(gl,{title:r("deployment.TrafficStatusTooltip")})]}),dataIndex:"trafficStatus",render:k=>n.jsx(ln,{color:k==="ACTIVE"?"success":"default",children:r(k==="ACTIVE"?"replicaStatus.Active":"replicaStatus.Inactive")})},{key:"session",title:r("general.Session"),onCell:()=>({style:{maxWidth:240}}),render:(k,P)=>{var Z;const N=P.sessionV2;if(!(N!=null&&N.id))return n.jsx(Xe.Text,{type:"secondary",children:"—"});const Y=(Z=N.metadata)==null?void 0:Z.name;return Y?n.jsxs(n.Fragment,{children:[n.jsx(La,{ellipsis:!0,onClick:()=>D(Ye(N.id)),style:{maxWidth:160},children:Y})," ",n.jsxs(Xe.Text,{type:"secondary",children:["(",n.jsx(Ll,{globalId:N.id,type:"secondary"}),")"]})]}):n.jsx(Ll,{globalId:N.id})}},{key:"revision",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.RevisionNumberWithID"),n.jsx(gl,{title:r("deployment.RevisionNumberTooltip")})]}),render:(k,P)=>{const N=P.revision;return N!=null&&N.id?n.jsxs(n.Fragment,{children:[n.jsx(Xe.Link,{onClick:()=>q(N),children:N.revisionNumber!=null?`#${N.revisionNumber}`:"-"})," ",n.jsxs(Xe.Text,{type:"secondary",children:["(",n.jsx(Ll,{globalId:N.id,type:"secondary"}),")"]})]}):n.jsx(Xe.Text,{type:"secondary",children:"—"})}},{key:"createdAt",title:r("deployment.CreatedAt"),dataIndex:"createdAt",sorter:Bn("createdAt"),render:k=>k?il(k).format("lll"):"-"}]);return n.jsxs(n.Fragment,{children:[n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:12},children:[n.jsxs(ie,{gap:"sm",align:"start",wrap:"wrap",style:{flexShrink:1},children:[n.jsx(ja,{value:u.rStatusCategory,onChange:k=>{const P=k.target.value,N=u.rFilter?m(u.rFilter):null;o({rStatusCategory:P,current:1}),C({filter:dn(N,P),offset:0})},options:[{label:r("deployment.Running"),value:"running"},{label:r("deployment.status.Terminated"),value:"terminated"}]}),n.jsx(Gl,{filterProperties:Q,value:E,onChange:k=>{const P=c(k);o({rFilter:P||null,current:1}),C({filter:dn(k??null,u.rStatusCategory),offset:0})}})]}),n.jsx(Ml,{loading:t,value:"",onChange:()=>{a(()=>S(k=>k+1))}})]}),n.jsx(Pl,{rowKey:k=>k.id,dataSource:_,columns:z,loading:t,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:d,onColumnOverridesChange:s},order:u.order,onChangeOrder:k=>{o({order:k??null}),C({orderBy:Nl(k||"-createdAt")})},pagination:{pageSize:u.pageSize,current:u.current,total:((B=L==null?void 0:L.replicas)==null?void 0:B.count)??0,onChange:(k,P)=>{o({current:k,pageSize:P});const N=k>1?(k-1)*P:0;C({limit:P,offset:N})}}}),n.jsx(pl,{children:n.jsx(Ga,{open:!!A,sessionId:A??void 0,onClose:()=>D(null)})}),n.jsx(pl,{children:n.jsx(sn,{open:!!$,revisionFrgmt:$,onClose:()=>q(null)})}),K!=null&&n.jsx(pl,{children:n.jsx(ts,{open:b,queryRef:K,onReload:R,onCancel:()=>x(!1)})})]})},qt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentCurrentRevisionTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionHistoryTab_deployment"}],type:"ModelDeployment",abstractKey:null};qt.hash="2a36e018f7a8b5999cad5c828ae16666";const os=l=>{"use memo";const e=Be.c(18),{deploymentId:i}=l,[r,t]=Ke.useQueryLoader(Za);let a;e[0]===Symbol.for("react.memo_cache_sentinel")?(a={current:1,pageSize:10},e[0]=a):a=e[0];const{baiPaginationOption:d,setTablePaginationOption:s}=Tn(a);let u;e[1]!==t||e[2]!==s?(u=(h,F)=>{const b=h.limit??10;s({pageSize:b,current:h.offset?Math.floor(h.offset/b)+1:1}),t(h,F)},e[1]=t,e[2]=s,e[3]=u):u=e[3];const o=u;let m;e[4]!==d.limit||e[5]!==d.offset||e[6]!==i||e[7]!==t?(m=()=>{t({scope:{entity:[{entityType:"MODEL_DEPLOYMENT",entityId:jl(i)??i}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:d.limit,offset:d.offset},{fetchPolicy:"store-and-network"})},e[4]=d.limit,e[5]=d.offset,e[6]=i,e[7]=t,e[8]=m):m=e[8];const c=m;let f;e[9]!==c?(f=()=>{c()},e[9]=c,e[10]=f):f=e[10];const g=V.useEffectEvent(f);let y;e[11]!==g?(y=()=>{g()},e[11]=g,e[12]=y):y=e[12];let S;e[13]!==i?(S=[i],e[13]=i,e[14]=S):S=e[14],V.useEffect(y,S);let p;return e[15]!==r||e[16]!==o?(p=n.jsx(lt,{children:r?n.jsx(V.Suspense,{fallback:n.jsx(Sl,{active:!0,paragraph:{rows:4}}),children:n.jsx(ei,{queryRef:r,onReload:o,tableSettings:{}})}):n.jsx(Sl,{active:!0,paragraph:{rows:4}})}),e[15]=r,e[16]=o,e[17]=p):p=e[17],p},zt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e=[l,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentCurrentRevisionTab_deployment",selections:[l,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:e,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:e,storageKey:null}],type:"ModelDeployment",abstractKey:null}}();zt.hash="81029f15aa0beb8289a21e0ca51303ff";const ds=l=>{"use memo";const e=Be.c(21),{deploymentFrgmt:i}=l,{t:r}=Ze(),{token:t}=Kl.useToken();let a;e[0]===Symbol.for("react.memo_cache_sentinel")?(a=zt,e[0]=a):a=e[0];const d=Ke.useFragment(a,i),[s,u]=V.useState(null);let o;e[1]===Symbol.for("react.memo_cache_sentinel")?(o=(A,D,$)=>{u({revisionFrgmt:A,status:D,title:$})},e[1]=o):o=e[1];const m=o,c=d==null?void 0:d.currentRevision,f=d==null?void 0:d.deployingRevision,g=!!f&&f.id!==(c==null?void 0:c.id);let y;e[2]!==f||e[3]!==g||e[4]!==r||e[5]!==t?(y=g&&n.jsx(bl,{type:"info",icon:n.jsx(Dn,{spin:!0}),showIcon:!0,style:{marginBottom:t.marginMD},title:r("deployment.ApplyingRevision",{revisionNumber:f.revisionNumber!=null?`#${f.revisionNumber}`:Ye(f.id)??""}),action:n.jsx(ul,{onClick:()=>m(f,"deploying",r("deployment.ApplyingRevisionDetail")),children:r("deployment.ViewRevision")})}),e[2]=f,e[3]=g,e[4]=r,e[5]=t,e[6]=y):y=e[6];let S;e[7]!==c||e[8]!==g||e[9]!==r?(S=c?n.jsx(Xa,{revisionFrgmt:c,status:"current"}):g?null:n.jsx(jn,{image:jn.PRESENTED_IMAGE_SIMPLE,description:r("deployment.NoCurrentRevisionDeployed")}),e[7]=c,e[8]=g,e[9]=r,e[10]=S):S=e[10];const p=s==null?void 0:s.revisionFrgmt,h=s==null?void 0:s.status,F=s==null?void 0:s.title,b=!!s;let x;e[11]===Symbol.for("react.memo_cache_sentinel")?(x=()=>u(null),e[11]=x):x=e[11];let K;e[12]!==p||e[13]!==h||e[14]!==F||e[15]!==b?(K=n.jsx(pl,{children:n.jsx(sn,{revisionFrgmt:p,status:h,title:F,open:b,onClose:x})}),e[12]=p,e[13]=h,e[14]=F,e[15]=b,e[16]=K):K=e[16];let R;return e[17]!==K||e[18]!==y||e[19]!==S?(R=n.jsxs(n.Fragment,{children:[y,S,K]}),e[17]=K,e[18]=y,e[19]=S,e[20]=R):R=e[20],R},Ut=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},a=[i,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],d={alias:null,args:null,kind:"ScalarField",name:"previousRevisionId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"activatedRevisionId",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},m=[u,o],c={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},g={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,u,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},y=[i,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[u,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},o,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[c,f,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},g],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[c,f,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},g],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,r,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:a,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:a,storageKey:null}],storageKey:null},d,s],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,r,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:y,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:y,storageKey:null}],storageKey:null},d,s],storageKey:null}]},params:{cacheID:"484c885f3fb5c0c9f4a4e12f257a49e6",id:null,metadata:{},name:"DeploymentRevisionHistoryTabActivateMutation",operationKind:"mutation",text:`mutation DeploymentRevisionHistoryTabActivateMutation(
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
`}}}();Ut.hash="153c096cf78b28827d7a04ef0f1610d4";const Wt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},g={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},S={alias:null,args:null,concreteType:"ModelMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[m,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},b=[y,F],x={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[m,y,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},R={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,s,{alias:null,args:u,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[m,c,f,g,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[y],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[y,S],storageKey:null}],storageKey:null},p,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[h,{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[m,y,{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,r],kind:"Operation",name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,s,{alias:null,args:u,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[m,c,f,g,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[y,m],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},F,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[y,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},m],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[y,S,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},p,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[h,x,K,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},R,{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:b,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[h,K,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},x],storageKey:null},p,R],storageKey:null}],storageKey:null}],storageKey:null},m],storageKey:null}]},params:{cacheID:"33ba9a0de55569323004cce82b1cc474",id:null,metadata:{},name:"DeploymentRevisionHistoryTabListQuery",operationKind:"query",text:`query DeploymentRevisionHistoryTabListQuery(
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
`}}}();Wt.hash="dc7544cf74c6e7b71663a4998c4d880c";const Gt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"}],type:"ModelDeployment",abstractKey:null};Gt.hash="6d00d8056ec0eba0eea404e554242adf";const Hn=["revisionNumber","createdAt","clusterMode","runtimeVariantName"],us=[...Hn,...Hn.map(l=>`-${l}`)],cs=({deploymentFrgmt:l,deploymentId:e,fetchKey:i})=>{"use memo";var Z;const{t:r}=Ze(),{token:t}=Kl.useToken(),{message:a}=Al.useApp(),{logger:d}=Vl(),[s,u]=V.useTransition(),[o,m]=V.useState(null),[c,f]=V.useState(null),[g,y]=V.useState(null),[S,p]=Tl("table_column_overrides.DeploymentRevisionHistoryTab"),[h,F]=Kn({current:nn.withDefault(1),pageSize:nn.withDefault(10),order:Ul(us),rvFilter:nt},{history:"replace",urlKeys:{current:"rvCurrent",pageSize:"rvPageSize",order:"rvOrder",rvFilter:"rvFilter"}}),b=Ke.useFragment(Gt,l),x=(Z=b==null?void 0:b.metadata)==null?void 0:Z.status,K=I=>{if(!I)return null;try{const T=JSON.parse(I);return T&&typeof T=="object"&&!Array.isArray(T)?T:null}catch{return null}},R=I=>!I||Object.keys(I).length===0?"":JSON.stringify(I),[A,D]=V.useState(()=>({filter:h.rvFilter?K(h.rvFilter):null,orderBy:Nl(h.order)??[{field:"REVISION_NUMBER",direction:"DESC"}],limit:h.pageSize,offset:h.current>1?(h.current-1)*h.pageSize:0})),[$,q]=Rl(),L=`${i??""}${$}`,_=(i===void 0||i===zl)&&$===zl,{deployment:C}=Ke.useLazyLoadQuery(Wt,{deploymentId:e,...A},{fetchKey:L,fetchPolicy:_?"store-and-network":"network-only"}),[M]=Ke.useMutation(Ut),Q=C==null?void 0:C.currentRevisionId,E=C==null?void 0:C.deployingRevisionId,z=C==null?void 0:C.revisionHistory,U=Dl(hl(z==null?void 0:z.edges,"node")),G=I=>{u(()=>{D(T=>({...T,...I}))})},O=()=>{u(()=>q())},B=I=>new Promise(T=>{m(I.id),M({variables:{input:{deploymentId:Ye(b.id),revisionId:Ye(I.id)}},onCompleted:(j,H)=>{var W;if(m(null),H&&H.length>0){d.error(H[0]),a.error(((W=H[0])==null?void 0:W.message)||r("general.ErrorOccurred")),T(!1);return}a.success(r("deployment.ApplySuccess",{revisionNumber:I.revisionNumber})),O(),T(!0)},onError:j=>{m(null),d.error(j),a.error((j==null?void 0:j.message)||r("general.ErrorOccurred")),T(!1)}})}),k=[{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.RevisionNumberWithID"),n.jsx(gl,{title:r("deployment.RevisionNumberTooltip")})]}),dataIndex:"revisionNumber",key:"revisionNumber",fixed:"left",sorter:!0,render:(I,T)=>{const j=Ye(T.id),H=j===Q,W=j===E,ee=H||W?r("deployment.ApplyDisabled"):void 0,X=H||W||kl(x)||o===T.id;return n.jsx(Fn,{title:n.jsxs(ie,{gap:"xs",align:"center",wrap:"nowrap",children:[n.jsx(Xe.Link,{onClick:()=>f({frgmt:T,status:H?"current":W?"deploying":"none"}),children:T.revisionNumber!=null?`#${T.revisionNumber}`:"-"}),n.jsxs(ie,{gap:0,align:"center",children:["(",n.jsx(Ll,{globalId:T.id}),")"]}),H?n.jsx(ln,{color:"success",children:r("deployment.Current")}):null,W&&!H?n.jsx(ln,{color:"warning",icon:n.jsx(Dn,{spin:!0}),children:r("deployment.Applying")}):null]}),showActions:"always",moreMenuDisabled:kl(x),actions:[{key:"deploy",title:r("deployment.Apply"),icon:n.jsx(Nn,{}),disabled:X,disabledReason:ee,popConfirm:{title:r("deployment.ApplyRevision"),description:r("deployment.ApplyConfirm",{revisionNumber:T.revisionNumber}),okText:r("deployment.Apply"),cancelText:r("button.Cancel"),okButtonProps:{danger:!0},onConfirm:()=>{B(T)}}},{key:"duplicate",title:r("deployment.AddNewRevisionFromThis"),icon:n.jsx(_n,{size:t.fontSize}),showInMenu:"always",disabled:kl(x),onClick:()=>{y(T)}}]})}},{title:r("general.CreatedAt"),dataIndex:"createdAt",key:"createdAt",sorter:!0,render:I=>I?il(I).format("lll"):"-"},{title:r("deployment.ModelVersion"),key:"modelVersion",defaultHidden:!0,render:(I,T)=>{var X,le,w;const j=(le=(X=T.modelDefinition)==null?void 0:X.models)==null?void 0:le[0];if(!j)return"-";const H=j.name??"-",W=(w=j.metadata)==null?void 0:w.version,ee=typeof W=="string"?W:W!=null?String(W):null;return ee?`${H} (${ee})`:H}},{title:r("deployment.RuntimeVariant"),key:"runtimeVariantName",dataIndex:"runtimeVariantName",sorter:!0,render:(I,T)=>{var j,H;return((H=(j=T.modelRuntimeConfig)==null?void 0:j.runtimeVariant)==null?void 0:H.name)??"-"}},{title:r("deployment.Image"),key:"image",defaultHidden:!0,render:(I,T)=>{var ee,X,le,w;const j=(X=(ee=T.imageV2)==null?void 0:ee.identity)==null?void 0:X.canonicalName,H=(w=(le=T.imageV2)==null?void 0:le.identity)==null?void 0:w.architecture,W=j&&H?`${j}@${H}`:j;return W?n.jsx(Cl,{copyable:{text:W},ellipsis:{tooltip:W},style:{maxWidth:180},children:W}):"-"}},{title:r("deployment.ModelFolder"),key:"modelFolder",defaultHidden:!0,render:(I,T)=>{var W,ee;const j=(W=T.modelMountConfig)==null?void 0:W.vfolder,H=(ee=T.modelMountConfig)==null?void 0:ee.vfolderId;return!j&&!H?"-":j?n.jsx(li,{vfolderNodeFragment:j}):n.jsx(Xe.Text,{type:"secondary",children:H})}},{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.ClusterMode"),n.jsx(gl,{title:r("deployment.ClusterModeTooltip")})]}),key:"clusterMode",dataIndex:"clusterMode",sorter:!0,render:(I,T)=>{var W,ee;const j=(W=T.clusterConfig)==null?void 0:W.mode,H=(ee=T.clusterConfig)==null?void 0:ee.size;return j==null&&H==null?"-":j==null?`${H}`:H==null?j:`${j} / ${H}`}}],P={message:r("general.InvalidUUID"),validate:I=>Pa(I.toLowerCase())},N=[{key:"revisionNumber",propertyLabel:r("deployment.RevisionNumber"),type:"number"},{key:"createdAt",propertyLabel:r("general.CreatedAt"),type:"datetime",operators:["after","before"],defaultOperator:"after"},{key:"clusterMode",propertyLabel:r("deployment.ClusterMode"),type:"string"},{key:"imageId",propertyLabel:r("deployment.Image"),type:"uuid",fixedOperator:"equals",rule:P},{key:"modelVfolderId",propertyLabel:r("deployment.ModelFolder"),type:"uuid",fixedOperator:"equals",rule:P}],Y=h.rvFilter?K(h.rvFilter)??void 0:void 0;return n.jsxs(n.Fragment,{children:[n.jsx(pl,{children:n.jsx(sn,{revisionFrgmt:c==null?void 0:c.frgmt,status:c==null?void 0:c.status,open:!!c,onClose:()=>f(null),extra:c?n.jsxs(ql.Compact,{children:[n.jsx(Na,{title:r("deployment.ApplyRevision"),description:r("deployment.ApplyConfirm",{revisionNumber:c.frgmt.revisionNumber}),okText:r("deployment.Apply"),cancelText:r("button.Cancel"),okButtonProps:{danger:!0},onConfirm:async()=>{await B(c.frgmt)&&f(null)},children:n.jsx(yl,{type:"primary",icon:n.jsx(Nn,{}),disabled:c.status==="current"||c.status==="deploying"||kl(x)||!!o,children:r("deployment.Apply")})}),n.jsx(et,{trigger:["click"],menu:{items:[{key:"duplicate",label:r("deployment.AddNewRevisionFromThis"),icon:n.jsx(_n,{size:t.fontSize}),disabled:kl(x),onClick:()=>{const I=c.frgmt;f(null),y(I)}}]},children:n.jsx(yl,{type:"primary",icon:n.jsx(Zn,{}),"aria-label":r("button.More"),disabled:kl(x)})})]}):void 0})}),n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:t.marginSM},wrap:"wrap",children:[n.jsx(Gl,{filterProperties:N,value:Y,onChange:I=>{const T=R(I),j=K(T||null);F({rvFilter:T||null,current:1}),G({filter:j,offset:0})}}),n.jsx(Ml,{loading:s,value:"",onChange:()=>O()})]}),n.jsx(Pl,{rowKey:"id",dataSource:U,columns:k,loading:s,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:S,onColumnOverridesChange:p},order:h.order??void 0,onChangeOrder:I=>{F({order:I??null}),G({orderBy:Nl(I||"-revisionNumber")})},pagination:{pageSize:h.pageSize,current:h.current,total:(z==null?void 0:z.count)??0,showSizeChanger:!0,onChange:(I,T)=>{const j=I>1?(I-1)*T:0;F({current:I,pageSize:T}),G({limit:T,offset:j})}}}),n.jsx(V.Suspense,{fallback:null,children:n.jsx(pl,{children:n.jsx(Dt,{open:!!g,deploymentFrgmt:b,sourceRevisionFrgmt:g,onRequestClose:I=>{y(null),I&&O()}})})})]})},ms=l=>{"use memo";const e=Be.c(49),{deploymentFrgmt:i,revisionFetchKey:r,onAddRevision:t,revisionCardRef:a,isAddRevisionDisabled:d}=l,s=d===void 0?!1:d,{t:u}=Ze();let o;e[0]===Symbol.for("react.memo_cache_sentinel")?(o=qt,e[0]=o):o=e[0];const m=Ke.useFragment(o,i);let c;e[1]===Symbol.for("react.memo_cache_sentinel")?(c=Ul(["currentRevision","revisionHistory","auditLog"]).withDefault("currentRevision"),e[1]=c):c=e[1];let f;e[2]===Symbol.for("react.memo_cache_sentinel")?(f={...c,history:"replace",scroll:!1},e[2]=f):f=e[2];const[g,y]=Va("revisionTab",f);let S;e[3]!==y?(S=Q=>{(Q==="currentRevision"||Q==="revisionHistory"||Q==="auditLog")&&y(Q)},e[3]=y,e[4]=S):S=e[4];let p;e[5]!==u?(p=u("deployment.CurrentRevision"),e[5]=u,e[6]=p):p=e[6];let h;e[7]!==p?(h={key:"currentRevision",label:p},e[7]=p,e[8]=h):h=e[8];let F;e[9]!==u?(F=u("deployment.RevisionHistory"),e[9]=u,e[10]=F):F=e[10];let b;e[11]!==F?(b={key:"revisionHistory",label:F},e[11]=F,e[12]=b):b=e[12];let x;e[13]!==u?(x=u("auditLog.AuditLog"),e[13]=u,e[14]=x):x=e[14];let K;e[15]!==x?(K={key:"auditLog",label:x},e[15]=x,e[16]=K):K=e[16];let R;e[17]!==K||e[18]!==h||e[19]!==b?(R=[h,b,K],e[17]=K,e[18]=h,e[19]=b,e[20]=R):R=e[20];let A;e[21]===Symbol.for("react.memo_cache_sentinel")?(A=n.jsx(Il,{}),e[21]=A):A=e[21];let D;e[22]!==t?(D=async()=>{t()},e[22]=t,e[23]=D):D=e[23];let $;e[24]!==u?($=u("deployment.AddRevision"),e[24]=u,e[25]=$):$=e[25];let q;e[26]!==s||e[27]!==D||e[28]!==$?(q=n.jsx(ie,{gap:"xs",align:"center",children:n.jsx(yl,{type:"primary",icon:A,disabled:s,action:D,children:$})}),e[26]=s,e[27]=D,e[28]=$,e[29]=q):q=e[29];let L;e[30]!==g||e[31]!==m?(L=g==="currentRevision"&&n.jsx(ds,{deploymentFrgmt:m}),e[30]=g,e[31]=m,e[32]=L):L=e[32];let _;e[33]!==g||e[34]!==m||e[35]!==r?(_=g==="revisionHistory"&&m&&n.jsx(Gn,{children:n.jsx(V.Suspense,{fallback:n.jsx(Sl,{active:!0,paragraph:{rows:4}}),children:n.jsx(cs,{deploymentFrgmt:m,deploymentId:m.id,fetchKey:r})})}),e[33]=g,e[34]=m,e[35]=r,e[36]=_):_=e[36];let C;e[37]!==g||e[38]!==m?(C=g==="auditLog"&&m&&n.jsx(os,{deploymentId:m.id}),e[37]=g,e[38]=m,e[39]=C):C=e[39];let M;return e[40]!==g||e[41]!==a||e[42]!==R||e[43]!==q||e[44]!==L||e[45]!==_||e[46]!==C||e[47]!==S?(M=n.jsxs(Wl,{ref:a,activeTabKey:g,onTabChange:S,tabList:R,tabBarExtraContent:q,children:[L,_,C]}),e[40]=g,e[41]=a,e[42]=R,e[43]=q,e[44]=L,e[45]=_,e[46]=C,e[47]=S,e[48]=M):M=e[48],M},Yt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"projectId"}],e=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"projectId"}],concreteType:"GroupNode",kind:"LinkedField",name:"group_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SwitchToProjectButtonQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SwitchToProjectButtonQuery",selections:e},params:{cacheID:"d9b043a52eacadb018a0097fe3c1f3c2",id:null,metadata:{},name:"SwitchToProjectButtonQuery",operationKind:"query",text:`query SwitchToProjectButtonQuery(
  $projectId: String!
) {
  group_node(id: $projectId) @since(version: "24.03.0") {
    id
    name
  }
}
`}}}();Yt.hash="4618e2aed2bc3c75a1d0a91f0b01c28c";const gs=l=>{"use memo";const e=Be.c(20);let i,r;e[0]!==l?({projectId:r,...i}=l,e[0]=l,e[1]=i,e[2]=r):(i=e[1],r=e[2]);const{t}=Ze(),a=_a(),[d,s]=V.useTransition();let u;e[3]===Symbol.for("react.memo_cache_sentinel")?(u=Yt,e[3]=u):u=e[3];let o;e[4]!==r?(o=Ql("GroupNode",r),e[4]=r,e[5]=o):o=e[5];let m;e[6]!==o?(m={projectId:o},e[6]=o,e[7]=m):m=e[7];const{group_node:c}=Ke.useLazyLoadQuery(u,m);let f;e[8]!==(c==null?void 0:c.id)||e[9]!==(c==null?void 0:c.name)||e[10]!==a?(f=()=>{const h=Ye((c==null?void 0:c.id)||""),F=c==null?void 0:c.name;h&&F&&s(()=>{a({projectId:h,projectName:F})})},e[8]=c==null?void 0:c.id,e[9]=c==null?void 0:c.name,e[10]=a,e[11]=f):f=e[11];const g=f,y=c==null?void 0:c.name;let S;e[12]!==t||e[13]!==y?(S=t("modelService.SwitchToProject",{projectName:y}),e[12]=t,e[13]=y,e[14]=S):S=e[14];let p;return e[15]!==i||e[16]!==g||e[17]!==d||e[18]!==S?(p=n.jsx(yl,{type:"link",size:"small",loading:d,onClick:g,...i,children:S}),e[15]=i,e[16]=g,e[17]=d,e[18]=S,e[19]=p):p=e[19],p},ps=l=>n.jsx(V.Suspense,{fallback:n.jsx(yl,{type:"link",size:"small",loading:!0}),children:n.jsx(gs,{...l})}),ys=5e3,_s=()=>{"use memo";var Qe,We,qe,ze,Je,De,$e,tl,Ae,Ue;const l=Be.c(114),{t:e}=Ze(),{token:i}=Kl.useToken(),[r]=Yn(),t=an(),a=Rn(),d=Un();let s;l[0]!==((Qe=a==null?void 0:a._config)==null?void 0:Qe.blockList)?(s=(qe=(We=a==null?void 0:a._config)==null?void 0:We.blockList)==null?void 0:qe.includes("chat"),l[0]=(ze=a==null?void 0:a._config)==null?void 0:ze.blockList,l[1]=s):s=l[1];const u=!!s,{deploymentId:o}=Ea(),m=o??"";let c;l[2]!==m?(c=Ql("ModelDeployment",m),l[2]=m,l[3]=c):c=l[3];const f=c,[g,y]=V.useTransition(),[S,p]=Rl(),[h,F]=Rl(),[b,x]=Rl(),[K,R]=Pn(!1),{setLeft:A,setRight:D}=R,[$,q]=Pn(!1),{setLeft:L,setRight:_}=q,C=V.useRef(null),M=V.useRef(null),[Q,E]=V.useState(null);let z;l[4]===Symbol.for("react.memo_cache_sentinel")?(z=yt,l[4]=z):z=l[4];let U;l[5]!==f?(U={deploymentId:f},l[5]=f,l[6]=U):U=l[6];const G=S===zl?"store-and-network":"network-only";let O;l[7]!==S||l[8]!==G?(O={fetchKey:S,fetchPolicy:G},l[7]=S,l[8]=G,l[9]=O):O=l[9];const{deployment:B}=Ke.useLazyLoadQuery(z,U,O);if(!B.ok){const Le=B.errors;if(Le.some(ks)){let nl;return l[10]===Symbol.for("react.memo_cache_sentinel")?(nl=n.jsx(fs,{}),l[10]=nl):nl=l[10],nl}const Ge=Le.map(Ss).filter(Boolean),sl=new Error(Ge.join("; ")||"DeploymentDetailPageQuery failed.");throw sl.errors=Le,sl}const k=B.value,P=k.metadata.name,N=k.metadata.status,Y=N==="READY",Z=k.metadata.projectId??null,I=!!Z&&Z!==d.id,T=!k.currentRevision&&!k.deployingRevision,j=!!k.deployingRevision&&k.deployingRevision.id!==((Je=k.currentRevision)==null?void 0:Je.id),H=!!k.networkAccess.endpointUrl,W=(((De=k.accessTokens)==null?void 0:De.count)??0)>0;let ee;l[11]!==N?(ee=kl(N),l[11]=N,l[12]=ee):ee=l[12];const X=ee,le=((($e=k.replicaState)==null?void 0:$e.desiredReplicaCount)??0)===0,w=!le&&(((tl=k.runningReplicas)==null?void 0:tl.count)??0)===0,te=le||w,ue=k.networkAccess.openToPublic===!1&&!X&&H&&!W,ce=((Ue=(Ae=k.creator)==null?void 0:Ae.basicInfo)==null?void 0:Ue.email)??null,Re=!ce||ce===r.email;let ye;l[13]!==p?(ye=()=>{y(()=>p())},l[13]=p,l[14]=ye):ye=l[14];const oe=ye;let de;l[15]!==A||l[16]!==i||l[17]!==p||l[18]!==x||l[19]!==F?(de=(Le,ll)=>{var Ge;A(),Le&&(ll&&E(ll),y(()=>{p(),F(),x()}),C.current&&(C.current.style.scrollMarginTop=`${((Ge=i.Layout)==null?void 0:Ge.headerHeight)??60}px`,C.current.scrollIntoView({behavior:"smooth",block:"start"})))},l[15]=A,l[16]=i,l[17]=p,l[18]=x,l[19]=F,l[20]=de):de=l[20];const me=de;let re;l[21]!==le||l[22]!==w||l[23]!==e?(re=()=>{if(le)return n.jsx(bl,{type:"warning",showIcon:!0,title:e("deployment.NoDesiredReplicas")});if(w)return n.jsx(bl,{type:"warning",showIcon:!0,title:e("deployment.NoRunningReplicas")})},l[21]=le,l[22]=w,l[23]=e,l[24]=re):re=l[24];const fe=re;let Fe;l[25]!==Z||l[26]!==I||l[27]!==e?(Fe=I&&Z&&n.jsx(bl,{type:"warning",showIcon:!0,title:e("deployment.NotInProject"),action:n.jsx(ps,{projectId:Z})}),l[25]=Z,l[26]=I,l[27]=e,l[28]=Fe):Fe=l[28];let be;l[29]!==fe||l[30]!==te||l[31]!==T||l[32]!==X?(be=te&&!T&&!X&&fe(),l[29]=fe,l[30]=te,l[31]=T,l[32]=X,l[33]=be):be=l[33];let ve;l[34]!==m||l[35]!==te||l[36]!==T||l[37]!==u||l[38]!==Y||l[39]!==e||l[40]!==i||l[41]!==t?(ve=Y&&!T&&!te&&n.jsx(bl,{type:"success",showIcon:!0,title:e("deployment.DeploymentReady"),action:!u&&n.jsx(ul,{type:"primary",icon:n.jsx(Oa,{size:i.fontSizeLG}),onClick:()=>{t({pathname:"/chat",search:new URLSearchParams({endpointId:m}).toString()})},children:e("deployment.StartChatTest")})}),l[34]=m,l[35]=te,l[36]=T,l[37]=u,l[38]=Y,l[39]=e,l[40]=i,l[41]=t,l[42]=ve):ve=l[42];let he;l[43]!==N||l[44]!==T||l[45]!==I||l[46]!==D||l[47]!==e?(he=T&&!I&&!kl(N)&&n.jsx(bl,{type:"warning",showIcon:!0,title:e("deployment.NoCurrentRevisionDeployed"),action:n.jsx(yl,{type:"primary",icon:n.jsx(Il,{}),action:async()=>{D()},children:e("deployment.AddRevision")})}),l[43]=N,l[44]=T,l[45]=I,l[46]=D,l[47]=e,l[48]=he):he=l[48];let ae;l[49]!==X||l[50]!==ue||l[51]!==_||l[52]!==e?(ae=ue&&n.jsx(bl,{type:"info",showIcon:!0,title:e("deployment.PrivateDeploymentAlertTitle"),action:n.jsx(yl,{type:"primary",icon:n.jsx(Il,{}),action:async()=>{_()},disabled:X,children:e("deployment.AddAccessToken")})}),l[49]=X,l[50]=ue,l[51]=_,l[52]=e,l[53]=ae):ae=l[53];let Se;l[54]===Symbol.for("react.memo_cache_sentinel")?(Se={margin:0},l[54]=Se):Se=l[54];let Ee;l[55]!==P?(Ee=n.jsx(Xe.Title,{level:3,style:Se,children:P}),l[55]=P,l[56]=Ee):Ee=l[56];let Ce;l[57]!==N?(Ce=n.jsx(ot,{status:N}),l[57]=N,l[58]=Ce):Ce=l[58];let Te;l[59]!==Ee||l[60]!==Ce?(Te=n.jsxs(ie,{direction:"row",align:"center",gap:"sm",children:[Ee,Ce]}),l[59]=Ee,l[60]=Ce,l[61]=Te):Te=l[61];const we=j?ys:null;let v;l[62]!==k||l[63]!==oe||l[64]!==g||l[65]!==we?(v=n.jsx(es,{deploymentFrgmt:k,isPendingRefetch:g,onRefetch:oe,autoUpdateDelay:we}),l[62]=k,l[63]=oe,l[64]=g,l[65]=we,l[66]=v):v=l[66];const J=X||I;let ne;l[67]!==k||l[68]!==D||l[69]!==h||l[70]!==J?(ne=n.jsx(ms,{deploymentFrgmt:k,revisionFetchKey:h,onAddRevision:D,revisionCardRef:C,isAddRevisionDisabled:J}),l[67]=k,l[68]=D,l[69]=h,l[70]=J,l[71]=ne):ne=l[71];let se;l[72]!==k||l[73]!==f||l[74]!==b?(se=n.jsx(ss,{deploymentFrgmt:k,deploymentId:f,replicaFetchKey:b}),l[72]=k,l[73]=f,l[74]=b,l[75]=se):se=l[75];let ge;l[76]!==k?(ge=n.jsx(Gi,{deploymentFrgmt:k}),l[76]=k,l[77]=ge):ge=l[77];let ke;l[78]!==L||l[79]!==_?(ke=Le=>{Le?_():L()},l[78]=L,l[79]=_,l[80]=ke):ke=l[80];let Pe;l[81]!==oe||l[82]!==i?(Pe=()=>{var Le;oe(),M.current&&(M.current.style.scrollMarginTop=`${((Le=i.Layout)==null?void 0:Le.headerHeight)??60}px`,M.current.scrollIntoView({behavior:"smooth",block:"start"}))},l[81]=oe,l[82]=i,l[83]=Pe):Pe=l[83];let Me;l[84]!==$||l[85]!==k||l[86]!==f||l[87]!==X||l[88]!==Re||l[89]!==ke||l[90]!==Pe?(Me=n.jsx(Ti,{cardRef:M,deploymentFrgmt:k,deploymentId:f,isOwnedByCurrentUser:Re,isDeploymentDestroying:X,isCreateModalOpen:$,onCreateModalOpenChange:ke,onTokenCreated:Pe}),l[84]=$,l[85]=k,l[86]=f,l[87]=X,l[88]=Re,l[89]=ke,l[90]=Pe,l[91]=Me):Me=l[91];let Oe;l[92]!==K||l[93]!==k||l[94]!==me?(Oe=n.jsx(pl,{children:n.jsx(Dt,{open:K,onRequestClose:me,deploymentFrgmt:k})}),l[92]=K,l[93]=k,l[94]=me,l[95]=Oe):Oe=l[95];const _e=!!Q;let He;l[96]===Symbol.for("react.memo_cache_sentinel")?(He=()=>E(null),l[96]=He):He=l[96];let xe;l[97]!==Q||l[98]!==_e?(xe=n.jsx(pl,{children:n.jsx(sn,{revisionFrgmt:Q,open:_e,onClose:He})}),l[97]=Q,l[98]=_e,l[99]=xe):xe=l[99];let el;return l[100]!==Fe||l[101]!==be||l[102]!==ve||l[103]!==he||l[104]!==ae||l[105]!==Te||l[106]!==v||l[107]!==ne||l[108]!==se||l[109]!==ge||l[110]!==Me||l[111]!==Oe||l[112]!==xe?(el=n.jsxs(ie,{direction:"column",align:"stretch",gap:"md",children:[Fe,be,ve,he,ae,Te,v,ne,se,ge,Me,Oe,xe]}),l[100]=Fe,l[101]=be,l[102]=ve,l[103]=he,l[104]=ae,l[105]=Te,l[106]=v,l[107]=ne,l[108]=se,l[109]=ge,l[110]=Me,l[111]=Oe,l[112]=xe,l[113]=el):el=l[113],el},fs=()=>{"use memo";const l=Be.c(39),{t:e}=Ze(),i=an(),{firstAvailableMenuItem:r}=$a();let t;l[0]!==r?(t=r?wa(r.key):"/start",l[0]=r,l[1]=t):t=l[1];const a=t;let d,s,u,o,m,c,f,g,y,S,p;if(l[2]!==a||l[3]!==(r==null?void 0:r.labelText)||l[4]!==e||l[5]!==i){const x=(r==null?void 0:r.labelText)??e("webui.menu.FirstPageNameAlias");u=ie,l[17]===Symbol.for("react.memo_cache_sentinel")?(y={margin:"auto"},l[17]=y):y=l[17],S="center",p="center",s=Ba,f="warning",l[18]!==e?(g=e("deployment.NotAccessibleOrDeleted"),l[18]=e,l[19]=g):g=l[19],d=ul,o="primary",l[20]!==a||l[21]!==i?(m=()=>{i(a)},l[20]=a,l[21]=i,l[22]=m):m=l[22],c=e("button.GoBackToStartPage",{title:x}),l[2]=a,l[3]=r==null?void 0:r.labelText,l[4]=e,l[5]=i,l[6]=d,l[7]=s,l[8]=u,l[9]=o,l[10]=m,l[11]=c,l[12]=f,l[13]=g,l[14]=y,l[15]=S,l[16]=p}else d=l[6],s=l[7],u=l[8],o=l[9],m=l[10],c=l[11],f=l[12],g=l[13],y=l[14],S=l[15],p=l[16];let h;l[23]!==d||l[24]!==o||l[25]!==m||l[26]!==c?(h=n.jsx(d,{type:o,onClick:m,children:c}),l[23]=d,l[24]=o,l[25]=m,l[26]=c,l[27]=h):h=l[27];let F;l[28]!==s||l[29]!==f||l[30]!==g||l[31]!==h?(F=n.jsx(s,{status:f,title:g,extra:h}),l[28]=s,l[29]=f,l[30]=g,l[31]=h,l[32]=F):F=l[32];let b;return l[33]!==u||l[34]!==F||l[35]!==y||l[36]!==S||l[37]!==p?(b=n.jsx(u,{style:y,justify:S,align:p,children:F}),l[33]=u,l[34]=F,l[35]=y,l[36]=S,l[37]=p,l[38]=b):b=l[38],b};function ks(l){return/Insufficient permission/i.test((l==null?void 0:l.message)??"")}function Ss(l){return(l==null?void 0:l.message)??""}export{_s as default};
//# sourceMappingURL=DeploymentDetailPage-BxgGb0qy.js.map
