# spec.md

In the tester, some template wrappers like KeypairResourcePolicyTemplate need to be included redundantly in all test cases.

Furthermore, this type of always-required template may also be created in the future.

Therefore, we need a way to group templates that must always be applied, or that need to be bundled together, into a single TemplateWrapper.

The grouping should not only handle specific cases like KeypairResourcePolicyTemplate, but should be applicable in a more generalized manner.

## Reference

- [What is TemplateWrapper](./src/ai/backend/test/templates/README.md)
: Understand the basic concept of templates.

- [How to run test](./src/ai/backend/test/tester/README.md)
: Refer to this README and try running the tests. Use the `run-test` command to debug the specific test code you modified.