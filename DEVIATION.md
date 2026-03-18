# Deviation Report: BA-5292

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Task 3: Update TOTPHook.validate_otp() | Cannot implement in this PR | The TOTP plugin (`backend.ai-totp-plugin`) is a separate repository not tracked in the main backend.ai repository. Changes to `validate_otp()` must be made in a separate PR to the backend.ai-totp-plugin repository. |
| Task 4: TOTP hook tests | Cannot implement in this PR | TOTP hook tests are part of the separate backend.ai-totp-plugin repository and must be added there. |

## Recommended Follow-up Actions

1. **Create a separate PR in backend.ai-totp-plugin** to:
   - Update `validate_otp()` in `src/ai/backend/security/totp/hook.py` line 77:
     ```python
     # Current:
     otp = params.get("stoken") or params.get("sToken")

     # Proposed:
     otp = params.get("stoken") or params.get("sToken") or params.get("otp")
     ```
   - Add test cases to verify the "otp" parameter is accepted

2. **This PR (BA-5292) provides the foundation** by:
   - Making the backend.ai core accept "otp" field in DTOs (Task 1 ✅)
   - Propagating "otp" to hook_params (Task 2 ✅)
   - These changes are sufficient for the webui to send "otp" and have it reach the hook layer

## Technical Details

The plugins directory structure:
- `plugins/.ignore` contains `!/*/` which excludes all plugin subdirectories from git tracking
- `plugins/README.md` describes the plugin installation workflow via `scripts/install-plugin.sh`
- TOTP plugin repository: https://github.com/lablup/backend.ai-totp-plugin (assumed based on naming convention)

Even without the TOTP plugin changes, this PR fixes the core issue: the "otp" field will now be properly parsed and propagated to hook_params, making it accessible to any auth hook that needs it.
