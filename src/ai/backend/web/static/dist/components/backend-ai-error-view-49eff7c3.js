import{B as e,d as t,I as s,b as a,f as o,i as r,a1 as i,a2 as l,y as c,j as n,t as d,_ as m,e as u,a as v}from"./backend-ai-webui-ab578ea5.js";
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */let h=class extends e{constructor(){super(...arguments),this.error_code=404}static get styles(){return[t,s,a,o,r`
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

      `]}async _viewStateChanged(e){await this.updateComplete}_moveTo(e=""){const t=""!==e?e:"summary";globalThis.history.pushState({},"","/summary"),i.dispatch(l(decodeURIComponent("/"+t),{}))}render(){return c`
    <link rel="stylesheet" href="resources/custom.css">
    <div class="horizontal center flex layout" style="margin:20px;">
      <img src="/resources/images/404_not_found.svg" style="width:500px;margin:20px;"/>
      <div class="vertical layout" style="width:100%;">
        <div class="title">${n("webui.NOTFOUND")}</div>
        <p class="description">${d("webui.DescNOTFOUND")}</p>
        <div>
          <mwc-button
              unelevated
              fullwidth
              id="go-to-summary"
              label="${d("button.GoBackToSummaryPage")}"
              @click="${()=>this._moveTo("summary")}"></mwc-button>
        </div>
      </div>
    </div>
    `}};m([u({type:Number})],h.prototype,"error_code",void 0),h=m([v("backend-ai-error-view")],h);var p=h;export{p as default};
