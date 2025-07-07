"""
Common template groups for frequently used template combinations.

This module provides pre-defined template groups that bundle commonly used templates
together to reduce redundancy in test cases.
"""

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.resource_policy.keypair_resource_policy import KeypairResourcePolicyTemplate
from ai.backend.test.templates.session.interactive_session import InteractiveSessionTemplate
from ai.backend.test.templates.session.batch_session import BatchSessionTemplate
from ai.backend.test.templates.vfolder.general_vfolder import ProjectVFolderTemplate
from ai.backend.test.templates.session.vfolder_mounted_interactive_session import VFolderMountedInteractiveSessionTemplate

from .group_template_wrapper import GroupTemplateWrapper


# Basic authentication group - includes keypair auth and resource policy
AuthGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    KeypairResourcePolicyTemplate,
])

# Basic session group - includes auth and interactive session
AuthSessionGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    InteractiveSessionTemplate,
])

# Batch session group - includes auth and batch session
AuthBatchSessionGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    BatchSessionTemplate,
])

# VFolder session group - includes auth, vfolder, and vfolder-mounted session
AuthVFolderSessionGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    ProjectVFolderTemplate,
    VFolderMountedInteractiveSessionTemplate,
])

# Resource policy session group - includes auth, resource policy, and interactive session
AuthResourcePolicySessionGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    KeypairResourcePolicyTemplate,
    InteractiveSessionTemplate,
])

# Resource policy batch session group - includes auth, resource policy, and batch session
AuthResourcePolicyBatchSessionGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    KeypairResourcePolicyTemplate,
    BatchSessionTemplate,
])

# Full VFolder with resource policy group - includes auth, resource policy, vfolder, and vfolder-mounted session
AuthResourcePolicyVFolderSessionGroup = GroupTemplateWrapper.create_group([
    KeypairAuthTemplate,
    KeypairResourcePolicyTemplate,
    ProjectVFolderTemplate,
    VFolderMountedInteractiveSessionTemplate,
])