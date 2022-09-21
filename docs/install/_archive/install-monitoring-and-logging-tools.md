
Install Monitoring and Logging Tools
------------------------------------

The Backend.AI can use several 3rd-party monitoring and logging services.
Using them is completely optional.

## Guide variables

⚠️ Prepare the values of the following variables before working with this page and replace their occurrences with the values when you follow the guide.

<table>
<tr><td><code>{DDAPIKEY}</code></td><td>The Datadog API key</td></tr>
<tr><td><code>{DDAPPKEY}</code></td><td>The Datadog application key</td></tr>
<tr><td><code>{SENTRYURL}</code></td><td>The private Sentry report URL</td></tr>
</table>

## Install Datadog agent

[Datadog](https://www.datadoghq.com) is a 3rd-party service to monitor the server resource usage.

```console
$ DD_API_KEY={DDAPIKEY} bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/dd-agent/master/packaging/datadog-agent/source/install_agent.sh)"
```

## Install Raven (Sentry client)

Raven is the official client package name of [Sentry](https://sentry.io), which reports detailed contextual information such as stack and package versions when an unhandled exception occurs.

```console
$ pip install "raven>=6.1"
```