from pathlib import Path

from pyinfra import host
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDeploy


class APIRequestsToHarbor(BaseDeploy):
    """
    Setup Harbor registry with projects and users via API calls.

    This deployment script creates a shell script that uses curl to interact
    with Harbor's REST API to:
    - Create projects
    - Create a Backend.AI user
    - Add the user to projects with maintainer role
    """

    # Harbor constants
    HARBOR_ADMIN_USER = "admin"
    HARBOR_MAINTAINER_ROLE_ID = 1
    SCRIPT_NAME = "setup_harbor.sh"

    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir: Path = Path(host_data.bai_home_dir)
        self.harbor_admin: str = self.HARBOR_ADMIN_USER
        self.harbor_user: str = host_data.registry_username
        self.harbor_user_password: str = host_data.registry_password
        self.harbor_projects: list[str] = host_data.registry_projects.split(",")

        self.config = host_data.services["harbor"]
        self.base_url: str = (
            f"{host_data.registry_scheme}://{host_data.registry_name}:"
            f"{host_data.registry_port}/api/v2.0"
        )

        self.script_dir: Path = self.home_dir / "harbor"

    def create_harbor_setup_script(self) -> None:
        """
        Create a shell script that handles all Harbor API operations.

        The script performs idempotent operations to:
        1. Create Harbor projects (private repositories)
        2. Create Backend.AI user account
        3. Add user to projects as maintainer
        """
        projects_list = " ".join(f'"{p}"' for p in self.harbor_projects)

        server.shell(
            name="Create Harbor setup script",
            commands=[
                f"mkdir -p {self.script_dir}",
                f"""cat > {self.script_dir}/{self.SCRIPT_NAME} << 'EOF'
#!/bin/bash

BASE_URL="{self.base_url}"
ADMIN_USER="{self.harbor_admin}"
ADMIN_PASSWORD="{self.config.admin_password}"
BAI_USER="{self.harbor_user}"
BAI_PASSWORD="{self.harbor_user_password}"
PROJECTS=({projects_list})

echo "Setting up Harbor projects and users..."

# Function to make API request
make_request() {{
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -n "$data" ]; then
        curl -s -w "\\nHTTP_STATUS:%{{http_code}}" \\
            -X "$method" \\
            -u "$ADMIN_USER:$ADMIN_PASSWORD" \\
            -H "Content-Type: application/json" \\
            -d "$data" \\
            "$BASE_URL$endpoint"
    else
        curl -s -w "\\nHTTP_STATUS:%{{http_code}}" \\
            -X "$method" \\
            -u "$ADMIN_USER:$ADMIN_PASSWORD" \\
            -H "Content-Type: application/json" \\
            "$BASE_URL$endpoint"
    fi
}}

# Create projects
echo "Creating projects..."
for project in "${{PROJECTS[@]}}"; do
    echo "Creating project: $project"
    project_data='{{"project_name":"'$project'","metadata":{{"public":"false"}},"storage_limit":-1,"registry_id":null}}'
    response=$(make_request "POST" "/projects" "$project_data")
    status=$(echo "$response" | tail -n1 | cut -d':' -f2)
    body=$(echo "$response" | head -n -1)

    if [ "$status" = "201" ]; then
        echo "Project '$project' created successfully"
    elif [ "$status" = "409" ]; then
        echo "Project '$project' already exists"
    else
        echo "Error creating project '$project' (HTTP $status): $body"
    fi
done

# Create user
echo "Creating user: $BAI_USER"
user_data='{{"username":"'$BAI_USER'","email":"'$BAI_USER'@backend.ai","realname":"'$BAI_USER'","password":"'$BAI_PASSWORD'","comment":"Backend.AI user"}}'
response=$(make_request "POST" "/users" "$user_data")
status=$(echo "$response" | tail -n1 | cut -d':' -f2)
body=$(echo "$response" | head -n -1)

if [ "$status" = "201" ]; then
    echo "User '$BAI_USER' created successfully"
elif [ "$status" = "409" ]; then
    echo "User '$BAI_USER' already exists"
else
    echo "Error creating user '$BAI_USER' (HTTP $status): $body"
fi

# Add user to projects as maintainer (role_id: {self.HARBOR_MAINTAINER_ROLE_ID})
echo "Adding user to projects..."
for project in "${{PROJECTS[@]}}"; do
    # Get project ID
    echo "Getting project ID for: $project"
    response=$(make_request "GET" "/projects?name=$project")
    project_id=$(echo "$response" | head -n -1 | jq -r '.[0].project_id // empty' 2>/dev/null)

    if [ -n "$project_id" ] && [ "$project_id" != "null" ]; then
        echo "Adding user '$BAI_USER' to project '$project' (ID: $project_id)"
        member_data='{{"role_id":{self.HARBOR_MAINTAINER_ROLE_ID},"member_user":{{"username":"'$BAI_USER'"}}}}'
        response=$(make_request "POST" "/projects/$project_id/members" "$member_data")
        status=$(echo "$response" | tail -n1 | cut -d':' -f2)
        body=$(echo "$response" | head -n -1)

        if [ "$status" = "201" ]; then
            echo "User '$BAI_USER' added to project '$project' successfully"
        elif [ "$status" = "409" ]; then
            echo "User '$BAI_USER' already member of project '$project'"
        else
            echo "Error adding user to project '$project' (HTTP $status): $body"
        fi
    else
        echo "Could not find project ID for '$project'"
    fi
done

echo "Harbor setup completed!"
EOF""",
                f"chmod +x {self.script_dir}/{self.SCRIPT_NAME}",
            ],
        )

    def run_harbor_setup(self) -> None:
        """Execute the Harbor setup script to configure projects and users."""
        server.shell(
            name="Run Harbor setup script",
            commands=[
                f"{self.script_dir}/{self.SCRIPT_NAME}",
            ],
        )

    def install(self) -> None:
        """
        Install Harbor user and project setup.

        Creates and executes a script that configures Harbor registry
        with required projects and Backend.AI user account.
        """
        self.create_harbor_setup_script()
        self.run_harbor_setup()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    APIRequestsToHarbor(host.data).run(deploy_mode)


main()
