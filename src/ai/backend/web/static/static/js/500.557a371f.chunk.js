"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[500],{31500:(e,t,n)=>{n.r(t),n.d(t,{default:()=>u});var s=n(25339),c=n(91412),o=n(29871),r=n(187),i=n(97041),l=n(5336),a=n(13279),d=n(6932),h=n(65080),p=n(42923),m=n(82028),x=(n(76998),n(77678)),A=n(23446);const{Text:j}=a.A,u=e=>{let{...t}=e;const{t:n}=(0,x.Bd)(),{value:a,dispatchEvent:u}=(0,c.useWebComponentInfo)();let v;try{v=JSON.parse(a||"")}catch(f){v={open:!1,servicePorts:[]}}const{open:y,servicePorts:b}=v;return(0,A.jsx)(s.A,{open:y,onCancel:()=>{u("cancel",null)},centered:!0,title:n("environment.ManageApps"),...t,footer:[(0,A.jsxs)(o.A,{direction:"row",justify:"between",children:[(0,A.jsx)(d.Ay,{type:"text",danger:!0,children:n("button.Reset")}),(0,A.jsx)(d.Ay,{type:"primary",icon:(0,A.jsx)(r.A,{}),children:n("button.Save")})]})],children:(0,A.jsx)(h.A,{initialValues:{apps:b},onFinish:e=>{console.log("Saved settings. ",e)},autoComplete:"off",children:(0,A.jsxs)(o.A,{direction:"column",gap:"xs",children:[(0,A.jsxs)(p.A.Compact,{block:!0,children:[(0,A.jsx)(j,{style:{width:"30%"},children:n("environment.AppName")}),(0,A.jsx)(j,{style:{width:"30%"},children:n("environment.Protocol")}),(0,A.jsx)(j,{style:{width:"30%"},children:n("environment.Port")}),(0,A.jsx)(j,{style:{width:"10%",textAlign:"center"}})]}),(0,A.jsx)(h.A.List,{name:"apps",children:(e,t)=>{let{add:s,remove:c}=t;return(0,A.jsxs)(o.A,{direction:"column",gap:"sm",children:[e.map((e=>(0,A.jsxs)(o.A,{direction:"row",gap:"xs",children:[(0,A.jsxs)(p.A.Compact,{block:!0,children:[(0,A.jsx)(h.A.Item,{...e,name:[e.name,"app"],rules:[{required:!0,message:n("environment.AppNameMustNotBeEmpty")}],noStyle:!0,children:(0,A.jsx)(m.A,{})}),(0,A.jsx)(h.A.Item,{...e,name:[e.name,"protocol"],noStyle:!0,children:(0,A.jsx)(m.A,{})}),(0,A.jsx)(h.A.Item,{...e,name:[e.name,"port"],noStyle:!0,children:(0,A.jsx)(m.A,{})})]},e.key),(0,A.jsx)(d.Ay,{type:"text",onClick:()=>c(e.name),style:{width:"10%"},icon:(0,A.jsx)(i.A,{})})]}))),(0,A.jsx)(d.Ay,{type:"dashed",onClick:()=>s(),block:!0,icon:(0,A.jsx)(l.A,{}),children:n("button.Add")})]})}})]})})})}},97041:(e,t,n)=>{n.d(t,{A:()=>l});var s=n(58168),c=n(76998);const o={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M360 184h-8c4.4 0 8-3.6 8-8v8h304v-8c0 4.4 3.6 8 8 8h-8v72h72v-80c0-35.3-28.7-64-64-64H352c-35.3 0-64 28.7-64 64v80h72v-72zm504 72H160c-17.7 0-32 14.3-32 32v32c0 4.4 3.6 8 8 8h60.4l24.7 523c1.6 34.1 29.8 61 63.9 61h454c34.2 0 62.3-26.8 63.9-61l24.7-523H888c4.4 0 8-3.6 8-8v-32c0-17.7-14.3-32-32-32zM731.3 840H292.7l-24.2-512h487l-24.2 512z"}}]},name:"delete",theme:"outlined"};var r=n(76228),i=function(e,t){return c.createElement(r.A,(0,s.A)({},e,{ref:t,icon:o}))};const l=c.forwardRef(i)}}]);
//# sourceMappingURL=500.557a371f.chunk.js.map