from pydantic import BaseModel, Field


class RtunConfig(BaseModel):
    client_port: int = Field(default=22)
    client_host: str = Field(default="127.0.0.1")
    server_port: int = Field()
    rtun_auth_key: str = Field()
    rtun_download_url: str = Field(
        default="https://github.com/snsinfu/reverse-tunnel/releases/download/v1.3.2/rtun-linux-amd64"
    )
    rtun_directory: str = Field()
