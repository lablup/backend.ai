import{B as i,d as e,I as t,b as o,x as a,f as l,i as s,ax as n,ay as c,g as d,y as r,t as h,_ as f,e as g,a as u}from"./backend-ai-webui-efd2500f.js";let v=class extends i{constructor(){super(...arguments),this.webUIShell=Object(),this.clientConfig=Object(),this.client=Object(),this.notification=Object(),this.successDialog=Object(),this.failDialog=Object()}static get styles(){return[e,t,o,a,l,s`
        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: var(--general-menu-color);
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-typography-font-family: var(--general-font-family);
        }
      `]}_initClient(i){var e,t;this.webUIShell=document.querySelector("#webui-shell"),this.webUIShell.appBody.style.visibility="visible",this.notification=globalThis.lablupNotification,this.successDialog=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#verification-success-dialog"),this.failDialog=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#verification-fail-dialog"),this.clientConfig=new n("","",i,"SESSION"),this.client=new c(this.clientConfig,"Backend.AI Web UI."),this.successDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()})),this.failDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()}))}_redirectToLoginPage(){window.location.href="/"}async verify(i){const e=new URLSearchParams(window.location.search).get("verification_code");if(this._initClient(i),e)try{await this.client.cloud.verify_email(e),this.successDialog.show()}catch(i){console.error(i),this.notification.text=d("signup.VerificationError"),this.notification.show(),window.setTimeout((()=>this.failDialog.show()),100)}else this.failDialog.show()}async sendVerificationCode(){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#email");if(e.value&&e.validity.valid)try{await this.client.cloud.send_verification_email(e.value),this.notification.text=d("signup.EmailSent"),this.notification.show()}catch(i){console.error(i),this.notification.text=i.message||d("signup.SendError"),this.notification.show()}}render(){return r`
      <link rel="stylesheet" href="resources/custom.css">
      <backend-ai-dialog id="verification-success-dialog" fixed backdrop blockscrolling persistent style="padding:0;">
        <span slot="title">${h("signup.EmailVerified")}</span>

        <div slot="content">
          <div class="horizontal layout center">
            <p style="width:256px;">${h("signup.EmailVerifiedMessage")}</p>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
              unelevated
              fullwidth
              label="${h("login.Login")}"
              @click="${()=>this._redirectToLoginPage()}"></mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="verification-fail-dialog" fixed backdrop blockscrolling persistent style="padding:0;">
        <span slot="title">${h("signup.EmailVerificationFailed")}</span>

        <div slot="content">
          <div class="horizontal layout center">
            <p style="width:256px;">${h("signup.EmailVerificationFailedMessage")}</p>
          </div>
          <div style="margin:20px;">
            <mwc-textfield id="email" label="${h("data.explorer.EnterEmailAddress")}"
                autofocus auto-validate validationMessage="${h("signup.InvalidEmail")}"
                pattern="^[A-Z0-9a-z#-_]+@.+\\..+$"
                maxLength="64" placeholder="${h("maxLength.64chars")}"></mwc-textfield>
            <div style="height:1em"></div>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
              unelevated
              fullwidth
              label="${h("signup.SendEmail")}"
              @click="${()=>this.sendVerificationCode()}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};f([g({type:Object})],v.prototype,"webUIShell",void 0),f([g({type:Object})],v.prototype,"clientConfig",void 0),f([g({type:Object})],v.prototype,"client",void 0),f([g({type:Object})],v.prototype,"notification",void 0),f([g({type:Object})],v.prototype,"successDialog",void 0),f([g({type:Object})],v.prototype,"failDialog",void 0),v=f([u("backend-ai-email-verification-view")],v);var p=v;export{p as default};
