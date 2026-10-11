"""AWS Lambda handler for the ``create_user`` function.

Invoked by API Gateway for ``POST /users``.
"""
import json

from shared.db.repos.user import create_user


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event=None, context=None):
    """Create a user from an API Gateway proxy event."""
    try:
        raw_body = event.get("body") if event else None
        if raw_body is None:
            return _response(400, {"error": "Missing request body"})

        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            body = raw_body

        if not isinstance(body, dict):
            return _response(400, {"error": "Request body must be a JSON object"})

        name = body.get("name")
        email = body.get("email")

        if not name or not email:
            return _response(400, {"error": "Missing required field(s): name, email"})

        user = create_user(name=name, email=email)
        return _response(201, user.dict())
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})
    except Exception as exc:  # pragma: no cover - last-resort guard
        return _response(500, {"error": str(exc)})


if __name__ == "__main__":  # pragma: no cover
    print(handler())