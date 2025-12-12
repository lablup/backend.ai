import{_ as e,c as t,t as o,B as s,a,I as r,b as i,e as n,i as c,s as l,n as d,o as u,h as m,k as v}from"./backend-ai-webui-CiZihJrO.js";let h=class extends s{constructor(){super(...arguments),this.error_code=404}static get styles(){return[a,r,i,n,c`
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
      `]}async _viewStateChanged(e){await this.updateComplete}_moveTo(e=""){const t=""!==e?e:"start";globalThis.history.pushState({},"","/start"),l.dispatch(d(decodeURIComponent("/"+t),{})),document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}render(){return v`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal center flex layout" style="margin:20px;">
        <img
          src="/resources/images/404_not_found.svg"
          style="width:500px;margin:20px;"
        />
        <div class="vertical layout" style="width:100%;">
          <div class="title">${u("webui.NotFound")}</div>
          <p class="description">${m("webui.DescNotFound")}</p>
          <div>
            <mwc-button
              unelevated
              fullwidth
              id="go-to-summary"
              label="${m("button.GoBackToSummaryPage")}"
              @click="${()=>this._moveTo("start")}"
            ></mwc-button>
          </div>
        </div>
      </div>
    `}};e([t({type:Number})],h.prototype,"error_code",void 0),h=e([o("backend-ai-error-view")],h);
