import{k as t,T as e,D as s,P as i}from"./backend-ai-webui-a9940dc0.js";import{I as a}from"./vaadin-item-mixin-88c89617.js";
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
