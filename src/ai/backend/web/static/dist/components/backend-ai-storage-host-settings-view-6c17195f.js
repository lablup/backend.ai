import{B as a,d as t,I as e,b as s,i,y as o,a1 as n,a2 as r,_ as d,a as c}from"./backend-ai-webui-ab578ea5.js";
/**
 @license
Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
*/let h=class extends a{static get styles(){return[t,e,s,i`
      `]}async _viewStateChanged(a){await this.updateComplete}render(){return o`
      <backend-ai-react-storage-host-settings value="${window.location.pathname.split("/")[2]}"  @moveTo="${a=>{const t=a.detail.path;globalThis.history.pushState({},"",t),n.dispatch(r(decodeURIComponent(t),{}))}}"></backend-ai-react-storage-host-settings>
    `}};h=d([c("backend-ai-storage-host-settings-view")],h);var l=h;export{l as default};
