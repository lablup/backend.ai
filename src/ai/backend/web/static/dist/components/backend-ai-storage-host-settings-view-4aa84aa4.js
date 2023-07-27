import{_ as a,e as t,B as e,c as s,I as i,a as o,i as n,x as c,a1 as r,a2 as d}from"./backend-ai-webui-aedf1078.js";
/**
 @license
Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
*/let h=class extends e{static get styles(){return[s,i,o,n`
      `]}async _viewStateChanged(a){await this.updateComplete}render(){return c`
      <backend-ai-react-storage-host-settings value="${window.location.pathname.split("/")[2]}"  @moveTo="${a=>{const t=a.detail.path;globalThis.history.pushState({},"",t),r.dispatch(d(decodeURIComponent(t),{}))}}"></backend-ai-react-storage-host-settings>
    `}};h=a([t("backend-ai-storage-host-settings-view")],h);
