import{_ as e,e as a,B as t,c as s,I as i,a as r,i as n,x as d,j as c,k as o}from"./backend-ai-webui-dbad9af8.js";let l=class extends t{static get styles(){return[s,i,r,n``]}async _viewStateChanged(e){await this.updateComplete}render(){return d`
      <backend-ai-react-serving-list
        @moveTo="${e=>{const a=e.detail.path,t=e.detail.params;globalThis.history.pushState({},"",a+"?folder="+t.folder),c.dispatch(o(decodeURIComponent(a),t))}}"
      ></backend-ai-react-serving-list>
    `}};l=e([a("backend-ai-serving-view")],l);
