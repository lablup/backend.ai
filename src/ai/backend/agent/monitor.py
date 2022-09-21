from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext


class AgentErrorPluginContext(ErrorPluginContext):
    blocklist = {"ai.backend.manager"}


class AgentStatsPluginContext(StatsPluginContext):
    blocklist = {"ai.backend.manager"}
