"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[5844],{93463:(e,t,n)=>{n.r(t),n.d(t,{default:()=>w});var a=n(96520),s=n(7352),i=n(81751),r=n(86879),c=n(70554),l=n(36290),d=n(9987),o=n(37090),h=n(60073),g=n(77397),m=n(55202),p=n(52426);const x=(0,g.rU)((e=>{let{css:t,token:n}=e;return{cardList:t`
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
    `}})),{Meta:u}=c.A,j=e=>{let{agent:t}=e;const n=t.meta.tags||[],{styles:i}=x();return(0,p.jsx)(c.A,{hoverable:!0,children:(0,p.jsxs)(a.A,{direction:"column",align:"stretch",gap:"xs",justify:"between",style:{minHeight:"200px"},children:[(0,p.jsx)(u,{title:t.meta.title,avatar:(0,p.jsx)(s.W,{name:t.meta.avatar,height:150,width:150}),description:t.meta.descriptions,className:i.meta}),(0,p.jsxs)(a.A,{direction:"row",justify:"start",style:{width:"100%",flexShrink:1},gap:6,wrap:"wrap",children:[(0,p.jsx)(l.A,{color:"orange-inverse",children:t.endpoint},t.endpoint),n.map(((e,t)=>(0,p.jsx)(l.A,{children:e},t)))]})]})})},k=e=>{let{agents:t,onClickAgent:n}=e;const{styles:a}=x();return(0,p.jsx)(d.A,{className:a.cardList,grid:{gutter:16,xs:1,sm:1,md:2,lg:2,xl:3,xxl:4},dataSource:t,renderItem:e=>(0,p.jsx)(d.A.Item,{style:{height:"100%"},onClick:()=>n(e),children:(0,p.jsx)(j,{agent:e})})})},w=()=>{const{token:e}=o.A.useToken(),{agents:t}=(0,r.B)(),n=(0,i.f0)();return(0,p.jsx)(m.Suspense,{fallback:(0,p.jsx)(h.A,{active:!0,style:{padding:e.paddingMD}}),children:(0,p.jsx)(a.A,{direction:"column",align:"stretch",justify:"center",gap:"lg",children:(0,p.jsx)(k,{agents:t,onClickAgent:e=>{n({pathname:"/chat",search:new URLSearchParams({endpointId:e.endpoint_id,agentId:e.id}).toString()})}})})})}}}]);
//# sourceMappingURL=5844.2095446f.chunk.js.map