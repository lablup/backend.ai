How to create a new translation for a new language
--------------------------------------------------

Add a new project in readthedocs.org with the "-xx" suffix
where "xx" is an ISO 639-1 language code, which targets
the same GitHub address to the original project.

Then configure the main project in readthedocs.org to have
the new project as a specific language translation.

Example:

* https://readthedocs.org/projects/backendai-client-sdk-for-python
* https://readthedocs.org/projects/backendai-client-sdk-for-python-ko

Please ask the docs maintainer for help.


Updating existing translation when the English version is updated
-----------------------------------------------------------------

Update the po message templates (generating/updating `.po` files):
```console
$ make gettext
$ sphinx-intl update -p _build/gettext -l xx
```

Edit the po messages (editing `.po` files):
```console
$ edit locales/xx/LC_MESSAGES/...
```

`git push` here to let readthedocs update the online docs.

Rebuild the compiled po message (compilling `.po` into `.mo` files) and preview the local build:
```console
$ sphinx-intl build
$ make -e SPHINXOPTS="-D language='xx'" html
$ open _build/html/index.html
```


Updateing existing translation to add/improve translations
----------------------------------------------------------

Edit the po messages (editing `.po` files):
```console
$ edit locales/xx/LC_MESSAGES/...
```

`git push` here to let readthedocs update the online docs.

Rebuild the compiled po message (compiling `.po` into `.mo` files) and preview the local build:
```console
$ sphinx-intl build
$ make -e SPHINXOPTS="-D language='xx'" html
$ open _build/html/index.html
```
