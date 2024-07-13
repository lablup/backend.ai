import{_ as e,t as a,B as t,b as s,I as i,a as r,i as n,x as d,j as o,k as c}from"./backend-ai-webui-CHZ-bl4E.js";let l=class extends t{static get styles(){return[s,i,r,n``]}async _viewStateChanged(e){await this.updateComplete}render(){return d`
      <backend-ai-react-serving-list
        @moveTo="${e=>{const a=e.detail.path,t=e.detail.params;globalThis.history.pushState({},"",a+"?folder="+t.folder),o.dispatch(c(decodeURIComponent(a),t))}}"
      ></backend-ai-react-serving-list>
    `}};l=e([a("backend-ai-serving-view")],l);
