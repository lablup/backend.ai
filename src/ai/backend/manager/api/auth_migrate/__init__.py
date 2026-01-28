"""
Auth API package.

Re-exports from auth.auth (legacy function-based handlers) for backward compatibility.
"""

from .auth import (  # noqa: F401
    _extract_auth_params,
    admin_required,
    admin_required_for_method,
    auth_middleware,
    auth_required,
    auth_required_for_method,
    authorize,
    check_date,
    create_app,
    generate_ssh_keypair,
    get_role,
    get_ssh_keypair,
    sign_request,
    signout,
    signup,
    superadmin_required,
    superadmin_required_for_method,
    test,
    update_full_name,
    update_password,
    update_password_no_auth,
    upload_ssh_keypair,
    validate_ip,
    whois_timezone_info,
)
