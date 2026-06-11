import{bT as et,h as ll,ad as In,r as _,aE as vn,ck as ca,au as Pl,d1 as lt,b9 as Yl,i as Ve,cl as ma,a6 as bl,bU as ga,ac as An,bj as En,j as n,az as xl,ak as ya,cn as pa,bB as Jl,N as Xe,m as Dn,ca as fa,cm as ka,aj as Sa,a1 as gn,aN as zl,b7 as Ul,bX as ml,bN as Ol,a3 as Cn,u as tl,t as Il,A as $l,v as Wl,K as nt,cb as Mn,T as el,aq as cl,B as ie,aD as wl,b6 as El,z as pl,bJ as ln,a7 as Sl,P as Gl,F as ue,d2 as ha,a_ as jn,b0 as Ln,b8 as Pn,aT as dn,d3 as tt,bW as Ll,cD as va,y as Bl,aS as at,bq as yl,d4 as Fa,an as Nn,d5 as xa,a4 as yn,d6 as Zl,b4 as gl,d7 as ba,w as en,ce as Ra,b5 as On,aJ as $n,d8 as Ta,d9 as Ka,da as Ia,db as Ql,dc as Aa,Y as Da,dd as Ca,a8 as Ma,bn as wn,de as sn,bD as rn,H as it,df as ja,cC as st,bg as La,a as rt,aI as Pa,dg as Na,M as Va,a5 as _a,dh as Ea,cc as Xl,c_ as Oa,bu as nn,bv as Vn,bt as $a,di as fl,a$ as wa,f as on,bY as ot,cX as ut,dj as cn,b$ as ql,dk as Bn,cB as mn,bV as _n,c2 as Ba,G as dt,dl as ct,ax as Fn,dm as Ha,p as pn,Z as mt,dn as Qa,b_ as qa,cK as gt,ay as za,ai as Hn,c$ as Ua,bK as yt,d0 as Wa,D as Ga,cF as Ya,c1 as Xa,dp as Ja,dq as Za,aY as Qn,dr as ei,ds as li,dt as ni,du as ti}from"./index-DluNL-GQ.js";import{t as pt,f as ai,i as kl,D as fn,a as ii,b as ft,B as si}from"./DeploymentRevisionDetailDrawer-C-by95-U.js";import{R as ri}from"./UndoOutlined-8UP-ohpZ.js";import{B as qn}from"./BAIVFolderSelect-BaU_j_e1.js";import{P as oi}from"./PrometheusQueryTemplatePreview-BW3cQCkG.js";import{B as kt,n as St,a as ht,o as ui,R as vt,S as di}from"./SessionDetailDrawer-Bz9DVA8f.js";import{B as tn}from"./BAIGraphQLPropertyFilter-BEXGUJCX.js";import{F as ci}from"./FolderLink-HST2MS7p.js";import{B as Hl}from"./BAIId-qXX3wVPc.js";import{S as mi,a as gi}from"./ScopedAuditLog-BWPayZ9o.js";import{B as yi}from"./BooleanTag-CsnTLJdn.js";import"./corner-down-left-C-_NlREz.js";import"./zip-Br5YunmY.js";import"./unzip-iY0mdYYt.js";/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const pi=[["line",{x1:"15",x2:"15",y1:"12",y2:"18",key:"1p7wdc"}],["line",{x1:"12",x2:"18",y1:"15",y2:"15",key:"1nscbv"}],["rect",{width:"14",height:"14",x:"8",y:"8",rx:"2",ry:"2",key:"17jyea"}],["path",{d:"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2",key:"zix9uf"}]],zn=et("copy-plus",pi);/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const fi=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",key:"usdka0"}]],Un=et("folder-open",fi),Ft=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},s=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"NAME"}]}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e,i],kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectPaginatedQuery",selections:s,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[i,e,l],kind:"Operation",name:"BAIRuntimeVariantSelectPaginatedQuery",selections:s},params:{cacheID:"e8d20623434b823880b9543cf3297c3f",id:null,metadata:{},name:"BAIRuntimeVariantSelectPaginatedQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectPaginatedQuery(
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
`}}}();Ft.hash="65da05baef2fee7bd3840fc61e39a8d8";const xt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"},{defaultValue:null,kind:"LocalArgument",name:"skip"}],e=[{condition:"skip",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectValueQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIRuntimeVariantSelectValueQuery",selections:e},params:{cacheID:"f029b9c8b12e9bc799f1ff1caaebd031",id:null,metadata:{},name:"BAIRuntimeVariantSelectValueQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectValueQuery(
  $id: UUID!
  $skip: Boolean!
) {
  runtimeVariant(id: $id) @skip(if: $skip) {
    id
    name
  }
}
`}}}();xt.hash="f7c1435633aeb06ecc9eafe324f06550";const ki=l=>{"use memo";var Ne;const e=ll.c(74);let i,s,t,a;e[0]!==l?({loading:i,onResolvedNamesChange:s,ref:t,...a}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a):(i=e[1],s=e[2],t=e[3],a=e[4]);const{t:d}=In(),r=_.useRef(null),[o,u]=vn(a);let m;e[5]===Symbol.for("react.memo_cache_sentinel")?(m={valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"},e[5]=m):m=e[5];const[c,k]=vn(a,m),h=_.useDeferredValue(c),[v,g]=_.useState(),y=ca(v),[p,P]=_.useOptimistic(v),[T,x]=_.useTransition(),[D,E]=Pl(),H=_.useDeferredValue(D),b=_.useDeferredValue(o);let K;e[6]!==b?(K=b?lt(Yl(b)):"",e[6]=b,e[7]=K):K=e[7];const R=K;let C;e[8]===Symbol.for("react.memo_cache_sentinel")?(C=xt,e[8]=C):C=e[8];const A=!R;let M;e[9]!==R||e[10]!==A?(M={id:R,skip:A},e[9]=R,e[10]=A,e[11]=M):M=e[11];const I=R?"store-or-network":"store-only";let V;e[12]!==H||e[13]!==I?(V={fetchPolicy:I,fetchKey:H},e[12]=H,e[13]=I,e[14]=V):V=e[14];const{runtimeVariant:L}=Ve.useLazyLoadQuery(C,M,V);let B;e[15]!==y?(B=y?{name:{iContains:y}}:null,e[15]=y,e[16]=B):B=e[16];const z=B;let U,$;e[17]===Symbol.for("react.memo_cache_sentinel")?($=Ft,U={limit:20},e[17]=U,e[18]=$):(U=e[17],$=e[18]);let S;e[19]!==z?(S={filter:z},e[19]=z,e[20]=S):S=e[20];const F=h?"network-only":"store-only";let O;e[21]!==H||e[22]!==F?(O={fetchPolicy:F,fetchKey:H},e[21]=H,e[22]=F,e[23]=O):O=e[23];let Y;e[24]===Symbol.for("react.memo_cache_sentinel")?(Y={getTotal:Si,getItem:vi,getId:Fi},e[24]=Y):Y=e[24];const{paginationData:X,result:ne,loadNext:N,isLoadingNext:j}=ma($,U,S,O,Y);let w,q;e[25]!==E?(w=()=>({refetch:()=>{x(()=>{E()})}}),q=[E,x],e[25]=E,e[26]=w,e[27]=q):(w=e[26],q=e[27]),_.useImperativeHandle(t,w,q);let W;e[28]!==s||e[29]!==X||e[30]!==L?(W=()=>{if(!s)return;const xe={};if(L!=null&&L.id&&L.name){const de=Xe(L.id);de&&(xe[de]=L.name)}for(const de of X??[])if(de!=null&&de.id&&de.name){const Be=Xe(de.id);Be&&(xe[Be]=de.name)}Dn(xe)||s(xe)},e[28]=s,e[29]=X,e[30]=L,e[31]=W):W=e[31];const Z=_.useEffectEvent(W);let ee;e[32]!==Z?(ee=()=>{Z()},e[32]=Z,e[33]=ee):ee=e[33];let G;e[34]!==X||e[35]!==L?(G=[L,X],e[34]=X,e[35]=L,e[36]=G):G=e[36],_.useEffect(ee,G);let Q;e[37]!==X?(Q=bl(X,xi),e[37]=X,e[38]=Q):Q=e[38];const Se=Q,ce=L==null?void 0:L.name;let ae;e[39]!==b||e[40]!==ce?(ae=b?{label:ce??Yl(b),value:Yl(b)}:void 0,e[39]=b,e[40]=ce,e[41]=ae):ae=e[41];const Me=ae,[Re,ve]=_.useState(Me);let me;e[42]!==d?(me=d("comp:BAIRuntimeVariantSelect.SelectRuntimeVariant"),e[42]=d,e[43]=me):me=e[43];const pe=i||o!==b||v!==y||T;let ge;e[44]!==a||e[45]!==P?(ge=async xe=>{var de;P(xe),g(xe),await((de=a.searchAction)==null?void 0:de.call(a,xe))},e[44]=a,e[45]=P,e[46]=ge):ge=e[46];let he;e[47]!==p||e[48]!==a.showSearch?(he=a.showSearch===!1?!1:{searchValue:p,autoClearSearchValue:!0,...ga(a.showSearch)?An(a.showSearch,["searchValue"]):{},filterOption:!1},e[47]=p,e[48]=a.showSearch,e[49]=he):he=e[49];const Te=o!==b?Re:Me;let Fe;e[50]!==Se||e[51]!==u?(Fe=(xe,de)=>{var le;if(En(xe)||fa(xe)){ve(void 0),u(void 0,de);return}const Be=ka(xe)[0],J={label:Sa(Be.label)?Be.label:((le=Se.find(te=>te.value===Be.value))==null?void 0:le.label)??Yl(Be.value),value:Yl(Be.value)};ve(J),u(J.value,de)},e[50]=Se,e[51]=u,e[52]=Fe):Fe=e[52];let je;e[53]!==N?(je=()=>{N()},e[53]=N,e[54]=je):je=e[54];let fe;e[55]!==X?(fe=En(X)?n.jsx(xl.Input,{active:!0,size:"small",block:!0}):void 0,e[55]=X,e[56]=fe):fe=e[56];let Ie;e[57]!==j||e[58]!==ne.runtimeVariants?(Ie=ya((Ne=ne.runtimeVariants)==null?void 0:Ne.count)&&ne.runtimeVariants.count>0?n.jsx(pa,{loading:j,total:ne.runtimeVariants.count}):void 0,e[57]=j,e[58]=ne.runtimeVariants,e[59]=Ie):Ie=e[59];let ke;return e[60]!==Se||e[61]!==c||e[62]!==a||e[63]!==k||e[64]!==me||e[65]!==pe||e[66]!==ge||e[67]!==he||e[68]!==Te||e[69]!==Fe||e[70]!==je||e[71]!==fe||e[72]!==Ie?(ke=n.jsx(Jl,{ref:r,placeholder:me,loading:pe,...a,searchAction:ge,showSearch:he,value:Te,labelInValue:!0,onChange:Fe,options:Se,endReached:je,open:c,onOpenChange:k,notFoundContent:fe,footer:Ie}),e[60]=Se,e[61]=c,e[62]=a,e[63]=k,e[64]=me,e[65]=pe,e[66]=ge,e[67]=he,e[68]=Te,e[69]=Fe,e[70]=je,e[71]=fe,e[72]=Ie,e[73]=ke):ke=e[73],ke};function Si(l){var e;return((e=l.runtimeVariants)==null?void 0:e.count)??void 0}function hi(l){return l==null?void 0:l.node}function vi(l){var e,i;return(i=(e=l.runtimeVariants)==null?void 0:e.edges)==null?void 0:i.map(hi)}function Fi(l){return l==null?void 0:l.id}function xi(l){return{label:l==null?void 0:l.name,value:l!=null&&l.id?Xe(l.id):void 0}}const bt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIDeploymentSchedulingHistoryNodesFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"DeploymentHistory",abstractKey:null};bt.hash="993394664d6af0ea9ee225d992cff972";const xn=[];[...xn,...xn.map(l=>`-${l}`)];const Tl=l=>Cn(xn,l),bi=l=>{"use memo";const e=ll.c(24);let i,s,t,a,d;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:s,customizeColumns:i,onChangeOrder:t,...d}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5]);const{t:r}=In();let o;e[6]===Symbol.for("react.memo_cache_sentinel")?(o=bt,e[6]=o):o=e[6];const u=Ve.useFragment(o,a);let m;if(e[7]!==i||e[8]!==s||e[9]!==r){let p;e[11]!==s?(p=T=>s?An(T,"sorter"):T,e[11]=s,e[12]=p):p=e[12];const P=bl(gn([{dataIndex:"updatedAt",title:r("comp:BAIDeploymentSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:Ri,sorter:Tl("updated_at")},{dataIndex:"createdAt",title:r("comp:BAIDeploymentSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:Ti,sorter:Tl("created_at")},{dataIndex:"phase",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Phase"),key:"phase",sorter:Tl("phase")},{dataIndex:"result",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Result"),key:"result",render:Ki,sorter:Tl("result")},{dataIndex:"category",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Category"),key:"category",sorter:Tl("category")},{title:r("comp:BAIDeploymentSchedulingHistoryNodes.StatusTransition"),key:"statusTransition",children:[{key:"fromStatus",title:r("comp:BAIDeploymentSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Tl("from_status")},{key:"toStatus",title:r("comp:BAIDeploymentSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Tl("to_status")}]},{dataIndex:"attempts",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Tl("attempts")},{key:"errorCode",title:r("comp:BAIDeploymentSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Ii,sorter:Tl("errorCode")},{key:"message",title:r("comp:BAIDeploymentSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:Ai,render:Di,sorter:Tl("message")}]),p);m=i?i(P):P,e[7]=i,e[8]=s,e[9]=r,e[10]=m}else m=e[10];const c=m;let k;e[13]!==u?(k=zl(u),e[13]=u,e[14]=k):k=e[14];let h;e[15]===Symbol.for("react.memo_cache_sentinel")?(h={x:"max-content"},e[15]=h):h=e[15];let v;e[16]!==t?(v=p=>{t==null||t(p||null)},e[16]=t,e[17]=v):v=e[17];let g;e[18]===Symbol.for("react.memo_cache_sentinel")?(g={rowExpandable:Ci,expandedRowRender:Mi},e[18]=g):g=e[18];let y;return e[19]!==c||e[20]!==k||e[21]!==v||e[22]!==d?(y=n.jsx(Ul,{rowKey:"id",dataSource:k,columns:c,scroll:h,onChangeOrder:v,expandable:g,...d}),e[19]=c,e[20]=k,e[21]=v,e[22]=d,e[23]=y):y=e[23],y};function Ri(l){return n.jsx("span",{children:ml(l).format("ll LTS")})}function Ti(l){return n.jsx("span",{children:ml(l).format("ll LTS")})}function Ki(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(kt,{result:i})}function Ii(l,e){return e.errorCode?n.jsx(Ol,{monospace:!0,children:e.errorCode}):"-"}function Ai(){return{style:{maxWidth:500}}}function Di(l,e){return e.message?n.jsx(Ol,{title:e.message,style:{width:"100%"},children:St(e.message)}):"-"}function Ci(l){return!Dn(l.subSteps)}function Mi(l){return n.jsx(ht,{resizable:!0,subStepsFrgmt:l.subSteps,pagination:!1})}const Rt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"BAIRouteSchedulingHistoryNodeTableFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"routeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null},{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{args:null,kind:"FragmentSpread",name:"BAISubStepNodesFragment"}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],type:"RouteHistory",abstractKey:null};Rt.hash="3f283b3e8ef039a11e41ade44a38092f";const bn=[];[...bn,...bn.map(l=>`-${l}`)];const Kl=l=>Cn(bn,l),ji=l=>{"use memo";const e=ll.c(24);let i,s,t,a,d;e[0]!==l?({schedulingHistoryFrgmt:a,disableSorter:s,customizeColumns:i,onChangeOrder:t,...d}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5]);const{t:r}=In();let o;e[6]===Symbol.for("react.memo_cache_sentinel")?(o=Rt,e[6]=o):o=e[6];const u=Ve.useFragment(o,a);let m;if(e[7]!==i||e[8]!==s||e[9]!==r){let p;e[11]!==s?(p=T=>s?An(T,"sorter"):T,e[11]=s,e[12]=p):p=e[12];const P=bl(gn([{dataIndex:"updatedAt",title:r("comp:BAIRouteSchedulingHistoryNodes.UpdatedAt"),key:"updatedAt",render:Li,sorter:Kl("updated_at")},{dataIndex:"createdAt",title:r("comp:BAIRouteSchedulingHistoryNodes.CreatedAt"),key:"createdAt",render:Pi,sorter:Kl("created_at")},{dataIndex:"phase",title:r("comp:BAIRouteSchedulingHistoryNodes.Phase"),key:"phase",sorter:Kl("phase")},{dataIndex:"result",title:r("comp:BAIRouteSchedulingHistoryNodes.Result"),key:"result",render:Ni,sorter:Kl("result")},{dataIndex:"category",title:r("comp:BAIRouteSchedulingHistoryNodes.Category"),key:"category",sorter:Kl("category")},{title:r("comp:BAIRouteSchedulingHistoryNodes.StatusTransition"),key:"statusTransition",children:[{key:"fromStatus",title:r("comp:BAIRouteSchedulingHistoryNodes.From"),dataIndex:"fromStatus",sorter:Kl("from_status")},{key:"toStatus",title:r("comp:BAIRouteSchedulingHistoryNodes.To"),dataIndex:"toStatus",sorter:Kl("to_status")}]},{dataIndex:"attempts",title:r("comp:BAIRouteSchedulingHistoryNodes.Attempts"),key:"attempts",sorter:Kl("attempts")},{key:"errorCode",title:r("comp:BAIRouteSchedulingHistoryNodes.ErrorCode"),dataIndex:"errorCode",render:Vi,sorter:Kl("errorCode")},{key:"message",title:r("comp:BAIRouteSchedulingHistoryNodes.Message"),dataIndex:"message",onCell:_i,render:Ei,sorter:Kl("message")}]),p);m=i?i(P):P,e[7]=i,e[8]=s,e[9]=r,e[10]=m}else m=e[10];const c=m;let k;e[13]!==u?(k=zl(u),e[13]=u,e[14]=k):k=e[14];let h;e[15]===Symbol.for("react.memo_cache_sentinel")?(h={x:"max-content"},e[15]=h):h=e[15];let v;e[16]!==t?(v=p=>{t==null||t(p||null)},e[16]=t,e[17]=v):v=e[17];let g;e[18]===Symbol.for("react.memo_cache_sentinel")?(g={rowExpandable:Oi,expandedRowRender:$i},e[18]=g):g=e[18];let y;return e[19]!==c||e[20]!==k||e[21]!==v||e[22]!==d?(y=n.jsx(Ul,{rowKey:"id",dataSource:k,columns:c,scroll:h,onChangeOrder:v,expandable:g,...d}),e[19]=c,e[20]=k,e[21]=v,e[22]=d,e[23]=y):y=e[23],y};function Li(l){return n.jsx("span",{children:ml(l).format("ll LTS")})}function Pi(l){return n.jsx("span",{children:ml(l).format("ll LTS")})}function Ni(l,e){const i=e.result&&e.result!=="%future added value"?e.result:null;return n.jsx(kt,{result:i})}function Vi(l,e){return e.errorCode?n.jsx(Ol,{monospace:!0,children:e.errorCode}):"-"}function _i(){return{style:{maxWidth:500}}}function Ei(l,e){return e.message?n.jsx(Ol,{title:e.message,style:{width:"100%"},children:St(e.message)}):"-"}function Oi(l){return!Dn(l.subSteps)}function $i(l){return n.jsx(ht,{resizable:!0,subStepsFrgmt:l.subSteps,pagination:!1})}const Tt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},d={alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},r={alias:null,args:null,concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:null},o=[i],u={alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},k={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,s,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},h={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[m,c,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},k],storageKey:null},v={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},g=[s,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],y={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null}],storageKey:null},p={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},P={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[m,c,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},k],storageKey:null},T={alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[s,i],storageKey:null},x={alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:g,storageKey:null}],storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},E={alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},H={alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},M={alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},L={alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},B={alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},z={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},U={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},$={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[B,{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentDetailPageQuery",selections:[{kind:"CatchField",field:{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[s,t,a],storageKey:null},d,r,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:o,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:o,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[u],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentConfigurationSection_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentReplicasTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAccessTokensTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAutoScalingTab_deployment"}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[s,t,a,{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[s],storageKey:null},i],storageKey:null}],storageKey:null},d,r,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,h,v,y,p,P,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},T,x,D],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[s,E,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[H,b,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[K,R,C,A,M,I],storageKey:null},V,L],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[B],storageKey:null}],storageKey:null},z,U,p,$],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:[i,z,U,v,p,y,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[T,D,x],storageKey:null},h,P,$,{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[s,E,{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[H,V,b,L,{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[K,C,R,A,M,I],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[u,i],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"5913260aefbefad07ea0672c2a759277",id:null,metadata:{},name:"DeploymentDetailPageQuery",operationKind:"query",text:`query DeploymentDetailPageQuery(
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
          path
          maxRetries
          initialDelay
          interval
          maxWaitTime
        }
      }
    }
  }
  imageV2 {
    id
    identity {
      canonicalName
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
`}}}();It.hash="4e84247d3aa97d220f9a949a56d396e1";const At=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAccessTokenPayload",kind:"LinkedField",name:"createAccessToken",plural:!1,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"accessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabCreateMutation",selections:e},params:{cacheID:"ad0b1632c09adadb34c59dfacd183923",id:null,metadata:{},name:"DeploymentAccessTokensTabCreateMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensTabCreateMutation(
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
`}}}();At.hash="df1b417c9205070e2bf82168815c312e";const Dt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Dt.hash="48a180522415b103a2e930a5abc7a973";const wi=l=>{"use memo";var Fe;const e=ll.c(91);let i,s,t,a,d,r,o;e[0]!==l?({deploymentFrgmt:t,deploymentId:a,isOwnedByCurrentUser:r,isDeploymentDestroying:o,onTokenCreated:d,cardRef:i,...s}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d,e[6]=r,e[7]=o):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5],r=e[6],o=e[7]);const u=r===void 0?!0:r,m=o===void 0?!1:o,{t:c}=tl(),{token:k}=Il.useToken(),{message:h}=$l.useApp(),{logger:v}=Wl(),[g,y]=_.useTransition(),[p,P]=_.useState(0);let T;e[8]===Symbol.for("react.memo_cache_sentinel")?(T={defaultValue:!1,valuePropName:"isCreateModalOpen",trigger:"onCreateModalOpenChange"},e[8]=T):T=e[8];const[x,D]=vn(s,T),[E,H]=_.useState(null),b=_.useDeferredValue(p);let K;e[9]===Symbol.for("react.memo_cache_sentinel")?(K=Dt,e[9]=K):K=e[9];const R=Ve.useFragment(K,t);let C;e[10]===Symbol.for("react.memo_cache_sentinel")?(C=At,e[10]=C):C=e[10];const A=nt(C);let M;e[11]===Symbol.for("react.memo_cache_sentinel")?(M=()=>{y(()=>{P(Qi)})},e[11]=M):M=e[11];const I=M,V=!!((Fe=R.networkAccess)!=null&&Fe.endpointUrl),L=m||!u,B=L||!V;let z;e[12]!==c?(z=c("deployment.tab.AccessTokens"),e[12]=c,e[13]=z):z=e[13];let U;e[14]!==c?(U=c("deployment.tab.description.AccessTokens"),e[14]=c,e[15]=U):U=e[15];let $;e[16]!==k.colorTextDescription?($=n.jsx(Mn,{style:{color:k.colorTextDescription}}),e[16]=k.colorTextDescription,e[17]=$):$=e[17];let S;e[18]!==U||e[19]!==$?(S=n.jsx(cl,{title:U,children:$}),e[18]=U,e[19]=$,e[20]=S):S=e[20];let F;e[21]!==S||e[22]!==z?(F=n.jsxs(ie,{gap:"xs",align:"center",children:[z,S]}),e[21]=S,e[22]=z,e[23]=F):F=e[23];let O;e[24]!==g?(O=n.jsx(wl,{loading:g,value:"",onChange:I}),e[24]=g,e[25]=O):O=e[25];let Y;e[26]!==V||e[27]!==c?(Y=V?"":c("deployment.accessToken.EndpointNotIssuedYet"),e[26]=V,e[27]=c,e[28]=Y):Y=e[28];let X;e[29]===Symbol.for("react.memo_cache_sentinel")?(X=n.jsx(El,{}),e[29]=X):X=e[29];let ne;e[30]!==D?(ne=()=>D(!0),e[30]=D,e[31]=ne):ne=e[31];let N;e[32]!==c?(N=c("deployment.accessToken.Create"),e[32]=c,e[33]=N):N=e[33];let j;e[34]!==B||e[35]!==ne||e[36]!==N?(j=n.jsx(pl,{type:"primary",icon:X,disabled:B,onClick:ne,children:N}),e[34]=B,e[35]=ne,e[36]=N,e[37]=j):j=e[37];let w;e[38]!==Y||e[39]!==j?(w=n.jsx(cl,{title:Y,children:j}),e[38]=Y,e[39]=j,e[40]=w):w=e[40];let q;e[41]!==O||e[42]!==w?(q=n.jsxs(ie,{gap:"xs",align:"center",children:[O,w]}),e[41]=O,e[42]=w,e[43]=q):q=e[43];let W;e[44]===Symbol.for("react.memo_cache_sentinel")?(W={body:{paddingTop:0}},e[44]=W):W=e[44];let Z;e[45]===Symbol.for("react.memo_cache_sentinel")?(Z=n.jsx(xl,{active:!0}),e[45]=Z):Z=e[45];let ee;e[46]!==b||e[47]!==a||e[48]!==L||e[49]!==g?(ee=n.jsx(_.Suspense,{fallback:Z,children:n.jsx(Bi,{deploymentId:a,fetchKey:b,isPendingRefetch:g,isDeleteDisabled:L,onAfterDelete:I})}),e[46]=b,e[47]=a,e[48]=L,e[49]=g,e[50]=ee):ee=e[50];let G;e[51]!==i||e[52]!==F||e[53]!==q||e[54]!==ee?(G=n.jsx(ln,{ref:i,title:F,extra:q,styles:W,children:ee}),e[51]=i,e[52]=F,e[53]=q,e[54]=ee,e[55]=G):G=e[55];let Q;e[56]!==A||e[57]!==R.id||e[58]!==v||e[59]!==h||e[60]!==d||e[61]!==D||e[62]!==c?(Q=je=>{D(!1),je&&A({input:{modelDeploymentId:Xe(R.id),expiresAt:je.expiresAt??new Date("2099-12-31").toISOString()}}).then(fe=>{var ke;const Ie=(ke=fe.createAccessToken)==null?void 0:ke.accessToken;Ie&&H({token:Ie.token,expiresAt:Ie.expiresAt??null}),h.success({key:"access-token-created",content:c("deployment.accessToken.Created")}),I(),d==null||d()}).catch(fe=>{const Ie=Array.isArray(fe)?fe:[fe];for(const ke of Ie)h.error((ke==null?void 0:ke.message)||c("dialog.ErrorOccurred"));v.error(fe)})},e[56]=A,e[57]=R.id,e[58]=v,e[59]=h,e[60]=d,e[61]=D,e[62]=c,e[63]=Q):Q=e[63];let Se;e[64]!==x||e[65]!==Q?(Se=n.jsx(Sl,{children:n.jsx(Hi,{open:x,confirmLoading:!1,onRequestClose:Q})}),e[64]=x,e[65]=Q,e[66]=Se):Se=e[66];const ce=E!==null;let ae;e[67]!==c?(ae=c("deployment.accessToken.Token"),e[67]=c,e[68]=ae):ae=e[68];let Me;e[69]===Symbol.for("react.memo_cache_sentinel")?(Me=()=>H(null),e[69]=Me):Me=e[69];let Re;e[70]!==c?(Re=c("deployment.accessToken.Created"),e[70]=c,e[71]=Re):Re=e[71];let ve;e[72]!==Re?(ve=n.jsx(el.Text,{children:Re}),e[72]=Re,e[73]=ve):ve=e[73];let me;e[74]!==E?(me=E?n.jsx(Ol,{copyable:{text:E.token},ellipsis:!0,code:!0,children:E.token}):null,e[74]=E,e[75]=me):me=e[75];let pe;e[76]!==E||e[77]!==c?(pe=E!=null&&E.expiresAt?n.jsx(el.Text,{type:"secondary",children:`${c("deployment.accessToken.Expiration")}: ${ml(E.expiresAt).format("ll LT")}`}):n.jsx(el.Text,{type:"secondary",children:c("deployment.accessToken.NoExpiration")}),e[76]=E,e[77]=c,e[78]=pe):pe=e[78];let ge;e[79]!==ve||e[80]!==me||e[81]!==pe?(ge=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[ve,me,pe]}),e[79]=ve,e[80]=me,e[81]=pe,e[82]=ge):ge=e[82];let he;e[83]!==ce||e[84]!==ae||e[85]!==ge?(he=n.jsx(Sl,{children:n.jsx(Gl,{open:ce,destroyOnHidden:!0,title:ae,onCancel:Me,footer:null,width:520,children:ge})}),e[83]=ce,e[84]=ae,e[85]=ge,e[86]=he):he=e[86];let Te;return e[87]!==G||e[88]!==Se||e[89]!==he?(Te=n.jsxs(n.Fragment,{children:[G,Se,he]}),e[87]=G,e[88]=Se,e[89]=he,e[90]=Te):Te=e[90],Te},Bi=l=>{"use memo";var w,q,W,Z;const e=ll.c(70),{deploymentId:i,fetchKey:s,isPendingRefetch:t,isDeleteDisabled:a,onAfterDelete:d}=l,{t:r}=tl(),{message:o}=$l.useApp(),{logger:u}=Wl(),[m,c]=_.useState(null);let k;e[0]===Symbol.for("react.memo_cache_sentinel")?(k=It,e[0]=k):k=e[0];let h;e[1]!==i?(h={deploymentId:i},e[1]=i,e[2]=h):h=e[2];let v;e[3]!==s?(v={fetchKey:s,fetchPolicy:"network-only"},e[3]=s,e[4]=v):v=e[4];const{deployment:g}=Ve.useLazyLoadQuery(k,h,v);let y;e[5]!==((w=g==null?void 0:g.accessTokens)==null?void 0:w.edges)?(y=zl((W=(q=g==null?void 0:g.accessTokens)==null?void 0:q.edges)==null?void 0:W.map(qi)),e[5]=(Z=g==null?void 0:g.accessTokens)==null?void 0:Z.edges,e[6]=y):y=e[6];const p=y;let P;e[7]===Symbol.for("react.memo_cache_sentinel")?(P=Kt,e[7]=P):P=e[7];const[T,x]=Ve.useMutation(P);let D;e[8]===Symbol.for("react.memo_cache_sentinel")?(D={x:"max-content"},e[8]=D):D=e[8];const E=t||x;let H;e[9]!==r?(H=r("deployment.accessToken.Token"),e[9]=r,e[10]=H):H=e[10];let b;e[11]!==a||e[12]!==r?(b=(ee,G)=>G?n.jsx(jn,{title:n.jsx(Ol,{copyable:{text:G.token},ellipsis:!0,style:{maxWidth:200},children:G.token}),showActions:"always",actions:[{key:"delete",title:r("deployment.accessToken.Delete"),icon:n.jsx(Ln,{}),type:"danger",disabled:a,onClick:()=>c({id:G.id,token:G.token??""})}]}):"-",e[11]=a,e[12]=r,e[13]=b):b=e[13];let K;e[14]!==H||e[15]!==b?(K={key:"token",title:H,dataIndex:"token",render:b},e[14]=H,e[15]=b,e[16]=K):K=e[16];let R;e[17]!==r?(R=r("deployment.CreatedAt"),e[17]=r,e[18]=R):R=e[18];let C;e[19]!==R?(C={key:"createdAt",title:R,dataIndex:"createdAt",render:zi},e[19]=R,e[20]=C):C=e[20];let A;e[21]!==r?(A=r("deployment.accessToken.Expiration"),e[21]=r,e[22]=A):A=e[22];let M;e[23]!==r?(M=(ee,G)=>G!=null&&G.expiresAt?ml(G.expiresAt).format("ll LT"):r("deployment.accessToken.NoExpiration"),e[23]=r,e[24]=M):M=e[24];let I;e[25]!==A||e[26]!==M?(I={key:"expiresAt",title:A,dataIndex:"expiresAt",render:M},e[25]=A,e[26]=M,e[27]=I):I=e[27];let V;e[28]!==K||e[29]!==C||e[30]!==I?(V=[K,C,I],e[28]=K,e[29]=C,e[30]=I,e[31]=V):V=e[31];let L;e[32]!==p||e[33]!==V||e[34]!==E?(L=n.jsx(Ul,{scroll:D,rowKey:"id",loading:E,dataSource:p,pagination:!1,resizable:!0,columns:V}),e[32]=p,e[33]=V,e[34]=E,e[35]=L):L=e[35];const B=!!m;let z;e[36]!==r?(z=r("deployment.accessToken.Delete"),e[36]=r,e[37]=z):z=e[37];let U;e[38]!==r?(U=r("deployment.AccessToken"),e[38]=r,e[39]=U):U=e[39];let $;e[40]!==m?($=m?[{key:m.id,label:m.id}]:[],e[40]=m,e[41]=$):$=e[41];let S;e[42]!==r?(S=r("data.folders.DeleteForeverConfirmText"),e[42]=r,e[43]=S):S=e[43];let F;e[44]!==r?(F=r("data.folders.DeleteForeverConfirmText"),e[44]=r,e[45]=F):F=e[45];let O;e[46]!==F?(O={placeholder:F},e[46]=F,e[47]=O):O=e[47];let Y;e[48]!==x?(Y={loading:x},e[48]=x,e[49]=Y):Y=e[49];let X;e[50]!==T||e[51]!==m||e[52]!==u||e[53]!==o||e[54]!==d||e[55]!==r?(X=()=>{m&&T({variables:{input:{id:Xe(m.id)??m.id}},onCompleted:(ee,G)=>{var Q;if(G&&G.length>0){u.error(G[0]),o.error(((Q=G[0])==null?void 0:Q.message)??r("dialog.ErrorOccurred"));return}o.success(r("deployment.accessToken.Deleted")),c(null),d()},onError:ee=>{u.error(ee),o.error(ee.message??r("dialog.ErrorOccurred"))}})},e[50]=T,e[51]=m,e[52]=u,e[53]=o,e[54]=d,e[55]=r,e[56]=X):X=e[56];let ne;e[57]===Symbol.for("react.memo_cache_sentinel")?(ne=()=>c(null),e[57]=ne):ne=e[57];let N;e[58]!==B||e[59]!==z||e[60]!==U||e[61]!==$||e[62]!==S||e[63]!==O||e[64]!==Y||e[65]!==X?(N=n.jsx(Pn,{open:B,title:z,target:U,items:$,confirmText:S,requireConfirmInput:!0,inputProps:O,okButtonProps:Y,onOk:X,onCancel:ne}),e[58]=B,e[59]=z,e[60]=U,e[61]=$,e[62]=S,e[63]=O,e[64]=Y,e[65]=X,e[66]=N):N=e[66];let j;return e[67]!==L||e[68]!==N?(j=n.jsxs(n.Fragment,{children:[L,N]}),e[67]=L,e[68]=N,e[69]=j):j=e[69],j},Hi=l=>{"use memo";const e=ll.c(64),{open:i,confirmLoading:s,onRequestClose:t}=l,{t:a}=tl(),[d]=ue.useForm(),r=ue.useWatch("expiryOption",d)??7;let o;e[0]!==d||e[1]!==t?(o=()=>{d.validateFields().then($=>{let S;$.expiryOption==="none"?S=null:$.expiryOption==="custom"?S=$.datetime.toISOString():S=ml().add($.expiryOption,"day").toISOString(),t({expiresAt:S})}).catch(Ui)},e[0]=d,e[1]=t,e[2]=o):o=e[2];const u=o;let m;e[3]!==a?(m=a("general.Days",{num:7,defaultValue:"7 days"}),e[3]=a,e[4]=m):m=e[4];let c;e[5]!==m?(c={value:7,label:m},e[5]=m,e[6]=c):c=e[6];let k;e[7]!==a?(k=a("general.Days",{num:30,defaultValue:"30 days"}),e[7]=a,e[8]=k):k=e[8];let h;e[9]!==k?(h={value:30,label:k},e[9]=k,e[10]=h):h=e[10];let v;e[11]!==a?(v=a("general.Days",{num:90,defaultValue:"90 days"}),e[11]=a,e[12]=v):v=e[12];let g;e[13]!==v?(g={value:90,label:v},e[13]=v,e[14]=g):g=e[14];let y;e[15]!==a?(y=a("deployment.accessToken.CustomExpiration"),e[15]=a,e[16]=y):y=e[16];let p;e[17]!==y?(p={value:"custom",label:y},e[17]=y,e[18]=p):p=e[18];let P;e[19]!==a?(P=a("deployment.accessToken.NoExpiration"),e[19]=a,e[20]=P):P=e[20];let T;e[21]!==P?(T={value:"none",label:P},e[21]=P,e[22]=T):T=e[22];let x;e[23]!==T||e[24]!==c||e[25]!==h||e[26]!==g||e[27]!==p?(x=[c,h,g,p,T],e[23]=T,e[24]=c,e[25]=h,e[26]=g,e[27]=p,e[28]=x):x=e[28];const D=x;let E;e[29]!==a?(E=a("deployment.accessToken.Create"),e[29]=a,e[30]=E):E=e[30];let H;e[31]!==a?(H=a("deployment.accessToken.Create"),e[31]=a,e[32]=H):H=e[32];let b;e[33]!==t?(b=()=>t(),e[33]=t,e[34]=b):b=e[34];let K,R;e[35]===Symbol.for("react.memo_cache_sentinel")?(K={expiryOption:7,datetime:ml().add(7,"day")},R=["onChange","onBlur"],e[35]=K,e[36]=R):(K=e[35],R=e[36]);let C;e[37]!==a?(C=a("deployment.accessToken.Expiration"),e[37]=a,e[38]=C):C=e[38];let A;e[39]===Symbol.for("react.memo_cache_sentinel")?(A=[{required:!0}],e[39]=A):A=e[39];let M;e[40]===Symbol.for("react.memo_cache_sentinel")?(M={width:200},e[40]=M):M=e[40];let I;e[41]!==d?(I=$=>{typeof $=="number"&&d.setFieldValue("datetime",ml().add($,"day"))},e[41]=d,e[42]=I):I=e[42];let V;e[43]!==D||e[44]!==I?(V=n.jsx(dn,{style:M,options:D,onChange:I}),e[43]=D,e[44]=I,e[45]=V):V=e[45];let L;e[46]!==C||e[47]!==V?(L=n.jsx(ue.Item,{name:"expiryOption",label:C,rules:A,children:V}),e[46]=C,e[47]=V,e[48]=L):L=e[48];let B;e[49]!==r||e[50]!==a?(B=r==="custom"&&n.jsx(ue.Item,{name:"datetime",label:a("deployment.accessToken.CustomExpiration"),rules:[{type:"object",required:!0},()=>({validator($,S){return S&&ml(S).isAfter(ml())?Promise.resolve():Promise.reject(new Error(a("dialog.ErrorOccurred")))}})],children:n.jsx(ha,{showTime:!0,format:"YYYY-MM-DD HH:mm:ss",style:{width:"100%"}})}),e[49]=r,e[50]=a,e[51]=B):B=e[51];let z;e[52]!==d||e[53]!==L||e[54]!==B?(z=n.jsxs(ue,{form:d,layout:"vertical",initialValues:K,validateTrigger:R,children:[L,B]}),e[52]=d,e[53]=L,e[54]=B,e[55]=z):z=e[55];let U;return e[56]!==s||e[57]!==u||e[58]!==i||e[59]!==E||e[60]!==H||e[61]!==b||e[62]!==z?(U=n.jsx(Gl,{open:i,destroyOnHidden:!0,centered:!0,width:420,title:E,okText:H,confirmLoading:s,onOk:u,onCancel:b,children:z}),e[56]=s,e[57]=u,e[58]=i,e[59]=E,e[60]=H,e[61]=b,e[62]=z,e[63]=U):U=e[63],U};function Qi(l){return l+1}function qi(l){return l==null?void 0:l.node}function zi(l,e){return e!=null&&e.createdAt?ml(e.createdAt).format("ll LT"):"-"}function Ui(){}const Ct=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"c7f86a18b204736e35e7935bb3913511",id:null,metadata:{},name:"DeploymentAddRevisionModalImageNameQuery",operationKind:"query",text:`query DeploymentAddRevisionModalImageNameQuery(
  $id: ID!
) {
  imageV2(id: $id) {
    identity {
      canonicalName
    }
    id
  }
}
`}}}();Ct.hash="e0f63d644538b757a6d30c78d1771156";const Mt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},t={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},d=[i,s],r={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},u={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},m={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},k=[c,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],h={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:k,storageKey:null}],storageKey:null}],storageKey:null},v={alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:k,storageKey:null}],storageKey:null}],storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},p={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},P={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[g,y,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},p],storageKey:null},T={alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[g,y,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},p],storageKey:null},x={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},D={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},E=[i,r,o,u,m,h,v,P,T,x,D];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,s,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:d,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:d,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[i,r,o,u,m,h,v,P,T,x,D,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,t,a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:E,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:E,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"2a37634f4db82b455442aaadbeddbf94",id:null,metadata:{},name:"DeploymentAddRevisionModalAddMutation",operationKind:"mutation",text:`mutation DeploymentAddRevisionModalAddMutation(
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
`}}}();Mt.hash="889773e313c63748043b8294cd2bb0b0";const jt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},i=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:i},params:{cacheID:"6728695a02d457f55b4cd4d3323823d8",id:null,metadata:{},name:"DeploymentAddRevisionModalSelectedPresetQuery",operationKind:"query",text:`query DeploymentAddRevisionModalSelectedPresetQuery(
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
`}}}();jt.hash="e9d60ac2d9540dae9c821fe3abd4b65e";const Lt=function(){var l=[{alias:null,args:[{kind:"Literal",name:"first",value:1},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"RANK"}]}],concreteType:"DeploymentRevisionPresetConnection",kind:"LinkedField",name:"deploymentRevisionPresets",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:'deploymentRevisionPresets(first:1,orderBy:[{"direction":"ASC","field":"RANK"}])'}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetCountQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAddRevisionModalPresetCountQuery",selections:l},params:{cacheID:"edaa5efa78debd74168a24185822d633",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetCountQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetCountQuery {
  deploymentRevisionPresets(orderBy: [{field: RANK, direction: "ASC"}], first: 1) {
    count
  }
}
`}}}();Lt.hash="4461df1967b1117642d3190b36d5cb33";const Pt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e=[l,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],i={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_revisionSource",selections:[{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:e,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[i,s],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[l],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:e,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[i,s,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelRevision",abstractKey:null}}();Pt.hash="d5d51918866d0b82f8843dc8acb580ee";const Nt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModal_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Nt.hash="614548b7fde80b4972dfb192b893b832";const Vt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentPresetDetailModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[i,s,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,s],storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startupCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"bootstrapScript",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[s,t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetDeploymentDefaults",kind:"LinkedField",name:"deploymentDefaults",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"replicaCount",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"revisionHistoryLimit",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentStrategy",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetValueEntry",kind:"LinkedField",name:"presetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},t],storageKey:null}],storageKey:null}]},params:{cacheID:"218b82beeca87da0b64539597ed3fe1b",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetDetailQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetDetailQuery(
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
  presetValues {
    presetId
    value
  }
}
`}}}();Vt.hash="8f60ae6bcf0fa60919e80838391f66f9";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */function _t(l){const e=pt(l.trim()),i={},s=[];let t=0;for(;t<e.length;){const a=e[t];if(a.startsWith("--")&&a.includes("=")){const d=a.indexOf("="),r=a.slice(0,d),o=a.slice(d+1);i[r]=o,t++;continue}if(a.startsWith("--no-")){const d="--"+a.slice(5);i[d]="false",t++;continue}if(a.startsWith("--")){const d=t+1<e.length?e[t+1]:void 0;d!==void 0&&!d.startsWith("-")?(i[a]=d,t+=2):(i[a]="true",t++);continue}s.push(a),t++}return{knownArgs:i,unknownTokens:s}}function Et(l,e=[]){const i=[];for(const[s,t]of Object.entries(l))if(t==="true")i.push(s);else{if(t==="false")continue;t.includes(" ")||t.includes("	")?i.push(`${s} "${t}"`):i.push(`${s} ${t}`)}return e.length>0&&i.push(e.join(" ")),i.join(" ")}function Wi(l,e,i={}){const s=_t(e),t={...l,...s.knownArgs},a={};for(const[d,r]of Object.entries(t))i[d]!==void 0&&i[d]===r||(a[d]=r);return Et(a,s.unknownTokens)}function Ot(l,e){const{knownArgs:i,unknownTokens:s}=_t(l),t={},a={};for(const[r,o]of Object.entries(i))e.has(r)?t[r]=o:a[r]=o;const d=Et(a,s);return{mappedArgs:t,unmappedText:d}}const $t=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"filter"},{defaultValue:null,kind:"LocalArgument",name:"orderBy"}],e=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Literal",name:"first",value:100},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},r={alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetTarget",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"valueType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"defaultValue",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"min",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"max",storageKey:null},m={alias:null,args:null,concreteType:"UIOption",kind:"LinkedField",name:"uiOption",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"uiType",storageKey:null},{alias:null,args:null,concreteType:"SliderOption",kind:"LinkedField",name:"slider",plural:!1,selections:[o,u,{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"NumberOption",kind:"LinkedField",name:"number",plural:!1,selections:[o,u],storageKey:null},{alias:null,args:null,concreteType:"ChoiceOption",kind:"LinkedField",name:"choices",plural:!1,selections:[{alias:null,args:null,concreteType:"ChoiceItem",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"label",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"TextOption",kind:"LinkedField",name:"text",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"placeholder",storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"useRuntimeParameterSchemaPresetsQuery",selections:[{kind:"CatchField",field:{alias:"runtimeVariantPresetsResult",args:e,concreteType:"RuntimeVariantPresetConnection",kind:"LinkedField",name:"runtimeVariantPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPresetEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"node",plural:!1,selections:[i,s,t,a,d,r,m],storageKey:null}],storageKey:null}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"useRuntimeParameterSchemaPresetsQuery",selections:[{alias:"runtimeVariantPresetsResult",args:e,concreteType:"RuntimeVariantPresetConnection",kind:"LinkedField",name:"runtimeVariantPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPresetEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"node",plural:!1,selections:[i,s,t,a,d,r,m,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"9ec67e7389f1f7cec0f197e6ff23ec91",id:null,metadata:{},name:"useRuntimeParameterSchemaPresetsQuery",operationKind:"query",text:`query useRuntimeParameterSchemaPresetsQuery(
  $filter: RuntimeVariantPresetFilter
  $orderBy: [RuntimeVariantPresetOrderBy!]
) {
  runtimeVariantPresetsResult: runtimeVariantPresets(filter: $filter, orderBy: $orderBy, first: 100) {
    edges {
      node {
        name
        description
        rank
        category
        displayName
        targetSpec {
          presetTarget
          valueType
          defaultValue
          key
        }
        uiOption {
          uiType
          slider {
            min
            max
            step
          }
          number {
            min
            max
          }
          choices {
            items {
              value
              label
            }
          }
          text {
            placeholder
          }
        }
        id
      }
    }
  }
}
`}}}();$t.hash="ca5ee1b8f0a7378db0a58b62f8709a68";const wt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"filter"}],e={alias:"runtimeVariantsResult",args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Literal",name:"first",value:1}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"useRuntimeParameterSchemaVariantsQuery",selections:[{kind:"CatchField",field:e,to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"useRuntimeParameterSchemaVariantsQuery",selections:[e]},params:{cacheID:"c682513f5e9e13cb4231c771873116d0",id:null,metadata:{},name:"useRuntimeParameterSchemaVariantsQuery",operationKind:"query",text:`query useRuntimeParameterSchemaVariantsQuery(
  $filter: RuntimeVariantFilter
) {
  runtimeVariantsResult: runtimeVariants(filter: $filter, first: 1) {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();wt.hash="4a430bb72586e76dae1f300fdd57f51a";function Gi(l){var a,d,r,o,u;const e=Ve.useLazyLoadQuery(wt,{filter:l?{name:{equals:l}}:{name:{equals:"__none__"}}},{fetchPolicy:"store-or-network"}),i=((a=e.runtimeVariantsResult)==null?void 0:a.ok)===!0?((u=(o=(r=(d=e.runtimeVariantsResult.value)==null?void 0:d.edges)==null?void 0:r[0])==null?void 0:o.node)==null?void 0:u.id)??null:null,s=i?Xe(i):null,t=Ve.useLazyLoadQuery($t,{filter:s?{runtimeVariantId:{equals:s}}:{name:{equals:"__none__"}},orderBy:[{field:"RANK",direction:"ASC"}]},{fetchPolicy:"store-or-network"});return _.useMemo(()=>{var h,v;if(!l||!s)return null;const m=((h=t.runtimeVariantPresetsResult)==null?void 0:h.ok)===!0?((v=t.runtimeVariantPresetsResult.value)==null?void 0:v.edges)??[]:[];if(m.length===0)return null;const c=m.map(g=>g==null?void 0:g.node).filter(Boolean).map(g=>{var y,p,P,T,x;return{name:g.name,description:g.description??null,rank:g.rank,category:g.category??null,displayName:g.displayName??null,presetTarget:g.targetSpec.presetTarget,valueType:g.targetSpec.valueType,defaultValue:g.targetSpec.defaultValue??null,key:g.targetSpec.key,uiType:((y=g.uiOption)==null?void 0:y.uiType)??null,slider:(p=g.uiOption)!=null&&p.slider?{min:g.uiOption.slider.min,max:g.uiOption.slider.max,step:g.uiOption.slider.step}:null,number:(P=g.uiOption)!=null&&P.number?{min:g.uiOption.number.min??null,max:g.uiOption.number.max??null}:null,choices:(T=g.uiOption)!=null&&T.choices?{items:g.uiOption.choices.items.map(D=>({value:D.value,label:D.label}))}:null,text:(x=g.uiOption)!=null&&x.text?{placeholder:g.uiOption.text.placeholder??null}:null}}),k=new Map;for(const g of c){const y=g.category??"general",p=k.get(y)??[];p.push(g),k.set(y,p)}return Array.from(k.entries()).map(([g,y])=>({category:g,params:y}))},[l,s,t])}function Rn(l){const e={};for(const i of l)for(const s of i.params)s.defaultValue!==null&&(e[s.key]=s.defaultValue);return e}function Bt(l){const e=new Set;for(const i of l)for(const s of i.params)s.presetTarget==="ARGS"&&e.add(s.key);return e}function Yi(l){const e=new Set;for(const i of l)for(const s of i.params)s.presetTarget==="ENV"&&e.add(s.key);return e}function Tn(l){return`${l.toUpperCase()}_EXTRA_ARGS`}const Xi=["vllm","sglang"];function Ji(){return Xi.map(Tn)}function Zi(l){return l.flatMap(e=>e.params)}function es(l){return l.split("_").map(e=>e.charAt(0).toUpperCase()+e.slice(1)).join(" ")}const ls=l=>{"use memo";const e=ll.c(114),{runtimeVariant:i,onChange:s,onTouchedKeysChange:t,onGroupsLoaded:a,initialExtraArgs:d,initialEnvVars:r}=l,{t:o}=tl(),{token:u}=Il.useToken(),m=Gi(i);let c;e[0]!==m||e[1]!==a?(c=()=>{a==null||a(m)},e[0]=m,e[1]=a,e[2]=c):c=e[2];const k=_.useEffectEvent(c);let h;e[3]!==a?(h=()=>{a==null||a(null)},e[3]=a,e[4]=h):h=e[4];const v=_.useEffectEvent(h);let g;e[5]!==k||e[6]!==v?(g=()=>(k(),()=>{v()}),e[5]=k,e[6]=v,e[7]=g):g=e[7];let y;e[8]!==m?(y=[m],e[8]=m,e[9]=y):y=e[9],_.useEffect(g,y);let p;e[10]===Symbol.for("react.memo_cache_sentinel")?(p={},e[10]=p):p=e[10];const[P,T]=_.useState(p),x=P;let D;e[11]===Symbol.for("react.memo_cache_sentinel")?(D=new Set,e[11]=D):D=e[11];const[E,H]=_.useState(D),[b,K]=_.useState("");let R;e[12]!==s?(R=Q=>{T(Q),s==null||s(Q)},e[12]=s,e[13]=R):R=e[13];const C=R;let A;e[14]!==m||e[15]!==r||e[16]!==d||e[17]!==t||e[18]!==C?(A=()=>{if(!m)return;const Q=Rn(m);if(!!d||!!r){let ce={};const ae={};if(d){const ve=Bt(m),{mappedArgs:me}=Ot(d,ve);ce=me}if(r){const ve=Yi(m);for(const me of ve)r[me]!==void 0&&(ae[me]=r[me])}const Me={...ce,...ae};C({...Q,...Me});const Re=new Set(Object.keys(Me));H(Re),t==null||t(Re)}else C(Q),H(new Set),t==null||t(new Set)},e[14]=m,e[15]=r,e[16]=d,e[17]=t,e[18]=C,e[19]=A):A=e[19];const M=_.useEffectEvent(A);let I;e[20]!==M?(I=()=>{M()},e[20]=M,e[21]=I):I=e[21];let V;e[22]!==m||e[23]!==i?(V=[i,m],e[22]=m,e[23]=i,e[24]=V):V=e[24],_.useEffect(I,V);let L;e[25]!==s||e[26]!==t?(L=(Q,Se)=>{T(ce=>{const ae={...ce,[Q]:Se};return queueMicrotask(()=>s==null?void 0:s(ae)),ae}),H(ce=>{if(ce.has(Q))return ce;const ae=new Set(ce);return ae.add(Q),queueMicrotask(()=>t==null?void 0:t(ae)),ae})},e[25]=s,e[26]=t,e[27]=L):L=e[27];const B=L;let z;e[28]!==m||e[29]!==t||e[30]!==C?(z=()=>{if(!m)return;const Q=Rn(m);C(Q),H(new Set),t==null||t(new Set)},e[28]=m,e[29]=t,e[30]=C,e[31]=z):z=e[31];const U=z;if(!m)return null;let $,S,F,O,Y,X,ne,N,j,w,q;if(e[32]!==b||e[33]!==m||e[34]!==B||e[35]!==U||e[36]!==o||e[37]!==u.colorTextSecondary||e[38]!==u.marginSM||e[39]!==E||e[40]!==x){const Q=m.map(as),Se=Q.map(is),ce=Q.includes(b)?b:Q[0]??"";S=tt,w="small",e[52]===Symbol.for("react.memo_cache_sentinel")?(q=["runtime-params"],e[52]=q):q=e[52],N="runtime-params";let ae;e[53]===Symbol.for("react.memo_cache_sentinel")?(ae={flex:1},e[53]=ae):ae=e[53];let Me;e[54]!==o?(Me=o("modelService.RuntimeParamTitle"),e[54]=o,e[55]=Me):Me=e[55];let Re;e[56]!==u.colorTextSecondary?(Re={color:u.colorTextSecondary},e[56]=u.colorTextSecondary,e[57]=Re):Re=e[57];let ve;e[58]!==o?(ve=o("general.Optional"),e[58]=o,e[59]=ve):ve=e[59];let me;e[60]!==Re||e[61]!==ve?(me=n.jsxs("span",{style:Re,children:["(",ve,")"]}),e[60]=Re,e[61]=ve,e[62]=me):me=e[62];let pe;e[63]!==Me||e[64]!==me?(pe=n.jsxs("span",{children:[Me," ",me]}),e[63]=Me,e[64]=me,e[65]=pe):pe=e[65];let ge;e[66]!==o?(ge=o("button.Reset"),e[66]=o,e[67]=ge):ge=e[67];let he;e[68]===Symbol.for("react.memo_cache_sentinel")?(he=n.jsx(ri,{}),e[68]=he):he=e[68];let Te;e[69]!==o?(Te=o("button.Reset"),e[69]=o,e[70]=Te):Te=e[70];let Fe;e[71]!==U?(Fe=de=>{de.stopPropagation(),U()},e[71]=U,e[72]=Fe):Fe=e[72];const je=E.size===0;let fe;e[73]!==Te||e[74]!==Fe||e[75]!==je?(fe=n.jsx(pl,{type:"link",size:"small",icon:he,"aria-label":Te,onClick:Fe,disabled:je}),e[73]=Te,e[74]=Fe,e[75]=je,e[76]=fe):fe=e[76];let Ie;e[77]!==ge||e[78]!==fe?(Ie=n.jsx(cl,{title:ge,children:fe}),e[77]=ge,e[78]=fe,e[79]=Ie):Ie=e[79],e[80]!==pe||e[81]!==Ie?(j=n.jsxs(ie,{justify:"between",align:"center",style:ae,children:[pe,Ie]}),e[80]=pe,e[81]=Ie,e[82]=j):j=e[82];let ke;e[83]!==o?(ke=o("modelService.RuntimeParamUnchangedHint"),e[83]=o,e[84]=ke):ke=e[84];let Ne;e[85]!==u.marginSM?(Ne={marginBottom:u.marginSM},e[85]=u.marginSM,e[86]=Ne):Ne=e[86],e[87]!==ke||e[88]!==Ne?(ne=n.jsx(Ll,{type:"warning",showIcon:!0,title:ke,style:Ne}),e[87]=ke,e[88]=Ne,e[89]=ne):ne=e[89],$=va,F="small",O=ce,e[90]===Symbol.for("react.memo_cache_sentinel")?(Y=de=>K(de),e[90]=Y):Y=e[90];let xe;e[91]!==m||e[92]!==B||e[93]!==E||e[94]!==x?(xe=de=>{const Be=m.find(f=>f.category===de.key);return{key:de.key,label:de.label,children:Be?n.jsx(ns,{group:Be,values:x,touchedKeys:E,onParamChange:B}):null}},e[91]=m,e[92]=B,e[93]=E,e[94]=x,e[95]=xe):xe=e[95],X=Se.map(xe),e[32]=b,e[33]=m,e[34]=B,e[35]=U,e[36]=o,e[37]=u.colorTextSecondary,e[38]=u.marginSM,e[39]=E,e[40]=x,e[41]=$,e[42]=S,e[43]=F,e[44]=O,e[45]=Y,e[46]=X,e[47]=ne,e[48]=N,e[49]=j,e[50]=w,e[51]=q}else $=e[41],S=e[42],F=e[43],O=e[44],Y=e[45],X=e[46],ne=e[47],N=e[48],j=e[49],w=e[50],q=e[51];let W;e[96]!==$||e[97]!==F||e[98]!==O||e[99]!==Y||e[100]!==X?(W=n.jsx($,{size:F,activeKey:O,onChange:Y,items:X}),e[96]=$,e[97]=F,e[98]=O,e[99]=Y,e[100]=X,e[101]=W):W=e[101];let Z;e[102]!==ne||e[103]!==W?(Z=n.jsxs(n.Fragment,{children:[ne,W]}),e[102]=ne,e[103]=W,e[104]=Z):Z=e[104];let ee;e[105]!==N||e[106]!==j||e[107]!==Z?(ee=[{key:N,label:j,children:Z}],e[105]=N,e[106]=j,e[107]=Z,e[108]=ee):ee=e[108];let G;return e[109]!==S||e[110]!==w||e[111]!==q||e[112]!==ee?(G=n.jsx(S,{size:w,defaultActiveKey:q,items:ee}),e[109]=S,e[110]=w,e[111]=q,e[112]=ee,e[113]=G):G=e[113],G},ns=l=>{"use memo";const e=ll.c(11),{group:i,values:s,touchedKeys:t,onParamChange:a}=l;let d;if(e[0]!==i.params||e[1]!==a||e[2]!==t||e[3]!==s){let o;e[5]!==a||e[6]!==t||e[7]!==s?(o=u=>n.jsx(ts,{param:u,value:s[u.key]??u.defaultValue??"",touched:t.has(u.key),onChange:m=>a(u.key,m)},u.key),e[5]=a,e[6]=t,e[7]=s,e[8]=o):o=e[8],d=i.params.map(o),e[0]=i.params,e[1]=a,e[2]=t,e[3]=s,e[4]=d}else d=e[4];let r;return e[9]!==d?(r=n.jsx(ie,{direction:"column",gap:"xxs",align:"stretch",children:d}),e[9]=d,e[10]=r):r=e[10],r},ts=l=>{"use memo";var v,g,y,p,P,T,x,D,E,H;const e=ll.c(91),{param:i,value:s,touched:t,onChange:a}=l,{t:d}=tl(),{token:r}=Il.useToken(),o=i.displayName??i.name,u=i.description??void 0;let m;e[0]!==r.marginXS?(m={marginBottom:r.marginXS},e[0]=r.marginXS,e[1]=m):m=e[1];const c=m,k=t?void 0:.45;switch(i.uiType){case"slider":{const b=((v=i.slider)==null?void 0:v.min)??0,K=((g=i.slider)==null?void 0:g.max)??100,R=((y=i.slider)==null?void 0:y.step)??1,C=s?parseFloat(s):b;let A;e[2]!==a?(A=U=>a(String(U)),e[2]=a,e[3]=A):A=e[3];let M;e[4]!==k?(M={opacity:k,transition:"opacity 0.2s"},e[4]=k,e[5]=M):M=e[5];let I;e[6]!==r.colorTextSecondary?(I={color:r.colorTextSecondary},e[6]=r.colorTextSecondary,e[7]=I):I=e[7];let V;e[8]!==K||e[9]!==I?(V={style:I,label:K},e[8]=K,e[9]=I,e[10]=V):V=e[10];let L;e[11]!==K||e[12]!==b||e[13]!==V?(L={marks:{[b]:b,[K]:V}},e[11]=K,e[12]=b,e[13]=V,e[14]=L):L=e[14];let B;e[15]!==K||e[16]!==b||e[17]!==R||e[18]!==C||e[19]!==A||e[20]!==M||e[21]!==L?(B=n.jsx(Fa,{min:b,max:K,step:R,value:C,onChange:A,inputContainerMinWidth:190,style:M,sliderProps:L}),e[15]=K,e[16]=b,e[17]=R,e[18]=C,e[19]=A,e[20]=M,e[21]=L,e[22]=B):B=e[22];let z;return e[23]!==c||e[24]!==o||e[25]!==B||e[26]!==u?(z=n.jsx(ue.Item,{label:o,tooltip:u,style:c,required:!0,children:B}),e[23]=c,e[24]=o,e[25]=B,e[26]=u,e[27]=z):z=e[27],z}case"number_input":{const b=((p=i.number)==null?void 0:p.min)??void 0,K=((P=i.number)==null?void 0:P.max)??void 0,R=i.valueType==="INT",C=R?1:.1,A=s?R?parseInt(s,10):parseFloat(s):void 0;let M;e[28]!==a?(M=B=>{B!==null&&a(String(B))},e[28]=a,e[29]=M):M=e[29];let I;e[30]!==k?(I={width:"100%",opacity:k,transition:"opacity 0.2s"},e[30]=k,e[31]=I):I=e[31];let V;e[32]!==K||e[33]!==b||e[34]!==C||e[35]!==A||e[36]!==M||e[37]!==I?(V=n.jsx(yl,{min:b,max:K,step:C,value:A,onChange:M,style:I}),e[32]=K,e[33]=b,e[34]=C,e[35]=A,e[36]=M,e[37]=I,e[38]=V):V=e[38];let L;return e[39]!==c||e[40]!==o||e[41]!==V||e[42]!==u?(L=n.jsx(ue.Item,{label:o,tooltip:u,style:c,required:!0,children:V}),e[39]=c,e[40]=o,e[41]=V,e[42]=u,e[43]=L):L=e[43],L}case"select":{const b=s||void 0;let K;e[44]!==a?(K=I=>a(I??""),e[44]=a,e[45]=K):K=e[45];let R;e[46]!==k?(R={opacity:k,transition:"opacity 0.2s"},e[46]=k,e[47]=R):R=e[47];let C;e[48]!==((T=i.choices)==null?void 0:T.items)?(C=(x=i.choices)==null?void 0:x.items.map(ss),e[48]=(D=i.choices)==null?void 0:D.items,e[49]=C):C=e[49];let A;e[50]!==b||e[51]!==K||e[52]!==R||e[53]!==C?(A=n.jsx(dn,{value:b,allowClear:!0,onChange:K,style:R,options:C}),e[50]=b,e[51]=K,e[52]=R,e[53]=C,e[54]=A):A=e[54];let M;return e[55]!==c||e[56]!==o||e[57]!==A||e[58]!==u?(M=n.jsx(ue.Item,{label:o,tooltip:u,style:c,required:!0,children:A}),e[55]=c,e[56]=o,e[57]=A,e[58]=u,e[59]=M):M=e[59],M}case"checkbox":{const b=s==="true";let K;e[60]!==a?(K=I=>a(I.target.checked?"true":"false"),e[60]=a,e[61]=K):K=e[61];let R;e[62]!==k?(R={opacity:k,transition:"opacity 0.2s"},e[62]=k,e[63]=R):R=e[63];let C;e[64]!==d?(C=d("general.Enable"),e[64]=d,e[65]=C):C=e[65];let A;e[66]!==o||e[67]!==b||e[68]!==K||e[69]!==R||e[70]!==C?(A=n.jsx(at,{checked:b,onChange:K,"aria-label":o,style:R,children:C}),e[66]=o,e[67]=b,e[68]=K,e[69]=R,e[70]=C,e[71]=A):A=e[71];let M;return e[72]!==c||e[73]!==o||e[74]!==A||e[75]!==u?(M=n.jsx(ue.Item,{label:o,tooltip:u,style:c,required:!0,children:A}),e[72]=c,e[73]=o,e[74]=A,e[75]=u,e[76]=M):M=e[76],M}case"text_input":default:{const b=t?s:"";let K;e[77]!==a?(K=I=>a(I.target.value),e[77]=a,e[78]=K):K=e[78];const R=t?((H=i.text)==null?void 0:H.placeholder)??void 0:s||(((E=i.text)==null?void 0:E.placeholder)??void 0);let C;e[79]!==k?(C={opacity:k,transition:"opacity 0.2s"},e[79]=k,e[80]=C):C=e[80];let A;e[81]!==b||e[82]!==K||e[83]!==R||e[84]!==C?(A=n.jsx(Bl,{value:b,onChange:K,placeholder:R,style:C}),e[81]=b,e[82]=K,e[83]=R,e[84]=C,e[85]=A):A=e[85];let M;return e[86]!==c||e[87]!==o||e[88]!==A||e[89]!==u?(M=n.jsx(ue.Item,{label:o,tooltip:u,style:c,required:!0,children:A}),e[86]=c,e[87]=o,e[88]=A,e[89]=u,e[90]=M):M=e[90],M}}};function as(l){return l.category}function is(l){return{key:l,label:es(l)}}function ss(l){return{value:l.value,label:l.label}}const kn=({children:l})=>{const{token:e}=Il.useToken();return n.jsx(it,{titlePlacement:"left",children:n.jsx(el.Text,{type:"secondary",style:{fontSize:e.fontSizeSM},children:l})})},rs=l=>{"use memo";const e=ll.c(6),{presetId:i,onCancel:s}=l;let t;e[0]===Symbol.for("react.memo_cache_sentinel")?(t=Vt,e[0]=t):t=e[0];let a;e[1]!==i?(a={id:i},e[1]=i,e[2]=a):a=e[2];const d=Ve.useLazyLoadQuery(t,a);let r;return e[3]!==d.deploymentRevisionPreset||e[4]!==s?(r=n.jsx(ja,{open:!0,presetFrgmt:d.deploymentRevisionPreset,onCancel:s}),e[3]=d.deploymentRevisionPreset,e[4]=s,e[5]=r):r=e[5],r},Ht=({onRequestClose:l,deploymentFrgmt:e,sourceRevisionFrgmt:i,open:s,...t})=>{"use memo";var xe,de,Be;const{t:a}=tl(),{token:d}=Il.useToken(),{message:r}=$l.useApp(),o=Ve.useRelayEnvironment(),u=Ve.useFragment(Nt,e),m=Pt,c=Ve.useFragment(m,(u==null?void 0:u.currentRevision)??null),k=Ve.useFragment(m,i??null),{id:h}=Nn(),{logger:v}=Wl(),{open:g}=xa(),y=_.useRef(null),p=_.useRef(null),[P,T]=_.useState(!1),[x]=ue.useForm(),[D]=ue.useForm(),[E,H]=_.useState(!0),[b,K]=yn("deploymentRevisionCreationMode"),R=b??"preset",[C,A]=_.useState(!1),[M,I]=_.useState(!1),[V,L]=_.useState(!1),[B,z]=_.useState(null),[U,$]=_.useState(null),[S,F]=_.useState(null),[O,Y]=_.useState({}),X=_.useRef({}),ne=_.useRef(new Set),N=_.useRef(null),[j,w]=_.useState(""),[q,W]=_.useState(void 0),Z=_.useRef({}),[ee,G]=_.useState(void 0);_.useEffect(()=>{if(!s)return;let f=!1;return Ve.fetchQuery(o,Lt,{},{fetchPolicy:"store-or-network"}).toPromise().then(J=>{var le;f||G((((le=J==null?void 0:J.deploymentRevisionPresets)==null?void 0:le.count)??0)===0)}).catch(()=>{f||G(!1)}),()=>{f=!0}},[s,o]);const Q=(de=(xe=u==null?void 0:u.currentRevision)==null?void 0:xe.modelMountConfig)!=null&&de.vfolderId?Zl("VirtualFolderNode",u.currentRevision.modelMountConfig.vfolderId):void 0,Se=_.useRef(new Map),ce=async f=>{const J=Se.current.get(f);if(J)return J;const le=await Ve.fetchQuery(o,jt,{id:f},{fetchPolicy:"store-or-network"}).toPromise(),te=(le==null?void 0:le.deploymentRevisionPreset)??null;return te&&Se.current.set(f,te),te},[ae,Me]=Ve.useMutation(Mt),Re=async f=>{var He,oe,Ce,Pe,qe,ze,Qe,We,be;const J=f.resourceSlots??[],le=J.find(ye=>ye.slotName==="cpu"),te=J.find(ye=>ye.slotName==="mem"),re=J.find(ye=>ye.slotName!=="cpu"&&ye.slotName!=="mem"),se=(((He=f.resource)==null?void 0:He.resourceOpts)??[]).find(ye=>ye.name==="shmem"),Ke=((oe=f.cluster)==null?void 0:oe.clusterMode)==="SINGLE_NODE"?"single-node":"multi-node";let _e;if((Ce=f.execution)!=null&&Ce.imageId)try{const ye=await Ve.fetchQuery(o,Ct,{id:f.execution.imageId},{fetchPolicy:"store-or-network"}).toPromise();_e=((qe=(Pe=ye==null?void 0:ye.imageV2)==null?void 0:Pe.identity)==null?void 0:qe.canonicalName)??void 0}catch{_e=void 0}const Ee=(((ze=f.execution)==null?void 0:ze.environ)??[]).map(ye=>({variable:ye.key,value:ye.value}));return{cluster_mode:Ke,cluster_size:((Qe=f.cluster)==null?void 0:Qe.clusterSize)??1,allocationPreset:"custom",resource:{cpu:le?Number(le.quantity):0,mem:((We=rn(String((te==null?void 0:te.quantity)??"0"),"g",2))==null?void 0:We.value)??"0g",shmem:((be=rn((se==null?void 0:se.value)??sn,"g",2))==null?void 0:be.value)??sn,...re?{acceleratorType:re.slotName,accelerator:re.slotName==="cuda.shares"?parseFloat(String(re.quantity)):parseInt(String(re.quantity),10)}:{}},enabledAutomaticShmem:!se,runtimeVariantId:f.runtimeVariantId??void 0,environ:Ee,..._e?{environments:{version:_e}}:{}}},ve=async f=>{if(f===R)return;if(R==="preset"&&f==="custom"){const te=D.getFieldsValue(),re=te.revisionPresetId;let se={};if(re){const Ke=await ce(re);Ke&&(se=await Re(Ke))}te.modelFolderId&&(se.modelFolderId=te.modelFolderId),z(Object.keys(se).length>0?se:null),K("custom");return}const J=x.getFieldsValue(),le={};J.modelFolderId&&(le.modelFolderId=J.modelFolderId),x.resetFields(),z(null),$(Object.keys(le).length>0?le:null),K("preset")},me=f=>{var Pe,qe,ze,Qe,We,be,ye,Ue,nl,Oe,Ge,Je,al,Ze,ol,Le,il,dl,Ae,we,rl,sl,ul,Rl,hl,vl,Fl,Al,Dl,Cl,Nl;const J=f.resourceSlots??[],le=J.find($e=>$e.slotName==="cpu"),te=J.find($e=>$e.slotName==="mem"),re=J.find($e=>$e.slotName!=="cpu"&&$e.slotName!=="mem"),se=(((qe=(Pe=f.resourceConfig)==null?void 0:Pe.resourceOpts)==null?void 0:qe.entries)??[]).find($e=>$e.name==="shmem"),Ke=((Qe=(ze=f.modelRuntimeConfig)==null?void 0:ze.runtimeVariant)==null?void 0:Qe.name)??"",_e=Ke==="custom",Ee=(We=f.modelRuntimeConfig)==null?void 0:We.runtimeVariantId;Ee&&Ke&&Y($e=>({...$e,[Ee]:Ke}));const De=(Ue=(ye=(be=f.modelDefinition)==null?void 0:be.models)==null?void 0:ye[0])==null?void 0:Ue.service,He=(Ge=(Oe=(nl=f.modelDefinition)==null?void 0:nl.models)==null?void 0:Oe[0])==null?void 0:Ge.modelPath,oe=_e&&!!De&&(((Je=De.startCommand)==null?void 0:Je.length)??0)>0;Z.current=wn((f.extraMounts??[]).filter($e=>!!$e.mountDestination).map($e=>[$e.vfolderId.replace(/-/g,""),$e.mountDestination]));const Ce=Object.fromEntries((((Ze=(al=f.modelRuntimeConfig)==null?void 0:al.environ)==null?void 0:Ze.entries)??[]).map($e=>[$e.name,$e.value]));if(!_e&&Ke){const $e=Tn(Ke),{[$e]:jl,...Vl}=Ce;w(jl??""),W(Object.keys(Vl).length>0?Vl:void 0)}x.setFieldsValue({cluster_mode:((ol=f.clusterConfig)==null?void 0:ol.mode)==="SINGLE_NODE"?"single-node":"multi-node",cluster_size:((Le=f.clusterConfig)==null?void 0:Le.size)??1,allocationPreset:"custom",resource:{cpu:le?Number(le.quantity):0,mem:((il=rn(String((te==null?void 0:te.quantity)??"0"),"g",2))==null?void 0:il.value)??"0g",shmem:((dl=rn((se==null?void 0:se.value)??sn,"g",2))==null?void 0:dl.value)??sn,...re?{acceleratorType:re.slotName,accelerator:re.slotName==="cuda.shares"?parseFloat(String(re.quantity)):parseInt(String(re.quantity),10)}:{}},enabledAutomaticShmem:!se,mount_ids:(f.extraMounts??[]).map($e=>$e.vfolderId.replace(/-/g,"")),mount_id_map:wn((f.extraMounts??[]).filter($e=>!!$e.mountDestination).map($e=>[$e.vfolderId.replace(/-/g,""),$e.mountDestination])),runtimeVariantId:((Ae=f.modelRuntimeConfig)==null?void 0:Ae.runtimeVariantId)??void 0,modelFolderId:(we=f.modelMountConfig)!=null&&we.vfolderId?Zl("VirtualFolderNode",f.modelMountConfig.vfolderId):void 0,mountDestination:((rl=f.modelMountConfig)==null?void 0:rl.mountDestination)??"/models",definitionPath:((sl=f.modelMountConfig)==null?void 0:sl.definitionPath)??void 0,environments:(Rl=(ul=f.imageV2)==null?void 0:ul.identity)!=null&&Rl.canonicalName?{version:f.imageV2.identity.canonicalName}:void 0,environ:(((vl=(hl=f.modelRuntimeConfig)==null?void 0:hl.environ)==null?void 0:vl.entries)??[]).map($e=>({variable:$e.name,value:$e.value})),...oe&&De?{customDefinitionMode:"command",startCommand:ai(De.startCommand??[]),commandPort:De.port,commandHealthCheck:((Fl=De.healthCheck)==null?void 0:Fl.path)??void 0,commandModelMount:He??"/models",commandInitialDelay:((Al=De.healthCheck)==null?void 0:Al.initialDelay)??void 0,commandMaxRetries:((Dl=De.healthCheck)==null?void 0:Dl.maxRetries)??void 0,commandInterval:((Cl=De.healthCheck)==null?void 0:Cl.interval)??void 0,commandMaxWaitTime:((Nl=De.healthCheck)==null?void 0:Nl.maxWaitTime)??void 0}:_e?{customDefinitionMode:"file"}:{}})},pe=_.useEffectEvent(()=>{B&&(x.setFieldsValue(B),z(null))}),ge=_.useEffectEvent(()=>{U&&(D.setFieldsValue(U),$(null))}),he=_.useEffectEvent(()=>{M||k&&(me(k),I(!0))}),Te=_.useEffectEvent(()=>{V&&c&&(me(c),L(!1),A(!0),r.success(a("deployment.CurrentRevisionConfigurationLoaded")))});_.useEffect(()=>{R==="custom"?(pe(),he(),Te()):ge()},[R]);const Fe=()=>{if(c){if(R==="custom"){me(c),A(!0),r.success(a("deployment.CurrentRevisionConfigurationLoaded"));return}L(!0),K("custom")}},je=(f,J)=>{const le=N.current;if(!le||Object.keys(X.current).length===0)return;const te=Tn(J);for(const oe of Ji())oe!==te&&delete f[oe];const re={};for(const[oe,Ce]of Object.entries(X.current))ne.current.has(oe)&&(re[oe]=Ce);const se=Zi(le),Ke=new Map(se.map(oe=>[oe.key,oe])),_e=Rn(le),Ee={},De={};for(const[oe,Ce]of Object.entries(re)){if(Ce===""||Ce===void 0)continue;const Pe=Ke.get(oe);Pe&&(Pe.presetTarget==="ENV"?De[oe]=Ce:Ee[oe]=Ce)}const He=Bt(le);if(f[te]&&He.size>0){const{unmappedText:oe}=Ot(f[te],He);oe?f[te]=oe:delete f[te]}for(const oe of se)oe.presetTarget==="ENV"&&delete f[oe.key];if(Object.keys(Ee).length>0){const oe=f[te]??"",Ce=Wi(Ee,oe,_e);Ce?f[te]=Ce:delete f[te]}for(const[oe,Ce]of Object.entries(De)){const Pe=Ke.get(oe);(Pe==null?void 0:Pe.defaultValue)!==null&&(Pe==null?void 0:Pe.defaultValue)===Ce||(f[oe]=Ce)}},fe=f=>{var Qe,We;const J=()=>{x.setFields([{name:["environments","version"],errors:[a("modelService.ImageRequired")]}]),x.scrollToField(["environments","version"],{behavior:"smooth",block:"center"})},le=(We=(Qe=f.environments)==null?void 0:Qe.image)==null?void 0:We.id;if(!le){J();return}const te=Ql(le);if(!te){J();return}const re=[{resourceType:"cpu",quantity:String(f.resource.cpu)},{resourceType:"mem",quantity:f.resource.mem}];f.resource.acceleratorType&&f.resource.accelerator&&f.resource.accelerator>0&&re.push({resourceType:f.resource.acceleratorType,quantity:String(f.resource.accelerator)});const se=[];f.resource.shmem&&se.push({name:"shmem",value:f.resource.shmem});const Ke=f.cluster_mode==="single-node"||f.cluster_mode==="multi-node"&&f.cluster_size===1?"SINGLE_NODE":"MULTI_NODE",_e=f.vfoldersNameMap??{},Ee=(f.mount_ids??[]).map(be=>{var Ue;const ye=((Ue=f.mount_id_map)==null?void 0:Ue[be])||Z.current[be]||(_e[be]?`/home/work/${_e[be]}`:`/home/work/${be}`);return{vfolderId:lt(be),mountDestination:ye}}),De=O[f.runtimeVariantId]??"",He=De==="custom",oe=f.customDefinitionMode==="command",Ce={};for(const{variable:be,value:ye}of f.environ??[])be&&(Ce[be]=ye);He||je(Ce,De);const Pe=Object.entries(Ce).map(([be,ye])=>({name:be,value:ye})),qe=He&&oe&&f.startCommand?{models:[{name:"model",modelPath:f.commandModelMount??"/models",service:{preStartActions:[],startCommand:pt(f.startCommand),port:f.commandPort??8e3,healthCheck:f.commandHealthCheck?{path:f.commandHealthCheck,interval:f.commandInterval??10,maxRetries:f.commandMaxRetries??10,maxWaitTime:f.commandMaxWaitTime??15,initialDelay:f.commandInitialDelay}:null}}]}:null,ze=He&&oe?f.commandModelMount??"/models":f.mountDestination||"/models";ae({variables:{input:{deploymentId:Xe((u==null?void 0:u.id)??"")??(u==null?void 0:u.id)??"",clusterConfig:{mode:Ke,size:f.cluster_size},resourceConfig:{resourceSlots:{entries:re},resourceOpts:se.length>0?{entries:se}:null},image:{id:te},modelRuntimeConfig:{runtimeVariantId:f.runtimeVariantId,environ:Pe.length>0?{entries:Pe}:null},modelMountConfig:{vfolderId:Xe(f.modelFolderId),mountDestination:ze,definitionPath:f.definitionPath},modelDefinition:qe,extraMounts:Ee.length>0?Ee:null,options:{autoActivate:E}}},onCompleted:(be,ye)=>{var Ue,nl;if(ye&&ye.length>0){const Oe=ye[0],Ge=(Ue=Oe==null?void 0:Oe.message)==null?void 0:Ue.includes("Another deployment is already in progress");r.error(Ge?a("deployment.AnotherDeploymentInProgress"):(Oe==null?void 0:Oe.message)??a("general.ErrorOccurred"));return}x.resetFields(),r.success(a("deployment.RevisionAdded")),l(!0,(nl=be.addModelRevision)==null?void 0:nl.revision)},onError:be=>{var Ue;const ye=(Ue=be.message)==null?void 0:Ue.includes("Another deployment is already in progress");r.error(ye?a("deployment.AnotherDeploymentInProgress"):be.message??a("general.ErrorOccurred"))}})},Ie=f=>{ae({variables:{input:{deploymentId:Xe((u==null?void 0:u.id)??"")??(u==null?void 0:u.id)??"",revisionPresetId:f.revisionPresetId,modelMountConfig:{vfolderId:Xe(f.modelFolderId),mountDestination:"/models"},options:{autoActivate:E}}},onCompleted:(J,le)=>{var te,re;if(le&&le.length>0){const se=le[0],Ke=(te=se==null?void 0:se.message)==null?void 0:te.includes("Another deployment is already in progress");v.error("[DeploymentAddRevisionModal] addModelRevision (preset) returned errors",le),r.error(Ke?a("deployment.AnotherDeploymentInProgress"):(se==null?void 0:se.message)??a("general.ErrorOccurred"));return}D.resetFields(),r.success(a("deployment.RevisionAdded")),l(!0,(re=J.addModelRevision)==null?void 0:re.revision)},onError:J=>{var te;const le=(te=J.message)==null?void 0:te.includes("Another deployment is already in progress");v.error("[DeploymentAddRevisionModal] addModelRevision (preset) failed",J),r.error(le?a("deployment.AnotherDeploymentInProgress"):J.message??a("general.ErrorOccurred"))}})},ke=()=>{requestAnimationFrame(()=>{const f=document.querySelector(".ant-modal-body .ant-form-item-has-error");f&&f.scrollIntoView({behavior:"smooth",block:"start"})})},Ne=async()=>{const f=R==="preset"?D:x;try{await f.validateFields()}catch{ke();return}f.submit()};return n.jsxs(Gl,{open:s,title:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"md",wrap:"wrap",style:{paddingRight:d.paddingLG},children:[n.jsx("span",{children:a("deployment.AddRevision")}),n.jsx($n,{value:R,onChange:ve,options:[{label:a("deployment.PresetMode"),value:"preset"},{label:a("deployment.CustomMode"),value:"custom"}],style:{fontWeight:"normal"}})]}),width:720,footer:n.jsxs(ie,{direction:"row",align:"center",justify:"between",gap:"sm",children:[n.jsx(at,{checked:E,onChange:f=>H(f.target.checked),disabled:R==="preset"&&ee,children:a("deployment.AutoApply")}),n.jsxs(ie,{direction:"row",align:"center",gap:"xs",children:[n.jsx(gl,{onClick:()=>l(),children:a("button.Cancel")}),n.jsx(gl,{type:"primary",loading:Me,onClick:Ne,disabled:R==="preset"&&ee,children:a("deployment.AddRevision")})]})]}),onCancel:()=>l(),confirmLoading:Me,destroyOnHidden:!0,...t,children:[c&&!i&&!C?n.jsx(Ll,{type:"info",showIcon:!0,style:{marginBottom:d.marginMD},title:a("deployment.CurrentRevisionAvailableDescription"),action:n.jsx(gl,{size:"small",onClick:Fe,children:a("deployment.LoadCurrentRevision")})}):null,R==="preset"?ee?n.jsx(Ll,{type:"info",showIcon:!0,style:{marginTop:d.marginXS},title:a("deployment.NoPresetsAvailable"),description:a("deployment.NoPresetsAvailableSwitchToCustom")}):n.jsxs(ue,{form:D,layout:"vertical",style:{marginTop:d.marginXS},onFinish:Ie,onFinishFailed:ke,initialValues:{modelFolderId:Q},children:[n.jsx(ue.Item,{label:a("modelStore.Preset"),tooltip:a("modelStore.PresetTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(_.Suspense,{fallback:n.jsx(Jl,{loading:!0,style:{flex:1}}),children:n.jsx(ue.Item,{name:"revisionPresetId",noStyle:!0,rules:[{required:!0}],children:n.jsx(ba,{style:{flex:1}})})}),n.jsx(ue.Item,{dependencies:["revisionPresetId"],noStyle:!0,children:({getFieldValue:f})=>{const J=f("revisionPresetId");return n.jsx(en.Compact,{children:n.jsx(cl,{title:a("modelService.DeploymentPresetDetail"),children:n.jsx(gl,{icon:n.jsx(Ra,{}),disabled:!J,onClick:()=>{J&&F(J)}})})})}})]})}),n.jsx(ue.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(_.Suspense,{fallback:n.jsx(Jl,{loading:!0,style:{flex:1}}),children:n.jsx(ue.Item,{name:"modelFolderId",noStyle:!0,rules:[{required:!0}],children:n.jsx(qn,{ref:y,currentProjectId:h??void 0,disabled:!h,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(ue.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:f})=>{const J=f("modelFolderId");return n.jsxs(en.Compact,{children:[n.jsx(cl,{title:a("modelService.OpenFolder"),children:n.jsx(gl,{icon:n.jsx(Un,{}),disabled:!J,onClick:()=>{J&&g(Xe(J))}})}),n.jsx(cl,{title:a("data.CreateANewStorageFolder"),children:n.jsx(gl,{icon:n.jsx(El,{}),onClick:()=>T(!0)})}),n.jsx(cl,{title:a("button.Refresh"),children:n.jsx(gl,{icon:n.jsx(On,{}),onClick:()=>{_.startTransition(()=>{var le;(le=y.current)==null||le.refetch()})}})})]})}})]})})]},"preset-form"):n.jsxs(ue,{form:x,layout:"vertical",style:{marginTop:d.marginXS},onFinish:fe,onFinishFailed:ke,initialValues:Da({},Ca,{resourceGroup:(Be=u==null?void 0:u.metadata)==null?void 0:Be.resourceGroupName,mountDestination:"/models",customDefinitionMode:"command",commandPort:8e3,commandHealthCheck:"/health",commandModelMount:"/models",commandInitialDelay:1800,commandMaxRetries:10,commandInterval:10,commandMaxWaitTime:15,environ:[]}),children:[n.jsx(kn,{children:a("deployment.step.ModelAndRuntime")}),n.jsx(ue.Item,{label:a("deployment.ModelFolder"),tooltip:a("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ie,{direction:"row",gap:"xs",children:[n.jsx(_.Suspense,{fallback:n.jsx(Jl,{loading:!0,style:{flex:1}}),children:n.jsx(ue.Item,{name:"modelFolderId",noStyle:!0,rules:[{required:!0}],children:n.jsx(qn,{ref:p,currentProjectId:h??void 0,disabled:!h,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})})}),n.jsx(ue.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:f})=>{const J=f("modelFolderId");return n.jsxs(en.Compact,{children:[n.jsx(cl,{title:a("modelService.OpenFolder"),children:n.jsx(gl,{icon:n.jsx(Un,{}),disabled:!J,onClick:()=>{J&&g(Xe(J))}})}),n.jsx(cl,{title:a("data.CreateANewStorageFolder"),children:n.jsx(gl,{icon:n.jsx(El,{}),onClick:()=>T(!0)})}),n.jsx(cl,{title:a("button.Refresh"),children:n.jsx(gl,{icon:n.jsx(On,{}),onClick:()=>{_.startTransition(()=>{var le;(le=p.current)==null||le.refetch()})}})})]})}})]})}),n.jsx(_.Suspense,{fallback:n.jsx(Jl,{loading:!0,style:{width:"100%"}}),children:n.jsx(ue.Item,{name:"runtimeVariantId",label:a("deployment.RuntimeVariant"),tooltip:a("deployment.RuntimeVariantTooltip"),rules:[{required:!0},{warningOnly:!0,validator:async(f,J)=>{const le=O[J];return le&&le!=="custom"?Promise.reject(a("modelService.RuntimeVariantDefaultCommandAppliedNote")):Promise.resolve()}}],children:n.jsx(ki,{onResolvedNamesChange:f=>Y(J=>({...J,...f}))})})}),n.jsx(ue.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:f})=>{const J=f("runtimeVariantId"),le=O[J];return!le||le==="custom"?null:n.jsx("div",{style:{marginBottom:d.marginMD},children:n.jsx(_.Suspense,{fallback:null,children:n.jsx(ls,{runtimeVariant:le,onChange:te=>{X.current={...X.current,...te}},onTouchedKeysChange:te=>{ne.current=te},onGroupsLoaded:te=>{N.current=te},initialExtraArgs:j,initialEnvVars:q})})})}}),n.jsx(ue.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:f})=>{const J=f("runtimeVariantId");return O[J]!=="custom"?null:n.jsxs(n.Fragment,{children:[n.jsx(ue.Item,{name:"customDefinitionMode",noStyle:!0,children:n.jsx($n,{options:[{label:a("modelService.EnterCommand"),value:"command"},{label:a("modelService.UseConfigFile"),value:"file"}],style:{marginBottom:d.marginMD}})}),n.jsx(ue.Item,{dependencies:["customDefinitionMode"],noStyle:!0,children:({getFieldValue:te})=>te("customDefinitionMode")==="command"?n.jsxs(n.Fragment,{children:[n.jsx(ue.Item,{name:"startCommand",label:a("modelService.StartCommand"),tooltip:a("modelService.StartCommandTooltip"),rules:[{required:!0,whitespace:!0}],children:n.jsx(Bl.TextArea,{placeholder:a("modelService.StartCommandPlaceholder"),autoSize:{minRows:2}})}),n.jsx(ue.Item,{name:"commandModelMount",label:a("modelService.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),children:n.jsx(Bl,{placeholder:"/models",allowClear:!0})}),n.jsxs(ie,{gap:"sm",children:[n.jsx(ue.Item,{name:"commandPort",label:a("modelService.Port"),tooltip:a("modelService.PortTooltip"),style:{flex:1},children:n.jsx(yl,{min:1,max:65535,style:{width:"100%"}})}),n.jsx(ue.Item,{name:"commandHealthCheck",label:a("modelService.HealthCheck"),tooltip:a("modelService.HealthCheckTooltip"),style:{flex:1},children:n.jsx(Bl,{placeholder:"/health",allowClear:!0})})]}),n.jsxs(ie,{gap:"sm",children:[n.jsx(ue.Item,{name:"commandInitialDelay",label:a("modelService.InitialDelay"),tooltip:a("modelService.InitialDelayTooltip"),style:{flex:1},children:n.jsx(yl,{min:0,step:.5,style:{width:"100%"}})}),n.jsx(ue.Item,{name:"commandMaxRetries",label:a("modelService.MaxRetries"),tooltip:a("modelService.MaxRetriesTooltip"),style:{flex:1},children:n.jsx(yl,{min:0,style:{width:"100%"}})})]}),n.jsxs(ie,{gap:"sm",children:[n.jsx(ue.Item,{name:"commandInterval",label:a("modelService.Interval"),tooltip:a("modelService.IntervalTooltip"),style:{flex:1},children:n.jsx(yl,{min:1,step:.5,style:{width:"100%"}})}),n.jsx(ue.Item,{name:"commandMaxWaitTime",label:a("modelService.MaxWaitTime"),tooltip:a("modelService.MaxWaitTimeTooltip"),style:{flex:1},children:n.jsx(yl,{min:1,step:.5,style:{width:"100%"}})})]})]}):n.jsxs(ie,{gap:"sm",children:[n.jsx(ue.Item,{name:"mountDestination",label:a("deployment.ModelMountDestination"),tooltip:a("modelService.ModelMountTooltip"),rules:[{required:!0}],style:{flex:1},children:n.jsx(Bl,{allowClear:!0,placeholder:"/models"})}),n.jsx(ue.Item,{name:"definitionPath",label:a("deployment.ModelDefinitionPath"),tooltip:a("modelService.ModelDefinitionPathTooltip"),style:{flex:1},children:n.jsx(Bl,{allowClear:!0,placeholder:"model-definition.yaml"})})]})})]})}}),n.jsx(kn,{children:a("session.launcher.Environments")}),n.jsx(_.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:2}}),children:n.jsx(Ta,{})}),n.jsx(Ka,{name:"environ",formItemProps:{validateTrigger:["onChange","onBlur"]}}),n.jsx(kn,{children:a("deployment.step.ClusterAndResources")}),n.jsx(_.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:4}}),children:n.jsx(Ia,{enableResourcePresets:!0,hideResourceGroupFormItem:!0})}),n.jsx(tt,{items:[{key:"advanced",label:a("session.launcher.AdvancedSettings"),children:n.jsx(_.Suspense,{fallback:n.jsx(xl,{active:!0}),children:n.jsx(ue.Item,{noStyle:!0,dependencies:["modelFolderId","mount_id_map","mount_ids"],children:({getFieldValue:f})=>{var te;const J=f("modelFolderId"),le=J?(te=Ql(String(J)))==null?void 0:te.replace(/-/g,""):void 0;return n.jsx(Aa,{label:a("modelService.AdditionalMounts"),tooltip:a("modelService.AdditionalMountsTooltip"),rowKey:"id",tableProps:{scroll:{x:"max-content",y:300}},rowFilter:re=>{var se;return re.usage_mode!=="model"&&re.status==="ready"&&!((se=re.name)!=null&&se.startsWith("."))&&re.id!==le}})}})})}]})]},"custom-form"),S&&n.jsx(_.Suspense,{fallback:null,children:n.jsx(rs,{presetId:S,onCancel:()=>F(null)})}),n.jsx(Ma,{open:P,initialValues:{usage_mode:"model"},onRequestClose:f=>{if(T(!1),f!=null&&f.id){const J=Ql(f.id);if(!J)return;const le=Zl("VirtualFolderNode",J),te=R==="preset"?D:x,re=R==="preset"?y:p;te.setFieldValue("modelFolderId",le),_.startTransition(()=>{var se;(se=re.current)==null||se.refetch()})}}})]})},Qt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};Qt.hash="129d74dafb7ab8394c47065f3b9af25e";const qt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAutoScalingRulePayload",kind:"LinkedField",name:"deleteAutoScalingRule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleListDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleListDeleteMutation",selections:e},params:{cacheID:"84fac37f17347340ba1f6a7991bc3624",id:null,metadata:{},name:"AutoScalingRuleListDeleteMutation",operationKind:"mutation",text:`mutation AutoScalingRuleListDeleteMutation(
  $input: DeleteAutoScalingRuleInput!
) {
  deleteAutoScalingRule(input: $input) {
    id
  }
}
`}}}();qt.hash="c0d22df767771306d1fc0a431e5d177b";const zt=function(){var l=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleListPresetsQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleListPresetsQuery",selections:l},params:{cacheID:"9b99973a6bf38ac02bd91f644c8cb1a1",id:null,metadata:{},name:"AutoScalingRuleListPresetsQuery",operationKind:"query",text:`query AutoScalingRuleListPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();zt.hash="7f4c998b34def6faefe25959c5cb64e2";const Ut=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"AutoScalingRuleListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[r,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[o,u,{args:null,kind:"FragmentSpread",name:"AutoScalingRuleListNodesFragment"},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,s,i,t,e],kind:"Operation",name:"AutoScalingRuleListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[r,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[o,u,{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},o],storageKey:null}]},params:{cacheID:"79f124acac426955bf7fe564f6d9a5c1",id:null,metadata:{},name:"AutoScalingRuleListQuery",operationKind:"query",text:`query AutoScalingRuleListQuery(
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
`}}}();Ut.hash="bfa849a7cb503e04b249b2f73510b568";const Wt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"AutoScalingRuleListNodesFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],type:"AutoScalingRule",abstractKey:null};Wt.hash="54a32b764fc7e506f5bddfe218691cd2";const Gt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"UpdateAutoScalingRulePayload",kind:"LinkedField",name:"updateAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalUpdateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalUpdateMutation",selections:e},params:{cacheID:"f5194bd994f4693e29536fec36e4f0e4",id:null,metadata:{},name:"AutoScalingRuleEditorModalUpdateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalUpdateMutation(
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
`}}}();Gt.hash="8e953443e1aa963b955810e5f97de017";const Yt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAutoScalingRulePayload",kind:"LinkedField",name:"createAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalCreateMutation",selections:e},params:{cacheID:"c7c250dabfc49b66cf1aebbff6414d44",id:null,metadata:{},name:"AutoScalingRuleEditorModalCreateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalCreateMutation(
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
`}}}();Yt.hash="7afa475334295923b7754d0563a8b919";const Xt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],type:"AutoScalingRule",abstractKey:null};Xt.hash="9dff1f6ce3b17626029eee3484220a7d";const Jt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[l,e,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"categoryId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queryTemplate",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,concreteType:"QueryPresetCategory",kind:"LinkedField",name:"category",plural:!1,selections:[l,e],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalPresetsQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleEditorModalPresetsQuery",selections:i},params:{cacheID:"04d06fec5284e709aaee3606d8a4bb53",id:null,metadata:{},name:"AutoScalingRuleEditorModalPresetsQuery",operationKind:"query",text:`query AutoScalingRuleEditorModalPresetsQuery {
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
`}}}();Jt.hash="6582d4cf067148f5b39755e919c0f4f2";const Sn={KERNEL:["cpu_util","mem","net_rx","net_tx"],INFERENCE_FRAMEWORK:[]},Wn=l=>l?l.minThreshold!=null&&l.maxThreshold!=null?"scale_in_out":l.maxThreshold!=null?"scale_out":"scale_in":"scale_out",os=l=>{"use memo";var dl;const e=ll.c(195),{autoScalingRule:i,formRef:s}=l,{t}=tl(),{token:a}=Il.useToken(),d=rt();let r;e[0]!==d?(r=d.supports("prometheus-auto-scaling-rule"),e[0]=d,e[1]=r):r=e[1];const o=r;let u,m;e[2]===Symbol.for("react.memo_cache_sentinel")?(u=Jt,m={},e[2]=u,e[3]=m):(u=e[2],m=e[3]);const{prometheusQueryPresets:c}=Ve.useLazyLoadQuery(u,m);let k;e[4]!==(c==null?void 0:c.edges)?(k=Pa(bl(c==null?void 0:c.edges,ds)),e[4]=c==null?void 0:c.edges,e[5]=k):k=e[5];const h=k;let v;e[6]!==i?(v=Wn(i),e[6]=i,e[7]=v):v=e[7];const[g,y]=_.useState(v),[p,P]=_.useState((i==null?void 0:i.metricSource)||"KERNEL");let T;e[8]!==i||e[9]!==h?(T=i!=null&&i.prometheusQueryPresetId?(dl=h.find(Ae=>Xe(Ae.id)===i.prometheusQueryPresetId))==null?void 0:dl.id:void 0,e[8]=i,e[9]=h,e[10]=T):T=e[10];const[x,D]=_.useState(T);let E;e[11]!==(i==null?void 0:i.metricSource)?(E=Sn[(i==null?void 0:i.metricSource)||"KERNEL"]||[],e[11]=i==null?void 0:i.metricSource,e[12]=E):E=e[12];const[H,b]=_.useState(E);let K;if(e[13]!==h||e[14]!==x){let Ae;e[16]!==x?(Ae=we=>we.id===x,e[16]=x,e[17]=Ae):Ae=e[17],K=h.find(Ae),e[13]=h,e[14]=x,e[15]=K}else K=e[15];const R=K;let C;if(e[18]!==h){const Ae=ui(h,["rank"],["asc"]),we=Ae.filter(cs),rl=Ae.filter(ms),sl=gs,ul=Na(we,ys),Rl=Object.entries(ul).map(hl=>{const[vl,Fl]=hl;return{label:vl,options:Fl.map(sl)}});C=rl.length>0?[...Rl,...rl.map(sl)]:Rl,e[18]=h,e[19]=C}else C=e[19];const A=C;let M;e[20]!==i||e[21]!==x?(M=()=>{if(i){const Ae=Wn(i);let we;return Ae==="scale_in"&&i.minThreshold!=null?we=Number(i.minThreshold):Ae==="scale_out"&&i.maxThreshold!=null&&(we=Number(i.maxThreshold)),{metricSource:i.metricSource,metricName:i.metricName,prometheusQueryPresetId:x,conditionMode:Ae,threshold:we,minThreshold:i.minThreshold!=null?Number(i.minThreshold):void 0,maxThreshold:i.maxThreshold!=null?Number(i.maxThreshold):void 0,stepSize:Math.abs(i.stepSize),timeWindow:i.timeWindow,minReplicas:i.minReplicas??void 0,maxReplicas:i.maxReplicas??void 0}}return{metricSource:"KERNEL",conditionMode:"scale_out",stepSize:1,timeWindow:300,minReplicas:0,maxReplicas:5}},e[20]=i,e[21]=x,e[22]=M):M=e[22];const I=M,V=p==="PROMETHEUS";let L;e[23]!==I?(L=I(),e[23]=I,e[24]=L):L=e[24];let B;e[25]!==t?(B=t("autoScalingRule.MetricSource"),e[25]=t,e[26]=B):B=e[26];let z;e[27]!==t?(z=t("autoScalingRule.MetricSourceTooltip"),e[27]=t,e[28]=z):z=e[28];let U;e[29]===Symbol.for("react.memo_cache_sentinel")?(U=[{required:!0}],e[29]=U):U=e[29];let $;e[30]!==s?($=Ae=>{var we,rl;if(P(Ae),(we=s.current)==null||we.setFieldsValue({metricName:void 0}),Ae!=="PROMETHEUS")b(Sn[Ae]||[]),D(void 0);else{const sl=(rl=s.current)==null?void 0:rl.getFieldValue("prometheusQueryPresetId");sl&&D(sl)}},e[30]=s,e[31]=$):$=e[31];let S;e[32]!==t?(S=t("autoScalingRule.MetricSourceKernel"),e[32]=t,e[33]=S):S=e[33];let F;e[34]!==S?(F={label:S,value:"KERNEL"},e[34]=S,e[35]=F):F=e[35];let O;e[36]!==o||e[37]!==t?(O=o?[]:[{label:t("autoScalingRule.MetricSourceInferenceFramework"),value:"INFERENCE_FRAMEWORK"}],e[36]=o,e[37]=t,e[38]=O):O=e[38];let Y;e[39]!==t?(Y=t("autoScalingRule.MetricSourcePrometheus"),e[39]=t,e[40]=Y):Y=e[40];let X;e[41]!==Y?(X={label:Y,value:"PROMETHEUS"},e[41]=Y,e[42]=X):X=e[42];let ne;e[43]!==F||e[44]!==O||e[45]!==X?(ne=[F,...O,X],e[43]=F,e[44]=O,e[45]=X,e[46]=ne):ne=e[46];let N;e[47]!==$||e[48]!==ne?(N=n.jsx(dn,{onChange:$,options:ne}),e[47]=$,e[48]=ne,e[49]=N):N=e[49];let j;e[50]!==B||e[51]!==z||e[52]!==N?(j=n.jsx(ue.Item,{label:B,name:"metricSource",tooltip:z,rules:U,children:N}),e[50]=B,e[51]=z,e[52]=N,e[53]=j):j=e[53];let w;e[54]!==t?(w=t("autoScalingRule.MetricName"),e[54]=t,e[55]=w):w=e[55];let q;e[56]!==t?(q=t("autoScalingRule.MetricNameTooltip"),e[56]=t,e[57]=q):q=e[57];const W=!V;let Z;e[58]!==W?(Z=[{required:W}],e[58]=W,e[59]=Z):Z=e[59];let ee;e[60]!==t?(ee=t("autoScalingRule.MetricName"),e[60]=t,e[61]=ee):ee=e[61];let G;e[62]!==H?(G=bl(H,ps),e[62]=H,e[63]=G):G=e[63];let Q;e[64]!==s?(Q={onSearch:Ae=>{var rl;const we=((rl=s.current)==null?void 0:rl.getFieldValue("metricSource"))||"KERNEL";b(_a(Sn[we]||[],sl=>sl.includes(Ae)))}},e[64]=s,e[65]=Q):Q=e[65];let Se;e[66]!==ee||e[67]!==G||e[68]!==Q?(Se=n.jsx(Ea,{placeholder:ee,options:G,showSearch:Q,allowClear:!0,popupMatchSelectWidth:!1}),e[66]=ee,e[67]=G,e[68]=Q,e[69]=Se):Se=e[69];let ce;e[70]!==V||e[71]!==w||e[72]!==q||e[73]!==Z||e[74]!==Se?(ce=n.jsx(ue.Item,{label:w,name:"metricName",hidden:V,tooltip:q,rules:Z,children:Se}),e[70]=V,e[71]=w,e[72]=q,e[73]=Z,e[74]=Se,e[75]=ce):ce=e[75];let ae;e[76]!==s||e[77]!==V||e[78]!==h||e[79]!==A||e[80]!==R||e[81]!==t||e[82]!==a.fontSizeSM?(ae=V&&n.jsx(n.Fragment,{children:n.jsx(ue.Item,{label:`${t("autoScalingRule.MetricName")} (${t("autoScalingRule.PrometheusPreset")})`,name:"prometheusQueryPresetId",tooltip:t("autoScalingRule.PrometheusPresetTooltip"),rules:[{required:!0,message:t("autoScalingRule.PrometheusPresetRequired")}],extra:R?n.jsx(oi,{queryTemplate:R.queryTemplate},R.id):void 0,children:n.jsx(dn,{onChange:Ae=>{var rl,sl;D(Ae);const we=h.find(ul=>ul.id===Ae);if(we){(rl=s.current)==null||rl.setFieldsValue({metricName:we.metricName});const ul=we.timeWindow!=null?Number(we.timeWindow):void 0;ul!=null&&!isNaN(ul)&&((sl=s.current)==null||sl.setFieldsValue({timeWindow:ul}))}},placeholder:t("autoScalingRule.SelectPrometheusPreset"),showSearch:{filterOption:fs},options:A,optionRender:Ae=>n.jsxs(ie,{direction:"column",align:"start",children:[Ae.label,Ae.data.description&&n.jsx(el.Text,{type:"secondary",style:{fontSize:a.fontSizeSM},ellipsis:!0,children:Ae.data.description})]}),allowClear:!0,onClear:()=>D(void 0)})})}),e[76]=s,e[77]=V,e[78]=h,e[79]=A,e[80]=R,e[81]=t,e[82]=a.fontSizeSM,e[83]=ae):ae=e[83];let Me;e[84]!==t?(Me=t("autoScalingRule.Condition"),e[84]=t,e[85]=Me):Me=e[85];let Re;e[86]!==t?(Re=t("autoScalingRule.ConditionTooltip"),e[86]=t,e[87]=Re):Re=e[87];let ve;e[88]===Symbol.for("react.memo_cache_sentinel")?(ve=Ae=>{y(Ae.target.value)},e[88]=ve):ve=e[88];let me;e[89]!==a.marginSM?(me={marginBottom:a.marginSM},e[89]=a.marginSM,e[90]=me):me=e[90];let pe;e[91]!==t?(pe=t("autoScalingRule.ScaleIn"),e[91]=t,e[92]=pe):pe=e[92];let ge;e[93]!==pe?(ge={label:pe,value:"scale_in"},e[93]=pe,e[94]=ge):ge=e[94];let he;e[95]!==t?(he=t("autoScalingRule.ScaleOut"),e[95]=t,e[96]=he):he=e[96];let Te;e[97]!==he?(Te={label:he,value:"scale_out"},e[97]=he,e[98]=Te):Te=e[98];let Fe;e[99]!==t?(Fe=t("autoScalingRule.ScaleInAndOut"),e[99]=t,e[100]=Fe):Fe=e[100];let je;e[101]!==Fe?(je={label:Fe,value:"scale_in_out"},e[101]=Fe,e[102]=je):je=e[102];let fe;e[103]!==ge||e[104]!==Te||e[105]!==je?(fe=[ge,Te,je],e[103]=ge,e[104]=Te,e[105]=je,e[106]=fe):fe=e[106];let Ie;e[107]!==me||e[108]!==fe?(Ie=n.jsx(ue.Item,{name:"conditionMode",noStyle:!0,children:n.jsx(Va.Group,{optionType:"button",onChange:ve,style:me,options:fe})}),e[107]=me,e[108]=fe,e[109]=Ie):Ie=e[109];let ke;e[110]!==g||e[111]!==t?(ke=g==="scale_in"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(el.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ue.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),e[110]=g,e[111]=t,e[112]=ke):ke=e[112];let Ne;e[113]!==g||e[114]!==t?(Ne=g==="scale_out"&&n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ue.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(el.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]}),e[113]=g,e[114]=t,e[115]=Ne):Ne=e[115];let xe;e[116]!==g||e[117]!==t?(xe=g==="scale_in_out"&&n.jsxs(ie,{direction:"column",gap:"xs",align:"stretch",children:[n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsxs(el.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ue.Item,{name:"minThreshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.MinThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ue.Item,{name:"maxThreshold",noStyle:!0,dependencies:["minThreshold"],rules:[{required:!0,message:t("autoScalingRule.MaxThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")},Ae=>{const{getFieldValue:we}=Ae;return{validator(rl,sl){const ul=we("minThreshold");return ul!=null&&sl!=null&&ul>=sl?Promise.reject(new Error(t("autoScalingRule.MinMustBeLessThanMax"))):Promise.resolve()}}}],children:n.jsx(yl,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(el.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]})]}),e[116]=g,e[117]=t,e[118]=xe):xe=e[118];let de;e[119]!==Me||e[120]!==Re||e[121]!==Ie||e[122]!==ke||e[123]!==Ne||e[124]!==xe?(de=n.jsxs(ue.Item,{label:Me,required:!0,tooltip:Re,children:[Ie,ke,Ne,xe]}),e[119]=Me,e[120]=Re,e[121]=Ie,e[122]=ke,e[123]=Ne,e[124]=xe,e[125]=de):de=e[125];let Be;e[126]!==t?(Be=t("autoScalingRule.StepSize"),e[126]=t,e[127]=Be):Be=e[127];let f;e[128]!==t?(f=t("autoScalingRule.StepSizeTooltip"),e[128]=t,e[129]=f):f=e[129];let J,le;e[130]===Symbol.for("react.memo_cache_sentinel")?(J={required:!0},le={type:"number",min:1,max:Xl},e[130]=J,e[131]=le):(J=e[130],le=e[131]);let te;e[132]!==t?(te=[J,le,{validator:(Ae,we)=>we%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[132]=t,e[133]=te):te=e[133];let re;e[134]===Symbol.for("react.memo_cache_sentinel")?(re={width:"100%"},e[134]=re):re=e[134];const se=g==="scale_in_out"?"±":g==="scale_out"?"+":"−";let Ke;e[135]!==se?(Ke=n.jsx(yl,{min:1,step:1,style:re,prefix:n.jsx(el.Text,{type:"secondary",children:se})}),e[135]=se,e[136]=Ke):Ke=e[136];let _e;e[137]!==Be||e[138]!==f||e[139]!==te||e[140]!==Ke?(_e=n.jsx(ue.Item,{label:Be,name:"stepSize",tooltip:f,rules:te,children:Ke}),e[137]=Be,e[138]=f,e[139]=te,e[140]=Ke,e[141]=_e):_e=e[141];let Ee;e[142]!==t?(Ee=t("autoScalingRule.CoolDownSeconds"),e[142]=t,e[143]=Ee):Ee=e[143];let De;e[144]!==t?(De=t("autoScalingRule.CoolDownTooltip"),e[144]=t,e[145]=De):De=e[145];let He,oe;e[146]===Symbol.for("react.memo_cache_sentinel")?(He={required:!0},oe={type:"number",min:1},e[146]=He,e[147]=oe):(He=e[146],oe=e[147]);let Ce;e[148]!==t?(Ce=[He,oe,{validator:(Ae,we)=>we%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[148]=t,e[149]=Ce):Ce=e[149];let Pe;e[150]===Symbol.for("react.memo_cache_sentinel")?(Pe={width:"100%"},e[150]=Pe):Pe=e[150];let qe;e[151]!==t?(qe=t("autoScalingRule.Seconds"),e[151]=t,e[152]=qe):qe=e[152];let ze;e[153]!==qe?(ze=n.jsx(yl,{min:1,step:1,style:Pe,suffix:n.jsx(el.Text,{type:"secondary",children:qe})}),e[153]=qe,e[154]=ze):ze=e[154];let Qe;e[155]!==Ee||e[156]!==De||e[157]!==Ce||e[158]!==ze?(Qe=n.jsx(ue.Item,{label:Ee,name:"timeWindow",tooltip:De,rules:Ce,children:ze}),e[155]=Ee,e[156]=De,e[157]=Ce,e[158]=ze,e[159]=Qe):Qe=e[159];let We;e[160]!==t?(We=t("autoScalingRule.MinReplicas"),e[160]=t,e[161]=We):We=e[161];let be;e[162]!==t?(be=t("autoScalingRule.MinReplicasTooltip"),e[162]=t,e[163]=be):be=e[163];let ye;e[164]===Symbol.for("react.memo_cache_sentinel")?(ye={min:0,max:Xl,type:"number"},e[164]=ye):ye=e[164];let Ue;e[165]!==t?(Ue=[ye,{validator:(Ae,we)=>we!=null&&we%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[165]=t,e[166]=Ue):Ue=e[166];let nl;e[167]===Symbol.for("react.memo_cache_sentinel")?(nl=n.jsx(yl,{min:0,max:Xl,style:{width:"100%"}}),e[167]=nl):nl=e[167];let Oe;e[168]!==We||e[169]!==be||e[170]!==Ue?(Oe=n.jsx(ue.Item,{label:We,name:"minReplicas",tooltip:be,rules:Ue,children:nl}),e[168]=We,e[169]=be,e[170]=Ue,e[171]=Oe):Oe=e[171];let Ge;e[172]!==t?(Ge=t("autoScalingRule.MaxReplicas"),e[172]=t,e[173]=Ge):Ge=e[173];let Je;e[174]!==t?(Je=t("autoScalingRule.MaxReplicasTooltip"),e[174]=t,e[175]=Je):Je=e[175];let al;e[176]===Symbol.for("react.memo_cache_sentinel")?(al={min:0,max:Xl,type:"number"},e[176]=al):al=e[176];let Ze;e[177]!==t?(Ze=[al,{validator:(Ae,we)=>we!=null&&we%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[177]=t,e[178]=Ze):Ze=e[178];let ol;e[179]===Symbol.for("react.memo_cache_sentinel")?(ol=n.jsx(yl,{min:0,max:Xl,style:{width:"100%"}}),e[179]=ol):ol=e[179];let Le;e[180]!==Ge||e[181]!==Je||e[182]!==Ze?(Le=n.jsx(ue.Item,{label:Ge,name:"maxReplicas",tooltip:Je,rules:Ze,children:ol}),e[180]=Ge,e[181]=Je,e[182]=Ze,e[183]=Le):Le=e[183];let il;return e[184]!==s||e[185]!==L||e[186]!==j||e[187]!==ce||e[188]!==ae||e[189]!==de||e[190]!==_e||e[191]!==Qe||e[192]!==Oe||e[193]!==Le?(il=n.jsxs(ue,{ref:s,layout:"vertical",initialValues:L,children:[j,ce,ae,de,_e,Qe,Oe,Le]}),e[184]=s,e[185]=L,e[186]=j,e[187]=ce,e[188]=ae,e[189]=de,e[190]=_e,e[191]=Qe,e[192]=Oe,e[193]=Le,e[194]=il):il=e[194],il},us=l=>{"use memo";const e=ll.c(34);let i,s,t,a,d;e[0]!==l?({onRequestClose:d,onComplete:a,modelDeploymentId:t,autoScalingRuleFrgmt:i,...s}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5]);const{t:r}=tl(),{message:o}=$l.useApp(),{logger:u}=Wl();let m;e[6]===Symbol.for("react.memo_cache_sentinel")?(m=Xt,e[6]=m):m=e[6];const c=Ve.useFragment(m,i??null),k=_.useRef(null);let h;e[7]===Symbol.for("react.memo_cache_sentinel")?(h=Yt,e[7]=h):h=e[7];const[v,g]=Ve.useMutation(h);let y;e[8]===Symbol.for("react.memo_cache_sentinel")?(y=Gt,e[8]=y):y=e[8];const[p,P]=Ve.useMutation(y);let T;e[9]!==c||e[10]!==v||e[11]!==p||e[12]!==u||e[13]!==o||e[14]!==t||e[15]!==a||e[16]!==d||e[17]!==r?(T=()=>{var M;return(M=k.current)==null?void 0:M.validateFields().then(I=>{let V=null,L=null;I.conditionMode==="scale_in_out"?(V=I.minThreshold??null,L=I.maxThreshold??null):I.conditionMode==="scale_in"?V=I.threshold??null:L=I.threshold??null;const B=I.metricName,z=I.metricSource==="PROMETHEUS"&&I.prometheusQueryPresetId?Xe(I.prometheusQueryPresetId):null;c?p({variables:{input:{id:Xe(c.id),metricSource:I.metricSource,metricName:B,minThreshold:V!=null?String(V):null,maxThreshold:L!=null?String(L):null,stepSize:I.stepSize,timeWindow:I.timeWindow,minReplicas:I.minReplicas,maxReplicas:I.maxReplicas,prometheusQueryPresetId:z??void 0}},onCompleted:(U,$)=>{if($&&$.length>0){const S=bl($,ks);for(const F of S)o.error(F);return}o.success(r("autoScalingRule.SuccessfullyUpdated")),a==null||a(),d(!0)},onError:U=>{o.error(U.message)}}):v({variables:{input:{modelDeploymentId:t,metricSource:I.metricSource,metricName:B,minThreshold:V!=null?String(V):null,maxThreshold:L!=null?String(L):null,stepSize:I.stepSize,timeWindow:I.timeWindow,minReplicas:I.minReplicas,maxReplicas:I.maxReplicas,prometheusQueryPresetId:z??void 0}},onCompleted:(U,$)=>{if($&&$.length>0){const S=bl($,Ss);for(const F of S)o.error(F);return}o.success(r("autoScalingRule.SuccessfullyCreated")),a==null||a(),d(!0)},onError:U=>{o.error(U.message)}})}).catch(I=>{u.error(I)})},e[9]=c,e[10]=v,e[11]=p,e[12]=u,e[13]=o,e[14]=t,e[15]=a,e[16]=d,e[17]=r,e[18]=T):T=e[18];const x=T;let D;e[19]!==d?(D=()=>{d(!1)},e[19]=d,e[20]=D):D=e[20];const E=D;let H;e[21]!==c||e[22]!==r?(H=r(c?"autoScalingRule.EditAutoScalingRule":"autoScalingRule.AddAutoScalingRule"),e[21]=c,e[22]=r,e[23]=H):H=e[23];const b=g||P;let K;e[24]===Symbol.for("react.memo_cache_sentinel")?(K=n.jsx(xl,{active:!0,paragraph:{rows:6}}),e[24]=K):K=e[24];const R=c??null;let C;e[25]!==R?(C=n.jsx(st,{children:n.jsx(La.Suspense,{fallback:K,children:n.jsx(os,{autoScalingRule:R,formRef:k})})}),e[25]=R,e[26]=C):C=e[26];let A;return e[27]!==s||e[28]!==E||e[29]!==x||e[30]!==C||e[31]!==H||e[32]!==b?(A=n.jsx(Gl,{...s,onOk:x,onCancel:E,centered:!0,title:H,confirmLoading:b,children:C}),e[27]=s,e[28]=E,e[29]=x,e[30]=C,e[31]=H,e[32]=b,e[33]=A):A=e[33],A};function ds(l){return l==null?void 0:l.node}function cs(l){var e;return(e=l.category)==null?void 0:e.name}function ms(l){var e;return!((e=l.category)!=null&&e.name)}function gs(l){return{label:l.name,value:l.id,description:l.description}}function ys(l){return l.category.name}function ps(l){return{label:l,value:l}}function fs(l,e){return String((e==null?void 0:e.label)??"").toLowerCase().includes(l.toLowerCase())}function ks(l){return l.message}function Ss(l){return l.message}const hs=(l,e,i)=>{const s=l.metricSource==="PROMETHEUS"&&l.prometheusQueryPresetId?(i==null?void 0:i.get(l.prometheusQueryPresetId))??l.metricName:l.metricName,t=l.minThreshold,a=l.maxThreshold;return t!=null&&a!=null?n.jsxs(ie,{direction:"column",gap:"xxs",children:[n.jsxs(ie,{gap:"xs",children:[n.jsx(on,{children:s})," < ",t]}),n.jsxs(ie,{gap:"xs",children:[a," < ",n.jsx(on,{children:s})]})]}):a!=null?n.jsxs(ie,{gap:"xs",children:[a,n.jsx(cl,{title:e("autoScalingRule.MaxThreshold"),children:"<"}),n.jsx(on,{children:s})]}):t!=null?n.jsxs(ie,{gap:"xs",children:[n.jsx(on,{children:s}),n.jsx(cl,{title:e("autoScalingRule.MinThreshold"),children:"<"}),t]}):"-"},un=l=>{const e={};return l.createdAt&&(e.createdAt=l.createdAt),l.lastTriggeredAt&&(e.lastTriggeredAt=l.lastTriggeredAt),Array.isArray(l.AND)&&(e.AND=l.AND.map(un)),Array.isArray(l.OR)&&(e.OR=l.OR.map(un)),Array.isArray(l.NOT)&&(e.NOT=l.NOT.map(un)),e},vs=l=>{"use memo";const e=ll.c(103);let i,s,t,a,d,r,o;e[0]!==l?({autoScalingRulesFrgmt:i,presetMap:r,isEndpointDestroying:s,isOwnedByCurrentUser:t,onEditRule:d,onDeleteRule:a,...o}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d,e[6]=r,e[7]=o):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5],r=e[6],o=e[7]);const{t:u}=tl();let m;e[8]===Symbol.for("react.memo_cache_sentinel")?(m=Wt,e[8]=m):m=e[8];const c=Ve.useFragment(m,i);let k;e[9]!==c?(k=zl(c),e[9]=c,e[10]=k):k=e[10];const h=k;let v;e[11]===Symbol.for("react.memo_cache_sentinel")?(v={x:"max-content"},e[11]=v):v=e[11];let g;e[12]!==u?(g=u("autoScalingRule.MetricSource"),e[12]=u,e[13]=g):g=e[13];let y;e[14]!==u?(y=u("autoScalingRule.MetricSourceTooltip"),e[14]=u,e[15]=y):y=e[15];let p;e[16]!==y?(p=n.jsx(fl,{title:y}),e[16]=y,e[17]=p):p=e[17];let P;e[18]!==g||e[19]!==p?(P={key:"metricSource",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[g,p]}),dataIndex:"metricSource",fixed:"left"},e[18]=g,e[19]=p,e[20]=P):P=e[20];let T;e[21]!==u?(T=u("autoScalingRule.Condition"),e[21]=u,e[22]=T):T=e[22];let x;e[23]!==u?(x=u("autoScalingRule.ConditionTooltip"),e[23]=u,e[24]=x):x=e[24];let D;e[25]!==x?(D=n.jsx(fl,{title:x}),e[25]=x,e[26]=D):D=e[26];let E;e[27]!==D||e[28]!==T?(E=n.jsxs(ie,{gap:"xxs",align:"center",children:[T,D]}),e[27]=D,e[28]=T,e[29]=E):E=e[29];let H;e[30]!==s||e[31]!==t||e[32]!==a||e[33]!==d||e[34]!==r||e[35]!==u?(H=(G,Q)=>Q?n.jsx(jn,{title:hs(Q,u,r),showActions:"always",actions:[{key:"edit",title:u("button.Edit"),icon:n.jsx(wa,{}),disabled:s||!t,onClick:()=>d(Q.id)},{key:"delete",title:u("button.Delete"),icon:n.jsx(Ln,{}),type:"danger",disabled:s||!t,onClick:()=>a(Q.id,Q.metricName??"")}]}):"-",e[30]=s,e[31]=t,e[32]=a,e[33]=d,e[34]=r,e[35]=u,e[36]=H):H=e[36];let b;e[37]!==E||e[38]!==H?(b={key:"condition",title:E,fixed:"left",render:H},e[37]=E,e[38]=H,e[39]=b):b=e[39];let K;e[40]!==u?(K=u("autoScalingRule.CoolDownSeconds"),e[40]=u,e[41]=K):K=e[41];let R;e[42]!==u?(R=u("autoScalingRule.CoolDownTooltip"),e[42]=u,e[43]=R):R=e[43];let C;e[44]!==R?(C=n.jsx(fl,{title:R}),e[44]=R,e[45]=C):C=e[45];let A;e[46]!==K||e[47]!==C?(A=n.jsxs(ie,{gap:"xxs",align:"center",children:[K,C]}),e[46]=K,e[47]=C,e[48]=A):A=e[48];let M;e[49]!==u?(M=G=>G!=null?u("autoScalingRule.CoolDownSecondsValue",{value:G}):"-",e[49]=u,e[50]=M):M=e[50];let I;e[51]!==A||e[52]!==M?(I={key:"timeWindow",title:A,dataIndex:"timeWindow",render:M},e[51]=A,e[52]=M,e[53]=I):I=e[53];let V;e[54]!==u?(V=u("autoScalingRule.StepSize"),e[54]=u,e[55]=V):V=e[55];let L;e[56]!==u?(L=u("autoScalingRule.StepSizeTooltip"),e[56]=u,e[57]=L):L=e[57];let B;e[58]!==L?(B=n.jsx(fl,{title:L}),e[58]=L,e[59]=B):B=e[59];let z;e[60]!==V||e[61]!==B?(z={key:"stepSize",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[V,B]}),dataIndex:"stepSize",render:xs},e[60]=V,e[61]=B,e[62]=z):z=e[62];let U;e[63]!==u?(U=u("autoScalingRule.MIN/MAXReplicas"),e[63]=u,e[64]=U):U=e[64];let $;e[65]!==u?($=u("autoScalingRule.MinMaxReplicasTooltip"),e[65]=u,e[66]=$):$=e[66];let S;e[67]!==$?(S=n.jsx(fl,{title:$}),e[67]=$,e[68]=S):S=e[68];let F;e[69]!==U||e[70]!==S?(F=n.jsxs(ie,{gap:"xxs",align:"center",children:[U,S]}),e[69]=U,e[70]=S,e[71]=F):F=e[71];let O;e[72]!==u?(O=(G,Q)=>{if(!(Q!=null&&Q.stepSize))return"-";const Se=Q.minThreshold!=null,ce=Q.maxThreshold!=null;return Se&&ce?n.jsxs("span",{children:[u("autoScalingRule.MinReplicasValue",{value:Q==null?void 0:Q.minReplicas})," / ",u("autoScalingRule.MaxReplicasValue",{value:Q==null?void 0:Q.maxReplicas})]}):ce?n.jsx("span",{children:u("autoScalingRule.MaxReplicasValue",{value:Q==null?void 0:Q.maxReplicas})}):n.jsx("span",{children:u("autoScalingRule.MinReplicasValue",{value:Q==null?void 0:Q.minReplicas})})},e[72]=u,e[73]=O):O=e[73];let Y;e[74]!==F||e[75]!==O?(Y={key:"minMaxReplicas",title:F,render:O},e[74]=F,e[75]=O,e[76]=Y):Y=e[76];let X;e[77]!==u?(X=u("autoScalingRule.CreatedAt"),e[77]=u,e[78]=X):X=e[78];let ne;e[79]===Symbol.for("react.memo_cache_sentinel")?(ne=["descend","ascend"],e[79]=ne):ne=e[79];let N;e[80]!==X?(N={key:"createdAt",title:X,dataIndex:"createdAt",sorter:!0,sortDirections:ne,render:bs},e[80]=X,e[81]=N):N=e[81];let j;e[82]!==u?(j=u("autoScalingRule.LastTriggered"),e[82]=u,e[83]=j):j=e[83];let w;e[84]!==u?(w=u("autoScalingRule.LastTriggeredTooltip"),e[84]=u,e[85]=w):w=e[85];let q;e[86]!==w?(q=n.jsx(fl,{title:w}),e[86]=w,e[87]=q):q=e[87];let W;e[88]!==j||e[89]!==q?(W={key:"lastTriggeredAt",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[j,q]}),render:Rs},e[88]=j,e[89]=q,e[90]=W):W=e[90];let Z;e[91]!==b||e[92]!==I||e[93]!==z||e[94]!==Y||e[95]!==N||e[96]!==W||e[97]!==P?(Z=[P,b,I,z,Y,N,W],e[91]=b,e[92]=I,e[93]=z,e[94]=Y,e[95]=N,e[96]=W,e[97]=P,e[98]=Z):Z=e[98];let ee;return e[99]!==h||e[100]!==Z||e[101]!==o?(ee=n.jsx(Ul,{scroll:v,rowKey:"id",columns:Z,showSorterTooltip:!1,dataSource:h,...o}),e[99]=h,e[100]=Z,e[101]=o,e[102]=ee):ee=e[102],ee},Fs=l=>{"use memo";var Ue,nl,Oe,Ge,Je,al,Ze,ol;const e=ll.c(125),{deploymentId:i,isEndpointDestroying:s,isOwnedByCurrentUser:t}=l,{t:a}=tl(),{message:d}=$l.useApp(),[r,o]=_.useTransition(),[u,m]=Pl(),[c,k]=_.useState(null),[h,v]=_.useState(!1),[g,y]=_.useState(null),[p,P]=yn("table_column_overrides.AutoScalingRuleList");let T,x;e[0]===Symbol.for("react.memo_cache_sentinel")?(T={order:nn(["createdAt","-createdAt"]).withDefault("-createdAt"),filter:Oa(Ts)},x={history:"replace"},e[0]=T,e[1]=x):(T=e[0],x=e[1]);const[D,E]=Vn(T,x),H=D.order,b=D.filter??void 0;let K;e[2]===Symbol.for("react.memo_cache_sentinel")?(K={current:1,pageSize:10},e[2]=K):K=e[2];const{baiPaginationOption:R,tablePaginationOption:C,setTablePaginationOption:A}=$a(K);let M;e[3]!==b?(M=b?un(b):null,e[3]=b,e[4]=M):M=e[4];const I=M,V=H.startsWith("-")?"DESC":"ASC";let L;e[5]!==V?(L=[{field:"CREATED_AT",direction:V}],e[5]=V,e[6]=L):L=e[6];let B;e[7]!==R.limit||e[8]!==R.offset||e[9]!==i||e[10]!==I||e[11]!==L?(B={deploymentId:i,offset:R.offset,limit:R.limit,orderBy:L,filter:I},e[7]=R.limit,e[8]=R.offset,e[9]=i,e[10]=I,e[11]=L,e[12]=B):B=e[12];const z=B,U=_.useDeferredValue(z);let $;e[13]===Symbol.for("react.memo_cache_sentinel")?($=Ut,e[13]=$):$=e[13];let S;e[14]!==u?(S={fetchPolicy:"store-and-network",fetchKey:u},e[14]=u,e[15]=S):S=e[15];const F=Ve.useLazyLoadQuery($,U,S);let O,Y;e[16]===Symbol.for("react.memo_cache_sentinel")?(O=zt,Y={},e[16]=O,e[17]=Y):(O=e[16],Y=e[17]);const{prometheusQueryPresets:X}=Ve.useLazyLoadQuery(O,Y);let ne;if(e[18]!==X){if(ne=new Map,X!=null&&X.edges)for(const Le of X.edges)Le!=null&&Le.node&&ne.set(Xe(Le.node.id),Le.node.name);e[18]=X,e[19]=ne}else ne=e[19];const N=ne;let j;e[20]!==((nl=(Ue=F==null?void 0:F.deployment)==null?void 0:Ue.autoScalingRules)==null?void 0:nl.edges)?(j=zl(bl((Ge=(Oe=F==null?void 0:F.deployment)==null?void 0:Oe.autoScalingRules)==null?void 0:Ge.edges,"node")),e[20]=(al=(Je=F==null?void 0:F.deployment)==null?void 0:Je.autoScalingRules)==null?void 0:al.edges,e[21]=j):j=e[21];const w=j,q=((ol=(Ze=F==null?void 0:F.deployment)==null?void 0:Ze.autoScalingRules)==null?void 0:ol.count)??0;let W;e[22]===Symbol.for("react.memo_cache_sentinel")?(W=qt,e[22]=W):W=e[22];const Z=nt(W);let ee;e[23]!==m?(ee=()=>{o(()=>{m()})},e[23]=m,e[24]=ee):ee=e[24];const G=ee;let Q;e[25]===Symbol.for("react.memo_cache_sentinel")?(Q=(Le,il)=>{y({id:Le,metricName:il})},e[25]=Q):Q=e[25];const Se=Q;let ce;e[26]===Symbol.for("react.memo_cache_sentinel")?(ce={flex:1},e[26]=ce):ce=e[26];let ae;e[27]!==a?(ae=a("autoScalingRule.CreatedAt"),e[27]=a,e[28]=ae):ae=e[28];let Me;e[29]===Symbol.for("react.memo_cache_sentinel")?(Me=["after","before"],e[29]=Me):Me=e[29];let Re;e[30]!==ae?(Re={key:"createdAt",propertyLabel:ae,type:"datetime",operators:Me,defaultOperator:"after"},e[30]=ae,e[31]=Re):Re=e[31];let ve;e[32]!==a?(ve=a("autoScalingRule.LastTriggered"),e[32]=a,e[33]=ve):ve=e[33];let me;e[34]===Symbol.for("react.memo_cache_sentinel")?(me=["after","before"],e[34]=me):me=e[34];let pe;e[35]!==ve?(pe={key:"lastTriggeredAt",propertyLabel:ve,type:"datetime",operators:me,defaultOperator:"after"},e[35]=ve,e[36]=pe):pe=e[36];let ge;e[37]!==Re||e[38]!==pe?(ge=[Re,pe],e[37]=Re,e[38]=pe,e[39]=ge):ge=e[39];let he;e[40]!==E||e[41]!==A?(he=Le=>{o(()=>{E({filter:Le??null}),A({current:1})})},e[40]=E,e[41]=A,e[42]=he):he=e[42];let Te;e[43]!==b||e[44]!==ge||e[45]!==he?(Te=n.jsx(tn,{style:ce,filterProperties:ge,value:b,onChange:he}),e[43]=b,e[44]=ge,e[45]=he,e[46]=Te):Te=e[46];let Fe;e[47]!==m?(Fe=()=>{o(()=>m())},e[47]=m,e[48]=Fe):Fe=e[48];let je;e[49]!==r||e[50]!==Fe?(je=n.jsx(wl,{loading:r,value:"",onChange:Fe}),e[49]=r,e[50]=Fe,e[51]=je):je=e[51];let fe;e[52]===Symbol.for("react.memo_cache_sentinel")?(fe=n.jsx(El,{}),e[52]=fe):fe=e[52];const Ie=s||!t;let ke;e[53]===Symbol.for("react.memo_cache_sentinel")?(ke=()=>{k(null),v(!0)},e[53]=ke):ke=e[53];let Ne;e[54]!==a?(Ne=a("modelService.AddRules"),e[54]=a,e[55]=Ne):Ne=e[55];let xe;e[56]!==Ie||e[57]!==Ne?(xe=n.jsx(pl,{type:"primary",icon:fe,disabled:Ie,onClick:ke,children:Ne}),e[56]=Ie,e[57]=Ne,e[58]=xe):xe=e[58];let de;e[59]!==Te||e[60]!==je||e[61]!==xe?(de=n.jsxs(ie,{align:"center",gap:"sm",children:[Te,je,xe]}),e[59]=Te,e[60]=je,e[61]=xe,e[62]=de):de=e[62];const Be=r||U!==z;let f;e[63]!==p||e[64]!==P?(f={columnOverrides:p,onColumnOverridesChange:P},e[63]=p,e[64]=P,e[65]=f):f=e[65];let J;e[66]!==E?(J=Le=>{o(()=>{E({order:Le||null})})},e[66]=E,e[67]=J):J=e[67];let le;e[68]!==A?(le=(Le,il)=>{A({current:Le,pageSize:il})},e[68]=A,e[69]=le):le=e[69];let te;e[70]!==le||e[71]!==C.current||e[72]!==C.pageSize||e[73]!==q?(te={pageSize:C.pageSize,current:C.current,total:q,onChange:le},e[70]=le,e[71]=C.current,e[72]=C.pageSize,e[73]=q,e[74]=te):te=e[74];let re;e[75]===Symbol.for("react.memo_cache_sentinel")?(re=Le=>{k(Le),v(!0)},e[75]=re):re=e[75];let se;e[76]!==w||e[77]!==s||e[78]!==t||e[79]!==H||e[80]!==N||e[81]!==Be||e[82]!==f||e[83]!==J||e[84]!==te?(se=n.jsx(vs,{autoScalingRulesFrgmt:w,presetMap:N,order:H,loading:Be,tableSettings:f,onChangeOrder:J,pagination:te,isEndpointDestroying:s,isOwnedByCurrentUser:t,onEditRule:re,onDeleteRule:Se}),e[76]=w,e[77]=s,e[78]=t,e[79]=H,e[80]=N,e[81]=Be,e[82]=f,e[83]=J,e[84]=te,e[85]=se):se=e[85];let Ke;e[86]!==de||e[87]!==se?(Ke=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[de,se]}),e[86]=de,e[87]=se,e[88]=Ke):Ke=e[88];let _e;e[89]!==i?(_e=Xe(i),e[89]=i,e[90]=_e):_e=e[90];let Ee;e[91]!==w||e[92]!==c?(Ee=c?w.find(Le=>Le.id===c)??null:null,e[91]=w,e[92]=c,e[93]=Ee):Ee=e[93];let De;e[94]!==G?(De=Le=>{v(!1),Le&&G()},e[94]=G,e[95]=De):De=e[95];let He;e[96]===Symbol.for("react.memo_cache_sentinel")?(He=()=>{k(null)},e[96]=He):He=e[96];let oe;e[97]!==h||e[98]!==_e||e[99]!==Ee||e[100]!==De?(oe=n.jsx(Sl,{children:n.jsx(us,{open:h,modelDeploymentId:_e,autoScalingRuleFrgmt:Ee,onRequestClose:De,afterClose:He})}),e[97]=h,e[98]=_e,e[99]=Ee,e[100]=De,e[101]=oe):oe=e[101];const Ce=!!g;let Pe;e[102]!==a?(Pe=a("autoScalingRule.DeleteAutoScalingRule"),e[102]=a,e[103]=Pe):Pe=e[103];let qe;e[104]!==a?(qe=a("autoScalingRule.DeleteConfirmation"),e[104]=a,e[105]=qe):qe=e[105];let ze;e[106]!==g?(ze=g?[{key:g.id,label:g.metricName}]:[],e[106]=g,e[107]=ze):ze=e[107];let Qe;e[108]!==Z||e[109]!==g||e[110]!==G||e[111]!==d||e[112]!==a?(Qe=()=>{if(g)return Z({input:{id:Xe(g.id)}}).then(()=>{y(null),G(),d.success({key:"autoscaling-rule-deleted",content:a("autoScalingRule.SuccessfullyDeleted")})}).catch(Le=>{const il=Array.isArray(Le)?Le:[Le];for(const dl of il)d.error((dl==null?void 0:dl.message)||a("dialog.ErrorOccurred"))})},e[108]=Z,e[109]=g,e[110]=G,e[111]=d,e[112]=a,e[113]=Qe):Qe=e[113];let We;e[114]===Symbol.for("react.memo_cache_sentinel")?(We=()=>y(null),e[114]=We):We=e[114];let be;e[115]!==Ce||e[116]!==Pe||e[117]!==qe||e[118]!==ze||e[119]!==Qe?(be=n.jsx(Pn,{open:Ce,title:Pe,description:qe,items:ze,reversible:!0,onOk:Qe,onCancel:We}),e[115]=Ce,e[116]=Pe,e[117]=qe,e[118]=ze,e[119]=Qe,e[120]=be):be=e[120];let ye;return e[121]!==Ke||e[122]!==oe||e[123]!==be?(ye=n.jsxs(n.Fragment,{children:[Ke,oe,be]}),e[121]=Ke,e[122]=oe,e[123]=be,e[124]=ye):ye=e[124],ye};function xs(l,e){if(!(e!=null&&e.stepSize))return"-";const i=e.minThreshold!=null,s=e.maxThreshold!=null;if(!i&&!s)return"-";const t=i&&s?"±":s?"+":"−";return n.jsxs(ie,{gap:"xs",children:[n.jsx(el.Text,{children:t}),n.jsx(el.Text,{children:Math.abs(e.stepSize)})]})}function bs(l,e){return n.jsx("span",{children:e!=null&&e.createdAt?ml(e.createdAt).format("ll LT"):"-"})}function Rs(l,e){return n.jsx("span",{children:e!=null&&e.lastTriggeredAt?ml.utc(e.lastTriggeredAt).tz().format("ll LTS"):"-"})}function Ts(l){return l}const Ks=l=>{"use memo";var E,H,b;const e=ll.c(24),{deploymentFrgmt:i}=l,{t:s}=tl(),{token:t}=Il.useToken(),[a]=ot();let d;e[0]===Symbol.for("react.memo_cache_sentinel")?(d=Qt,e[0]=d):d=e[0];const r=Ve.useFragment(d,i);if(!(r!=null&&r.id))return null;const o=(E=r.metadata)==null?void 0:E.status,u=((b=(H=r.creator)==null?void 0:H.basicInfo)==null?void 0:b.email)??null,m=!u||u===a.email;let c;e[1]!==s?(c=s("deployment.tab.AutoScaling"),e[1]=s,e[2]=c):c=e[2];let k;e[3]!==s?(k=s("deployment.tab.description.AutoScaling"),e[3]=s,e[4]=k):k=e[4];let h;e[5]!==t.colorTextDescription?(h=n.jsx(Mn,{style:{color:t.colorTextDescription}}),e[5]=t.colorTextDescription,e[6]=h):h=e[6];let v;e[7]!==k||e[8]!==h?(v=n.jsx(cl,{title:k,children:h}),e[7]=k,e[8]=h,e[9]=v):v=e[9];let g;e[10]!==c||e[11]!==v?(g=n.jsxs(ie,{gap:"xs",align:"center",children:[c,v]}),e[10]=c,e[11]=v,e[12]=g):g=e[12];let y;e[13]===Symbol.for("react.memo_cache_sentinel")?(y={body:{paddingTop:0}},e[13]=y):y=e[13];let p;e[14]===Symbol.for("react.memo_cache_sentinel")?(p=n.jsx(xl,{active:!0}),e[14]=p):p=e[14];const P=r.id;let T;e[15]!==o?(T=kl(o),e[15]=o,e[16]=T):T=e[16];let x;e[17]!==r.id||e[18]!==m||e[19]!==T?(x=n.jsx(_.Suspense,{fallback:p,children:n.jsx(Fs,{deploymentId:P,isEndpointDestroying:T,isOwnedByCurrentUser:m})}),e[17]=r.id,e[18]=m,e[19]=T,e[20]=x):x=e[20];let D;return e[21]!==x||e[22]!==g?(D=n.jsx(ln,{title:g,styles:y,children:x}),e[21]=x,e[22]=g,e[23]=D):D=e[23],D},Zt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentConfigurationSectionDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentConfigurationSectionDeleteMutation",selections:e},params:{cacheID:"ccb2e618fc149ec819f2dbee3d35c7a1",id:null,metadata:{},name:"DeploymentConfigurationSectionDeleteMutation",operationKind:"mutation",text:`mutation DeploymentConfigurationSectionDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();Zt.hash="739b8de15b5a7bdec89ece3d8628621f";const ea=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i=[l,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentConfigurationSection_deployment",selections:[l,{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[e],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"BAIDeploymentTagChips_metadata"}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:i,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:i,storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionHistoryTab_deployment"}],type:"ModelDeployment",abstractKey:null}}();ea.hash="021c9e11d0201fb948249c5b903b8992";const la=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},a=[i,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],d={alias:null,args:null,kind:"ScalarField",name:"previousRevisionId",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"activatedRevisionId",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},u=[o,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],m={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},k={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,o,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},h=[i,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:u,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[o,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:u,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[m,c,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},k],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[m,c,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},k],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[o,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,s,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:a,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:a,storageKey:null}],storageKey:null},d,r],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,s,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:h,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:h,storageKey:null}],storageKey:null},d,r],storageKey:null}]},params:{cacheID:"63303da8901ae3a9a0c9593e583089fd",id:null,metadata:{},name:"DeploymentRevisionHistoryTabActivateMutation",operationKind:"mutation",text:`mutation DeploymentRevisionHistoryTabActivateMutation(
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
`}}}();la.hash="153c096cf78b28827d7a04ef0f1610d4";const na=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},o=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},h={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},g={alias:null,args:null,concreteType:"ModelMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],storageKey:null},y={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[m,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},P=[v,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],T={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[m,v,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},x={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},D={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,r,{alias:null,args:o,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[m,c,k,h,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[v],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[v,g],storageKey:null}],storageKey:null},y,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[m,v,{args:null,kind:"FragmentSpread",name:"FolderLink_vfolderNode"}],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_revisionSource"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,s],kind:"Operation",name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[d,r,{alias:null,args:o,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[m,c,k,h,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[v,m],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:P,storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[v,g,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},y,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,T,x,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},D,{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:P,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[p,x,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},T],storageKey:null},y,D],storageKey:null}],storageKey:null}],storageKey:null},m],storageKey:null}]},params:{cacheID:"c7361c42ae45e53ccf5673bbc36622a6",id:null,metadata:{},name:"DeploymentRevisionHistoryTabListQuery",operationKind:"query",text:`query DeploymentRevisionHistoryTabListQuery(
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
          path
          maxRetries
          initialDelay
          interval
          maxWaitTime
        }
      }
    }
  }
  imageV2 {
    id
    identity {
      canonicalName
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
`}}}();na.hash="dc7544cf74c6e7b71663a4998c4d880c";const ta={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentAddRevisionModal_deployment"}],type:"ModelDeployment",abstractKey:null};ta.hash="6d00d8056ec0eba0eea404e554242adf";const Gn=["revisionNumber","createdAt","clusterMode","runtimeVariantName"],Is=[...Gn,...Gn.map(l=>`-${l}`)],As=({deploymentFrgmt:l,deploymentId:e,fetchKey:i})=>{"use memo";var ne;const{t:s}=tl(),{token:t}=Il.useToken(),{message:a}=$l.useApp(),{logger:d}=Wl(),[r,o]=_.useTransition(),[u,m]=_.useState(null),[c,k]=_.useState(null),[h,v]=_.useState(null),[g,y]=yn("table_column_overrides.DeploymentRevisionHistoryTab"),[p,P]=Vn({current:cn.withDefault(1),pageSize:cn.withDefault(10),order:nn(Is),rvFilter:ut},{history:"replace",urlKeys:{current:"rvCurrent",pageSize:"rvPageSize",order:"rvOrder",rvFilter:"rvFilter"}}),T=Ve.useFragment(ta,l),x=(ne=T==null?void 0:T.metadata)==null?void 0:ne.status,D=N=>{if(!N)return null;try{const j=JSON.parse(N);return j&&typeof j=="object"&&!Array.isArray(j)?j:null}catch{return null}},E=N=>!N||Object.keys(N).length===0?"":JSON.stringify(N),[H,b]=_.useState(()=>({filter:p.rvFilter?D(p.rvFilter):null,orderBy:ql(p.order)??[{field:"REVISION_NUMBER",direction:"DESC"}],limit:p.pageSize,offset:p.current>1?(p.current-1)*p.pageSize:0})),[K,R]=Pl(),C=`${i??""}${K}`,A=(i===void 0||i===Fn)&&K===Fn,{deployment:M}=Ve.useLazyLoadQuery(na,{deploymentId:e,...H},{fetchKey:C,fetchPolicy:A?"store-and-network":"network-only"}),[I]=Ve.useMutation(la),V=M==null?void 0:M.currentRevisionId,L=M==null?void 0:M.deployingRevisionId,B=M==null?void 0:M.revisionHistory,z=zl(bl(B==null?void 0:B.edges,"node")),U=N=>{o(()=>{b(j=>({...j,...N}))})},$=()=>{o(()=>R())},S=N=>new Promise(j=>{m(N.id),I({variables:{input:{deploymentId:Xe(T.id),revisionId:Xe(N.id)}},onCompleted:(w,q)=>{var W;if(m(null),q&&q.length>0){d.error(q[0]),a.error(((W=q[0])==null?void 0:W.message)||s("general.ErrorOccurred")),j(!1);return}a.success(s("deployment.ApplySuccess",{revisionNumber:N.revisionNumber})),$(),j(!0)},onError:w=>{m(null),d.error(w),a.error((w==null?void 0:w.message)||s("general.ErrorOccurred")),j(!1)}})}),F=[{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.RevisionNumberWithID"),n.jsx(fl,{title:s("deployment.RevisionNumberTooltip")})]}),dataIndex:"revisionNumber",key:"revisionNumber",fixed:"left",sorter:!0,render:(N,j)=>{const w=Xe(j.id),q=w===V,W=w===L,Z=q||W?s("deployment.ApplyDisabled"):void 0,ee=q||W||kl(x)||u===j.id;return n.jsx(jn,{title:n.jsxs(ie,{gap:"xs",align:"center",wrap:"nowrap",children:[n.jsx(el.Link,{onClick:()=>k({frgmt:j,status:q?"current":W?"deploying":"none"}),children:j.revisionNumber!=null?`#${j.revisionNumber}`:"-"}),n.jsxs(ie,{gap:0,align:"center",children:["(",n.jsx(Hl,{globalId:j.id}),")"]}),q?n.jsx(mn,{color:"success",children:s("deployment.Current")}):null,W&&!q?n.jsx(mn,{color:"warning",icon:n.jsx(_n,{spin:!0}),children:s("deployment.Applying")}):null]}),showActions:"always",moreMenuDisabled:kl(x),actions:[{key:"deploy",title:s("deployment.Apply"),icon:n.jsx(Bn,{}),disabled:ee,disabledReason:Z,popConfirm:{title:s("deployment.ApplyRevision"),description:s("deployment.ApplyConfirm",{revisionNumber:j.revisionNumber}),okText:s("deployment.Apply"),cancelText:s("button.Cancel"),okButtonProps:{danger:!0},onConfirm:()=>{S(j)}}},{key:"duplicate",title:s("deployment.AddNewRevisionFromThis"),icon:n.jsx(zn,{size:t.fontSize}),showInMenu:"always",disabled:kl(x),onClick:()=>{v(j)}}]})}},{title:s("general.CreatedAt"),dataIndex:"createdAt",key:"createdAt",sorter:!0,render:N=>N?ml(N).format("lll"):"-"},{title:s("deployment.ModelVersion"),key:"modelVersion",defaultHidden:!0,render:(N,j)=>{var ee,G,Q;const w=(G=(ee=j.modelDefinition)==null?void 0:ee.models)==null?void 0:G[0];if(!w)return"-";const q=w.name??"-",W=(Q=w.metadata)==null?void 0:Q.version,Z=typeof W=="string"?W:W!=null?String(W):null;return Z?`${q} (${Z})`:q}},{title:s("deployment.RuntimeVariant"),key:"runtimeVariantName",dataIndex:"runtimeVariantName",sorter:!0,render:(N,j)=>{var w,q;return((q=(w=j.modelRuntimeConfig)==null?void 0:w.runtimeVariant)==null?void 0:q.name)??"-"}},{title:s("deployment.Image"),key:"image",defaultHidden:!0,render:(N,j)=>{var Z,ee,G,Q;const w=(ee=(Z=j.imageV2)==null?void 0:Z.identity)==null?void 0:ee.canonicalName,q=(Q=(G=j.imageV2)==null?void 0:G.identity)==null?void 0:Q.architecture,W=w&&q?`${w}@${q}`:w;return W?n.jsx(Ol,{copyable:{text:W},ellipsis:{tooltip:W},style:{maxWidth:180},children:W}):"-"}},{title:s("deployment.ModelFolder"),key:"modelFolder",defaultHidden:!0,render:(N,j)=>{var W,Z;const w=(W=j.modelMountConfig)==null?void 0:W.vfolder,q=(Z=j.modelMountConfig)==null?void 0:Z.vfolderId;return!w&&!q?"-":w?n.jsx(ci,{vfolderNodeFragment:w}):n.jsx(el.Text,{type:"secondary",children:q})}},{title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.ClusterMode"),n.jsx(fl,{title:s("deployment.ClusterModeTooltip")})]}),key:"clusterMode",dataIndex:"clusterMode",sorter:!0,render:(N,j)=>{var W,Z;const w=(W=j.clusterConfig)==null?void 0:W.mode,q=(Z=j.clusterConfig)==null?void 0:Z.size;return w==null&&q==null?"-":w==null?`${q}`:q==null?w:`${w} / ${q}`}}],O={message:s("general.InvalidUUID"),validate:N=>Ha(N.toLowerCase())},Y=[{key:"revisionNumber",propertyLabel:s("deployment.RevisionNumber"),type:"number"},{key:"createdAt",propertyLabel:s("general.CreatedAt"),type:"datetime",operators:["after","before"],defaultOperator:"after"},{key:"clusterMode",propertyLabel:s("deployment.ClusterMode"),type:"string"},{key:"imageId",propertyLabel:s("deployment.Image"),type:"uuid",fixedOperator:"equals",rule:O},{key:"modelVfolderId",propertyLabel:s("deployment.ModelFolder"),type:"uuid",fixedOperator:"equals",rule:O}],X=p.rvFilter?D(p.rvFilter)??void 0:void 0;return n.jsxs(n.Fragment,{children:[n.jsx(Sl,{children:n.jsx(fn,{revisionFrgmt:c==null?void 0:c.frgmt,status:c==null?void 0:c.status,open:!!c,onClose:()=>k(null),extra:c?n.jsxs(en.Compact,{children:[n.jsx(Ba,{title:s("deployment.ApplyRevision"),description:s("deployment.ApplyConfirm",{revisionNumber:c.frgmt.revisionNumber}),okText:s("deployment.Apply"),cancelText:s("button.Cancel"),okButtonProps:{danger:!0},onConfirm:async()=>{await S(c.frgmt)&&k(null)},children:n.jsx(pl,{type:"primary",icon:n.jsx(Bn,{}),disabled:c.status==="current"||c.status==="deploying"||kl(x)||!!u,children:s("deployment.Apply")})}),n.jsx(dt,{trigger:["click"],menu:{items:[{key:"duplicate",label:s("deployment.AddNewRevisionFromThis"),icon:n.jsx(zn,{size:t.fontSize}),disabled:kl(x),onClick:()=>{const N=c.frgmt;k(null),v(N)}}]},children:n.jsx(pl,{type:"primary",icon:n.jsx(ct,{}),"aria-label":s("button.More"),disabled:kl(x)})})]}):void 0})}),n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:t.marginSM},wrap:"wrap",children:[n.jsx(tn,{filterProperties:Y,value:X,onChange:N=>{const j=E(N),w=D(j||null);P({rvFilter:j||null,current:1}),U({filter:w,offset:0})}}),n.jsx(wl,{loading:r,value:"",onChange:()=>$()})]}),n.jsx(Ul,{rowKey:"id",dataSource:z,columns:F,loading:r,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:g,onColumnOverridesChange:y},order:p.order??void 0,onChangeOrder:N=>{P({order:N}),U({orderBy:ql(N)})},pagination:{pageSize:p.pageSize,current:p.current,total:(B==null?void 0:B.count)??0,showSizeChanger:!0,onChange:(N,j)=>{const w=N>1?(N-1)*j:0;P({current:N,pageSize:j}),U({limit:j,offset:w})}}}),n.jsx(_.Suspense,{fallback:null,children:n.jsx(Sl,{children:n.jsx(Ht,{open:!!h,deploymentFrgmt:T,sourceRevisionFrgmt:h,onRequestClose:N=>{v(null),N&&$()}})})})]})},aa=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"orderBy"},i={defaultValue:null,kind:"LocalArgument",name:"scope"},s=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],t={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i],kind:"Fragment",metadata:null,name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:s,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIDeploymentSchedulingHistoryNodesFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[i,l,e],kind:"Operation",name:"DeploymentSchedulingHistoryModalQuery",selections:[{alias:null,args:s,concreteType:"DeploymentHistoryConnection",kind:"LinkedField",name:"deploymentScopedSchedulingHistories",plural:!1,selections:[{alias:null,args:null,concreteType:"DeploymentHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"DeploymentHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},t,a,d,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},t,a,d,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"6cc521a7daf46bd6ff23d8369e069d7c",id:null,metadata:{},name:"DeploymentSchedulingHistoryModalQuery",operationKind:"query",text:`query DeploymentSchedulingHistoryModalQuery(
  $scope: DeploymentScope!
  $filter: DeploymentHistoryFilter
  $orderBy: [DeploymentHistoryOrderBy!]
) {
  deploymentScopedSchedulingHistories(scope: $scope, filter: $filter, orderBy: $orderBy) {
    edges {
      node {
        ...BAIDeploymentSchedulingHistoryNodesFragment
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
  subSteps {
    ...BAISubStepNodesFragment
  }
  attempts
  createdAt
  updatedAt
}

fragment BAISubStepNodesFragment on SubStepResultGQL {
  step
  result
  errorCode
  message
  startedAt
  endedAt
}
`}}}();aa.hash="4386ab0845d3e5ba13c6f60075522b52";const ia=aa,Ds=l=>{"use memo";var Q,Se,ce;const e=ll.c(97);let i,s,t,a,d;e[0]!==l?({open:a,queryRef:d,onReload:t,onCancel:s,...i}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5]);const{t:r}=tl(),[o,u]=Pl(),[m,c]=_.useState(),[k,h]=_.useState("-updatedAt"),v=_.useDeferredValue(d),g=v!==d,y=Ve.usePreloadedQuery(ia,v);let p;e[6]!==r?(p=r("deployment.DeploymentSchedulingHistory"),e[6]=r,e[7]=p):p=e[7];let P,T;e[8]===Symbol.for("react.memo_cache_sentinel")?(P={maxWidth:1600},T={body:{minHeight:"80vh"}},e[8]=P,e[9]=T):(P=e[8],T=e[9]);let x;e[10]!==r?(x=r("button.Close"),e[10]=r,e[11]=x):x=e[11];let D;e[12]!==t||e[13]!==d.variables?(D=ae=>{c(ae),t({...d.variables,filter:ae},{fetchPolicy:"network-only"})},e[12]=t,e[13]=d.variables,e[14]=D):D=e[14];let E;e[15]!==r?(E=r("deployment.ID"),e[15]=r,e[16]=E):E=e[16];let H;e[17]!==E?(H={key:"id",propertyLabel:E,type:"uuid",fixedOperator:"equals"},e[17]=E,e[18]=H):H=e[18];let b;e[19]!==r?(b=r("deployment.Phase"),e[19]=r,e[20]=b):b=e[20];let K;e[21]!==b?(K={key:"phase",propertyLabel:b,type:"string",fixedOperator:"contains"},e[21]=b,e[22]=K):K=e[22];let R;e[23]!==r?(R=r("deployment.Result"),e[23]=r,e[24]=R):R=e[24];let C;e[25]===Symbol.for("react.memo_cache_sentinel")?(C=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=C):C=e[25];let A;e[26]!==R?(A={key:"result",propertyLabel:R,type:"enum",strictSelection:!0,options:C},e[26]=R,e[27]=A):A=e[27];let M;e[28]!==r?(M=r("deployment.FromStatus"),e[28]=r,e[29]=M):M=e[29];let I;e[30]!==M?(I={key:"fromStatus",propertyLabel:M,type:"string",valueMode:"scalar"},e[30]=M,e[31]=I):I=e[31];let V;e[32]!==r?(V=r("deployment.ToStatus"),e[32]=r,e[33]=V):V=e[33];let L;e[34]!==V?(L={key:"toStatus",propertyLabel:V,type:"string",valueMode:"scalar"},e[34]=V,e[35]=L):L=e[35];let B;e[36]!==r?(B=r("deployment.ErrorCode"),e[36]=r,e[37]=B):B=e[37];let z;e[38]!==B?(z={key:"errorCode",propertyLabel:B,type:"string",fixedOperator:"contains"},e[38]=B,e[39]=z):z=e[39];let U;e[40]!==r?(U=r("deployment.Message"),e[40]=r,e[41]=U):U=e[41];let $;e[42]!==U?($={key:"message",propertyLabel:U,type:"string",fixedOperator:"contains"},e[42]=U,e[43]=$):$=e[43];let S;e[44]!==r?(S=r("deployment.CreatedAt"),e[44]=r,e[45]=S):S=e[45];let F;e[46]!==S?(F={key:"createdAt",propertyLabel:S,type:"datetime",defaultOperator:"after"},e[46]=S,e[47]=F):F=e[47];let O;e[48]!==r?(O=r("deployment.UpdatedAt"),e[48]=r,e[49]=O):O=e[49];let Y;e[50]!==O?(Y={key:"updatedAt",propertyLabel:O,type:"datetime",defaultOperator:"after"},e[50]=O,e[51]=Y):Y=e[51];let X;e[52]!==A||e[53]!==I||e[54]!==L||e[55]!==z||e[56]!==$||e[57]!==F||e[58]!==Y||e[59]!==H||e[60]!==K?(X=[H,K,A,I,L,z,$,F,Y],e[52]=A,e[53]=I,e[54]=L,e[55]=z,e[56]=$,e[57]=F,e[58]=Y,e[59]=H,e[60]=K,e[61]=X):X=e[61];let ne;e[62]!==m||e[63]!==X||e[64]!==D?(ne=n.jsx(tn,{value:m,onChange:D,filterProperties:X}),e[62]=m,e[63]=X,e[64]=D,e[65]=ne):ne=e[65];let N;e[66]!==t||e[67]!==d.variables||e[68]!==u?(N=ae=>{u(ae),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=u,e[69]=N):N=e[69];let j;e[70]!==o||e[71]!==g||e[72]!==N?(j=n.jsx(ie,{children:n.jsx(wl,{value:o,onChange:N,loading:g,autoUpdateDelay:null})}),e[70]=o,e[71]=g,e[72]=N,e[73]=j):j=e[73];let w;e[74]!==ne||e[75]!==j?(w=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[ne,j]}),e[74]=ne,e[75]=j,e[76]=w):w=e[76];let q;e[77]!==t||e[78]!==d.variables?(q=ae=>{h(ae),t({...d.variables,orderBy:ql(ae)},{fetchPolicy:"network-only"})},e[77]=t,e[78]=d.variables,e[79]=q):q=e[79];let W;e[80]!==((Q=y.deploymentScopedSchedulingHistories)==null?void 0:Q.edges)?(W=bl((Se=y.deploymentScopedSchedulingHistories)==null?void 0:Se.edges,"node"),e[80]=(ce=y.deploymentScopedSchedulingHistories)==null?void 0:ce.edges,e[81]=W):W=e[81];let Z;e[82]!==g||e[83]!==k||e[84]!==q||e[85]!==W?(Z=n.jsx(bi,{resizable:!0,loading:g,order:k,onChangeOrder:q,schedulingHistoryFrgmt:W}),e[82]=g,e[83]=k,e[84]=q,e[85]=W,e[86]=Z):Z=e[86];let ee;e[87]!==w||e[88]!==Z?(ee=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[w,Z]}),e[87]=w,e[88]=Z,e[89]=ee):ee=e[89];let G;return e[90]!==i||e[91]!==s||e[92]!==a||e[93]!==p||e[94]!==ee||e[95]!==x?(G=n.jsx(Gl,{title:p,open:a,width:"90%",style:P,styles:T,cancelText:x,footer:Cs,onCancel:s,...i,children:ee}),e[90]=i,e[91]=s,e[92]=a,e[93]=p,e[94]=ee,e[95]=x,e[96]=G):G=e[96],G};function Cs(l,e){const{CancelBtn:i}=e;return n.jsx(i,{})}const Ml=()=>n.jsx(el.Text,{type:"secondary",children:"-"}),Ms=l=>{"use memo";var k,h,v;const e=ll.c(26),{deployment:i,onClickSchedulingHistoryAction:s}=l,{t}=tl(),a=pn(),d=mt(),r=((h=(k=i==null?void 0:i.metadata.projectV2)==null?void 0:k.basicInfo)==null?void 0:h.name)??(i==null?void 0:i.metadata.projectId);let o;if(e[0]!==i||e[1]!==d.pathname||e[2]!==s||e[3]!==r||e[4]!==t||e[5]!==a){const g=t("deployment.Visibility"),y=i==null?void 0:i.networkAccess.openToPublic;let p;e[7]!==t?(p=t("deployment.Public"),e[7]=t,e[8]=p):p=e[8];let P;e[9]!==t?(P=t("deployment.Private"),e[9]=t,e[10]=P):P=e[10];let T;e[11]===Symbol.for("react.memo_cache_sentinel")?(T=Ml(),e[11]=T):T=e[11];let x;e[12]!==y||e[13]!==p||e[14]!==P?(x=n.jsx(yi,{value:y,trueLabel:p,falseLabel:P,fallback:T}),e[12]=y,e[13]=p,e[14]=P,e[15]=x):x=e[15];const D=t("deployment.Tags"),E=(i==null?void 0:i.metadata)??null;let H;e[16]!==d.pathname||e[17]!==a?(H=R=>{const C=d.pathname.startsWith("/admin-deployments")?"/admin-deployments":d.pathname.startsWith("/project-admin-deployments")?"/project-admin-deployments":"/deployments";a({pathname:C,search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:R}})}).toString()})},e[16]=d.pathname,e[17]=a,e[18]=H):H=e[18];let b;e[19]===Symbol.for("react.memo_cache_sentinel")?(b=Ml(),e[19]=b):b=e[19];let K;e[20]!==H||e[21]!==E?(K=n.jsx(si,{metadataFrgmt:E,onTagClick:H,fallback:b}),e[20]=H,e[21]=E,e[22]=K):K=e[22],o=gn([{key:"status",label:t("deployment.Status"),children:i!=null&&i.metadata.status?n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(ft,{status:i.metadata.status}),s&&n.jsxs(n.Fragment,{children:[n.jsx(it,{type:"vertical",style:{margin:0}}),n.jsx(pl,{type:"link",size:"small",icon:n.jsx(vt,{}),style:{padding:0},action:async()=>{await s()},children:t("deployment.SchedulingHistory")})]})]}):Ml()},{key:"id",label:t("deployment.DeploymentId"),children:i!=null&&i.id?n.jsx(Hl,{globalId:i.id,copyable:!0,ellipsis:!1,style:{maxWidth:"none"}}):Ml()},{key:"project",label:t("deployment.Project"),children:r||Ml()},{key:"domain",label:t("deployment.Domain"),children:(i==null?void 0:i.metadata.domainName)||Ml()},{key:"resource-group",label:t("modelStore.ResourceGroup"),children:(i==null?void 0:i.metadata.resourceGroupName)||Ml()},{key:"endpoint-url",label:t("deployment.EndpointUrl"),children:i!=null&&i.networkAccess.endpointUrl?n.jsx(el.Text,{copyable:!0,style:{wordBreak:"break-all"},children:i.networkAccess.endpointUrl}):Ml()},{key:"visibility",label:g,children:x},{key:"desired-replicas",label:t("deployment.DesiredReplicas"),children:((v=i==null?void 0:i.replicaState)==null?void 0:v.desiredReplicaCount)??Ml()},{key:"tags",label:D,children:K}]),e[0]=i,e[1]=d.pathname,e[2]=s,e[3]=r,e[4]=t,e[5]=a,e[6]=o}else o=e[6];const u=o;let m;e[23]===Symbol.for("react.memo_cache_sentinel")?(m={xs:1,sm:1,md:2,lg:2,xl:2,xxl:2},e[23]=m):m=e[23];let c;return e[24]!==u?(c=n.jsx(Ga,{bordered:!0,column:m,items:u}),e[24]=u,e[25]=c):c=e[25],c},js=l=>{"use memo";const e=ll.c(181),{deploymentFrgmt:i,revisionFetchKey:s,isPendingRefetch:t,onRefetch:a,onAddRevision:d,revisionCardRef:r}=l,{t:o}=tl(),{token:u}=Il.useToken(),{message:m}=$l.useApp(),{logger:c}=Wl(),k=pn(),h=mt(),v=Nn();let g;e[0]===Symbol.for("react.memo_cache_sentinel")?(g=ea,e[0]=g):g=e[0];const y=Ve.useFragment(g,i),[p,P]=_.useState(null);let T;e[1]===Symbol.for("react.memo_cache_sentinel")?(T=nn(["currentRevision","revisionHistory","auditLog"]).withDefault("currentRevision"),e[1]=T):T=e[1];let x;e[2]===Symbol.for("react.memo_cache_sentinel")?(x={...T,history:"replace",scroll:!1},e[2]=x):x=e[2];const[D,E]=Qa("revisionTab",x),[H,b]=_.useState(!1),[K,R]=_.useState(!1),[C,A]=_.useState(!1),[M,I]=Ve.useQueryLoader(ia),[V,L]=Ve.useQueryLoader(mi);let B;e[3]===Symbol.for("react.memo_cache_sentinel")?(B={current:1,pageSize:10},e[3]=B):B=e[3];const{baiPaginationOption:z,setTablePaginationOption:U}=qa(B);let $;e[4]!==L||e[5]!==U?($=(Ye,_l)=>{const an=Ye.limit??10;U({pageSize:an,current:Ye.offset?Math.floor(Ye.offset/an)+1:1}),L(Ye,_l)},e[4]=L,e[5]=U,e[6]=$):$=e[6];const S=$;let F;e[7]!==z||e[8]!==y||e[9]!==L?(F=()=>{if(!(y!=null&&y.id))return;const Ye=y.id;L({scope:{entity:[{entityType:"MODEL_DEPLOYMENT",entityId:Ql(Ye)??Ye}]},orderBy:[{field:"CREATED_AT",direction:"DESC"}],limit:z.limit,offset:z.offset},{fetchPolicy:"store-and-network"})},e[7]=z,e[8]=y,e[9]=L,e[10]=F):F=e[10];const O=F;let Y;e[11]!==D||e[12]!==V||e[13]!==O?(Y=()=>{D==="auditLog"&&V==null&&O()},e[11]=D,e[12]=V,e[13]=O,e[14]=Y):Y=e[14];const X=_.useEffectEvent(Y);let ne;e[15]!==X?(ne=function(){X()},e[15]=X,e[16]=ne):ne=e[16];let N;e[17]===Symbol.for("react.memo_cache_sentinel")?(N=[],e[17]=N):N=e[17],_.useEffect(ne,N);const j=gt();let w;e[18]!==j?(w=(j==null?void 0:j.supports("deployment-scheduling-history"))??!1,e[18]=j,e[19]=w):w=e[19];const q=w;let W;e[20]===Symbol.for("react.memo_cache_sentinel")?(W=Zt,e[20]=W):W=e[20];const[Z,ee]=Ve.useMutation(W),G=(y==null?void 0:y.metadata.name)??"",Q=y==null?void 0:y.metadata.status,Se=h.pathname.startsWith("/admin-deployments")?"/admin-deployments":h.pathname.startsWith("/project-admin-deployments")?"/project-admin-deployments":"/deployments",ce=(y==null?void 0:y.metadata.projectId)??null,ae=!!ce&&ce!==v.id;let Me;e[21]!==Z||e[22]!==y||e[23]!==Se||e[24]!==c||e[25]!==m||e[26]!==o||e[27]!==k?(Me=()=>{y!=null&&y.id&&Z({variables:{input:{id:Xe(y.id)??y.id}},onCompleted:(Ye,_l)=>{if(_l&&_l.length>0){c.error("Failed to delete deployment",_l),m.error(o("deployment.FailedToDeleteDeployment"));return}m.success(o("deployment.DeploymentDeleted")),R(!1),k(Se)},onError:Ye=>{c.error("Failed to delete deployment",Ye),m.error(o("deployment.FailedToDeleteDeployment"))}})},e[21]=Z,e[22]=y,e[23]=Se,e[24]=c,e[25]=m,e[26]=o,e[27]=k,e[28]=Me):Me=e[28];const Re=Me;let ve;e[29]===Symbol.for("react.memo_cache_sentinel")?(ve=(Ye,_l,an)=>{P({revisionFrgmt:Ye,status:_l,title:an})},e[29]=ve):ve=e[29];const me=ve,pe=y==null?void 0:y.currentRevision,ge=y==null?void 0:y.deployingRevision,he=!!ge&&ge.id!==(pe==null?void 0:pe.id);za(a,he?5e3:null);let Te;e[30]!==o?(Te=o("deployment.BasicInformation"),e[30]=o,e[31]=Te):Te=e[31];let Fe;e[32]!==t||e[33]!==a?(Fe=n.jsx(wl,{loading:t,value:"",onChange:a}),e[32]=t,e[33]=a,e[34]=Fe):Fe=e[34];let je;e[35]===Symbol.for("react.memo_cache_sentinel")?(je=n.jsx(Ua,{}),e[35]=je):je=e[35];let fe;e[36]!==Q?(fe=kl(Q),e[36]=Q,e[37]=fe):fe=e[37];let Ie;e[38]===Symbol.for("react.memo_cache_sentinel")?(Ie=async()=>{b(!0)},e[38]=Ie):Ie=e[38];let ke;e[39]!==o?(ke=o("button.Edit"),e[39]=o,e[40]=ke):ke=e[40];let Ne;e[41]!==fe||e[42]!==ke?(Ne=n.jsx(pl,{icon:je,disabled:fe,action:Ie,children:ke}),e[41]=fe,e[42]=ke,e[43]=Ne):Ne=e[43];let xe;e[44]===Symbol.for("react.memo_cache_sentinel")?(xe=["click"],e[44]=xe):xe=e[44];let de;e[45]!==o?(de=o("deployment.DeleteDeployment"),e[45]=o,e[46]=de):de=e[46];let Be;e[47]===Symbol.for("react.memo_cache_sentinel")?(Be=n.jsx(Ln,{}),e[47]=Be):Be=e[47];let f;e[48]!==Q||e[49]!==ee?(f=kl(Q)||ee,e[48]=Q,e[49]=ee,e[50]=f):f=e[50];let J;e[51]===Symbol.for("react.memo_cache_sentinel")?(J=()=>R(!0),e[51]=J):J=e[51];let le;e[52]!==de||e[53]!==f?(le={items:[{key:"delete",label:de,icon:Be,danger:!0,disabled:f,onClick:J}]},e[52]=de,e[53]=f,e[54]=le):le=e[54];let te;e[55]===Symbol.for("react.memo_cache_sentinel")?(te=n.jsx(ct,{}),e[55]=te):te=e[55];let re;e[56]!==o?(re=o("button.More"),e[56]=o,e[57]=re):re=e[57];let se;e[58]!==re?(se=n.jsx(gl,{icon:te,"aria-label":re}),e[58]=re,e[59]=se):se=e[59];let Ke;e[60]!==le||e[61]!==se?(Ke=n.jsx(dt,{trigger:xe,menu:le,children:se}),e[60]=le,e[61]=se,e[62]=Ke):Ke=e[62];let _e;e[63]!==Ne||e[64]!==Ke?(_e=n.jsxs(en.Compact,{children:[Ne,Ke]}),e[63]=Ne,e[64]=Ke,e[65]=_e):_e=e[65];let Ee;e[66]!==Fe||e[67]!==_e?(Ee=n.jsxs(ie,{gap:"xs",align:"center",children:[Fe,_e]}),e[66]=Fe,e[67]=_e,e[68]=Ee):Ee=e[68];let De;e[69]===Symbol.for("react.memo_cache_sentinel")?(De={body:{paddingTop:0}},e[69]=De):De=e[69];let He;e[70]!==y||e[71]!==I||e[72]!==q?(He=q&&(y!=null&&y.id)?async()=>{const Ye=y.id;Ye&&(I({scope:{deploymentId:Ql(Ye)??Ye},orderBy:[{field:"UPDATED_AT",direction:"DESC"}]},{fetchPolicy:"store-and-network"}),A(!0))}:void 0,e[70]=y,e[71]=I,e[72]=q,e[73]=He):He=e[73];let oe;e[74]!==y||e[75]!==He?(oe=n.jsx(Ms,{deployment:y,onClickSchedulingHistoryAction:He}),e[74]=y,e[75]=He,e[76]=oe):oe=e[76];let Ce;e[77]!==Te||e[78]!==Ee||e[79]!==oe?(Ce=n.jsx(ln,{title:Te,extra:Ee,styles:De,children:oe}),e[77]=Te,e[78]=Ee,e[79]=oe,e[80]=Ce):Ce=e[80];let Pe;e[81]!==V||e[82]!==O||e[83]!==E?(Pe=Ye=>{(Ye==="currentRevision"||Ye==="revisionHistory"||Ye==="auditLog")&&(Ye==="auditLog"&&V==null&&O(),E(Ye))},e[81]=V,e[82]=O,e[83]=E,e[84]=Pe):Pe=e[84];let qe;e[85]!==o?(qe=o("deployment.CurrentRevision"),e[85]=o,e[86]=qe):qe=e[86];let ze;e[87]!==qe?(ze={key:"currentRevision",label:qe},e[87]=qe,e[88]=ze):ze=e[88];let Qe;e[89]!==o?(Qe=o("deployment.RevisionHistory"),e[89]=o,e[90]=Qe):Qe=e[90];let We;e[91]!==Qe?(We={key:"revisionHistory",label:Qe},e[91]=Qe,e[92]=We):We=e[92];let be;e[93]!==o?(be=o("auditLog.AuditLog"),e[93]=o,e[94]=be):be=e[94];let ye;e[95]!==be?(ye={key:"auditLog",label:be},e[95]=be,e[96]=ye):ye=e[96];let Ue;e[97]!==ze||e[98]!==We||e[99]!==ye?(Ue=[ze,We,ye],e[97]=ze,e[98]=We,e[99]=ye,e[100]=Ue):Ue=e[100];let nl;e[101]===Symbol.for("react.memo_cache_sentinel")?(nl=n.jsx(El,{}),e[101]=nl):nl=e[101];let Oe;e[102]!==Q||e[103]!==ae?(Oe=kl(Q)||ae,e[102]=Q,e[103]=ae,e[104]=Oe):Oe=e[104];let Ge;e[105]!==d?(Ge=async()=>{d()},e[105]=d,e[106]=Ge):Ge=e[106];let Je;e[107]!==o?(Je=o("deployment.AddRevision"),e[107]=o,e[108]=Je):Je=e[108];let al;e[109]!==Oe||e[110]!==Ge||e[111]!==Je?(al=n.jsx(ie,{gap:"xs",align:"center",children:n.jsx(pl,{type:"primary",icon:nl,disabled:Oe,action:Ge,children:Je})}),e[109]=Oe,e[110]=Ge,e[111]=Je,e[112]=al):al=e[112];let Ze;e[113]!==D||e[114]!==pe||e[115]!==ge||e[116]!==he||e[117]!==o||e[118]!==u?(Ze=D==="currentRevision"&&n.jsxs(n.Fragment,{children:[he&&n.jsx(Ll,{type:"info",icon:n.jsx(_n,{spin:!0}),showIcon:!0,style:{marginBottom:u.marginMD},title:o("deployment.ApplyingRevision",{revisionNumber:ge.revisionNumber!=null?`#${ge.revisionNumber}`:Xe(ge.id)??""}),action:n.jsx(gl,{onClick:()=>me(ge,"deploying",o("deployment.ApplyingRevisionDetail")),children:o("deployment.ViewRevision")})}),pe?n.jsx(ii,{revisionFrgmt:pe,status:"current"}):he?null:n.jsx(Hn,{image:Hn.PRESENTED_IMAGE_SIMPLE,description:o("deployment.NoCurrentRevisionDeployed")})]}),e[113]=D,e[114]=pe,e[115]=ge,e[116]=he,e[117]=o,e[118]=u,e[119]=Ze):Ze=e[119];let ol;e[120]!==D||e[121]!==y||e[122]!==s?(ol=D==="revisionHistory"&&y&&n.jsx(st,{children:n.jsx(_.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:4}}),children:n.jsx(As,{deploymentFrgmt:y,deploymentId:y.id,fetchKey:s})})}),e[120]=D,e[121]=y,e[122]=s,e[123]=ol):ol=e[123];let Le;e[124]!==D||e[125]!==V||e[126]!==y||e[127]!==S?(Le=D==="auditLog"&&y&&n.jsx(yt,{children:V?n.jsx(_.Suspense,{fallback:n.jsx(xl,{active:!0,paragraph:{rows:4}}),children:n.jsx(gi,{queryRef:V,onReload:S,tableSettings:{}})}):n.jsx(xl,{active:!0,paragraph:{rows:4}})}),e[124]=D,e[125]=V,e[126]=y,e[127]=S,e[128]=Le):Le=e[128];let il;e[129]!==D||e[130]!==r||e[131]!==Pe||e[132]!==Ue||e[133]!==al||e[134]!==Ze||e[135]!==ol||e[136]!==Le?(il=n.jsxs(ln,{ref:r,activeTabKey:D,onTabChange:Pe,tabList:Ue,tabBarExtraContent:al,children:[Ze,ol,Le]}),e[129]=D,e[130]=r,e[131]=Pe,e[132]=Ue,e[133]=al,e[134]=Ze,e[135]=ol,e[136]=Le,e[137]=il):il=e[137];let dl;e[138]!==a?(dl=Ye=>{b(!1),Ye&&a()},e[138]=a,e[139]=dl):dl=e[139];let Ae;e[140]!==y||e[141]!==H||e[142]!==dl?(Ae=n.jsx(Wa,{open:H,deploymentFrgmt:y,onRequestClose:dl}),e[140]=y,e[141]=H,e[142]=dl,e[143]=Ae):Ae=e[143];const we=p==null?void 0:p.revisionFrgmt,rl=p==null?void 0:p.status,sl=p==null?void 0:p.title,ul=!!p;let Rl;e[144]===Symbol.for("react.memo_cache_sentinel")?(Rl=()=>P(null),e[144]=Rl):Rl=e[144];let hl;e[145]!==we||e[146]!==rl||e[147]!==sl||e[148]!==ul?(hl=n.jsx(Sl,{children:n.jsx(fn,{revisionFrgmt:we,status:rl,title:sl,open:ul,onClose:Rl})}),e[145]=we,e[146]=rl,e[147]=sl,e[148]=ul,e[149]=hl):hl=e[149];let vl;e[150]!==o?(vl=o("deployment.DeleteDeployment"),e[150]=o,e[151]=vl):vl=e[151];let Fl;e[152]!==o?(Fl=o("deployment.Deployment"),e[152]=o,e[153]=Fl):Fl=e[153];let Al;e[154]!==G?(Al=G?[{key:G,label:G}]:[],e[154]=G,e[155]=Al):Al=e[155];let Dl;e[156]!==G?(Dl={placeholder:G},e[156]=G,e[157]=Dl):Dl=e[157];let Cl;e[158]!==ee?(Cl={loading:ee},e[158]=ee,e[159]=Cl):Cl=e[159];let Nl;e[160]===Symbol.for("react.memo_cache_sentinel")?(Nl=()=>R(!1),e[160]=Nl):Nl=e[160];let $e;e[161]!==G||e[162]!==Re||e[163]!==K||e[164]!==vl||e[165]!==Fl||e[166]!==Al||e[167]!==Dl||e[168]!==Cl?($e=n.jsx(Pn,{open:K,title:vl,target:Fl,items:Al,confirmText:G,requireConfirmInput:!0,inputProps:Dl,okButtonProps:Cl,onOk:Re,onCancel:Nl}),e[161]=G,e[162]=Re,e[163]=K,e[164]=vl,e[165]=Fl,e[166]=Al,e[167]=Dl,e[168]=Cl,e[169]=$e):$e=e[169];let jl;e[170]!==M||e[171]!==C||e[172]!==I?(jl=M!=null&&n.jsx(Sl,{children:n.jsx(Ds,{open:C,queryRef:M,onReload:I,onCancel:()=>A(!1)})}),e[170]=M,e[171]=C,e[172]=I,e[173]=jl):jl=e[173];let Vl;return e[174]!==Ce||e[175]!==il||e[176]!==Ae||e[177]!==hl||e[178]!==$e||e[179]!==jl?(Vl=n.jsxs(n.Fragment,{children:[Ce,il,Ae,hl,$e,jl]}),e[174]=Ce,e[175]=il,e[176]=Ae,e[177]=hl,e[178]=$e,e[179]=jl,e[180]=Vl):Vl=e[180],Vl},sa=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},s={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},a=[{kind:"Variable",name:"id",variableName:"deploymentId"}],d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"sessionId",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"revisionId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"trafficStatus",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"healthStatus",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},p={alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"sessionV2",plural:!1,selections:[o,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[y],storageKey:null}],storageKey:null},P=[y,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],T={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},x={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},D={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[o,y,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[l,e,i,s,t],kind:"Fragment",metadata:null,name:"DeploymentReplicasTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[o,u,m,c,k,h,v,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[o,g,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null},p],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,i,s],kind:"Operation",name:"DeploymentReplicasTabListQuery",selections:[{alias:null,args:a,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:d,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[o,u,m,c,k,h,v,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[o,g,v,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:P,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[y,o],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:P,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[T,x,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},D],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[T,x,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},D],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[y,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},p],storageKey:null}],storageKey:null}],storageKey:null},o],storageKey:null}]},params:{cacheID:"8241c83606821a73c83cc9a9d8814b88",id:null,metadata:{},name:"DeploymentReplicasTabListQuery",operationKind:"query",text:`query DeploymentReplicasTabListQuery(
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
`}}}();sa.hash="26b1dbb98e07f4bdd28168cb4a306efd";const ra={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentReplicasTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};ra.hash="6134739d7e3addb802e0658f5858bcea";const Ls={HEALTHY:"success",UNHEALTHY:"error",DEGRADED:"warning",NOT_CHECKED:"default",PROVISIONING:"info",WARMING_UP:"info",RUNNING:"success",TERMINATING:"warning",TERMINATED:"default",FAILED_TO_START:"error"},Ps={HEALTHY:"Healthy",UNHEALTHY:"Unhealthy",DEGRADED:"Degraded",NOT_CHECKED:"NotChecked",PROVISIONING:"Provisioning",WARMING_UP:"WarmingUp",RUNNING:"Running",TERMINATING:"Terminating",TERMINATED:"Terminated",FAILED_TO_START:"FailedToStart"},Yn=l=>{"use memo";const e=ll.c(23);let i,s,t;e[0]!==l?({status:i,showTooltip:s,...t}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t):(i=e[1],s=e[2],t=e[3]);const a=s===void 0?!0:s,{t:d}=tl(),r=Ls[i],o=Ps[i],u=`replicaStatus.${o}`;let m;e[4]!==d||e[5]!==u?(m=d(u),e[4]=d,e[5]=u,e[6]=m):m=e[6];const c=m;let k;e[7]!==o||e[8]!==a||e[9]!==d?(k=a?d(`replicaStatus.tooltip.${o}`,{defaultValue:""}):void 0,e[7]=o,e[8]=a,e[9]=d,e[10]=k):k=e[10];const h=k;let v;e[11]!==i?(v=i==="WARMING_UP"?n.jsx(_n,{spin:!0}):void 0,e[11]=i,e[12]=v):v=e[12];const g=v;let y;e[13]!==r||e[14]!==g||e[15]!==c||e[16]!==t?(y=n.jsx(mn,{...t,color:r,icon:g,children:c}),e[13]=r,e[14]=g,e[15]=c,e[16]=t,e[17]=y):y=e[17];const p=y;if(!a||!h)return p;let P;e[18]!==p?(P=n.jsx("span",{children:p}),e[18]=p,e[19]=P):P=e[19];let T;return e[20]!==P||e[21]!==h?(T=n.jsx(cl,{title:h,children:P}),e[20]=P,e[21]=h,e[22]=T):T=e[22],T},oa=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"orderBy"},i={defaultValue:null,kind:"LocalArgument",name:"scope"},s=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{kind:"Variable",name:"scope",variableName:"scope"}],t={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"errorCode",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"message",storageKey:null};return{fragment:{argumentDefinitions:[l,e,i],kind:"Fragment",metadata:null,name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:s,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIRouteSchedulingHistoryNodeTableFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[i,l,e],kind:"Operation",name:"RouteSchedulingHistoryModalQuery",selections:[{alias:null,args:s,concreteType:"RouteHistoryConnection",kind:"LinkedField",name:"routeScopedSchedulingHistories",plural:!1,selections:[{alias:null,args:null,concreteType:"RouteHistoryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RouteHistory",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"routeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"phase",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fromStatus",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"toStatus",storageKey:null},t,a,d,{alias:null,args:null,concreteType:"SubStepResultGQL",kind:"LinkedField",name:"subSteps",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null},t,a,d,{alias:null,args:null,kind:"ScalarField",name:"startedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endedAt",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"attempts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"5db4b1d03cdc23ddcee7e24da57e934d",id:null,metadata:{},name:"RouteSchedulingHistoryModalQuery",operationKind:"query",text:`query RouteSchedulingHistoryModalQuery(
  $scope: RouteScope!
  $filter: RouteHistoryFilter
  $orderBy: [RouteHistoryOrderBy!]
) {
  routeScopedSchedulingHistories(scope: $scope, filter: $filter, orderBy: $orderBy) {
    edges {
      node {
        ...BAIRouteSchedulingHistoryNodeTableFragment
        id
      }
    }
  }
}

fragment BAIRouteSchedulingHistoryNodeTableFragment on RouteHistory {
  id
  routeId
  deploymentId
  category
  phase
  fromStatus
  toStatus
  result
  errorCode
  message
  subSteps {
    ...BAISubStepNodesFragment
  }
  attempts
  createdAt
  updatedAt
}

fragment BAISubStepNodesFragment on SubStepResultGQL {
  step
  result
  errorCode
  message
  startedAt
  endedAt
}
`}}}();oa.hash="d718b55942730d51c42ce434352c4e59";const ua=oa,Ns=l=>{"use memo";var Q,Se,ce;const e=ll.c(97);let i,s,t,a,d;e[0]!==l?({open:a,queryRef:d,onReload:t,onCancel:s,...i}=l,e[0]=l,e[1]=i,e[2]=s,e[3]=t,e[4]=a,e[5]=d):(i=e[1],s=e[2],t=e[3],a=e[4],d=e[5]);const{t:r}=tl(),[o,u]=Pl(),[m,c]=_.useState(),[k,h]=_.useState("-updatedAt"),v=_.useDeferredValue(d),g=v!==d,y=Ve.usePreloadedQuery(ua,v);let p;e[6]!==r?(p=r("route.RouteSchedulingHistory"),e[6]=r,e[7]=p):p=e[7];let P,T;e[8]===Symbol.for("react.memo_cache_sentinel")?(P={maxWidth:1600},T={body:{minHeight:"80vh"}},e[8]=P,e[9]=T):(P=e[8],T=e[9]);let x;e[10]!==r?(x=r("button.Close"),e[10]=r,e[11]=x):x=e[11];let D;e[12]!==t||e[13]!==d.variables?(D=ae=>{c(ae),t({...d.variables,filter:ae},{fetchPolicy:"network-only"})},e[12]=t,e[13]=d.variables,e[14]=D):D=e[14];let E;e[15]!==r?(E=r("route.ID"),e[15]=r,e[16]=E):E=e[16];let H;e[17]!==E?(H={key:"id",propertyLabel:E,type:"uuid",fixedOperator:"equals"},e[17]=E,e[18]=H):H=e[18];let b;e[19]!==r?(b=r("route.Phase"),e[19]=r,e[20]=b):b=e[20];let K;e[21]!==b?(K={key:"phase",propertyLabel:b,type:"string",fixedOperator:"contains"},e[21]=b,e[22]=K):K=e[22];let R;e[23]!==r?(R=r("route.Result"),e[23]=r,e[24]=R):R=e[24];let C;e[25]===Symbol.for("react.memo_cache_sentinel")?(C=[{label:"SUCCESS",value:"SUCCESS"},{label:"FAILURE",value:"FAILURE"},{label:"STALE",value:"STALE"},{label:"NEED_RETRY",value:"NEED_RETRY"},{label:"EXPIRED",value:"EXPIRED"},{label:"GIVE_UP",value:"GIVE_UP"},{label:"SKIPPED",value:"SKIPPED"}],e[25]=C):C=e[25];let A;e[26]!==R?(A={key:"result",propertyLabel:R,type:"enum",strictSelection:!0,options:C},e[26]=R,e[27]=A):A=e[27];let M;e[28]!==r?(M=r("route.FromStatus"),e[28]=r,e[29]=M):M=e[29];let I;e[30]!==M?(I={key:"fromStatus",propertyLabel:M,type:"string",valueMode:"scalar"},e[30]=M,e[31]=I):I=e[31];let V;e[32]!==r?(V=r("route.ToStatus"),e[32]=r,e[33]=V):V=e[33];let L;e[34]!==V?(L={key:"toStatus",propertyLabel:V,type:"string",valueMode:"scalar"},e[34]=V,e[35]=L):L=e[35];let B;e[36]!==r?(B=r("route.ErrorCode"),e[36]=r,e[37]=B):B=e[37];let z;e[38]!==B?(z={key:"errorCode",propertyLabel:B,type:"string",fixedOperator:"contains"},e[38]=B,e[39]=z):z=e[39];let U;e[40]!==r?(U=r("route.Message"),e[40]=r,e[41]=U):U=e[41];let $;e[42]!==U?($={key:"message",propertyLabel:U,type:"string",fixedOperator:"contains"},e[42]=U,e[43]=$):$=e[43];let S;e[44]!==r?(S=r("route.CreatedAt"),e[44]=r,e[45]=S):S=e[45];let F;e[46]!==S?(F={key:"createdAt",propertyLabel:S,type:"datetime",defaultOperator:"after"},e[46]=S,e[47]=F):F=e[47];let O;e[48]!==r?(O=r("route.UpdatedAt"),e[48]=r,e[49]=O):O=e[49];let Y;e[50]!==O?(Y={key:"updatedAt",propertyLabel:O,type:"datetime",defaultOperator:"after"},e[50]=O,e[51]=Y):Y=e[51];let X;e[52]!==A||e[53]!==I||e[54]!==L||e[55]!==z||e[56]!==$||e[57]!==F||e[58]!==Y||e[59]!==H||e[60]!==K?(X=[H,K,A,I,L,z,$,F,Y],e[52]=A,e[53]=I,e[54]=L,e[55]=z,e[56]=$,e[57]=F,e[58]=Y,e[59]=H,e[60]=K,e[61]=X):X=e[61];let ne;e[62]!==m||e[63]!==X||e[64]!==D?(ne=n.jsx(tn,{value:m,onChange:D,filterProperties:X}),e[62]=m,e[63]=X,e[64]=D,e[65]=ne):ne=e[65];let N;e[66]!==t||e[67]!==d.variables||e[68]!==u?(N=ae=>{u(ae),t(d.variables,{fetchPolicy:"network-only"})},e[66]=t,e[67]=d.variables,e[68]=u,e[69]=N):N=e[69];let j;e[70]!==o||e[71]!==g||e[72]!==N?(j=n.jsx(ie,{children:n.jsx(wl,{value:o,onChange:N,loading:g,autoUpdateDelay:null})}),e[70]=o,e[71]=g,e[72]=N,e[73]=j):j=e[73];let w;e[74]!==ne||e[75]!==j?(w=n.jsxs(ie,{justify:"between",wrap:"wrap",gap:"sm",children:[ne,j]}),e[74]=ne,e[75]=j,e[76]=w):w=e[76];let q;e[77]!==t||e[78]!==d.variables?(q=ae=>{h(ae),t({...d.variables,orderBy:ql(ae)},{fetchPolicy:"network-only"})},e[77]=t,e[78]=d.variables,e[79]=q):q=e[79];let W;e[80]!==((Q=y.routeScopedSchedulingHistories)==null?void 0:Q.edges)?(W=bl((Se=y.routeScopedSchedulingHistories)==null?void 0:Se.edges,"node"),e[80]=(ce=y.routeScopedSchedulingHistories)==null?void 0:ce.edges,e[81]=W):W=e[81];let Z;e[82]!==g||e[83]!==k||e[84]!==q||e[85]!==W?(Z=n.jsx(ji,{resizable:!0,loading:g,order:k,onChangeOrder:q,schedulingHistoryFrgmt:W}),e[82]=g,e[83]=k,e[84]=q,e[85]=W,e[86]=Z):Z=e[86];let ee;e[87]!==w||e[88]!==Z?(ee=n.jsxs(ie,{direction:"column",align:"stretch",gap:"sm",children:[w,Z]}),e[87]=w,e[88]=Z,e[89]=ee):ee=e[89];let G;return e[90]!==i||e[91]!==s||e[92]!==a||e[93]!==p||e[94]!==ee||e[95]!==x?(G=n.jsx(Gl,{title:p,open:a,width:"90%",style:P,styles:T,cancelText:x,footer:Vs,onCancel:s,...i,children:ee}),e[90]=i,e[91]=s,e[92]=a,e[93]=p,e[94]=ee,e[95]=x,e[96]=G):G=e[96],G};function Vs(l,e){const{CancelBtn:i}=e;return n.jsx(i,{})}const Xn=["TERMINATED","FAILED_TO_START"],_s=l=>l==="terminated"?{status:{in:[...Xn]}}:{status:{notIn:[...Xn]}},hn=(l,e)=>({...l,..._s(e)}),Kn=["createdAt","id"],Es=[...Kn,...Kn.map(l=>`-${l}`)],Jn=l=>Cn(Kn,l),Zn=l=>l??"NOT_CHECKED",Os=({deploymentFrgmt:l,deploymentId:e,replicaFetchKey:i})=>{"use memo";var B,z,U,$;const{t:s}=tl(),[t,a]=_.useTransition(),[d,r]=yn("table_column_overrides.DeploymentReplicasTab"),[o,u]=Vn({current:cn.withDefault(1),pageSize:cn.withDefault(10),order:nn(Es),rFilter:ut,rStatusCategory:nn(["running","terminated"]).withDefault("running")},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rOrder",rFilter:"rFilter",rStatusCategory:"rStatusCategory"}});Ve.useFragment(ra,l);const m=S=>{if(!S)return null;try{const F=JSON.parse(S);return F&&typeof F=="object"&&!Array.isArray(F)?F:null}catch{return null}},c=S=>!S||Object.keys(S).length===0?"":JSON.stringify(S),[k,h]=_.useState(()=>({filter:hn(o.rFilter?m(o.rFilter):null,o.rStatusCategory),orderBy:ql(o.order||"-createdAt"),limit:o.pageSize,offset:o.current>1?(o.current-1)*o.pageSize:0})),[v,g]=_.useState(0),p=gt().supports("route-scheduling-history"),[P,T]=_.useState(!1),[x,D]=Ve.useQueryLoader(ua),[E,H]=_.useState(null),[b,K]=_.useState(null),{deployment:R}=Ve.useLazyLoadQuery(sa,{deploymentId:e,...k},{fetchKey:`${v}-${i??""}`,fetchPolicy:"network-only"}),C=((U=(z=(B=R==null?void 0:R.replicas)==null?void 0:B.edges)==null?void 0:z.map(S=>S==null?void 0:S.node))==null?void 0:U.filter(S=>!!S))??[],A=S=>{a(()=>{h(F=>({...F,...S}))})},M=[{label:s("replicaStatus.Active"),value:"ACTIVE"},{label:s("replicaStatus.Inactive"),value:"INACTIVE"}],I=[{key:"trafficStatus",propertyLabel:s("deployment.TrafficStatus"),type:"enum",options:M,strictSelection:!0}],V=o.rFilter?m(o.rFilter)??void 0:void 0,L=gn([{key:"id",title:s("deployment.ReplicaId"),dataIndex:"id",fixed:"left",sorter:Jn("id"),render:S=>n.jsx(Hl,{globalId:S,copyable:!0})},{key:"status",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("general.Status"),n.jsx(fl,{title:s("deployment.ReplicaLifecycleStatusTooltip")})]}),dataIndex:"status",render:(S,F)=>n.jsxs(ie,{align:"center",gap:"xs",children:[n.jsx(Yn,{status:Zn(S)}),p&&n.jsx(cl,{title:s("route.RouteSchedulingHistory"),children:n.jsx(pl,{type:"link",icon:n.jsx(vt,{}),size:"small",style:{padding:0},action:async()=>{const O=Ql(F.id)??F.id;D({scope:{routeId:O},orderBy:[{field:"UPDATED_AT",direction:"DESC"}]},{fetchPolicy:"store-and-network"}),T(!0)}})})]})},{key:"healthStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.HealthStatus"),n.jsx(fl,{title:s("deployment.HealthStatusTooltip")})]}),dataIndex:"healthStatus",render:S=>n.jsx(Yn,{status:Zn(S)})},{key:"trafficStatus",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.TrafficStatus"),n.jsx(fl,{title:s("deployment.TrafficStatusTooltip")})]}),dataIndex:"trafficStatus",render:S=>n.jsx(mn,{color:S==="ACTIVE"?"success":"default",children:s(S==="ACTIVE"?"replicaStatus.Active":"replicaStatus.Inactive")})},{key:"session",title:s("general.Session"),onCell:()=>({style:{maxWidth:240}}),render:(S,F)=>{var X;const O=F.sessionV2;if(!(O!=null&&O.id))return n.jsx(el.Text,{type:"secondary",children:"—"});const Y=(X=O.metadata)==null?void 0:X.name;return Y?n.jsxs(n.Fragment,{children:[n.jsx(Ya,{ellipsis:!0,onClick:()=>H(Xe(O.id)),style:{maxWidth:160},children:Y})," ",n.jsxs(el.Text,{type:"secondary",children:["(",n.jsx(Hl,{globalId:O.id,type:"secondary"}),")"]})]}):n.jsx(Hl,{globalId:O.id})}},{key:"revision",title:n.jsxs(ie,{gap:"xxs",align:"center",children:[s("deployment.RevisionNumberWithID"),n.jsx(fl,{title:s("deployment.RevisionNumberTooltip")})]}),render:(S,F)=>{const O=F.revision;return O!=null&&O.id?n.jsxs(n.Fragment,{children:[n.jsx(el.Link,{onClick:()=>K(O),children:O.revisionNumber!=null?`#${O.revisionNumber}`:"-"})," ",n.jsxs(el.Text,{type:"secondary",children:["(",n.jsx(Hl,{globalId:O.id,type:"secondary"}),")"]})]}):n.jsx(el.Text,{type:"secondary",children:"—"})}},{key:"createdAt",title:s("deployment.CreatedAt"),dataIndex:"createdAt",sorter:Jn("createdAt"),render:S=>S?ml(S).format("lll"):"-"}]);return n.jsxs(n.Fragment,{children:[n.jsxs(ie,{justify:"between",align:"center",gap:"xs",style:{marginBottom:12},children:[n.jsxs(ie,{gap:"sm",align:"start",wrap:"wrap",style:{flexShrink:1},children:[n.jsx(Xa,{value:o.rStatusCategory,onChange:S=>{const F=S.target.value,O=o.rFilter?m(o.rFilter):null;u({rStatusCategory:F,current:1}),A({filter:hn(O,F),offset:0})},options:[{label:s("deployment.Running"),value:"running"},{label:s("deployment.status.Terminated"),value:"terminated"}]}),n.jsx(tn,{filterProperties:I,value:V,onChange:S=>{const F=c(S);u({rFilter:F||null,current:1}),A({filter:hn(S??null,o.rStatusCategory),offset:0})}})]}),n.jsx(wl,{loading:t,value:"",onChange:()=>{a(()=>g(S=>S+1))}})]}),n.jsx(Ul,{rowKey:S=>S.id,dataSource:C,columns:L,loading:t,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:d,onColumnOverridesChange:r},order:o.order,onChangeOrder:S=>{u({order:S??null}),A({orderBy:ql(S||"-createdAt")})},pagination:{pageSize:o.pageSize,current:o.current,total:(($=R==null?void 0:R.replicas)==null?void 0:$.count)??0,onChange:(S,F)=>{u({current:S,pageSize:F});const O=S>1?(S-1)*F:0;A({limit:F,offset:O})}}}),n.jsx(Sl,{children:n.jsx(di,{open:!!E,sessionId:E??void 0,onClose:()=>H(null)})}),n.jsx(Sl,{children:n.jsx(fn,{open:!!b,revisionFrgmt:b,onClose:()=>K(null)})}),x!=null&&n.jsx(Sl,{children:n.jsx(Ns,{open:P,queryRef:x,onReload:D,onCancel:()=>T(!1)})})]})},da=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"projectId"}],e=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"projectId"}],concreteType:"GroupNode",kind:"LinkedField",name:"group_node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"SwitchToProjectButtonQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"SwitchToProjectButtonQuery",selections:e},params:{cacheID:"d9b043a52eacadb018a0097fe3c1f3c2",id:null,metadata:{},name:"SwitchToProjectButtonQuery",operationKind:"query",text:`query SwitchToProjectButtonQuery(
  $projectId: String!
) {
  group_node(id: $projectId) @since(version: "24.03.0") {
    id
    name
  }
}
`}}}();da.hash="4618e2aed2bc3c75a1d0a91f0b01c28c";const $s=l=>{"use memo";const e=ll.c(20);let i,s;e[0]!==l?({projectId:s,...i}=l,e[0]=l,e[1]=i,e[2]=s):(i=e[1],s=e[2]);const{t}=tl(),a=Ja(),[d,r]=_.useTransition();let o;e[3]===Symbol.for("react.memo_cache_sentinel")?(o=da,e[3]=o):o=e[3];let u;e[4]!==s?(u=Zl("GroupNode",s),e[4]=s,e[5]=u):u=e[5];let m;e[6]!==u?(m={projectId:u},e[6]=u,e[7]=m):m=e[7];const{group_node:c}=Ve.useLazyLoadQuery(o,m);let k;e[8]!==(c==null?void 0:c.id)||e[9]!==(c==null?void 0:c.name)||e[10]!==a?(k=()=>{const p=Xe((c==null?void 0:c.id)||""),P=c==null?void 0:c.name;p&&P&&r(()=>{a({projectId:p,projectName:P})})},e[8]=c==null?void 0:c.id,e[9]=c==null?void 0:c.name,e[10]=a,e[11]=k):k=e[11];const h=k,v=c==null?void 0:c.name;let g;e[12]!==t||e[13]!==v?(g=t("modelService.SwitchToProject",{projectName:v}),e[12]=t,e[13]=v,e[14]=g):g=e[14];let y;return e[15]!==i||e[16]!==h||e[17]!==d||e[18]!==g?(y=n.jsx(pl,{type:"link",size:"small",loading:d,onClick:h,...i,children:g}),e[15]=i,e[16]=h,e[17]=d,e[18]=g,e[19]=y):y=e[19],y},ws=l=>n.jsx(_.Suspense,{fallback:n.jsx(pl,{type:"link",size:"small",loading:!0}),children:n.jsx($s,{...l})}),ir=()=>{"use memo";var oe,Ce,Pe,qe,ze,Qe,We,be,ye,Ue,nl;const l=ll.c(115),{t:e}=tl(),{token:i}=Il.useToken(),[s]=ot(),t=pn(),a=rt(),d=Nn();let r;l[0]!==((oe=a==null?void 0:a._config)==null?void 0:oe.blockList)?(r=(Pe=(Ce=a==null?void 0:a._config)==null?void 0:Ce.blockList)==null?void 0:Pe.includes("chat"),l[0]=(qe=a==null?void 0:a._config)==null?void 0:qe.blockList,l[1]=r):r=l[1];const o=!!r,{deploymentId:u}=Za(),m=u??"";let c;l[2]!==m?(c=Zl("ModelDeployment",m),l[2]=m,l[3]=c):c=l[3];const k=c,[h,v]=_.useTransition(),[g,y]=Pl(),[p,P]=Pl(),[T,x]=Pl(),[D,E]=Qn(!1),{setLeft:H,setRight:b}=E,[K,R]=Qn(!1),{setLeft:C,setRight:A}=R,M=_.useRef(null),I=_.useRef(null),[V,L]=_.useState(null);let B;l[4]===Symbol.for("react.memo_cache_sentinel")?(B=Tt,l[4]=B):B=l[4];let z;l[5]!==k?(z={deploymentId:k},l[5]=k,l[6]=z):z=l[6];const U=g===Fn?"store-and-network":"network-only";let $;l[7]!==g||l[8]!==U?($={fetchKey:g,fetchPolicy:U},l[7]=g,l[8]=U,l[9]=$):$=l[9];const{deployment:S}=Ve.useLazyLoadQuery(B,z,$);if(!S.ok){const Oe=S.errors;if(Oe.some(Hs)){let Ze;return l[10]===Symbol.for("react.memo_cache_sentinel")?(Ze=n.jsx(Bs,{}),l[10]=Ze):Ze=l[10],Ze}const Je=Oe.map(Qs).filter(Boolean),al=new Error(Je.join("; ")||"DeploymentDetailPageQuery failed.");throw al.errors=Oe,al}const F=S.value,O=F.metadata.name,Y=F.metadata.status,X=Y==="READY",ne=F.metadata.projectId??null,N=!!ne&&ne!==d.id,j=!F.currentRevision&&!F.deployingRevision,w=!!F.networkAccess.endpointUrl,q=(((ze=F.accessTokens)==null?void 0:ze.count)??0)>0;let W;l[11]!==Y?(W=kl(Y),l[11]=Y,l[12]=W):W=l[12];const Z=W,ee=F.networkAccess.openToPublic===!1&&!Z&&w&&!q,G=((We=(Qe=F.creator)==null?void 0:Qe.basicInfo)==null?void 0:We.email)??null,Q=!G||G===s.email;let Se;l[13]!==y?(Se=()=>{v(()=>y())},l[13]=y,l[14]=Se):Se=l[14];const ce=Se;let ae;l[15]!==H||l[16]!==((be=i.Layout)==null?void 0:be.headerHeight)||l[17]!==y||l[18]!==x||l[19]!==P?(ae=(Oe,Ge)=>{var Je;H(),Oe&&(Ge&&L(Ge),v(()=>{y(),P(),x()}),M.current&&(M.current.style.scrollMarginTop=`${((Je=i.Layout)==null?void 0:Je.headerHeight)??60}px`,M.current.scrollIntoView({behavior:"smooth",block:"start"})))},l[15]=H,l[16]=(ye=i.Layout)==null?void 0:ye.headerHeight,l[17]=y,l[18]=x,l[19]=P,l[20]=ae):ae=l[20];const Me=ae;let Re;l[21]!==ne||l[22]!==N||l[23]!==e?(Re=N&&ne&&n.jsx(Ll,{type:"warning",showIcon:!0,title:e("deployment.NotInProject"),action:n.jsx(ws,{projectId:ne})}),l[21]=ne,l[22]=N,l[23]=e,l[24]=Re):Re=l[24];let ve;l[25]!==m||l[26]!==j||l[27]!==o||l[28]!==X||l[29]!==e||l[30]!==i.fontSizeLG||l[31]!==t?(ve=X&&!j&&n.jsx(Ll,{type:"success",showIcon:!0,title:e("deployment.DeploymentReady"),action:!o&&n.jsx(gl,{type:"primary",icon:n.jsx(ei,{size:i.fontSizeLG}),onClick:()=>{t({pathname:"/chat",search:new URLSearchParams({endpointId:m}).toString()})},children:e("deployment.StartChatTest")})}),l[25]=m,l[26]=j,l[27]=o,l[28]=X,l[29]=e,l[30]=i.fontSizeLG,l[31]=t,l[32]=ve):ve=l[32];let me;l[33]!==Y||l[34]!==j||l[35]!==N||l[36]!==b||l[37]!==e?(me=j&&!N&&!kl(Y)&&n.jsx(Ll,{type:"warning",showIcon:!0,title:e("deployment.NoCurrentRevisionDeployed"),action:n.jsx(pl,{type:"primary",icon:n.jsx(El,{}),action:async()=>{b()},children:e("deployment.AddRevision")})}),l[33]=Y,l[34]=j,l[35]=N,l[36]=b,l[37]=e,l[38]=me):me=l[38];let pe;l[39]!==Z||l[40]!==ee||l[41]!==A||l[42]!==e?(pe=ee&&n.jsx(Ll,{type:"info",showIcon:!0,title:e("deployment.PrivateDeploymentAlertTitle"),action:n.jsx(pl,{type:"primary",icon:n.jsx(El,{}),action:async()=>{A()},disabled:Z,children:e("deployment.AddAccessToken")})}),l[39]=Z,l[40]=ee,l[41]=A,l[42]=e,l[43]=pe):pe=l[43];let ge;l[44]===Symbol.for("react.memo_cache_sentinel")?(ge={margin:0},l[44]=ge):ge=l[44];let he;l[45]!==O?(he=n.jsx(el.Title,{level:3,style:ge,children:O}),l[45]=O,l[46]=he):he=l[46];let Te;l[47]!==Y?(Te=n.jsx(ft,{status:Y}),l[47]=Y,l[48]=Te):Te=l[48];let Fe;l[49]!==he||l[50]!==Te?(Fe=n.jsxs(ie,{direction:"row",align:"center",gap:"sm",children:[he,Te]}),l[49]=he,l[50]=Te,l[51]=Fe):Fe=l[51];let je;l[52]!==F||l[53]!==ce||l[54]!==h||l[55]!==b||l[56]!==p?(je=n.jsx(js,{deploymentFrgmt:F,revisionFetchKey:p,isPendingRefetch:h,onRefetch:ce,onAddRevision:b,revisionCardRef:M}),l[52]=F,l[53]=ce,l[54]=h,l[55]=b,l[56]=p,l[57]=je):je=l[57];let fe;l[58]!==e?(fe=e("deployment.tab.Replicas"),l[58]=e,l[59]=fe):fe=l[59];let Ie;l[60]!==e?(Ie=e("deployment.tab.description.Replicas"),l[60]=e,l[61]=Ie):Ie=l[61];let ke;l[62]!==i.colorTextDescription?(ke=n.jsx(Mn,{style:{color:i.colorTextDescription}}),l[62]=i.colorTextDescription,l[63]=ke):ke=l[63];let Ne;l[64]!==Ie||l[65]!==ke?(Ne=n.jsx(cl,{title:Ie,children:ke}),l[64]=Ie,l[65]=ke,l[66]=Ne):Ne=l[66];let xe;l[67]!==fe||l[68]!==Ne?(xe=n.jsxs(ie,{gap:"xs",align:"center",children:[fe,Ne]}),l[67]=fe,l[68]=Ne,l[69]=xe):xe=l[69];let de;l[70]===Symbol.for("react.memo_cache_sentinel")?(de={body:{paddingTop:0}},l[70]=de):de=l[70];let Be;l[71]===Symbol.for("react.memo_cache_sentinel")?(Be=n.jsx(xl,{active:!0}),l[71]=Be):Be=l[71];let f;l[72]!==F||l[73]!==k||l[74]!==T?(f=n.jsx(yt,{children:n.jsx(_.Suspense,{fallback:Be,children:n.jsx(Os,{deploymentFrgmt:F,deploymentId:k,replicaFetchKey:T})})}),l[72]=F,l[73]=k,l[74]=T,l[75]=f):f=l[75];let J;l[76]!==xe||l[77]!==f?(J=n.jsx(ln,{title:xe,styles:de,children:f}),l[76]=xe,l[77]=f,l[78]=J):J=l[78];let le;l[79]!==F?(le=n.jsx(Ks,{deploymentFrgmt:F}),l[79]=F,l[80]=le):le=l[80];let te;l[81]!==C||l[82]!==A?(te=Oe=>{Oe?A():C()},l[81]=C,l[82]=A,l[83]=te):te=l[83];let re;l[84]!==ce||l[85]!==((Ue=i.Layout)==null?void 0:Ue.headerHeight)?(re=()=>{var Oe;ce(),I.current&&(I.current.style.scrollMarginTop=`${((Oe=i.Layout)==null?void 0:Oe.headerHeight)??60}px`,I.current.scrollIntoView({behavior:"smooth",block:"start"}))},l[84]=ce,l[85]=(nl=i.Layout)==null?void 0:nl.headerHeight,l[86]=re):re=l[86];let se;l[87]!==K||l[88]!==F||l[89]!==k||l[90]!==Z||l[91]!==Q||l[92]!==te||l[93]!==re?(se=n.jsx(wi,{cardRef:I,deploymentFrgmt:F,deploymentId:k,isOwnedByCurrentUser:Q,isDeploymentDestroying:Z,isCreateModalOpen:K,onCreateModalOpenChange:te,onTokenCreated:re}),l[87]=K,l[88]=F,l[89]=k,l[90]=Z,l[91]=Q,l[92]=te,l[93]=re,l[94]=se):se=l[94];let Ke;l[95]!==D||l[96]!==F||l[97]!==Me?(Ke=n.jsx(Sl,{children:n.jsx(Ht,{open:D,onRequestClose:Me,deploymentFrgmt:F})}),l[95]=D,l[96]=F,l[97]=Me,l[98]=Ke):Ke=l[98];const _e=!!V;let Ee;l[99]===Symbol.for("react.memo_cache_sentinel")?(Ee=()=>L(null),l[99]=Ee):Ee=l[99];let De;l[100]!==V||l[101]!==_e?(De=n.jsx(Sl,{children:n.jsx(fn,{revisionFrgmt:V,open:_e,onClose:Ee})}),l[100]=V,l[101]=_e,l[102]=De):De=l[102];let He;return l[103]!==Re||l[104]!==ve||l[105]!==me||l[106]!==pe||l[107]!==Fe||l[108]!==je||l[109]!==J||l[110]!==le||l[111]!==se||l[112]!==Ke||l[113]!==De?(He=n.jsxs(ie,{direction:"column",align:"stretch",gap:"md",children:[Re,ve,me,pe,Fe,je,J,le,se,Ke,De]}),l[103]=Re,l[104]=ve,l[105]=me,l[106]=pe,l[107]=Fe,l[108]=je,l[109]=J,l[110]=le,l[111]=se,l[112]=Ke,l[113]=De,l[114]=He):He=l[114],He},Bs=()=>{"use memo";const l=ll.c(39),{t:e}=tl(),i=pn(),{firstAvailableMenuItem:s}=li();let t;l[0]!==s?(t=s?ni(s.key):"/start",l[0]=s,l[1]=t):t=l[1];const a=t;let d,r,o,u,m,c,k,h,v,g,y;if(l[2]!==a||l[3]!==(s==null?void 0:s.labelText)||l[4]!==e||l[5]!==i){const x=(s==null?void 0:s.labelText)??e("webui.menu.FirstPageNameAlias");o=ie,l[17]===Symbol.for("react.memo_cache_sentinel")?(v={margin:"auto"},l[17]=v):v=l[17],g="center",y="center",r=ti,k="warning",l[18]!==e?(h=e("deployment.NotAccessibleOrDeleted"),l[18]=e,l[19]=h):h=l[19],d=gl,u="primary",l[20]!==a||l[21]!==i?(m=()=>{i(a)},l[20]=a,l[21]=i,l[22]=m):m=l[22],c=e("button.GoBackToStartPage",{title:x}),l[2]=a,l[3]=s==null?void 0:s.labelText,l[4]=e,l[5]=i,l[6]=d,l[7]=r,l[8]=o,l[9]=u,l[10]=m,l[11]=c,l[12]=k,l[13]=h,l[14]=v,l[15]=g,l[16]=y}else d=l[6],r=l[7],o=l[8],u=l[9],m=l[10],c=l[11],k=l[12],h=l[13],v=l[14],g=l[15],y=l[16];let p;l[23]!==d||l[24]!==u||l[25]!==m||l[26]!==c?(p=n.jsx(d,{type:u,onClick:m,children:c}),l[23]=d,l[24]=u,l[25]=m,l[26]=c,l[27]=p):p=l[27];let P;l[28]!==r||l[29]!==k||l[30]!==h||l[31]!==p?(P=n.jsx(r,{status:k,title:h,extra:p}),l[28]=r,l[29]=k,l[30]=h,l[31]=p,l[32]=P):P=l[32];let T;return l[33]!==o||l[34]!==P||l[35]!==v||l[36]!==g||l[37]!==y?(T=n.jsx(o,{style:v,justify:g,align:y,children:P}),l[33]=o,l[34]=P,l[35]=v,l[36]=g,l[37]=y,l[38]=T):T=l[38],T};function Hs(l){return/Insufficient permission/i.test((l==null?void 0:l.message)??"")}function Qs(l){return(l==null?void 0:l.message)??""}export{ir as default};
//# sourceMappingURL=DeploymentDetailPage-BCT9Twel.js.map
