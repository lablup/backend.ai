# Backend.AI Vendored Libarires

## Adding a new vendored library

First, add a git subtree from the library's repository.
You may change `main` to other branch names.

```
git remote add subtree-LIB https://github.com/OWNER/LIB
# NOTE: --squash is to required to avoid CLA signing issues from the upstream contributors.
git subtree add --prefix src/ai/backend/vendor/LIB subtree-LIB main --squash
```

Include it in our build chain by adding `BUILD` and `VERSION` files.

```
cp src/ai/backend/vendor/asyncudp/BUILD src/ai/backend/vendor/LIB/BUILD  # use as reference
$EDITOR src/ai/backend/vendor/LIB/BUILD
cd src/ai/backend/vendor/LIB
ln -s ../../../../../VERSION
git add src/ai/backend/vendor/LIB
```

Update all existing references (if applicable) to the library like:

```diff
- import LIB
+ from ai.backend.vendor import LIB
```


## Updating an existing vendored libary

It is recommended to create a new branch first before running the following commands:

```
# NOTE: --squash is to required to avoid CLA signing issues from the upstream contributors.
git subtree pull --prefix src/ai/backend/vendor/LIB subtree-LIB main --squash
git push
```

Then create a pull request to ensure CI checks.
