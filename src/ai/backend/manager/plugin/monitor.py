from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext


class ManagerErrorPluginContext(ErrorPluginContext):
    blocklist = {"ai.backend.agent"}


class ManagerStatsPluginContext(StatsPluginContext):
    blocklist = {"ai.backend.agent"}
