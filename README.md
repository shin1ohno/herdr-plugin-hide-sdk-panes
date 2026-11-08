# herdr-plugin-hide-sdk-panes

Herdr 1 plugin that hides `claude remote-control` (`claude rc`, `--sdk-url`) panes from the Agents view.

It tags matching panes with the pane token `hide_sdk=1` and installs an `agent.view.set` filter that excludes them. It runs at startup and on `pane.created` / `pane.agent_detected`.

Install: `herdr plugin link <this directory>`.
