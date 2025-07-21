"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[997],{80057:(e,t,n)=>{n.d(t,{A:()=>u});var o=n(26395),i=n(16042),r=n(60073),a=n(77397),s=n(98311),d=n.n(s),c=n(55202),l=n(52426);const m=(0,a.rU)((e=>{let{css:t,token:n}=e;return{board:t`
      .bai_board_placeholder {
        border-radius: var(--token-borderRadius) !important;
      }
      .bai_board_placeholder--active {
        background-color: var(--token-colorSplit) !important ;
      }
      .bai_board_placeholder--hover {
        background-color: var(--token-colorPrimaryHover) !important ;
        // FIXME: global token doesn't exist, so opacity fits color
        opacity: 0.3;
      }
      .bai_board_handle button span {
        color: ${n.colorTextTertiary} !important;
      }
      .bai_board_container-override
        > div:first-child
        > div:nth-child(2)
        > div:first-child {
        padding: 0 !important;
      }
    `,disableResize:t`
      .bai_board_resizer {
        display: none !important;
      }
    `,disableMove:t`
      .bai_board_handle {
        display: none !important;
      }
      .bai_board_header {
        display: none !important;
      }
    `,boardItems:t`
      & > div:first-child {
        border-radius: var(--token-borderRadius) !important;
        background-color: var(--token-colorBgContainer) !important;
        border: 1px solid ${n.colorBorderSecondary} !important;
      }

      & > div:first-child > div:first-child > div:first-child {
        margin-bottom: var(--token-margin);
        background-color: var(--token-colorBgContainer) !important;
        position: absolute;
        z-index: 1;
      }
    `,disableBorder:t`
      & > div:first-child {
        border: none !important;
      }
    `}})),u=e=>{let{items:t,resizable:n=!1,movable:a=!1,bordered:s=!1,...u}=e;const{styles:v}=m();return(0,l.jsx)(o.A,{className:d()(v.board,!a&&v.disableMove,!n&&v.disableResize),empty:!0,renderItem:e=>(0,l.jsx)(i.A,{className:d()(v.boardItems,!s&&v.disableBorder),i18nStrings:{dragHandleAriaLabel:"",dragHandleAriaDescription:"",resizeHandleAriaLabel:"",resizeHandleAriaDescription:""},children:(0,l.jsx)(c.Suspense,{fallback:(0,l.jsx)(r.A,{active:!0}),children:e.data.content})},e.id),items:t,i18nStrings:(()=>{const e=(e,t,n)=>[e,t.length>0?`Conflicts with ${t.map((e=>e.data.title)).join(", ")}.`:"",n.length>0?`Disturbed ${n.length} items.`:""].filter(Boolean).join(" ");return{liveAnnouncementDndStarted:e=>"resize"===e?"Resizing":"Dragging",liveAnnouncementDndItemReordered:t=>{const n=`column ${t.placement.x+1}`,o=`row ${t.placement.y+1}`;return e(`Item moved to ${"horizontal"===t.direction?n:o}.`,t.conflicts,t.disturbed)},liveAnnouncementDndItemResized:t=>{const n=t.isMinimalColumnsReached?" (minimal)":"",o=t.isMinimalRowsReached?" (minimal)":"",i="horizontal"===t.direction?`columns ${t.placement.width}${n}`:`rows ${t.placement.height}${o}`;return e(`Item resized to ${i}.`,t.conflicts,t.disturbed)},liveAnnouncementDndItemInserted:t=>{const n=`column ${t.placement.x+1}`,o=`row ${t.placement.y+1}`;return e(`Item inserted to ${n}, ${o}.`,t.conflicts,t.disturbed)},liveAnnouncementDndCommitted:e=>`${e} committed`,liveAnnouncementDndDiscarded:e=>`${e} discarded`,liveAnnouncementItemRemoved:t=>e(`Removed item ${t.item.data.title}.`,[],t.disturbed),navigationAriaLabel:"Board navigation",navigationAriaDescription:"Click on non-empty item to move focus over",navigationItemAriaLabel:e=>e?e.data.title:"Empty"}})(),...u})}},90997:(e,t,n)=>{n.r(t),n.d(t,{default:()=>I});var o=n(223),i=n(81751),r=n(7885),a=n(25483),s=n(37090),d=n(64428),c=n.n(d),l=n(98983),m=n(55202),u=n(52426);const v=e=>{let{style:t,...n}=e;const o=(0,i.CX)(),{token:d}=s.A.useToken(),{data:m}=(0,r.nj)({queryKey:["baiClient","service","get_announcement"],queryFn:()=>o.service.get_announcement()});return c().isEmpty(m.message)?"":(0,u.jsx)(a.A,{description:(0,u.jsx)("div",{style:{marginBottom:-1*d.marginSM},children:(0,u.jsx)(l.Ay,{options:{overrides:{p:{props:{style:{marginTop:0,marginBottom:d.marginSM}}}}},children:m.message+"<p></p>"})}),...n})};var p=n(80057),h=n(32630),b=n(53641),g=n(36162),f=n(97990);const A=e=>{var t;let{...n}=e;const o=(0,b.M)(),i=(null===(t=(0,m.useContext)(f.Ay.ConfigContext).theme)||void 0===t?void 0:t.algorithm)===s.A.darkAlgorithm,r={token:{colorPrimary:(0,g.A)().secondary}};return(0,u.jsx)(f.Ay,{...n,theme:{...i?c().merge({},null===o||void 0===o?void 0:o.dark,r,n.theme):c().merge({},null===o||void 0===o?void 0:o.light,r,n.theme),algorithm:i?s.A.darkAlgorithm:s.A.defaultAlgorithm}})};var S=n(65079),y=n(6017),x=n(79678),k=n(15756),_=n(44127),j=n(81679);const z={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"defs",attrs:{},children:[{tag:"style",attrs:{}}]},{tag:"path",attrs:{d:"M464 144H160c-8.8 0-16 7.2-16 16v304c0 8.8 7.2 16 16 16h304c8.8 0 16-7.2 16-16V160c0-8.8-7.2-16-16-16zm-52 268H212V212h200v200zm452-268H560c-8.8 0-16 7.2-16 16v304c0 8.8 7.2 16 16 16h304c8.8 0 16-7.2 16-16V160c0-8.8-7.2-16-16-16zm-52 268H612V212h200v200zm52 132H560c-8.8 0-16 7.2-16 16v304c0 8.8 7.2 16 16 16h304c8.8 0 16-7.2 16-16V560c0-8.8-7.2-16-16-16zm-52 268H612V612h200v200zM424 712H296V584c0-4.4-3.6-8-8-8h-48c-4.4 0-8 3.6-8 8v128H104c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8h128v128c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V776h128c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8z"}}]},name:"appstore-add",theme:"outlined"};var C=n(42688),w=function(e,t){return m.createElement(C.A,(0,j.A)({},e,{ref:t,icon:z}))};const M=m.forwardRef(w);var $=n(58923),H=n(90635);const I=()=>{var e,t,n,r,s,d;const{t:l}=(0,H.Bd)(),b=(0,i.CX)(),g=null!==(e=null===b||void 0===b||null===(t=b._config)||void 0===t?void 0:t.blockList)&&void 0!==e?e:[],f=null!==(n=null===b||void 0===b||null===(r=b._config)||void 0===r?void 0:r.inactiveList)&&void 0!==n?n:[],j=null!==(s=null===b||void 0===b||null===(d=b._config)||void 0===d?void 0:d.enableModelFolders)&&void 0!==s&&s,z=(0,i.f0)(),[C,w]=(0,m.useState)(!1),{upsertNotification:I}=(0,y.js)(),{count:R}=(0,k.P)();(0,m.useEffect)((()=>{R<=0||I({key:"invitedFolders",message:l("data.InvitedFoldersTooltip",{count:R}),to:{search:new URLSearchParams({invitation:"true"}).toString()},open:!0,duration:0})}),[R,l,I]);const D=(0,S.LY)([{id:"createFolder",requiredMenuKey:"data",rowSpan:3,columnSpan:1,columnOffset:{6:0,4:0},data:{content:(0,u.jsx)(o.A,{title:l("start.CreateFolder"),description:l("start.CreateFolderDesc"),buttonText:l("start.button.CreateFolder"),icon:(0,u.jsx)(_.A,{}),onClick:()=>w(!0)})}},{id:"startSession",requiredMenuKey:"job",rowSpan:3,columnSpan:1,columnOffset:{6:1,4:1},data:{content:(0,u.jsx)(o.A,{title:l("start.StartSession"),description:l("start.StartSessionDesc"),buttonText:l("start.button.StartSession"),icon:(0,u.jsx)(M,{}),onClick:()=>z("/session/start")})}},{id:"startBatchSession",requiredMenuKey:"job",rowSpan:3,columnSpan:1,columnOffset:{6:2,4:2},data:{content:(0,u.jsx)(o.A,{title:l("start.StartBatchSession"),description:l("start.StartBatchSessionDesc"),buttonText:l("start.button.StartSession"),icon:(0,u.jsx)(M,{}),onClick:()=>{const e=new URLSearchParams;e.set("step","0"),e.set("formValues",JSON.stringify({sessionType:"batch"})),z(`/session/start?${e.toString()}`)}})}},j&&{id:"modelService",rowSpan:3,requiredMenuKey:"serving",columnSpan:1,columnOffset:{6:0,4:0},data:{content:(0,u.jsx)(A,{children:(0,u.jsx)(o.A,{title:l("start.ModelService"),description:l("start.ModelServiceDesc"),buttonText:l("start.button.ModelService"),icon:(0,u.jsx)(M,{}),onClick:()=>z("/service/start")})})}}]).filter((e=>!c().includes([...g,...f],e.requiredMenuKey))),[B,V]=(0,x.q)("start_page_board_items"),L=B?(0,S.LY)(c().map(B,(e=>{const t=c().find(D,(t=>t.id===e.id));return t?{...e,data:t.data}:null}))):D,[T,q]=(0,m.useState)(L);return(0,u.jsxs)($.so,{direction:"column",gap:"md",align:"stretch",children:[(0,u.jsx)(v,{showIcon:!0,closable:!0}),(0,u.jsx)(p.A,{movable:!0,items:T,onItemsChange:e=>{const t=[...e.detail.items];q(t),V(c().map(t,(e=>c().omit(e,"data"))))}}),c().isEmpty(T)&&(0,u.jsx)(a.A,{type:"info",description:l("start.NoStartItems"),showIcon:!0}),(0,u.jsx)(h.A,{open:C,onRequestClose:e=>{w(!1),e&&z("/data")}})]})}},44127:(e,t,n)=>{n.d(t,{A:()=>d});var o=n(81679),i=n(55202);const r={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M484 443.1V528h-84.5c-4.1 0-7.5 3.1-7.5 7v42c0 3.8 3.4 7 7.5 7H484v84.9c0 3.9 3.2 7.1 7 7.1h42c3.9 0 7-3.2 7-7.1V584h84.5c4.1 0 7.5-3.2 7.5-7v-42c0-3.9-3.4-7-7.5-7H540v-84.9c0-3.9-3.1-7.1-7-7.1h-42c-3.8 0-7 3.2-7 7.1zm396-144.7H521L403.7 186.2a8.15 8.15 0 00-5.5-2.2H144c-17.7 0-32 14.3-32 32v592c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V330.4c0-17.7-14.3-32-32-32zM840 768H184V256h188.5l119.6 114.4H840V768z"}}]},name:"folder-add",theme:"outlined"};var a=n(42688),s=function(e,t){return i.createElement(a.A,(0,o.A)({},e,{ref:t,icon:r}))};const d=i.forwardRef(s)}}]);
//# sourceMappingURL=997.7748b569.chunk.js.map