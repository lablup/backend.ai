from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.templates.template import (
    TestTemplate,
    WrapperTestTemplate,
    WrapperTestTemplateProtocol,
)


class GroupTemplateWrapper(WrapperTestTemplate):
    """
    A wrapper template that bundles multiple templates that must always be applied together.
    
    This template allows grouping commonly used templates to reduce redundancy in test cases.
    Instead of repeatedly specifying the same set of templates, they can be grouped together
    and used as a single unit.
    
    The GroupTemplateWrapper works by creating a composite template that applies all the
    group templates in sequence using the existing with_wrappers mechanism.
    
    Example usage:
        # Define a group of always-required templates
        auth_resource_group = GroupTemplateWrapper.create_group([
            KeypairAuthTemplate,
            KeypairResourcePolicyTemplate,
        ])
        
        # Use the group in test cases
        BasicTestTemplate(test_code).with_wrappers(auth_resource_group)
    """
    
    @classmethod
    def create_group(cls, group_templates: list[WrapperTestTemplateProtocol]) -> WrapperTestTemplateProtocol:
        """
        Create a group template wrapper class that can be used as a single template.
        
        This method returns a wrapper template class that, when applied to a base template,
        will apply all the group templates in sequence.
        
        :param group_templates: List of wrapper template classes to group together.
        :return: A wrapper template class that applies all group templates.
        """
        
        class GroupTemplate(WrapperTestTemplate):
            @property
            def name(self) -> str:
                template_names = []
                for template_cls in group_templates:
                    if hasattr(template_cls, '__name__'):
                        template_names.append(template_cls.__name__)
                    else:
                        template_names.append(str(template_cls))
                return f"group[{','.join(template_names)}]"
            
            @override
            @actxmgr
            async def _context(self) -> AsyncIterator[None]:
                # The GroupTemplate acts as a transparent wrapper that applies
                # all group templates to the base template using with_wrappers
                yield
            
            @override
            async def run_test(self, exporter) -> None:
                # Apply all group templates to the base template and run it
                wrapped_template = self._template.with_wrappers(*group_templates)
                await wrapped_template.run_test(exporter)
        
        return GroupTemplate