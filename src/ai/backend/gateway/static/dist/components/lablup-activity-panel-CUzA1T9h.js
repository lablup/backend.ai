import{_ as t,n as i,t as o,s as e,I as d,a as r,i as s,x as a}from"./backend-ai-webui-dvRyOX_e.js";let h=class extends e{constructor(){super(...arguments),this.title="",this.message="",this.panelId="",this.horizontalsize="",this.headerColor="",this.elevation=1,this.autowidth=!1,this.width=350,this.widthpct=0,this.height=0,this.marginWidth=14,this.minwidth=0,this.maxwidth=0,this.pinned=!1,this.disabled=!1,this.narrow=!1,this.noheader=!1,this.scrollableY=!1}static get styles(){return[d,r,s`
        div.card {
          display: block;
          background: var(
            --token-colorBgContainer,
            --general-background-color,
            #ffffff
          );
          box-sizing: border-box;
          margin: 0 !important;
          padding: 0;
          border-radius: 5px;
          width: 280px;
          line-height: 1.1;
          color: var(--token-colorText);
          border: 1px solid var(--token-colorBorder, #424242);
        }

        div.card > h4 {
          background-color: var(--token-colorBgContainer, #ffffff);
          color: var(--token-colorText, #000000);
          font-size: var(--token-fontSize, 14px);
          font-weight: 400;
          height: 48px;
          padding: 5px 15px 5px 20px;
          margin: 0 0 10px 0;
          border-radius: 5px 5px 0 0;
          border-bottom: 1px solid var(--token-colorBorder, #ddd);
          display: flex;
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }

        div.card[disabled] {
          background-color: var(
            --token-colorBgContainerDisabled,
            rgba(0, 0, 0, 0.1)
          );
        }

        div.card > div {
          margin: 20px;
          padding-bottom: 0.5rem;
          font-size: 12px;
          overflow-wrap: break-word;
        }

        ul {
          padding-inline-start: 0;
        }

        #button {
          display: none;
        }

        @media screen and (max-width: 1015px) {
          div.card {
            max-width: 700px;
          }
        }

        @media screen and (max-width: 750px) {
          div.card {
            width: auto;
            height: auto !important;
          }
        }

        @media screen and (max-width: 375px) {
          div.card {
            width: 350px;
          }
        }
      `]}render(){return a`
      <link rel="stylesheet" href="resources/custom.css" />
      <div
        class="card"
        id="activity"
        elevation="${this.elevation}"
        ?disabled="${this.disabled}"
      >
        <h4
          id="header"
          class="horizontal center justified layout"
          style="font-weight:bold"
        >
          <span>${this.title}</span>
          <div class="flex"></div>
          <mwc-icon-button
            id="button"
            class="fg"
            icon="close"
            @click="${()=>this._removePanel()}"
          ></mwc-icon-button>
        </h4>
        <div class="${this.disabled?"disabled":"enabled"}">
          <slot name="message"></slot>
        </div>
      </div>
    `}firstUpdated(){var t,i,o,e,d,r;if(this.pinned||null==this.panelId){const e=null===(t=this.shadowRoot)||void 0===t?void 0:t.getElementById("button");null===(o=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("h4"))||void 0===o||o.removeChild(e)}const s=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector(".card"),a=null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("#header");this.autowidth?s.style.width="auto":s.style.width=0!==this.widthpct?this.widthpct+"%":this.width+"px",this.minwidth&&(s.style.minWidth=this.minwidth+"px"),this.maxwidth&&(s.style.minWidth=this.maxwidth+"px"),"2x"===this.horizontalsize?s.style.width=2*this.width+28+"px":"3x"===this.horizontalsize?s.style.width=3*this.width+56+"px":"4x"==this.horizontalsize&&(s.style.width=4*this.width+84+"px"),s.style.margin=this.marginWidth+"px",""!==this.headerColor&&(a.style.backgroundColor=this.headerColor),this.narrow&&((null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("div.card > div")).style.margin="0",a.style.marginBottom="0"),this.height>0&&(130==this.height?s.style.height="fit-content":s.style.height=this.height+"px"),this.noheader&&(a.style.display="none"),this.scrollableY&&(s.style.overflowY="auto")}_removePanel(){}};t([i({type:String})],h.prototype,"title",void 0),t([i({type:String})],h.prototype,"message",void 0),t([i({type:String})],h.prototype,"panelId",void 0),t([i({type:String})],h.prototype,"horizontalsize",void 0),t([i({type:String})],h.prototype,"headerColor",void 0),t([i({type:Number})],h.prototype,"elevation",void 0),t([i({type:Boolean})],h.prototype,"autowidth",void 0),t([i({type:Number})],h.prototype,"width",void 0),t([i({type:Number})],h.prototype,"widthpct",void 0),t([i({type:Number})],h.prototype,"height",void 0),t([i({type:Number})],h.prototype,"marginWidth",void 0),t([i({type:Number})],h.prototype,"minwidth",void 0),t([i({type:Number})],h.prototype,"maxwidth",void 0),t([i({type:Boolean})],h.prototype,"pinned",void 0),t([i({type:Boolean})],h.prototype,"disabled",void 0),t([i({type:Boolean})],h.prototype,"narrow",void 0),t([i({type:Boolean})],h.prototype,"noheader",void 0),t([i({type:Boolean})],h.prototype,"scrollableY",void 0),h=t([o("lablup-activity-panel")],h);
