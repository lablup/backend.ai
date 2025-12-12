import{_ as a,t as e,B as s,a as t,I as i,b as n,i as r,s as d,n as o,k as c}from"./backend-ai-webui-CiZihJrO.js";let l=class extends s{static get styles(){return[t,i,n,r``]}async _viewStateChanged(a){await this.updateComplete}render(){return c`
      <backend-ai-react-serving-list
        @moveTo="${a=>{const e=a.detail.path,s=a.detail.params;globalThis.history.pushState({},"",e+"?folder="+s.folder),d.dispatch(o(decodeURIComponent(e),s))}}"
      ></backend-ai-react-serving-list>
    `}};l=a([e("backend-ai-serving-view")],l);
