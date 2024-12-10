FIXTURES_FOR_HARBOR_CRUD_TEST = [
    {
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "type": "harbor2",
                "url": "http://mock_registry",
                "registry_name": "mock_registry",
                "project": "mock_project",
                "username": "mock_user",
                "password": "mock_password",
                "ssl_verify": False,
                "is_global": True,
            }
        ],
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "container_registry": {
                    "registry": "mock_registry",
                    "project": "mock_project",
                },
                "type": "general",
            }
        ],
    },
]
