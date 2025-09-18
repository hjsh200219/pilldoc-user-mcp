import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.mcp_tools import (
    register_auth_tools,
    register_druginfo_tools,
    register_pilldoc_tools,
)


# Load env once
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)


def create_server() -> FastMCP:
    mcp = FastMCP("pilldoc-user-mcp")
    register_auth_tools(mcp)
    register_druginfo_tools(mcp)
    register_pilldoc_tools(mcp)
    return mcp


if __name__ == "__main__":
    create_server().run()


