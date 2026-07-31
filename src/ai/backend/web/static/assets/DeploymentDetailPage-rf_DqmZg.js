import{bS as Un,i as Ue,ag as kn,r as j,aE as mn,cr as la,au as Il,db as Wn,b9 as Bl,k as Ke,cs as na,ac as Fl,bV as ta,af as Sn,bi as Mn,j as n,az as vl,b7 as aa,cu as ia,bz as ql,V as Ze,p as hn,cf as sa,ct as ra,b0 as oa,a7 as tn,aN as Al,b5 as El,bU as dl,bM as jl,a9 as vn,u as ll,t as Dl,A as Pl,E as Ol,P as Gn,cg as Fn,T as el,aq as cl,B as ie,aD as wl,b4 as Ll,K as kl,bJ as Yl,v as fl,X as $l,F as ge,dc as da,aZ as bn,a_ as xn,b8 as Rn,aT as gn,ax as Wl,an as Yn,dd as ua,a as Kn,aa as Cl,de as zl,bh as Tl,s as ml,df as ca,G as Ul,cj as ma,b3 as Ln,aK as jn,J as Hl,bq as gl,aS as Pn,dg as ga,dh as ya,di as pa,dj as fa,dk as Vl,dl as ka,a1 as Sa,dm as ha,ad as va,bn as Nn,dn as Jl,bB as Zl,N as Xn,dp as Fa,cN as Jn,bg as ba,m as xa,aI as Ra,cE as Ka,U as Ta,ab as Ia,dq as Da,ch as Ql,ck as pl,f as en,b_ as Zn,a6 as Ca,bt as Gl,a4 as Tn,aY as Aa,c0 as In,bY as _l,w as an,x as Dn,cV as et,dr as lt,M as nt,da as Ma,D as La,bT as ln,bW as Cn,bI as tt,a5 as at,ds as nn,cQ as ja,c2 as Pa,bX as Na,am as Vn,d3 as _n,c3 as Va,dt as _a,aL as Ea,du as Oa,dv as wa,o as En,a2 as $a,dw as Ba,dx as Ha,dy as Qa,dz as qa,dA as za}from"./index-DB7yUW94.js";import{f as Ua,t as Wa}from"./parseCliCommand-DLNI3aPC.js";import{R as Ga,b as Ya}from"./RuntimeParameterFormSection-ClTo0JKf.js";import{B as On}from"./BAIVFolderSelect-BotbTtRC.js";import{P as Xa}from"./PrometheusQueryTemplatePreview-DGwR5cK6.js";import{B as it,n as st,u as rt,a as ot,o as Ja,R as dt,S as Za}from"./SessionDetailDrawer-3BikG1o_.js";import{S as ut}from"./square-pen-BbLd2-Yf.js";import{i as hl,a as ct,B as ei,D as sn,b as li}from"./DeploymentRevisionDetailDrawer-d0xOqlsg.js";import{B as Xl}from"./BAIGraphQLPropertyFilter-URVW9R-R.js";import{B as Nl}from"./BAIId-DEscoFqK.js";import{B as ni}from"./BooleanTag-UCS-BJYP.js";import{S as ti,a as ai}from"./ScopedAuditLog-BgqNEK4R.js";import{F as ii}from"./FolderLink-DJPzhdHs.js";import"./UndoOutlined-01DfyQbh.js";import"./corner-down-left-YcyydeqR.js";import"./zip-DRoFeMJl.js";import"./unzip-kgVO-3Vy.js";import"./union-CChSQL5X.js";import"./WarningOutlined-BN1g72Bn.js";import"./camelCase-D3Ek1WIG.js";/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const si=[["line",{x1:"15",x2:"15",y1:"12",y2:"18",key:"1p7wdc"}],["line",{x1:"12",x2:"18",y1:"15",y2:"15",key:"1nscbv"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2",key:"17jyea"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",key:"zix9uf"}]],wn=Un("copy-plus",si);/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ri=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",key:"usdka0"}]],$n=Un("folder-open",ri),mt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},r=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"NAME"}]}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e,i],kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectPaginatedQuery",selections:r,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[i,e,l],kind:"Operation",name:"BAIRuntimeVariantSelectPaginatedQuery",selections:r},params:{cacheID:"e8d20623434b823880b9543cf3297c3f",id:null,metadata:{},name:"BAIRuntimeVariantSelectPaginatedQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectPaginatedQuery(
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
`}}})();mt.hash="65da05baef2fee7bd3840fc61e39a8d8";const gt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"},{defaultValue:null,kind:"LocalArgument",name:"skip"}],e=[{condition:"skip",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectValueQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIRuntimeVariantSelectValueQuery",selections:e},params:{cacheID:"f029b9c8b12e9bc799f1ff1caaebd031",id:null,metadata:{},name:"BAIRuntimeVariantSelectValueQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectValueQuery(
  $id: UUID!
  $skip: Boolean!
) {
  runtimeVariant(id: $id) @skip(if: $skip) {
    id
    name
  }
}
`}}})();gt.hash="f7c1435633aeb06ecc9eafe324f06550";const oi=l=>{"use memo";var je;const e=Ue.c(74);let i,r,t,a;e[0]!==l?({loading:i,onResolvedNamesChange:r,ref:t,...a}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a):(i=e[1],r=e[2],t=e[3],a=e[4]);const{t:d}=kn(),s=j.useRef(null),[c,o]=mn(a);let g;e[5]===Symbol.for("react.memo_cache_sentinel")?(g={valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"},e[5]=g):g=e[5];const[u,S]=mn(a,g),m=j.useDeferredValue(u),[y,f]=j.useState(),p=la(y),[k,b]=j.useOptimistic(y),[x,F]=j.useTransition(),[T,R]=Il(),D=j.useDeferredValue(T),C=j.useDeferredValue(c);let $;e[6]!==C?($=C?Wn(Bl(C)):"",e[6]=C,e[7]=$):$=e[7];const z=$;let P;e[8]===Symbol.for("react.memo_cache_sentinel")?(P=gt,e[8]=P):P=e[8];const B=!z;let O;e[9]!==z||e[10]!==B?(O={id:z,skip:B},e[9]=z,e[10]=B,e[11]=O):O=e[11];const I=z?"store-or-network":"store-only";let w;e[12]!==D||e[13]!==I?(w={fetchPolicy:I,fetchKey:D},e[12]=D,e[13]=I,e[14]=w):w=e[14];const{runtimeVariant:N}=Ke.useLazyLoadQuery(P,O,w);let G;e[15]!==p?(G=p?{name:{iContains:p}}:null,e[15]=p,e[16]=G):G=e[16];const W=G;let Q,H;e[17]===Symbol.for("react.memo_cache_sentinel")?(H=mt,Q={limit:20},e[17]=Q,e[18]=H):(Q=e[17],H=e[18]);let V;e[19]!==W?(V={filter:W},e[19]=W,e[20]=V):V=e[20];const K=m?"network-only":"store-only";let M;e[21]!==D||e[22]!==K?(M={fetchPolicy:K,fetchKey:D},e[21]=D,e[22]=K,e[23]=M):M=e[23];let _;e[24]===Symbol.for("react.memo_cache_sentinel")?(_={getTotal:di,getItem:ci,getId:mi},e[24]=_):_=e[24];const{paginationData:Y,result:ne,loadNext:A,isLoadingNext:v}=na(H,Q,V,M,_);let E,L;e[25]!==R?(E=()=>({refetch:()=>{F(()=>{R()})}}),L=[R,F],e[25]=R,e[26]=E,e[27]=L):(E=e[26],L=e[27]),j.useImperativeHandle(t,E,L);let U;e[28]!==r||e[29]!==Y||e[30]!==N?(U=()=>{if(!r)return;const Ce={};if(N!=null&&N.id&&N.name){const Me=Ze(N.id);Me&&(Ce[Me]=N.name)}for(const Me of Y??[])if(Me!=null&&Me.id&&Me.name){const Pe=Ze(Me.id);Pe&&(Ce[Pe]=Me.name)}hn(Ce)||r(Ce)},e[28]=r,e[29]=Y,e[30]=N,e[31]=U):U=e[31];const Z=j.useEffectEvent(U);let J;e[32]!==Z?(J=()=>{Z()},e[32]=Z,e[33]=J):J=e[33];let ee;e[34]!==Y||e[35]!==N?(ee=[N,Y],e[34]=Y,e[35]=N,e[36]=ee):ee=e[36],j.useEffect(J,ee);let q;e[37]!==Y?(q=Fl(Y,gi),e[37]=Y,e[38]=q):q=e[38];const te=q,ye=N==null?void 0:N.name;let de;e[39]!==C||e[40]!==ye?(de=C?{label:ye??Bl(C),value:Bl(C)}:void 0,e[39]=C,e[40]=ye,e[41]=de):de=e[41];const pe=de,[ue,fe]=j.useState(pe);let se;e[42]!==d?(se=d("comp:BAIRuntimeVariantSelect.SelectRuntimeVariant"),e[42]=d,e[43]=se):se=e[43];const ce=i||c!==C||y!==p||x;let re;e[44]!==a||e[45]!==b?(re=async Ce=>{var Me;b(Ce),f(Ce),await((Me=a.searchAction)==null?void 0:Me.call(a,Ce))},e[44]=a,e[45]=b,e[46]=re):re=e[46];let ke;e[47]!==k||e[48]!==a.showSearch?(ke=a.showSearch===!1?!1:{searchValue:k,autoClearSearchValue:!0,...ta(a.showSearch)?Sn(a.showSearch,["searchValue"]):{},filterOption:!1},e[47]=k,e[48]=a.showSearch,e[49]=ke):ke=e[49];const Re=c!==C?ue:pe;let Fe;e[50]!==te||e[51]!==o?(Fe=(Ce,Me)=>{var h;if(Mn(Ce)||sa(Ce)){fe(void 0),o(void 0,Me);return}const Pe=ra(Ce)[0],Je={label:oa(Pe.label)?Pe.label:((h=te.find(X=>X.value===Pe.value))==null?void 0:h.label)??Bl(Pe.value),value:Bl(Pe.value)};fe(Je),o(Je.value,Me)},e[50]=te,e[51]=o,e[52]=Fe):Fe=e[52];let De;e[53]!==A?(De=()=>{A()},e[53]=A,e[54]=De):De=e[54];let xe;e[55]!==Y?(xe=Mn(Y)?n.jsx(vl.Input,{active:!0,size:"small",block:!0}):void 0,e[55]=Y,e[56]=xe):xe=e[56];let ae;e[57]!==v||e[58]!==ne.runtimeVariants?(ae=aa((je=ne.runtimeVariants)==null?void 0:je.count)&&ne.runtimeVariants.count>0?n.jsx(ia,{loading:v,total:ne.runtimeVariants.count}):void 0,e[57]=v,e[58]=ne.runtimeVariants,e[59]=ae):ae=e[59];let ve;return e[60]!==te||e[61]!==u||e[62]!==a||e[63]!==S||e[64]!==se||e[65]!==ce||e[66]!==re||e[67]!==ke||e[68]!==Re||e[69]!==Fe||e[70]!==De||e[71]!==xe||e[72]!==ae?(ve=n.jsx(ql,{ref:s,placeholder:se,loading:ce,...a,searchAction:re,showSearch:ke,value:Re,labelInValue:!0,onChange:Fe,options:te,endReached:De,open:u,onOpenChange:S,notFoundContent:xe,footer:ae}),e[60]=te,e[61]=u,e[62]=a,e[63]=S,e[64]=se,e[65]=ce,e[66]=re,e[67]=ke,e[68]=Re,e[69]=Fe,e[70]=De,e[71]=xe,e[72]=ae,e[73]=ve):ve=e[73],ve};function di(l){var e;return((e=l.runtimeVariants)==null?void 0:e.count)??void 0}function ui(l){return l==null?void 0:l.node}function ci(l){var e,i;return(i=(e=l.runtimeVariants)==null?void 0:e.edges)==null?void 0:i.map(ui)}function mi(l){return l==null?void 0:l.id}function gi(l){return{label:l==null?void 0:l.name,value:l!=null&&l.id?Ze(l.id):void 0}}const yt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"DeploymentHistory",abstractKey:null};yt.hash="eb0787126d34e31d6d0aa79127c25d2f";const yn=[];[...yn,...yn.map(l=>`-${l}`)];const bl=l=>vn(yn,l),yi=l=>{"use memo";const e=Ue.c(23);let i,r,t,a,d;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:r,customizeColumns:i,onChangeOrder:t,...d}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=kn();let c;e[6]===Symbol.for("react.memo_cache_sentinel")?(c=yt,e[6]=c):c=e[6];const o=Ke.useFragment(c,a);let g;if(e[7]!==i||e[8]!==r||e[9]!==s){let p;e[11]!==r?(p=b=>r?Sn(b,"sorter"):b,e[11]=r,e[12]=p):p=e[12];const k=Fl(tn([{dataIndex:"updatedAt",title:s("comp:BAIDeploymentSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:pi,sorter:bl("updated_at")},{dataIndex:"createdAt",title:s("comp:BAIDeploymentSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:fi,sorter:bl("created_at")},{dataIndex:"phase",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Phase"),key:"phase",sorter:bl("phase")},{dataIndex:"result",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Result"),key:"result",render:ki,sorter:bl("result")},{dataIndex:"category",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Category"),key:"category",sorter:bl("category")},{key:"fromStatus",title:s("comp:BAIDeploymentSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:bl("from_status")},{key:"toStatus",title:s("comp:BAIDeploymentSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:bl("to_status")},{dataIndex:"attempts",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:bl("attempts")},{key:"errorCode",title:s("comp:BAIDeploymentSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Si,sorter:bl("errorCode")},{key:"message",title:s("comp:BAIDeploymentSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:hi,render:vi,sorter:bl("message")}]),p);g=i?i(k):k,e[7]=i,e[8]=r,e[9]=s,e[10]=g}else g=e[10];const u=g;let S;e[13]!==o?(S=Al(o),e[13]=o,e[14]=S):S=e[14];let m;e[15]===Symbol.for("react.memo_cache_sentinel")?(m={x:"max-content"},e[15]=m):m=e[15];let y;e[16]!==t?(y=p=>{t==null||t(p||null)},e[16]=t,e[17]=y):y=e[17];let f;return e[18]!==u||e[19]!==S||e[20]!==y||e[21]!==d?(f=n.jsx(El,{rowKey:"id",dataSource:S,columns:u,scroll:m,onChangeOrder:y,...d}),e[18]=u,e[19]=S,e[20]=y,e[21]=d,e[22]=f):f=e[22],f};function pi(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function fi(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function ki(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(it,{result:i})}function Si(l,e){return e.errorCode?n.jsx(jl,{monospace:!0,children:e.errorCode}):"-"}function hi(){return{style:{maxWidth:500}}}function vi(l,e){return e.message?n.jsx(jl,{title:e.message,style:{width:"100%"},children:st(e.message)}):"-"}const pt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryNodeTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"RouteHistory",abstractKey:null};pt.hash="bd0c64d2e599015d8b9db0afbcb05c7c";const pn=[];[...pn,...pn.map(l=>`-${l}`)];const xl=l=>vn(pn,l),Fi=l=>{"use memo";const e=Ue.c(23);let i,r,t,a,d;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:r,customizeColumns:i,onChangeOrder:t,...d}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=kn();let c;e[6]===Symbol.for("react.memo_cache_sentinel")?(c=pt,e[6]=c):c=e[6];const o=Ke.useFragment(c,a);let g;if(e[7]!==i||e[8]!==r||e[9]!==s){let p;e[11]!==r?(p=b=>r?Sn(b,"sorter"):b,e[11]=r,e[12]=p):p=e[12];const k=Fl(tn([{dataIndex:"updatedAt",title:s("comp:BAIRouteSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:bi,sorter:xl("updated_at")},{dataIndex:"createdAt",title:s("comp:BAIRouteSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:xi,sorter:xl("created_at")},{dataIndex:"phase",title:s("comp:BAIRouteSchedulingHistoryNodes.Phase"),key:"phase",sorter:xl("phase")},{dataIndex:"result",title:s("comp:BAIRouteSchedulingHistoryNodes.Result"),key:"result",render:Ri,sorter:xl("result")},{dataIndex:"category",title:s("comp:BAIRouteSchedulingHistoryNodes.Category"),key:"category",sorter:xl("category")},{key:"fromStatus",title:s("comp:BAIRouteSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:xl("from_status")},{key:"toStatus",title:s("comp:BAIRouteSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:xl("to_status")},{dataIndex:"attempts",title:s("comp:BAIRouteSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:xl("attempts")},{key:"errorCode",title:s("comp:BAIRouteSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Ki,sorter:xl("errorCode")},{key:"message",title:s("comp:BAIRouteSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:Ti,render:Ii,sorter:xl("message")}]),p);g=i?i(k):k,e[7]=i,e[8]=r,e[9]=s,e[10]=g}else g=e[10];const u=g;let S;e[13]!==o?(S=Al(o),e[13]=o,e[14]=S):S=e[14];let m;e[15]===Symbol.for("react.memo_cache_sentinel")?(m={x:"max-content"},e[15]=m):m=e[15];let y;e[16]!==t?(y=p=>{t==null||t(p||null)},e[16]=t,e[17]=y):y=e[17];let f;return e[18]!==u||e[19]!==S||e[20]!==y||e[21]!==d?(f=n.jsx(El,{rowKey:"id",dataSource:S,columns:u,scroll:m,onChangeOrder:y,...d}),e[18]=u,e[19]=S,e[20]=y,e[21]=d,e[22]=f):f=e[22],f};function bi(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function xi(l){return n.jsx("span",{children:dl(l).format("ll LTS")})}function Ri(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(it,{result:i})}function Ki(l,e){return e.errorCode?n.jsx(jl,{monospace:!0,children:e.errorCode}):"-"}function Ti(){return{style:{maxWidth:500}}}function Ii(l,e){return e.message?n.jsx(jl,{title:e.message,style:{width:"100%"},children:st(e.message)}):"-"}const ft={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryNodesFragment"}],type:"DeploymentHistory",abstractKey:null};ft.hash="72a9b8118e4f52a97c2ab8996996098d";const Di=l=>{"use memo";const e=Ue.c(26);let i,r,t,a;e[0]!==l?({schedulingHistoryFrgmt:a,expandMode:i,onExpandModeChange:r,...t}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a):(i=e[1],r=e[2],t=e[3],a=e[4]);let d;e[5]===Symbol.for("react.memo_cache_sentinel")?(d=ft,e[5]=d):d=e[5];const s=Ke.useFragment(d,a);let c;e[6]!==s?(c=Al(s),e[6]=s,e[7]=c):c=e[7];const o=c;let g;e[8]!==i||e[9]!==r?(g={mode:i,onModeChange:r},e[8]=i,e[9]=r,e[10]=g):g=e[10];const{mode:u,expandedRowKeys:S,onExpandedRowsChange:m,expandColumnTitle:y}=rt(o,g);let f;e[11]!==o?(f=x=>{var F;return!hn((F=o.find(T=>T.id===x.id))==null?void 0:F.subSteps)},e[11]=o,e[12]=f):f=e[12];let p;e[13]!==o||e[14]!==u?(p=x=>{var F;return n.jsx(ot,{resizable:!0,subStepsFrgmt:((F=o.find(T=>T.id===x.id))==null?void 0:F.subSteps)??[],pagination:!1,errorsOnly:u==="errors-only"})},e[13]=o,e[14]=u,e[15]=p):p=e[15];let k;e[16]!==y||e[17]!==S||e[18]!==m||e[19]!==f||e[20]!==p?(k={columnTitle:y,expandedRowKeys:S,onExpandedRowsChange:m,rowExpandable:f,expandedRowRender:p},e[16]=y,e[17]=S,e[18]=m,e[19]=f,e[20]=p,e[21]=k):k=e[21];let b;return e[22]!==s||e[23]!==t||e[24]!==k?(b=n.jsx(yi,{schedulingHistoryFrgmt:s,expandable:k,...t}),e[22]=s,e[23]=t,e[24]=k,e[25]=b):b=e[25],b},kt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryNodeTableFragment"}],type:"RouteHistory",abstractKey:null};kt.hash="7f5f32e6a4ea10ddfc54ff01c8b260b2";const Ci=l=>{"use memo";const e=Ue.c(26);let i,r,t,a;e[0]!==l?({schedulingHistoryFrgmt:a,expandMode:i,onExpandModeChange:r,...t}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a):(i=e[1],r=e[2],t=e[3],a=e[4]);let d;e[5]===Symbol.for("react.memo_cache_sentinel")?(d=kt,e[5]=d):d=e[5];const s=Ke.useFragment(d,a);let c;e[6]!==s?(c=Al(s),e[6]=s,e[7]=c):c=e[7];const o=c;let g;e[8]!==i||e[9]!==r?(g={mode:i,onModeChange:r},e[8]=i,e[9]=r,e[10]=g):g=e[10];const{mode:u,expandedRowKeys:S,onExpandedRowsChange:m,expandColumnTitle:y}=rt(o,g);let f;e[11]!==o?(f=x=>{var F;return!hn((F=o.find(T=>T.id===x.id))==null?void 0:F.subSteps)},e[11]=o,e[12]=f):f=e[12];let p;e[13]!==o||e[14]!==u?(p=x=>{var F;return n.jsx(ot,{resizable:!0,subStepsFrgmt:((F=o.find(T=>T.id===x.id))==null?void 0:F.subSteps)??[],pagination:!1,errorsOnly:u==="errors-only"})},e[13]=o,e[14]=u,e[15]=p):p=e[15];let k;e[16]!==y||e[17]!==S||e[18]!==m||e[19]!==f||e[20]!==p?(k={columnTitle:y,expandedRowKeys:S,onExpandedRowsChange:m,rowExpandable:f,expandedRowRender:p},e[16]=y,e[17]=S,e[18]=m,e[19]=f,e[20]=p,e[21]=k):k=e[21];let b;return e[22]!==s||e[23]!==t||e[24]!==k?(b=n.jsx(Fi,{schedulingHistoryFrgmt:s,expandable:k,...t}),e[22]=s,e[23]=t,e[24]=k,e[25]=b):b=e[25],b},St=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},d={alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},s={alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},c=[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],o={alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:c,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},g={alias:null,args:null,concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:c,storageKey:null},u=[i],S={alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},f={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,r,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[m,y,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},f],storageKey:null},k={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},x=[r,b],F={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null}],storageKey:null},T={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},R={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[m,y,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},f],storageKey:null},D={alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[r,i],storageKey:null},C={alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null},$={alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},b,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null},z={alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},B={alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},O={alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},w={alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},G={alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},W={alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},Q={alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},H={alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},V={alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},K={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},M={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentDetailPageQuery",selections:[{kind:"CatchField",field:{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,t,a],storageKey:null},d,s,o,g,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:u,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:u,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[S],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentBasicInfoCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentReplicasCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAccessTokensCard_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAutoScalingCard_deployment"}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[r,t,a,{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[r],storageKey:null},i],storageKey:null}],storageKey:null},d,s,o,g,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,p,k,F,T,R,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},D,C,$,z],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,P,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[B,O,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},I,w,N,G,W,Q],storageKey:null},H,V],storageKey:null}],storageKey:null}],storageKey:null},K,M,_,T,K],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:[i,M,_,k,T,F,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[D,z,C,$],storageKey:null},p,R,K,{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,P,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[B,H,O,V,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[I,N,w,G,W,Q],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[S,i],storageKey:null}],storageKey:null}]},params:{cacheID:"cf0be491960db330acb124fcdb02e651",id:null,metadata:{},name:"DeploymentDetailPageQuery",operationKind:"query",text:`query DeploymentDetailPageQuery(
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
`}}})();St.hash="9089d2f31b9601fe2fa64e840ab45300";const ht=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAccessTokenPayload",kind:"LinkedField",name:"deleteAccessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardDeleteMutation",selections:e},params:{cacheID:"3001cf022c16a198843b296bca8e75f9",id:null,metadata:{},name:"DeploymentAccessTokensCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensCardDeleteMutation(
  $input: DeleteAccessTokenInput!
) {
  deleteAccessToken(input: $input) {
    id
  }
}
`}}})();ht.hash="6877559748beeee076979bb65393d59f";const vt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:[{kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"CREATED_AT"}]}],concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"AccessTokenEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:'accessTokens(orderBy:[{"direction":"DESC","field":"CREATED_AT"}])'};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[r],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[r,i],storageKey:null}]},params:{cacheID:"fe0599e3ca582035a0afb69f61751a53",id:null,metadata:{},name:"DeploymentAccessTokensCardListQuery",operationKind:"query",text:`query DeploymentAccessTokensCardListQuery(
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
`}}})();vt.hash="b43bdbd02f49d9e5a3e3b15dac4c1b90";const Ft=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAccessTokenPayload",kind:"LinkedField",name:"createAccessToken",plural:!1,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"accessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCardCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensCardCreateMutation",selections:e},params:{cacheID:"8c08238f7222fe51a04881e736d82b15",id:null,metadata:{},name:"DeploymentAccessTokensCardCreateMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensCardCreateMutation(
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
`}}})();Ft.hash="4ba926c16e8cf928584ec3a34cde8b34";const bt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAccessTokensCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};bt.hash="e7372d3fa2bb21537f6b39e44698dedf";const Ai=l=>{"use memo";var Fe;const e=Ue.c(95);let i,r,t,a,d,s,c;e[0]!==l?({deploymentFrgmt:t,deploymentId:a,isOwnedByCurrentUser:s,isDeploymentDestroying:c,onTokenCreated:d,cardRef:i,...r}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d,e[6]=s,e[7]=c):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5],s=e[6],c=e[7]);const o=s===void 0?!0:s,g=c===void 0?!1:c,{t:u}=ll(),{token:S}=Dl.useToken(),{message:m}=Pl.useApp(),{logger:y}=Ol(),[f,p]=j.useTransition(),[k,b]=Il();let x;e[8]===Symbol.for("react.memo_cache_sentinel")?(x={defaultValue:!1,valuePropName:"isCreateModalOpen",trigger:"onCreateModalOpenChange"},e[8]=x):x=e[8];const[F,T]=mn(r,x),[R,D]=j.useState(null),C=j.useDeferredValue(k);let $;e[9]===Symbol.for("react.memo_cache_sentinel")?($=bt,e[9]=$):$=e[9];const z=Ke.useFragment($,t);let P;e[10]===Symbol.for("react.memo_cache_sentinel")?(P=Ft,e[10]=P):P=e[10];const B=Gn(P);let O;e[11]!==b?(O=()=>{p(()=>{b()})},e[11]=b,e[12]=O):O=e[12];const I=O,w=!!((Fe=z.networkAccess)!=null&&Fe.endpointUrl),N=g||!o,G=N||!w;let W;e[13]!==u?(W=u("deployment.tab.AccessTokens"),e[13]=u,e[14]=W):W=e[14];let Q;e[15]!==u?(Q=u("deployment.tab.description.AccessTokens"),e[15]=u,e[16]=Q):Q=e[16];let H;e[17]!==S.colorTextDescription?(H=n.jsx(Fn,{style:{color:S.colorTextDescription}}),e[17]=S.colorTextDescription,e[18]=H):H=e[18];let V;e[19]!==Q||e[20]!==H?(V=n.jsx(cl,{title:Q,children:H}),e[19]=Q,e[20]=H,e[21]=V):V=e[21];let K;e[22]!==V||e[23]!==W?(K=n.jsxs(ie,{gap:"xs",align:"center",children:[W,V]}),e[22]=V,e[23]=W,e[24]=K):K=e[24];let M;e[25]!==I||e[26]!==f?(M=n.jsx(wl,{loading:f,value:"",onChange:I}),e[25]=I,e[26]=f,e[27]=M):M=e[27];let _;e[28]!==w||e[29]!==u?(_=w?"":u("deployment.accessToken.EndpointNotIssuedYet"),e[28]=w,e[29]=u,e[30]=_):_=e[30];let Y;e[31]===Symbol.for("react.memo_cache_sentinel")?(Y=n.jsx(Ll,{}),e[31]=Y):Y=e[31];let ne;e[32]!==T?(ne=()=>T(!0),e[32]=T,e[33]=ne):ne=e[33];let A;e[34]!==u?(A=u("deployment.accessToken.Create"),e[34]=u,e[35]=A):A=e[35];let v;e[36]!==G||e[37]!==ne||e[38]!==A?(v=n.jsx(kl,{type:"primary",icon:Y,disabled:G,onClick:ne,children:A}),e[36]=G,e[37]=ne,e[38]=A,e[39]=v):v=e[39];let E;e[40]!==_||e[41]!==v?(E=n.jsx(cl,{title:_,children:v}),e[40]=_,e[41]=v,e[42]=E):E=e[42];let L;e[43]!==M||e[44]!==E?(L=n.jsxs(ie,{gap:"xs",align:"center",children:[M,E]}),e[43]=M,e[44]=E,e[45]=L):L=e[45];let U;e[46]===Symbol.for("react.memo_cache_sentinel")?(U={body:{paddingTop:0}},e[46]=U):U=e[46];let Z;e[47]===Symbol.for("react.memo_cache_sentinel")?(Z=n.jsx(vl,{active:!0}),e[47]=Z):Z=e[47];let J;e[48]!==C||e[49]!==a||e[50]!==I||e[51]!==N||e[52]!==f?(J=n.jsx(j.Suspense,{fallback:Z,children:n.jsx(Mi,{deploymentId:a,fetchKey:C,isPendingRefetch:f,isDeleteDisabled:N,onAfterDelete:I})}),e[48]=C,e[49]=a,e[50]=I,e[51]=N,e[52]=f,e[53]=J):J=e[53];let ee;e[54]!==i||e[55]!==K||e[56]!==L||e[57]!==J?(ee=n.jsx(Yl,{ref:i,title:K,extra:L,styles:U,children:J}),e[54]=i,e[55]=K,e[56]=L,e[57]=J,e[58]=ee):ee=e[58];let q;e[59]!==B||e[60]!==z.id||e[61]!==I||e[62]!==y||e[63]!==m||e[64]!==d||e[65]!==T||e[66]!==u?(q=De=>{T(!1),De&&B({input:{modelDeploymentId:Ze(z.id),expiresAt:De.expiresAt??new Date("2099-12-31").toISOString()}}).then(xe=>{var ve;const ae=(ve=xe.createAccessToken)==null?void 0:ve.accessToken;ae&&D({token:ae.token,expiresAt:ae.expiresAt??null}),m.success({key:"access-token-created",content:u("deployment.accessToken.Created")}),I(),d==null||d()}).catch(xe=>{const ae=Array.isArray(xe)?xe:[xe];for(const ve of ae)m.error((ve==null?void 0:ve.message)||u("dialog.ErrorOccurred"));y.error(xe)})},e[59]=B,e[60]=z.id,e[61]=I,e[62]=y,e[63]=m,e[64]=d,e[65]=T,e[66]=u,e[67]=q):q=e[67];let te;e[68]!==F||e[69]!==q?(te=n.jsx(fl,{children:n.jsx(Li,{open:F,confirmLoading:!1,onRequestClose:q})}),e[68]=F,e[69]=q,e[70]=te):te=e[70];const ye=R!==null;let de;e[71]!==u?(de=u("deployment.accessToken.Token"),e[71]=u,e[72]=de):de=e[72];let pe;e[73]===Symbol.for("react.memo_cache_sentinel")?(pe=()=>D(null),e[73]=pe):pe=e[73];let ue;e[74]!==u?(ue=u("deployment.accessToken.Created"),e[74]=u,e[75]=ue):ue=e[75];let fe;e[76]!==ue?(fe=n.jsx(el.Text,{children:ue}),e[76]=ue,e[77]=fe):fe=e[77];let se;e[78]!==R?(se=R?n.jsx(jl,{copyable:{text:R.token},ellipsis:!0,code:!0,children:R.token}):null,e[78]=R,e[79]=se):se=e[79];let ce;e[80]!==R||e[81]!==u?(ce=R!=null&&R.expiresAt?n.jsx(el.Text,{type:"secondary",children:`${u("deployment.accessToken.Expiration")}: ${dl(R.expiresAt).format("ll LT")}`}):n.jsx(el.Text,{type:"secondary",children:u("deployment.accessToken.NoExpiration")}),e[80]=R,e[81]=u,e[82]=ce):ce=e[82];let re;e[83]!==fe||e[84]!==se||e[85]!==ce?(re=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[fe,se,ce]}),e[83]=fe,e[84]=se,e[85]=ce,e[86]=re):re=e[86];let ke;e[87]!==ye||e[88]!==de||e[89]!==re?(ke=n.jsx(fl,{children:n.jsx($l,{open:ye,destroyOnHidden:!0,title:de,onCancel:pe,footer:null,width:520,children:re})}),e[87]=ye,e[88]=de,e[89]=re,e[90]=ke):ke=e[90];let Re;return e[91]!==ee||e[92]!==te||e[93]!==ke?(Re=n.jsxs(n.Fragment,{children:[ee,te,ke]}),e[91]=ee,e[92]=te,e[93]=ke,e[94]=Re):Re=e[94],Re},Mi=l=>{"use memo";var U,Z,J,ee;const e=Ue.c(71),{deploymentId:i,fetchKey:r,isPendingRefetch:t,isDeleteDisabled:a,onAfterDelete:d}=l,{t:s}=ll(),{message:c}=Pl.useApp(),{logger:o}=Ol(),[g,u]=j.useState(null),S=r===Wl;let m;e[0]===Symbol.for("react.memo_cache_sentinel")?(m=vt,e[0]=m):m=e[0];let y;e[1]!==i?(y={deploymentId:i},e[1]=i,e[2]=y):y=e[2];const f=S?"store-and-network":"network-only";let p;e[3]!==r||e[4]!==f?(p={fetchKey:r,fetchPolicy:f},e[3]=r,e[4]=f,e[5]=p):p=e[5];const{deployment:k}=Ke.useLazyLoadQuery(m,y,p);let b;e[6]!==((U=k==null?void 0:k.accessTokens)==null?void 0:U.edges)?(b=Al((J=(Z=k==null?void 0:k.accessTokens)==null?void 0:Z.edges)==null?void 0:J.map(ji)),e[6]=(ee=k==null?void 0:k.accessTokens)==null?void 0:ee.edges,e[7]=b):b=e[7];const x=b;let F;e[8]===Symbol.for("react.memo_cache_sentinel")?(F=ht,e[8]=F):F=e[8];const[T,R]=Ke.useMutation(F);let D;e[9]===Symbol.for("react.memo_cache_sentinel")?(D={x:"max-content"},e[9]=D):D=e[9];const C=t||R;let $;e[10]!==s?($=s("deployment.accessToken.Token"),e[10]=s,e[11]=$):$=e[11];let z;e[12]!==a||e[13]!==s?(z=(q,te)=>te?n.jsx(bn,{title:n.jsx(jl,{copyable:{text:te.token},ellipsis:!0,style:{maxWidth:200},children:te.token}),showActions:"always",actions:[{key:"delete",title:s("deployment.accessToken.Delete"),icon:n.jsx(xn,{}),type:"danger",disabled:a,onClick:()=>u({id:te.id,token:te.token??""})}]}):"-",e[12]=a,e[13]=s,e[14]=z):z=e[14];let P;e[15]!==z||e[16]!==$?(P={key:"token",title:$,dataIndex:"token",render:z},e[15]=z,e[16]=$,e[17]=P):P=e[17];let B;e[18]!==s?(B=s("deployment.CreatedAt"),e[18]=s,e[19]=B):B=e[19];let O;e[20]!==B?(O={key:"createdAt",title:B,dataIndex:"createdAt",render:Pi},e[20]=B,e[21]=O):O=e[21];let I;e[22]!==s?(I=s("deployment.accessToken.Expiration"),e[22]=s,e[23]=I):I=e[23];let w;e[24]!==s?(w=(q,te)=>te!=null&&te.expiresAt?dl(te.expiresAt).format("ll LT"):s("deployment.accessToken.NoExpiration"),e[24]=s,e[25]=w):w=e[25];let N;e[26]!==I||e[27]!==w?(N={key:"expiresAt",title:I,dataIndex:"expiresAt",render:w},e[26]=I,e[27]=w,e[28]=N):N=e[28];let G;e[29]!==P||e[30]!==O||e[31]!==N?(G=[P,O,N],e[29]=P,e[30]=O,e[31]=N,e[32]=G):G=e[32];let W;e[33]!==x||e[34]!==G||e[35]!==C?(W=n.jsx(El,{scroll:D,rowKey:"id",loading:C,dataSource:x,pagination:!1,resizable:!0,columns:G}),e[33]=x,e[34]=G,e[35]=C,e[36]=W):W=e[36];const Q=!!g;let H;e[37]!==s?(H=s("deployment.accessToken.Delete"),e[37]=s,e[38]=H):H=e[38];let V;e[39]!==s?(V=s("deployment.AccessToken"),e[39]=s,e[40]=V):V=e[40];let K;e[41]!==g?(K=g?[{key:g.id,label:g.id}]:[],e[41]=g,e[42]=K):K=e[42];let M;e[43]!==s?(M=s("data.folders.DeleteForeverConfirmText"),e[43]=s,e[44]=M):M=e[44];let _;e[45]!==s?(_=s("data.folders.DeleteForeverConfirmText"),e[45]=s,e[46]=_):_=e[46];let Y;e[47]!==_?(Y={placeholder:_},e[47]=_,e[48]=Y):Y=e[48];let ne;e[49]!==R?(ne={loading:R},e[49]=R,e[50]=ne):ne=e[50];let A;e[51]!==T||e[52]!==g||e[53]!==o||e[54]!==c||e[55]!==d||e[56]!==s?(A=()=>{g&&T({variables:{input:{id:Ze(g.id)??g.id}},onCompleted:(q,te)=>{var ye;if(te&&te.length>0){o.error(te[0]),c.error(((ye=te[0])==null?void 0:ye.message)??s("dialog.ErrorOccurred"));return}c.success(s("deployment.accessToken.Deleted")),u(null),d()},onError:q=>{o.error(q),c.error(q.message??s("dialog.ErrorOccurred"))}})},e[51]=T,e[52]=g,e[53]=o,e[54]=c,e[55]=d,e[56]=s,e[57]=A):A=e[57];let v;e[58]===Symbol.for("react.memo_cache_sentinel")?(v=()=>u(null),e[58]=v):v=e[58];let E;e[59]!==Q||e[60]!==H||e[61]!==V||e[62]!==K||e[63]!==M||e[64]!==Y||e[65]!==ne||e[66]!==A?(E=n.jsx(Rn,{open:Q,title:H,target:V,items:K,confirmText:M,requireConfirmInput:!0,inputProps:Y,okButtonProps:ne,onOk:A,onCancel:v}),e[59]=Q,e[60]=H,e[61]=V,e[62]=K,e[63]=M,e[64]=Y,e[65]=ne,e[66]=A,e[67]=E):E=e[67];let L;return e[68]!==W||e[69]!==E?(L=n.jsxs(n.Fragment,{children:[W,E]}),e[68]=W,e[69]=E,e[70]=L):L=e[70],L},Li=l=>{"use memo";const e=Ue.c(64),{open:i,confirmLoading:r,onRequestClose:t}=l,{t:a}=ll(),[d]=ge.useForm(),s=ge.useWatch("expiryOption",d)??7;let c;e[0]!==d||e[1]!==t?(c=()=>{d.validateFields().then(H=>{let V;H.expiryOption==="none"?V=null:H.expiryOption==="custom"?V=H.datetime.toISOString():V=dl().add(H.expiryOption,"day").toISOString(),t({expiresAt:V})}).catch(Ni)},e[0]=d,e[1]=t,e[2]=c):c=e[2];const o=c;let g;e[3]!==a?(g=a("general.Days",{num:7,defaultValue:"7 days"}),e[3]=a,e[4]=g):g=e[4];let u;e[5]!==g?(u={value:7,label:g},e[5]=g,e[6]=u):u=e[6];let S;e[7]!==a?(S=a("general.Days",{num:30,defaultValue:"30 days"}),e[7]=a,e[8]=S):S=e[8];let m;e[9]!==S?(m={value:30,label:S},e[9]=S,e[10]=m):m=e[10];let y;e[11]!==a?(y=a("general.Days",{num:90,defaultValue:"90 days"}),e[11]=a,e[12]=y):y=e[12];let f;e[13]!==y?(f={value:90,label:y},e[13]=y,e[14]=f):f=e[14];let p;e[15]!==a?(p=a("deployment.accessToken.CustomExpiration"),e[15]=a,e[16]=p):p=e[16];let k;e[17]!==p?(k={value:"custom",label:p},e[17]=p,e[18]=k):k=e[18];let b;e[19]!==a?(b=a("deployment.accessToken.NoExpiration"),e[19]=a,e[20]=b):b=e[20];let x;e[21]!==b?(x={value:"none",label:b},e[21]=b,e[22]=x):x=e[22];let F;e[23]!==x||e[24]!==u||e[25]!==m||e[26]!==f||e[27]!==k?(F=[u,m,f,k,x],e[23]=x,e[24]=u,e[25]=m,e[26]=f,e[27]=k,e[28]=F):F=e[28];const T=F;let R;e[29]!==a?(R=a("deployment.accessToken.Create"),e[29]=a,e[30]=R):R=e[30];let D;e[31]!==a?(D=a("deployment.accessToken.Create"),e[31]=a,e[32]=D):D=e[32];let C;e[33]!==t?(C=()=>t(),e[33]=t,e[34]=C):C=e[34];let $,z;e[35]===Symbol.for("react.memo_cache_sentinel")?($={expiryOption:7,datetime:dl().add(7,"day")},z=["onChange","onBlur"],e[35]=$,e[36]=z):($=e[35],z=e[36]);let P;e[37]!==a?(P=a("deployment.accessToken.Expiration"),e[37]=a,e[38]=P):P=e[38];let B;e[39]===Symbol.for("react.memo_cache_sentinel")?(B=[{required:!0}],e[39]=B):B=e[39];let O;e[40]===Symbol.for("react.memo_cache_sentinel")?(O={width:200},e[40]=O):O=e[40];let I;e[41]!==d?(I=H=>{typeof H=="number"&&d.setFieldValue("datetime",dl().add(H,"day"))},e[41]=d,e[42]=I):I=e[42];let w;e[43]!==T||e[44]!==I?(w=n.jsx(gn,{style:O,options:T,onChange:I}),e[43]=T,e[44]=I,e[45]=w):w=e[45];let N;e[46]!==P||e[47]!==w?(N=n.jsx(ge.Item,{name:"expiryOption",label:P,rules:B,children:w}),e[46]=P,e[47]=w,e[48]=N):N=e[48];let G;e[49]!==s||e[50]!==a?(G=s==="custom"&&n.jsx(ge.Item,{name:"datetime",label:a("deployment.accessToken.CustomExpiration"),rules:[{type:"object",required:!0},()=>({validator(H,V){return V&&dl(V).isAfter(dl())?Promise.resolve():Promise.reject(new Error(a("dialog.ErrorOccurred")))}})],children:n.jsx(da,{showTime:!0,format:"YYYY-MM-DD HH:mm:ss",style:{width:"100%"}})}),e[49]=s,e[50]=a,e[51]=G):G=e[51];let W;e[52]!==d||e[53]!==N||e[54]!==G?(W=n.jsxs(ge,{form:d,layout:"vertical",initialValues:$,validateTrigger:z,children:[N,G]}),e[52]=d,e[53]=N,e[54]=G,e[55]=W):W=e[55];let Q;return e[56]!==r||e[57]!==o||e[58]!==i||e[59]!==R||e[60]!==D||e[61]!==C||e[62]!==W?(Q=n.jsx($l,{open:i,destroyOnHidden:!0,centered:!0,width:420,title:R,okText:D,confirmLoading:r,onOk:o,onCancel:C,children:W}),e[56]=r,e[57]=o,e[58]=i,e[59]=R,e[60]=D,e[61]=C,e[62]=W,e[63]=Q):Q=e[63],Q};function ji(l){return l==null?void 0:l.node}function Pi(l,e){return e!=null&&e.createdAt?dl(e.createdAt).format("ll LT"):"-"}function Ni(){}const xt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"architecture"},e={defaultValue:null,kind:"LocalArgument",name:"reference"},i=[{alias:null,args:[{kind:"Variable",name:"architecture",variableName:"architecture"},{kind:"Variable",name:"reference",variableName:"reference"}],concreteType:"Image",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalManualImageQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,l],kind:"Operation",name:"DeploymentAddRevisionModalManualImageQuery",selections:i},params:{cacheID:"6bcc84ae2c2ac9e9606dddd37c2b9d15",id:null,metadata:{},name:"DeploymentAddRevisionModalManualImageQuery",operationKind:"query",text:`query DeploymentAddRevisionModalManualImageQuery(
  $reference: String!
  $architecture: String
) {
  image(reference: $reference, architecture: $architecture) {
    id
  }
}
`}}})();xt.hash="9a966eb2f1a961353ecfc61d58978716";const Rt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"71af54781375e6ee4bceb1c73e74d088",id:null,metadata:{},name:"DeploymentAddRevisionModalImageNameQuery",operationKind:"query",text:`query DeploymentAddRevisionModalImageNameQuery(
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
`}}})();Rt.hash="7f7c91d5e401085de1ab4d56ffb2ef9b";const Kt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},t={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},d=[i,r],s={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},o={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},g={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},m=[u,S],y={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null}],storageKey:null},f={alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[u,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:m,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},S,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},b={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,u,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},x={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,k,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},b],storageKey:null},F={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[p,k,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},b],storageKey:null},T={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},R={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},D=[i,s,c,o,g,y,f,x,F,T,R];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,r,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:d,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,s,c,o,g,y,f,x,F,T,R,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:D,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:D,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"97d46eaffe190c0a696e6d7daacc3529",id:null,metadata:{},name:"DeploymentAddRevisionModalAddMutation",operationKind:"mutation",text:`mutation DeploymentAddRevisionModalAddMutation(
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
`}}})();Kt.hash="889773e313c63748043b8294cd2bb0b0";const Tt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i},params:{cacheID:"6728695a02d457f55b4cd4d3323823d8",id:null,metadata:{},name:"DeploymentAddRevisionModalSelectedPresetQuery",operationKind:"query",text:`query DeploymentAddRevisionModalSelectedPresetQuery(
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
`}}})();Tt.hash="e9d60ac2d9540dae9c821fe3abd4b65e";const It=(function(){var l=[{alias:null,args:[{kind:"Literal",name:"first",value:1},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"RANK"}]}],concreteType:"DeploymentRevisionPresetConnection",kind:"LinkedField",name:"deploymentRevisionPresets",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:'deploymentRevisionPresets(first:1,orderBy:[{"direction":"ASC","field":"RANK"}])'}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetCountQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAddRevisionModalPresetCountQuery",selections:l},params:{cacheID:"edaa5efa78debd74168a24185822d633",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetCountQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetCountQuery {
  deploymentRevisionPresets(orderBy: [{field: RANK, direction: "ASC"}], first: 1) {
    count
  }
}
`}}})();It.hash="4461df1967b1117642d3190b36d5cb33";const Dt=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[l,e],r={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_revisionSource",selections:[{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:i,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[r,t],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[l],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:i,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[r,t,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelRevision",abstractKey:null}})();Dt.hash="94f9806003b984d4534543e7895a61e8";const Ct={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Ct.hash="614548b7fde80b4972dfb192b893b832";const At=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentPresetDetailModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[i,r,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,r],storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startupCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"bootstrapScript",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"image",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[r,t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetDeploymentDefaults",kind:"LinkedField",name:"deploymentDefaults",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"replicaCount",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"revisionHistoryLimit",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentStrategy",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValueEntry",kind:"LinkedField",name:"presetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},t],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[r,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"ccd4b84ef4b7bf255f7a95f4bbbacd00",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetDetailQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetDetailQuery(
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
`}}})();At.hash="8f60ae6bcf0fa60919e80838391f66f9";const rn=({children:l})=>{const{token:e}=Dl.useToken();return n.jsx(Xn,{titlePlacement:"left",children:n.jsx(el.Text,{type:"secondary",style:{fontSize:e.fontSizeSM},children:l})})},Vi=l=>{"use memo";const e=Ue.c(6),{presetId:i,onCancel:r}=l;let t;e[0]===Symbol.for("react.memo_cache_sentinel")?(t=At,e[0]=t):t=e[0];let a;e[1]!==i?(a={id:i},e[1]=i,e[2]=a):a=e[2];const d=Ke.useLazyLoadQuery(t,a);let s;return e[3]!==d.deploymentRevisionPreset||e[4]!==r?(s=n.jsx(Fa,{open:!0,presetFrgmt:d.deploymentRevisionPreset,onCancel:r}),e[3]=d.deploymentRevisionPreset,e[4]=r,e[5]=s):s=e[5],s},Mt=({onRequestClose:l,deploymentFrgmt:e,sourceRevisionFrgmt:i,open:r,...t})=>{"use memo";var Pe,Xe,Je;const{t:a}=ll(),{token:d}=Dl.useToken(),{message:s}=Pl.useApp(),c=Ke.useRelayEnvironment(),o=Ke.useFragment(Ct,e),g=Dt,u=Ke.useFragment(g,(o==null?void 0:o.currentRevision)??null),S=Ke.useFragment(g,i??null),{id:m}=Yn(),{logger:y}=Ol(),{open:f}=ua(),p=Kn(),k=p.supports("model-health-check-enable"),b=p.supports("model-runtime-variant-preset-values"),x=j.useRef(null),F=j.useRef(null),[T,R]=j.useState(!1),[D]=ge.useForm(),[C]=ge.useForm(),[$,z]=j.useState(!0),[P,B]=j.useState(!1),[O,I]=Cl("deploymentRevisionCreationMode"),w=O??"preset",[N,G]=j.useState(!1),[W,Q]=j.useState(!1),[H,V]=j.useState(!1),[K,M]=j.useState(null),[_,Y]=j.useState(null),[ne,A]=j.useState(null),[v,E]=j.useState({}),L=j.useRef(new Set),U=j.useRef(null),[Z,J]=j.useState(void 0),ee=j.useRef({}),[q,te]=j.useState(void 0);j.useEffect(()=>{if(!r)return;let h=!1;return Ke.fetchQuery(c,It,{},{fetchPolicy:"store-or-network"}).toPromise().then(X=>{var le;h||te((((le=X==null?void 0:X.deploymentRevisionPresets)==null?void 0:le.count)??0)===0)}).catch(()=>{h||te(!1)}),()=>{h=!0}},[r,c]);const ye=(Xe=(Pe=o==null?void 0:o.currentRevision)==null?void 0:Pe.modelMountConfig)!=null&&Xe.vfolderId?zl("VirtualFolderNode",o.currentRevision.modelMountConfig.vfolderId):void 0,de=j.useRef(new Map),pe=async h=>{const X=de.current.get(h);if(X)return X;const le=await Ke.fetchQuery(c,Tt,{id:h},{fetchPolicy:"store-or-network"}).toPromise(),oe=(le==null?void 0:le.deploymentRevisionPreset)??null;return oe&&de.current.set(h,oe),oe},[ue,fe]=Ke.useMutation(Kt),se=async h=>{var Qe,be,He,qe,We,we,ze,nl;const X=h.resourceSlots??[],le=X.find(Ne=>Ne.slotName==="cpu"),oe=X.find(Ne=>Ne.slotName==="mem"),me=X.find(Ne=>Ne.slotName!=="cpu"&&Ne.slotName!=="mem"),Se=(((Qe=h.resource)==null?void 0:Qe.resourceOpts)??[]).find(Ne=>Ne.name==="shmem"),Le=((be=h.cluster)==null?void 0:be.clusterMode)==="SINGLE_NODE"?"single-node":"multi-node";let _e;if((He=h.execution)!=null&&He.imageId)try{const Ne=await Ke.fetchQuery(c,Rt,{id:h.execution.imageId},{fetchPolicy:"store-or-network"}).toPromise(),Ge=(qe=Ne==null?void 0:Ne.imageV2)==null?void 0:qe.identity;_e=Ge!=null&&Ge.canonicalName?Ge.architecture?`${Ge.canonicalName}@${Ge.architecture}`:Ge.canonicalName:void 0}catch{_e=void 0}const Be=(((We=h.execution)==null?void 0:We.environ)??[]).map(Ne=>({variable:Ne.key,value:Ne.value}));return{cluster_mode:Le,cluster_size:((we=h.cluster)==null?void 0:we.clusterSize)??1,allocationPreset:"custom",resource:{cpu:le?Number(le.quantity):0,mem:((ze=Zl(String((oe==null?void 0:oe.quantity)??"0"),"g",2))==null?void 0:ze.value)??"0g",shmem:((nl=Zl((Se==null?void 0:Se.value)??Jl,"g",2))==null?void 0:nl.value)??Jl,...me?{acceleratorType:me.slotName,accelerator:me.slotName==="cuda.shares"?parseFloat(String(me.quantity)):parseInt(String(me.quantity),10)}:{}},enabledAutomaticShmem:!Se,runtimeVariantId:h.runtimeVariantId??void 0,environ:Be,..._e?{environments:{version:_e}}:{}}},ce=async h=>{if(h===w)return;if(w==="preset"&&h==="custom"){const oe=C.getFieldsValue(),me=oe.revisionPresetId;let Se={};if(me){const Le=await pe(me);Le&&(Se=await se(Le))}oe.modelFolderId&&(Se.modelFolderId=oe.modelFolderId),M(Object.keys(Se).length>0?Se:null),I("custom");return}const X=D.getFieldsValue(),le={};X.modelFolderId&&(le.modelFolderId=X.modelFolderId),D.resetFields(),M(null),Y(Object.keys(le).length>0?le:null),I("preset")},re=h=>{var qe,We,we,ze,nl,Ne,Ge,ul,al,il,sl,ol,Ie,Te,Ve,Ye,Sl,he,Ae,rl,$e,tl,yl,Ml,Rl;const X=h.resourceSlots??[],le=X.find(Ee=>Ee.slotName==="cpu"),oe=X.find(Ee=>Ee.slotName==="mem"),me=X.find(Ee=>Ee.slotName!=="cpu"&&Ee.slotName!=="mem"),Se=(((We=(qe=h.resourceConfig)==null?void 0:qe.resourceOpts)==null?void 0:We.entries)??[]).find(Ee=>Ee.name==="shmem"),Le=((ze=(we=h.modelRuntimeConfig)==null?void 0:we.runtimeVariant)==null?void 0:ze.name)??"",_e=Le==="custom",Be=(nl=h.modelRuntimeConfig)==null?void 0:nl.runtimeVariantId;Be&&Le&&E(Ee=>({...Ee,[Be]:Le}));const Oe=(ul=(Ge=(Ne=h.modelDefinition)==null?void 0:Ne.models)==null?void 0:Ge[0])==null?void 0:ul.service,Qe=(sl=(il=(al=h.modelDefinition)==null?void 0:al.models)==null?void 0:il[0])==null?void 0:sl.modelPath,be=Oe!=null&&Oe.healthCheck&&Oe.healthCheck.enable!==!1?Oe.healthCheck:void 0,He=_e&&!!Oe&&(((ol=Oe.startCommand)==null?void 0:ol.length)??0)>0;if(ee.current=Nn((h.extraMounts??[]).filter(Ee=>!!Ee.mountDestination).map(Ee=>[Ee.vfolderId.replace(/-/g,""),Ee.mountDestination])),!_e&&Le){const Ee=(Ie=h.modelRuntimeConfig)==null?void 0:Ie.runtimeVariantPresetValues;J(Ee&&Ee.length>0?Ee.map(An=>({presetId:An.presetId,value:An.value})):void 0)}D.setFieldsValue({cluster_mode:((Te=h.clusterConfig)==null?void 0:Te.mode)==="SINGLE_NODE"?"single-node":"multi-node",cluster_size:((Ve=h.clusterConfig)==null?void 0:Ve.size)??1,allocationPreset:"custom",resource:{cpu:le?Number(le.quantity):0,mem:((Ye=Zl(String((oe==null?void 0:oe.quantity)??"0"),"g",2))==null?void 0:Ye.value)??"0g",shmem:((Sl=Zl((Se==null?void 0:Se.value)??Jl,"g",2))==null?void 0:Sl.value)??Jl,...me?{acceleratorType:me.slotName,accelerator:me.slotName==="cuda.shares"?parseFloat(String(me.quantity)):parseInt(String(me.quantity),10)}:{}},enabledAutomaticShmem:!Se,mount_ids:(h.extraMounts??[]).map(Ee=>Ee.vfolderId.replace(/-/g,"")),mount_id_map:Nn((h.extraMounts??[]).filter(Ee=>!!Ee.mountDestination).map(Ee=>[Ee.vfolderId.replace(/-/g,""),Ee.mountDestination])),runtimeVariantId:((he=h.modelRuntimeConfig)==null?void 0:he.runtimeVariantId)??void 0,modelFolderId:(Ae=h.modelMountConfig)!=null&&Ae.vfolderId?zl("VirtualFolderNode",h.modelMountConfig.vfolderId):void 0,mountDestination:((rl=h.modelMountConfig)==null?void 0:rl.mountDestination)??"/models",definitionPath:(($e=h.modelMountConfig)==null?void 0:$e.definitionPath)??void 0,environments:(yl=(tl=h.imageV2)==null?void 0:tl.identity)!=null&&yl.canonicalName?{version:h.imageV2.identity.architecture?`${h.imageV2.identity.canonicalName}@${h.imageV2.identity.architecture}`:h.imageV2.identity.canonicalName}:void 0,environ:(((Rl=(Ml=h.modelRuntimeConfig)==null?void 0:Ml.environ)==null?void 0:Rl.entries)??[]).map(Ee=>({variable:Ee.name,value:Ee.value})),commandEnableHealthCheck:!!be,commandHealthCheck:(be==null?void 0:be.path)??void 0,commandInitialDelay:(be==null?void 0:be.initialDelay)??void 0,commandMaxRetries:(be==null?void 0:be.maxRetries)??void 0,commandInterval:(be==null?void 0:be.interval)??void 0,commandMaxWaitTime:(be==null?void 0:be.maxWaitTime)??void 0,commandExpectedStatusCode:(be==null?void 0:be.expectedStatusCode)??void 0,...He&&Oe?{customDefinitionMode:"command",startCommand:Ua(Oe.startCommand??[]),commandPort:Oe.port,commandModelMount:Qe??"/models"}:_e?{customDefinitionMode:"file"}:{}})},ke=j.useEffectEvent(()=>{K&&(D.setFieldsValue(K),M(null))}),Re=j.useEffectEvent(()=>{_&&(C.setFieldsValue(_),Y(null))}),Fe=j.useEffectEvent(()=>{W||S&&(re(S),Q(!0))}),De=j.useEffectEvent(()=>{H&&u&&(re(u),V(!1),G(!0),s.success(a("deployment.CurrentRevisionConfigurationLoaded")))});j.useEffect(()=>{w==="custom"?(ke(),Fe(),De()):Re()},[w]);const xe=()=>{if(u){if(w==="custom"){re(u),G(!0),s.success(a("deployment.CurrentRevisionConfigurationLoaded"));return}V(!0),I("custom")}},ae=h=>{const X=U.current;if(!X||!h)return[];const le={};for(const[oe,me]of Object.entries(h))me==null||me===""||(le[oe]=String(me));return Ya(X,le,L.current)},ve=()=>{requestAnimationFrame(()=>{const h=document.querySelector(".ant-modal-body .ant-form-item-has-error");h&&h.scrollIntoView({behavior:"smooth",block:"start"})})},je=async h=>{var al,il,sl,ol,Ie;const X=(Te,Ve)=>{D.setFields([{name:Te,errors:[a(Ve)]}]),D.scrollToField(Te,{behavior:"smooth",block:"center"})};let le=(il=(al=h.environments)==null?void 0:al.image)==null?void 0:il.id;const oe=(ol=(sl=h.environments)==null?void 0:sl.manual)==null?void 0:ol.trim(),me=oe?["environments","manual"]:["environments","version"];if(!le&&oe){const[Te,Ve]=oe.split("@");B(!0);try{const Ye=await Ke.fetchQuery(c,xt,{reference:Te,architecture:Ve||null},{fetchPolicy:"network-only"}).toPromise();le=((Ie=Ye==null?void 0:Ye.image)==null?void 0:Ie.id)??void 0}catch(Ye){y.error("[DeploymentAddRevisionModal] failed to resolve manual image reference",Ye),s.error(a("general.ErrorOccurred"));return}finally{B(!1)}if(!le){X(me,"modelService.ManualImageNotFound");return}}if(!le){X(me,"modelService.ImageRequired");return}const Se=Vl(le);if(!Se){X(me,"modelService.ImageRequired");return}const Le=[{resourceType:"cpu",quantity:String(h.resource.cpu)},{resourceType:"mem",quantity:h.resource.mem}];h.resource.acceleratorType&&h.resource.accelerator&&h.resource.accelerator>0&&Le.push({resourceType:h.resource.acceleratorType,quantity:String(h.resource.accelerator)});const _e=[];h.resource.shmem&&_e.push({name:"shmem",value:h.resource.shmem});const Be=h.cluster_mode==="single-node"||h.cluster_mode==="multi-node"&&h.cluster_size===1?"SINGLE_NODE":"MULTI_NODE",Oe=h.vfoldersNameMap??{},Qe=(h.mount_ids??[]).map(Te=>{var Ye;const Ve=((Ye=h.mount_id_map)==null?void 0:Ye[Te])||ee.current[Te]||(Oe[Te]?`/home/work/${Oe[Te]}`:`/home/work/${Te}`);return{vfolderId:Wn(Te),mountDestination:Ve}}),He=(v[h.runtimeVariantId]??"")==="custom",qe=h.customDefinitionMode==="command",We={};for(const{variable:Te,value:Ve}of h.environ??[])Te&&(We[Te]=Ve);const we=Object.entries(We).map(([Te,Ve])=>({name:Te,value:Ve})),ze=!!h.commandEnableHealthCheck,nl=(()=>{const Te={path:h.commandHealthCheck,interval:h.commandInterval,maxRetries:h.commandMaxRetries,maxWaitTime:h.commandMaxWaitTime,initialDelay:h.commandInitialDelay,expectedStatusCode:h.commandExpectedStatusCode};return k?ze?{enable:!0,...Te}:{enable:!1}:ze?Te:null})(),Ne=He||!b?[]:ae(h.runtimeParams),Ge=He&&qe&&h.startCommand?{models:[{name:"model",modelPath:h.commandModelMount??"/models",service:{preStartActions:[],startCommand:Wa(h.startCommand??""),port:h.commandPort??8e3,healthCheck:nl}}]}:ze?{models:[{service:{healthCheck:nl}}]}:null,ul=He&&qe?h.commandModelMount??"/models":h.mountDestination||"/models";ue({variables:{input:{deploymentId:Ze((o==null?void 0:o.id)??"")??(o==null?void 0:o.id)??"",clusterConfig:{mode:Be,size:h.cluster_size},resourceConfig:{resourceSlots:{entries:Le},resourceOpts:_e.length>0?{entries:_e}:null},image:{id:Se},modelRuntimeConfig:{runtimeVariantId:h.runtimeVariantId,environ:we.length>0?{entries:we}:null,...b&&{runtimeVariantPresetValues:Ne.length>0?Ne:null}},modelMountConfig:{vfolderId:Ze(h.modelFolderId),mountDestination:ul,definitionPath:h.definitionPath},modelDefinition:Ge,extraMounts:Qe.length>0?Qe:null,options:{autoActivate:$}}},onCompleted:(Te,Ve)=>{var Ye,Sl;if(Ve&&Ve.length>0){const he=Ve[0],Ae=(Ye=he==null?void 0:he.message)==null?void 0:Ye.includes("Another deployment is already in progress");s.error(Ae?a("deployment.AnotherDeploymentInProgress"):(he==null?void 0:he.message)??a("general.ErrorOccurred"));return}D.resetFields(),s.success(a("deployment.RevisionAdded")),l(!0,(Sl=Te.addModelRevision)==null?void 0:Sl.revision)},onError:Te=>{var Ye;const Ve=(Ye=Te.message)==null?void 0:Ye.includes("Another deployment is already in progress");s.error(Ve?a("deployment.AnotherDeploymentInProgress"):Te.message??a("general.ErrorOccurred"))}})},Ce=h=>{ue({variables:{input:{deploymentId:Ze((o==null?void 0:o.id)??"")??(o==null?void 0:o.id)??"",revisionPresetId:h.revisionPresetId,modelMountConfig:{vfolderId:Ze(h.modelFolderId),mountDestination:"/models"},options:{autoActivate:$}}},onCompleted:(X,le)=>{var oe,me;if(le&&le.length>0){const Se=le[0],Le=(oe=Se==null?void 0:Se.message)==null?void 0:oe.includes("Another deployment is already in progress");y.error("[DeploymentAddRevisionModal] addModelRevision (preset) returned errors",le),s.error(Le?a("deployment.AnotherDeploymentInProgress"):(Se==null?void 0:Se.message)??a("general.ErrorOccurred"));return}C.resetFields(),s.success(a("deployment.RevisionAdded")),l(!0,(me=X.addModelRevision)==null?void 0:me.revision)},onError:X=>{var oe;const le=(oe=X.message)==null?void 0:oe.includes("Another deployment is already in progress");y.error("[DeploymentAddRevisionModal] addModelRevision (preset) failed",X),s.error(le?a("deployment.AnotherDeploymentInProgress"):X.message??a("general.ErrorOccurred"))}})},Me=async()=>{const h=w==="preset"?C:D;try{await h.validateFields()}catch{ve();return}h.submit()};return n.jsxs($l,{open:r,title:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"md",wrap:"wrap",style:{paddingRight:d.paddingLG},children:[n.jsx("span",{children:a("deployment.AddRevision")}),n.jsx(jn,{value:w,onChange:ce,options:[{label:a("deployment.PresetMode"),value:"preset"},{label:a("deployment.CustomMode"),value:"custom"}],style:{fontWeight:"normal"}})]}),width:720,footer:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"sm",children:[n.jsx(Pn,{checked:$,onChange:h=>z(h.target.checked),disabled:w==="preset"&&q,children:a("deployment.AutoApply")}),n.jsxs(ie,{direction:"row",align:"center",gap:"xs",children:[n.jsx(ml,{onClick:()=>l(),children:a("button.Cancel")}),n.jsx(ml,{type:"primary",loading:fe||P,onClick:Me,disabled:w==="preset"&&q,children:a("deployment.AddRevision")})]})]}),onCancel:()=>l(),confirmLoading:fe||P,destroyOnHidden:!0,...t,children:[u&&!i&&!N?n.jsx(Tl,{type:"info",showIcon:!0,style:{marginBottom:d.marginMD},title:a("deployment.CurrentRevisionAvailableDescription"),action:n.jsx(ml,{size:"small",onClick:xe,children:a("deployment.LoadCurrentRevision")})}):null,w==="preset"?q?n.jsx(Tl,{type:"info",showIcon:!0,style:{marginTop:d.marginXS},title:a("deployment.NoPresetsAvailable"),description:a("deployment.NoPresetsAvailableSwitchToCustom")}):n.jsxs(ge,{form:C,layout:"vertical",style:{marginTop:d.marginXS},onFinish:Ce,onFinishFailed:ve,initialValues:{modelFolderId:ye},children:[n.jsx(ge.Item,{label:a("modelStore.Preset"),tooltip:a("modelStore.PresetTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(j.Suspense,{fallback:n.jsx(ql,{loading:!0,style:{flex:1}}),children:n.jsx(ge.Item,{name:"revisionPresetId",noStyle:!0,rules:[{required:!0}],children:n.jsx(ca,{style:{flex:1}})})}),n.jsx(ge.Item,{dependencies:["revisionPresetId"],noStyle:!0,children:({getFieldValue:h})=>{const X=h("revisionPresetId");return n.jsx(Ul.Compact,{children:n.jsx(cl,{title:a("modelService.DeploymentPresetDetail"),children:n.jsx(ml,{icon:n.jsx(ma,{}),disabled:!X,onClick:()=>{X&&A(X)}})})})}})]})}),n.jsx(ge.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(j.Suspense,{fallback:n.jsx(ql,{loading:!0,style:{flex:1}}),children:n.jsx(ge.Item,{name:"modelFolderId",label:a("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(On,{ref:x,currentProjectId:m??void 0,disabled:!m,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(ge.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:h})=>{const X=h("modelFolderId");return n.jsxs(Ul.Compact,{children:[n.jsx(cl,{title:a("modelService.OpenFolder"),children:n.jsx(ml,{icon:n.jsx($n,{}),disabled:!X,onClick:()=>{X&&f(Ze(X))}})}),n.jsx(cl,{title:a("data.CreateANewStorageFolder"),children:n.jsx(ml,{icon:n.jsx(Ll,{}),onClick:()=>R(!0)})}),n.jsx(cl,{title:a("button.Refresh"),children:n.jsx(ml,{icon:n.jsx(Ln,{}),onClick:()=>{j.startTransition(()=>{var le;(le=x.current)==null||le.refetch()})}})})]})}})]})})]},"preset-form"):n.jsxs(ge,{form:D,layout:"vertical",style:{marginTop:d.marginXS},onFinish:je,onFinishFailed:ve,initialValues:Sa({},ha,{resourceGroup:(Je=o==null?void 0:o.metadata)==null?void 0:Je.resourceGroupName,customDefinitionMode:"command",commandEnableHealthCheck:!1,environ:[]}),children:[n.jsx(rn,{children:a("deployment.step.ModelAndRuntime")}),n.jsx(ge.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(j.Suspense,{fallback:n.jsx(ql,{loading:!0,style:{flex:1}}),children:n.jsx(ge.Item,{name:"modelFolderId",label:a("deployment.ModelFolder"),noStyle:!0,rules:[{required:!0}],children:n.jsx(On,{ref:F,currentProjectId:m??void 0,disabled:!m,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(ge.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:h})=>{const X=h("modelFolderId");return n.jsxs(Ul.Compact,{children:[n.jsx(cl,{title:a("modelService.OpenFolder"),children:n.jsx(ml,{icon:n.jsx($n,{}),disabled:!X,onClick:()=>{X&&f(Ze(X))}})}),n.jsx(cl,{title:a("data.CreateANewStorageFolder"),children:n.jsx(ml,{icon:n.jsx(Ll,{}),onClick:()=>R(!0)})}),n.jsx(cl,{title:a("button.Refresh"),children:n.jsx(ml,{icon:n.jsx(Ln,{}),onClick:()=>{j.startTransition(()=>{var le;(le=F.current)==null||le.refetch()})}})})]})}})]})}),n.jsx(j.Suspense,{fallback:n.jsx(ql,{loading:!0,style:{width:"100%"}}),children:n.jsx(ge.Item,{name:"runtimeVariantId",label:a("deployment.RuntimeVariant"),tooltip:a("deployment.RuntimeVariantTooltip"),rules:[{required:!0},{warningOnly:!0,validator:async(h,X)=>{const le=v[X];return le&&le!=="custom"?Promise.reject(a("modelService.RuntimeVariantDefaultCommandAppliedNote")):Promise.resolve()}}],children:n.jsx(oi,{onResolvedNamesChange:h=>E(X=>({...X,...h}))})})}),n.jsx(ge.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:h})=>{const X=h("runtimeVariantId"),le=v[X];return!le||le==="custom"?null:n.jsx("div",{style:{marginBottom:d.marginMD},children:n.jsx(j.Suspense,{fallback:null,children:n.jsx(Ga,{runtimeVariant:le,onTouchedKeysChange:oe=>{L.current=oe},onGroupsLoaded:oe=>{U.current=oe},initialPresetValues:Z})})})}}),n.jsx(ge.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:h})=>{const X=h("runtimeVariantId");return v[X]!=="custom"?null:n.jsxs(n.Fragment,{children:[n.jsx(ge.Item,{name:"customDefinitionMode",noStyle:!0,children:n.jsx(jn,{options:[{label:a("modelService.EnterCommand"),value:"command"},{label:a("modelService.UseConfigFile"),value:"file"}],style:{marginBottom:d.marginMD}})}),n.jsx(ge.Item,{dependencies:["customDefinitionMode"],noStyle:!0,children:({getFieldValue:oe})=>oe("customDefinitionMode")==="command"?n.jsxs(n.Fragment,{children:[n.jsx(ge.Item,{name:"startCommand",label:a("modelService.StartCommand"),tooltip:a("modelService.StartCommandTooltip"),extra:a("modelService.StartCommandHelperShell"),rules:[{required:!0,whitespace:!0}],children:n.jsx(Hl.TextArea,{placeholder:a("modelService.StartCommandPlaceholder"),autoSize:{minRows:2}})}),n.jsx(ge.Item,{name:"commandModelMount",label:a("modelService.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),children:n.jsx(Hl,{placeholder:"/models",allowClear:!0})}),n.jsx(ge.Item,{name:"commandPort",label:a("modelService.Port"),tooltip:a("modelService.PortTooltip"),children:n.jsx(gl,{min:2,max:65535,placeholder:"8000",style:{width:"100%"}})})]}):n.jsxs(ie,{gap:"sm",children:[n.jsx(ge.Item,{name:"mountDestination",label:a("modelService.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),rules:[{required:!0}],style:{flex:1},children:n.jsx(Hl,{allowClear:!0,placeholder:"/models"})}),n.jsx(ge.Item,{name:"definitionPath",label:a("deployment.ModelDefinitionPath"),tooltip:a("modelService.ModelDefinitionPathTooltip"),style:{flex:1},children:n.jsx(Hl,{allowClear:!0,placeholder:"model-definition.yaml"})})]})})]})}}),n.jsx(ge.Item,{name:"commandEnableHealthCheck",valuePropName:"checked",style:{marginBottom:d.marginXS},children:n.jsx(Pn,{children:a("modelService.EnableHealthCheck")})}),n.jsx(ge.Item,{dependencies:["commandEnableHealthCheck"],noStyle:!0,children:({getFieldValue:h})=>h("commandEnableHealthCheck")?n.jsxs(ie,{direction:"column",align:"stretch",gap:"xs",children:[n.jsx(ge.Item,{name:"commandHealthCheck",label:a("adminDeploymentPreset.modelDef.HealthCheckPath"),tooltip:a("modelService.HealthCheckTooltip"),rules:[{required:!0}],children:n.jsx(Hl,{placeholder:a("general.Example",{value:"/health"}),allowClear:!0})}),n.jsxs(ie,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(ge.Item,{name:"commandInterval",label:a("adminDeploymentPreset.modelDef.HealthCheckInterval"),tooltip:a("modelService.IntervalTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:1,placeholder:a("general.Example",{value:"10"}),suffix:a("time.Sec"),style:{width:"100%"}})}),n.jsx(ge.Item,{name:"commandMaxRetries",label:a("adminDeploymentPreset.modelDef.HealthCheckMaxRetries"),tooltip:a("modelService.MaxRetriesTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:1,placeholder:a("general.Example",{value:"10"}),style:{width:"100%"}})}),n.jsx(ge.Item,{name:"commandMaxWaitTime",label:a("adminDeploymentPreset.modelDef.HealthCheckMaxWaitTime"),tooltip:a("modelService.MaxWaitTimeTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:1,placeholder:a("general.Example",{value:"15"}),suffix:a("time.Sec"),style:{width:"100%"}})})]}),n.jsxs(ie,{gap:"md",wrap:"wrap",align:"end",children:[n.jsx(ge.Item,{name:"commandExpectedStatusCode",label:a("adminDeploymentPreset.modelDef.HealthCheckExpectedStatus"),tooltip:a("modelService.ExpectedStatusTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:101,max:599,placeholder:a("general.Example",{value:"200"}),style:{width:"100%"}})}),n.jsx(ge.Item,{name:"commandInitialDelay",label:a("adminDeploymentPreset.modelDef.HealthCheckInitialDelay"),tooltip:a("modelService.InitialDelayTooltip"),rules:[{required:!0}],style:{flex:1,minWidth:160},children:n.jsx(gl,{min:0,placeholder:a("general.Example",{value:"60"}),suffix:a("time.Sec"),style:{width:"100%"}})}),n.jsx("div",{style:{flex:1,minWidth:160}})]})]}):null}),n.jsx(rn,{children:a("session.launcher.Environments")}),n.jsx(j.Suspense,{fallback:n.jsx(vl,{active:!0,paragraph:{rows:2}}),children:n.jsx(ga,{})}),n.jsx(ya,{name:"environ",formItemProps:{validateTrigger:["onChange","onBlur"]}}),n.jsx(rn,{children:a("deployment.step.ClusterAndResources")}),n.jsx(j.Suspense,{fallback:n.jsx(vl,{active:!0,paragraph:{rows:4}}),children:n.jsx(pa,{enableResourcePresets:!0,hideResourceGroupFormItem:!0})}),n.jsx(fa,{items:[{key:"advanced",label:a("session.launcher.AdvancedSettings"),children:n.jsx(j.Suspense,{fallback:n.jsx(vl,{active:!0}),children:n.jsx(ge.Item,{noStyle:!0,dependencies:["modelFolderId","mount_id_map","mount_ids"],children:({getFieldValue:h})=>{var oe;const X=h("modelFolderId"),le=X?(oe=Vl(String(X)))==null?void 0:oe.replace(/-/g,""):void 0;return n.jsx(ka,{label:a("modelService.AdditionalMounts"),tooltip:a("modelService.AdditionalMountsTooltip"),rowKey:"id",tableProps:{scroll:{x:"max-content",y:300}},rowFilter:me=>{var Se;return me.usage_mode!=="model"&&me.status==="ready"&&!((Se=me.name)!=null&&Se.startsWith("."))&&me.id!==le}})}})})}]})]},"custom-form"),ne&&n.jsx(j.Suspense,{fallback:null,children:n.jsx(Vi,{presetId:ne,onCancel:()=>A(null)})}),n.jsx(va,{open:T,initialValues:{usage_mode:"model"},onRequestClose:h=>{if(R(!1),h!=null&&h.id){const X=Vl(h.id);if(!X)return;const le=zl("VirtualFolderNode",X),oe=w==="preset"?C:D,me=w==="preset"?x:F;oe.setFieldValue("modelFolderId",le),j.startTransition(()=>{var Se;(Se=me.current)==null||Se.refetch()})}}})]})},Lt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAutoScalingRulePayload",kind:"LinkedField",name:"deleteAutoScalingRule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAutoScalingCardDeleteMutation",selections:e},params:{cacheID:"1b7b8f1adf6afd81d338607d63841181",id:null,metadata:{},name:"DeploymentAutoScalingCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAutoScalingCardDeleteMutation(
  $input: DeleteAutoScalingRuleInput!
) {
  deleteAutoScalingRule(input: $input) {
    id
  }
}
`}}})();Lt.hash="051eb6f0b4919363bd328fca5366d60b";const jt=(function(){var l=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardPresetsQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAutoScalingCardPresetsQuery",selections:l},params:{cacheID:"cc679b7f385bc973b5b68d9964531688",id:null,metadata:{},name:"DeploymentAutoScalingCardPresetsQuery",operationKind:"query",text:`query DeploymentAutoScalingCardPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}})();jt.hash="6d5f2bbfca84b48a6aa4d1e118d88fdb";const Pt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[s,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[c,o,{args:null,kind:"FragmentSpread",name:"AutoScalingRuleListNodesFragment"},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,r,i,t,e],kind:"Operation",name:"DeploymentAutoScalingCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[s,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[c,o,{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},c],storageKey:null}]},params:{cacheID:"41c9b35cb41550bd8f8cde32c8b21c1a",id:null,metadata:{},name:"DeploymentAutoScalingCardListQuery",operationKind:"query",text:`query DeploymentAutoScalingCardListQuery(
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
`}}})();Pt.hash="56b6637e50dbda972f85edac73bc04b5";const Nt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Nt.hash="a7ebc88f8233e21188ec26bb29ecdb73";const Vt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"UpdateAutoScalingRulePayload",kind:"LinkedField",name:"updateAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalUpdateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalUpdateMutation",selections:e},params:{cacheID:"f5194bd994f4693e29536fec36e4f0e4",id:null,metadata:{},name:"AutoScalingRuleEditorModalUpdateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalUpdateMutation(
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
`}}})();Vt.hash="8e953443e1aa963b955810e5f97de017";const _t=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAutoScalingRulePayload",kind:"LinkedField",name:"createAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalCreateMutation",selections:e},params:{cacheID:"c7c250dabfc49b66cf1aebbff6414d44",id:null,metadata:{},name:"AutoScalingRuleEditorModalCreateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalCreateMutation(
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
`}}})();_t.hash="7afa475334295923b7754d0563a8b919";const Et={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],type:"AutoScalingRule",abstractKey:null};Et.hash="9dff1f6ce3b17626029eee3484220a7d";const Ot=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[l,e,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"categoryId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queryTemplate",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,concreteType:"QueryPresetCategory",kind:"LinkedField",name:"category",plural:!1,selections:[l,e],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalPresetsQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleEditorModalPresetsQuery",selections:i},params:{cacheID:"04d06fec5284e709aaee3606d8a4bb53",id:null,metadata:{},name:"AutoScalingRuleEditorModalPresetsQuery",operationKind:"query",text:`query AutoScalingRuleEditorModalPresetsQuery {
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
`}}})();Ot.hash="6582d4cf067148f5b39755e919c0f4f2";const on={KERNEL:["cpu_util","mem","net_rx","net_tx"],INFERENCE_FRAMEWORK:[]},Bn=l=>l?l.minThreshold!=null&&l.maxThreshold!=null?"scale_in_out":l.maxThreshold!=null?"scale_out":"scale_in":"scale_out",_i=l=>{"use memo";var Sl;const e=Ue.c(196),{autoScalingRule:i,formRef:r}=l,{t}=ll(),{token:a}=Dl.useToken(),d=Kn(),s=xa();let c;e[0]!==d?(c=d.supports("prometheus-auto-scaling-rule"),e[0]=d,e[1]=c):c=e[1];const o=c;let g,u;e[2]===Symbol.for("react.memo_cache_sentinel")?(g=Ot,u={},e[2]=g,e[3]=u):(g=e[2],u=e[3]);const{prometheusQueryPresets:S}=Ke.useLazyLoadQuery(g,u);let m;e[4]!==(S==null?void 0:S.edges)?(m=Ra(Fl(S==null?void 0:S.edges,Oi)),e[4]=S==null?void 0:S.edges,e[5]=m):m=e[5];const y=m;let f;e[6]!==i?(f=Bn(i),e[6]=i,e[7]=f):f=e[7];const[p,k]=j.useState(f),[b,x]=j.useState((i==null?void 0:i.metricSource)||"KERNEL");let F;e[8]!==i||e[9]!==y?(F=i!=null&&i.prometheusQueryPresetId?(Sl=y.find(he=>Ze(he.id)===i.prometheusQueryPresetId))==null?void 0:Sl.id:void 0,e[8]=i,e[9]=y,e[10]=F):F=e[10];const[T,R]=j.useState(F);let D;e[11]!==(i==null?void 0:i.metricSource)?(D=on[(i==null?void 0:i.metricSource)||"KERNEL"]||[],e[11]=i==null?void 0:i.metricSource,e[12]=D):D=e[12];const[C,$]=j.useState(D);let z;if(e[13]!==y||e[14]!==T){let he;e[16]!==T?(he=Ae=>Ae.id===T,e[16]=T,e[17]=he):he=e[17],z=y.find(he),e[13]=y,e[14]=T,e[15]=z}else z=e[15];const P=z;let B;if(e[18]!==y){const he=Ja(y,["rank"],["asc"]),Ae=he.filter(wi),rl=he.filter($i),$e=Bi,tl=Ka(Ae,Hi),yl=Object.entries(tl).map(Ml=>{const[Rl,Ee]=Ml;return{label:Rl,options:Ee.map($e)}});B=rl.length>0?[...yl,...rl.map($e)]:yl,e[18]=y,e[19]=B}else B=e[19];const O=B;let I;e[20]!==i||e[21]!==T?(I=()=>{if(i){const he=Bn(i);let Ae;return he==="scale_in"&&i.minThreshold!=null?Ae=Number(i.minThreshold):he==="scale_out"&&i.maxThreshold!=null&&(Ae=Number(i.maxThreshold)),{metricSource:i.metricSource,metricName:i.metricName,prometheusQueryPresetId:T,conditionMode:he,threshold:Ae,minThreshold:i.minThreshold!=null?Number(i.minThreshold):void 0,maxThreshold:i.maxThreshold!=null?Number(i.maxThreshold):void 0,stepSize:Math.abs(i.stepSize),timeWindow:i.timeWindow,minReplicas:i.minReplicas??void 0,maxReplicas:i.maxReplicas??void 0}}return{metricSource:"KERNEL",conditionMode:"scale_out",stepSize:1,timeWindow:300,minReplicas:0,maxReplicas:5}},e[20]=i,e[21]=T,e[22]=I):I=e[22];const w=I,N=b==="PROMETHEUS";let G;e[23]!==w?(G=w(),e[23]=w,e[24]=G):G=e[24];let W;e[25]!==t?(W=t("autoScalingRule.MetricSource"),e[25]=t,e[26]=W):W=e[26];let Q;e[27]!==t?(Q=t("autoScalingRule.MetricSourceTooltip"),e[27]=t,e[28]=Q):Q=e[28];let H;e[29]===Symbol.for("react.memo_cache_sentinel")?(H=[{required:!0}],e[29]=H):H=e[29];let V;e[30]!==r?(V=he=>{var Ae,rl;if(x(he),(Ae=r.current)==null||Ae.setFieldsValue({metricName:void 0}),he!=="PROMETHEUS")$(on[he]||[]),R(void 0);else{const $e=(rl=r.current)==null?void 0:rl.getFieldValue("prometheusQueryPresetId");$e&&R($e)}},e[30]=r,e[31]=V):V=e[31];let K;e[32]!==t?(K=t("autoScalingRule.MetricSourceKernel"),e[32]=t,e[33]=K):K=e[33];let M;e[34]!==K?(M={label:K,value:"KERNEL"},e[34]=K,e[35]=M):M=e[35];let _;e[36]!==o||e[37]!==t?(_=o?[]:[{label:t("autoScalingRule.MetricSourceInferenceFramework"),value:"INFERENCE_FRAMEWORK"}],e[36]=o,e[37]=t,e[38]=_):_=e[38];let Y;e[39]!==t?(Y=t("autoScalingRule.MetricSourcePrometheus"),e[39]=t,e[40]=Y):Y=e[40];let ne;e[41]!==Y?(ne={label:Y,value:"PROMETHEUS"},e[41]=Y,e[42]=ne):ne=e[42];let A;e[43]!==M||e[44]!==_||e[45]!==ne?(A=[M,..._,ne],e[43]=M,e[44]=_,e[45]=ne,e[46]=A):A=e[46];let v;e[47]!==V||e[48]!==A?(v=n.jsx(gn,{onChange:V,options:A}),e[47]=V,e[48]=A,e[49]=v):v=e[49];let E;e[50]!==W||e[51]!==Q||e[52]!==v?(E=n.jsx(ge.Item,{label:W,name:"metricSource",tooltip:Q,rules:H,children:v}),e[50]=W,e[51]=Q,e[52]=v,e[53]=E):E=e[53];let L;e[54]!==t?(L=t("autoScalingRule.MetricName"),e[54]=t,e[55]=L):L=e[55];let U;e[56]!==t?(U=t("autoScalingRule.MetricNameTooltip"),e[56]=t,e[57]=U):U=e[57];const Z=!N;let J;e[58]!==Z?(J=[{required:Z}],e[58]=Z,e[59]=J):J=e[59];let ee;e[60]!==t?(ee=t("autoScalingRule.MetricName"),e[60]=t,e[61]=ee):ee=e[61];let q;e[62]!==C?(q=Fl(C,Qi),e[62]=C,e[63]=q):q=e[63];let te;e[64]!==r?(te={onSearch:he=>{var rl;const Ae=((rl=r.current)==null?void 0:rl.getFieldValue("metricSource"))||"KERNEL";$(Ia(on[Ae]||[],$e=>$e.includes(he)))}},e[64]=r,e[65]=te):te=e[65];let ye;e[66]!==ee||e[67]!==q||e[68]!==te?(ye=n.jsx(Da,{placeholder:ee,options:q,showSearch:te,allowClear:!0,popupMatchSelectWidth:!1}),e[66]=ee,e[67]=q,e[68]=te,e[69]=ye):ye=e[69];let de;e[70]!==N||e[71]!==L||e[72]!==U||e[73]!==J||e[74]!==ye?(de=n.jsx(ge.Item,{label:L,name:"metricName",hidden:N,tooltip:U,rules:J,children:ye}),e[70]=N,e[71]=L,e[72]=U,e[73]=J,e[74]=ye,e[75]=de):de=e[75];let pe;e[76]!==s||e[77]!==r||e[78]!==N||e[79]!==y||e[80]!==O||e[81]!==P||e[82]!==t||e[83]!==a.fontSizeSM?(pe=N&&n.jsx(n.Fragment,{children:n.jsx(ge.Item,{label:`${t("autoScalingRule.MetricName")} (${t("autoScalingRule.PrometheusPreset")})`,name:"prometheusQueryPresetId",tooltip:t("autoScalingRule.PrometheusPresetTooltip"),rules:[{required:!0,message:t("autoScalingRule.PrometheusPresetRequired")}],extra:s==="superadmin"&&P?n.jsx(Xa,{queryTemplate:P.queryTemplate},P.id):void 0,children:n.jsx(gn,{onChange:he=>{var rl,$e;R(he);const Ae=y.find(tl=>tl.id===he);if(Ae){(rl=r.current)==null||rl.setFieldsValue({metricName:Ae.metricName});const tl=Ae.timeWindow!=null?Number(Ae.timeWindow):void 0;tl!=null&&!isNaN(tl)&&(($e=r.current)==null||$e.setFieldsValue({timeWindow:tl}))}},placeholder:t("autoScalingRule.SelectPrometheusPreset"),showSearch:{filterOption:qi},options:O,optionRender:he=>n.jsxs(ie,{direction:"column",align:"start",children:[he.label,he.data.description&&n.jsx(el.Text,{type:"secondary",style:{fontSize:a.fontSizeSM},ellipsis:!0,children:he.data.description})]}),allowClear:!0,onClear:()=>R(void 0)})})}),e[76]=s,e[77]=r,e[78]=N,e[79]=y,e[80]=O,e[81]=P,e[82]=t,e[83]=a.fontSizeSM,e[84]=pe):pe=e[84];let ue;e[85]!==t?(ue=t("autoScalingRule.Condition"),e[85]=t,e[86]=ue):ue=e[86];let fe;e[87]!==t?(fe=t("autoScalingRule.ConditionTooltip"),e[87]=t,e[88]=fe):fe=e[88];let se;e[89]===Symbol.for("react.memo_cache_sentinel")?(se=he=>{k(he.target.value)},e[89]=se):se=e[89];let ce;e[90]!==a.marginSM?(ce={marginBottom:a.marginSM},e[90]=a.marginSM,e[91]=ce):ce=e[91];let re;e[92]!==t?(re=t("autoScalingRule.ScaleIn"),e[92]=t,e[93]=re):re=e[93];let ke;e[94]!==re?(ke={label:re,value:"scale_in"},e[94]=re,e[95]=ke):ke=e[95];let Re;e[96]!==t?(Re=t("autoScalingRule.ScaleOut"),e[96]=t,e[97]=Re):Re=e[97];let Fe;e[98]!==Re?(Fe={label:Re,value:"scale_out"},e[98]=Re,e[99]=Fe):Fe=e[99];let De;e[100]!==t?(De=t("autoScalingRule.ScaleInAndOut"),e[100]=t,e[101]=De):De=e[101];let xe;e[102]!==De?(xe={label:De,value:"scale_in_out"},e[102]=De,e[103]=xe):xe=e[103];let ae;e[104]!==ke||e[105]!==Fe||e[106]!==xe?(ae=[ke,Fe,xe],e[104]=ke,e[105]=Fe,e[106]=xe,e[107]=ae):ae=e[107];let ve;e[108]!==ce||e[109]!==ae?(ve=n.jsx(ge.Item,{name:"conditionMode",noStyle:!0,children:n.jsx(Ta.Group,{optionType:"button",onChange:se,style:ce,options:ae})}),e[108]=ce,e[109]=ae,e[110]=ve):ve=e[110];let je;e[111]!==p||e[112]!==t?(je=p==="scale_in"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(el.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ge.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),e[111]=p,e[112]=t,e[113]=je):je=e[113];let Ce;e[114]!==p||e[115]!==t?(Ce=p==="scale_out"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ge.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(el.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]}),e[114]=p,e[115]=t,e[116]=Ce):Ce=e[116];let Me;e[117]!==p||e[118]!==t?(Me=p==="scale_in_out"&&n.jsxs(ie,{direction:"column",gap:"xs",align:"stretch",children:[n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(el.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ge.Item,{name:"minThreshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.MinThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ge.Item,{name:"maxThreshold",noStyle:!0,dependencies:["minThreshold"],rules:[{required:!0,message:t("autoScalingRule.MaxThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")},he=>{const{getFieldValue:Ae}=he;return{validator(rl,$e){const tl=Ae("minThreshold");return tl!=null&&$e!=null&&tl>=$e?Promise.reject(new Error(t("autoScalingRule.MinMustBeLessThanMax"))):Promise.resolve()}}}],children:n.jsx(gl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(el.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]})]}),e[117]=p,e[118]=t,e[119]=Me):Me=e[119];let Pe;e[120]!==ue||e[121]!==fe||e[122]!==ve||e[123]!==je||e[124]!==Ce||e[125]!==Me?(Pe=n.jsxs(ge.Item,{label:ue,required:!0,tooltip:fe,children:[ve,je,Ce,Me]}),e[120]=ue,e[121]=fe,e[122]=ve,e[123]=je,e[124]=Ce,e[125]=Me,e[126]=Pe):Pe=e[126];let Xe;e[127]!==t?(Xe=t("autoScalingRule.StepSize"),e[127]=t,e[128]=Xe):Xe=e[128];let Je;e[129]!==t?(Je=t("autoScalingRule.StepSizeTooltip"),e[129]=t,e[130]=Je):Je=e[130];let h,X;e[131]===Symbol.for("react.memo_cache_sentinel")?(h={required:!0},X={type:"number",min:1,max:Ql},e[131]=h,e[132]=X):(h=e[131],X=e[132]);let le;e[133]!==t?(le=[h,X,{validator:(he,Ae)=>Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[133]=t,e[134]=le):le=e[134];let oe;e[135]===Symbol.for("react.memo_cache_sentinel")?(oe={width:"100%"},e[135]=oe):oe=e[135];const me=p==="scale_in_out"?"±":p==="scale_out"?"+":"−";let Se;e[136]!==me?(Se=n.jsx(gl,{min:1,step:1,style:oe,prefix:n.jsx(el.Text,{type:"secondary",children:me})}),e[136]=me,e[137]=Se):Se=e[137];let Le;e[138]!==Xe||e[139]!==Je||e[140]!==le||e[141]!==Se?(Le=n.jsx(ge.Item,{label:Xe,name:"stepSize",tooltip:Je,rules:le,children:Se}),e[138]=Xe,e[139]=Je,e[140]=le,e[141]=Se,e[142]=Le):Le=e[142];let _e;e[143]!==t?(_e=t("autoScalingRule.CoolDownSeconds"),e[143]=t,e[144]=_e):_e=e[144];let Be;e[145]!==t?(Be=t("autoScalingRule.CoolDownTooltip"),e[145]=t,e[146]=Be):Be=e[146];let Oe,Qe;e[147]===Symbol.for("react.memo_cache_sentinel")?(Oe={required:!0},Qe={type:"number",min:1},e[147]=Oe,e[148]=Qe):(Oe=e[147],Qe=e[148]);let be;e[149]!==t?(be=[Oe,Qe,{validator:(he,Ae)=>Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[149]=t,e[150]=be):be=e[150];let He;e[151]===Symbol.for("react.memo_cache_sentinel")?(He={width:"100%"},e[151]=He):He=e[151];let qe;e[152]!==t?(qe=t("autoScalingRule.Seconds"),e[152]=t,e[153]=qe):qe=e[153];let We;e[154]!==qe?(We=n.jsx(gl,{min:1,step:1,style:He,suffix:n.jsx(el.Text,{type:"secondary",children:qe})}),e[154]=qe,e[155]=We):We=e[155];let we;e[156]!==_e||e[157]!==Be||e[158]!==be||e[159]!==We?(we=n.jsx(ge.Item,{label:_e,name:"timeWindow",tooltip:Be,rules:be,children:We}),e[156]=_e,e[157]=Be,e[158]=be,e[159]=We,e[160]=we):we=e[160];let ze;e[161]!==t?(ze=t("autoScalingRule.MinReplicas"),e[161]=t,e[162]=ze):ze=e[162];let nl;e[163]!==t?(nl=t("autoScalingRule.MinReplicasTooltip"),e[163]=t,e[164]=nl):nl=e[164];let Ne;e[165]===Symbol.for("react.memo_cache_sentinel")?(Ne={min:0,max:Ql,type:"number"},e[165]=Ne):Ne=e[165];let Ge;e[166]!==t?(Ge=[Ne,{validator:(he,Ae)=>Ae!=null&&Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[166]=t,e[167]=Ge):Ge=e[167];let ul;e[168]===Symbol.for("react.memo_cache_sentinel")?(ul=n.jsx(gl,{min:0,max:Ql,style:{width:"100%"}}),e[168]=ul):ul=e[168];let al;e[169]!==ze||e[170]!==nl||e[171]!==Ge?(al=n.jsx(ge.Item,{label:ze,name:"minReplicas",tooltip:nl,rules:Ge,children:ul}),e[169]=ze,e[170]=nl,e[171]=Ge,e[172]=al):al=e[172];let il;e[173]!==t?(il=t("autoScalingRule.MaxReplicas"),e[173]=t,e[174]=il):il=e[174];let sl;e[175]!==t?(sl=t("autoScalingRule.MaxReplicasTooltip"),e[175]=t,e[176]=sl):sl=e[176];let ol;e[177]===Symbol.for("react.memo_cache_sentinel")?(ol={min:0,max:Ql,type:"number"},e[177]=ol):ol=e[177];let Ie;e[178]!==t?(Ie=[ol,{validator:(he,Ae)=>Ae!=null&&Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[178]=t,e[179]=Ie):Ie=e[179];let Te;e[180]===Symbol.for("react.memo_cache_sentinel")?(Te=n.jsx(gl,{min:0,max:Ql,style:{width:"100%"}}),e[180]=Te):Te=e[180];let Ve;e[181]!==il||e[182]!==sl||e[183]!==Ie?(Ve=n.jsx(ge.Item,{label:il,name:"maxReplicas",tooltip:sl,rules:Ie,children:Te}),e[181]=il,e[182]=sl,e[183]=Ie,e[184]=Ve):Ve=e[184];let Ye;return e[185]!==r||e[186]!==G||e[187]!==E||e[188]!==de||e[189]!==pe||e[190]!==Pe||e[191]!==Le||e[192]!==we||e[193]!==al||e[194]!==Ve?(Ye=n.jsxs(ge,{ref:r,layout:"vertical",initialValues:G,children:[E,de,pe,Pe,Le,we,al,Ve]}),e[185]=r,e[186]=G,e[187]=E,e[188]=de,e[189]=pe,e[190]=Pe,e[191]=Le,e[192]=we,e[193]=al,e[194]=Ve,e[195]=Ye):Ye=e[195],Ye},Ei=l=>{"use memo";const e=Ue.c(34);let i,r,t,a,d;e[0]!==l?({onRequestClose:d,onComplete:a,modelDeploymentId:t,autoScalingRuleFrgmt:i,...r}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=ll(),{message:c}=Pl.useApp(),{logger:o}=Ol();let g;e[6]===Symbol.for("react.memo_cache_sentinel")?(g=Et,e[6]=g):g=e[6];const u=Ke.useFragment(g,i??null),S=j.useRef(null);let m;e[7]===Symbol.for("react.memo_cache_sentinel")?(m=_t,e[7]=m):m=e[7];const[y,f]=Ke.useMutation(m);let p;e[8]===Symbol.for("react.memo_cache_sentinel")?(p=Vt,e[8]=p):p=e[8];const[k,b]=Ke.useMutation(p);let x;e[9]!==u||e[10]!==y||e[11]!==k||e[12]!==o||e[13]!==c||e[14]!==t||e[15]!==a||e[16]!==d||e[17]!==s?(x=()=>{var O;return(O=S.current)==null?void 0:O.validateFields().then(I=>{let w=null,N=null;I.conditionMode==="scale_in_out"?(w=I.minThreshold??null,N=I.maxThreshold??null):I.conditionMode==="scale_in"?w=I.threshold??null:N=I.threshold??null;const G=I.metricName,W=I.metricSource==="PROMETHEUS"&&I.prometheusQueryPresetId?Ze(I.prometheusQueryPresetId):null;u?k({variables:{input:{id:Ze(u.id),metricSource:I.metricSource,metricName:G,minThreshold:w!=null?String(w):null,maxThreshold:N!=null?String(N):null,stepSize:I.stepSize,timeWindow:I.timeWindow,minReplicas:I.minReplicas,maxReplicas:I.maxReplicas,prometheusQueryPresetId:W??void 0}},onCompleted:(Q,H)=>{if(H&&H.length>0){const V=Fl(H,zi);for(const K of V)c.error(K);return}c.success(s("autoScalingRule.SuccessfullyUpdated")),a==null||a(),d(!0)},onError:Q=>{c.error(Q.message)}}):y({variables:{input:{modelDeploymentId:t,metricSource:I.metricSource,metricName:G,minThreshold:w!=null?String(w):null,maxThreshold:N!=null?String(N):null,stepSize:I.stepSize,timeWindow:I.timeWindow,minReplicas:I.minReplicas,maxReplicas:I.maxReplicas,prometheusQueryPresetId:W??void 0}},onCompleted:(Q,H)=>{if(H&&H.length>0){const V=Fl(H,Ui);for(const K of V)c.error(K);return}c.success(s("autoScalingRule.SuccessfullyCreated")),a==null||a(),d(!0)},onError:Q=>{c.error(Q.message)}})}).catch(I=>{o.error(I)})},e[9]=u,e[10]=y,e[11]=k,e[12]=o,e[13]=c,e[14]=t,e[15]=a,e[16]=d,e[17]=s,e[18]=x):x=e[18];const F=x;let T;e[19]!==d?(T=()=>{d(!1)},e[19]=d,e[20]=T):T=e[20];const R=T;let D;e[21]!==u||e[22]!==s?(D=s(u?"autoScalingRule.EditAutoScalingRule":"autoScalingRule.AddAutoScalingRule"),e[21]=u,e[22]=s,e[23]=D):D=e[23];const C=f||b;let $;e[24]===Symbol.for("react.memo_cache_sentinel")?($=n.jsx(vl,{active:!0,paragraph:{rows:6}}),e[24]=$):$=e[24];const z=u??null;let P;e[25]!==z?(P=n.jsx(Jn,{children:n.jsx(ba.Suspense,{fallback:$,children:n.jsx(_i,{autoScalingRule:z,formRef:S})})}),e[25]=z,e[26]=P):P=e[26];let B;return e[27]!==r||e[28]!==R||e[29]!==F||e[30]!==P||e[31]!==D||e[32]!==C?(B=n.jsx($l,{...r,onOk:F,onCancel:R,centered:!0,title:D,confirmLoading:C,children:P}),e[27]=r,e[28]=R,e[29]=F,e[30]=P,e[31]=D,e[32]=C,e[33]=B):B=e[33],B};function Oi(l){return l==null?void 0:l.node}function wi(l){var e;return(e=l.category)==null?void 0:e.name}function $i(l){var e;return!((e=l.category)!=null&&e.name)}function Bi(l){return{label:l.name,value:l.id,description:l.description}}function Hi(l){return l.category.name}function Qi(l){return{label:l,value:l}}function qi(l,e){return String((e==null?void 0:e.label)??"").toLowerCase().includes(l.toLowerCase())}function zi(l){return l.message}function Ui(l){return l.message}const wt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"AutoScalingRuleListNodesFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],type:"AutoScalingRule",abstractKey:null};wt.hash="54a32b764fc7e506f5bddfe218691cd2";const Wi=(l,e,i)=>{const r=l.metricSource==="PROMETHEUS"&&l.prometheusQueryPresetId?(i==null?void 0:i.get(l.prometheusQueryPresetId))??l.metricName:l.metricName,t=l.minThreshold,a=l.maxThreshold;return t!=null&&a!=null?n.jsxs(ie,{direction:"column",gap:"xxs",children:[n.jsxs(ie,{gap:"xs",children:[n.jsx(en,{children:r})," < ",t]}),n.jsxs(ie,{gap:"xs",children:[a," < ",n.jsx(en,{children:r})]})]}):a!=null?n.jsxs(ie,{gap:"xs",children:[a,n.jsx(cl,{title:e("autoScalingRule.MaxThreshold"),children:"<"}),n.jsx(en,{children:r})]}):t!=null?n.jsxs(ie,{gap:"xs",children:[n.jsx(en,{children:r}),n.jsx(cl,{title:e("autoScalingRule.MinThreshold"),children:"<"}),t]}):"-"},Gi=l=>{"use memo";const e=Ue.c(103);let i,r,t,a,d,s,c;e[0]!==l?({autoScalingRulesFrgmt:i,presetMap:s,isEndpointDestroying:r,isOwnedByCurrentUser:t,onEditRule:d,onDeleteRule:a,...c}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d,e[6]=s,e[7]=c):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5],s=e[6],c=e[7]);const{t:o}=ll();let g;e[8]===Symbol.for("react.memo_cache_sentinel")?(g=wt,e[8]=g):g=e[8];const u=Ke.useFragment(g,i);let S;e[9]!==u?(S=Al(u),e[9]=u,e[10]=S):S=e[10];const m=S;let y;e[11]===Symbol.for("react.memo_cache_sentinel")?(y={x:"max-content"},e[11]=y):y=e[11];let f;e[12]!==o?(f=o("autoScalingRule.MetricSource"),e[12]=o,e[13]=f):f=e[13];let p;e[14]!==o?(p=o("autoScalingRule.MetricSourceTooltip"),e[14]=o,e[15]=p):p=e[15];let k;e[16]!==p?(k=n.jsx(pl,{title:p}),e[16]=p,e[17]=k):k=e[17];let b;e[18]!==f||e[19]!==k?(b={key:"metricSource",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[f,k]}),dataIndex:"metricSource",fixed:"left"},e[18]=f,e[19]=k,e[20]=b):b=e[20];let x;e[21]!==o?(x=o("autoScalingRule.Condition"),e[21]=o,e[22]=x):x=e[22];let F;e[23]!==o?(F=o("autoScalingRule.ConditionTooltip"),e[23]=o,e[24]=F):F=e[24];let T;e[25]!==F?(T=n.jsx(pl,{title:F}),e[25]=F,e[26]=T):T=e[26];let R;e[27]!==T||e[28]!==x?(R=n.jsxs(ie,{gap:"xxs",align:"center",children:[x,T]}),e[27]=T,e[28]=x,e[29]=R):R=e[29];let D;e[30]!==r||e[31]!==t||e[32]!==a||e[33]!==d||e[34]!==s||e[35]!==o?(D=(ee,q)=>q?n.jsx(bn,{title:Wi(q,o,s),showActions:"always",actions:[{key:"edit",title:o("button.Edit"),icon:n.jsx(ut,{}),disabled:r||!t,onClick:()=>d(q.id)},{key:"delete",title:o("button.Delete"),icon:n.jsx(xn,{}),type:"danger",disabled:r||!t,onClick:()=>a(q.id,q.metricName??"")}]}):"-",e[30]=r,e[31]=t,e[32]=a,e[33]=d,e[34]=s,e[35]=o,e[36]=D):D=e[36];let C;e[37]!==R||e[38]!==D?(C={key:"condition",title:R,fixed:"left",render:D},e[37]=R,e[38]=D,e[39]=C):C=e[39];let $;e[40]!==o?($=o("autoScalingRule.CoolDownSeconds"),e[40]=o,e[41]=$):$=e[41];let z;e[42]!==o?(z=o("autoScalingRule.CoolDownTooltip"),e[42]=o,e[43]=z):z=e[43];let P;e[44]!==z?(P=n.jsx(pl,{title:z}),e[44]=z,e[45]=P):P=e[45];let B;e[46]!==$||e[47]!==P?(B=n.jsxs(ie,{gap:"xxs",align:"center",children:[$,P]}),e[46]=$,e[47]=P,e[48]=B):B=e[48];let O;e[49]!==o?(O=ee=>ee!=null?o("autoScalingRule.CoolDownSecondsValue",{value:ee}):"-",e[49]=o,e[50]=O):O=e[50];let I;e[51]!==B||e[52]!==O?(I={key:"timeWindow",title:B,dataIndex:"timeWindow",render:O},e[51]=B,e[52]=O,e[53]=I):I=e[53];let w;e[54]!==o?(w=o("autoScalingRule.StepSize"),e[54]=o,e[55]=w):w=e[55];let N;e[56]!==o?(N=o("autoScalingRule.StepSizeTooltip"),e[56]=o,e[57]=N):N=e[57];let G;e[58]!==N?(G=n.jsx(pl,{title:N}),e[58]=N,e[59]=G):G=e[59];let W;e[60]!==w||e[61]!==G?(W={key:"stepSize",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[w,G]}),dataIndex:"stepSize",render:Yi},e[60]=w,e[61]=G,e[62]=W):W=e[62];let Q;e[63]!==o?(Q=o("autoScalingRule.MIN/MAXReplicas"),e[63]=o,e[64]=Q):Q=e[64];let H;e[65]!==o?(H=o("autoScalingRule.MinMaxReplicasTooltip"),e[65]=o,e[66]=H):H=e[66];let V;e[67]!==H?(V=n.jsx(pl,{title:H}),e[67]=H,e[68]=V):V=e[68];let K;e[69]!==Q||e[70]!==V?(K=n.jsxs(ie,{gap:"xxs",align:"center",children:[Q,V]}),e[69]=Q,e[70]=V,e[71]=K):K=e[71];let M;e[72]!==o?(M=(ee,q)=>{if(!(q!=null&&q.stepSize))return"-";const te=q.minThreshold!=null,ye=q.maxThreshold!=null;return te&&ye?n.jsxs("span",{children:[o("autoScalingRule.MinReplicasValue",{value:q==null?void 0:q.minReplicas})," / ",o("autoScalingRule.MaxReplicasValue",{value:q==null?void 0:q.maxReplicas})]}):ye?n.jsx("span",{children:o("autoScalingRule.MaxReplicasValue",{value:q==null?void 0:q.maxReplicas})}):n.jsx("span",{children:o("autoScalingRule.MinReplicasValue",{value:q==null?void 0:q.minReplicas})})},e[72]=o,e[73]=M):M=e[73];let _;e[74]!==K||e[75]!==M?(_={key:"minMaxReplicas",title:K,render:M},e[74]=K,e[75]=M,e[76]=_):_=e[76];let Y;e[77]!==o?(Y=o("autoScalingRule.CreatedAt"),e[77]=o,e[78]=Y):Y=e[78];let ne;e[79]===Symbol.for("react.memo_cache_sentinel")?(ne=["descend","ascend"],e[79]=ne):ne=e[79];let A;e[80]!==Y?(A={key:"createdAt",title:Y,dataIndex:"createdAt",sorter:!0,sortDirections:ne,render:Xi},e[80]=Y,e[81]=A):A=e[81];let v;e[82]!==o?(v=o("autoScalingRule.LastTriggered"),e[82]=o,e[83]=v):v=e[83];let E;e[84]!==o?(E=o("autoScalingRule.LastTriggeredTooltip"),e[84]=o,e[85]=E):E=e[85];let L;e[86]!==E?(L=n.jsx(pl,{title:E}),e[86]=E,e[87]=L):L=e[87];let U;e[88]!==v||e[89]!==L?(U={key:"lastTriggeredAt",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[v,L]}),render:Ji},e[88]=v,e[89]=L,e[90]=U):U=e[90];let Z;e[91]!==C||e[92]!==I||e[93]!==W||e[94]!==_||e[95]!==A||e[96]!==U||e[97]!==b?(Z=[b,C,I,W,_,A,U],e[91]=C,e[92]=I,e[93]=W,e[94]=_,e[95]=A,e[96]=U,e[97]=b,e[98]=Z):Z=e[98];let J;return e[99]!==m||e[100]!==Z||e[101]!==c?(J=n.jsx(El,{scroll:y,rowKey:"id",columns:Z,showSorterTooltip:!1,dataSource:m,...c}),e[99]=m,e[100]=Z,e[101]=c,e[102]=J):J=e[102],J};function Yi(l,e){if(!(e!=null&&e.stepSize))return"-";const i=e.minThreshold!=null,r=e.maxThreshold!=null;if(!i&&!r)return"-";const t=i&&r?"±":r?"+":"−";return n.jsxs(ie,{gap:"xs",children:[n.jsx(el.Text,{children:t}),n.jsx(el.Text,{children:Math.abs(e.stepSize)})]})}function Xi(l,e){return n.jsx("span",{children:e!=null&&e.createdAt?dl(e.createdAt).format("ll LT"):"-"})}function Ji(l,e){return n.jsx("span",{children:e!=null&&e.lastTriggeredAt?dl.utc(e.lastTriggeredAt).tz().format("ll LTS"):"-"})}const Zi=l=>{"use memo";var R,D,C;const e=Ue.c(24),{deploymentFrgmt:i}=l,{t:r}=ll(),{token:t}=Dl.useToken(),[a]=Zn();let d;e[0]===Symbol.for("react.memo_cache_sentinel")?(d=Nt,e[0]=d):d=e[0];const s=Ke.useFragment(d,i);if(!(s!=null&&s.id))return null;const c=(R=s.metadata)==null?void 0:R.status;let o;e[1]!==c?(o=hl(c),e[1]=c,e[2]=o):o=e[2];const g=o,u=((C=(D=s.creator)==null?void 0:D.basicInfo)==null?void 0:C.email)??null,S=!u||u===a.email;let m;e[3]!==r?(m=r("deployment.tab.AutoScaling"),e[3]=r,e[4]=m):m=e[4];let y;e[5]!==r?(y=r("deployment.tab.description.AutoScaling"),e[5]=r,e[6]=y):y=e[6];let f;e[7]!==t.colorTextDescription?(f=n.jsx(Fn,{style:{color:t.colorTextDescription}}),e[7]=t.colorTextDescription,e[8]=f):f=e[8];let p;e[9]!==y||e[10]!==f?(p=n.jsx(cl,{title:y,children:f}),e[9]=y,e[10]=f,e[11]=p):p=e[11];let k;e[12]!==m||e[13]!==p?(k=n.jsxs(ie,{gap:"xs",align:"center",children:[m,p]}),e[12]=m,e[13]=p,e[14]=k):k=e[14];let b;e[15]===Symbol.for("react.memo_cache_sentinel")?(b={body:{paddingTop:0}},e[15]=b):b=e[15];let x;e[16]===Symbol.for("react.memo_cache_sentinel")?(x=n.jsx(vl,{active:!0}),e[16]=x):x=e[16];let F;e[17]!==s.id||e[18]!==g||e[19]!==S?(F=n.jsx(j.Suspense,{fallback:x,children:n.jsx(es,{deploymentId:s.id,isEndpointDestroying:g,isOwnedByCurrentUser:S})}),e[17]=s.id,e[18]=g,e[19]=S,e[20]=F):F=e[20];let T;return e[21]!==F||e[22]!==k?(T=n.jsx(Yl,{title:k,styles:b,children:F}),e[21]=F,e[22]=k,e[23]=T):T=e[23],T},es=l=>{"use memo";var nl,Ne,Ge,ul,al,il,sl,ol;const e=Ue.c(123),{deploymentId:i,isEndpointDestroying:r,isOwnedByCurrentUser:t}=l,{t:a}=ll(),{message:d}=Pl.useApp(),[s,c]=j.useTransition(),[o,g]=Il(),[u,S]=j.useState(null),[m,y]=j.useState(!1),[f,p]=j.useState(null),[k,b]=Cl("table_column_overrides.AutoScalingRuleList");let x,F;e[0]===Symbol.for("react.memo_cache_sentinel")?(x={order:Gl(["createdAt","-createdAt"]).withDefault("-createdAt"),filter:Ca(ls)},F={history:"replace"},e[0]=x,e[1]=F):(x=e[0],F=e[1]);const[T,R]=Tn(x,F),D=T.order,C=T.filter??void 0;let $;e[2]===Symbol.for("react.memo_cache_sentinel")?($={current:1,pageSize:10},e[2]=$):$=e[2];const{baiPaginationOption:z,tablePaginationOption:P,setTablePaginationOption:B}=Aa($),O=D.startsWith("-")?"DESC":"ASC";let I;e[3]!==O?(I=[{field:"CREATED_AT",direction:O}],e[3]=O,e[4]=I):I=e[4];const w=C??null;let N;e[5]!==z.limit||e[6]!==z.offset||e[7]!==i||e[8]!==I||e[9]!==w?(N={deploymentId:i,offset:z.offset,limit:z.limit,orderBy:I,filter:w},e[5]=z.limit,e[6]=z.offset,e[7]=i,e[8]=I,e[9]=w,e[10]=N):N=e[10];const G=N,W=j.useDeferredValue(G);let Q;e[11]===Symbol.for("react.memo_cache_sentinel")?(Q=Pt,e[11]=Q):Q=e[11];let H;e[12]!==o?(H={fetchPolicy:"store-and-network",fetchKey:o},e[12]=o,e[13]=H):H=e[13];const V=Ke.useLazyLoadQuery(Q,W,H);let K,M;e[14]===Symbol.for("react.memo_cache_sentinel")?(K=jt,M={},e[14]=K,e[15]=M):(K=e[14],M=e[15]);const{prometheusQueryPresets:_}=Ke.useLazyLoadQuery(K,M);let Y;if(e[16]!==_){if(Y=new Map,_!=null&&_.edges)for(const Ie of _.edges)Ie!=null&&Ie.node&&Y.set(Ze(Ie.node.id),Ie.node.name);e[16]=_,e[17]=Y}else Y=e[17];const ne=Y;let A;e[18]!==((Ne=(nl=V==null?void 0:V.deployment)==null?void 0:nl.autoScalingRules)==null?void 0:Ne.edges)?(A=Al(Fl((ul=(Ge=V==null?void 0:V.deployment)==null?void 0:Ge.autoScalingRules)==null?void 0:ul.edges,"node")),e[18]=(il=(al=V==null?void 0:V.deployment)==null?void 0:al.autoScalingRules)==null?void 0:il.edges,e[19]=A):A=e[19];const v=A,E=((ol=(sl=V==null?void 0:V.deployment)==null?void 0:sl.autoScalingRules)==null?void 0:ol.count)??0;let L;e[20]===Symbol.for("react.memo_cache_sentinel")?(L=Lt,e[20]=L):L=e[20];const U=Gn(L);let Z;e[21]!==g?(Z=()=>{c(()=>{g()})},e[21]=g,e[22]=Z):Z=e[22];const J=Z;let ee;e[23]===Symbol.for("react.memo_cache_sentinel")?(ee=(Ie,Te)=>{p({id:Ie,metricName:Te})},e[23]=ee):ee=e[23];const q=ee;let te;e[24]===Symbol.for("react.memo_cache_sentinel")?(te={flex:1},e[24]=te):te=e[24];let ye;e[25]!==a?(ye=a("autoScalingRule.CreatedAt"),e[25]=a,e[26]=ye):ye=e[26];let de;e[27]===Symbol.for("react.memo_cache_sentinel")?(de=["after","before"],e[27]=de):de=e[27];let pe;e[28]!==ye?(pe={key:"createdAt",propertyLabel:ye,type:"datetime",operators:de,defaultOperator:"after"},e[28]=ye,e[29]=pe):pe=e[29];let ue;e[30]!==a?(ue=a("autoScalingRule.LastTriggered"),e[30]=a,e[31]=ue):ue=e[31];let fe;e[32]===Symbol.for("react.memo_cache_sentinel")?(fe=["after","before"],e[32]=fe):fe=e[32];let se;e[33]!==ue?(se={key:"lastTriggeredAt",propertyLabel:ue,type:"datetime",operators:fe,defaultOperator:"after"},e[33]=ue,e[34]=se):se=e[34];let ce;e[35]!==pe||e[36]!==se?(ce=[pe,se],e[35]=pe,e[36]=se,e[37]=ce):ce=e[37];let re;e[38]!==R||e[39]!==B?(re=Ie=>{c(()=>{R({filter:Ie??null}),B({current:1})})},e[38]=R,e[39]=B,e[40]=re):re=e[40];let ke;e[41]!==C||e[42]!==ce||e[43]!==re?(ke=n.jsx(Xl,{style:te,filterProperties:ce,value:C,onChange:re}),e[41]=C,e[42]=ce,e[43]=re,e[44]=ke):ke=e[44];let Re;e[45]!==g?(Re=()=>{c(()=>g())},e[45]=g,e[46]=Re):Re=e[46];let Fe;e[47]!==s||e[48]!==Re?(Fe=n.jsx(wl,{loading:s,value:"",onChange:Re}),e[47]=s,e[48]=Re,e[49]=Fe):Fe=e[49];let De;e[50]===Symbol.for("react.memo_cache_sentinel")?(De=n.jsx(Ll,{}),e[50]=De):De=e[50];const xe=r||!t;let ae;e[51]===Symbol.for("react.memo_cache_sentinel")?(ae=()=>{S(null),y(!0)},e[51]=ae):ae=e[51];let ve;e[52]!==a?(ve=a("modelService.AddRules"),e[52]=a,e[53]=ve):ve=e[53];let je;e[54]!==xe||e[55]!==ve?(je=n.jsx(kl,{type:"primary",icon:De,disabled:xe,onClick:ae,children:ve}),e[54]=xe,e[55]=ve,e[56]=je):je=e[56];let Ce;e[57]!==ke||e[58]!==Fe||e[59]!==je?(Ce=n.jsxs(ie,{align:"center",gap:"xs",children:[ke,Fe,je]}),e[57]=ke,e[58]=Fe,e[59]=je,e[60]=Ce):Ce=e[60];const Me=s||W!==G;let Pe;e[61]!==k||e[62]!==b?(Pe={columnOverrides:k,onColumnOverridesChange:b},e[61]=k,e[62]=b,e[63]=Pe):Pe=e[63];let Xe;e[64]!==R?(Xe=Ie=>{c(()=>{R({order:Ie||null})})},e[64]=R,e[65]=Xe):Xe=e[65];let Je;e[66]!==B?(Je=(Ie,Te)=>{B({current:Ie,pageSize:Te})},e[66]=B,e[67]=Je):Je=e[67];let h;e[68]!==Je||e[69]!==P.current||e[70]!==P.pageSize||e[71]!==E?(h={pageSize:P.pageSize,current:P.current,total:E,onChange:Je},e[68]=Je,e[69]=P.current,e[70]=P.pageSize,e[71]=E,e[72]=h):h=e[72];let X;e[73]===Symbol.for("react.memo_cache_sentinel")?(X=Ie=>{S(Ie),y(!0)},e[73]=X):X=e[73];let le;e[74]!==v||e[75]!==r||e[76]!==t||e[77]!==D||e[78]!==ne||e[79]!==Me||e[80]!==Pe||e[81]!==Xe||e[82]!==h?(le=n.jsx(Gi,{autoScalingRulesFrgmt:v,presetMap:ne,order:D,loading:Me,tableSettings:Pe,onChangeOrder:Xe,pagination:h,isEndpointDestroying:r,isOwnedByCurrentUser:t,onEditRule:X,onDeleteRule:q}),e[74]=v,e[75]=r,e[76]=t,e[77]=D,e[78]=ne,e[79]=Me,e[80]=Pe,e[81]=Xe,e[82]=h,e[83]=le):le=e[83];let oe;e[84]!==Ce||e[85]!==le?(oe=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[Ce,le]}),e[84]=Ce,e[85]=le,e[86]=oe):oe=e[86];let me;e[87]!==i?(me=Ze(i),e[87]=i,e[88]=me):me=e[88];let Se;e[89]!==v||e[90]!==u?(Se=u?v.find(Ie=>Ie.id===u)??null:null,e[89]=v,e[90]=u,e[91]=Se):Se=e[91];let Le;e[92]!==J?(Le=Ie=>{y(!1),Ie&&J()},e[92]=J,e[93]=Le):Le=e[93];let _e;e[94]===Symbol.for("react.memo_cache_sentinel")?(_e=()=>{S(null)},e[94]=_e):_e=e[94];let Be;e[95]!==m||e[96]!==me||e[97]!==Se||e[98]!==Le?(Be=n.jsx(fl,{children:n.jsx(Ei,{open:m,modelDeploymentId:me,autoScalingRuleFrgmt:Se,onRequestClose:Le,afterClose:_e})}),e[95]=m,e[96]=me,e[97]=Se,e[98]=Le,e[99]=Be):Be=e[99];const Oe=!!f;let Qe;e[100]!==a?(Qe=a("autoScalingRule.DeleteAutoScalingRule"),e[100]=a,e[101]=Qe):Qe=e[101];let be;e[102]!==a?(be=a("autoScalingRule.DeleteConfirmation"),e[102]=a,e[103]=be):be=e[103];let He;e[104]!==f?(He=f?[{key:f.id,label:f.metricName}]:[],e[104]=f,e[105]=He):He=e[105];let qe;e[106]!==U||e[107]!==f||e[108]!==J||e[109]!==d||e[110]!==a?(qe=()=>{if(f)return U({input:{id:Ze(f.id)}}).then(()=>{p(null),J(),d.success({key:"autoscaling-rule-deleted",content:a("autoScalingRule.SuccessfullyDeleted")})}).catch(Ie=>{const Te=Array.isArray(Ie)?Ie:[Ie];for(const Ve of Te)d.error((Ve==null?void 0:Ve.message)||a("dialog.ErrorOccurred"))})},e[106]=U,e[107]=f,e[108]=J,e[109]=d,e[110]=a,e[111]=qe):qe=e[111];let We;e[112]===Symbol.for("react.memo_cache_sentinel")?(We=()=>p(null),e[112]=We):We=e[112];let we;e[113]!==Oe||e[114]!==Qe||e[115]!==be||e[116]!==He||e[117]!==qe?(we=n.jsx(Rn,{open:Oe,title:Qe,description:be,items:He,reversible:!0,onOk:qe,onCancel:We}),e[113]=Oe,e[114]=Qe,e[115]=be,e[116]=He,e[117]=qe,e[118]=we):we=e[118];let ze;return e[119]!==oe||e[120]!==Be||e[121]!==we?(ze=n.jsxs(n.Fragment,{children:[oe,Be,we]}),e[119]=oe,e[120]=Be,e[121]=we,e[122]=ze):ze=e[122],ze};function ls(l){return l}const $t=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentBasicInfoCardDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentBasicInfoCardDeleteMutation",selections:e},params:{cacheID:"70ed95e6d8ed42187398c9bc2c13f5bb",id:null,metadata:{},name:"DeploymentBasicInfoCardDeleteMutation",operationKind:"mutation",text:`mutation DeploymentBasicInfoCardDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();$t.hash="219d6f05b61219aeb47beff89d87a769";const Bt=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentBasicInfoCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[l],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentTagChips_metadata"}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null}})();Bt.hash="25c43526c832d75ea335a66d0e86f3af";const Ht=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,r,e,i],kind:"Operation",name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},s,c,o,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},c,o,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"b24d145b426294eb9cc72c268ccd1df2",id:null,metadata:{},name:"DeploymentSchedulingHistoryModalQuery",operationKind:"query",text:`query DeploymentSchedulingHistoryModalQuery(
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
`}}})();Ht.hash="89ec50bb9b1f834e59c642072090d378";const Qt=Ht,ns=l=>{"use memo";var Re,Fe,De,xe;const e=Ue.c(113);let i,r,t,a,d;e[0]!==l?({open:a,queryRef:d,onReload:t,onCancel:r,...i}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=ll(),[c,o]=Il(),[g,u]=j.useState(),[S,m]=j.useState("-updatedAt"),[y,f]=Cl("schedulingHistoryExpandMode"),[p,k]=Cl("table_column_overrides.DeploymentSchedulingHistory");let b;e[6]===Symbol.for("react.memo_cache_sentinel")?(b={current:1,pageSize:10},e[6]=b):b=e[6];const{tablePaginationOption:x,setTablePaginationOption:F}=In(b),T=j.useDeferredValue(d),R=T!==d,D=Ke.usePreloadedQuery(Qt,T);let C;e[7]!==s?(C=s("deployment.DeploymentSchedulingHistory"),e[7]=s,e[8]=C):C=e[8];let $,z;e[9]===Symbol.for("react.memo_cache_sentinel")?($={maxWidth:1600},z={body:{minHeight:"80vh"}},e[9]=$,e[10]=z):($=e[9],z=e[10]);let P;e[11]!==t||e[12]!==d.variables||e[13]!==F?(P=ae=>{u(ae),F({current:1}),t({...d.variables,filter:ae,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=d.variables,e[13]=F,e[14]=P):P=e[14];let B;e[15]!==s?(B=s("deployment.ID"),e[15]=s,e[16]=B):B=e[16];let O;e[17]!==B?(O={key:"id",propertyLabel:B,type:"uuid",fixedOperator:"equals"},e[17]=B,e[18]=O):O=e[18];let I;e[19]!==s?(I=s("deployment.Phase"),e[19]=s,e[20]=I):I=e[20];let w;e[21]!==I?(w={key:"phase",propertyLabel:I,type:"string",fixedOperator:"contains"},e[21]=I,e[22]=w):w=e[22];let N;e[23]!==s?(N=s("deployment.Result"),e[23]=s,e[24]=N):N=e[24];let G;e[25]===Symbol.for("react.memo_cache_sentinel")?(G=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=G):G=e[25];let W;e[26]!==N?(W={key:"result",propertyLabel:N,type:"enum",strictSelection:!0,options:G},e[26]=N,e[27]=W):W=e[27];let Q;e[28]!==s?(Q=s("deployment.FromStatus"),e[28]=s,e[29]=Q):Q=e[29];let H;e[30]!==Q?(H={key:"fromStatus",propertyLabel:Q,type:"string",valueMode:"scalar"},e[30]=Q,e[31]=H):H=e[31];let V;e[32]!==s?(V=s("deployment.ToStatus"),e[32]=s,e[33]=V):V=e[33];let K;e[34]!==V?(K={key:"toStatus",propertyLabel:V,type:"string",valueMode:"scalar"},e[34]=V,e[35]=K):K=e[35];let M;e[36]!==s?(M=s("deployment.ErrorCode"),e[36]=s,e[37]=M):M=e[37];let _;e[38]!==M?(_={key:"errorCode",propertyLabel:M,type:"string",fixedOperator:"contains"},e[38]=M,e[39]=_):_=e[39];let Y;e[40]!==s?(Y=s("deployment.Message"),e[40]=s,e[41]=Y):Y=e[41];let ne;e[42]!==Y?(ne={key:"message",propertyLabel:Y,type:"string",fixedOperator:"contains"},e[42]=Y,e[43]=ne):ne=e[43];let A;e[44]!==s?(A=s("deployment.CreatedAt"),e[44]=s,e[45]=A):A=e[45];let v;e[46]!==A?(v={key:"createdAt",propertyLabel:A,type:"datetime",defaultOperator:"after"},e[46]=A,e[47]=v):v=e[47];let E;e[48]!==s?(E=s("deployment.UpdatedAt"),e[48]=s,e[49]=E):E=e[49];let L;e[50]!==E?(L={key:"updatedAt",propertyLabel:E,type:"datetime",defaultOperator:"after"},e[50]=E,e[51]=L):L=e[51];let U;e[52]!==W||e[53]!==H||e[54]!==K||e[55]!==_||e[56]!==ne||e[57]!==v||e[58]!==L||e[59]!==O||e[60]!==w?(U=[O,w,W,H,K,_,ne,v,L],e[52]=W,e[53]=H,e[54]=K,e[55]=_,e[56]=ne,e[57]=v,e[58]=L,e[59]=O,e[60]=w,e[61]=U):U=e[61];let Z;e[62]!==g||e[63]!==U||e[64]!==P?(Z=n.jsx(Xl,{value:g,onChange:P,filterProperties:U}),e[62]=g,e[63]=U,e[64]=P,e[65]=Z):Z=e[65];let J;e[66]!==t||e[67]!==d.variables||e[68]!==o?(J=ae=>{o(ae),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=o,e[69]=J):J=e[69];let ee;e[70]!==c||e[71]!==R||e[72]!==J?(ee=n.jsx(ie,{children:n.jsx(wl,{value:c,onChange:J,loading:R,autoUpdateDelay:null})}),e[70]=c,e[71]=R,e[72]=J,e[73]=ee):ee=e[73];let q;e[74]!==Z||e[75]!==ee?(q=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,ee]}),e[74]=Z,e[75]=ee,e[76]=q):q=e[76];const te=y??void 0;let ye;e[77]!==p||e[78]!==k?(ye={columnOverrides:p,onColumnOverridesChange:k},e[77]=p,e[78]=k,e[79]=ye):ye=e[79];let de;e[80]!==t||e[81]!==d.variables||e[82]!==F?(de=ae=>{m(ae),F({current:1}),t({...d.variables,orderBy:_l(ae),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=d.variables,e[82]=F,e[83]=de):de=e[83];const pe=((Re=D.deploymentScopedSchedulingHistories)==null?void 0:Re.count)??0;let ue;e[84]!==t||e[85]!==d.variables||e[86]!==F?(ue=(ae,ve)=>{F({current:ae,pageSize:ve}),t({...d.variables,limit:ve,offset:ae>1?(ae-1)*ve:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=d.variables,e[86]=F,e[87]=ue):ue=e[87];let fe;e[88]!==pe||e[89]!==ue||e[90]!==x.current||e[91]!==x.pageSize?(fe={pageSize:x.pageSize,current:x.current,total:pe,onChange:ue},e[88]=pe,e[89]=ue,e[90]=x.current,e[91]=x.pageSize,e[92]=fe):fe=e[92];let se;e[93]!==((Fe=D.deploymentScopedSchedulingHistories)==null?void 0:Fe.edges)?(se=Fl((De=D.deploymentScopedSchedulingHistories)==null?void 0:De.edges,"node"),e[93]=(xe=D.deploymentScopedSchedulingHistories)==null?void 0:xe.edges,e[94]=se):se=e[94];let ce;e[95]!==R||e[96]!==S||e[97]!==f||e[98]!==te||e[99]!==ye||e[100]!==de||e[101]!==fe||e[102]!==se?(ce=n.jsx(Di,{resizable:!0,loading:R,expandMode:te,onExpandModeChange:f,tableSettings:ye,order:S,onChangeOrder:de,pagination:fe,schedulingHistoryFrgmt:se}),e[95]=R,e[96]=S,e[97]=f,e[98]=te,e[99]=ye,e[100]=de,e[101]=fe,e[102]=se,e[103]=ce):ce=e[103];let re;e[104]!==q||e[105]!==ce?(re=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[q,ce]}),e[104]=q,e[105]=ce,e[106]=re):re=e[106];let ke;return e[107]!==i||e[108]!==r||e[109]!==a||e[110]!==C||e[111]!==re?(ke=n.jsx($l,{title:C,open:a,width:"90%",style:$,styles:z,footer:null,onCancel:r,...i,children:re}),e[107]=i,e[108]=r,e[109]=a,e[110]=C,e[111]=re,e[112]=ke):ke=e[112],ke},Kl=()=>n.jsx(el.Text,{type:"secondary",children:"-"}),ts=l=>{"use memo";var S,m,y;const e=Ue.c(26),{deployment:i,onClickSchedulingHistoryAction:r}=l,{t}=ll(),a=an(),d=Dn(),s=((m=(S=i==null?void 0:i.metadata.projectV2)==null?void 0:S.basicInfo)==null?void 0:m.name)??(i==null?void 0:i.metadata.projectId);let c;if(e[0]!==d||e[1]!==i||e[2]!==r||e[3]!==s||e[4]!==t||e[5]!==a){const f=t("deployment.Visibility"),p=i==null?void 0:i.networkAccess.openToPublic;let k;e[7]!==t?(k=t("deployment.Public"),e[7]=t,e[8]=k):k=e[8];let b;e[9]!==t?(b=t("deployment.Private"),e[9]=t,e[10]=b):b=e[10];let x;e[11]===Symbol.for("react.memo_cache_sentinel")?(x=Kl(),e[11]=x):x=e[11];let F;e[12]!==p||e[13]!==k||e[14]!==b?(F=n.jsx(ni,{value:p,trueLabel:k,falseLabel:b,fallback:x}),e[12]=p,e[13]=k,e[14]=b,e[15]=F):F=e[15];const T=t("deployment.Tags"),R=(i==null?void 0:i.metadata)??null;let D;e[16]!==d||e[17]!==a?(D=z=>{const P=d("deployments");a({pathname:P,search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:z}})}).toString()})},e[16]=d,e[17]=a,e[18]=D):D=e[18];let C;e[19]===Symbol.for("react.memo_cache_sentinel")?(C=Kl(),e[19]=C):C=e[19];let $;e[20]!==D||e[21]!==R?($=n.jsx(ei,{metadataFrgmt:R,onTagClick:D,fallback:C}),e[20]=D,e[21]=R,e[22]=$):$=e[22],c=tn([{key:"lifecycle",label:t("deployment.Lifecycle"),children:i!=null&&i.metadata.status?n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ct,{status:i.metadata.status}),r&&n.jsxs(n.Fragment,{children:[n.jsx(Xn,{type:"vertical",style:{margin:0}}),n.jsx(kl,{type:"link",size:"small",icon:n.jsx(dt,{}),style:{padding:0},action:async()=>{await r()},children:t("deployment.SchedulingHistory")})]})]}):Kl()},{key:"id",label:t("deployment.DeploymentId"),children:i!=null&&i.id?n.jsx(Nl,{globalId:i.id,copyable:!0,ellipsis:!1,style:{maxWidth:"none"}}):Kl()},{key:"project",label:t("deployment.Project"),children:s||Kl()},{key:"domain",label:t("deployment.Domain"),children:(i==null?void 0:i.metadata.domainName)||Kl()},{key:"resource-group",label:t("modelStore.ResourceGroup"),children:(i==null?void 0:i.metadata.resourceGroupName)||Kl()},{key:"endpoint-url",label:t("deployment.EndpointUrl"),children:i!=null&&i.networkAccess.endpointUrl?n.jsx(el.Text,{copyable:!0,style:{wordBreak:"break-all"},children:i.networkAccess.endpointUrl}):Kl()},{key:"visibility",label:f,children:F},{key:"desired-replicas",label:t("deployment.DesiredReplicas"),children:((y=i==null?void 0:i.replicaState)==null?void 0:y.desiredReplicaCount)??Kl()},{key:"tags",label:T,children:$}]),e[0]=d,e[1]=i,e[2]=r,e[3]=s,e[4]=t,e[5]=a,e[6]=c}else c=e[6];const o=c;let g;e[23]===Symbol.for("react.memo_cache_sentinel")?(g={xs:1,sm:1,md:2,lg:2,xl:2,xxl:2},e[23]=g):g=e[23];let u;return e[24]!==o?(u=n.jsx(La,{bordered:!0,column:g,items:o}),e[24]=o,e[25]=u):u=e[25],u},as=l=>{"use memo";const e=Ue.c(101),{deploymentFrgmt:i,isPendingRefetch:r,onRefetch:t,autoUpdateDelay:a}=l,d=a===void 0?null:a,{t:s}=ll(),{message:c}=Pl.useApp(),{logger:o}=Ol(),g=an(),u=Dn();let S;e[0]===Symbol.for("react.memo_cache_sentinel")?(S=Bt,e[0]=S):S=e[0];const m=Ke.useFragment(S,i),[y,f]=j.useState(!1),[p,k]=j.useState(!1),[b,x]=j.useState(!1),[F,T]=Ke.useQueryLoader(Qt),R=et();let D;e[1]!==R?(D=(R==null?void 0:R.supports("deployment-scheduling-history"))??!1,e[1]=R,e[2]=D):D=e[2];const C=D;let $;e[3]===Symbol.for("react.memo_cache_sentinel")?($=$t,e[3]=$):$=e[3];const[z,P]=Ke.useMutation($),B=(m==null?void 0:m.metadata.name)??"",O=m==null?void 0:m.metadata.status;let I;e[4]!==u?(I=u("deployments"),e[4]=u,e[5]=I):I=e[5];const w=I;let N;e[6]!==z||e[7]!==m||e[8]!==w||e[9]!==o||e[10]!==c||e[11]!==s||e[12]!==g?(N=()=>{m!=null&&m.id&&z({variables:{input:{id:Ze(m.id)??m.id}},onCompleted:(je,Ce)=>{if(Ce&&Ce.length>0){o.error("Failed to delete deployment",Ce),c.error(s("deployment.FailedToDeleteDeployment"));return}c.success(s("deployment.DeploymentDeleted")),k(!1),g(w)},onError:je=>{o.error("Failed to delete deployment",je),c.error(s("deployment.FailedToDeleteDeployment"))}})},e[6]=z,e[7]=m,e[8]=w,e[9]=o,e[10]=c,e[11]=s,e[12]=g,e[13]=N):N=e[13];const G=N;let W;e[14]!==s?(W=s("deployment.BasicInformation"),e[14]=s,e[15]=W):W=e[15];let Q;e[16]!==d||e[17]!==r||e[18]!==t?(Q=n.jsx(wl,{loading:r,value:"",onChange:t,autoUpdateDelay:d}),e[16]=d,e[17]=r,e[18]=t,e[19]=Q):Q=e[19];let H;e[20]===Symbol.for("react.memo_cache_sentinel")?(H=n.jsx(ut,{}),e[20]=H):H=e[20];let V;e[21]!==O?(V=hl(O),e[21]=O,e[22]=V):V=e[22];let K;e[23]===Symbol.for("react.memo_cache_sentinel")?(K=async()=>{f(!0)},e[23]=K):K=e[23];let M;e[24]!==s?(M=s("button.Edit"),e[24]=s,e[25]=M):M=e[25];let _;e[26]!==V||e[27]!==M?(_=n.jsx(kl,{icon:H,disabled:V,action:K,children:M}),e[26]=V,e[27]=M,e[28]=_):_=e[28];let Y;e[29]===Symbol.for("react.memo_cache_sentinel")?(Y=["click"],e[29]=Y):Y=e[29];let ne;e[30]!==s?(ne=s("deployment.DeleteDeployment"),e[30]=s,e[31]=ne):ne=e[31];let A;e[32]===Symbol.for("react.memo_cache_sentinel")?(A=n.jsx(xn,{}),e[32]=A):A=e[32];let v;e[33]!==O||e[34]!==P?(v=hl(O)||P,e[33]=O,e[34]=P,e[35]=v):v=e[35];let E;e[36]===Symbol.for("react.memo_cache_sentinel")?(E=()=>k(!0),e[36]=E):E=e[36];let L;e[37]!==ne||e[38]!==v?(L={items:[{key:"delete",label:ne,icon:A,danger:!0,disabled:v,onClick:E}]},e[37]=ne,e[38]=v,e[39]=L):L=e[39];let U;e[40]===Symbol.for("react.memo_cache_sentinel")?(U=n.jsx(lt,{}),e[40]=U):U=e[40];let Z;e[41]!==s?(Z=s("button.More"),e[41]=s,e[42]=Z):Z=e[42];let J;e[43]!==Z?(J=n.jsx(ml,{icon:U,"aria-label":Z}),e[43]=Z,e[44]=J):J=e[44];let ee;e[45]!==L||e[46]!==J?(ee=n.jsx(nt,{trigger:Y,menu:L,children:J}),e[45]=L,e[46]=J,e[47]=ee):ee=e[47];let q;e[48]!==_||e[49]!==ee?(q=n.jsxs(Ul.Compact,{children:[_,ee]}),e[48]=_,e[49]=ee,e[50]=q):q=e[50];let te;e[51]!==q||e[52]!==Q?(te=n.jsxs(ie,{gap:"xs",align:"center",children:[Q,q]}),e[51]=q,e[52]=Q,e[53]=te):te=e[53];let ye;e[54]===Symbol.for("react.memo_cache_sentinel")?(ye={body:{paddingTop:0}},e[54]=ye):ye=e[54];let de;e[55]!==m||e[56]!==T||e[57]!==C?(de=C&&(m!=null&&m.id)?async()=>{const je=m.id;je&&(T({scope:{deploymentId:Vl(je)??je},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),x(!0))}:void 0,e[55]=m,e[56]=T,e[57]=C,e[58]=de):de=e[58];let pe;e[59]!==m||e[60]!==de?(pe=n.jsx(ts,{deployment:m,onClickSchedulingHistoryAction:de}),e[59]=m,e[60]=de,e[61]=pe):pe=e[61];let ue;e[62]!==te||e[63]!==pe||e[64]!==W?(ue=n.jsx(Yl,{title:W,extra:te,styles:ye,children:pe}),e[62]=te,e[63]=pe,e[64]=W,e[65]=ue):ue=e[65];let fe;e[66]!==t?(fe=je=>{f(!1),je&&t()},e[66]=t,e[67]=fe):fe=e[67];let se;e[68]!==m||e[69]!==y||e[70]!==fe?(se=n.jsx(Ma,{open:y,deploymentFrgmt:m,onRequestClose:fe}),e[68]=m,e[69]=y,e[70]=fe,e[71]=se):se=e[71];let ce;e[72]!==s?(ce=s("deployment.DeleteDeployment"),e[72]=s,e[73]=ce):ce=e[73];let re;e[74]!==s?(re=s("deployment.Deployment"),e[74]=s,e[75]=re):re=e[75];let ke;e[76]!==B?(ke=B?[{key:B,label:B}]:[],e[76]=B,e[77]=ke):ke=e[77];let Re;e[78]!==B?(Re={placeholder:B},e[78]=B,e[79]=Re):Re=e[79];let Fe;e[80]!==P?(Fe={loading:P},e[80]=P,e[81]=Fe):Fe=e[81];let De;e[82]===Symbol.for("react.memo_cache_sentinel")?(De=()=>k(!1),e[82]=De):De=e[82];let xe;e[83]!==B||e[84]!==G||e[85]!==p||e[86]!==ce||e[87]!==re||e[88]!==ke||e[89]!==Re||e[90]!==Fe?(xe=n.jsx(Rn,{open:p,title:ce,target:re,items:ke,confirmText:B,requireConfirmInput:!0,inputProps:Re,okButtonProps:Fe,onOk:G,onCancel:De}),e[83]=B,e[84]=G,e[85]=p,e[86]=ce,e[87]=re,e[88]=ke,e[89]=Re,e[90]=Fe,e[91]=xe):xe=e[91];let ae;e[92]!==F||e[93]!==b||e[94]!==T?(ae=F!=null&&n.jsx(fl,{children:n.jsx(ns,{open:b,queryRef:F,onReload:T,onCancel:()=>x(!1)})}),e[92]=F,e[93]=b,e[94]=T,e[95]=ae):ae=e[95];let ve;return e[96]!==ue||e[97]!==se||e[98]!==xe||e[99]!==ae?(ve=n.jsxs(n.Fragment,{children:[ue,se,xe,ae]}),e[96]=ue,e[97]=se,e[98]=xe,e[99]=ae,e[100]=ve):ve=e[100],ve},qt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"sessionId",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"revisionId",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"trafficStatus",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"healthStatus",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},k={alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"sessionV2",plural:!1,selections:[c,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[p],storageKey:null}],storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},x=[p,b],F={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},R={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[c,p,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentReplicasCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[c,o,g,u,S,m,y,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[c,f,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null},k],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,r],kind:"Operation",name:"DeploymentReplicasCardListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[c,o,g,u,S,m,y,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[c,f,y,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[p,c],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},b,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},c],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[F,T,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},R],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[F,T,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},R],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[c,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},k],storageKey:null}],storageKey:null}],storageKey:null},c],storageKey:null}]},params:{cacheID:"79f688ce3d9ffc3c72881648d7d76eab",id:null,metadata:{},name:"DeploymentReplicasCardListQuery",operationKind:"query",text:`query DeploymentReplicasCardListQuery(
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
`}}})();qt.hash="3c889ebaa68c08cff62a842b2869be6a";const zt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentReplicasCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};zt.hash="c535e4dd070869785c37a4074751984b";const is={HEALTHY:"success",UNHEALTHY:"error",DEGRADED:"warning",NOT_CHECKED:"default",PROVISIONING:"processing",WARMING_UP:"processing",RUNNING:"success",TERMINATING:"warning",TERMINATED:"default",FAILED_TO_START:"error"},ss={HEALTHY:"Healthy",UNHEALTHY:"Unhealthy",DEGRADED:"Degraded",NOT_CHECKED:"NotChecked",PROVISIONING:"Provisioning",WARMING_UP:"WarmingUp",RUNNING:"Running",TERMINATING:"Terminating",TERMINATED:"Terminated",FAILED_TO_START:"FailedToStart"},Hn=l=>{"use memo";const e=Ue.c(23);let i,r,t;e[0]!==l?({status:i,showTooltip:r,...t}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t):(i=e[1],r=e[2],t=e[3]);const a=r===void 0?!0:r,{t:d}=ll(),s=is[i],c=ss[i],o=`replicaStatus.${c}`;let g;e[4]!==d||e[5]!==o?(g=d(o),e[4]=d,e[5]=o,e[6]=g):g=e[6];const u=g;let S;e[7]!==c||e[8]!==a||e[9]!==d?(S=a?d(`replicaStatus.tooltip.${c}`,{defaultValue:""}):void 0,e[7]=c,e[8]=a,e[9]=d,e[10]=S):S=e[10];const m=S;let y;e[11]!==i?(y=i==="WARMING_UP"?n.jsx(Cn,{spin:!0}):void 0,e[11]=i,e[12]=y):y=e[12];const f=y;let p;e[13]!==s||e[14]!==f||e[15]!==u||e[16]!==t?(p=n.jsx(ln,{...t,color:s,icon:f,children:u}),e[13]=s,e[14]=f,e[15]=u,e[16]=t,e[17]=p):p=e[17];const k=p;if(!a||!m)return k;let b;e[18]!==k?(b=n.jsx("span",{children:k}),e[18]=k,e[19]=b):b=e[19];let x;return e[20]!==b||e[21]!==m?(x=n.jsx(cl,{title:m,children:b}),e[20]=b,e[21]=m,e[22]=x):x=e[22],x},Ut=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},r={defaultValue:null,kind:"LocalArgument",name:"orderBy"},t={defaultValue:null,kind:"LocalArgument",name:"scope"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[t,l,r,e,i],kind:"Operation",name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:a,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[d,{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},s,c,o,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},c,o,{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"e02133438de747b29f05fb0c3109339d",id:null,metadata:{},name:"RouteSchedulingHistoryModalQuery",operationKind:"query",text:`query RouteSchedulingHistoryModalQuery(
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
`}}})();Ut.hash="e770c8de50ced262d1f75ecd5be88c57";const Wt=Ut,rs=l=>{"use memo";var Re,Fe,De,xe;const e=Ue.c(113);let i,r,t,a,d;e[0]!==l?({open:a,queryRef:d,onReload:t,onCancel:r,...i}=l,e[0]=l,e[1]=i,e[2]=r,e[3]=t,e[4]=a,e[5]=d):(i=e[1],r=e[2],t=e[3],a=e[4],d=e[5]);const{t:s}=ll(),[c,o]=Il(),[g,u]=j.useState(),[S,m]=j.useState("-updatedAt"),[y,f]=Cl("schedulingHistoryExpandMode"),[p,k]=Cl("table_column_overrides.RouteSchedulingHistory");let b;e[6]===Symbol.for("react.memo_cache_sentinel")?(b={current:1,pageSize:10},e[6]=b):b=e[6];const{tablePaginationOption:x,setTablePaginationOption:F}=In(b),T=j.useDeferredValue(d),R=T!==d,D=Ke.usePreloadedQuery(Wt,T);let C;e[7]!==s?(C=s("route.RouteSchedulingHistory"),e[7]=s,e[8]=C):C=e[8];let $,z;e[9]===Symbol.for("react.memo_cache_sentinel")?($={maxWidth:1600},z={body:{minHeight:"80vh"}},e[9]=$,e[10]=z):($=e[9],z=e[10]);let P;e[11]!==t||e[12]!==d.variables||e[13]!==F?(P=ae=>{u(ae),F({current:1}),t({...d.variables,filter:ae,offset:0},{fetchPolicy:"network-only"})},e[11]=t,e[12]=d.variables,e[13]=F,e[14]=P):P=e[14];let B;e[15]!==s?(B=s("route.ID"),e[15]=s,e[16]=B):B=e[16];let O;e[17]!==B?(O={key:"id",propertyLabel:B,type:"uuid",fixedOperator:"equals"},e[17]=B,e[18]=O):O=e[18];let I;e[19]!==s?(I=s("route.Phase"),e[19]=s,e[20]=I):I=e[20];let w;e[21]!==I?(w={key:"phase",propertyLabel:I,type:"string",fixedOperator:"contains"},e[21]=I,e[22]=w):w=e[22];let N;e[23]!==s?(N=s("route.Result"),e[23]=s,e[24]=N):N=e[24];let G;e[25]===Symbol.for("react.memo_cache_sentinel")?(G=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=G):G=e[25];let W;e[26]!==N?(W={key:"result",propertyLabel:N,type:"enum",strictSelection:!0,options:G},e[26]=N,e[27]=W):W=e[27];let Q;e[28]!==s?(Q=s("route.FromStatus"),e[28]=s,e[29]=Q):Q=e[29];let H;e[30]!==Q?(H={key:"fromStatus",propertyLabel:Q,type:"string",valueMode:"scalar"},e[30]=Q,e[31]=H):H=e[31];let V;e[32]!==s?(V=s("route.ToStatus"),e[32]=s,e[33]=V):V=e[33];let K;e[34]!==V?(K={key:"toStatus",propertyLabel:V,type:"string",valueMode:"scalar"},e[34]=V,e[35]=K):K=e[35];let M;e[36]!==s?(M=s("route.ErrorCode"),e[36]=s,e[37]=M):M=e[37];let _;e[38]!==M?(_={key:"errorCode",propertyLabel:M,type:"string",fixedOperator:"contains"},e[38]=M,e[39]=_):_=e[39];let Y;e[40]!==s?(Y=s("route.Message"),e[40]=s,e[41]=Y):Y=e[41];let ne;e[42]!==Y?(ne={key:"message",propertyLabel:Y,type:"string",fixedOperator:"contains"},e[42]=Y,e[43]=ne):ne=e[43];let A;e[44]!==s?(A=s("route.CreatedAt"),e[44]=s,e[45]=A):A=e[45];let v;e[46]!==A?(v={key:"createdAt",propertyLabel:A,type:"datetime",defaultOperator:"after"},e[46]=A,e[47]=v):v=e[47];let E;e[48]!==s?(E=s("route.UpdatedAt"),e[48]=s,e[49]=E):E=e[49];let L;e[50]!==E?(L={key:"updatedAt",propertyLabel:E,type:"datetime",defaultOperator:"after"},e[50]=E,e[51]=L):L=e[51];let U;e[52]!==W||e[53]!==H||e[54]!==K||e[55]!==_||e[56]!==ne||e[57]!==v||e[58]!==L||e[59]!==O||e[60]!==w?(U=[O,w,W,H,K,_,ne,v,L],e[52]=W,e[53]=H,e[54]=K,e[55]=_,e[56]=ne,e[57]=v,e[58]=L,e[59]=O,e[60]=w,e[61]=U):U=e[61];let Z;e[62]!==g||e[63]!==U||e[64]!==P?(Z=n.jsx(Xl,{value:g,onChange:P,filterProperties:U}),e[62]=g,e[63]=U,e[64]=P,e[65]=Z):Z=e[65];let J;e[66]!==t||e[67]!==d.variables||e[68]!==o?(J=ae=>{o(ae),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=o,e[69]=J):J=e[69];let ee;e[70]!==c||e[71]!==R||e[72]!==J?(ee=n.jsx(ie,{children:n.jsx(wl,{value:c,onChange:J,loading:R,autoUpdateDelay:null})}),e[70]=c,e[71]=R,e[72]=J,e[73]=ee):ee=e[73];let q;e[74]!==Z||e[75]!==ee?(q=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,ee]}),e[74]=Z,e[75]=ee,e[76]=q):q=e[76];const te=y??void 0;let ye;e[77]!==p||e[78]!==k?(ye={columnOverrides:p,onColumnOverridesChange:k},e[77]=p,e[78]=k,e[79]=ye):ye=e[79];let de;e[80]!==t||e[81]!==d.variables||e[82]!==F?(de=ae=>{m(ae),F({current:1}),t({...d.variables,orderBy:_l(ae),offset:0},{fetchPolicy:"network-only"})},e[80]=t,e[81]=d.variables,e[82]=F,e[83]=de):de=e[83];const pe=((Re=D.routeScopedSchedulingHistories)==null?void 0:Re.count)??0;let ue;e[84]!==t||e[85]!==d.variables||e[86]!==F?(ue=(ae,ve)=>{F({current:ae,pageSize:ve}),t({...d.variables,limit:ve,offset:ae>1?(ae-1)*ve:0},{fetchPolicy:"network-only"})},e[84]=t,e[85]=d.variables,e[86]=F,e[87]=ue):ue=e[87];let fe;e[88]!==pe||e[89]!==ue||e[90]!==x.current||e[91]!==x.pageSize?(fe={pageSize:x.pageSize,current:x.current,total:pe,onChange:ue},e[88]=pe,e[89]=ue,e[90]=x.current,e[91]=x.pageSize,e[92]=fe):fe=e[92];let se;e[93]!==((Fe=D.routeScopedSchedulingHistories)==null?void 0:Fe.edges)?(se=Fl((De=D.routeScopedSchedulingHistories)==null?void 0:De.edges,"node"),e[93]=(xe=D.routeScopedSchedulingHistories)==null?void 0:xe.edges,e[94]=se):se=e[94];let ce;e[95]!==R||e[96]!==S||e[97]!==f||e[98]!==te||e[99]!==ye||e[100]!==de||e[101]!==fe||e[102]!==se?(ce=n.jsx(Ci,{resizable:!0,loading:R,expandMode:te,onExpandModeChange:f,tableSettings:ye,order:S,onChangeOrder:de,pagination:fe,schedulingHistoryFrgmt:se}),e[95]=R,e[96]=S,e[97]=f,e[98]=te,e[99]=ye,e[100]=de,e[101]=fe,e[102]=se,e[103]=ce):ce=e[103];let re;e[104]!==q||e[105]!==ce?(re=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[q,ce]}),e[104]=q,e[105]=ce,e[106]=re):re=e[106];let ke;return e[107]!==i||e[108]!==r||e[109]!==a||e[110]!==C||e[111]!==re?(ke=n.jsx($l,{title:C,open:a,width:"90%",style:$,styles:z,footer:null,onCancel:r,...i,children:re}),e[107]=i,e[108]=r,e[109]=a,e[110]=C,e[111]=re,e[112]=ke):ke=e[112],ke},Qn=["TERMINATED","FAILED_TO_START"],os=l=>l==="terminated"?{status:{in:[...Qn]}}:{status:{notIn:[...Qn]}},dn=(l,e)=>({...l,...os(e)}),fn=["createdAt","id"],ds=[...fn,...fn.map(l=>`-${l}`)],qn=l=>vn(fn,l),un=l=>l??"NOT_CHECKED",us=l=>{"use memo";const e=Ue.c(21),{deploymentFrgmt:i,deploymentId:r,replicaFetchKey:t}=l,{t:a}=ll(),{token:d}=Dl.useToken();let s;e[0]!==a?(s=a("deployment.tab.Replicas"),e[0]=a,e[1]=s):s=e[1];let c;e[2]!==a?(c=a("deployment.tab.description.Replicas"),e[2]=a,e[3]=c):c=e[3];let o;e[4]!==d.colorTextDescription?(o=n.jsx(Fn,{style:{color:d.colorTextDescription}}),e[4]=d.colorTextDescription,e[5]=o):o=e[5];let g;e[6]!==c||e[7]!==o?(g=n.jsx(cl,{title:c,children:o}),e[6]=c,e[7]=o,e[8]=g):g=e[8];let u;e[9]!==s||e[10]!==g?(u=n.jsxs(ie,{gap:"xs",align:"center",children:[s,g]}),e[9]=s,e[10]=g,e[11]=u):u=e[11];let S;e[12]===Symbol.for("react.memo_cache_sentinel")?(S={body:{paddingTop:0}},e[12]=S):S=e[12];let m;e[13]===Symbol.for("react.memo_cache_sentinel")?(m=n.jsx(vl,{active:!0}),e[13]=m):m=e[13];let y;e[14]!==i||e[15]!==r||e[16]!==t?(y=n.jsx(tt,{children:n.jsx(j.Suspense,{fallback:m,children:n.jsx(cs,{deploymentFrgmt:i,deploymentId:r,replicaFetchKey:t})})}),e[14]=i,e[15]=r,e[16]=t,e[17]=y):y=e[17];let f;return e[18]!==u||e[19]!==y?(f=n.jsx(Yl,{title:u,styles:S,children:y}),e[18]=u,e[19]=y,e[20]=f):f=e[20],f},cs=({deploymentFrgmt:l,deploymentId:e,replicaFetchKey:i})=>{"use memo";var W,Q,H,V;const{t:r}=ll(),[t,a]=j.useTransition(),[d,s]=Cl("table_column_overrides.DeploymentReplicasTab"),[c,o]=Tn({current:nn.withDefault(1),pageSize:nn.withDefault(10),order:Gl(ds),rFilter:at,rStatusCategory:Gl(["running","terminated"]).withDefault("running")},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rOrder",rFilter:"rFilter",rStatusCategory:"rStatusCategory"}});Ke.useFragment(zt,l);const g=K=>{if(!K)return null;try{const M=JSON.parse(K);return M&&typeof M=="object"&&!Array.isArray(M)?M:null}catch{return null}},u=K=>!K||Object.keys(K).length===0?"":JSON.stringify(K),[S,m]=j.useState(()=>({filter:dn(c.rFilter?g(c.rFilter):null,c.rStatusCategory),orderBy:_l(c.order||"-createdAt"),limit:c.pageSize,offset:c.current>1?(c.current-1)*c.pageSize:0})),[y,f]=j.useState(0),p=y===0&&(i===void 0||i===Wl),b=et().supports("route-scheduling-history"),[x,F]=j.useState(!1),[T,R]=Ke.useQueryLoader(Wt),[D,C]=j.useState(null),[$,z]=j.useState(null),{deployment:P}=Ke.useLazyLoadQuery(qt,{deploymentId:e,...S},{fetchKey:`${y}-${i??""}`,fetchPolicy:p?"store-and-network":"network-only"}),B=((H=(Q=(W=P==null?void 0:P.replicas)==null?void 0:W.edges)==null?void 0:Q.map(K=>K==null?void 0:K.node))==null?void 0:H.filter(K=>!!K))??[],O=K=>{a(()=>{m(M=>({...M,...K}))})},I=[{label:r("replicaStatus.Active"),value:"ACTIVE"},{label:r("replicaStatus.Inactive"),value:"INACTIVE"}],w=[{key:"trafficStatus",propertyLabel:r("deployment.TrafficStatus"),type:"enum",options:I,strictSelection:!0}],N=c.rFilter?g(c.rFilter)??void 0:void 0,G=tn([{key:"id",title:r("deployment.ReplicaId"),dataIndex:"id",fixed:"left",sorter:qn("id"),render:K=>n.jsx(Nl,{globalId:K,copyable:!0})},{key:"status",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.ReplicaLifecycle"),n.jsx(pl,{title:r("deployment.ReplicaLifecycleStatusTooltip")})]}),dataIndex:"status",render:(K,M)=>n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(Hn,{status:un(K)}),b&&n.jsx(cl,{title:r("route.RouteSchedulingHistory"),children:n.jsx(kl,{type:"link",icon:n.jsx(dt,{}),size:"small",style:{padding:0},action:async()=>{const _=Vl(M.id)??M.id;R({scope:{routeId:_},orderBy:[{field:"UPDATED_AT",direction:"DESC"}],limit:10,offset:0},{fetchPolicy:"store-and-network"}),F(!0)}})})]})},{key:"healthStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.HealthStatus"),n.jsx(pl,{title:r("deployment.HealthStatusTooltip")})]}),dataIndex:"healthStatus",render:(K,M)=>n.jsx(Hn,{status:un(K),showTooltip:un(M.status)!=="TERMINATED"})},{key:"trafficStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.TrafficStatus"),n.jsx(pl,{title:r("deployment.TrafficStatusTooltip")})]}),dataIndex:"trafficStatus",render:K=>n.jsx(ln,{color:K==="ACTIVE"?"success":"default",children:r(K==="ACTIVE"?"replicaStatus.Active":"replicaStatus.Inactive")})},{key:"session",title:r("general.Session"),onCell:()=>({style:{maxWidth:240}}),render:(K,M)=>{var ne;const _=M.sessionV2;if(!(_!=null&&_.id))return n.jsx(el.Text,{type:"secondary",children:"—"});const Y=(ne=_.metadata)==null?void 0:ne.name;return Y?n.jsxs(n.Fragment,{children:[n.jsx(ja,{ellipsis:!0,onClick:()=>C(Ze(_.id)),style:{maxWidth:160},children:Y})," ",n.jsxs(el.Text,{type:"secondary",children:["(",n.jsx(Nl,{globalId:_.id,type:"secondary"}),")"]})]}):n.jsx(Nl,{globalId:_.id})}},{key:"revision",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.RevisionNumberWithID"),n.jsx(pl,{title:r("deployment.RevisionNumberTooltip")})]}),render:(K,M)=>{const _=M.revision;return _!=null&&_.id?n.jsxs(n.Fragment,{children:[n.jsx(el.Link,{onClick:()=>z(_),children:_.revisionNumber!=null?`#${_.revisionNumber}`:"-"})," ",n.jsxs(el.Text,{type:"secondary",children:["(",n.jsx(Nl,{globalId:_.id,type:"secondary"}),")"]})]}):n.jsx(el.Text,{type:"secondary",children:"—"})}},{key:"createdAt",title:r("deployment.CreatedAt"),dataIndex:"createdAt",sorter:qn("createdAt"),render:K=>K?dl(K).format("lll"):"-"}]);return n.jsxs(n.Fragment,{children:[n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:12},children:[n.jsxs(ie,{gap:"sm",align:"start",wrap:"wrap",style:{flexShrink:1},children:[n.jsx(Pa,{value:c.rStatusCategory,onChange:K=>{const M=K.target.value,_=c.rFilter?g(c.rFilter):null;o({rStatusCategory:M,current:1}),O({filter:dn(_,M),offset:0})},options:[{label:r("deployment.Running"),value:"running"},{label:r("deployment.status.Terminated"),value:"terminated"}]}),n.jsx(Xl,{filterProperties:w,value:N,onChange:K=>{const M=u(K);o({rFilter:M||null,current:1}),O({filter:dn(K??null,c.rStatusCategory),offset:0})}})]}),n.jsx(Na,{settingId:"deployment-replicas",defaultAutoUpdateDelay:1e4,loading:t,value:"",onChange:()=>{a(()=>f(K=>K+1))}})]}),n.jsx(El,{rowKey:K=>K.id,dataSource:B,columns:G,loading:t,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:d,onColumnOverridesChange:s},order:c.order,onChangeOrder:K=>{o({order:K??null}),O({orderBy:_l(K||"-createdAt")})},pagination:{pageSize:c.pageSize,current:c.current,total:((V=P==null?void 0:P.replicas)==null?void 0:V.count)??0,onChange:(K,M)=>{o({current:K,pageSize:M});const _=K>1?(K-1)*M:0;O({limit:M,offset:_})}}}),n.jsx(fl,{children:n.jsx(Za,{open:!!D,sessionId:D??void 0,onClose:()=>C(null)})}),n.jsx(fl,{children:n.jsx(sn,{open:!!$,revisionFrgmt:$,onClose:()=>z(null)})}),T!=null&&n.jsx(fl,{children:n.jsx(rs,{open:x,queryRef:T,onReload:R,onCancel:()=>F(!1)})})]})},Gt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionCard_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentCurrentRevisionTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionHistoryTab_deployment"}],type:"ModelDeployment",abstractKey:null};Gt.hash="2a36e018f7a8b5999cad5c828ae16666";const ms=l=>{"use memo";const e=Ue.c(18),{deploymentId:i}=l,[r,t]=Ke.useQueryLoader(ti);let a;e[0]===Symbol.for("react.memo_cache_sentinel")?(a={current:1,pageSize:10},e[0]=a):a=e[0];const{baiPaginationOption:d,setTablePaginationOption:s}=In(a);let c;e[1]!==t||e[2]!==s?(c=(k,b)=>{const x=k.limit??10;s({pageSize:x,current:k.offset?Math.floor(k.offset/x)+1:1}),t(k,b)},e[1]=t,e[2]=s,e[3]=c):c=e[3];const o=c;let g;e[4]!==d.limit||e[5]!==d.offset||e[6]!==i||e[7]!==t?(g=()=>{t({scope:{entity:[{entityType:"MODEL_DEPLOYMENT",entityId:Vl(i)??i}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:d.limit,offset:d.offset},{fetchPolicy:"store-and-network"})},e[4]=d.limit,e[5]=d.offset,e[6]=i,e[7]=t,e[8]=g):g=e[8];const u=g;let S;e[9]!==u?(S=()=>{u()},e[9]=u,e[10]=S):S=e[10];const m=j.useEffectEvent(S);let y;e[11]!==m?(y=()=>{m()},e[11]=m,e[12]=y):y=e[12];let f;e[13]!==i?(f=[i],e[13]=i,e[14]=f):f=e[14],j.useEffect(y,f);let p;return e[15]!==r||e[16]!==o?(p=n.jsx(tt,{children:r?n.jsx(j.Suspense,{fallback:n.jsx(vl,{active:!0,paragraph:{rows:4}}),children:n.jsx(ai,{queryRef:r,onReload:o,tableSettings:{}})}):n.jsx(vl,{active:!0,paragraph:{rows:4}})}),e[15]=r,e[16]=o,e[17]=p):p=e[17],p},Yt=(function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e=[l,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentCurrentRevisionTab_deployment",selections:[l,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:e,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:e,storageKey:null}],type:"ModelDeployment",abstractKey:null}})();Yt.hash="81029f15aa0beb8289a21e0ca51303ff";const gs=l=>{"use memo";const e=Ue.c(21),{deploymentFrgmt:i}=l,{t:r}=ll(),{token:t}=Dl.useToken();let a;e[0]===Symbol.for("react.memo_cache_sentinel")?(a=Yt,e[0]=a):a=e[0];const d=Ke.useFragment(a,i),[s,c]=j.useState(null);let o;e[1]===Symbol.for("react.memo_cache_sentinel")?(o=(D,C,$)=>{c({revisionFrgmt:D,status:C,title:$})},e[1]=o):o=e[1];const g=o,u=d==null?void 0:d.currentRevision,S=d==null?void 0:d.deployingRevision,m=!!S&&S.id!==(u==null?void 0:u.id);let y;e[2]!==S||e[3]!==m||e[4]!==r||e[5]!==t?(y=m&&n.jsx(Tl,{type:"info",icon:n.jsx(Cn,{spin:!0}),showIcon:!0,style:{marginBottom:t.marginMD},title:r("deployment.ApplyingRevision",{revisionNumber:S.revisionNumber!=null?`#${S.revisionNumber}`:Ze(S.id)??""}),action:n.jsx(ml,{onClick:()=>g(S,"deploying",r("deployment.ApplyingRevisionDetail")),children:r("deployment.ViewRevision")})}),e[2]=S,e[3]=m,e[4]=r,e[5]=t,e[6]=y):y=e[6];let f;e[7]!==u||e[8]!==m||e[9]!==r?(f=u?n.jsx(li,{revisionFrgmt:u,status:"current"}):m?null:n.jsx(Vn,{image:Vn.PRESENTED_IMAGE_SIMPLE,description:r("deployment.NoCurrentRevisionDeployed")}),e[7]=u,e[8]=m,e[9]=r,e[10]=f):f=e[10];const p=s==null?void 0:s.revisionFrgmt,k=s==null?void 0:s.status,b=s==null?void 0:s.title,x=!!s;let F;e[11]===Symbol.for("react.memo_cache_sentinel")?(F=()=>c(null),e[11]=F):F=e[11];let T;e[12]!==p||e[13]!==k||e[14]!==b||e[15]!==x?(T=n.jsx(fl,{children:n.jsx(sn,{revisionFrgmt:p,status:k,title:b,open:x,onClose:F})}),e[12]=p,e[13]=k,e[14]=b,e[15]=x,e[16]=T):T=e[16];let R;return e[17]!==T||e[18]!==y||e[19]!==f?(R=n.jsxs(n.Fragment,{children:[y,f,T]}),e[17]=T,e[18]=y,e[19]=f,e[20]=R):R=e[20],R},Xt=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},a=[i,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],d={alias:null,args:null,kind:"ScalarField",name:"previousRevisionId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"activatedRevisionId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},g=[c,o],u={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},m={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},y=[i,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},o,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[u,S,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},m],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[u,S,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},m],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,r,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:a,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:a,storageKey:null}],storageKey:null},d,s],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,r,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:y,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:y,storageKey:null}],storageKey:null},d,s],storageKey:null}]},params:{cacheID:"484c885f3fb5c0c9f4a4e12f257a49e6",id:null,metadata:{},name:"DeploymentRevisionHistoryTabActivateMutation",operationKind:"mutation",text:`mutation DeploymentRevisionHistoryTabActivateMutation(
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
`}}})();Xt.hash="153c096cf78b28827d7a04ef0f1610d4";const Jt=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},c=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},m={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,concreteType:"ModelMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[g,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},x=[y,b],F={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[g,y,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},R={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,r,t],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,s,{alias:null,args:c,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[g,u,S,m,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[y],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[y,f],storageKey:null}],storageKey:null},p,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[k,{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[g,y,{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,r],kind:"Operation",name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,s,{alias:null,args:c,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[g,u,S,m,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[y,g],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},b,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[y,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},g],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[y,f,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"enable",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},p,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[k,F,T,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},R,{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:x,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[k,T,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},F],storageKey:null},p,R],storageKey:null}],storageKey:null}],storageKey:null},g],storageKey:null}]},params:{cacheID:"33ba9a0de55569323004cce82b1cc474",id:null,metadata:{},name:"DeploymentRevisionHistoryTabListQuery",operationKind:"query",text:`query DeploymentRevisionHistoryTabListQuery(
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
`}}})();Jt.hash="dc7544cf74c6e7b71663a4998c4d880c";const Zt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"}],type:"ModelDeployment",abstractKey:null};Zt.hash="6d00d8056ec0eba0eea404e554242adf";const zn=["revisionNumber","createdAt","clusterMode","runtimeVariantName"],ys=[...zn,...zn.map(l=>`-${l}`)],ps=({deploymentFrgmt:l,deploymentId:e,fetchKey:i})=>{"use memo";var ne;const{t:r}=ll(),{token:t}=Dl.useToken(),{message:a}=Pl.useApp(),{logger:d}=Ol(),[s,c]=j.useTransition(),[o,g]=j.useState(null),[u,S]=j.useState(null),[m,y]=j.useState(null),[f,p]=Cl("table_column_overrides.DeploymentRevisionHistoryTab"),[k,b]=Tn({current:nn.withDefault(1),pageSize:nn.withDefault(10),order:Gl(ys),rvFilter:at},{history:"replace",urlKeys:{current:"rvCurrent",pageSize:"rvPageSize",order:"rvOrder",rvFilter:"rvFilter"}}),x=Ke.useFragment(Zt,l),F=(ne=x==null?void 0:x.metadata)==null?void 0:ne.status,T=A=>{if(!A)return null;try{const v=JSON.parse(A);return v&&typeof v=="object"&&!Array.isArray(v)?v:null}catch{return null}},R=A=>!A||Object.keys(A).length===0?"":JSON.stringify(A),[D,C]=j.useState(()=>({filter:k.rvFilter?T(k.rvFilter):null,orderBy:_l(k.order)??[{field:"REVISION_NUMBER",direction:"DESC"}],limit:k.pageSize,offset:k.current>1?(k.current-1)*k.pageSize:0})),[$,z]=Il(),P=`${i??""}${$}`,B=(i===void 0||i===Wl)&&$===Wl,{deployment:O}=Ke.useLazyLoadQuery(Jt,{deploymentId:e,...D},{fetchKey:P,fetchPolicy:B?"store-and-network":"network-only"}),[I]=Ke.useMutation(Xt),w=O==null?void 0:O.currentRevisionId,N=O==null?void 0:O.deployingRevisionId,G=O==null?void 0:O.revisionHistory,W=Al(Fl(G==null?void 0:G.edges,"node")),Q=A=>{c(()=>{C(v=>({...v,...A}))})},H=()=>{c(()=>z())},V=A=>new Promise(v=>{g(A.id),I({variables:{input:{deploymentId:Ze(x.id),revisionId:Ze(A.id)}},onCompleted:(E,L)=>{var U;if(g(null),L&&L.length>0){d.error(L[0]),a.error(((U=L[0])==null?void 0:U.message)||r("general.ErrorOccurred")),v(!1);return}a.success(r("deployment.ApplySuccess",{revisionNumber:A.revisionNumber})),H(),v(!0)},onError:E=>{g(null),d.error(E),a.error((E==null?void 0:E.message)||r("general.ErrorOccurred")),v(!1)}})}),K=[{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.RevisionNumberWithID"),n.jsx(pl,{title:r("deployment.RevisionNumberTooltip")})]}),dataIndex:"revisionNumber",key:"revisionNumber",fixed:"left",sorter:!0,render:(A,v)=>{const E=Ze(v.id),L=E===w,U=E===N,Z=L||U?r("deployment.ApplyDisabled"):void 0,J=L||U||hl(F)||o===v.id;return n.jsx(bn,{title:n.jsxs(ie,{gap:"xs",align:"center",wrap:"nowrap",children:[n.jsx(el.Link,{onClick:()=>S({frgmt:v,status:L?"current":U?"deploying":"none"}),children:v.revisionNumber!=null?`#${v.revisionNumber}`:"-"}),n.jsxs(ie,{gap:0,align:"center",children:["(",n.jsx(Nl,{globalId:v.id}),")"]}),L?n.jsx(ln,{color:"success",children:r("deployment.Current")}):null,U&&!L?n.jsx(ln,{color:"warning",icon:n.jsx(Cn,{spin:!0}),children:r("deployment.Applying")}):null]}),showActions:"always",moreMenuDisabled:hl(F),actions:[{key:"deploy",title:r("deployment.Apply"),icon:n.jsx(_n,{}),disabled:J,disabledReason:Z,popConfirm:{title:r("deployment.ApplyRevision"),description:r("deployment.ApplyConfirm",{revisionNumber:v.revisionNumber}),okText:r("deployment.Apply"),cancelText:r("button.Cancel"),okButtonProps:{danger:!0},onConfirm:()=>{V(v)}}},{key:"duplicate",title:r("deployment.AddNewRevisionFromThis"),icon:n.jsx(wn,{size:t.fontSize}),showInMenu:"always",disabled:hl(F),onClick:()=>{y(v)}}]})}},{title:r("general.CreatedAt"),dataIndex:"createdAt",key:"createdAt",sorter:!0,render:A=>A?dl(A).format("lll"):"-"},{title:r("deployment.ModelVersion"),key:"modelVersion",defaultHidden:!0,render:(A,v)=>{var J,ee,q;const E=(ee=(J=v.modelDefinition)==null?void 0:J.models)==null?void 0:ee[0];if(!E)return"-";const L=E.name??"-",U=(q=E.metadata)==null?void 0:q.version,Z=typeof U=="string"?U:U!=null?String(U):null;return Z?`${L} (${Z})`:L}},{title:r("deployment.RuntimeVariant"),key:"runtimeVariantName",dataIndex:"runtimeVariantName",sorter:!0,render:(A,v)=>{var E,L;return((L=(E=v.modelRuntimeConfig)==null?void 0:E.runtimeVariant)==null?void 0:L.name)??"-"}},{title:r("deployment.Image"),key:"image",defaultHidden:!0,render:(A,v)=>{var Z,J,ee,q;const E=(J=(Z=v.imageV2)==null?void 0:Z.identity)==null?void 0:J.canonicalName,L=(q=(ee=v.imageV2)==null?void 0:ee.identity)==null?void 0:q.architecture,U=E&&L?`${E}@${L}`:E;return U?n.jsx(jl,{copyable:{text:U},ellipsis:{tooltip:U},style:{maxWidth:180},children:U}):"-"}},{title:r("deployment.ModelFolder"),key:"modelFolder",defaultHidden:!0,render:(A,v)=>{var U,Z;const E=(U=v.modelMountConfig)==null?void 0:U.vfolder,L=(Z=v.modelMountConfig)==null?void 0:Z.vfolderId;return!E&&!L?"-":E?n.jsx(ii,{vfolderNodeFragment:E}):n.jsx(el.Text,{type:"secondary",children:L})}},{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[r("deployment.ClusterMode"),n.jsx(pl,{title:r("deployment.ClusterModeTooltip")})]}),key:"clusterMode",dataIndex:"clusterMode",sorter:!0,render:(A,v)=>{var U,Z;const E=(U=v.clusterConfig)==null?void 0:U.mode,L=(Z=v.clusterConfig)==null?void 0:Z.size;return E==null&&L==null?"-":E==null?`${L}`:L==null?E:`${E} / ${L}`}}],M={message:r("general.InvalidUUID"),validate:A=>_a(A.toLowerCase())},_=[{key:"revisionNumber",propertyLabel:r("deployment.RevisionNumber"),type:"number"},{key:"createdAt",propertyLabel:r("general.CreatedAt"),type:"datetime",operators:["after","before"],defaultOperator:"after"},{key:"clusterMode",propertyLabel:r("deployment.ClusterMode"),type:"string"},{key:"imageId",propertyLabel:r("deployment.Image"),type:"uuid",fixedOperator:"equals",rule:M},{key:"modelVfolderId",propertyLabel:r("deployment.ModelFolder"),type:"uuid",fixedOperator:"equals",rule:M}],Y=k.rvFilter?T(k.rvFilter)??void 0:void 0;return n.jsxs(n.Fragment,{children:[n.jsx(fl,{children:n.jsx(sn,{revisionFrgmt:u==null?void 0:u.frgmt,status:u==null?void 0:u.status,open:!!u,onClose:()=>S(null),extra:u?n.jsxs(Ul.Compact,{children:[n.jsx(Va,{title:r("deployment.ApplyRevision"),description:r("deployment.ApplyConfirm",{revisionNumber:u.frgmt.revisionNumber}),okText:r("deployment.Apply"),cancelText:r("button.Cancel"),okButtonProps:{danger:!0},onConfirm:async()=>{await V(u.frgmt)&&S(null)},children:n.jsx(kl,{type:"primary",icon:n.jsx(_n,{}),disabled:u.status==="current"||u.status==="deploying"||hl(F)||!!o,children:r("deployment.Apply")})}),n.jsx(nt,{trigger:["click"],menu:{items:[{key:"duplicate",label:r("deployment.AddNewRevisionFromThis"),icon:n.jsx(wn,{size:t.fontSize}),disabled:hl(F),onClick:()=>{const A=u.frgmt;S(null),y(A)}}]},children:n.jsx(kl,{type:"primary",icon:n.jsx(lt,{}),"aria-label":r("button.More"),disabled:hl(F)})})]}):void 0})}),n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:t.marginSM},wrap:"wrap",children:[n.jsx(Xl,{filterProperties:_,value:Y,onChange:A=>{const v=R(A),E=T(v||null);b({rvFilter:v||null,current:1}),Q({filter:E,offset:0})}}),n.jsx(wl,{loading:s,value:"",onChange:()=>H()})]}),n.jsx(El,{rowKey:"id",dataSource:W,columns:K,loading:s,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:f,onColumnOverridesChange:p},order:k.order??void 0,onChangeOrder:A=>{b({order:A??null}),Q({orderBy:_l(A||"-revisionNumber")})},pagination:{pageSize:k.pageSize,current:k.current,total:(G==null?void 0:G.count)??0,showSizeChanger:!0,onChange:(A,v)=>{const E=A>1?(A-1)*v:0;b({current:A,pageSize:v}),Q({limit:v,offset:E})}}}),n.jsx(j.Suspense,{fallback:null,children:n.jsx(fl,{children:n.jsx(Mt,{open:!!m,deploymentFrgmt:x,sourceRevisionFrgmt:m,onRequestClose:A=>{y(null),A&&H()}})})})]})},fs=l=>{"use memo";const e=Ue.c(49),{deploymentFrgmt:i,revisionFetchKey:r,onAddRevision:t,revisionCardRef:a,isAddRevisionDisabled:d}=l,s=d===void 0?!1:d,{t:c}=ll();let o;e[0]===Symbol.for("react.memo_cache_sentinel")?(o=Gt,e[0]=o):o=e[0];const g=Ke.useFragment(o,i);let u;e[1]===Symbol.for("react.memo_cache_sentinel")?(u=Gl(["currentRevision","revisionHistory","auditLog"]).withDefault("currentRevision"),e[1]=u):u=e[1];let S;e[2]===Symbol.for("react.memo_cache_sentinel")?(S={...u,history:"replace",scroll:!1},e[2]=S):S=e[2];const[m,y]=Ea("revisionTab",S);let f;e[3]!==y?(f=w=>{(w==="currentRevision"||w==="revisionHistory"||w==="auditLog")&&y(w)},e[3]=y,e[4]=f):f=e[4];let p;e[5]!==c?(p=c("deployment.CurrentRevision"),e[5]=c,e[6]=p):p=e[6];let k;e[7]!==p?(k={key:"currentRevision",label:p},e[7]=p,e[8]=k):k=e[8];let b;e[9]!==c?(b=c("deployment.RevisionHistory"),e[9]=c,e[10]=b):b=e[10];let x;e[11]!==b?(x={key:"revisionHistory",label:b},e[11]=b,e[12]=x):x=e[12];let F;e[13]!==c?(F=c("auditLog.AuditLog"),e[13]=c,e[14]=F):F=e[14];let T;e[15]!==F?(T={key:"auditLog",label:F},e[15]=F,e[16]=T):T=e[16];let R;e[17]!==T||e[18]!==k||e[19]!==x?(R=[k,x,T],e[17]=T,e[18]=k,e[19]=x,e[20]=R):R=e[20];let D;e[21]===Symbol.for("react.memo_cache_sentinel")?(D=n.jsx(Ll,{}),e[21]=D):D=e[21];let C;e[22]!==t?(C=async()=>{t()},e[22]=t,e[23]=C):C=e[23];let $;e[24]!==c?($=c("deployment.AddRevision"),e[24]=c,e[25]=$):$=e[25];let z;e[26]!==s||e[27]!==C||e[28]!==$?(z=n.jsx(ie,{gap:"xs",align:"center",children:n.jsx(kl,{type:"primary",icon:D,disabled:s,action:C,children:$})}),e[26]=s,e[27]=C,e[28]=$,e[29]=z):z=e[29];let P;e[30]!==m||e[31]!==g?(P=m==="currentRevision"&&n.jsx(gs,{deploymentFrgmt:g}),e[30]=m,e[31]=g,e[32]=P):P=e[32];let B;e[33]!==m||e[34]!==g||e[35]!==r?(B=m==="revisionHistory"&&g&&n.jsx(Jn,{children:n.jsx(j.Suspense,{fallback:n.jsx(vl,{active:!0,paragraph:{rows:4}}),children:n.jsx(ps,{deploymentFrgmt:g,deploymentId:g.id,fetchKey:r})})}),e[33]=m,e[34]=g,e[35]=r,e[36]=B):B=e[36];let O;e[37]!==m||e[38]!==g?(O=m==="auditLog"&&g&&n.jsx(ms,{deploymentId:g.id}),e[37]=m,e[38]=g,e[39]=O):O=e[39];let I;return e[40]!==m||e[41]!==a||e[42]!==R||e[43]!==z||e[44]!==P||e[45]!==B||e[46]!==O||e[47]!==f?(I=n.jsxs(Yl,{ref:a,activeTabKey:m,onTabChange:f,tabList:R,tabBarExtraContent:z,children:[P,B,O]}),e[40]=m,e[41]=a,e[42]=R,e[43]=z,e[44]=P,e[45]=B,e[46]=O,e[47]=f,e[48]=I):I=e[48],I},ea=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"projectId"}],e=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"projectId"}],concreteType:"GroupNode",kind:"LinkedField",name:"group_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SwitchToProjectButtonQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SwitchToProjectButtonQuery",selections:e},params:{cacheID:"d9b043a52eacadb018a0097fe3c1f3c2",id:null,metadata:{},name:"SwitchToProjectButtonQuery",operationKind:"query",text:`query SwitchToProjectButtonQuery(
  $projectId: String!
) {
  group_node(id: $projectId) @since(version: "24.03.0") {
    id
    name
  }
}
`}}})();ea.hash="4618e2aed2bc3c75a1d0a91f0b01c28c";const ks=l=>{"use memo";const e=Ue.c(20);let i,r;e[0]!==l?({projectId:r,...i}=l,e[0]=l,e[1]=i,e[2]=r):(i=e[1],r=e[2]);const{t}=ll(),a=Oa(),[d,s]=j.useTransition();let c;e[3]===Symbol.for("react.memo_cache_sentinel")?(c=ea,e[3]=c):c=e[3];let o;e[4]!==r?(o=zl("GroupNode",r),e[4]=r,e[5]=o):o=e[5];let g;e[6]!==o?(g={projectId:o},e[6]=o,e[7]=g):g=e[7];const{group_node:u}=Ke.useLazyLoadQuery(c,g);let S;e[8]!==(u==null?void 0:u.id)||e[9]!==(u==null?void 0:u.name)||e[10]!==a?(S=()=>{const k=Ze((u==null?void 0:u.id)||""),b=u==null?void 0:u.name;k&&b&&s(()=>{a({projectId:k,projectName:b})})},e[8]=u==null?void 0:u.id,e[9]=u==null?void 0:u.name,e[10]=a,e[11]=S):S=e[11];const m=S,y=u==null?void 0:u.name;let f;e[12]!==t||e[13]!==y?(f=t("modelService.SwitchToProject",{projectName:y}),e[12]=t,e[13]=y,e[14]=f):f=e[14];let p;return e[15]!==i||e[16]!==m||e[17]!==d||e[18]!==f?(p=n.jsx(kl,{type:"link",size:"small",loading:d,onClick:m,...i,children:f}),e[15]=i,e[16]=m,e[17]=d,e[18]=f,e[19]=p):p=e[19],p},Ss=l=>n.jsx(j.Suspense,{fallback:n.jsx(kl,{type:"link",size:"small",loading:!0}),children:n.jsx(ks,{...l})}),hs=5e3,cn=(l,e)=>{l&&(l.style.scrollMarginTop=`${e}px`,l.scrollIntoView({behavior:"smooth",block:"start"}))},Hs=()=>{"use memo";var nl,Ne,Ge,ul,al,il,sl,ol,Ie,Te,Ve,Ye,Sl,he,Ae,rl;const l=Ue.c(122),{t:e}=ll(),{token:i}=Dl.useToken(),[r]=Zn(),t=an(),a=Kn(),d=Yn(),s=Dn();let c;l[0]!==((nl=a==null?void 0:a._config)==null?void 0:nl.blockList)?(c=(Ge=(Ne=a==null?void 0:a._config)==null?void 0:Ne.blockList)==null?void 0:Ge.includes("chat"),l[0]=(ul=a==null?void 0:a._config)==null?void 0:ul.blockList,l[1]=c):c=l[1];const o=!!c,{deploymentId:g}=wa(),u=g??"";let S;l[2]!==u?(S=zl("ModelDeployment",u),l[2]=u,l[3]=S):S=l[3];const m=S,[y,f]=j.useTransition(),[p,k]=Il(),[b,x]=Il(),[F,T]=Il(),[R,D]=En(!1),{setLeft:C,setRight:$}=D,[z,P]=En(!1),{setLeft:B,setRight:O}=P,I=j.useRef(null),w=j.useRef(null),{hash:N}=$a();let G;l[4]!==N||l[5]!==((al=i.Layout)==null?void 0:al.headerHeight)?(G=()=>{var tl,yl;cn(((tl={"#revisions":I,"#access-tokens":w}[N])==null?void 0:tl.current)??null,((yl=i.Layout)==null?void 0:yl.headerHeight)??60)},l[4]=N,l[5]=(il=i.Layout)==null?void 0:il.headerHeight,l[6]=G):G=l[6];const W=j.useEffectEvent(G);let Q;l[7]!==W?(Q=()=>{W()},l[7]=W,l[8]=Q):Q=l[8];let H;l[9]!==N?(H=[N],l[9]=N,l[10]=H):H=l[10],j.useEffect(Q,H);const[V,K]=j.useState(null);let M;l[11]===Symbol.for("react.memo_cache_sentinel")?(M=St,l[11]=M):M=l[11];let _;l[12]!==m?(_={deploymentId:m},l[12]=m,l[13]=_):_=l[13];const Y=p===Wl?"store-and-network":"network-only";let ne;l[14]!==p||l[15]!==Y?(ne={fetchKey:p,fetchPolicy:Y},l[14]=p,l[15]=Y,l[16]=ne):ne=l[16];const{deployment:A}=Ke.useLazyLoadQuery(M,_,ne);if(!A.ok){const $e=A.errors;if($e.some(Fs)){let Rl;return l[17]===Symbol.for("react.memo_cache_sentinel")?(Rl=n.jsx(vs,{}),l[17]=Rl):Rl=l[17],Rl}const yl=$e.map(bs).filter(Boolean),Ml=new Error(yl.join("; ")||"DeploymentDetailPageQuery failed.");throw Ml.errors=$e,Ml}const v=A.value,E=v.metadata.name,L=v.metadata.status,U=L==="READY",Z=v.metadata.projectId??null,J=!!Z&&Z!==d.id,ee=!v.currentRevision&&!v.deployingRevision,q=!!v.deployingRevision&&v.deployingRevision.id!==((sl=v.currentRevision)==null?void 0:sl.id),te=!!v.networkAccess.endpointUrl,ye=(((ol=v.accessTokens)==null?void 0:ol.count)??0)>0;let de;l[18]!==L?(de=hl(L),l[18]=L,l[19]=de):de=l[19];const pe=de,ue=(((Ie=v.replicaState)==null?void 0:Ie.desiredReplicaCount)??0)===0,fe=!ue&&(((Te=v.runningReplicas)==null?void 0:Te.count)??0)===0,se=ue||fe,ce=v.networkAccess.openToPublic===!1&&!pe&&te&&!ye,re=((Ye=(Ve=v.creator)==null?void 0:Ve.basicInfo)==null?void 0:Ye.email)??null,ke=!re||re===r.email;let Re;l[20]!==k?(Re=()=>{f(()=>k())},l[20]=k,l[21]=Re):Re=l[21];const Fe=Re;let De;l[22]!==C||l[23]!==((Sl=i.Layout)==null?void 0:Sl.headerHeight)||l[24]!==k||l[25]!==T||l[26]!==x?(De=($e,tl)=>{var yl;C(),$e&&(tl&&K(tl),f(()=>{k(),x(),T()}),cn(I.current,((yl=i.Layout)==null?void 0:yl.headerHeight)??60))},l[22]=C,l[23]=(he=i.Layout)==null?void 0:he.headerHeight,l[24]=k,l[25]=T,l[26]=x,l[27]=De):De=l[27];const xe=De;let ae;l[28]!==ue||l[29]!==fe||l[30]!==e?(ae=()=>{if(ue)return n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NoDesiredReplicas")});if(fe)return n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NoRunningReplicas")})},l[28]=ue,l[29]=fe,l[30]=e,l[31]=ae):ae=l[31];const ve=ae;let je;l[32]!==Z||l[33]!==J||l[34]!==e?(je=J&&Z&&n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NotInProject"),action:n.jsx(Ss,{projectId:Z})}),l[32]=Z,l[33]=J,l[34]=e,l[35]=je):je=l[35];let Ce;l[36]!==ve||l[37]!==se||l[38]!==ee||l[39]!==pe?(Ce=se&&!ee&&!pe&&ve(),l[36]=ve,l[37]=se,l[38]=ee,l[39]=pe,l[40]=Ce):Ce=l[40];let Me;l[41]!==s||l[42]!==u||l[43]!==se||l[44]!==ee||l[45]!==o||l[46]!==U||l[47]!==e||l[48]!==i.fontSizeLG||l[49]!==t?(Me=U&&!ee&&!se&&n.jsx(Tl,{type:"success",showIcon:!0,title:e("deployment.DeploymentReady"),action:!o&&n.jsx(ml,{type:"primary",icon:n.jsx(Ba,{size:i.fontSizeLG}),onClick:()=>{t({pathname:s("chat",{scope:"project"}),search:new URLSearchParams({endpointId:u}).toString()})},children:e("deployment.StartChatTest")})}),l[41]=s,l[42]=u,l[43]=se,l[44]=ee,l[45]=o,l[46]=U,l[47]=e,l[48]=i.fontSizeLG,l[49]=t,l[50]=Me):Me=l[50];let Pe;l[51]!==L||l[52]!==ee||l[53]!==J||l[54]!==$||l[55]!==e?(Pe=ee&&!J&&!hl(L)&&n.jsx(Tl,{type:"warning",showIcon:!0,title:e("deployment.NoCurrentRevisionDeployed"),action:n.jsx(kl,{type:"primary",icon:n.jsx(Ll,{}),action:async()=>{$()},children:e("deployment.AddRevision")})}),l[51]=L,l[52]=ee,l[53]=J,l[54]=$,l[55]=e,l[56]=Pe):Pe=l[56];let Xe;l[57]!==pe||l[58]!==ce||l[59]!==O||l[60]!==e?(Xe=ce&&n.jsx(Tl,{type:"info",showIcon:!0,title:e("deployment.PrivateDeploymentAlertTitle"),action:n.jsx(kl,{type:"primary",icon:n.jsx(Ll,{}),action:async()=>{O()},disabled:pe,children:e("deployment.AddAccessToken")})}),l[57]=pe,l[58]=ce,l[59]=O,l[60]=e,l[61]=Xe):Xe=l[61];let Je;l[62]===Symbol.for("react.memo_cache_sentinel")?(Je={margin:0},l[62]=Je):Je=l[62];let h;l[63]!==E?(h=n.jsx(el.Title,{level:3,style:Je,children:E}),l[63]=E,l[64]=h):h=l[64];let X;l[65]!==L?(X=n.jsx(ct,{status:L}),l[65]=L,l[66]=X):X=l[66];let le;l[67]!==h||l[68]!==X?(le=n.jsxs(ie,{direction:"row",align:"center",gap:"sm",children:[h,X]}),l[67]=h,l[68]=X,l[69]=le):le=l[69];const oe=q?hs:null;let me;l[70]!==v||l[71]!==Fe||l[72]!==y||l[73]!==oe?(me=n.jsx(as,{deploymentFrgmt:v,isPendingRefetch:y,onRefetch:Fe,autoUpdateDelay:oe}),l[70]=v,l[71]=Fe,l[72]=y,l[73]=oe,l[74]=me):me=l[74];const Se=pe||J;let Le;l[75]!==v||l[76]!==$||l[77]!==b||l[78]!==Se?(Le=n.jsx(fs,{deploymentFrgmt:v,revisionFetchKey:b,onAddRevision:$,revisionCardRef:I,isAddRevisionDisabled:Se}),l[75]=v,l[76]=$,l[77]=b,l[78]=Se,l[79]=Le):Le=l[79];let _e;l[80]!==v||l[81]!==m||l[82]!==F?(_e=n.jsx(us,{deploymentFrgmt:v,deploymentId:m,replicaFetchKey:F}),l[80]=v,l[81]=m,l[82]=F,l[83]=_e):_e=l[83];let Be;l[84]!==v?(Be=n.jsx(Zi,{deploymentFrgmt:v}),l[84]=v,l[85]=Be):Be=l[85];let Oe;l[86]!==B||l[87]!==O?(Oe=$e=>{$e?O():B()},l[86]=B,l[87]=O,l[88]=Oe):Oe=l[88];let Qe;l[89]!==Fe||l[90]!==((Ae=i.Layout)==null?void 0:Ae.headerHeight)?(Qe=()=>{var $e;Fe(),cn(w.current,(($e=i.Layout)==null?void 0:$e.headerHeight)??60)},l[89]=Fe,l[90]=(rl=i.Layout)==null?void 0:rl.headerHeight,l[91]=Qe):Qe=l[91];let be;l[92]!==z||l[93]!==v||l[94]!==m||l[95]!==pe||l[96]!==ke||l[97]!==Oe||l[98]!==Qe?(be=n.jsx(Ai,{cardRef:w,deploymentFrgmt:v,deploymentId:m,isOwnedByCurrentUser:ke,isDeploymentDestroying:pe,isCreateModalOpen:z,onCreateModalOpenChange:Oe,onTokenCreated:Qe}),l[92]=z,l[93]=v,l[94]=m,l[95]=pe,l[96]=ke,l[97]=Oe,l[98]=Qe,l[99]=be):be=l[99];let He;l[100]!==R||l[101]!==v||l[102]!==xe?(He=n.jsx(fl,{children:n.jsx(Mt,{open:R,onRequestClose:xe,deploymentFrgmt:v})}),l[100]=R,l[101]=v,l[102]=xe,l[103]=He):He=l[103];const qe=!!V;let We;l[104]===Symbol.for("react.memo_cache_sentinel")?(We=()=>K(null),l[104]=We):We=l[104];let we;l[105]!==V||l[106]!==qe?(we=n.jsx(fl,{children:n.jsx(sn,{revisionFrgmt:V,open:qe,onClose:We})}),l[105]=V,l[106]=qe,l[107]=we):we=l[107];let ze;return l[108]!==je||l[109]!==Ce||l[110]!==Me||l[111]!==Pe||l[112]!==Xe||l[113]!==le||l[114]!==me||l[115]!==Le||l[116]!==_e||l[117]!==Be||l[118]!==be||l[119]!==He||l[120]!==we?(ze=n.jsxs(ie,{direction:"column",align:"stretch",gap:"md",children:[je,Ce,Me,Pe,Xe,le,me,Le,_e,Be,be,He,we]}),l[108]=je,l[109]=Ce,l[110]=Me,l[111]=Pe,l[112]=Xe,l[113]=le,l[114]=me,l[115]=Le,l[116]=_e,l[117]=Be,l[118]=be,l[119]=He,l[120]=we,l[121]=ze):ze=l[121],ze},vs=()=>{"use memo";const l=Ue.c(40),{t:e}=ll(),i=an(),{firstAvailableMenuItem:r}=Ha(),t=Qa();let a;l[0]!==t||l[1]!==r?(a=r?qa(r.key,t):"/start",l[0]=t,l[1]=r,l[2]=a):a=l[2];const d=a;let s,c,o,g,u,S,m,y,f,p,k;if(l[3]!==d||l[4]!==(r==null?void 0:r.labelText)||l[5]!==e||l[6]!==i){const T=(r==null?void 0:r.labelText)??e("webui.menu.FirstPageNameAlias");o=ie,l[18]===Symbol.for("react.memo_cache_sentinel")?(f={margin:"auto"},l[18]=f):f=l[18],p="center",k="center",c=za,m="warning",l[19]!==e?(y=e("deployment.NotAccessibleOrDeleted"),l[19]=e,l[20]=y):y=l[20],s=ml,g="primary",l[21]!==d||l[22]!==i?(u=()=>{i(d)},l[21]=d,l[22]=i,l[23]=u):u=l[23],S=e("button.GoBackToStartPage",{title:T}),l[3]=d,l[4]=r==null?void 0:r.labelText,l[5]=e,l[6]=i,l[7]=s,l[8]=c,l[9]=o,l[10]=g,l[11]=u,l[12]=S,l[13]=m,l[14]=y,l[15]=f,l[16]=p,l[17]=k}else s=l[7],c=l[8],o=l[9],g=l[10],u=l[11],S=l[12],m=l[13],y=l[14],f=l[15],p=l[16],k=l[17];let b;l[24]!==s||l[25]!==g||l[26]!==u||l[27]!==S?(b=n.jsx(s,{type:g,onClick:u,children:S}),l[24]=s,l[25]=g,l[26]=u,l[27]=S,l[28]=b):b=l[28];let x;l[29]!==c||l[30]!==m||l[31]!==y||l[32]!==b?(x=n.jsx(c,{status:m,title:y,extra:b}),l[29]=c,l[30]=m,l[31]=y,l[32]=b,l[33]=x):x=l[33];let F;return l[34]!==o||l[35]!==x||l[36]!==f||l[37]!==p||l[38]!==k?(F=n.jsx(o,{style:f,justify:p,align:k,children:x}),l[34]=o,l[35]=x,l[36]=f,l[37]=p,l[38]=k,l[39]=F):F=l[39],F};function Fs(l){return/Insufficient permission/i.test((l==null?void 0:l.message)??"")}function bs(l){return(l==null?void 0:l.message)??""}export{Hs as default};
//# sourceMappingURL=DeploymentDetailPage-rf_DqmZg.js.map
