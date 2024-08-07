import{_ as t,n as s,e,t as i,s as a,i as o,x as l,B as d,b as n,I as p,a as c}from"./backend-ai-webui-Cvl-SpQz.js";let r=class extends a{constructor(){super(...arguments),this.active=!1}static get styles(){return[o`
        .dots-box {
          width: 100px;
          background-color: transparent;
        }

        .pulse-container {
          width: 100px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .pulse-bubble {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background-color: rgba(114, 235, 81, 0.8);
        }

        .pulse-bubble-1 {
          animation: pulse 0.4s ease 0s infinite alternate;
        }

        .pulse-bubble-2 {
          animation: pulse 0.4s ease 0.2s infinite alternate;
        }

        .pulse-bubble-3 {
          animation: pulse 0.4s ease 0.4s infinite alternate;
        }

        @keyframes pulse {
          from {
            opacity: 1;
            transform: scale(1);
          }
          to {
            opacity: 0.25;
            transform: scale(0.75);
          }
        }
      `]}render(){return l`
      <div class="dots-box" id="dots">
        <div class="pulse-container">
          <div class="pulse-bubble pulse-bubble-1"></div>
          <div class="pulse-bubble pulse-bubble-2"></div>
          <div class="pulse-bubble pulse-bubble-3"></div>
        </div>
      </div>
    `}shouldUpdate(){return this.active}firstUpdated(){this.active=!0}async show(){this.active=!0,await this.updateComplete,this.dots.style.display="block"}async hide(){this.active=!0,await this.updateComplete,this.dots.style.display="none",this.active=!1}async toggle(){await this.updateComplete,"block"===this.dots.style.display?await this.hide():await this.show()}};t([s({type:Boolean,reflect:!0})],r.prototype,"active",void 0),t([e("#dots")],r.prototype,"dots",void 0),r=t([i("lablup-loading-dots")],r);let u=class extends d{constructor(){super(),this.listStatus=Object(),this.message="There is nothing to display",this.statusCondition="loading",this.dots=Object(),this.active=!1}static get styles(){return[n,p,c,o`
        #status {
          position: absolute;
          top: 55%;
          left: 50%;
          transform: translate(-50%, -50%);
        }
      `]}render(){return l`
      <div class="vertical layout center flex" id="status">
        ${"loading"===this.statusCondition?l`
              <lablup-loading-dots id="loading-dots"></lablup-loading-dots>
            `:l`
              ${"no-data"===this.statusCondition?l`
                    <span class="list-message">${this.message}</span>
                  `:l``}
            `}
      </div>
    `}shouldUpdate(){return this.active}firstUpdated(){var t;this.listStatus=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#status"),this.active=!0}connectedCallback(){super.connectedCallback()}disconnectedCallback(){super.disconnectedCallback()}async show(){this.active=!0,await this.updateComplete,this.listStatus.style.display="flex"}async hide(){this.active=!0,await this.updateComplete,this.listStatus.style.display="none",this.active=!1}};t([s({type:Object})],u.prototype,"listStatus",void 0),t([s({type:String})],u.prototype,"message",void 0),t([s({type:String})],u.prototype,"statusCondition",void 0),t([s({type:Object})],u.prototype,"dots",void 0),t([s({type:Boolean,reflect:!0})],u.prototype,"active",void 0),u=t([i("backend-ai-list-status")],u);
