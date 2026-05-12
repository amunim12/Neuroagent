# Documentation media

This directory holds the images and recordings referenced from the project's [README](../../README.md).

The README references these assets by relative path, so the filenames matter. Drop the files below into this directory once you've recorded / captured them.

## Required assets

| File                    | What it should show                                                                                              | Suggested capture                                                                                                  |
|-------------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `demo.gif`              | A single end-to-end agent run in the browser: goal submission → planning → tool calls streaming → final answer. | Record at 1280×720, 10–15 fps, under ~8 MB. A task that uses at least two tools (web search + code exec) works well. |
| `langsmith-trace.png`   | A LangSmith run page showing the node-by-node trace of a representative agent run, with model/tool spans visible. | Full-page screenshot from `https://smith.langchain.com` of a run tagged to the `neuroagent` project.               |
| `architecture.png`      | *(Optional)* A rendered version of the ASCII diagram in the README, for use in social cards / blog posts.        | Export from Excalidraw / diagrams.net at 1600px wide.                                                              |

## Capture tips

### `demo.gif`

1. Start the stack with `docker compose up --build` and wait until both `backend` and `frontend` containers are healthy.
2. Register a new user, sign in, and open the dashboard.
3. Submit a goal that exercises multiple tools, e.g. *"Search for the latest stable Python release, then write a snippet that prints its major/minor version."*
4. Record from goal submission to the final synthesised answer.
5. Trim dead air and convert to `.gif` (ffmpeg, [Peek](https://github.com/phw/peek), or ScreenToGif on Windows).

### `langsmith-trace.png`

1. Ensure `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` are set in `.env`.
2. Run a single agent session (the same task used for `demo.gif` is fine).
3. Open the run in [LangSmith](https://smith.langchain.com) under the `neuroagent` project.
4. Expand the `read_memory → plan → route_model → execute → synthesize → write_memory` chain so every node is visible.
5. Full-page screenshot. Redact any user identifiers that shouldn't be public.

## Why these files are not committed

Recording a meaningful demo and capturing a real trace requires a working deployment with valid API keys, which the automated build intentionally does not have. The README will still render without these files — the image tags will simply show alt text until you add them.
