import{_ as a,e,B as t,c as s,I as i,a as r,i as n,x as d,p as c,q as l}from"./backend-ai-webui-75df15ed.js";let o=class extends t{static get styles(){return[s,i,r,n``]}async _viewStateChanged(a){await this.updateComplete}render(){return d`
      <backend-ai-react-serving-list
        @moveTo="${a=>{const e=a.detail.path,t=a.detail.params;globalThis.history.pushState({},"",e+"?folder="+t.folder),c.dispatch(l(decodeURIComponent(e),t))}}"
      ></backend-ai-react-serving-list>
    `}};o=a([e("backend-ai-serving-list")],o);
