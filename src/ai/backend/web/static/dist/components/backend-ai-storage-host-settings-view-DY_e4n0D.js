import{_ as t,t as a,B as e,b as s,I as i,a as o,i as n,x as r,j as c,k as d}from"./backend-ai-webui-dvRyOX_e.js";let h=class extends e{static get styles(){return[s,i,o,n``]}async _viewStateChanged(t){await this.updateComplete}render(){return r`
      <backend-ai-react-storage-host-settings
        value="${window.location.pathname.split("/")[2]}"
        @moveTo="${t=>{const a=t.detail.path;globalThis.history.pushState({},"",a),c.dispatch(d(decodeURIComponent(a),{}))}}"
      ></backend-ai-react-storage-host-settings>
    `}};h=t([a("backend-ai-storage-host-settings-view")],h);
