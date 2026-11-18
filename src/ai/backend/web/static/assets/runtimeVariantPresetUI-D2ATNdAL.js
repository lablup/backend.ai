/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var e={slider:`SLIDER`,number_input:`NUMBER_INPUT`,select:`SELECT`,checkbox:`CHECKBOX`,text_input:`TEXT_INPUT`},t={SLIDER:[`INT`,`FLOAT`],NUMBER_INPUT:[`INT`,`FLOAT`],CHECKBOX:[`BOOL`,`FLAG`],SELECT:[`STR`],TEXT_INPUT:[`STR`,`INT`,`FLOAT`]};function n(e,n){let r=e?t[e]:void 0;return!r||r.includes(n)}export{n,e as t};
