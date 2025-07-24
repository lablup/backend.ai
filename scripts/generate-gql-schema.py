#!/usr/bin/env python3
"""
Generate GraphQL schema with correct federation version.
This script generates the schema and post-processes it to use the correct federation version.
"""

import subprocess
import sys
from pathlib import Path


def main():
    # Define paths
    backend_ai_path = Path(__file__).parent.parent
    schema2_path = backend_ai_path / "src/ai/backend/manager/api/gql/schema2.graphql"

    # Generate schema using backend.ai command
    print("Generating GraphQL schema...")
    result = subprocess.run(
        ["./backend.ai", "mgr", "api", "dump-gql-schema", "--v2", "-o", str(schema2_path)],
        cwd=backend_ai_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error generating schema: {result.stderr}")
        sys.exit(1)

    # Read the generated schema
    with open(schema2_path, 'r') as f:
        content = f.read()

    # Replace federation version from v2.7 to v2.3
    content = content.replace(
        'schema @link(url: "https://specs.apollo.dev/federation/v2.7"',
        'schema @link(url: "https://specs.apollo.dev/federation/v2.3"'
    )

    # Ensure PageInfo has @shareable directive
    content = content.replace(
        'type PageInfo {',
        'type PageInfo @shareable {'
    )

    # Write back the modified content
    with open(schema2_path, 'w') as f:
        f.write(content)

    print(f"Schema generated and post-processed at: {schema2_path}")
    print("- Federation version changed to v2.3")
    print("- PageInfo marked as @shareable")

    # Generate supergraph
    print("\nGenerating supergraph...")
    supergraph_path = backend_ai_path / "src/ai/backend/manager/api/gql/supergraph.graphql"
    result = subprocess.run(
        ["rover", "supergraph", "compose", "--config", "./src/ai/backend/manager/api/gql/supergraph.yaml"],
        cwd=backend_ai_path,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        with open(supergraph_path, 'w') as f:
            f.write(result.stdout)
        print(f"Supergraph generated at: {supergraph_path}")
    else:
        print(f"Error generating supergraph: {result.stderr}")


if __name__ == "__main__":
    main()
