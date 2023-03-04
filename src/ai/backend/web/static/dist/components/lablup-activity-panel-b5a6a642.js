import{_ as t,e as i,a as e,s as o,I as d,b as s,i as r,y as a}from"./backend-ai-webui-efd2500f.js";let h=class extends o{constructor(){super(...arguments),this.title="",this.message="",this.panelId="",this.horizontalsize="",this.headerColor="",this.elevation=1,this.autowidth=!1,this.width=350,this.widthpct=0,this.height=0,this.marginWidth=14,this.minwidth=0,this.maxwidth=0,this.pinned=!1,this.disabled=!1,this.narrow=!1,this.noheader=!1,this.scrollableY=!1}static get styles(){return[d,s,r`
        div.card {
          display: block;
          background: var(--card-background-color, #ffffff);
          box-sizing: border-box;
          margin: 14px;
          padding: 0;
          border-radius: 5px;
          box-shadow: rgba(4, 7, 22, 0.7) 0px 0px 4px -2px;
          width: 280px;
        }

        div.card > h4 {
          background-color: #FFFFFF;
          color: #000000;
          font-size: 14px;
          font-weight: 400;
          height: 48px;
          padding: 5px 15px 5px 20px;
          margin: 0 0 10px 0;
          border-radius: 5px 5px 0 0;
          border-bottom: 1px solid #DDD;
          display: flex;
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }

        div.card[disabled] {
          background-color: rgba(0, 0, 0, 0.1);
        }

        div.card > div {
          margin: 20px;
          padding-bottom: .5rem;
          font-size: 12px;
          overflow-wrap:break-word;
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
      <link rel="stylesheet" href="resources/custom.css">
      <div class="card" id="activity" elevation="${this.elevation}" ?disabled="${this.disabled}">
        <h4 id="header" class="horizontal center justified layout" style="font-weight:bold">
          <span>${this.title}</span>
          <div class="flex"></div>
          <wl-button id="button" fab flat inverted @click="${()=>this._removePanel()}">
            <wl-icon>close</wl-icon>
          </wl-button>
        </h4>
        <div class="${this.disabled?"disabled":"enabled"}">
          <slot name="message"></slot>
        </div>
      </div>
    `}firstUpdated(){var t,i,e,o,d,s;if(this.pinned||null==this.panelId){const o=null===(t=this.shadowRoot)||void 0===t?void 0:t.getElementById("button");null===(e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("h4"))||void 0===e||e.removeChild(o)}const r=null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector(".card"),a=null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("#header");this.autowidth?r.style.width="auto":r.style.width=0!==this.widthpct?this.widthpct+"%":this.width+"px",this.minwidth&&(r.style.minWidth=this.minwidth+"px"),this.maxwidth&&(r.style.minWidth=this.maxwidth+"px"),"2x"===this.horizontalsize?r.style.width=2*this.width+28+"px":"3x"===this.horizontalsize?r.style.width=3*this.width+56+"px":"4x"==this.horizontalsize&&(r.style.width=4*this.width+84+"px"),r.style.margin=this.marginWidth+"px",""!==this.headerColor&&(a.style.backgroundColor=this.headerColor),this.narrow&&((null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("div.card > div")).style.margin="0",a.style.marginBottom="0"),this.height>0&&(130==this.height?r.style.height="fit-content":r.style.height=this.height+"px"),this.noheader&&(a.style.display="none"),this.scrollableY&&(r.style.overflowY="auto")}_removePanel(){}};t([i({type:String})],h.prototype,"title",void 0),t([i({type:String})],h.prototype,"message",void 0),t([i({type:String})],h.prototype,"panelId",void 0),t([i({type:String})],h.prototype,"horizontalsize",void 0),t([i({type:String})],h.prototype,"headerColor",void 0),t([i({type:Number})],h.prototype,"elevation",void 0),t([i({type:Boolean})],h.prototype,"autowidth",void 0),t([i({type:Number})],h.prototype,"width",void 0),t([i({type:Number})],h.prototype,"widthpct",void 0),t([i({type:Number})],h.prototype,"height",void 0),t([i({type:Number})],h.prototype,"marginWidth",void 0),t([i({type:Number})],h.prototype,"minwidth",void 0),t([i({type:Number})],h.prototype,"maxwidth",void 0),t([i({type:Boolean})],h.prototype,"pinned",void 0),t([i({type:Boolean})],h.prototype,"disabled",void 0),t([i({type:Boolean})],h.prototype,"narrow",void 0),t([i({type:Boolean})],h.prototype,"noheader",void 0),t([i({type:Boolean})],h.prototype,"scrollableY",void 0),h=t([e("lablup-activity-panel")],h);
