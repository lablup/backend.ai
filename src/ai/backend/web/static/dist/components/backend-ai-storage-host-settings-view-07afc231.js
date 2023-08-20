import{_ as t,e as a,B as e,c as s,I as i,a as o,i as n,x as c,N as r,O as d}from"./backend-ai-webui-d4819018.js";
/**
 @license
Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
*/let h=class extends e{static get styles(){return[s,i,o,n`
      `]}async _viewStateChanged(t){await this.updateComplete}render(){return c`
      <backend-ai-react-storage-host-settings value="${window.location.pathname.split("/")[2]}"  @moveTo="${t=>{const a=t.detail.path;globalThis.history.pushState({},"",a),r.dispatch(d(decodeURIComponent(a),{}))}}"></backend-ai-react-storage-host-settings>
    `}};h=t([a("backend-ai-storage-host-settings-view")],h);
