from openai import OpenAI


def init_session(session: list, directive: str | None, continuous: bool):
    if not continuous:
        session = []
        return session
    session.append({"role": "system", "content": directive})
    return session


def call_llm(client: OpenAI, messages, **kwargs):
    res = client.chat.completions.create(model="gpt-4o", messages=messages, **kwargs)
    return res.choices[0].message


def update_status(status_callback, text: str | None):
    if status_callback is not None and text:
        status_callback(text)
