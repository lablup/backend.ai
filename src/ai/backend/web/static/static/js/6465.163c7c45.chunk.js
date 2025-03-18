"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[6465],{50396:(e,t,n)=>{n.d(t,{W:()=>i});var s=n(63075),a=(n(53350),n(60598));const i=e=>{let{name:t,height:n,width:i}=e;const r=s.Pt.icons[null!==t&&void 0!==t?t:"pure"];return(0,a.jsx)("svg",{xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 32 32",height:n,width:i,role:"img",dangerouslySetInnerHTML:{__html:r.body}})}},31513:(e,t,n)=>{n.d(t,{B:()=>r});var s=n(23441),a=n(73e3),i=n(53350);const r=()=>{var e;const[t,n]=(0,s.Tw)("first"),{data:r,isLoading:l}=(0,a.nN)({queryKey:["useAgents",t],queryFn:()=>fetch("resources/ai-agents.json").then((e=>e.json())),staleTime:864e5});return{agents:null!==(e=null===r||void 0===r?void 0:r.agents)&&void 0!==e?e:[],isLoading:l,refresh:(0,i.useCallback)((()=>n()),[n])}}},26465:(e,t,n)=>{n.r(t),n.d(t,{default:()=>v});var s=n(72338),a=n(50396),i=n(23441),r=n(31513),l=n(20418),d=n(24798),c=n(56459),o=n(9571),g=n(91867),h=n(43403),u=n(53350),m=n(60598);const x=(0,h.rU)((e=>{let{css:t,token:n}=e;return{cardList:t`
      .and-col {
        height: calc(100% - ${n.marginMD});
      }
      .ant-tag {
        margin-inline-end: 0;
      }
    `,meta:t`
      .ant-card-meta-description {
        max-height: 6.4em; // Adjusted for 4 lines
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .ant-card-meta-title {
        white-space: normal;
      }
    `}})),{Meta:p}=l.A,j=e=>{let{agent:t}=e;const n=t.meta.tags||[],{styles:i}=x();return(0,m.jsx)(l.A,{hoverable:!0,children:(0,m.jsxs)(s.A,{direction:"column",align:"stretch",gap:"xs",justify:"between",style:{minHeight:"200px"},children:[(0,m.jsx)(p,{title:t.meta.title,avatar:(0,m.jsx)(a.W,{name:t.meta.avatar,height:150,width:150}),description:t.meta.descriptions,className:i.meta}),(0,m.jsxs)(s.A,{direction:"row",justify:"start",style:{width:"100%",flexShrink:1},gap:6,wrap:"wrap",children:[(0,m.jsx)(d.A,{color:"orange-inverse",children:t.endpoint},t.endpoint),n.map(((e,t)=>(0,m.jsx)(d.A,{children:e},t)))]})]})})},w=e=>{let{agents:t,onClickAgent:n}=e;const{styles:s}=x();return(0,m.jsx)(c.A,{className:s.cardList,grid:{gutter:16,xs:1,sm:1,md:2,lg:2,xl:3,xxl:4},dataSource:t,renderItem:e=>(0,m.jsx)(c.A.Item,{style:{height:"100%"},onClick:()=>n(e),children:(0,m.jsx)(j,{agent:e})})})},v=()=>{const{token:e}=o.A.useToken(),{agents:t}=(0,r.B)(),n=(0,i.f0)();return(0,m.jsx)(u.Suspense,{fallback:(0,m.jsx)(g.A,{active:!0,style:{padding:e.paddingMD}}),children:(0,m.jsx)(s.A,{direction:"column",align:"stretch",justify:"center",gap:"lg",children:(0,m.jsx)(w,{agents:t,onClickAgent:e=>{n(`/chat?endpointId=${e.endpoint_id}&agentId=${e.id}`)}})})})}}}]);
//# sourceMappingURL=6465.163c7c45.chunk.js.map