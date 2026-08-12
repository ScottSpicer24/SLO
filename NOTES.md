# Backend notes
- **src folder** and a **test folder**
- src contains: functions, shared, and a lambda layers file
    - layers is for dependencies.
    - shared is for DB, models, utils. 
- For test use moto
    - ensure tests folder mirror function folder.

```
my-app/
├── src/
│   ├── functions/
│   │   ├── create_user/
│   │   │   ├── handler.py          # Actual lambda code
│   │   │   ├── requirements.txt    # Maybe function-specific deps
│   │   │   └── __init__.py
│   │   ├── get_user/
│   │   │   └── handler.py
│   │   └── process_order/
│   │       └── handler.py
│   │
│   ├── shared/                     # code reused across functions
│   │   ├── db/
|   |   |   └── __init__.py                      
│   │   │   └── client.py           # Establishes DB connection
│   │   │   └── tables.py           # Dynamically pulls table names 
│   │   │   └── exceptions.py       # Custom exceptions
│   │   │   └── repos/              # Actual DB operations
│   │   │       └── __init__.py
│   │   │       └── budget.py       
│   │   ├── models/
│   │   │   └── user.py             # Python class of DB table models
│   │   ├── utils/
│   │       └── serialize.py        # Commonly used operations. 
│   │
│   └── layers/                     # Lambda layers
│       └── python/                     
│       |    └── pandas/
│       |    └── requests/
│       └── requirements.txt
|
├── tests/
│   ├── unit/
│   │   ├── functions/
│   │   │   ├── test_create_user.py
│   │   │   └── test_get_user.py
│   │   └── shared/
│   │       └── test_db_client.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   ├── fixtures/
│   │   └── sample_events/          # sample Lambda event JSONs
│   │       ├── api_gateway_post.json
│   │       └── sqs_event.json
│   └── conftest.py                 # pytest fixtures (mocks, env setup)
|
├── scripts/
│   ├── invoke_local.sh             # invoke a function locally with a sample event
│   ├── run_tests.sh
│   └── build.sh                    # zip/package functions for deploy
|
|
├── fe/                             # your Angular lives here
├── infra/                          # your terraform lives here
├── .env.example
├── requirements-dev.txt            # pytest, moto, boto3, etc.
└── README.md
```
## be/src/
### be/src/functions
- need a *handler.py* file for the actual lambda
- Keep these functions light! ***most of the code should live in shared***. (per Claude) Why? Bc it causes issues doen the line:
    1. *Testing*: Every test has to construct a fake Lambda event/context just to exercise the flow properly.
    2. *Code Reusability*: The same underlying logic often needs to run from more than one entry point
    3. *Lmbda Evants Are Annoying*: Lambda events are messy and can change, especially when comming from different places.
- Vanilla python code for *handler.py*:
```python
import json

def handler(event = None, context = None):
    # TODO

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Hello, World!"}),
    }

if __name__ == "__main__":
    print(handler())
```
- All *handler.py* files must have an entry function called handler
- Give each function its own folder
- Optionally include an *shared-manifest.txt* to inform what from the shared folder is used.
    - Unless using all
- Prev added a *requirements.txt*, I dont remember how that works on the AWS side bc it would need layers.

### be/src/shared/
- typically includes *db/*, *models/*, *utils/*
- How to deploy this varies:
    1. Add it to lambda layers 
    2. Zip the entire file in with the lambda code.
    3. Zip SPECIFIC parts of the shared folder in with the lambda.
- Pros and Cons: 

| Approach | Pros | Cons |
|---|---|---|
| **1. Lambda Layers** | Deploy shared code once, reuse across functions; smaller per-function packages; faster deploys when only one function changes | Layer versioning must be manually bumped per function; risk of drift/stale code; 5-layer limit per function; adds debugging indirection |
| **2. Zip entire shared folder into each function** | Simple, no extra AWS resource to manage; each package is self-contained/immutable; no version mismatch risk; easiest local testing | Duplicated code across every zip; larger packages if shared folder grows large |
| **3. Zip only specific parts of shared folder** | Minimal package size; explicit, reviewable dependencies per function; avoids bundling unused code | Requires manual tracking (manifest file) or bundler tooling; more build script complexity; easy to forget updating manifest when code changes |

#### ...db/
- client.py --> sets up a connection to dynamoDB
- tables.py --> pull table neams  from env vars
- exceptions.py --> custom DB exception types
- repos/ --> python files that are the actual data access layers. 
    - From Claude:
```
This is the important part. Wrap DynamoDB's API (which is verbose and easy to get wrong — Key, Attr, condition expressions) behind plain functions so your handlers never touch boto3 directly
```
- repos can have multiple python files.
- *db/* has its own **__init__.py** and does *repos/*
    - This makes them importable packages so importing is reliable and explicit. 
- Testing: moto mocks dynamodb once, then can test *repos/* functions directly
#### ...models/
- python classes that represent the structure of the dynamo tables
- **Keep seperate from the dynamoDB**
- Will also have multiple python files. 
- Example:
```python
from dataclasses import dataclass, asdict

@dataclass
class User:
    user_id: str
    name: str
    email: str
    status: str = "active"

    def dict(self):
        return asdict(self)
```
#### ...utils/
- various functions that would be helpful, like data transformation stuff

### be/src/layers/
- This will have the dependencies
- must be zipped on deployment
- potentiall bundle shared folder in here. 
    - layers are versioned, different functions could accidently be running on old layer and thus old shared code
    - limits on layer size. 
    - easy to just "throw" the shared folder in here (the lambda layer) and slap it on those bad boys (the lambda functions).
- have a requirements.txt ***BUT there is an expected folder struct*** .
- either  python/pandas/ *or* python/lib/python3.12/pandas/
    - pandas can be any package and can have multiple at once
    - python3.12 must match the EXACT runtime
- the top-level folder in the zip must be named python
- you need to pip istall the package locally in the folder
- Command to install locally: 
```bash
pip install -r requirements.txt -t layer_build/python
```
--or-- 
```bash
pip install pandas -t layer_build/python
```
- BETTER COMMAND:
    - *--platform manylinux2014_x86_64* --> forces Linux x86_64 wheels (use manylinux2014_aarch64 for Graviton/arm64 Lambdas)
    - *--implementation cp* --> CPython (standard Python)
    - *--python-version 3.12* --> must match your Lambda runtime version
    - *--only-binary=:all:* --> refuses to build from source, only pulls prebuilt wheels (avoids needing a C compiler locally, and guarantees the binary matches --platform)

```bash
pip install -r requirements.txt \
  -t layer_build/python \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all:
```
## be/tests/
TODO    