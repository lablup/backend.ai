Use prebuilt supergraph.graphql in package mode while keeping rover CLI for development

In development mode (InstallType.SOURCE), continue using rover CLI to generate supergraph.graphql dynamically. In package mode (InstallType.PACKAGE), use the prebuilt supergraph.graphql from release artifacts to avoid rover CLI dependency in production deployments.
