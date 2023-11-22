.. role:: raw-html-m2r(raw)
   :format: html

User Management
===============

Users
-----

Backend.AI's user account has two types of authentication modes: *session* and *keypair*.
The session mode just uses the normal username and password based on browser sessions (e.g., when using the Web UI), while the keypair mode uses a pair of access and secret keys for programmatic access.

Projects
--------

There may be multiple projects created by administrators and users may belong to one or more projects.
Administrators may configure project-level resource policies such as storage quota shared by all project vfolders and project-level artifacts.

When a user creates a new session, he/she must choose which project to use if he/she belongs to multiple projects to be in line with the resource policies.
