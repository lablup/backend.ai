import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{t}from"./compiler-runtime-CZQb2eIb.js";/* empty css            */import{t as n}from"./jsx-runtime-BapUIyWk.js";import{_ as r}from"./usePressFeedback-BIoIGSxE.js";import{G as i,K as a,s as o}from"./DefaultProviders-BFjPhnQa.js";import{r as s}from"./Skeleton-D35z7Ria.js";import{t as c}from"./BAIFlex-BElkJeHW.js";import{a as l}from"./useThemeMode-Dg5yAWy7.js";import{G as u}from"./helper-BWFKT_2Y.js";import{t as d}from"./react-relay-BfoHYpUf.js";import{C as f}from"./helper-DF1Eunoe.js";import{t as p}from"./dayjs.min-PJVk-kyH.js";import{t as m}from"./BAIText-CtDfjLnS.js";import{t as h}from"./SessionActionButtons-BKP8A1TC.js";import{t as g}from"./SessionStatusBadge-CfC0KQk5.js";import{o as _}from"./useRouteScope-Dgi-LDmN.js";var v=t(),y={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIComputeSessionNodeNotificationItemFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},{args:null,kind:`FragmentSpread`,name:`SessionActionButtonsFragment`},{args:null,kind:`FragmentSpread`,name:`SessionStatusBadgeFragment`}],type:`ComputeSessionNode`,abstractKey:null};y.hash=`8d53c71903c9d2d640979e4ab2758dfe`;var b=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`session_id`}],t=[{kind:`Variable`,name:`sessionId`,variableName:`session_id`}],n={alias:null,args:null,kind:`ScalarField`,name:`reason`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},i={alias:null,args:null,kind:`ScalarField`,name:`status_info`,storageKey:null},a={alias:null,args:null,kind:`ScalarField`,name:`status_data`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`result`,storageKey:null},s={alias:null,args:null,kind:`ScalarField`,name:`service_ports`,storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`commit_status`,storageKey:null},l={alias:null,args:null,kind:`ScalarField`,name:`agent_ids`,storageKey:null},u={alias:null,args:null,kind:`ScalarField`,name:`occupied_slots`,storageKey:null},d={alias:null,args:null,kind:`ScalarField`,name:`created_at`,storageKey:null},f={alias:null,args:null,kind:`ScalarField`,name:`starts_at`,storageKey:null},p={alias:null,args:null,kind:`ScalarField`,name:`terminated_at`,storageKey:null},m={alias:null,args:null,kind:`ScalarField`,name:`queue_position`,storageKey:null},h={alias:null,args:null,kind:`ScalarField`,name:`idle_checks`,storageKey:null},g={alias:null,args:null,kind:`ScalarField`,name:`agent_id`,storageKey:null},_={alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},v={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null},y={alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},b={alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},x={alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null},S=[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null}],C={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIComputeSessionNodeNotificationItemSubscription`,selections:[{alias:null,args:t,concreteType:`SchedulingBroadcastEventPayload`,kind:`LinkedField`,name:`schedulingEventsBySession`,plural:!1,selections:[n,{alias:null,args:null,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`session`,plural:!1,selections:[r,i,a,o,s,c,l,u,d,f,p,m,h,{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[r,i,g,_,v,y,b,x,{alias:null,args:null,concreteType:`ImageNode`,kind:`LinkedField`,name:`image`,plural:!1,selections:[{args:null,kind:`FragmentSpread`,name:`BAIImageNodeSimpleTagFragment`}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:`Subscription`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIComputeSessionNodeNotificationItemSubscription`,selections:[{alias:null,args:t,concreteType:`SchedulingBroadcastEventPayload`,kind:`LinkedField`,name:`schedulingEventsBySession`,plural:!1,selections:[n,{alias:null,args:null,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`session`,plural:!1,selections:[r,i,a,o,s,c,l,u,d,f,p,m,h,{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[r,i,g,_,v,y,b,x,{alias:null,args:null,concreteType:`ImageNode`,kind:`LinkedField`,name:`image`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`base_image_name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`version`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null},{alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`tags`,plural:!0,selections:S,storageKey:null},{alias:null,args:null,concreteType:`KVPair`,kind:`LinkedField`,name:`labels`,plural:!0,selections:S,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`registry`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`namespace`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`tag`,storageKey:null},C],storageKey:null},C],storageKey:null}],storageKey:null}],storageKey:null},C],storageKey:null}],storageKey:null}]},params:{cacheID:`5c7c80f39ca3febd9ec8265e3b7ee651`,id:null,metadata:{},name:`BAIComputeSessionNodeNotificationItemSubscription`,operationKind:`subscription`,text:`subscription BAIComputeSessionNodeNotificationItemSubscription(
  $session_id: ID!
) {
  schedulingEventsBySession(sessionId: $session_id) {
    reason
    session {
      status
      status_info
      status_data
      result
      service_ports
      commit_status
      agent_ids
      occupied_slots
      created_at
      starts_at
      terminated_at
      queue_position
      idle_checks
      kernel_nodes {
        edges {
          node {
            status
            status_info
            agent_id
            container_id
            row_id
            cluster_role
            cluster_idx
            cluster_hostname
            image {
              ...BAIImageNodeSimpleTagFragment
              id
            }
            id
          }
        }
      }
      id
    }
  }
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
`}}})();b.hash=`f7b622d732889064edeaa6be25551f0d`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var x=e(p(),1),S=d(),C=n(),w=e=>{"use memo";let t=(0,v.c)(20),{sessionFrgmt:n,showDate:d,notification:p,primaryAppOption:b}=e,{closeNotification:w}=o(),{t:E}=s(),D=u(),{token:O}=r(),k=_(),A=(0,S.useFragment)(y,n),j;t[0]!==w||t[1]!==(A==null?void 0:A.status)||t[2]!==p?(j=()=>{((A==null?void 0:A.status)===`TERMINATED`||(A==null?void 0:A.status)===`CANCELLED`)&&setTimeout(()=>{w(p.key)},3e3)},t[0]=w,t[1]=A==null?void 0:A.status,t[2]=p,t[3]=j):j=t[3];let M=A==null?void 0:A.status,N;t[4]===M?N=t[5]:(N=[M],t[4]=M,t[5]=N),l(j,N);let P;bb0:{if(!(A!=null&&A.status_data)){P=null;break bb0}try{var F,I;let e;t[6]===A?e=t[7]:(e=JSON.parse(A.status_data),t[6]=A,t[7]=e);let n=e;P=(n==null||(F=n.error)==null?void 0:F.repr)??(n==null||(I=n.error)==null||(I=I.collection)==null||(I=I[0])==null?void 0:I.repr)??null}catch{P=null}}let L=P,R=((A==null?void 0:A.status)===`ERROR`||(A==null?void 0:A.status)===`CANCELLED`)&&(!!L||!!(A!=null&&A.status_info)),z;return t[8]!==k||t[9]!==w||t[10]!==L||t[11]!==R||t[12]!==D||t[13]!==A||t[14]!==p||t[15]!==b||t[16]!==d||t[17]!==E||t[18]!==O?(z=A&&(0,C.jsxs)(C.Fragment,{children:[(0,C.jsx)(i,{className:`bai-node-notification-item`,title:(0,C.jsxs)(m,{ellipsis:!0,children:[E(`general.Session`),`:\xA0`,(0,C.jsx)(a,{style:{fontWeight:`normal`},title:A.name||``,onClick:()=>{D(`${k(`session`,{scope:`project`})}${A.id?`?${new URLSearchParams({sessionDetail:f(A.id)}).toString()}`:``}`),w(p.key)},children:A.name})]}),description:(0,C.jsxs)(c,{direction:`column`,gap:`xs`,style:{width:`100%`},children:[(0,C.jsxs)(c,{justify:`between`,style:{width:`100%`},children:[(0,C.jsx)(g,{sessionFrgmt:A||null,showQueuePosition:!1,showTooltip:!1}),(0,C.jsx)(h,{compact:!0,size:`small`,sessionFrgmt:A||null,hiddenButtonKeys:[`containerCommit`],primaryAppOption:b})]}),R&&(0,C.jsx)(c,{direction:`column`,gap:`xs`,style:{width:`100%`},children:(0,C.jsx)(m,{type:`secondary`,style:{fontSize:O(`--font-size-sm`),wordBreak:`break-word`},children:L??A.status_info})})]}),footer:d?(0,x.default)(p.created).format(`lll`):void 0}),A.id?(0,C.jsx)(T,{sessionRowId:f(A.id)}):null]}),t[8]=k,t[9]=w,t[10]=L,t[11]=R,t[12]=D,t[13]=A,t[14]=p,t[15]=b,t[16]=d,t[17]=E,t[18]=O,t[19]=z):z=t[19],z},T=e=>{"use memo";let t=(0,v.c)(2),{sessionRowId:n}=e,r;return t[0]===n?r=t[1]:(r={subscription:b,variables:{session_id:n}},t[0]=n,t[1]=r),(0,S.useSubscription)(r),null};export{w as default};
