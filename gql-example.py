import base64
import json
import textwrap
import requests

from datetime import datetime
from dateutil.tz import tzutc
import yarl
from ai.backend.client.auth import generate_signature


def create_global_id(type_name: str, id_value: str) -> str:
    """Create a Relay-compatible GlobalID"""
    raw_id = f"{type_name}:{id_value}"
    return base64.b64encode(raw_id.encode()).decode()

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HASH_TYPE = "sha256"


def make_request(query_or_mutation):
    method = "POST"
    date = datetime.now(tzutc())
    rel_url = "/gql/artifact-registry"
    content_type = "application/json"
    hdrs, _ = generate_signature(
        method=method,
        version=API_VERSION,
        endpoint=API_ENDPOINT,
        date=date,
        rel_url=rel_url,
        content_type=content_type,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        hash_type=HASH_TYPE,
    )

    headers = {
        "User-Agent": "Backend.AI API Client",
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }

    data = {"query": textwrap.dedent(query_or_mutation).strip()}
    r = requests.post(API_ENDPOINT / rel_url[1:], headers=headers, json=data)
    return r.json()


def query_all_artifacts():
    query = """
        query GetAllArtifacts {
            artifacts {
                edges {
                    node {
                        name
                        type
                        status
                        description
                        registry {
                            name
                            url
                        }
                        source {
                            name
                            url
                        }
                        size
                        createdAt
                        updatedAt
                        version
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
                totalCount
            }
        }
    """
    return make_request(query)


def query_filtered_artifacts():
    query = """
        query GetModelArtifacts {
            artifacts(
                filter: {
                    type: [MODEL]
                    status: [AVAILABLE, INSTALLED]
                    name: { contains: "llama" }
                }
                order: { updatedAt: DESC }
                first: 10
            ) {
                edges {
                    node {
                        name
                        type
                        status
                        version
                        size
                        updatedAt
                    }
                }
                totalCount
            }
        }
    """
    return make_request(query)


def query_single_artifact():
    query = """
        query GetArtifact {
            artifact(id: "QXJ0aWZhY3Q6YXJ0aWZhY3QtMTIz") {
                name
                type
                status
                description
                registry {
                    name
                    url
                }
                source {
                    name
                    url
                }
                size
                version
                createdAt
                updatedAt
            }
        }
    """
    return make_request(query)


def query_artifact_groups():
    query = """
        query GetArtifactGroups {
            artifactGroups(
                filter: { type: [MODEL] }
                order: { name: ASC }
            ) {
                id
                name
                type
                status
                description
                artifacts(first: 5) {
                    edges {
                        node {
                            name
                            version
                            status
                        }
                    }
                    totalCount
                }
            }
        }
    """
    return make_request(query)


def mutation_pull_artifact():
    mutation = """
        mutation PullArtifact {
            pullArtifact(input: {
                artifactId: "QXJ0aWZhY3Q6YXJ0aWZhY3QtMTIz"
                version: "1.0.0"
            }) {
                artifact {
                    name
                    type
                    status
                    version
                }
            }
        }
    """
    return make_request(mutation)


def mutation_install_artifact():
    mutation = """
        mutation InstallArtifact {
            installArtifact(input: {
                artifactId: "QXJ0aWZhY3Q6YXJ0aWZhY3QtMTIz"
                version: "1.0.0"
            }) {
                artifact {
                    name
                    type
                    status
                    version
                }
            }
        }
    """
    return make_request(mutation)


def mutation_update_artifact():
    mutation = """
        mutation UpdateArtifact {
            updateArtifact(input: {
                artifactId: "QXJ0aWZhY3Q6YXJ0aWZhY3QtMTIz"
                targetVersion: "1.1.0"
            }) {
                artifact {
                    name
                    version
                    status
                    updatedAt
                }
            }
        }
    """
    return make_request(mutation)


def mutation_verify_artifact():
    mutation = """
        mutation VerifyArtifact {
            verifyArtifact(
                artifactId: "QXJ0aWZhY3Q6YXJ0aWZhY3QtMTIz"
                version: "1.0.0"
            ) {
                artifact {
                    name
                    status
                    version
                }
            }
        }
    """
    return make_request(mutation)


def mutation_delete_artifact():
    mutation = """
        mutation DeleteArtifact {
            deleteArtifact(input: {
                artifactId: "QXJ0aWZhY3Q6YXJ0aWZhY3QtMTIz"
                version: "1.0.0"
                forceDelete: false
            }) {
                artifact {
                    name
                    version
                    status
                }
            }
        }
    """
    return make_request(mutation)


def mutation_cancel_pull():
    mutation = """
        mutation CancelPull {
            cancelPull(artifactId: "artifact-123") {
                artifact {
                    name
                    status
                }
            }
        }
    """
    return make_request(mutation)


def main():
    print("=== Artifact Registry GraphQL Examples ===\n")
    
    print("1. Query All Artifacts:")
    result = query_all_artifacts()
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    print("2. Query Filtered Artifacts (Models containing 'llama'):")
    result = query_filtered_artifacts()
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    print("3. Query Single Artifact:")
    result = query_single_artifact()
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    print("4. Query Artifact Groups:")
    result = query_artifact_groups()
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    print("5. Pull Artifact Mutation:")
    result = mutation_pull_artifact()
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    print("6. Install Artifact Mutation:")
    result = mutation_install_artifact()
    print(json.dumps(result, indent=2))
    print("\n" + "="*50 + "\n")
    
    print("7. Verify Artifact Mutation:")
    result = mutation_verify_artifact()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()