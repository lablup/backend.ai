# from .service import ImageService


# class ImageProcessors:
#     create_image: ActionProcessor[CreateImageAction, CreateImageActionResult]
#     forget_image: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
#     purge_images: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

#     def __init__(self, service: ImageService) -> None:
#         self.create_image = ActionProcessor(service.create_image)
#         self.forget_image = ActionProcessor(service.forget_image)
#         self.purge_images = ActionProcessor(service.purge_images)
