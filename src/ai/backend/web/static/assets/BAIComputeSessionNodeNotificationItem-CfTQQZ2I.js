import{bt as A,u as C,aK as E,A as j,cb as w,r as T,cB as R,n as a,cC as D,a6 as P,C as K,R as N,bz as z,af as B,c as U}from"./index-CwWAznqi.js";import{S as V}from"./SessionActionButtons-OpwSB8w_.js";import{S as q}from"./SessionStatusBadge-MHSUzVAj.js";import"./icons-BgdBQS0N.js";import"./lodash-RhKGq0BF.js";import"./TerminateSessionModal-Bj88xpmv.js";import"./useBackendAIAppLauncher-Dj1iRGeB.js";import"./BAIMetadataList-BYZUwKjA.js";import"./SourceCodeView-jXLvuWSO.js";import"./CodeBlock-CV2dJgqa.js";import"./useScrollableArea-Bsuw_xFk.js";import"./Grid-BAKellpz.js";import"./TagsInput-B_f8kLOn.js";import"./Tokenizer-Czn8bbzO.js";import"./groupItems-BfxkhRY8.js";import"./characters-DWaYg7k3.js";import"./Token-B6wppFPd.js";import"./CheckboxInput-Dvbz8RhO.js";import"./NumberInput-BX3bbN7A.js";import"./NumberInput-BAShrYzU.js";import"./useLocale-tF6sKPhr.js";import"./usePainKiller-BiH1iwVD.js";import"./SFTPConnectionInfoModal-D0lzKwMf.js";import"./BAIJupyterIcon-BjgUodlW.js";import"./ButtonGroup-DPQvGHtt.js";import"./HoverCard-5uBx5TYH.js";import"./astryxTagVariant-CibgwVXb.js";const x=(function(){var r=[{defaultValue:null,kind:"LocalArgument",name:"session_id"}],l=[{kind:"Variable",name:"sessionId",variableName:"session_id"}],i={alias:null,args:null,kind:"ScalarField",name:"reason",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"result",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"agent_ids",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"occupied_slots",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"starts_at",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"terminated_at",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"idle_checks",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},b=[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],F={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{fragment:{argumentDefinitions:r,kind:"Fragment",metadata:null,name:"BAIComputeSessionNodeNotificationItemSubscription",selections:[{alias:null,args:l,concreteType:"SchedulingBroadcastEventPayload",kind:"LinkedField",name:"schedulingEventsBySession",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"session",plural:!1,selections:[s,n,g,p,y,k,e,o,S,u,d,c,m,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,n,t,f,_,v,h,I,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"BAIImageNodeSimpleTagFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Subscription",abstractKey:null},kind:"Request",operation:{argumentDefinitions:r,kind:"Operation",name:"BAIComputeSessionNodeNotificationItemSubscription",selections:[{alias:null,args:l,concreteType:"SchedulingBroadcastEventPayload",kind:"LinkedField",name:"schedulingEventsBySession",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"session",plural:!1,selections:[s,n,g,p,y,k,e,o,S,u,d,c,m,{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,n,t,f,_,v,h,I,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"base_image_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"tags",plural:!0,selections:b,storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:b,storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"namespace",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},F],storageKey:null},F],storageKey:null}],storageKey:null}],storageKey:null},F],storageKey:null}],storageKey:null}]},params:{cacheID:"5c7c80f39ca3febd9ec8265e3b7ee651",id:null,metadata:{},name:"BAIComputeSessionNodeNotificationItemSubscription",operationKind:"subscription",text:`subscription BAIComputeSessionNodeNotificationItemSubscription(
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
`}}})();x.hash="f7b622d732889064edeaa6be25551f0d";const L={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIComputeSessionNodeNotificationItemFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{args:null,kind:"FragmentSpread",name:"SessionActionButtonsFragment"},{args:null,kind:"FragmentSpread",name:"SessionStatusBadgeFragment"}],type:"ComputeSessionNode",abstractKey:null};L.hash="8d53c71903c9d2d640979e4ab2758dfe";const Se=({sessionFrgmt:r,showDate:l,notification:i,primaryAppOption:s})=>{"use memo";const{closeNotification:n}=A(),{t:g}=C(),p=E(),{token:y}=j(),k=w(),e=T.useFragment(L,r);R(()=>{((e==null?void 0:e.status)==="TERMINATED"||(e==null?void 0:e.status)==="CANCELLED")&&setTimeout(()=>{n(i.key)},3e3)},[e==null?void 0:e.status]);const o=(()=>{var u,d,c,m;if(!(e!=null&&e.status_data))return null;try{const t=JSON.parse(e.status_data);return((u=t==null?void 0:t.error)==null?void 0:u.repr)??((m=(c=(d=t==null?void 0:t.error)==null?void 0:d.collection)==null?void 0:c[0])==null?void 0:m.repr)??null}catch{return null}})(),S=((e==null?void 0:e.status)==="ERROR"||(e==null?void 0:e.status)==="CANCELLED")&&(!!o||!!(e!=null&&e.status_info));return e&&a.jsxs(a.Fragment,{children:[a.jsx(D,{className:"bai-node-notification-item",title:a.jsxs(N,{ellipsis:!0,children:[g("general.Session"),": ",a.jsx(z,{style:{fontWeight:"normal"},title:e.name||"",onClick:()=>{p(`${k("session",{scope:"project"})}${e.id?`?${new URLSearchParams({sessionDetail:B(e.id)}).toString()}`:""}`),n(i.key)},children:e.name})]}),description:a.jsxs(K,{direction:"column",gap:"xs",style:{width:"100%"},children:[a.jsxs(K,{justify:"between",style:{width:"100%"},children:[a.jsx(q,{sessionFrgmt:e||null,showQueuePosition:!1,showTooltip:!1}),a.jsx(V,{compact:!0,size:"small",sessionFrgmt:e||null,hiddenButtonKeys:["containerCommit"],primaryAppOption:s})]}),S&&a.jsx(K,{direction:"column",gap:"xs",style:{width:"100%"},children:a.jsx(N,{type:"secondary",style:{fontSize:y("--font-size-sm"),wordBreak:"break-word"},children:o??e.status_info})})]}),footer:l?P(i.created).format("lll"):void 0}),e.id?a.jsx(O,{sessionRowId:B(e.id)}):null]})},O=r=>{"use memo";const l=U.c(3),{sessionRowId:i}=r;let s;l[0]===Symbol.for("react.memo_cache_sentinel")?(s=x,l[0]=s):s=l[0];let n;return l[1]!==i?(n={subscription:s,variables:{session_id:i}},l[1]=i,l[2]=n):n=l[2],T.useSubscription(n),null};export{Se as default};
//# sourceMappingURL=BAIComputeSessionNodeNotificationItem-CfTQQZ2I.js.map
