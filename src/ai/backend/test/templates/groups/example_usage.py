"""
Example usage of GroupTemplateWrapper showing how to replace redundant template combinations.

This file demonstrates how to use the GroupTemplateWrapper to reduce redundancy
in test cases by bundling commonly used templates together.
"""

from ai.backend.test.templates.template import BasicTestTemplate, NopTestCode
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.session.interactive_session import InteractiveSessionTemplate
from ai.backend.test.templates.session.batch_session import BatchSessionTemplate
from ai.backend.test.templates.resource_policy.keypair_resource_policy import KeypairResourcePolicyTemplate

from .group_template_wrapper import GroupTemplateWrapper
from .common_groups import (
    AuthSessionGroup,
    AuthBatchSessionGroup,
    AuthResourcePolicySessionGroup,
)


def example_before_grouping():
    """
    Example showing how test cases looked before using GroupTemplateWrapper.
    This demonstrates the redundant template specifications.
    """
    
    # Test case 1: Basic interactive session
    test1 = BasicTestTemplate(NopTestCode()).with_wrappers(
        KeypairAuthTemplate,
        InteractiveSessionTemplate,
    )
    
    # Test case 2: Batch session
    test2 = BasicTestTemplate(NopTestCode()).with_wrappers(
        KeypairAuthTemplate,
        BatchSessionTemplate,
    )
    
    # Test case 3: Session with resource policy
    test3 = BasicTestTemplate(NopTestCode()).with_wrappers(
        KeypairAuthTemplate,
        KeypairResourcePolicyTemplate,
        InteractiveSessionTemplate,
    )
    
    # Test case 4: Another interactive session test
    test4 = BasicTestTemplate(NopTestCode()).with_wrappers(
        KeypairAuthTemplate,
        InteractiveSessionTemplate,
    )
    
    return [test1, test2, test3, test4]


def example_after_grouping():
    """
    Example showing how test cases look after using GroupTemplateWrapper.
    This demonstrates the reduced redundancy and cleaner code.
    """
    
    # Test case 1: Basic interactive session
    test1 = BasicTestTemplate(NopTestCode()).with_wrappers(
        AuthSessionGroup,
    )
    
    # Test case 2: Batch session
    test2 = BasicTestTemplate(NopTestCode()).with_wrappers(
        AuthBatchSessionGroup,
    )
    
    # Test case 3: Session with resource policy
    test3 = BasicTestTemplate(NopTestCode()).with_wrappers(
        AuthResourcePolicySessionGroup,
    )
    
    # Test case 4: Another interactive session test
    test4 = BasicTestTemplate(NopTestCode()).with_wrappers(
        AuthSessionGroup,
    )
    
    return [test1, test2, test3, test4]


def example_custom_group():
    """
    Example showing how to create a custom group for specific use cases.
    """
    
    # Create a custom group for a specific testing scenario
    CustomTestGroup = GroupTemplateWrapper.create_group([
        KeypairAuthTemplate,
        KeypairResourcePolicyTemplate,
        # Could add more specific templates here
    ])
    
    # Use the custom group
    test = BasicTestTemplate(NopTestCode()).with_wrappers(
        CustomTestGroup,
        InteractiveSessionTemplate,  # Additional template not in the group
    )
    
    return test


def example_nested_grouping():
    """
    Example showing that groups can be combined with other templates.
    """
    
    # Groups can be used with additional individual templates
    test1 = BasicTestTemplate(NopTestCode()).with_wrappers(
        AuthSessionGroup,
        # Additional templates can be added here
    )
    
    # Multiple groups can be used together (though this would be rare)
    # This would apply AuthSessionGroup templates, then AuthResourcePolicySessionGroup templates
    test2 = BasicTestTemplate(NopTestCode()).with_wrappers(
        AuthSessionGroup,
        # Note: In practice, you'd want to create a single group that combines all needed templates
        # rather than chaining multiple groups
    )
    
    return [test1, test2]


# Example of how these would be used in actual test specifications
EXAMPLE_TESTSPECS = [
    {
        "name": "example_interactive_session_with_group",
        "template": BasicTestTemplate(NopTestCode()).with_wrappers(AuthSessionGroup),
        "description": "Example test using AuthSessionGroup instead of individual templates",
    },
    {
        "name": "example_resource_policy_session_with_group", 
        "template": BasicTestTemplate(NopTestCode()).with_wrappers(AuthResourcePolicySessionGroup),
        "description": "Example test using AuthResourcePolicySessionGroup for resource policy testing",
    },
]