import{_ as e,n as i,t,B as a,b as o,I as s,a as r,c as d,i as n,j as c,k as l,x as m,h as u,f as p}from"./backend-ai-webui-dvRyOX_e.js";let g=class extends a{constructor(){super(...arguments),this.error_code=401}static get styles(){return[o,s,r,d,n`
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
      `]}async _viewStateChanged(e){await this.updateComplete}_moveTo(e=""){const i=""!==e?e:"summary";globalThis.history.pushState({},"","/summary"),c.dispatch(l(decodeURIComponent("/"+i),{}))}render(){return m`
      <div class="page-layout">
        <img
          id="unauthorized-access"
          src="/resources/images/401_unauthorized_access.svg"
        />
        <div class="vertical layout desc">
          <div class="title">${u("webui.UNAUTHORIZEDACCESS")}</div>
          <p class="description">${u("webui.AdminOnlyPage")}</p>
          <div>
            <mwc-button
              unelevated
              fullwidth
              id="go-to-summary"
              label="${p("button.GoBackToSummaryPage")}"
              @click="${()=>this._moveTo("summary")}"
            ></mwc-button>
          </div>
        </div>
      </div>
    `}};e([i({type:Number})],g.prototype,"error_code",void 0),g=e([t("backend-ai-permission-denied-view")],g);
