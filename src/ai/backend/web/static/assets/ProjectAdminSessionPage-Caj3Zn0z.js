import{i as Je,u as We,ab as Fn,W as Tn,a$ as In,l as E,aT as mn,r as Qe,de as Ln,br as hn,df as Kn,j as a,a8 as Vn,c as ve,s as gn,d as Ge,a2 as on,ak as An,K as jn,cJ as vn,c1 as Cn,z as xn,cu as Bn,aV as dn,dd as En,bJ as Pn,af as Mn,ce as un,ae as _n,aM as Nn,a as Rn,a7 as On,aS as $n,cf as Dn,di as wn,J as qn,h_ as cn,bk as Un,dj as zn,b2 as Qn,dJ as Gn,dh as Jn,eO as Wn,bL as Hn,ag as Yn,dk as Xn}from"./index-4XAoWQdC.js";import{g as Zn,B as el,a as nl,s as ll}from"./sessionStatusBuckets-DOsrVVEE.js";import{B as al}from"./BAIUserSelect-DVfCsXl8.js";const fn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u={defaultValue:null,kind:"LocalArgument",name:"projectId"},s=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{items:[{fields:[{kind:"Variable",name:"value",variableName:"projectId"}],kind:"ObjectValue",name:"project.0"}],kind:"ListValue",name:"project"}],kind:"ObjectValue",name:"scope"}],g={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},K=[f],L=[{alias:null,args:null,concreteType:"ResourceSlotEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],y={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},P=[y,c];return{fragment:{argumentDefinitions:[n,e,i,l,u],kind:"Fragment",metadata:null,name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:s,concreteType:"SessionV2Connection",kind:"LinkedField",name:"scopedSessionsV2",plural:!1,selections:[g,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,v,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:K,storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISessionNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalForProjectAdminFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[u,n,l,e,i],kind:"Operation",name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:s,concreteType:"SessionV2Connection",kind:"LinkedField",name:"scopedSessionsV2",plural:!1,selections:[g,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,v,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[f,{alias:null,args:null,kind:"ScalarField",name:"sessionType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:K,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2LifecycleInfo",kind:"LinkedField",name:"lifecycle",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminatedAt",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ResourceAllocation",kind:"LinkedField",name:"allocation",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"requested",plural:!1,selections:L,storageKey:null},{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"used",plural:!1,selections:L,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2Connection",kind:"LinkedField",name:"images",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:P,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:P,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[r,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[y,c,r,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"a2f21dd364247b8fc9c3ddeb08a03304",id:null,metadata:{},name:"ProjectAdminSessionPageQuery",operationKind:"query",text:`query ProjectAdminSessionPageQuery(
  $projectId: UUID!
  $filter: SessionV2Filter
  $orderBy: [SessionV2OrderBy!]
  $limit: Int
  $offset: Int
) {
  scopedSessionsV2(scope: {project: [{value: $projectId}]}, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        entityId
        metadata {
          name
        }
        ...BAISessionNodesV2Fragment
        ...TerminateSessionModalForProjectAdminFragment
      }
    }
  }
}

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
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
  entityId
  project {
    id
    basicInfo {
      name
    }
  }
  metadata {
    name
    ...BAISessionTypeTokenV2Fragment
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
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
}

fragment BAISessionTypeTokenV2Fragment on SessionV2MetadataInfo {
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
`}}})();fn.hash="dffdafc4db1a23f3470e7b6f8aa0dcd1";const yn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"forced"},e={defaultValue:null,kind:"LocalArgument",name:"sessionIds"},i=[{alias:null,args:[{kind:"Variable",name:"forced",variableName:"forced"},{kind:"Variable",name:"sessionIds",variableName:"sessionIds"}],concreteType:"TerminateSessionsPayload",kind:"LinkedField",name:"terminateSessionsV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"cancelled",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminating",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"forceTerminated",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"skipped",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e],kind:"Fragment",metadata:null,name:"TerminateSessionModalForProjectAdminMutation",selections:i,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n],kind:"Operation",name:"TerminateSessionModalForProjectAdminMutation",selections:i},params:{cacheID:"be4736b37ff54351dd17b8f5d312c2bd",id:null,metadata:{},name:"TerminateSessionModalForProjectAdminMutation",operationKind:"mutation",text:`mutation TerminateSessionModalForProjectAdminMutation(
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
`}}})();yn.hash="8c1ab011f362b60cae0d0e3b7c59bf7e";const pn=(function(){var n={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"TerminateSessionModalForProjectAdminFragment",selections:[n,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[n,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"SessionV2",abstractKey:null}})();pn.hash="7f806d407dac1670a060b0f1979cba15";const sl=n=>{"use memo";var $,D;const e=Je.c(27);let i,l,u;e[0]!==n?({sessionsFrgmt:u,onRequestClose:l,...i}=n,e[0]=n,e[1]=i,e[2]=l,e[3]=u):(i=e[1],l=e[2],u=e[3]);const{t:s}=We(),{token:g}=Fn(),{message:r}=Tn.useApp(),v=In(),[f,K]=E.useState(!1);let L;e[4]===Symbol.for("react.memo_cache_sentinel")?(L=pn,e[4]=L):L=e[4];const y=mn(Qe.useFragment(L,u));let c;e[5]===Symbol.for("react.memo_cache_sentinel")?(c=yn,e[5]=c):c=e[5];const[P,R]=Qe.useMutation(c);let b;e[6]!==l?(b=T=>{K(!1),l(T)},e[6]=l,e[7]=b):b=e[7];const k=b,p=Ln(hn(Kn(y,il)),rl);let V;e[8]!==s?(V=s("session.TerminateSession"),e[8]=s,e[9]=V):V=e[9];let A;e[10]!==f||e[11]!==s?(A=s(f?"button.ForceTerminate":"session.Terminate"),e[10]=f,e[11]=s,e[12]=A):A=e[12];const d=f?"primary":"default";let m;e[13]!==d?(m={type:d},e[13]=d,e[14]=m):m=e[14];let h;e[15]!==k?(h=()=>k(!1),e[15]=k,e[16]=h):h=e[16];let o;e[17]!==s?(o=s("userSettings.SessionTerminationDialog"),e[17]=s,e[18]=o):o=e[18];let C;e[19]!==o?(C=a.jsx(on,{children:o}),e[19]=o,e[20]=C):C=e[20];let F;e[21]!==s?(F=s("button.ForceTerminate"),e[21]=s,e[22]=F):F=e[22];let O;e[23]===Symbol.for("react.memo_cache_sentinel")?(O=T=>K(T),e[23]=O):O=e[23];let x;return e[24]!==f||e[25]!==F?(x=a.jsx(vn,{label:F,value:f,onChange:O}),e[24]=f,e[25]=F,e[26]=x):x=e[26],a.jsx(Vn,{centered:!0,title:V,okText:A,okType:"danger",okButtonProps:m,confirmLoading:R,onOk:()=>{if(y.length===0){k(!1);return}P({variables:{sessionIds:y.map(ol),forced:f},onCompleted:(T,M)=>{var j;if(M&&M.length>0){r.error(((j=M[0])==null?void 0:j.message)??s("general.ErrorOccurred"));return}r.success(s("session.SessionTerminated")),k(!0)},onError:T=>{r.error(T.message)}})},onCancel:h,...i,children:a.jsxs(ve,{className:"terminate-session-modal-admin-list",direction:"column",align:"stretch",gap:"xs",children:[C,a.jsx(gn,{mark:!0,children:y.length===1?((D=($=y[0])==null?void 0:$.metadata)==null?void 0:D.name)??"":`${y.length} sessions`}),x,f&&a.jsxs(Ge,{styles:{body:{padding:g("--spacing-4")}},children:[a.jsx(on,{as:"p",display:"block",color:"danger",children:s("session.ForceTerminateWarningMsg")}),a.jsxs("ul",{children:[a.jsx("li",{children:s("session.ForceTerminateWarningMsg2")}),a.jsx("li",{children:s("session.ForceTerminateWarningMsg3")})]}),v==="superadmin"&&a.jsx(Ge,{type:"inner",title:s("session.ContainerToCleanUp"),children:An(p,ul)})]})]})})};function tl(n){return n==null?void 0:n.node}function il(n){var e,i;return(i=(e=n.kernels)==null?void 0:e.edges)==null?void 0:i.map(tl)}function rl(n){var e;return((e=n==null?void 0:n.resource)==null?void 0:e.agentId)??"-"}function ol(n){return jn(n.id)}function dl(n){var e;return a.jsx("li",{children:a.jsx(gn,{copyable:!0,children:((e=n==null?void 0:n.resource)==null?void 0:e.containerId)??""})},n==null?void 0:n.id)}function ul(n,e){return a.jsxs(Cn.Fragment,{children:[e,a.jsx("ul",{children:n.map(dl)})]},e)}const cl=n=>{"use memo";var Ze,en,nn,ln,an,sn;const e=Je.c(150),{projectId:i}=n,{t:l}=We();let u;e[0]===Symbol.for("react.memo_cache_sentinel")?(u=[],e[0]=u):u=e[0];const[s,g]=E.useState(u);let r;e[1]===Symbol.for("react.memo_cache_sentinel")?(r=[],e[1]=r):r=e[1];const[v,f]=E.useState(r),[K,L]=E.useState(!1),y=En("session"),[c,P]=E.useState(null);let R;e[2]===Symbol.for("react.memo_cache_sentinel")?(R={current:1,pageSize:10},e[2]=R):R=e[2];const{baiPaginationOption:b,tablePaginationOption:k,setTablePaginationOption:p}=Pn(R);let V,A;e[3]===Symbol.for("react.memo_cache_sentinel")?(V={statusCategory:un(ll).withDefault("running"),order:un(nl),filter:Mn(ml)},A={history:"replace"},e[3]=V,e[4]=A):(V=e[3],A=e[4]);const[d,m]=_n(V,A),[h,o]=Nn(),C=Rn();let F;e[5]!==C?(F=Zn(C.isManagerVersionCompatibleWith("26.8.0")),e[5]=C,e[6]=F):F=e[6];const O=F,[x,$]=On("table_column_overrides.ProjectAdminSessionPage"),D=O[d.statusCategory];let T;e[7]!==D?(T={in:D},e[7]=D,e[8]=T):T=e[8];const M=T;let j;e[9]!==d.filter?(j=d.filter??{},e[9]=d.filter,e[10]=j):j=e[10];let w;e[11]!==M||e[12]!==j?(w={...j,status:M},e[11]=M,e[12]=j,e[13]=w):w=e[13];let q;e[14]!==d.order?(q=$n(d.order)??[{field:"CREATED_AT",direction:"DESC"}],e[14]=d.order,e[15]=q):q=e[15];let Ce;e[16]!==b.limit||e[17]!==b.offset||e[18]!==i||e[19]!==w||e[20]!==q?(Ce={projectId:i,filter:w,orderBy:q,limit:b.limit,offset:b.offset},e[16]=b.limit,e[17]=b.offset,e[18]=i,e[19]=w,e[20]=q,e[21]=Ce):Ce=e[21];const He=Ce,Ye=E.useDeferredValue(He),je=E.useDeferredValue(h);let xe;e[22]===Symbol.for("react.memo_cache_sentinel")?(xe=fn,e[22]=xe):xe=e[22];const $e=je===Un?"store-and-network":"network-only";let Be;e[23]!==je||e[24]!==$e?(Be={fetchKey:je,fetchPolicy:$e},e[23]=je,e[24]=$e,e[25]=Be):Be=e[25];const Ee=Qe.useLazyLoadQuery(xe,Ye,Be);let Pe;e[26]!==((Ze=Ee.scopedSessionsV2)==null?void 0:Ze.edges)?(Pe=mn((nn=(en=Ee.scopedSessionsV2)==null?void 0:en.edges)==null?void 0:nn.map(gl)),e[26]=(ln=Ee.scopedSessionsV2)==null?void 0:ln.edges,e[27]=Pe):Pe=e[27];const I=Pe,De=((an=Ee.scopedSessionsV2)==null?void 0:an.count)??0;let Me;e[28]===Symbol.for("react.memo_cache_sentinel")?(Me=t=>{f(t),L(!0)},e[28]=Me):Me=e[28];const Xe=Me,U=Ye!==He||je!==h;let _e;e[29]===Symbol.for("react.memo_cache_sentinel")?(_e={flexShrink:1},e[29]=_e):_e=e[29];const kn=d.statusCategory;let z;e[30]!==m||e[31]!==p?(z=t=>{m({statusCategory:t.target.value}),p({current:1})},e[30]=m,e[31]=p,e[32]=z):z=e[32];let Q;e[33]!==l?(Q=l("session.Running"),e[33]=l,e[34]=Q):Q=e[34];let G;e[35]!==Q?(G={label:Q,value:"running"},e[35]=Q,e[36]=G):G=e[36];let J;e[37]!==l?(J=l("session.Finished"),e[37]=l,e[38]=J):J=e[38];let W;e[39]!==J?(W={label:J,value:"finished"},e[39]=J,e[40]=W):W=e[40];let H;e[41]!==G||e[42]!==W?(H=[G,W],e[41]=G,e[42]=W,e[43]=H):H=e[43];let Y;e[44]!==d.statusCategory||e[45]!==z||e[46]!==H?(Y=a.jsx(zn,{optionType:"button",value:kn,onChange:z,options:H}),e[44]=d.statusCategory,e[45]=z,e[46]=H,e[47]=Y):Y=e[47];let Ne;e[48]===Symbol.for("react.memo_cache_sentinel")?(Ne={key:"id",propertyLabel:"ID",type:"uuid"},e[48]=Ne):Ne=e[48];let X;e[49]!==l?(X=l("session.SessionName"),e[49]=l,e[50]=X):X=e[50];let Z;e[51]!==X?(Z={key:"name",propertyLabel:X,type:"string"},e[51]=X,e[52]=Z):Z=e[52];let ee;e[53]!==l?(ee=l("session.Owner"),e[53]=l,e[54]=ee):ee=e[54];let ne;e[55]!==l?(ne=t=>{const{onAddCondition:S,value:Ve,isDisabled:B}=t;return a.jsx(al,{valuePropName:"id",label:l("session.Owner"),isLabelHidden:!0,value:Ve,isDisabled:B,onChange:(_,N)=>{var Ae;return S(_,Array.isArray(N)?(Ae=N[0])==null?void 0:Ae.label:N==null?void 0:N.label)}})},e[55]=l,e[56]=ne):ne=e[56];let le;e[57]!==ee||e[58]!==ne?(le={key:"userUuid",propertyLabel:ee,type:"uuid",renderInput:ne},e[57]=ee,e[58]=ne,e[59]=le):le=e[59];let ae;e[60]!==y||e[61]!==l?(ae=y?[{key:"labels.some.key",propertyLabel:l("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:l("entityLabel.LabelValue"),type:"string"}]:[],e[60]=y,e[61]=l,e[62]=ae):ae=e[62];let se;e[63]!==Z||e[64]!==le||e[65]!==ae?(se=[Ne,Z,le,...ae],e[63]=Z,e[64]=le,e[65]=ae,e[66]=se):se=e[66];const we=d.filter??void 0;let te;e[67]!==m||e[68]!==p?(te=t=>{m({filter:t??null}),p({current:1})},e[67]=m,e[68]=p,e[69]=te):te=e[69];let ie;e[70]!==se||e[71]!==we||e[72]!==te?(ie=a.jsx(Qn,{filterProperties:se,value:we,onChange:te}),e[70]=se,e[71]=we,e[72]=te,e[73]=ie):ie=e[73];let re;e[74]!==Y||e[75]!==ie?(re=a.jsxs(ve,{gap:"sm",align:"start",wrap:"wrap",style:_e,children:[Y,ie]}),e[74]=Y,e[75]=ie,e[76]=re):re=e[76];let oe;e[77]!==s||e[78]!==l||e[79]!==o?(oe=s.length>0&&a.jsxs(a.Fragment,{children:[a.jsx(Dn,{count:s.length,onClearSelection:()=>g([])}),a.jsx(wn,{entityType:"session",targets:s.map(fl),onLabelsChanged:()=>o()}),a.jsx(qn,{label:l("session.TerminateSession"),tooltip:l("session.TerminateSession"),icon:a.jsx(cn,{color:"var(--color-error)"}),onClick:()=>Xe(s)})]}),e[77]=s,e[78]=l,e[79]=o,e[80]=oe):oe=e[80];let de;e[81]!==o?(de=t=>o(t),e[81]=o,e[82]=de):de=e[82];let ue;e[83]!==h||e[84]!==U||e[85]!==de?(ue=a.jsx(Gn,{settingId:"project-admin-session",defaultAutoUpdateDelay:15e3,loading:U,value:h,onChange:de}),e[83]=h,e[84]=U,e[85]=de,e[86]=ue):ue=e[86];let ce;e[87]!==oe||e[88]!==ue?(ce=a.jsxs(ve,{gap:"xs",children:[oe,ue]}),e[87]=oe,e[88]=ue,e[89]=ce):ce=e[89];let me;e[90]!==re||e[91]!==ce?(me=a.jsxs(ve,{direction:"row",justify:"between",wrap:"wrap",gap:"sm",children:[re,ce]}),e[90]=re,e[91]=ce,e[92]=me):me=e[92];const qe=y?P:void 0;let ge;e[93]!==m||e[94]!==p?(ge=t=>{m({filter:Jn(t)}),p({current:1})},e[93]=m,e[94]=p,e[95]=ge):ge=e[95];const Sn=d.order;let fe;e[96]!==m?(fe=t=>{m({order:t})},e[96]=m,e[97]=fe):fe=e[97];let ye;if(e[98]!==s||e[99]!==I){let t;e[101]!==I?(t=Ve=>{Wn(Ve,I,g)},e[101]=I,e[102]=t):t=e[102];let S;e[103]!==s?(S=s.map(yl),e[103]=s,e[104]=S):S=e[104],ye={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(Ve){var _;const B=(_=Ve.lifecycle)==null?void 0:_.status;return{disabled:!!B&&["TERMINATED","CANCELLED","TERMINATING"].includes(B)}},onChange:t,selectedRowKeys:S},e[98]=s,e[99]=I,e[100]=ye}else ye=e[100];let pe;e[105]!==I||e[106]!==l?(pe=t=>t.map(S=>S.key!=="name"?S:{...S,render:(Ve,B)=>{var tn,rn;const _=(tn=B.lifecycle)==null?void 0:tn.status,N=!!_&&["TERMINATED","CANCELLED","TERMINATING"].includes(_),Ae=I.find(bn=>bn.id===B.id);return a.jsx(Hn,{title:((rn=B.metadata)==null?void 0:rn.name)??"-",showActions:"always",actions:Yn([{key:"terminate",title:l("session.TerminateSession"),icon:a.jsx(cn,{}),type:"danger",disabled:N||!Ae,onClick:()=>Ae&&Xe([Ae])}])})}}),e[105]=I,e[106]=l,e[107]=pe):pe=e[107];let ke;e[108]!==p?(ke=(t,S)=>{p({current:t,pageSize:S})},e[108]=p,e[109]=ke):ke=e[109];let Se;e[110]!==ke||e[111]!==k.current||e[112]!==k.pageSize||e[113]!==De?(Se={current:k.current,pageSize:k.pageSize,total:De,onChange:ke},e[110]=ke,e[111]=k.current,e[112]=k.pageSize,e[113]=De,e[114]=Se):Se=e[114];let Re;e[115]===Symbol.for("react.memo_cache_sentinel")?(Re={environment:{hidden:!1},resourceGroup:{hidden:!1},sessionType:{hidden:!1},clusterMode:{hidden:!1},createdAt:{hidden:!1}},e[115]=Re):Re=e[115];let be;e[116]!==x||e[117]!==$?(be={columnOverrides:x,defaultColumnOverrides:Re,onColumnOverridesChange:$},e[116]=x,e[117]=$,e[118]=be):be=e[118];let Fe;e[119]!==U||e[120]!==d.order||e[121]!==I||e[122]!==qe||e[123]!==ge||e[124]!==fe||e[125]!==ye||e[126]!==pe||e[127]!==Se||e[128]!==be?(Fe=a.jsx(el,{onEditLabels:qe,showLabelsByDefault:!0,onLabelClick:ge,sessionsFrgmt:I,loading:U,order:Sn,onChangeOrder:fe,rowSelection:ye,customizeColumns:pe,pagination:Se,tableSettings:be}),e[119]=U,e[120]=d.order,e[121]=I,e[122]=qe,e[123]=ge,e[124]=fe,e[125]=ye,e[126]=pe,e[127]=Se,e[128]=be,e[129]=Fe):Fe=e[129];const Ue=!!c;let Te;e[130]!==c?(Te=c?[{entityId:c.entityId,name:((sn=c.metadata)==null?void 0:sn.name)??void 0}]:[],e[130]=c,e[131]=Te):Te=e[131];const ze=c==null?void 0:c.entityLabels;let Ie;e[132]!==o?(Ie=t=>{P(null),t&&o()},e[132]=o,e[133]=Ie):Ie=e[133];let Le;e[134]!==Ue||e[135]!==Te||e[136]!==ze||e[137]!==Ie?(Le=a.jsx(Xn,{open:Ue,entityType:"session",targets:Te,entityLabelsFrgmt:ze,onRequestClose:Ie}),e[134]=Ue,e[135]=Te,e[136]=ze,e[137]=Ie,e[138]=Le):Le=e[138];let he;e[139]!==o?(he=t=>{L(!1),t&&(g([]),o())},e[139]=o,e[140]=he):he=e[140];let Ke;e[141]!==K||e[142]!==he||e[143]!==v?(Ke=a.jsx(sl,{open:K,sessionsFrgmt:v,onRequestClose:he}),e[141]=K,e[142]=he,e[143]=v,e[144]=Ke):Ke=e[144];let Oe;return e[145]!==me||e[146]!==Fe||e[147]!==Le||e[148]!==Ke?(Oe=a.jsxs(ve,{direction:"column",align:"stretch",gap:"sm",children:[me,Fe,Le,Ke]}),e[145]=me,e[146]=Fe,e[147]=Le,e[148]=Ke,e[149]=Oe):Oe=e[149],Oe},bl=()=>{"use memo";const n=Je.c(9),{t:e}=We(),i=xn();let l;n[0]!==e?(l=e("webui.menu.ProjectSessions"),n[0]=e,n[1]=l):l=n[1];let u;n[2]===Symbol.for("react.memo_cache_sentinel")?(u={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=u):u=n[2];let s;n[3]===Symbol.for("react.memo_cache_sentinel")?(s=a.jsx(dn,{}),n[3]=s):s=n[3];let g;n[4]!==i.id?(g=a.jsx(Bn,{children:a.jsx(E.Suspense,{fallback:s,children:i.id?a.jsx(cl,{projectId:i.id}):a.jsx(dn,{})})}),n[4]=i.id,n[5]=g):g=n[5];let r;return n[6]!==l||n[7]!==g?(r=a.jsx(a.Fragment,{children:a.jsx(Ge,{variant:"borderless",title:l,styles:u,children:g})}),n[6]=l,n[7]=g,n[8]=r):r=n[8],r};function ml(n){return n}function gl(n){return n==null?void 0:n.node}function fl(n){var e;return{entityId:n.entityId,name:((e=n.metadata)==null?void 0:e.name)??void 0}}function yl(n){return n.id}export{bl as default};
//# sourceMappingURL=ProjectAdminSessionPage-Caj3Zn0z.js.map
