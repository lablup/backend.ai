import{_ as e,t as a,B as s,a as t,I as i,b as n,i as r,s as d,n as o,x as c}from"./backend-ai-webui-l_Uz0-VA.js";let l=class extends s{static get styles(){return[t,i,n,r``]}async _viewStateChanged(e){await this.updateComplete}render(){return c`
      <backend-ai-react-serving-list
        @moveTo="${e=>{const a=e.detail.path,s=e.detail.params;globalThis.history.pushState({},"",a+"?folder="+s.folder),d.dispatch(o(decodeURIComponent(a),s))}}"
      ></backend-ai-react-serving-list>
    `}};l=e([a("backend-ai-serving-view")],l);
