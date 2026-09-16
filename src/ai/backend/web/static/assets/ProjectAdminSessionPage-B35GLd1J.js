import{i as _e,u as Ne,ab as rn,X as on,a_ as un,l as E,aS as Je,r as Pe,dy as cn,bn as dn,dz as mn,j as l,a8 as gn,c as ke,s as Xe,d as Me,a2 as Ge,al as fn,N as pn,cx as yn,bY as Sn,z as kn,co as Fn,aU as We,bE as Tn,ag as In,c8 as Ye,ae as hn,aN as bn,a as Kn,a7 as jn,aR as Vn,c9 as An,K as Ln,hR as He,bg as xn,cC as Cn,cz as vn,ew as Bn,bG as Pn,ah as Mn}from"./index-DPebpL40.js";import{a as _n,s as Nn,g as En,B as Rn}from"./sessionStatusBuckets-CRW9PX0M.js";import{B as On}from"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import"./BAIId-oHD2WVBQ.js";import"./BAITag-dedPDMOM.js";const Ze=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},t={defaultValue:null,kind:"LocalArgument",name:"offset"},s={defaultValue:null,kind:"LocalArgument",name:"orderBy"},o={defaultValue:null,kind:"LocalArgument",name:"projectId"},a=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],c={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d=[C],j=[{alias:null,args:null,concreteType:"ResourceSlotEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],k=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}];return{fragment:{argumentDefinitions:[n,e,t,s,o],kind:"Fragment",metadata:null,name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:a,concreteType:"SessionV2Connection",kind:"LinkedField",name:"projectSessionsV2",plural:!1,selections:[c,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:d,storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISessionNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalForProjectAdminFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[o,n,s,e,t],kind:"Operation",name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:a,concreteType:"SessionV2Connection",kind:"LinkedField",name:"projectSessionsV2",plural:!1,selections:[c,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[C,{alias:null,args:null,kind:"ScalarField",name:"sessionType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:d,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2LifecycleInfo",kind:"LinkedField",name:"lifecycle",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminatedAt",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ResourceAllocation",kind:"LinkedField",name:"allocation",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"requested",plural:!1,selections:j,storageKey:null},{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"used",plural:!1,selections:j,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2Connection",kind:"LinkedField",name:"images",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:k,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:k,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[i,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"ce21c7ce05a652ddcd879723a7162834",id:null,metadata:{},name:"ProjectAdminSessionPageQuery",operationKind:"query",text:`query ProjectAdminSessionPageQuery(
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
    namespace
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
`}}})();Ze.hash="0319d10e5f67b53895012b3e1c631bde";const en=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"forced"},e={defaultValue:null,kind:"LocalArgument",name:"sessionIds"},t=[{alias:null,args:[{kind:"Variable",name:"forced",variableName:"forced"},{kind:"Variable",name:"sessionIds",variableName:"sessionIds"}],concreteType:"TerminateSessionsPayload",kind:"LinkedField",name:"terminateSessionsV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"cancelled",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminating",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"forceTerminated",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"skipped",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e],kind:"Fragment",metadata:null,name:"TerminateSessionModalForProjectAdminMutation",selections:t,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n],kind:"Operation",name:"TerminateSessionModalForProjectAdminMutation",selections:t},params:{cacheID:"be4736b37ff54351dd17b8f5d312c2bd",id:null,metadata:{},name:"TerminateSessionModalForProjectAdminMutation",operationKind:"mutation",text:`mutation TerminateSessionModalForProjectAdminMutation(
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
`}}})();en.hash="8c1ab011f362b60cae0d0e3b7c59bf7e";const nn=(function(){var n={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"TerminateSessionModalForProjectAdminFragment",selections:[n,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[n,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"SessionV2",abstractKey:null}})();nn.hash="7f806d407dac1670a060b0f1979cba15";const $n=n=>{"use memo";var R,x;const e=_e.c(27);let t,s,o;e[0]!==n?({sessionsFrgmt:o,onRequestClose:s,...t}=n,e[0]=n,e[1]=t,e[2]=s,e[3]=o):(t=e[1],s=e[2],o=e[3]);const{t:a}=Ne(),{token:c}=rn.useToken(),{message:i}=on.useApp(),C=un(),[d,j]=E.useState(!1);let k;e[4]===Symbol.for("react.memo_cache_sentinel")?(k=nn,e[4]=k):k=e[4];const f=Je(Pe.useFragment(k,o));let p;e[5]===Symbol.for("react.memo_cache_sentinel")?(p=en,e[5]=p):p=e[5];const[v,y]=Pe.useMutation(p);let V;e[6]!==s?(V=g=>{j(!1),s(g)},e[6]=s,e[7]=V):V=e[7];const F=V,u=cn(dn(mn(f,wn)),Un);let m;e[8]!==a?(m=a("session.TerminateSession"),e[8]=a,e[9]=m):m=e[9];let T;e[10]!==d||e[11]!==a?(T=a(d?"button.ForceTerminate":"session.Terminate"),e[10]=d,e[11]=a,e[12]=T):T=e[12];const I=d?"primary":"default";let B;e[13]!==I?(B={type:I},e[13]=I,e[14]=B):B=e[14];let A;e[15]!==F?(A=()=>F(!1),e[15]=F,e[16]=A):A=e[16];let P;e[17]!==a?(P=a("userSettings.SessionTerminationDialog"),e[17]=a,e[18]=P):P=e[18];let M;e[19]!==P?(M=l.jsx(Ge,{children:P}),e[19]=P,e[20]=M):M=e[20];let h;e[21]!==a?(h=a("button.ForceTerminate"),e[21]=a,e[22]=h):h=e[22];let _;e[23]===Symbol.for("react.memo_cache_sentinel")?(_=g=>j(g),e[23]=_):_=e[23];let L;return e[24]!==d||e[25]!==h?(L=l.jsx(yn,{label:h,value:d,onChange:_}),e[24]=d,e[25]=h,e[26]=L):L=e[26],l.jsx(gn,{centered:!0,title:m,okText:T,okType:"danger",okButtonProps:B,confirmLoading:y,onOk:()=>{if(f.length===0){F(!1);return}v({variables:{sessionIds:f.map(qn),forced:d},onCompleted:(g,b)=>{var N;if(b&&b.length>0){i.error(((N=b[0])==null?void 0:N.message)??a("general.ErrorOccurred"));return}i.success(a("session.SessionTerminated")),F(!0)},onError:g=>{i.error(g.message)}})},onCancel:A,...t,children:l.jsxs(ke,{className:"terminate-session-modal-admin-list",direction:"column",align:"stretch",gap:"xs",children:[M,l.jsx(Xe,{mark:!0,children:f.length===1?((x=(R=f[0])==null?void 0:R.metadata)==null?void 0:x.name)??"":`${f.length} sessions`}),L,d&&l.jsxs(Me,{styles:{body:{padding:c.padding}},children:[l.jsx(Ge,{as:"p",display:"block",color:"danger",children:a("session.ForceTerminateWarningMsg")}),l.jsxs("ul",{children:[l.jsx("li",{children:a("session.ForceTerminateWarningMsg2")}),l.jsx("li",{children:a("session.ForceTerminateWarningMsg3")})]}),C==="superadmin"&&l.jsx(Me,{type:"inner",title:a("session.ContainerToCleanUp"),children:fn(u,Qn)})]})]})})};function Dn(n){return n==null?void 0:n.node}function wn(n){var e,t;return(t=(e=n.kernels)==null?void 0:e.edges)==null?void 0:t.map(Dn)}function Un(n){var e;return((e=n==null?void 0:n.resource)==null?void 0:e.agentId)??"-"}function qn(n){return pn(n.id)}function zn(n){var e;return l.jsx("li",{children:l.jsx(Xe,{copyable:!0,children:((e=n==null?void 0:n.resource)==null?void 0:e.containerId)??""})},n==null?void 0:n.id)}function Qn(n,e){return l.jsxs(Sn.Fragment,{children:[e,l.jsx("ul",{children:n.map(zn)})]},e)}const Gn=n=>{"use memo";var $e,De,we,Ue,qe;const e=_e.c(127),{projectId:t}=n,{t:s}=Ne();let o;e[0]===Symbol.for("react.memo_cache_sentinel")?(o=[],e[0]=o):o=e[0];const[a,c]=E.useState(o);let i;e[1]===Symbol.for("react.memo_cache_sentinel")?(i=[],e[1]=i):i=e[1];const[C,d]=E.useState(i),[j,k]=E.useState(!1);let f;e[2]===Symbol.for("react.memo_cache_sentinel")?(f={current:1,pageSize:10},e[2]=f):f=e[2];const{baiPaginationOption:p,tablePaginationOption:v,setTablePaginationOption:y}=Tn(f);let V,F;e[3]===Symbol.for("react.memo_cache_sentinel")?(V={statusCategory:Ye(Nn).withDefault("running"),order:Ye(_n),filter:In(Wn)},F={history:"replace"},e[3]=V,e[4]=F):(V=e[3],F=e[4]);const[u,m]=hn(V,F),[T,I]=bn(),B=Kn();let A;e[5]!==B?(A=En(B.supports("session-preemption-statuses")),e[5]=B,e[6]=A):A=e[6];const P=A,[M,h]=jn("table_column_overrides.ProjectAdminSessionPage"),_=P[u.statusCategory];let L;e[7]!==_?(L={in:_},e[7]=_,e[8]=L):L=e[8];const R=L;let x;e[9]!==u.filter?(x=u.filter??{},e[9]=u.filter,e[10]=x):x=e[10];let g;e[11]!==R||e[12]!==x?(g={...x,status:R},e[11]=R,e[12]=x,e[13]=g):g=e[13];let b;e[14]!==u.order?(b=Vn(u.order)??[{field:"CREATED_AT",direction:"DESC"}],e[14]=u.order,e[15]=b):b=e[15];let N;e[16]!==p.limit||e[17]!==p.offset||e[18]!==t||e[19]!==g||e[20]!==b?(N={projectId:t,filter:g,orderBy:b,limit:p.limit,offset:p.offset},e[16]=p.limit,e[17]=p.offset,e[18]=t,e[19]=g,e[20]=b,e[21]=N):N=e[21];const Ee=N,Re=E.useDeferredValue(Ee),ye=E.useDeferredValue(T);let Fe;e[22]===Symbol.for("react.memo_cache_sentinel")?(Fe=Ze,e[22]=Fe):Fe=e[22];const xe=ye===xn?"store-and-network":"network-only";let Te;e[23]!==ye||e[24]!==xe?(Te={fetchKey:ye,fetchPolicy:xe},e[23]=ye,e[24]=xe,e[25]=Te):Te=e[25];const Ie=Pe.useLazyLoadQuery(Fe,Re,Te);let he;e[26]!==(($e=Ie.projectSessionsV2)==null?void 0:$e.edges)?(he=Je((we=(De=Ie.projectSessionsV2)==null?void 0:De.edges)==null?void 0:we.map(Yn)),e[26]=(Ue=Ie.projectSessionsV2)==null?void 0:Ue.edges,e[27]=he):he=e[27];const S=he,Ce=((qe=Ie.projectSessionsV2)==null?void 0:qe.count)??0;let be;e[28]===Symbol.for("react.memo_cache_sentinel")?(be=r=>{d(r),k(!0)},e[28]=be):be=e[28];const Oe=be,O=Re!==Ee||ye!==T;let Ke;e[29]===Symbol.for("react.memo_cache_sentinel")?(Ke={flexShrink:1},e[29]=Ke):Ke=e[29];const ln=u.statusCategory;let $;e[30]!==m||e[31]!==y?($=r=>{m({statusCategory:r.target.value}),y({current:1})},e[30]=m,e[31]=y,e[32]=$):$=e[32];let D;e[33]!==s?(D=s("session.Running"),e[33]=s,e[34]=D):D=e[34];let w;e[35]!==D?(w={label:D,value:"running"},e[35]=D,e[36]=w):w=e[36];let U;e[37]!==s?(U=s("session.Finished"),e[37]=s,e[38]=U):U=e[38];let q;e[39]!==U?(q={label:U,value:"finished"},e[39]=U,e[40]=q):q=e[40];let z;e[41]!==w||e[42]!==q?(z=[w,q],e[41]=w,e[42]=q,e[43]=z):z=e[43];let Q;e[44]!==u.statusCategory||e[45]!==$||e[46]!==z?(Q=l.jsx(Cn,{optionType:"button",value:ln,onChange:$,options:z}),e[44]=u.statusCategory,e[45]=$,e[46]=z,e[47]=Q):Q=e[47];let je;e[48]===Symbol.for("react.memo_cache_sentinel")?(je={key:"id",propertyLabel:"ID",type:"uuid"},e[48]=je):je=e[48];let G;e[49]!==s?(G=s("session.SessionName"),e[49]=s,e[50]=G):G=e[50];let W;e[51]!==G?(W={key:"name",propertyLabel:G,type:"string"},e[51]=G,e[52]=W):W=e[52];let Y;e[53]!==s?(Y=s("session.OwnerUUID"),e[53]=s,e[54]=Y):Y=e[54];let H;e[55]!==Y?(H={key:"userUuid",propertyLabel:Y,type:"uuid"},e[55]=Y,e[56]=H):H=e[56];let J;e[57]!==W||e[58]!==H?(J=[je,W,H],e[57]=W,e[58]=H,e[59]=J):J=e[59];const ve=u.filter??void 0;let X;e[60]!==m||e[61]!==y?(X=r=>{m({filter:r??null}),y({current:1})},e[60]=m,e[61]=y,e[62]=X):X=e[62];let Z;e[63]!==J||e[64]!==ve||e[65]!==X?(Z=l.jsx(On,{filterProperties:J,value:ve,onChange:X}),e[63]=J,e[64]=ve,e[65]=X,e[66]=Z):Z=e[66];let ee;e[67]!==Q||e[68]!==Z?(ee=l.jsxs(ke,{gap:"sm",align:"start",wrap:"wrap",style:Ke,children:[Q,Z]}),e[67]=Q,e[68]=Z,e[69]=ee):ee=e[69];let ne;e[70]!==a||e[71]!==s?(ne=a.length>0&&l.jsxs(l.Fragment,{children:[l.jsx(An,{count:a.length,onClearSelection:()=>c([])}),l.jsx(Ln,{label:s("session.TerminateSession"),tooltip:s("session.TerminateSession"),icon:l.jsx(He,{color:"var(--color-error)"}),onClick:()=>Oe(a)})]}),e[70]=a,e[71]=s,e[72]=ne):ne=e[72];let le;e[73]!==I?(le=r=>I(r),e[73]=I,e[74]=le):le=e[74];let ae;e[75]!==T||e[76]!==O||e[77]!==le?(ae=l.jsx(vn,{settingId:"project-admin-session",defaultAutoUpdateDelay:15e3,loading:O,value:T,onChange:le}),e[75]=T,e[76]=O,e[77]=le,e[78]=ae):ae=e[78];let se;e[79]!==ne||e[80]!==ae?(se=l.jsxs(ke,{gap:"xs",children:[ne,ae]}),e[79]=ne,e[80]=ae,e[81]=se):se=e[81];let te;e[82]!==ee||e[83]!==se?(te=l.jsxs(ke,{direction:"row",justify:"between",wrap:"wrap",gap:"sm",children:[ee,se]}),e[82]=ee,e[83]=se,e[84]=te):te=e[84];const an=u.order;let ie;e[85]!==m?(ie=r=>{m({order:r})},e[85]=m,e[86]=ie):ie=e[86];let re;if(e[87]!==a||e[88]!==S){let r;e[90]!==S?(r=Le=>{Bn(Le,S,c)},e[90]=S,e[91]=r):r=e[91];let K;e[92]!==a?(K=a.map(Hn),e[92]=a,e[93]=K):K=e[93],re={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(Le){var Se;const pe=(Se=Le.lifecycle)==null?void 0:Se.status;return{disabled:!!pe&&["TERMINATED","CANCELLED","TERMINATING"].includes(pe)}},onChange:r,selectedRowKeys:K},e[87]=a,e[88]=S,e[89]=re}else re=e[89];let oe;e[94]!==S||e[95]!==s?(oe=r=>r.map(K=>K.key!=="name"?K:{...K,render:(Le,pe)=>{var ze,Qe;const Se=(ze=pe.lifecycle)==null?void 0:ze.status,sn=!!Se&&["TERMINATED","CANCELLED","TERMINATING"].includes(Se),Be=S.find(tn=>tn.id===pe.id);return l.jsx(Pn,{title:((Qe=pe.metadata)==null?void 0:Qe.name)??"-",showActions:"always",actions:Mn([{key:"terminate",title:s("session.TerminateSession"),icon:l.jsx(He,{}),type:"danger",disabled:sn||!Be,onClick:()=>Be&&Oe([Be])}])})}}),e[94]=S,e[95]=s,e[96]=oe):oe=e[96];let ue;e[97]!==y?(ue=(r,K)=>{y({current:r,pageSize:K})},e[97]=y,e[98]=ue):ue=e[98];let ce;e[99]!==ue||e[100]!==v.current||e[101]!==v.pageSize||e[102]!==Ce?(ce={current:v.current,pageSize:v.pageSize,total:Ce,onChange:ue},e[99]=ue,e[100]=v.current,e[101]=v.pageSize,e[102]=Ce,e[103]=ce):ce=e[103];let Ve;e[104]===Symbol.for("react.memo_cache_sentinel")?(Ve={environment:{hidden:!1},resourceGroup:{hidden:!1},sessionType:{hidden:!1},clusterMode:{hidden:!1},createdAt:{hidden:!1}},e[104]=Ve):Ve=e[104];let de;e[105]!==M||e[106]!==h?(de={columnOverrides:M,defaultColumnOverrides:Ve,onColumnOverridesChange:h},e[105]=M,e[106]=h,e[107]=de):de=e[107];let me;e[108]!==O||e[109]!==u.order||e[110]!==S||e[111]!==ie||e[112]!==re||e[113]!==oe||e[114]!==ce||e[115]!==de?(me=l.jsx(Rn,{sessionsFrgmt:S,loading:O,order:an,onChangeOrder:ie,rowSelection:re,customizeColumns:oe,pagination:ce,tableSettings:de}),e[108]=O,e[109]=u.order,e[110]=S,e[111]=ie,e[112]=re,e[113]=oe,e[114]=ce,e[115]=de,e[116]=me):me=e[116];let ge;e[117]!==I?(ge=r=>{k(!1),r&&(c([]),I())},e[117]=I,e[118]=ge):ge=e[118];let fe;e[119]!==j||e[120]!==ge||e[121]!==C?(fe=l.jsx($n,{open:j,sessionsFrgmt:C,onRequestClose:ge}),e[119]=j,e[120]=ge,e[121]=C,e[122]=fe):fe=e[122];let Ae;return e[123]!==te||e[124]!==me||e[125]!==fe?(Ae=l.jsxs(ke,{direction:"column",align:"stretch",gap:"sm",children:[te,me,fe]}),e[123]=te,e[124]=me,e[125]=fe,e[126]=Ae):Ae=e[126],Ae},ll=()=>{"use memo";const n=_e.c(9),{t:e}=Ne(),t=kn();let s;n[0]!==e?(s=e("webui.menu.ProjectSessions"),n[0]=e,n[1]=s):s=n[1];let o;n[2]===Symbol.for("react.memo_cache_sentinel")?(o={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=o):o=n[2];let a;n[3]===Symbol.for("react.memo_cache_sentinel")?(a=l.jsx(We,{}),n[3]=a):a=n[3];let c;n[4]!==t.id?(c=l.jsx(Fn,{children:l.jsx(E.Suspense,{fallback:a,children:t.id?l.jsx(Gn,{projectId:t.id}):l.jsx(We,{})})}),n[4]=t.id,n[5]=c):c=n[5];let i;return n[6]!==s||n[7]!==c?(i=l.jsx(l.Fragment,{children:l.jsx(Me,{variant:"borderless",title:s,styles:o,children:c})}),n[6]=s,n[7]=c,n[8]=i):i=n[8],i};function Wn(n){return n}function Yn(n){return n==null?void 0:n.node}function Hn(n){return n.id}export{ll as default};
//# sourceMappingURL=ProjectAdminSessionPage-B35GLd1J.js.map
