---
name: secret-adapter-scenarios
type: reference
description: what the secret adapter guarantees; the status count of stored secrets by the key holding them, the re-encryption pass that rewrites every row through the write provider, the monitor role passing the status and rejected on the pass
scope: src/ai/backend/manager/api/adapters/secret
keywords: [secret, scenario, adapter, superadmin, monitor, reencrypt, key provider, plaintext]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# secret adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This adapter has no entity row of its own. It has only the status get that counts how many stored `secret` values are encrypted with each key, and the re-encryption that rewrites every stored `secret` through the provider the `write_provider_type` value refers to. Both check whether the calling user is superadmin, and the status get is a read operation so a monitor role passes too, while re-encryption is a write operation so it does not. This is the only pair that shows the difference within one adapter.

The only column counted is `secret_key` of a keypair. The caller holds a keypair too, so the caller's `secret_key` value is always in the `counts` aggregate, and a situation with no stored `secret` cannot be created.

The scenario creates and injects the key pool directly. There is no external service: the only implemented key provider is the `config` provider that reads keys from config, and when the `write_provider_type` value is not specified, the new value is stored as plaintext.

## Status get

`counts` is returned sorted by `provider_type` and then `key_id`. The order is the same on every run, so tests compare it as is.

## Re-encryption

Re-encryption treats every row the same. It rewrites even a row already encrypted with the key of the provider that the `write_provider_type` value refers to, using a new data key, so even in the scenario "move a `secret` already encrypted with that key again" the `reencrypted` value equals the `scanned` value. Re-encryption interrupted in the middle is designed to continue when run again, so running the same request twice returns the same response.

When `write_provider_type` is `plain`, re-encryption turns the value back to plaintext. "run when `write_provider_type` is `plain`" and "turn an encrypted `secret` back to plaintext" cover that case. The `reencrypted` value is the number of rows rewritten, not the number of rows whose content changed, so a row rewritten from plaintext to plaintext is counted too.

"a monitor role user gets the status" and "a monitor role user runs" are the point of this adapter. The same user can get the status but cannot run re-encryption.
