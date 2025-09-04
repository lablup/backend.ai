"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[8361],{88361:(e,t,n)=>{n.r(t),n.d(t,{default:()=>w});var a=n(53611),s=n(37769),i=n(41777),r=n(50377),c=n(5837),l=n(76614),d=n(62081),o=n(26845),h=n(77986),g=n(55004),m=n(35422),p=n(27966);const x=(0,h.rU)((e=>{let{css:t,token:n}=e;return{cardList:t`
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
    `}})),{Meta:u}=r.A,j=e=>{let{agent:t}=e;const n=t.meta.tags||[],{styles:s}=x();return(0,p.jsx)(r.A,{hoverable:!0,children:(0,p.jsxs)(g.OO,{direction:"column",align:"stretch",gap:"xs",justify:"between",style:{minHeight:"200px"},children:[(0,p.jsx)(u,{title:t.meta.title,avatar:(0,p.jsx)(a.W,{name:t.meta.avatar,height:150,width:150}),description:t.meta.descriptions,className:s.meta}),(0,p.jsxs)(g.OO,{direction:"row",justify:"start",style:{width:"100%",flexShrink:1},gap:6,wrap:"wrap",children:[(0,p.jsx)(c.A,{color:"orange-inverse",children:t.endpoint},t.endpoint),n.map(((e,t)=>(0,p.jsx)(c.A,{children:e},t)))]})]})})},k=e=>{let{agents:t,onClickAgent:n}=e;const{styles:a}=x();return(0,p.jsx)(l.A,{className:a.cardList,grid:{gutter:16,xs:1,sm:1,md:2,lg:2,xl:3,xxl:4},dataSource:t,renderItem:e=>(0,p.jsx)(l.A.Item,{style:{height:"100%"},onClick:()=>n(e),children:(0,p.jsx)(j,{agent:e})})})},w=()=>{const{token:e}=d.A.useToken(),{agents:t}=(0,i.B)(),n=(0,s.f0)();return(0,p.jsx)(m.Suspense,{fallback:(0,p.jsx)(o.A,{active:!0,style:{padding:e.paddingMD}}),children:(0,p.jsx)(g.OO,{direction:"column",align:"stretch",justify:"center",gap:"lg",children:(0,p.jsx)(k,{agents:t,onClickAgent:e=>{n({pathname:"/chat",search:new URLSearchParams({endpointId:e.endpoint_id,agentId:e.id}).toString()})}})})})}}}]);
//# sourceMappingURL=8361.c3f62e07.chunk.js.map