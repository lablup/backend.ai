# @pytest.mark.parametrize(
#     "test_scenario",
#     [
#         TestScenario.success("Success Case", PurgeImagesAction(), PurgeImagesActionResult()),
#         TestScenario.failure(
#             "When No Image exists, raise Image Not Found Error",
#             PurgeImagesAction(),
#             BackendError,
#         ),
#     ],
# )
# def test_purge_images(
#     test_scenario: TestScenario[PurgeImagesAction, PurgeImagesActionResult],
#     processors: ImageProcessors,
# ):
#     test_scenario.test(processors.purge_images.fire_and_forget)


# @pytest.mark.parametrize(
#     "test_scenario",
#     [
#         TestScenario.success("Success Case", ForgetImageAction(), ForgetImageActionResult()),
#         TestScenario.failure(
#             "When No Image exists, raise Image Not Found Error", ForgetImageAction(), BackendError
#         ),
#     ],
# )
# def test_forget_images(
#     test_scenario: TestScenario[ForgetImageAction, ForgetImageActionResult],
#     processors: ImageProcessors,
# ):
#     test_scenario.test(processors.forget_image.fire_and_forget)
