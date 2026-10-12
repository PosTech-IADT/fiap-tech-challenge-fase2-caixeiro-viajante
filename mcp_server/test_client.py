import asyncio
import os

from mcp import ClientSession
from mcp.client.sse import sse_client


async def main() -> None:
    url = os.getenv("MCP_URL", "http://localhost:8000/sse")

    async with sse_client(url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            ferramentas = await session.list_tools()
            resultado = await session.call_tool(
                "consultar_ponto_entrega",
                {"nome": "HCor"},
            )

            print("Ferramentas disponiveis:")
            for ferramenta in ferramentas.tools:
                print(f"- {ferramenta.name}")

            print("\nResposta da consulta de ponto:")
            print(resultado.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
