## image

[background](/src/ai/backend/manager/api/adapters/image/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/image/adapter.py)

Scenario: incomplete 3 / 17

- built from ops (12)
  - admin_search: representative success ✓ · representative rejection ✓
  - admin_search_images_gql: representative success ✓ · representative rejection ✓
  - batch_load_aliases_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - delete: representative success ✓ · representative rejection ✓
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - restore: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - scoped_search_aliases: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (5)
  - admin_alias: success present 1 · rejection present 3 (global_scope)
  - admin_dealias: success present 1 · rejection present 2 (global_scope)
  - admin_purge: success present 3 · rejection present 3 (single_entity)
  - admin_scan_image: success present 2 · rejection present 3 (global_scope)
  - admin_search_image_aliases: success present 3 · rejection present 1 (global_scope)

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches with only a cursor and no size or offset, only the requested count comes back and the answer says there is a next page](#searching-a-cursor-alone-answers-the-first-page-and-says-there-is-more) | answered |
| [among custom images committed by the caller and by another user, searching for the ones the caller committed brings back only the caller's images](#searching-filtering-images-by-creator-returns-only-images-they-committed) | answered |
| [searching a mix of customized and uncustomized images for customized images brings back only the customized images together with the user who committed them](#searching-filtering-images-by-customized-returns-only-customized-images) | answered |
| [when the superadmin searches by the name of one image, only that image comes back](#searching-filtering-images-by-name-returns-only-the-match) | answered |
| [searching a mix of customized and uncustomized images for images that are not customized brings back only the uncustomized images](#searching-filtering-images-by-not-customized-returns-only-uncustomized-images) | answered |
| [searching a mix of alive and deleted images for the alive status brings back only those images](#searching-filtering-images-by-status-returns-only-alive-images) | answered |
| [when the superadmin searches with the page size omitted, only 50 come back and the answer says there is a next page](#searching-omitting-the-page-size-answers-with-fifty-and-says-there-is-more) | answered |
| [ordering by name descending and skipping the first item brings back the second and third images](#searching-ordering-by-name-and-offsetting-returns-the-middle-page) | answered |
| [when the superadmin searches without a filter, every image seeded in advance comes back](#searching-searching-without-a-filter-counts-every-image) | answered |
| [naming both a size and a cursor is rejected as invalid input](#searching-a-size-beside-a-cursor-is-refused) | rejected |
| [when a user who is not the superadmin tries to search images, the call is rejected for lack of superadmin privilege](#searching-a-user-who-is-not-the-superadmin-may-not-search-images) | rejected |

**admin_search_images_gql**

| scenario | verdict |
|---|---|
| [when the superadmin reads from the front by cursor, only the requested count comes back and the answer says there is a next page](#searching-a-cursor-search-answers-the-first-page-and-says-there-is-more) | answered |
| [naming a cursor value that cannot be read is rejected as an invalid cursor](#searching-a-cursor-that-cannot-be-read-is-refused) | rejected |
| [naming both a size and a cursor is rejected as invalid input. It happens while the adapter picks the page mode, not in the request type](#searching-naming-two-pagination-modes-at-once-is-refused) | rejected |

**batch_load_aliases_by_ids**

| scenario | verdict |
|---|---|
| [reading with an empty alias id list brings back an empty list](#reading-an-empty-alias-id-list-answers-with-an-empty-list) | answered |
| [when the superadmin reads one alias seeded in advance and one id that points at no alias at once, they come back in the requested order and only the position of the unknown id is empty](#reading-loading-many-alias-ids-keeps-the-order-and-leaves-a-hole) | answered |
| [when a user granted nothing reads several alias ids at once, a rejection for lack of permission comes back for the alias that exists and the position of the unknown id is empty](#reading-a-plain-user-loading-many-alias-ids-is-refused-per-element) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [reading with an empty id list brings back an empty list](#reading-an-empty-image-id-list-answers-with-an-empty-list) | answered |
| [reading the same image id twice brings the same image back in both positions](#reading-duplicate-image-ids-keep-both-input-positions) | answered |
| [when the superadmin reads two images seeded in advance and one id that points at no image at once, they come back in the requested order and only the position of the unknown id is empty](#reading-loading-many-image-ids-keeps-the-order-and-leaves-a-hole) | answered |
| [when a user granted nothing reads several ids at once, a rejection for lack of permission comes back for each element in input order, not for the whole request](#reading-a-plain-user-loading-many-image-ids-is-refused-per-element) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [a user granted image permission on the registry can soft delete an image that is not customized too, and the deleted status comes back](#forgetting-a-granted-user-may-forget-an-image-they-did-not-customize) | answered |
| [when the superadmin soft deletes an image, the row remains and the node comes back carrying the deleted status](#forgetting-forgetting-an-image-marks-it-deleted-and-keeps-the-row) | answered |
| [when a user soft deletes a custom image they committed under the permission of their personal project, the image belongs to that personal project, so the image permission check passes and the deleted status comes back](#forgetting-the-maker-of-a-custom-image-may-forget-it) | answered |
| [when a user granted nothing tries to soft delete an image, the call is rejected for lack of permission](#forgetting-a-user-granted-nothing-may-not-forget-an-image) | rejected |
| [a custom image another user committed belongs to that user's personal project, so a user holding permission in their own personal project is rejected for lack of permission when trying to soft delete it](#forgetting-a-user-may-not-forget-a-custom-image-another-user-made) | rejected |
| [soft deleting an image that is being purged is rejected as not found. Only an alive image can be soft deleted](#forgetting-an-image-a-purge-is-working-through-cannot-be-reached) | rejected |
| [soft deleting an id that points at no image is rejected as not found](#forgetting-forgetting-an-id-that-holds-no-image-is-refused) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to soft delete several images at once, nothing is deleted and all come back in the failed list for lack of permission](#partial_bulk_forgetting-a-user-granted-nothing-forgets-none-of-several-images) | answered |
| [soft deleting two alive images and one unknown id at once brings the two back as deleted, and the unknown id comes back in the failed list as not found](#partial_bulk_forgetting-forgetting-several-answers-for-the-missing-one) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [restoring several soft-deleted images at once brings them all back alive](#partial_bulk_forgetting-restoring-several-brings-them-back-alive) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to update several images at once, nothing is updated and every one comes back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-images) | answered |
| [when the superadmin changes the tags of several images at once, they all come back with the new tag and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-images-at-once) | answered |

**restore**

| scenario | verdict |
|---|---|
| [when the superadmin restores a deleted image, the node comes back carrying the alive status](#forgetting-restoring-a-forgotten-image-brings-it-back-alive) | answered |
| [restoring an image that is already alive leaves it alive](#forgetting-restoring-an-image-that-was-never-forgotten-leaves-it-alive) | answered |
| [when a user granted nothing tries to restore an image, the call is rejected for lack of permission](#forgetting-a-user-granted-nothing-may-not-restore-an-image) | rejected |
| [restoring an id that points at no image is rejected as not found](#forgetting-restoring-an-id-that-holds-no-image-is-refused) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when images are split across two registries, a user granted permission on one registry searching scoped to that registry gets back only its images, and the other registry is not counted](#searching-a-user-granted-on-a-registry-reads-the-images-it-holds) | answered |
| [when a user granted nothing tries to search images scoped to one registry, the call is rejected for lack of permission](#searching-a-user-who-cannot-read-the-registry-is-refused-its-images) | rejected |

**scoped_search_aliases**

| scenario | verdict |
|---|---|
| [a user granted permission on the image searching its aliases gets the attached alias back](#searching-a-user-who-can-read-the-image-gets-its-aliases) | answered |
| [when a user granted nothing tries to search the aliases of that image, the call is rejected for lack of permission](#searching-a-user-who-cannot-read-the-image-is-refused-its-aliases) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin updates without naming any value, the whole node comes back unchanged](#editing-an-edit-that-names-no-value-changes-nothing) | answered |
| [when the superadmin changes the labels and the CPU lower and upper limits, the values it named come back](#editing-changing-labels-and-resource-limits-returns-the-new-values) | answered |
| [when the superadmin changes only the tag, only the tag takes the new value and every other field stays as it was](#editing-changing-only-the-tag-leaves-every-other-field-alone) | answered |
| [when the superadmin changes several basic fields such as the name and the registry at once, the values it named come back](#editing-changing-the-remaining-scalar-fields-returns-the-new-values) | answered |
| [when the superadmin clears the accelerator list, that field comes back empty. It is the only field that distinguishes omission from clearing](#editing-clearing-the-accelerator-list-empties-it) | answered |
| [when the superadmin names an accelerator, the node comes back carrying that name](#editing-writing-an-accelerator-onto-an-image-that-had-none) | answered |
| [when a user granted nothing tries to update an image, the call is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-an-image) | rejected |
| [updating an id that points at no image is rejected as not found](#editing-editing-an-id-that-holds-no-image-is-refused) | rejected |

**admin_alias**

| scenario | verdict |
|---|---|
| [when the superadmin registers an alias on an image, the alias and the image it names come back](#aliasing-aliasing-an-image-answers-with-the-alias-and-the-image-it-names) | answered |
| [registering an alias on an id that points at no image is rejected as not found](#aliasing-aliasing-an-id-that-holds-no-image-is-refused) | rejected |
| [registering an alias that is already in use is rejected as a unique constraint violation](#aliasing-an-alias-that-is-already-in-use-is-refused) | rejected |
| [even the maker of a custom image may not register an alias, because the superadmin check protects alias registration, not the permission on that image](#aliasing-the-maker-of-a-custom-image-still-may-not-alias-it) | rejected |

**admin_dealias**

| scenario | verdict |
|---|---|
| [when the superadmin removes a registered alias, the removed alias and its image come back](#aliasing-dealiasing-answers-with-the-alias-it-removed) | answered |
| [when a user who is not the superadmin tries to remove an alias, the call is rejected for lack of superadmin privilege](#aliasing-a-user-who-is-not-the-superadmin-may-not-dealias) | rejected |
| [removing a name no image holds is rejected as not found](#aliasing-dealiasing-a-name-no-image-holds-is-refused) | rejected |

**admin_purge**

| scenario | verdict |
|---|---|
| [when an image that holds an alias is purged, the purged image comes back](#retiring-purging-an-aliased-image-answers-with-the-image-it-removed) | answered |
| [when the superadmin purges an image, the purged image comes back](#retiring-purging-an-image-answers-with-the-image-it-removed) | answered |
| [when a user purges a custom image they committed under the permission of their personal project, the image belongs to that personal project, so both the image permission check and the custom image creator check pass and the purged image comes back](#retiring-the-maker-of-a-custom-image-may-purge-it) | answered |
| [a user holding permission still cannot purge an image that is not customized. The image permission check passes, and then the custom image creator check rejects the call](#retiring-a-granted-user-may-not-purge-an-image-they-did-not-customize) | rejected |
| [when a user granted nothing tries to purge an image, the call is rejected for lack of permission](#retiring-a-user-granted-nothing-may-not-purge-an-image) | rejected |
| [purging an id that points at no image is rejected as not found](#retiring-purging-an-id-that-holds-no-image-is-refused) | rejected |

**admin_scan_image**

| scenario | verdict |
|---|---|
| [when the superadmin scans an already registered image, it refreshes the registered image with the registry values and brings it back without creating a new one](#scanning-scanning-a-registered-image-refreshes-it-from-the-registry) | answered |
| [when the superadmin scans an unregistered image, one image of the requested architecture comes back. A scan runs only with the superadmin role](#scanning-scanning-an-unregistered-image-registers-the-requested-architecture) | answered |
| [a name no registry holds as an image is rejected without a scan. Giving only the registry name does not scan the whole registry](#scanning-a-name-no-registry-holds-as-an-image-is-refused-without-a-scan) | rejected |
| [scanning a tag the registry does not hold is rejected as not found](#scanning-a-tag-the-registry-does-not-hold-is-refused) | rejected |
| [a plain user may not run a scan, so the call is rejected for lack of superadmin privilege](#scanning-a-user-who-is-not-the-superadmin-may-not-scan) | rejected |

**admin_search_image_aliases**

| scenario | verdict |
|---|---|
| [when the superadmin searches only the aliases of one image ordered by name descending, only those aliases come back ordered](#searching-filtering-aliases-by-image-and-ordering-by-name) | answered |
| [with an alias attached, a superadmin searching aliases gets that alias back](#searching-searching-aliases-answers-with-the-one-that-was-attached) | answered |
| [with no alias attached, a superadmin searching aliases gets an empty answer](#searching-searching-aliases-when-none-were-attached-answers-empty) | answered |
| [when a user who is not the superadmin tries to search aliases, the call is rejected for lack of superadmin privilege](#searching-a-user-who-is-not-the-superadmin-may-not-search-aliases) | rejected |

### admin_search

<a id="searching-a-cursor-alone-answers-the-first-page-and-says-there-is-more"></a>

#### [a-cursor-alone-answers-the-first-page-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when the superadmin searches with only a cursor and no size or offset, only the requested count comes back and the answer says there is a next page

Given

- one registry and 3 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Image image-2-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches from the front by cursor

Then

- only the requested count comes back and the answer says there is a next page
  - length = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

<a id="searching-filtering-images-by-creator-returns-only-images-they-committed"></a>

#### [filtering-images-by-creator-returns-only-images-they-committed](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

among custom images committed by the caller and by another user, searching for the ones the caller committed brings back only the caller's images

Given

- one custom image the caller committed and one custom image another user committed, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Image mine-1: x86_64 image, custom image with an owner
  - Image theirs-1: x86_64 image, custom image with an owner

When

- ImageAdapter.admin_search: user-1 searches committed by the caller taking 50 per page

Then

- only images the caller committed come back
  - items = ['mine-1']
  - creator_id: same as the id of the caller
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-images-by-customized-returns-only-customized-images"></a>

#### [filtering-images-by-customized-returns-only-customized-images](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

searching a mix of customized and uncustomized images for customized images brings back only the customized images together with the user who committed them

Given

- one custom image the caller committed and one image that is not customized, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Image customized-1: x86_64 image, custom image with an owner
  - Image uncustomized-1: x86_64 image

When

- ImageAdapter.admin_search: user-1 searches customized taking 50 per page

Then

- only customized images come back, carrying the caller as the user who committed them
  - items = ['customized-1']
  - customized = [True]
  - creator_id: same as the id of the caller
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-images-by-name-returns-only-the-match"></a>

#### [filtering-images-by-name-returns-only-the-match](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when the superadmin searches by the name of one image, only that image comes back

Given

- one registry and 3 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Image image-2-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches by the name image-0-1 taking 50 per page

Then

- only the image whose name matches comes back
  - items = ['image-0-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-images-by-not-customized-returns-only-uncustomized-images"></a>

#### [filtering-images-by-not-customized-returns-only-uncustomized-images](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

searching a mix of customized and uncustomized images for images that are not customized brings back only the uncustomized images

Given

- one custom image the caller committed and one image that is not customized, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Image customized-1: x86_64 image, custom image with an owner
  - Image uncustomized-1: x86_64 image

When

- ImageAdapter.admin_search: user-1 searches not customized taking 50 per page

Then

- only images that are not customized come back, and the user who committed them is empty
  - items = ['uncustomized-1']
  - customized = [False]
  - creator_id = [None]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-images-by-status-returns-only-alive-images"></a>

#### [filtering-images-by-status-returns-only-alive-images](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

searching a mix of alive and deleted images for the alive status brings back only those images

Given

- one alive image and one deleted image, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image alive-1: x86_64 image
  - Image deleted-1: x86_64 image, status DELETED
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches with status ALIVE taking 50 per page

Then

- only alive images come back
  - items = ['alive-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-with-fifty-and-says-there-is-more"></a>

#### [omitting-the-page-size-answers-with-fifty-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when the superadmin searches with the page size omitted, only 50 come back and the answer says there is a next page

Given

- one registry and 51 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Image image-2-1: x86_64 image
  - Image image-3-1: x86_64 image
  - Image image-4-1: x86_64 image
  - Image image-5-1: x86_64 image
  - Image image-6-1: x86_64 image
  - Image image-7-1: x86_64 image
  - Image image-8-1: x86_64 image
  - Image image-9-1: x86_64 image
  - Image image-10-1: x86_64 image
  - Image image-11-1: x86_64 image
  - Image image-12-1: x86_64 image
  - Image image-13-1: x86_64 image
  - Image image-14-1: x86_64 image
  - Image image-15-1: x86_64 image
  - Image image-16-1: x86_64 image
  - Image image-17-1: x86_64 image
  - Image image-18-1: x86_64 image
  - Image image-19-1: x86_64 image
  - Image image-20-1: x86_64 image
  - Image image-21-1: x86_64 image
  - Image image-22-1: x86_64 image
  - Image image-23-1: x86_64 image
  - Image image-24-1: x86_64 image
  - Image image-25-1: x86_64 image
  - Image image-26-1: x86_64 image
  - Image image-27-1: x86_64 image
  - Image image-28-1: x86_64 image
  - Image image-29-1: x86_64 image
  - Image image-30-1: x86_64 image
  - Image image-31-1: x86_64 image
  - Image image-32-1: x86_64 image
  - Image image-33-1: x86_64 image
  - Image image-34-1: x86_64 image
  - Image image-35-1: x86_64 image
  - Image image-36-1: x86_64 image
  - Image image-37-1: x86_64 image
  - Image image-38-1: x86_64 image
  - Image image-39-1: x86_64 image
  - Image image-40-1: x86_64 image
  - Image image-41-1: x86_64 image
  - Image image-42-1: x86_64 image
  - Image image-43-1: x86_64 image
  - Image image-44-1: x86_64 image
  - Image image-45-1: x86_64 image
  - Image image-46-1: x86_64 image
  - Image image-47-1: x86_64 image
  - Image image-48-1: x86_64 image
  - Image image-49-1: x86_64 image
  - Image image-50-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches with the page size omitted

Then

- only the requested count comes back and the answer says there is a next page
  - length = 50
  - total_count = 51
  - has_next_page = True
  - has_previous_page = False

<a id="searching-ordering-by-name-and-offsetting-returns-the-middle-page"></a>

#### [ordering-by-name-and-offsetting-returns-the-middle-page](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

ordering by name descending and skipping the first item brings back the second and third images

Given

- one registry and 4 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Image image-2-1: x86_64 image
  - Image image-3-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches ordered by name descending skipping the first 1 and taking 2 per page

Then

- the middle two of the ordered result come back with both page flags
  - items = ['image-2-1', 'image-1-1']
  - total_count = 4
  - has_next_page = True
  - has_previous_page = True

<a id="searching-searching-without-a-filter-counts-every-image"></a>

#### [searching-without-a-filter-counts-every-image](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when the superadmin searches without a filter, every image seeded in advance comes back

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches taking 50 per page

Then

- every image created in advance is counted
  - items = ['image-0-1', 'image-1-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-size-beside-a-cursor-is-refused"></a>

#### [a-size-beside-a-cursor-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

naming both a size and a cursor is rejected as invalid input

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches with the size and a cursor at once

Then

- the call is rejected
  - rejected: InvalidGraphQLParameters

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-images"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-images](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when a user who is not the superadmin tries to search images, the call is rejected for lack of superadmin privilege

Given

- one registry and 2 images in it, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search: user-1 searches taking 50 per page

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_images_gql

<a id="searching-a-cursor-search-answers-the-first-page-and-says-there-is-more"></a>

#### [a-cursor-search-answers-the-first-page-and-says-there-is-more](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when the superadmin reads from the front by cursor, only the requested count comes back and the answer says there is a next page

Given

- one registry and 3 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Image image-2-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_images_gql: user-1 searches from the front by cursor

Then

- only the requested count comes back and the answer says there is a next page
  - length = 2
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-cursor-that-cannot-be-read-is-refused"></a>

#### [a-cursor-that-cannot-be-read-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

naming a cursor value that cannot be read is rejected as an invalid cursor

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_images_gql: user-1 searches with a broken cursor

Then

- the call is rejected
  - rejected: InvalidCursor

<a id="searching-naming-two-pagination-modes-at-once-is-refused"></a>

#### [naming-two-pagination-modes-at-once-is-refused](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

naming both a size and a cursor is rejected as invalid input. It happens while the adapter picks the page mode, not in the request type

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_images_gql: user-1 searches with the size and a cursor at once

Then

- the call is rejected
  - rejected: InvalidGraphQLParameters

### batch_load_aliases_by_ids

<a id="reading-an-empty-alias-id-list-answers-with-an-empty-list"></a>

#### [an-empty-alias-id-list-answers-with-an-empty-list](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

reading with an empty alias id list brings back an empty list

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_aliases_by_ids: user-1 reads with an empty alias id list

Then

- an empty list comes back
  - items = []

<a id="reading-loading-many-alias-ids-keeps-the-order-and-leaves-a-hole"></a>

#### [loading-many-alias-ids-keeps-the-order-and-leaves-a-hole](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

when the superadmin reads one alias seeded in advance and one id that points at no alias at once, they come back in the requested order and only the position of the unknown id is empty

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_aliases_by_ids: user-1 reads one alias seeded in advance and one unknown id at once

Then

- the aliases come back in the requested order and the position of the unknown id is empty
  - length = 2
  - aliases = ['seeded-alias', None]

<a id="reading-a-plain-user-loading-many-alias-ids-is-refused-per-element"></a>

#### [a-plain-user-loading-many-alias-ids-is-refused-per-element](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

when a user granted nothing reads several alias ids at once, a rejection for lack of permission comes back for the alias that exists and the position of the unknown id is empty

Given

- one image with an alias registered, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_aliases_by_ids: user-1 reads one alias seeded in advance and one unknown id at once

Then

- a rejection for lack of permission comes back for the alias that exists, and an empty value for the unknown id
  - length = 2
  - rejected: NotEnoughPermission
  - [1] = None

### batch_load_by_ids

<a id="reading-an-empty-image-id-list-answers-with-an-empty-list"></a>

#### [an-empty-image-id-list-answers-with-an-empty-list](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

reading with an empty id list brings back an empty list

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- an empty list comes back
  - items = []

<a id="reading-duplicate-image-ids-keep-both-input-positions"></a>

#### [duplicate-image-ids-keep-both-input-positions](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

reading the same image id twice brings the same image back in both positions

Given

- one registry and 1 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_by_ids: user-1 reads the same image id twice

Then

- the same image comes back in both positions
  - length = 2
  - names = ['image-0-1', 'image-0-1']

<a id="reading-loading-many-image-ids-keeps-the-order-and-leaves-a-hole"></a>

#### [loading-many-image-ids-keeps-the-order-and-leaves-a-hole](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

when the superadmin reads two images seeded in advance and one id that points at no image at once, they come back in the requested order and only the position of the unknown id is empty

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_by_ids: user-1 reads two images seeded in advance and one unknown id at once

Then

- the images come back in the requested order and the position of the unknown id is empty
  - length = 3
  - [0].name = 'image-0-1'
  - [1] = None
  - [2].name = 'image-1-1'

<a id="reading-a-plain-user-loading-many-image-ids-is-refused-per-element"></a>

#### [a-plain-user-loading-many-image-ids-is-refused-per-element](/tests/scenario/bai_scenario/manager/image/test_reading.py): pass

when a user granted nothing reads several ids at once, a rejection for lack of permission comes back for each element in input order, not for the whole request

Given

- one registry and 2 images in it, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.batch_load_by_ids: user-1 reads two images seeded in advance and one unknown id at once

Then

- a rejection for lack of permission comes back for each element in input order
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### delete

<a id="forgetting-a-granted-user-may-forget-an-image-they-did-not-customize"></a>

#### [a-granted-user-may-forget-an-image-they-did-not-customize](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

a user granted image permission on the registry can soft delete an image that is not customized too, and the deleted status comes back

Given

- one image that is not customized and one user with permission on that image
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to handle images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.delete: user-1 soft deletes image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="forgetting-forgetting-an-image-marks-it-deleted-and-keeps-the-row"></a>

#### [forgetting-an-image-marks-it-deleted-and-keeps-the-row](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

when the superadmin soft deletes an image, the row remains and the node comes back carrying the deleted status

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.delete: user-1 soft deletes image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="forgetting-the-maker-of-a-custom-image-may-forget-it"></a>

#### [the-maker-of-a-custom-image-may-forget-it](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

when a user soft deletes a custom image they committed under the permission of their personal project, the image belongs to that personal project, so the image permission check passes and the deleted status comes back

Given

- one custom image the caller committed, with image permission in the caller's personal project
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Committed image image-1: custom image with an owner, belongs to that user's personal project
  - Prepare a user granted permission to handle the project's images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.delete: user-1 soft deletes image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = True
  - creator_id: same as the id of the user who committed the image
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="forgetting-a-user-granted-nothing-may-not-forget-an-image"></a>

#### [a-user-granted-nothing-may-not-forget-an-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

when a user granted nothing tries to soft delete an image, the call is rejected for lack of permission

Given

- one image that is not customized and one user with no permission
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.delete: user-1 soft deletes image-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="forgetting-a-user-may-not-forget-a-custom-image-another-user-made"></a>

#### [a-user-may-not-forget-a-custom-image-another-user-made](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

a custom image another user committed belongs to that user's personal project, so a user holding permission in their own personal project is rejected for lack of permission when trying to soft delete it

Given

- one custom image another user committed and the caller holds image permission only in their own personal project
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Committed image image-1: custom image with an owner, belongs to that user's personal project
  - Prepare a user granted permission to handle the project's images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-2: holds Role image-keeper-1

When

- ImageAdapter.delete: user-2 soft deletes image-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="forgetting-an-image-a-purge-is-working-through-cannot-be-reached"></a>

#### [an-image-a-purge-is-working-through-cannot-be-reached](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

soft deleting an image that is being purged is rejected as not found. Only an alive image can be soft deleted

Given

- one registry and one image in it, status PURGING, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image, status PURGING
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.delete: user-1 soft deletes image-1

Then

- the call is rejected
  - rejected: ImageNotFound

<a id="forgetting-forgetting-an-id-that-holds-no-image-is-refused"></a>

#### [forgetting-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

soft deleting an id that points at no image is rejected as not found

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.delete: user-1 soft deletes an id that points at no image

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_delete

<a id="partial_bulk_forgetting-a-user-granted-nothing-forgets-none-of-several-images"></a>

#### [a-user-granted-nothing-forgets-none-of-several-images](/tests/scenario/bai_scenario/manager/image/test_partial_bulk_forgetting.py): pass

when a user granted nothing tries to soft delete several images at once, nothing is deleted and all come back in the failed list for lack of permission

Given

- one registry and 2 images in it, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.partial_bulk_delete: user-1 soft deletes 2 images at once

Then

- no image is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target image
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target image
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_forgetting-forgetting-several-answers-for-the-missing-one"></a>

#### [forgetting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/image/test_partial_bulk_forgetting.py): pass

soft deleting two alive images and one unknown id at once brings the two back as deleted, and the unknown id comes back in the failed list as not found

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.partial_bulk_delete: user-1 soft deletes 2 images and one missing id at once

Then

- every target image comes back with status DELETED and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - id: same as the id of the image created in advance
  - name = 'image-0-1'
  - image = 'image-0-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-0-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-0-1'
  - identity.namespace = 'image-0-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-0-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]
  - id: same as the id of the image created in advance
  - name = 'image-1-1'
  - image = 'image-1-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.DELETED: 'DELETED'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-1-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1-1'
  - identity.namespace = 'image-1-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-1-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.DELETED: 'DELETED'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_restore

<a id="partial_bulk_forgetting-restoring-several-brings-them-back-alive"></a>

#### [restoring-several-brings-them-back-alive](/tests/scenario/bai_scenario/manager/image/test_partial_bulk_forgetting.py): pass

restoring several soft-deleted images at once brings them all back alive

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.partial_bulk_restore: user-1 soft deletes 2 images at once and then restores them at once

Then

- every target image comes back with status ALIVE and nothing failed
  - successes count = 2
  - id: same as the id of the image created in advance
  - name = 'image-0-1'
  - image = 'image-0-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-0-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-0-1'
  - identity.namespace = 'image-0-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-0-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]
  - id: same as the id of the image created in advance
  - name = 'image-1-1'
  - image = 'image-1-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-1-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1-1'
  - identity.namespace = 'image-1-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-1-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]
  - failed = []

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-images"></a>

#### [a-user-granted-nothing-edits-none-of-several-images](/tests/scenario/bai_scenario/manager/image/test_partial_bulk_editing.py): pass

when a user granted nothing tries to update several images at once, nothing is updated and every one comes back in the failed list for lack of permission

Given

- one registry and 2 images in it, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.partial_bulk_update: user-1 changes the tags of 2 images at once

Then

- no image is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target image
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target image
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-images-at-once"></a>

#### [the-superadmin-edits-several-images-at-once](/tests/scenario/bai_scenario/manager/image/test_partial_bulk_editing.py): pass

when the superadmin changes the tags of several images at once, they all come back with the new tag and nothing failed

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.partial_bulk_update: user-1 changes the tags of 2 images at once

Then

- every target image comes back with status ALIVE and nothing failed
  - successes count = 2
  - id: same as the id of the image created in advance
  - name = 'image-0-1'
  - image = 'image-0-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'edited-together'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-0-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-0-1'
  - identity.namespace = 'image-0-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-0-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]
  - id: same as the id of the image created in advance
  - name = 'image-1-1'
  - image = 'image-1-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'edited-together'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-1-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1-1'
  - identity.namespace = 'image-1-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:0000000000000000000000000000000000000000000000000000000image-1-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]
  - failed = []

### restore

<a id="forgetting-restoring-a-forgotten-image-brings-it-back-alive"></a>

#### [restoring-a-forgotten-image-brings-it-back-alive](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

when the superadmin restores a deleted image, the node comes back carrying the alive status

Given

- one registry and one image in it, status DELETED, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image, status DELETED
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.restore: user-1 restores image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="forgetting-restoring-an-image-that-was-never-forgotten-leaves-it-alive"></a>

#### [restoring-an-image-that-was-never-forgotten-leaves-it-alive](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

restoring an image that is already alive leaves it alive

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.restore: user-1 restores image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="forgetting-a-user-granted-nothing-may-not-restore-an-image"></a>

#### [a-user-granted-nothing-may-not-restore-an-image](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

when a user granted nothing tries to restore an image, the call is rejected for lack of permission

Given

- one image that is not customized and one user with no permission
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.restore: user-1 restores image-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="forgetting-restoring-an-id-that-holds-no-image-is-refused"></a>

#### [restoring-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_forgetting.py): pass

restoring an id that points at no image is rejected as not found

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.restore: user-1 restores an id that points at no image

Then

- the call is rejected
  - rejected: EntityNotFoundError

### scoped_search

<a id="searching-a-user-granted-on-a-registry-reads-the-images-it-holds"></a>

#### [a-user-granted-on-a-registry-reads-the-images-it-holds](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when images are split across two registries, a user granted permission on one registry searching scoped to that registry gets back only its images, and the other registry is not counted

Given

- two registries, 2 images in one and 2 in the other, one user granted permission on one registry
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Image here-0-1: x86_64 image
  - Image here-1-1: x86_64 image
  - Image there-0-1: x86_64 image
  - Image there-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to handle images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.scoped_search: user-1 searches images scoped to one registry

Then

- every image created in advance is counted
  - items = ['here-0-1', 'here-1-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-cannot-read-the-registry-is-refused-its-images"></a>

#### [a-user-who-cannot-read-the-registry-is-refused-its-images](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when a user granted nothing tries to search images scoped to one registry, the call is rejected for lack of permission

Given

- two registries, 2 images in one and 2 in the other, one user granted no permission
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Image here-0-1: x86_64 image
  - Image here-1-1: x86_64 image
  - Image there-0-1: x86_64 image
  - Image there-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.scoped_search: user-1 searches images scoped to one registry

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search_aliases

<a id="searching-a-user-who-can-read-the-image-gets-its-aliases"></a>

#### [a-user-who-can-read-the-image-gets-its-aliases](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

a user granted permission on the image searching its aliases gets the attached alias back

Given

- one image with an alias registered and one user with permission on that image
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to handle images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.scoped_search_aliases: user-1 searches the aliases of image-1

Then

- the alias that was attached comes back
  - items = ['seeded-alias']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-cannot-read-the-image-is-refused-its-aliases"></a>

#### [a-user-who-cannot-read-the-image-is-refused-its-aliases](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when a user granted nothing tries to search the aliases of that image, the call is rejected for lack of permission

Given

- one image with an alias registered and one user with no permission
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.scoped_search_aliases: user-1 searches the aliases of image-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-an-edit-that-names-no-value-changes-nothing"></a>

#### [an-edit-that-names-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when the superadmin updates without naming any value, the whole node comes back unchanged

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 updates without naming any value

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="editing-changing-labels-and-resource-limits-returns-the-new-values"></a>

#### [changing-labels-and-resource-limits-returns-the-new-values](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when the superadmin changes the labels and the CPU lower and upper limits, the values it named come back

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 changes several fields of image-1 at once

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = [ImageLabelInfo(key='purpose', value='scenario')]
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='2', max='4'), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = [ImageLabelInfo(key='purpose', value='scenario')]
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='2', max='4'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="editing-changing-only-the-tag-leaves-every-other-field-alone"></a>

#### [changing-only-the-tag-leaves-every-other-field-alone](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when the superadmin changes only the tag, only the tag takes the new value and every other field stays as it was

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 changes the tag of image-1 to moved

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'moved'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="editing-changing-the-remaining-scalar-fields-returns-the-new-values"></a>

#### [changing-the-remaining-scalar-fields-returns-the-new-values](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when the superadmin changes several basic fields such as the name and the registry at once, the values it named come back

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 changes several fields of image-1 at once

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'updated-image'
  - image = 'team/updated-image'
  - registry = 'updated.example.com'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'aarch64'
  - size_bytes = 2048
  - type = <ImageType.SERVICE: 'service'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
  - is_local = True
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'updated-image'
  - identity.namespace = 'team/updated-image'
  - identity.architecture = 'aarch64'
  - metadata.digest = 'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
  - metadata.size_bytes = 2048
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="editing-clearing-the-accelerator-list-empties-it"></a>

#### [clearing-the-accelerator-list-empties-it](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when the superadmin clears the accelerator list, that field comes back empty. It is the only field that distinguishes omission from clearing

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image, accelerator cuda
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 clears the accelerator list of image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="editing-writing-an-accelerator-onto-an-image-that-had-none"></a>

#### [writing-an-accelerator-onto-an-image-that-had-none](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when the superadmin names an accelerator, the node comes back carrying that name

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 sets the accelerator list of image-1 to cuda

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = 'cuda'
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['cuda']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="editing-a-user-granted-nothing-may-not-edit-an-image"></a>

#### [a-user-granted-nothing-may-not-edit-an-image](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

when a user granted nothing tries to update an image, the call is rejected for lack of permission

Given

- one registry and one image in it, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 changes the tag of image-1 to moved

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-editing-an-id-that-holds-no-image-is-refused"></a>

#### [editing-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_editing.py): pass

updating an id that points at no image is rejected as not found

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.update: user-1 updates an id that points at no image

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_alias

<a id="aliasing-aliasing-an-image-answers-with-the-alias-and-the-image-it-names"></a>

#### [aliasing-an-image-answers-with-the-alias-and-the-image-it-names](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

when the superadmin registers an alias on an image, the alias and the image it names come back

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_alias: user-1 aliases image-1 as made-alias

Then

- the alias just registered and the id of the image it names come back
  - alias = 'made-alias'
  - image_id: same as the id of the image created in advance
  - alias_id: skipped: the database generates it

<a id="aliasing-aliasing-an-id-that-holds-no-image-is-refused"></a>

#### [aliasing-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

registering an alias on an id that points at no image is rejected as not found

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_alias: user-1 aliases an id that points at no image

Then

- the call is rejected
  - rejected: ImageNotFound

<a id="aliasing-an-alias-that-is-already-in-use-is-refused"></a>

#### [an-alias-that-is-already-in-use-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

registering an alias that is already in use is rejected as a unique constraint violation

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_alias: user-1 registers the already-used alias seeded-alias

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="aliasing-the-maker-of-a-custom-image-still-may-not-alias-it"></a>

#### [the-maker-of-a-custom-image-still-may-not-alias-it](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

even the maker of a custom image may not register an alias, because the superadmin check protects alias registration, not the permission on that image

Given

- one custom image the caller committed, with image permission in the caller's personal project
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Committed image image-1: custom image with an owner, belongs to that user's personal project
  - Prepare a user granted permission to handle the project's images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.admin_alias: user-1 aliases image-1 as made-alias

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_dealias

<a id="aliasing-dealiasing-answers-with-the-alias-it-removed"></a>

#### [dealiasing-answers-with-the-alias-it-removed](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

when the superadmin removes a registered alias, the removed alias and its image come back

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_dealias: user-1 dealiases seeded-alias

Then

- the alias just removed and the id of the image it named come back
  - alias = 'seeded-alias'
  - image_id: same as the id of the image created in advance
  - alias_id: skipped: the database generates it

<a id="aliasing-a-user-who-is-not-the-superadmin-may-not-dealias"></a>

#### [a-user-who-is-not-the-superadmin-may-not-dealias](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

when a user who is not the superadmin tries to remove an alias, the call is rejected for lack of superadmin privilege

Given

- one image with an alias registered, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.admin_dealias: user-1 dealiases seeded-alias

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="aliasing-dealiasing-a-name-no-image-holds-is-refused"></a>

#### [dealiasing-a-name-no-image-holds-is-refused](/tests/scenario/bai_scenario/manager/image/test_aliasing.py): pass

removing a name no image holds is rejected as not found

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_dealias: user-1 dealiases a name no image holds

Then

- the call is rejected
  - rejected: ImageAliasNotFound

### admin_purge

<a id="retiring-purging-an-aliased-image-answers-with-the-image-it-removed"></a>

#### [purging-an-aliased-image-answers-with-the-image-it-removed](/tests/scenario/bai_scenario/manager/image/test_retiring.py): pass

when an image that holds an alias is purged, the purged image comes back

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_purge: user-1 purges the image that holds the alias seeded-alias

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="retiring-purging-an-image-answers-with-the-image-it-removed"></a>

#### [purging-an-image-answers-with-the-image-it-removed](/tests/scenario/bai_scenario/manager/image/test_retiring.py): pass

when the superadmin purges an image, the purged image comes back

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_purge: user-1 purges image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = False
  - creator_id = None
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="retiring-the-maker-of-a-custom-image-may-purge-it"></a>

#### [the-maker-of-a-custom-image-may-purge-it](/tests/scenario/bai_scenario/manager/image/test_retiring.py): pass

when a user purges a custom image they committed under the permission of their personal project, the image belongs to that personal project, so both the image permission check and the custom image creator check pass and the purged image comes back

Given

- one custom image the caller committed, with image permission in the caller's personal project
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Committed image image-1: custom image with an owner, belongs to that user's personal project
  - Prepare a user granted permission to handle the project's images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.admin_purge: user-1 purges image-1

Then

- every field of the image node matches the expected value
  - id: same as the id of the image created in advance
  - name = 'image-1'
  - image = 'image-1'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = None
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 0
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = None
  - config_digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - is_local = False
  - customized = True
  - creator_id: same as the id of the user who committed the image
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'image-1'
  - identity.namespace = 'image-1'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:000000000000000000000000000000000000000000000000000000000image-1'
  - metadata.size_bytes = 0
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="retiring-a-granted-user-may-not-purge-an-image-they-did-not-customize"></a>

#### [a-granted-user-may-not-purge-an-image-they-did-not-customize](/tests/scenario/bai_scenario/manager/image/test_retiring.py): pass

a user holding permission still cannot purge an image that is not customized. The image permission check passes, and then the custom image creator check rejects the call

Given

- one image that is not customized and one user with permission on that image
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to handle images
    - Role image-keeper-1: applies only within the scope it is granted in
    - Role image-keeper-1: READ allowed on every image
    - Role image-keeper-1: SOFT_DELETE allowed on every image
    - Role image-keeper-1: HARD_DELETE allowed on every image
    - regular user user-1: holds Role image-keeper-1

When

- ImageAdapter.admin_purge: user-1 purges image-1

Then

- the call is rejected
  - rejected: ImageAccessForbiddenError

<a id="retiring-a-user-granted-nothing-may-not-purge-an-image"></a>

#### [a-user-granted-nothing-may-not-purge-an-image](/tests/scenario/bai_scenario/manager/image/test_retiring.py): pass

when a user granted nothing tries to purge an image, the call is rejected for lack of permission

Given

- one image that is not customized and one user with no permission
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.admin_purge: user-1 purges image-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-purging-an-id-that-holds-no-image-is-refused"></a>

#### [purging-an-id-that-holds-no-image-is-refused](/tests/scenario/bai_scenario/manager/image/test_retiring.py): pass

purging an id that points at no image is rejected as not found

Given

- one registry and one image in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_purge: user-1 purges an id that points at no image

Then

- the call is rejected
  - rejected: ImageNotFound

### admin_scan_image

<a id="scanning-scanning-a-registered-image-refreshes-it-from-the-registry"></a>

#### [scanning-a-registered-image-refreshes-it-from-the-registry](/tests/scenario/bai_scenario/manager/image/test_scanning.py): pass

when the superadmin scans an already registered image, it refreshes the registered image with the registry values and brings it back without creating a new one

Given

- one registry serving the tag stable/python:latest for amd64, arm64, one x86_64 image already registered with that tag, one superadmin
  - Domain home-1
  - Container registry host-1: image source, project stable
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Image stable/python:latest: x86_64 image, config digest is sha256:before-scan

When

- ImageAdapter.admin_scan_image: user-1 scans the tag stable/python:latest for the x86_64 architecture

Then

- the image node registered for the requested architecture comes back
  - id: same as the id of the already registered image
  - name = 'host-1/stable/python:latest'
  - image = 'stable/python'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = 'stable'
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 10
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = '*'
  - config_digest = 'sha256:config-amd64'
  - is_local = False
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'host-1/stable/python:latest'
  - identity.namespace = 'stable/python'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:config-amd64'
  - metadata.size_bytes = 10
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="scanning-scanning-an-unregistered-image-registers-the-requested-architecture"></a>

#### [scanning-an-unregistered-image-registers-the-requested-architecture](/tests/scenario/bai_scenario/manager/image/test_scanning.py): pass

when the superadmin scans an unregistered image, one image of the requested architecture comes back. A scan runs only with the superadmin role

Given

- one registry serving the tag stable/python:latest for amd64, arm64, one superadmin
  - Domain home-1
  - Container registry host-1: image source, project stable
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_scan_image: user-1 scans the tag stable/python:latest for the x86_64 architecture

Then

- the image node registered for the requested architecture comes back
  - id: skipped: the scan created the row, so the database decides it
  - name = 'host-1/stable/python:latest'
  - image = 'stable/python'
  - registry = 'host-1'
  - registry_id: same as the id of the registry created in advance
  - project = 'stable'
  - tag = 'latest'
  - architecture = 'x86_64'
  - size_bytes = 10
  - type = <ImageType.COMPUTE: 'compute'>
  - status = <ImageStatus.ALIVE: 'ALIVE'>
  - labels = []
  - tags = []
  - resource_limits = [ImageResourceLimitInfo(key='cpu', min='1', max=None), ImageResourceLimitInfo(key='mem', min='1073741824', max=None)]
  - accelerators = '*'
  - config_digest = 'sha256:config-amd64'
  - is_local = False
  - created_at: the time this run wrote
  - last_used_at: skipped: a session records it, so this run cannot know it
  - identity.canonical_name = 'host-1/stable/python:latest'
  - identity.namespace = 'stable/python'
  - identity.architecture = 'x86_64'
  - metadata.digest = 'sha256:config-amd64'
  - metadata.size_bytes = 10
  - metadata.created_at: the time this run wrote
  - metadata.last_used_at: same as the node's last_used_at field
  - metadata.tags = []
  - metadata.labels = []
  - metadata.status = <ImageStatus.ALIVE: 'ALIVE'>
  - requirements.supported_accelerators = ['*']
  - requirements.resource_limits = [ImageResourceLimitGQLInfo(key='cpu', min='1', max='Infinity'), ImageResourceLimitGQLInfo(key='mem', min='1073741824', max='Infinity')]

<a id="scanning-a-name-no-registry-holds-as-an-image-is-refused-without-a-scan"></a>

#### [a-name-no-registry-holds-as-an-image-is-refused-without-a-scan](/tests/scenario/bai_scenario/manager/image/test_scanning.py): pass

a name no registry holds as an image is rejected without a scan. Giving only the registry name does not scan the whole registry

Given

- one registry serving the tag stable/python:latest for amd64, arm64, one superadmin
  - Domain home-1
  - Container registry host-1: image source, project stable
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_scan_image: user-1 scans the registry name alone without an image for the x86_64 architecture

Then

- the call is rejected
  - rejected: RegistryNotFoundForImage

<a id="scanning-a-tag-the-registry-does-not-hold-is-refused"></a>

#### [a-tag-the-registry-does-not-hold-is-refused](/tests/scenario/bai_scenario/manager/image/test_scanning.py): pass

scanning a tag the registry does not hold is rejected as not found

Given

- one registry serving the tag stable/python:latest for amd64, arm64, one superadmin
  - Domain home-1
  - Container registry host-1: image source, project stable
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_scan_image: user-1 scans the tag stable/python:removed for the x86_64 architecture

Then

- the call is rejected
  - rejected: ImageNotFound

<a id="scanning-a-user-who-is-not-the-superadmin-may-not-scan"></a>

#### [a-user-who-is-not-the-superadmin-may-not-scan](/tests/scenario/bai_scenario/manager/image/test_scanning.py): pass

a plain user may not run a scan, so the call is rejected for lack of superadmin privilege

Given

- one registry serving the tag stable/python:latest for amd64, arm64, one user
  - Domain home-1
  - Container registry host-1: image source, project stable
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.admin_scan_image: user-1 scans the tag stable/python:latest for the x86_64 architecture

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_image_aliases

<a id="searching-filtering-aliases-by-image-and-ordering-by-name"></a>

#### [filtering-aliases-by-image-and-ordering-by-name](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when the superadmin searches only the aliases of one image ordered by name descending, only those aliases come back ordered

Given

- two images, two aliases on one and one on the other, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image wanted-1: x86_64 image
  - Image other-1: x86_64 image
  - Image wanted-1: alias alpha
  - Image wanted-1: alias zeta
  - Image other-1: alias middle
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_image_aliases: user-1 searches the aliases of one image ordered by name descending

Then

- only the aliases of that image come back, ordered by name descending
  - items = ['zeta', 'alpha']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-searching-aliases-answers-with-the-one-that-was-attached"></a>

#### [searching-aliases-answers-with-the-one-that-was-attached](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

with an alias attached, a superadmin searching aliases gets that alias back

Given

- one image with an alias registered, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-1: x86_64 image
  - Image image-1: alias seeded-alias
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_image_aliases: user-1 searches aliases

Then

- the alias that was attached comes back
  - items = ['seeded-alias']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-searching-aliases-when-none-were-attached-answers-empty"></a>

#### [searching-aliases-when-none-were-attached-answers-empty](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

with no alias attached, a superadmin searching aliases gets an empty answer

Given

- one registry and 2 images in it, one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_image_aliases: user-1 searches aliases

Then

- there is no alias at all
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-aliases"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-aliases](/tests/scenario/bai_scenario/manager/image/test_searching.py): pass

when a user who is not the superadmin tries to search aliases, the call is rejected for lack of superadmin privilege

Given

- one registry and 2 images in it, one user
  - Domain home-1
  - Container registry host-1: image source
  - Image image-0-1: x86_64 image
  - Image image-1-1: x86_64 image
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ImageAdapter.admin_search_image_aliases: user-1 searches aliases

Then

- the call is rejected
  - rejected: InsufficientPrivilege

