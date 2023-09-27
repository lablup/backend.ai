import{B as e,c as t,I as s,a as o,d as a,i as r,p as i,q as l,x as c,h as n,t as d,_ as m,n as u,e as h}from"./backend-ai-webui-75df15ed.js";let v=class extends e{constructor(){super(...arguments),this.error_code=404}static get styles(){return[t,s,o,a,r`
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
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal center flex layout" style="margin:20px;">
        <img
          src="/resources/images/404_not_found.svg"
          style="width:500px;margin:20px;"
        />
        <div class="vertical layout" style="width:100%;">
          <div class="title">${n("webui.NOTFOUND")}</div>
          <p class="description">${d("webui.DescNOTFOUND")}</p>
          <div>
            <mwc-button
              unelevated
              fullwidth
              id="go-to-summary"
              label="${d("button.GoBackToSummaryPage")}"
              @click="${()=>this._moveTo("summary")}"
            ></mwc-button>
          </div>
        </div>
      </div>
    `}};m([u({type:Number})],v.prototype,"error_code",void 0),v=m([h("backend-ai-error-view")],v);var p=v;export{p as default};
