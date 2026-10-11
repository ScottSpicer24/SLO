# Backend tests

High-level notes on how the `be/` test suite is organised and what each piece
does. The suite uses **pytest** + **moto** + **boto3** and runs inside the
`be/.venv` virtual environment.

Dependencies are listed in `requirements-dev.txt` (`pytest`, `boto3`,
`moto[dynamodb]`) and installed into `be/.venv`.

NOTE: There are lambda fixtures and pytest fixtures. lambda fixtures are json taht mimic API gateway calls. Pytest fixtures are for for seting up the environment (temp db client, tables, ...).

## Running tests

Run from the `be/` directory using the project venv:

```bash
cd be
.\.venv\Scripts\python.exe -m pytest                                             # all tests
.\.venv\Scripts\python.exe -m pytest tests\functions\test_create_user.py         # single file
.\.venv\Scripts\python.exe -m pytest tests\functions\test_create_user.py::test_create_user_success  # single test
.\.venv\Scripts\python.exe -m pytest -v                                          # verbose
.\.venv\Scripts\python.exe -m pytest -x                                          # stop at first failure
.\.venv\Scripts\python.exe -m pytest --lf                                        # rerun last-failed tests
.\.venv\Scripts\python.exe -m pytest -k create_user                              # run tests matching a keyword
```

This tells pytest to use this environment (the venv for the BE)
```bash
.\.venv\Scripts\python.exe 
```

Could also potentially start the venv then run the test
```bash
.\.venv\Scripts\Activate.ps1   # activates
python -m pytest -v
```

## Layout

```
be/
├── pytest.ini
└── tests/                          # mirrors the src/ layout
    ├── conftest.py                 # shared pytest fixtures
    ├── fixtures/
    │   └── api_gateway_create_user.json
    └── functions/
        └── test_create_user.py
```

## Role of each component

### `pytest.ini`
Two settings that keep imports predictable:
- `pythonpath = src` — puts `be/src` on `sys.path` so tests can do
  `import functions...` and `import shared...` with no path hacks.
- `testpaths = tests` — points pytest at the test directory.

### `tests/conftest.py`
The single shared conftest. pytest discovers it automatically because it is an
ancestor of every test file, so its fixtures are available to all tests.

| Pytest Fixture | Role |
| --- | --- |
| `dynamodb_client` | Returns a boto3 DynamoDB client wrapped in `mock_aws()` (moto). Moto intercepts boto3 calls and emulates DynamoDB in memory, so tests never touch a real AWS account. |
| `users_table` | Creates the `users` table to match the production schema (`user_id` HASH key, `PAY_PER_REQUEST`) and sets `USERS_TABLE`, so the repo writes to the mocked table. |
| `load_event` | Loads a sample Lambda event JSON from `tests/fixtures/` and hands it back to the test to pass to a handler. |

#### load_event
- This is passed to each of the tests. 
- They then can call `event = load_event("api_gateway_create_user.json")`

### `tests/fixtures/`
Sample Lambda events stored as `.json` files (e.g. an API Gateway proxy event
for `POST /users`). They are written by hand and can be tweaked inside a test —
change the `body`, drop a field, etc. — to exercise different scenarios without
adding a new file for every case.

### `tests/functions/`
Mirrors `src/functions/`: one test file per Lambda. These tests call the thin
`handler()` with a mocked event and assert the API Gateway response (status code
and parsed body) and, on success, that the record was actually written to the
mocked table.

### Handler vs. shared logic
Handlers stay thin — they parse the event, call into `src/shared`, and return
the API Gateway response. The real work (DynamoDB access) lives in
`src/shared/db/repos/`, so those functions can also be tested directly with
plain arguments, while handlers are exercised through mocked Lambda events.

## Implmentation Details
### monkeypatch
- A part of pytest let's you temp configure/chnge your env for the test. 
- passed as a parameter to the pytest fixtures, they then use/call it as needed. 
    - DO NOT need it in the test in functions, it updates the env they live in
- Update the environment like it would in prod... but then removes it after the test
    - Not just for environment vars; attributes, cwd, items in dicts, db tables...
- `setenv("USERS_TABLE", TABLE_NAME)` This is done to ensure that the table name in the test env is the same as prod

### mock_AWS()
- Fake in-mem implmentation of aws services
- intercepts calls to aws and routes it to a local version

### Flow
 - pytest.ini > conftest.py > lambda_fixture.json > test_funct.py
1. mock_aws activates
2. pytest fixture create mock local user table
3. Set: setenv("USERS_TABLE", "users") → production code will request same table name "users"
4. When called in test (client.get_table("users")) moto/mock_aws() intercepts it and uses mock table