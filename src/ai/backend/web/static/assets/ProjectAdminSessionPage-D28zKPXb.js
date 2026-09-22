import{i as Ee,u as Re,ac as on,Y as un,a$ as dn,l as $,aT as Ze,r as _e,dc as cn,bo as mn,dd as gn,j as l,a9 as fn,c as Ie,t as en,d as Ne,a3 as He,am as pn,O as yn,cE as Sn,b_ as kn,A as Fn,cr as Tn,aV as Ye,bG as bn,ah as In,ca as Je,af as hn,aO as Kn,a as jn,a8 as Vn,aS as An,cb as Ln,N as xn,hR as Xe,bh as Cn,de as vn,dx as Bn,ej as Pn,bI as Mn,ai as _n}from"./index-Dd8bt51s.js";import{a as Nn,s as En,g as Rn,B as On}from"./sessionStatusBuckets-DbmNcNIk.js";import{B as $n}from"./BAIUserSelect-BvFo0nz_.js";import{B as Dn}from"./BAIGraphQLPropertyFilter-DFTNvxk2.js";import"./BAITag-D3A3qz0g.js";const nn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},t={defaultValue:null,kind:"LocalArgument",name:"offset"},a={defaultValue:null,kind:"LocalArgument",name:"orderBy"},o={defaultValue:null,kind:"LocalArgument",name:"projectId"},s=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},c=[C],j=[{alias:null,args:null,concreteType:"ResourceSlotEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],F=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}];return{fragment:{argumentDefinitions:[n,e,t,a,o],kind:"Fragment",metadata:null,name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:s,concreteType:"SessionV2Connection",kind:"LinkedField",name:"projectSessionsV2",plural:!1,selections:[d,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:c,storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISessionNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalForProjectAdminFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[o,n,a,e,t],kind:"Operation",name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:s,concreteType:"SessionV2Connection",kind:"LinkedField",name:"projectSessionsV2",plural:!1,selections:[d,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[C,{alias:null,args:null,kind:"ScalarField",name:"sessionType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:c,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2LifecycleInfo",kind:"LinkedField",name:"lifecycle",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminatedAt",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ResourceAllocation",kind:"LinkedField",name:"allocation",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"requested",plural:!1,selections:j,storageKey:null},{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"used",plural:!1,selections:j,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2Connection",kind:"LinkedField",name:"images",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:F,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:F,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[r,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"e894bcd148585ed26646f2638d53ee35",id:null,metadata:{},name:"ProjectAdminSessionPageQuery",operationKind:"query",text:`query ProjectAdminSessionPageQuery(
  $projectId: UUID!
  $filter: SessionV2Filter
  $orderBy: [SessionV2OrderBy!]
  $limit: Int
  $offset: Int
) {
  projectSessionsV2(scope: {projectId: $projectId}, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        metadata {
          name
        }
        ...BAISessionNodesV2Fragment
        ...TerminateSessionModalForProjectAdminFragment
      }
    }
  }
}

fragment BAIImageNodeSimpleTagV2Fragment on ImageV2 {
  identity {
    canonicalName
    architecture
  }
  metadata {
    tags {
      key
      value
    }
    labels {
      key
      value
    }
  }
}

fragment BAISessionClusterModeV2Fragment on SessionV2MetadataInfo {
  clusterMode
  clusterSize
}

fragment BAISessionNodesV2Fragment on SessionV2 {
  id
  project {
    id
    basicInfo {
      name
    }
  }
  metadata {
    name
    ...BAISessionTypeTagV2Fragment
    ...BAISessionClusterModeV2Fragment
  }
  lifecycle {
    status
    createdAt
    terminatedAt
  }
  resource {
    resourceGroupName
    allocation {
      requested {
        entries {
          resourceType
          quantity
        }
      }
      used {
        entries {
          resourceType
          quantity
        }
      }
    }
  }
  images {
    edges {
      node {
        id
        ...BAIImageNodeSimpleTagV2Fragment
      }
    }
  }
  user {
    id
    basicInfo {
      email
    }
  }
}

fragment BAISessionTypeTagV2Fragment on SessionV2MetadataInfo {
  sessionType
}

fragment TerminateSessionModalForProjectAdminFragment on SessionV2 {
  id
  metadata {
    name
  }
  kernels {
    edges {
      node {
        id
        resource {
          agentId
          containerId
        }
      }
    }
  }
}
`}}})();nn.hash="0319d10e5f67b53895012b3e1c631bde";const ln=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"forced"},e={defaultValue:null,kind:"LocalArgument",name:"sessionIds"},t=[{alias:null,args:[{kind:"Variable",name:"forced",variableName:"forced"},{kind:"Variable",name:"sessionIds",variableName:"sessionIds"}],concreteType:"TerminateSessionsPayload",kind:"LinkedField",name:"terminateSessionsV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"cancelled",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminating",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"forceTerminated",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"skipped",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e],kind:"Fragment",metadata:null,name:"TerminateSessionModalForProjectAdminMutation",selections:t,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n],kind:"Operation",name:"TerminateSessionModalForProjectAdminMutation",selections:t},params:{cacheID:"be4736b37ff54351dd17b8f5d312c2bd",id:null,metadata:{},name:"TerminateSessionModalForProjectAdminMutation",operationKind:"mutation",text:`mutation TerminateSessionModalForProjectAdminMutation(
  $sessionIds: [ID!]!
  $forced: Boolean!
) {
  terminateSessionsV2(sessionIds: $sessionIds, forced: $forced) {
    cancelled
    terminating
    forceTerminated
    skipped
  }
}
`}}})();ln.hash="8c1ab011f362b60cae0d0e3b7c59bf7e";const an=(function(){var n={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"TerminateSessionModalForProjectAdminFragment",selections:[n,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[n,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"SessionV2",abstractKey:null}})();an.hash="7f806d407dac1670a060b0f1979cba15";const wn=n=>{"use memo";var D,x;const e=Ee.c(27);let t,a,o;e[0]!==n?({sessionsFrgmt:o,onRequestClose:a,...t}=n,e[0]=n,e[1]=t,e[2]=a,e[3]=o):(t=e[1],a=e[2],o=e[3]);const{t:s}=Re(),{token:d}=on.useToken(),{message:r}=un.useApp(),C=dn(),[c,j]=$.useState(!1);let F;e[4]===Symbol.for("react.memo_cache_sentinel")?(F=an,e[4]=F):F=e[4];const p=Ze(_e.useFragment(F,o));let y;e[5]===Symbol.for("react.memo_cache_sentinel")?(y=ln,e[5]=y):y=e[5];const[v,S]=_e.useMutation(y);let V;e[6]!==a?(V=g=>{j(!1),a(g)},e[6]=a,e[7]=V):V=e[7];const T=V,u=cn(mn(gn(p,Un)),Qn);let m;e[8]!==s?(m=s("session.TerminateSession"),e[8]=s,e[9]=m):m=e[9];let b;e[10]!==c||e[11]!==s?(b=s(c?"button.ForceTerminate":"session.Terminate"),e[10]=c,e[11]=s,e[12]=b):b=e[12];const I=c?"primary":"default";let B;e[13]!==I?(B={type:I},e[13]=I,e[14]=B):B=e[14];let A;e[15]!==T?(A=()=>T(!1),e[15]=T,e[16]=A):A=e[16];let P;e[17]!==s?(P=s("userSettings.SessionTerminationDialog"),e[17]=s,e[18]=P):P=e[18];let M;e[19]!==P?(M=l.jsx(He,{children:P}),e[19]=P,e[20]=M):M=e[20];let h;e[21]!==s?(h=s("button.ForceTerminate"),e[21]=s,e[22]=h):h=e[22];let _;e[23]===Symbol.for("react.memo_cache_sentinel")?(_=g=>j(g),e[23]=_):_=e[23];let L;return e[24]!==c||e[25]!==h?(L=l.jsx(Sn,{label:h,value:c,onChange:_}),e[24]=c,e[25]=h,e[26]=L):L=e[26],l.jsx(fn,{centered:!0,title:m,okText:b,okType:"danger",okButtonProps:B,confirmLoading:S,onOk:()=>{if(p.length===0){T(!1);return}v({variables:{sessionIds:p.map(zn),forced:c},onCompleted:(g,K)=>{var E;if(K&&K.length>0){r.error(((E=K[0])==null?void 0:E.message)??s("general.ErrorOccurred"));return}r.success(s("session.SessionTerminated")),T(!0)},onError:g=>{r.error(g.message)}})},onCancel:A,...t,children:l.jsxs(Ie,{className:"terminate-session-modal-admin-list",direction:"column",align:"stretch",gap:"xs",children:[M,l.jsx(en,{mark:!0,children:p.length===1?((x=(D=p[0])==null?void 0:D.metadata)==null?void 0:x.name)??"":`${p.length} sessions`}),L,c&&l.jsxs(Ne,{styles:{body:{padding:d.padding}},children:[l.jsx(He,{as:"p",display:"block",color:"danger",children:s("session.ForceTerminateWarningMsg")}),l.jsxs("ul",{children:[l.jsx("li",{children:s("session.ForceTerminateWarningMsg2")}),l.jsx("li",{children:s("session.ForceTerminateWarningMsg3")})]}),C==="superadmin"&&l.jsx(Ne,{type:"inner",title:s("session.ContainerToCleanUp"),children:pn(u,Wn)})]})]})})};function qn(n){return n==null?void 0:n.node}function Un(n){var e,t;return(t=(e=n.kernels)==null?void 0:e.edges)==null?void 0:t.map(qn)}function Qn(n){var e;return((e=n==null?void 0:n.resource)==null?void 0:e.agentId)??"-"}function zn(n){return yn(n.id)}function Gn(n){var e;return l.jsx("li",{children:l.jsx(en,{copyable:!0,children:((e=n==null?void 0:n.resource)==null?void 0:e.containerId)??""})},n==null?void 0:n.id)}function Wn(n,e){return l.jsxs(kn.Fragment,{children:[e,l.jsx("ul",{children:n.map(Gn)})]},e)}const Hn=n=>{"use memo";var we,qe,Ue,Qe,ze;const e=Ee.c(130),{projectId:t}=n,{t:a}=Re();let o;e[0]===Symbol.for("react.memo_cache_sentinel")?(o=[],e[0]=o):o=e[0];const[s,d]=$.useState(o);let r;e[1]===Symbol.for("react.memo_cache_sentinel")?(r=[],e[1]=r):r=e[1];const[C,c]=$.useState(r),[j,F]=$.useState(!1);let p;e[2]===Symbol.for("react.memo_cache_sentinel")?(p={current:1,pageSize:10},e[2]=p):p=e[2];const{baiPaginationOption:y,tablePaginationOption:v,setTablePaginationOption:S}=bn(p);let V,T;e[3]===Symbol.for("react.memo_cache_sentinel")?(V={statusCategory:Je(En).withDefault("running"),order:Je(Nn),filter:In(Yn)},T={history:"replace"},e[3]=V,e[4]=T):(V=e[3],T=e[4]);const[u,m]=hn(V,T),[b,I]=Kn(),B=jn();let A;e[5]!==B?(A=Rn(B.supports("session-preemption-statuses")),e[5]=B,e[6]=A):A=e[6];const P=A,[M,h]=Vn("table_column_overrides.ProjectAdminSessionPage"),_=P[u.statusCategory];let L;e[7]!==_?(L={in:_},e[7]=_,e[8]=L):L=e[8];const D=L;let x;e[9]!==u.filter?(x=u.filter??{},e[9]=u.filter,e[10]=x):x=e[10];let g;e[11]!==D||e[12]!==x?(g={...x,status:D},e[11]=D,e[12]=x,e[13]=g):g=e[13];let K;e[14]!==u.order?(K=An(u.order)??[{field:"CREATED_AT",direction:"DESC"}],e[14]=u.order,e[15]=K):K=e[15];let E;e[16]!==y.limit||e[17]!==y.offset||e[18]!==t||e[19]!==g||e[20]!==K?(E={projectId:t,filter:g,orderBy:K,limit:y.limit,offset:y.offset},e[16]=y.limit,e[17]=y.offset,e[18]=t,e[19]=g,e[20]=K,e[21]=E):E=e[21];const Oe=E,$e=$.useDeferredValue(Oe),be=$.useDeferredValue(b);let he;e[22]===Symbol.for("react.memo_cache_sentinel")?(he=nn,e[22]=he):he=e[22];const Be=be===Cn?"store-and-network":"network-only";let Ke;e[23]!==be||e[24]!==Be?(Ke={fetchKey:be,fetchPolicy:Be},e[23]=be,e[24]=Be,e[25]=Ke):Ke=e[25];const je=_e.useLazyLoadQuery(he,$e,Ke);let Ve;e[26]!==((we=je.projectSessionsV2)==null?void 0:we.edges)?(Ve=Ze((Ue=(qe=je.projectSessionsV2)==null?void 0:qe.edges)==null?void 0:Ue.map(Jn)),e[26]=(Qe=je.projectSessionsV2)==null?void 0:Qe.edges,e[27]=Ve):Ve=e[27];const k=Ve,Pe=((ze=je.projectSessionsV2)==null?void 0:ze.count)??0;let Ae;e[28]===Symbol.for("react.memo_cache_sentinel")?(Ae=i=>{c(i),F(!0)},e[28]=Ae):Ae=e[28];const De=Ae,w=$e!==Oe||be!==b;let Le;e[29]===Symbol.for("react.memo_cache_sentinel")?(Le={flexShrink:1},e[29]=Le):Le=e[29];const sn=u.statusCategory;let q;e[30]!==m||e[31]!==S?(q=i=>{m({statusCategory:i.target.value}),S({current:1})},e[30]=m,e[31]=S,e[32]=q):q=e[32];let U;e[33]!==a?(U=a("session.Running"),e[33]=a,e[34]=U):U=e[34];let Q;e[35]!==U?(Q={label:U,value:"running"},e[35]=U,e[36]=Q):Q=e[36];let z;e[37]!==a?(z=a("session.Finished"),e[37]=a,e[38]=z):z=e[38];let G;e[39]!==z?(G={label:z,value:"finished"},e[39]=z,e[40]=G):G=e[40];let W;e[41]!==Q||e[42]!==G?(W=[Q,G],e[41]=Q,e[42]=G,e[43]=W):W=e[43];let H;e[44]!==u.statusCategory||e[45]!==q||e[46]!==W?(H=l.jsx(vn,{optionType:"button",value:sn,onChange:q,options:W}),e[44]=u.statusCategory,e[45]=q,e[46]=W,e[47]=H):H=e[47];let xe;e[48]===Symbol.for("react.memo_cache_sentinel")?(xe={key:"id",propertyLabel:"ID",type:"uuid"},e[48]=xe):xe=e[48];let Y;e[49]!==a?(Y=a("session.SessionName"),e[49]=a,e[50]=Y):Y=e[50];let J;e[51]!==Y?(J={key:"name",propertyLabel:Y,type:"string"},e[51]=Y,e[52]=J):J=e[52];let X;e[53]!==a?(X=a("session.Owner"),e[53]=a,e[54]=X):X=e[54];let Z;e[55]!==a?(Z=i=>{const{onAddCondition:f,value:Fe,isDisabled:N}=i;return l.jsx($n,{valuePropName:"id",label:a("session.Owner"),isLabelHidden:!0,value:Fe,isDisabled:N,onChange:(R,O)=>{var Te;return f(R,Array.isArray(O)?(Te=O[0])==null?void 0:Te.label:O==null?void 0:O.label)}})},e[55]=a,e[56]=Z):Z=e[56];let ee;e[57]!==X||e[58]!==Z?(ee={key:"userUuid",propertyLabel:X,type:"uuid",renderInput:Z},e[57]=X,e[58]=Z,e[59]=ee):ee=e[59];let ne;e[60]!==J||e[61]!==ee?(ne=[xe,J,ee],e[60]=J,e[61]=ee,e[62]=ne):ne=e[62];const Me=u.filter??void 0;let le;e[63]!==m||e[64]!==S?(le=i=>{m({filter:i??null}),S({current:1})},e[63]=m,e[64]=S,e[65]=le):le=e[65];let ae;e[66]!==ne||e[67]!==Me||e[68]!==le?(ae=l.jsx(Dn,{filterProperties:ne,value:Me,onChange:le}),e[66]=ne,e[67]=Me,e[68]=le,e[69]=ae):ae=e[69];let se;e[70]!==H||e[71]!==ae?(se=l.jsxs(Ie,{gap:"sm",align:"start",wrap:"wrap",style:Le,children:[H,ae]}),e[70]=H,e[71]=ae,e[72]=se):se=e[72];let te;e[73]!==s||e[74]!==a?(te=s.length>0&&l.jsxs(l.Fragment,{children:[l.jsx(Ln,{count:s.length,onClearSelection:()=>d([])}),l.jsx(xn,{label:a("session.TerminateSession"),tooltip:a("session.TerminateSession"),icon:l.jsx(Xe,{color:"var(--color-error)"}),onClick:()=>De(s)})]}),e[73]=s,e[74]=a,e[75]=te):te=e[75];let ie;e[76]!==I?(ie=i=>I(i),e[76]=I,e[77]=ie):ie=e[77];let re;e[78]!==b||e[79]!==w||e[80]!==ie?(re=l.jsx(Bn,{settingId:"project-admin-session",defaultAutoUpdateDelay:15e3,loading:w,value:b,onChange:ie}),e[78]=b,e[79]=w,e[80]=ie,e[81]=re):re=e[81];let oe;e[82]!==te||e[83]!==re?(oe=l.jsxs(Ie,{gap:"xs",children:[te,re]}),e[82]=te,e[83]=re,e[84]=oe):oe=e[84];let ue;e[85]!==se||e[86]!==oe?(ue=l.jsxs(Ie,{direction:"row",justify:"between",wrap:"wrap",gap:"sm",children:[se,oe]}),e[85]=se,e[86]=oe,e[87]=ue):ue=e[87];const tn=u.order;let de;e[88]!==m?(de=i=>{m({order:i})},e[88]=m,e[89]=de):de=e[89];let ce;if(e[90]!==s||e[91]!==k){let i;e[93]!==k?(i=Fe=>{Pn(Fe,k,d)},e[93]=k,e[94]=i):i=e[94];let f;e[95]!==s?(f=s.map(Xn),e[95]=s,e[96]=f):f=e[96],ce={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(Fe){var R;const N=(R=Fe.lifecycle)==null?void 0:R.status;return{disabled:!!N&&["TERMINATED","CANCELLED","TERMINATING"].includes(N)}},onChange:i,selectedRowKeys:f},e[90]=s,e[91]=k,e[92]=ce}else ce=e[92];let me;e[97]!==k||e[98]!==a?(me=i=>i.map(f=>f.key!=="name"?f:{...f,render:(Fe,N)=>{var Ge,We;const R=(Ge=N.lifecycle)==null?void 0:Ge.status,O=!!R&&["TERMINATED","CANCELLED","TERMINATING"].includes(R),Te=k.find(rn=>rn.id===N.id);return l.jsx(Mn,{title:((We=N.metadata)==null?void 0:We.name)??"-",showActions:"always",actions:_n([{key:"terminate",title:a("session.TerminateSession"),icon:l.jsx(Xe,{}),type:"danger",disabled:O||!Te,onClick:()=>Te&&De([Te])}])})}}),e[97]=k,e[98]=a,e[99]=me):me=e[99];let ge;e[100]!==S?(ge=(i,f)=>{S({current:i,pageSize:f})},e[100]=S,e[101]=ge):ge=e[101];let fe;e[102]!==ge||e[103]!==v.current||e[104]!==v.pageSize||e[105]!==Pe?(fe={current:v.current,pageSize:v.pageSize,total:Pe,onChange:ge},e[102]=ge,e[103]=v.current,e[104]=v.pageSize,e[105]=Pe,e[106]=fe):fe=e[106];let Ce;e[107]===Symbol.for("react.memo_cache_sentinel")?(Ce={environment:{hidden:!1},resourceGroup:{hidden:!1},sessionType:{hidden:!1},clusterMode:{hidden:!1},createdAt:{hidden:!1}},e[107]=Ce):Ce=e[107];let pe;e[108]!==M||e[109]!==h?(pe={columnOverrides:M,defaultColumnOverrides:Ce,onColumnOverridesChange:h},e[108]=M,e[109]=h,e[110]=pe):pe=e[110];let ye;e[111]!==w||e[112]!==u.order||e[113]!==k||e[114]!==de||e[115]!==ce||e[116]!==me||e[117]!==fe||e[118]!==pe?(ye=l.jsx(On,{sessionsFrgmt:k,loading:w,order:tn,onChangeOrder:de,rowSelection:ce,customizeColumns:me,pagination:fe,tableSettings:pe}),e[111]=w,e[112]=u.order,e[113]=k,e[114]=de,e[115]=ce,e[116]=me,e[117]=fe,e[118]=pe,e[119]=ye):ye=e[119];let Se;e[120]!==I?(Se=i=>{F(!1),i&&(d([]),I())},e[120]=I,e[121]=Se):Se=e[121];let ke;e[122]!==j||e[123]!==Se||e[124]!==C?(ke=l.jsx(wn,{open:j,sessionsFrgmt:C,onRequestClose:Se}),e[122]=j,e[123]=Se,e[124]=C,e[125]=ke):ke=e[125];let ve;return e[126]!==ue||e[127]!==ye||e[128]!==ke?(ve=l.jsxs(Ie,{direction:"column",align:"stretch",gap:"sm",children:[ue,ye,ke]}),e[126]=ue,e[127]=ye,e[128]=ke,e[129]=ve):ve=e[129],ve},sl=()=>{"use memo";const n=Ee.c(9),{t:e}=Re(),t=Fn();let a;n[0]!==e?(a=e("webui.menu.ProjectSessions"),n[0]=e,n[1]=a):a=n[1];let o;n[2]===Symbol.for("react.memo_cache_sentinel")?(o={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=o):o=n[2];let s;n[3]===Symbol.for("react.memo_cache_sentinel")?(s=l.jsx(Ye,{}),n[3]=s):s=n[3];let d;n[4]!==t.id?(d=l.jsx(Tn,{children:l.jsx($.Suspense,{fallback:s,children:t.id?l.jsx(Hn,{projectId:t.id}):l.jsx(Ye,{})})}),n[4]=t.id,n[5]=d):d=n[5];let r;return n[6]!==a||n[7]!==d?(r=l.jsx(l.Fragment,{children:l.jsx(Ne,{variant:"borderless",title:a,styles:o,children:d})}),n[6]=a,n[7]=d,n[8]=r):r=n[8],r};function Yn(n){return n}function Jn(n){return n==null?void 0:n.node}function Xn(n){return n.id}export{sl as default};
//# sourceMappingURL=ProjectAdminSessionPage-D28zKPXb.js.map
