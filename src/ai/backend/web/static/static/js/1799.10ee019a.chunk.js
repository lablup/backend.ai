"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[1799],{71801:(t,e,r)=>{r.d(e,{A:()=>d});var o=r(80404),n=r(70899),a=r(66596),c=r(91043),l=r(80963),s=r(46976),i=r.n(s),u=(r(55093),r(79569));const d=t=>{let{status:e="default",extraButtonTitle:r,onClickExtraButton:s,extra:d,style:p,...m}=t;const{token:h}=a.A.useToken(),f=d||r&&(0,u.jsx)(c.Ay,{type:"link",icon:"error"===e?(0,u.jsx)(o.A,{twoToneColor:h.colorError}):"warning"===e?(0,u.jsx)(n.A,{twoToneColor:h.colorWarning}):void 0,onClick:s,children:r})||void 0;return(0,u.jsx)(l.A,{className:"error"===e?"bai-card-error":"",style:i().extend(p,{borderColor:"error"===e?h.colorError:"warning"===e?h.colorWarning:"success"===e?h.colorSuccess:null===p||void 0===p?void 0:p.borderColor}),extra:f,...m})}},61799:(t,e,r)=>{r.r(e),r.d(e,{default:()=>k});var o=r(71801),n=r(72375),a=r(23441),c=r(40991),l=r(55093);const s={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M624 706.3h-74.1V464c0-4.4-3.6-8-8-8h-60c-4.4 0-8 3.6-8 8v242.3H400c-6.7 0-10.4 7.7-6.3 12.9l112 141.7a8 8 0 0012.6 0l112-141.7c4.1-5.2.4-12.9-6.3-12.9z"}},{tag:"path",attrs:{d:"M811.4 366.7C765.6 245.9 648.9 160 512.2 160S258.8 245.8 213 366.6C127.3 389.1 64 467.2 64 560c0 110.5 89.5 200 199.9 200H304c4.4 0 8-3.6 8-8v-60c0-4.4-3.6-8-8-8h-40.1c-33.7 0-65.4-13.4-89-37.7-23.5-24.2-36-56.8-34.9-90.6.9-26.4 9.9-51.2 26.2-72.1 16.7-21.3 40.1-36.8 66.1-43.7l37.9-9.9 13.9-36.6c8.6-22.8 20.6-44.1 35.7-63.4a245.6 245.6 0 0152.4-49.9c41.1-28.9 89.5-44.2 140-44.2s98.9 15.3 140 44.2c19.9 14 37.5 30.8 52.4 49.9 15.1 19.3 27.1 40.7 35.7 63.4l13.8 36.5 37.8 10C846.1 454.5 884 503.8 884 560c0 33.1-12.9 64.3-36.3 87.7a123.07 123.07 0 01-87.6 36.3H720c-4.4 0-8 3.6-8 8v60c0 4.4 3.6 8 8 8h40.1C870.5 760 960 670.5 960 560c0-92.7-63.1-170.7-148.6-193.3z"}}]},name:"cloud-download",theme:"outlined"};var i=r(36462),u=function(t,e){return l.createElement(i.A,(0,c.A)({},t,{ref:e,icon:s}))};const d=l.forwardRef(u);var p=r(79597),m=r(1364),h=r(91043),f=r(33364),b=r(79569);const v=t=>{const e=(0,l.useRef)(null),{t:r}=(0,f.Bd)(),o=(0,a.f0)();return(0,a.CX)(),(0,b.jsxs)(p.A,{ref:e,layout:"inline",requiredMark:"optional",...t,children:[(0,b.jsx)(p.A.Item,{name:"url",label:r("import.NotebookURL"),rules:[{required:!0},{pattern:new RegExp("^(https?)://([\\w./-]{1,}).ipynb$"),message:r("import.InvalidNotebookURL")},{type:"string",max:2048}],style:{flex:1},children:(0,b.jsx)(m.A,{placeholder:r("import.NotebookURL")})}),(0,b.jsx)(h.Ay,{icon:(0,b.jsx)(d,{}),type:"primary",onClick:()=>{var t;null===(t=e.current)||void 0===t||t.validateFields().then((t=>{const e=t.url.replace("/blob/","/").replace("github.com","raw.githubusercontent.com");const a={sessionName:"imported-notebook-"+(0,n.kX)(5),environments:{environment:"cr.backend.ai/stable/python"},bootstrap_script:"#!/bin/sh\ncurl -O "+e},c=new URLSearchParams;c.set("step","4"),c.set("formValues",JSON.stringify(a)),c.set("appOption",JSON.stringify({runtime:"jupyter",filename:e.split("/").pop()})),o(`/session/start?${c.toString()}`,{state:{from:{pathname:"/import",label:r("webui.menu.Import&Run")}}})})).catch((()=>{}))},children:r("import.GetAndRunNotebook")})]})};var g=r(66596);const k=()=>{const{t:t}=(0,f.Bd)(),{token:e}=g.A.useToken();return(0,b.jsx)(o.A,{title:t("import.ImportNotebook"),style:{maxWidth:728,marginBottom:e.paddingMD},children:(0,b.jsx)(v,{})})}},80404:(t,e,r)=>{r.d(e,{A:()=>s});var o=r(40991),n=r(55093);const a={icon:function(t,e){return{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z",fill:t}},{tag:"path",attrs:{d:"M512 140c-205.4 0-372 166.6-372 372s166.6 372 372 372 372-166.6 372-372-166.6-372-372-372zm171.8 527.1c1.2 1.5 1.9 3.3 1.9 5.2 0 4.5-3.6 8-8 8l-66-.3-99.3-118.4-99.3 118.5-66.1.3c-4.4 0-8-3.6-8-8 0-1.9.7-3.7 1.9-5.2L471 512.3l-130.1-155a8.32 8.32 0 01-1.9-5.2c0-4.5 3.6-8 8-8l66.1.3 99.3 118.4 99.4-118.5 66-.3c4.4 0 8 3.6 8 8 0 1.9-.6 3.8-1.8 5.2l-130.1 155 129.9 154.9z",fill:e}},{tag:"path",attrs:{d:"M685.8 352c0-4.4-3.6-8-8-8l-66 .3-99.4 118.5-99.3-118.4-66.1-.3c-4.4 0-8 3.5-8 8 0 1.9.7 3.7 1.9 5.2l130.1 155-130.1 154.9a8.32 8.32 0 00-1.9 5.2c0 4.4 3.6 8 8 8l66.1-.3 99.3-118.5L611.7 680l66 .3c4.4 0 8-3.5 8-8 0-1.9-.7-3.7-1.9-5.2L553.9 512.2l130.1-155c1.2-1.4 1.8-3.3 1.8-5.2z",fill:t}}]}},name:"close-circle",theme:"twotone"};var c=r(36462),l=function(t,e){return n.createElement(c.A,(0,o.A)({},t,{ref:e,icon:a}))};const s=n.forwardRef(l)},70899:(t,e,r)=>{r.d(e,{A:()=>s});var o=r(40991),n=r(55093);const a={icon:function(t,e){return{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M955.7 856l-416-720c-6.2-10.7-16.9-16-27.7-16s-21.6 5.3-27.7 16l-416 720C56 877.4 71.4 904 96 904h832c24.6 0 40-26.6 27.7-48zm-783.5-27.9L512 239.9l339.8 588.2H172.2z",fill:t}},{tag:"path",attrs:{d:"M172.2 828.1h679.6L512 239.9 172.2 828.1zM560 720a48.01 48.01 0 01-96 0 48.01 48.01 0 0196 0zm-16-304v184c0 4.4-3.6 8-8 8h-48c-4.4 0-8-3.6-8-8V416c0-4.4 3.6-8 8-8h48c4.4 0 8 3.6 8 8z",fill:e}},{tag:"path",attrs:{d:"M464 720a48 48 0 1096 0 48 48 0 10-96 0zm16-304v184c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V416c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8z",fill:t}}]}},name:"warning",theme:"twotone"};var c=r(36462),l=function(t,e){return n.createElement(c.A,(0,o.A)({},t,{ref:e,icon:a}))};const s=n.forwardRef(l)}}]);
//# sourceMappingURL=1799.10ee019a.chunk.js.map