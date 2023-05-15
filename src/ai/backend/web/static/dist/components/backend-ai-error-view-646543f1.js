import{B as e,d as t,I as s,b as a,f as o,i as r,D as i,aB as l,y as n,t as c,_ as d,e as m,a as u}from"./backend-ai-webui-8cfa3078.js";import{t as h}from"./translate-unsafe-html-04ec0865.js";
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */let v=class extends e{constructor(){super(...arguments),this.error_code=404}static get styles(){return[t,s,a,o,r`
      .title {
        font-size: 2em;
        font-weight: bolder;
        color: var(--general-navbar-footer-color, #424242);
        line-height: 1em;
      }

      .description {
        font-size: 1em;
        font-weight: normal;
        color: var(--general-sidebar-color, #949494);
      }

      mwc-button {
        width: auto;
      }

      `]}async _viewStateChanged(e){await this.updateComplete}_moveTo(e=""){const t=""!==e?e:"summary";globalThis.history.pushState({},"","/summary"),i.dispatch(l(decodeURIComponent("/"+t),{}))}render(){return n`
    <link rel="stylesheet" href="resources/custom.css">
    <div class="horizontal center flex layout" style="margin:20px;">
      <img src="/resources/images/404_not_found.svg" style="width:500px;margin:20px;"/>
      <div class="vertical layout" style="width:100%;">
        <div class="title">${h("webui.NOTFOUND")}</div>
        <p class="description">${c("webui.DescNOTFOUND")}</p>
        <div>
          <mwc-button
              unelevated
              fullwidth
              id="go-to-summary"
              label="${c("button.GoBackToSummaryPage")}"
              @click="${()=>this._moveTo("summary")}"></mwc-button>
        </div>
      </div>
    </div>
    `}};d([m({type:Number})],v.prototype,"error_code",void 0),v=d([u("backend-ai-error-view")],v);var p=v;export{p as default};
