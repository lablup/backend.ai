"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[6161],{36161:(e,n,t)=>{t.a(e,(async(e,r)=>{try{t.r(n),t.d(n,{default:()=>y});var a=t(6070),o=t(7786),s=t(59764),i=t(72338),l=t(11956),u=t(66596),c=t(12221),d=t(88221),f=t(78502),h=t.n(f),v=t(55093),p=t(33364),S=t(79569),g=e([s]);s=(g.then?(await g)():g)[0];const y=e=>{let{...n}=e;const{t:t}=(0,p.Bd)(),{token:r}=u.A.useToken(),[f,{toggle:g}]=(0,l.A)(!1),[y,A]=v.useState(),{dispatchEvent:m}=(0,s.useWebComponentInfo)(),x=e=>{A(e),m("change",e)},b=(0,v.useRef)(null);return(0,S.jsxs)(S.Fragment,{children:[(0,S.jsx)(c.A.Text,{type:"secondary",style:{fontSize:r.fontSizeSM},children:t("session.launcher.SessionStartTime")}),(0,S.jsxs)(i.A,{align:"start",gap:"sm",children:[(0,S.jsx)(d.A,{checked:f,onChange:e=>{g();const n=e?h()().add(2,"minutes").toISOString():void 0;x(n)},children:t("session.launcher.Enable")}),(0,S.jsxs)(i.A,{direction:"column",align:"end",children:[(0,S.jsx)(o.A,{ref:b,...n,popupStyle:{position:"fixed"},disabledDate:e=>e.isBefore(h()().startOf("day")),localFormat:!0,disabled:!f,showTime:{hideDisabledOptions:!0},value:f?y:void 0,onChange:e=>{x(e)},onCalendarChange:()=>{var e;null===(e=b.current)||void 0===e||e.focus()},onPanelChange:()=>{var e;null===(e=b.current)||void 0===e||e.focus()},status:f&&!y?"warning":h()(y).isBefore(h()())?"error":void 0,needConfirm:!1,showNow:!1}),f&&y&&!h()(y).isBefore(h()())&&(0,S.jsxs)(c.A.Text,{type:"secondary",style:{fontSize:r.fontSizeSM-2},children:["(",t("session.launcher.StartAfter"),(0,S.jsx)(a.A,{callback:()=>h()(y).fromNow(),delay:1e3}),")"]}),f&&!y&&(0,S.jsx)(c.A.Text,{type:"warning",style:{fontSize:r.fontSizeSM-2},children:t("session.launcher.StartTimeDoesNotApply")}),f&&y&&h()(y).isBefore(h()())&&(0,S.jsx)(c.A.Text,{type:"danger",style:{fontSize:r.fontSizeSM-2},children:t("session.launcher.StartTimeMustBeInTheFuture")})]})]})]})};r()}catch(y){r(y)}}))},7786:(e,n,t)=>{t.d(n,{A:()=>d});var r=t(62976),a=t(80899),o=t(78502),s=t.n(o),i=t(46976),l=t.n(i),u=t(55093),c=t(79569);const d=u.forwardRef(((e,n)=>{let{value:t,onChange:o,localFormat:i,...u}=e;const[,d]=(0,r.A)({value:t,onChange:o});return(0,c.jsx)(a.A,{ref:n,value:t?s()(t):void 0,onChange:e=>{var n,t,r;l().isArray(e)&&(e=e[0]);const a=i?null===(n=e)||void 0===n?void 0:n.format():null===(t=e)||void 0===t||null===(r=t.tz())||void 0===r?void 0:r.toISOString();d(a)},...u})}))},62976:(e,n,t)=>{t.d(n,{A:()=>l});var r=t(92509),a=t(55093),o=t(99358),s=t(4060);const i=function(){var e=(0,r.zs)((0,a.useState)({}),2)[1];return(0,a.useCallback)((function(){return e({})}),[])};const l=function(e,n){void 0===e&&(e={}),void 0===n&&(n={});var t=n.defaultValue,l=n.defaultValuePropName,u=void 0===l?"defaultValue":l,c=n.valuePropName,d=void 0===c?"value":c,f=n.trigger,h=void 0===f?"onChange":f,v=e[d],p=Object.prototype.hasOwnProperty.call(e,d),S=(0,a.useMemo)((function(){return p?v:Object.prototype.hasOwnProperty.call(e,u)?e[u]:t}),[]),g=(0,a.useRef)(S);p&&(g.current=v);var y=i();return[g.current,(0,s.A)((function(n){for(var t=[],a=1;a<arguments.length;a++)t[a-1]=arguments[a];var s=(0,o.Tn)(n)?n(g.current):n;p||(g.current=s,y()),e[h]&&e[h].apply(e,(0,r.fX)([s],(0,r.zs)(t),!1))}))]}}}]);
//# sourceMappingURL=6161.38399bfa.chunk.js.map