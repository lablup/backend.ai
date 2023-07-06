import{B as e,d as i,I as t,b as a,f as o,i as s,a1 as r,a2 as d,y as n,j as c,t as l,_ as m,e as u,a as p}from"./backend-ai-webui-ab578ea5.js";
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */let g=class extends e{constructor(){super(...arguments),this.error_code=401}static get styles(){return[i,t,a,o,s`
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

      img#unauthorized-access {
        width: 400px;
        margin: 20px;
      }

      div.page-layout {
        display: flex;
        -ms-flex-direction: row;
        -webkit-flex-direction: row;
        flex-direction: row;
        align-items: center;
        margin: 20px;
      }

      div.desc {
        width: 100%;
      }

      @media screen and (max-width: 1015px) {
        div.page-layout {
          -ms-flex-direction: column;
          -webkit-flex-direction: column;
          flex-direction: column;
          align-content: center;
        }

        div.desc {
          align-items: center;
        }
      }

      @media screen and (max-width: 440px) {
        img#unauthorized-access {
          width: 330px;
          margin: 20px;
        }

        div.desc > p.description {
          max-width: 330px;
          font-size: 13px;
        }
      }

      `]}async _viewStateChanged(e){await this.updateComplete}_moveTo(e=""){const i=""!==e?e:"summary";globalThis.history.pushState({},"","/summary"),r.dispatch(d(decodeURIComponent("/"+i),{}))}render(){return n`
    <div class="page-layout">
      <img id="unauthorized-access" src="/resources/images/401_unauthorized_access.svg" />
      <div class="vertical layout desc">
        <div class="title">${c("webui.UNAUTHORIZEDACCESS")}</div>
        <p class="description">${c("webui.AdminOnlyPage")}</p>
        <div>
          <mwc-button
              unelevated
              fullwidth
              id="go-to-summary"
              label="${l("button.GoBackToSummaryPage")}"
              @click="${()=>this._moveTo("summary")}"></mwc-button>
        </div>
      </div>
    </div>
    `}};m([u({type:Number})],g.prototype,"error_code",void 0),g=m([p("backend-ai-permission-denied-view")],g);var v=g;export{v as default};
