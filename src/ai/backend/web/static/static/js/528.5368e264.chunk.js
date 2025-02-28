"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[528],{8699:(e,t,n)=>{n.d(t,{A:()=>z});var r=n(23524),a=n(82776),o=n(9571),i=n(18659),s=n(37826),l=n(43403),c=n(62097),d=n.n(c),u=n(46976),h=n.n(u),p=n(53350),f=n(48556),b=n(60598);const w=(0,l.rU)((e=>{let{token:t,css:n}=e;return{resizableTable:n`
    .react-resizable-handle {
      position: absolute;
      inset-inline-end: 0px;
      bottom: 0;
      z-index: 1;
      width: 10px;
      height: 100%;
      cursor: col-resize;
    }
    .ant-table-cell {
      overflow: hidden;
      whitespace: 'pre';
      wordwrap: 'break-word';
    }
  `,neoHeader:n`
    thead.ant-table-thead > tr > th.ant-table-cell {
      font-weight: 500;
      color: ${t.colorTextTertiary};
    }
  `}})),g=e=>{const{onResize:t,width:n,onClick:r,...o}=e,i=(0,p.useRef)(null),[s,l]=(0,p.useState)(!1),c=(0,a.A)(s,{wait:100});return(0,p.useEffect)((()=>{i.current&&h().isUndefined(n)&&(null===t||void 0===t||t(void 0,{size:{width:i.current.offsetWidth,height:i.current.offsetHeight},node:i.current,handle:"e"}))})),h().isUndefined(n)?(0,b.jsx)("th",{ref:i,...o}):(0,b.jsx)(f.Resizable,{width:n,height:0,handle:(0,b.jsx)("span",{className:"react-resizable-handle",onClick:e=>{e.stopPropagation()}}),onResize:t,onResizeStart:()=>{l(!0)},onResizeStop:()=>{l(!1)},draggableOpts:{enableUserSelectHack:!1},children:(0,b.jsx)("th",{onClick:e=>{c?e.preventDefault():null===r||void 0===r||r(e)},...o})})},v=(e,t)=>e.key||`index_${t}`,z=e=>{let{resizable:t=!1,columns:n,components:a,neoStyle:l,loading:c,...u}=e;const{styles:f}=w(),{token:z}=o.A.useToken(),{isDarkMode:k}=(0,r.e)(),[m,S]=(0,p.useState)((e=>{const t={};return h().each(e,((e,n)=>{t[v(e,n)]=e.width})),t})(n)),y=(0,p.useMemo)((()=>t?h().map(n,((e,t)=>({...e,width:m[v(e,t)]||e.width,onHeaderCell:e=>({width:e.width,onResize:(n,r)=>{let{size:a}=r;S((n=>({...n,[v(e,t)]:a.width})))}})}))):n),[t,n,m]);return(0,b.jsx)(i.Ay,{theme:{components:{Table:!k&&l?{headerBg:"#E3E3E3",headerSplitColor:z.colorTextQuaternary}:void 0}},children:(0,b.jsx)(s.A,{sortDirections:["descend","ascend","descend"],showSorterTooltip:!1,className:d()(t&&f.resizableTable,l&&f.neoHeader),style:{opacity:c?.7:1,transition:"opacity 0.3s ease"},components:t?h().merge(a||{},{header:{cell:g}}):a,columns:y,...u})})}},54690:(e,t,n)=>{n.d(t,{w4:()=>i});var r=n(46976),a=n.n(r),o=n(53350);n(22018),n(32043);const i=e=>{const[t,n]=(0,o.useState)(e);return{baiPaginationOption:{limit:t.pageSize,first:t.pageSize,offset:t.current>1?(t.current-1)*t.pageSize:0},tablePaginationOption:{pageSize:t.pageSize,current:t.current},setTablePaginationOption:e=>{a().isEqual(e,t)||n((t=>({...t,...e})))}}}},28567:(e,t,n)=>{n.d(t,{A:()=>l});var r=n(40991),a=n(53350),o=n(14334),i=n(90055),s=function(e,t){return a.createElement(i.A,(0,r.A)({},e,{ref:t,icon:o.A}))};const l=a.forwardRef(s)},51847:(e,t,n)=>{n.d(t,{A:()=>l});var r=n(92509),a=n(53350),o=n(66413),i=n(7447);const s=function(){var e=(0,r.zs)((0,a.useState)({}),2)[1];return(0,a.useCallback)((function(){return e({})}),[])};const l=function(e,t){void 0===e&&(e={}),void 0===t&&(t={});var n=t.defaultValue,l=t.defaultValuePropName,c=void 0===l?"defaultValue":l,d=t.valuePropName,u=void 0===d?"value":d,h=t.trigger,p=void 0===h?"onChange":h,f=e[u],b=Object.prototype.hasOwnProperty.call(e,u),w=(0,a.useMemo)((function(){return b?f:Object.prototype.hasOwnProperty.call(e,c)?e[c]:n}),[]),g=(0,a.useRef)(w);b&&(g.current=f);var v=s();return[g.current,(0,i.A)((function(t){for(var n=[],a=1;a<arguments.length;a++)n[a-1]=arguments[a];var i=(0,o.Tn)(t)?t(g.current):t;b||(g.current=i,v()),e[p]&&e[p].apply(e,(0,r.fX)([i],(0,r.zs)(n),!1))}))]}}}]);
//# sourceMappingURL=528.5368e264.chunk.js.map