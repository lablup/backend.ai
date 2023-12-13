import{m as t,T as e,D as s,P as i}from"./backend-ai-webui-ff615d7c.js";import{I as a}from"./vaadin-item-mixin-602d9d60.js";
/**
 * @license
 * Copyright (c) 2017 - 2023 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */class n extends(a(e(s(i)))){static get template(){return t`
      <style>
        :host {
          display: inline-block;
        }

        :host([hidden]) {
          display: none !important;
        }
      </style>
      <span part="checkmark" aria-hidden="true"></span>
      <div part="content">
        <slot></slot>
      </div>
    `}static get is(){return"vaadin-item"}constructor(){super(),this.value}ready(){super.ready(),this.setAttribute("role","option")}}customElements.define(n.is,n);
