"""Local development entrypoint.

psycopg v3 async requires SelectorEventLoop. On Windows Python 3.12+, the
default is ProactorEventLoop which is incompatible. Setting the loop policy
here — before uvicorn is imported — ensures asyncio.run() inside uvicorn
creates a SelectorEventLoop for every coroutine.
"""
import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402 — must import after policy is set

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
