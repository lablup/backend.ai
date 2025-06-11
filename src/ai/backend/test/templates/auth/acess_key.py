
from ai.backend.client.config import APIConfig


class AccessKeyTemplate(WrapperTestTemplate):
    def __init__(
        self, template: TestTemplate, user_id: str, password: str, otp: Optional[str] = None
    ) -> None:
        super().__init__(template)
        self.otp = otp

    @property
    def name(self) -> str:
        return "login"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        test_id = TestIDContext.get_current()
        test_id_str = str(test_id)
        endpoint = EndpointContext.get_current()
        access_key_pair = AccesKeyPairContext.get_current()
        api_config = APIConfig(
            endpoint=endpoint.endpoint,
            endpoint_type=endpoint.endpoint_type,
            access_key=access_key_pair.access_key,
            secret_key=access_key_pair.secret_key,
        )
        
        await _login(
            session=client_session,
            test_id=test_id_str,
            otp=self.otp,
        )
        try:
            yield
        finally:
            await _logout(session=client_session, test_id=test_id_str)
