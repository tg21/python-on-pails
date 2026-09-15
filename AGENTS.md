# AGENTS.md

Zero dependencies — vanilla stdlib Python 3 only. Do not add requirements/installs.
Adding dev dependicies are fine, e.g adding testing libraries.

## Run / test
- Run server: `python3 main.py` (binds `config.host:config.port` in `server/settings.py`, default `0.0.0.0:80` — needs sudo/root or change port).
- Tests: `python3 -m unittest discover -s tests -v` (or `python3 -m unittest tests.test_pyop_server -v`). Only test file is `tests/test_pyop_server.py`; it unit-tests `PyOPSever.ParseRequestDataInToObject`, not a live server.
- No lint/typecheck/formatter/CI config.


## Conventions that differ from normal frameworks (can be changed based on requirements, as long as framework stays true to its ideology or is backwards compatible)
- Views (`views.py`): bare callables take **no args**; string = file under `config.static`; `.py` runs `main()` with no args via `exec`, `.pyhtml` executes `<py>...</py>` blocks. Returns `text/html`.
- Controllers (`routes.py`): value forms are `callable` | `{'action','input','customResponse'}` dict | `'path/to.py'` string (must define file-level `main`, executed in **subprocess** via `server/responseHandler.py:subprocessPyFile`, gets pickled reqData; access via `from server.helper import reqData`). Callable without `input` uses introspection (`__code__.co_varnames` + `__annotations__`) for auto type-casting; `PyopReq`-annotated param receives the raw handler (`send_custom_response`, `client_address`). With `input`, `input` is a model class (`mvc/models/inputModels.py`: plain class whose attrs are types/callables, e.g. `d = [int]`).
- Response MIME: plain callable/file result defaults to `application/json`; `customResponse=True` expects dict `{content, code?, mimeType?}`; `customResponse={...}` wraps raw return with those code/mime defaults.
- Request parsing (`main.py:FormatRequestData` + `server/misc.py:parseJsonToClass`): GET reads query string, POST reads `Content-Length` body; tries `json.loads`, falls back to `a=1&b=2` query-string parse (`jsonify`). Failed casts silently become `None` (see test expectations) — do not "fix" to raise.

more infrormation is stored in docs/ folder
IMPORTANT: Only read files from docs/ when required.

docs/architecture.md - contains information about architecture
docs/serving.md - protocol contracts, WSGI/ASGI adapters, production vs legacy, proxy/lifecycle/timeouts, deployment patterns


## Development
 - We'll do test driven development
 - Whatever changes you make, you add summary to changelog.md. It'll be an append only log, no need to read it. Even if we revert something, we'll only append to changelog.
 - any spike/ressearch plans that we make, if I tell you to save them for future, then they'll be saved to research_docs folder.
 - no need to read from research_docs folder unless explicitly asked.
 - We prioritze clean code, maintainablity and evolvability for this project. 
 - IMPORTANT: follow DRY (Don't repeat yourself) principle when wiriting code.
 - after we are done making changes, add relevent updates to documentation in docs/ folder, if a new doc file is created then update the dictionary for docs in AGENTS.md
 - Don't ever read server/mimetypes.py. It's a big file has `mimeTypes: dict[str, str]`. no need to waste context reading that. It contains all the mime types.

 ## MOST IMPORTANT: one core ideology of this project should not be sacrificed (we should try our best to preserve it)
 - Users of this framework should not have to waste their time writing server, they should be able to focus on writing their business logic.
 - That means, that all the settings can be configured from settings.py while the best options are on by default.
