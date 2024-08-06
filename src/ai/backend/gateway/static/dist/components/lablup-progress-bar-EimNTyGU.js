import{_ as e,n as r,t,s,b as o,I as a,a as i,u as n,c,i as l,x as p}from"./backend-ai-webui-Cvl-SpQz.js";let d=class extends s{constructor(){super(...arguments),this.progress="",this.description=""}static get styles(){return[o,a,i,n,c,l`
        .progress {
          position: relative;
          display: flex;
          height: var(--progress-bar-height, 20px);
          width: var(--progress-bar-width, 186px);
          border: var(--progress-bar-border, 0px);
          border-radius: var(--progress-bar-border-radius, 5px);
          font-size: var(--progress-bar-font-size, 10px);
          font-family: var(--progress-bar-font-family, var(--token-fontFamily));
          overflow: hidden;
        }

        .back {
          display: flex;
          justify-content: left;
          align-items: center;
          width: 100%;
          background: var(--progress-bar-background, var(--paper-green-500));
          color: var(--progress-bar-font-color-inverse, white);
        }

        .front {
          position: absolute;
          display: flex;
          justify-content: left;
          align-items: center;
          left: 0;
          right: 0;
          top: -1px;
          bottom: -1px;
          background: var(--general-progress-bar-bg, #e8e8e8);
          color: var(--progress-bar-font-color, black);
          clip-path: inset(0 0 0 100%);
          -webkit-clip-path: inset(0 0 0 100%);
          transition: clip-path var(--progress-bar-transition-second, 1s) linear;
        }

        .front[slot='description-2'] {
          color: var(--progress-bar-font-color, black);
        }
      `]}render(){return p`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal layout flex">
        <slot name="left-desc"></slot>
        <div class="progress">
          <div id="back" class="back"></div>
          <div id="front" class="front"></div>
        </div>
        <slot name="right-desc"></slot>
      </div>
    `}firstUpdated(){var e,r,t;this.progressBar=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#front"),this.frontDesc=null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#front"),this.backDesc=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#back"),this.progressBar.style.clipPath="inset(0 0 0 0%)"}async changePct(e){await this.updateComplete,this.progressBar.style.clipPath="inset(0 0 0 "+100*e+"%)"}async changeDesc(e){await this.updateComplete,this.frontDesc.innerHTML="&nbsp;"+e,this.backDesc.innerHTML="&nbsp;"+e}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}attributeChangedCallback(e,r,t){"progress"!=e||null===t||isNaN(t)||this.changePct(t),"description"!=e||null===t||t.startsWith("undefined")||this.changeDesc(t),super.attributeChangedCallback(e,r,t)}};e([r({type:Object})],d.prototype,"progressBar",void 0),e([r({type:Object})],d.prototype,"frontDesc",void 0),e([r({type:Object})],d.prototype,"backDesc",void 0),e([r({type:String})],d.prototype,"progress",void 0),e([r({type:String})],d.prototype,"description",void 0),d=e([t("lablup-progress-bar")],d);
