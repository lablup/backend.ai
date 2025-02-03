import{_ as a,t as e,B as s,b as t,I as i,a as r,i as n,k as d,s as l,l as o}from"./backend-ai-webui-CrYAk2kU.js";let c=class extends s{static get styles(){return[t,i,r,n``]}async _viewStateChanged(a){await this.updateComplete}render(){return d`
      <backend-ai-react-serving-list
        @moveTo="${a=>{const e=a.detail.path,s=a.detail.params;globalThis.history.pushState({},"",e+"?folder="+s.folder),l.dispatch(o(decodeURIComponent(e),s))}}"
      ></backend-ai-react-serving-list>
    `}};c=a([e("backend-ai-serving-view")],c);
