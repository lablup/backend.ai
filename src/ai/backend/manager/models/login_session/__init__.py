from .row import LoginHistoryRow, LoginSessionRow

login_sessions = LoginSessionRow.__table__
login_history = LoginHistoryRow.__table__

__all__ = ("LoginSessionRow", "LoginHistoryRow", "login_sessions", "login_history")
