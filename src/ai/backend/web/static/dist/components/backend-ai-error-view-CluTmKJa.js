import{B as e,b as t,I as o,a as s,c as a,i as r,s as i,l as n,k as l,j as c,f as d,_ as u,n as m,t as v}from"./backend-ai-webui-CrYAk2kU.js";let h=class extends e{constructor(){super(...arguments),this.error_code=404}static get styles(){return[t,o,s,a,r`
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
      `]}async _viewStateChanged(e){await this.updateComplete}_moveTo(e=""){const t=""!==e?e:"summary";globalThis.history.pushState({},"","/summary"),i.dispatch(n(decodeURIComponent("/"+t),{})),document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}render(){return l`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal center flex layout" style="margin:20px;">
        <img
          src="/resources/images/404_not_found.svg"
          style="width:500px;margin:20px;"
        />
        <div class="vertical layout" style="width:100%;">
          <div class="title">${c("webui.NotFound")}</div>
          <p class="description">${d("webui.DescNotFound")}</p>
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
    `}};u([m({type:Number})],h.prototype,"error_code",void 0),h=u([v("backend-ai-error-view")],h);var p=h;export{p as default};
