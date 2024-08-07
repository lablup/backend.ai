import{_ as e,n as t,t as i,s,i as a,x as c}from"./backend-ai-webui-dvRyOX_e.js";let r=class extends s{constructor(){super(...arguments),this.active=!1}static get styles(){return[a`
        mwc-circular-progress {
          width: 48px;
          height: 48px;
          position: fixed;
          --mdc-theme-primary: #e91e63;
          top: calc(50vh - 24px);
        }
      `]}render(){return c`
      <link rel="stylesheet" href="resources/custom.css" />
      <mwc-circular-progress id="spinner" indeterminate></mwc-circular-progress>
    `}shouldUpdate(){return this.active}firstUpdated(){var e;this.spinner=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#spinner"),this.active=!0}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}async show(){this.active=!0,await this.updateComplete,this.spinner.style.display="block"}async hide(){this.active=!0,await this.updateComplete,this.spinner.style.display="none",this.active=!1}async toggle(){await this.updateComplete,!0===this.spinner.active?(this.active=!0,this.spinner.style.display="none",this.active=!1):(this.active=!0,this.spinner.style.display="block")}};e([t({type:Object})],r.prototype,"spinner",void 0),e([t({type:Boolean,reflect:!0})],r.prototype,"active",void 0),r=e([i("lablup-loading-spinner")],r);
