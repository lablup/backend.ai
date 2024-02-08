# Backend.AI Watcher

A base interface of Backend.AI watcher. Watcher is a special process that runs with root privileges so that **watch** a Backend.AI process and run any subprocess that needs root privilege.


## How to use
First, you should implement the watcher as a Backend.AI Watcher plugin. There are two interfaces that you should implement.
- `ai.backend.watcher.base.BaseWatcher`
- `ai.backend.watcher.base.BaseWatcherConfig`

`BaseWatcher` is the interface of watcher and `BaseWatcherConfig` is for configuration. Please check [Backend.AI agent watcher](https://github.com/lablup/backend.ai-agent-watcher) and [Backend.AI storage watcher](https://github.com/lablup/backend.ai-storage-watcher) for any detail with implementation.

After that, you need to set a configuration file based on your `WatcherConfig` implementation. The config should be in the watcher's toml configuration file.
```toml
[watcher]
# watcher configs
# ...

[module.MODULE_NAME]
# configs
```

You can check `configs/watcher/sample.toml` file.

If you complete all above steps, you can run watcher like below.
```bash
$ ./py -m ai.backend.watcher.server CONFIG_TOML_PATH
```
