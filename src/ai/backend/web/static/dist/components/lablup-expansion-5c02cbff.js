import{_ as t,b as e,n as i,a$ as o,x as n,C as a,i as s,b0 as r,e as d,s as c,c as p,I as l,a as h,m as g,d as m}from"./backend-ai-webui-8aa3adc0.js";
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */class x extends o{constructor(){super(...arguments),this.left=!1,this.graphic="control"}render(){const t={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},e=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():n``,o=this.hasMeta&&this.left?this.renderMeta():n``,s=this.renderRipple();return n`
      ${s}
      ${i}
      ${this.left?"":e}
      <span class=${a(t)}>
        <mwc-checkbox
            reducedTouchTarget
            tabindex=${this.tabindex}
            .checked=${this.selected}
            ?disabled=${this.disabled}
            @change=${this.onChange}>
        </mwc-checkbox>
      </span>
      ${this.left?e:""}
      ${o}`}async onChange(t){const e=t.target;this.selected===e.checked||(this._skipPropRequest=!0,this.selected=e.checked,await this.updateComplete,this._skipPropRequest=!1)}}t([e("slot")],x.prototype,"slotElement",void 0),t([e("mwc-checkbox")],x.prototype,"checkboxElement",void 0),t([i({type:Boolean})],x.prototype,"left",void 0),t([i({type:String,reflect:!0})],x.prototype,"graphic",void 0);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const v=s`:host(:not([twoline])){height:56px}:host(:not([left])) .mdc-deprecated-list-item__meta{height:40px;width:40px}`
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let f=class extends x{};f.styles=[r,v],f=t([d("mwc-check-list-item")],f);
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
let u=class extends c{static get styles(){return[p,l,h,g,m,s`
        div.card {
          padding:0;
          margin:0;
        }

        #accordion > div.card > h3 {
          background-color: var(--general-dialog-background-color, #ffffff);
          padding: var(--expansion-header-padding, 0);
          font-size: var(--expansion-header-font-size, 12px);
          font-weight: var(--expansion-header-font-weight, 600);
          font-family: var(--general-font-family);
          transition: all .35s;
        }
        #accordion > div.card > h3 > mwc-icon-button {
          --mdc-icon-button-size: 16px;
        }

        div.content {
          font-size: var(--expansion-content-font-size, 14px);
          word-break: keep-all;
          overflow-x: hidden;
        }

        #accordion div.content {
          max-height: 0;
          transition: all .35s;
          padding: 0;
          margin: 0;
        }

        #accordion[open] div.content {
          margin: var(--expansion-content-margin, 0);
          padding: var(--expansion-content-padding, 0);
          max-height: 100vh;
        }

        #accordion #expand_icon {
          transition: all .35s;
          transform: rotate(0deg);
        }

        #accordion[open] #expand_icon {
          transition: all .35s;
          transform: rotate(-180deg);
        }

        div[narrow] div.content {
          padding: 0;
          margin: 0;
        }

        div.content h4 {
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #DDD !important;
        }
      `]}_toggleAccordion(){this.ExpansionShell.hasAttribute("open")?this.ExpansionShell.removeAttribute("open"):this.ExpansionShell.setAttribute("open","true")}render(){return n`
      <link rel="stylesheet" href="resources/custom.css">
      <div .name="${this.name}" id="accordion" ${this.open?"open":""}>
        <div elevation="1" class="card" style="margin: 0;padding:0;">
          <h3 class="horizontal justified layout" style="font-weight:bold" @click="${()=>this._toggleAccordion()}">
            <span class="vertical center-justified layout">
              <slot name="title"></slot>
            </span>
            <div class="flex"></div>
            <slot name="action"></slot>
            <mwc-icon-button id="expand_icon" icon="expand_more">
            </mwc-icon-button>
          </h3>
          <div class="content">
            <slot></slot>
          </div>
        </div>
      </div>
    `}constructor(){super(),this.name="",this.open=!1}firstUpdated(){this.open&&this.ExpansionShell.setAttribute("open","true")}};t([i({type:String})],u.prototype,"name",void 0),t([i({type:Boolean})],u.prototype,"open",void 0),t([e("#accordion")],u.prototype,"ExpansionShell",void 0),t([e("#expand_icon")],u.prototype,"ExpandIcon",void 0),t([e("div.content")],u.prototype,"ContentArea",void 0),u=t([d("lablup-expansion")],u);
