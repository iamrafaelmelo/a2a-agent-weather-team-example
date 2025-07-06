# A2A: Agent Weather Team Example

Agent weather team example powered by A2A Google SDK.

> If you want use voice, dont't forget to change `MODEL` constant for a model that supports
> voice input, e.g `gemini-2.0-flash-live-001`.
> See more in https://ai.google.dev/gemini-api/docs/models#gemini-2.0-flash

## Requirements

- Python 3
- Google Account (To get gemini free api key)

## Get started

**1. Create a root folder**

```sh
mkdir myagents
```

**2. Clone this repository in root folder**

```sh
# via https
git clone https://github.com/iamrafaelmelo/a2a-agent-weather-team-example.git
# or via ssh
git@github.com:iamrafaelmelo/a2a-agent-weather-team-example.git
```

**4. Change API key on .env file**

```text
GOOGLE_API_KEY=your_api_key_here
```

**3. Running and testing**

```sh
adk web # in root folder
```

Once access [http://127.0.0.1:8000](http://127.0.0.1:8000), you ca see the web interface of ADK.

## Known issues

- Even though the prompt contains words blocked by guardrails, the transfer to another agent was carried out.
- This implementation does not have [session 4 of the official tutorial's memory session](https://google.github.io/adk-docs/tutorials/agent-team/#step-4-adding-memory-and-personalization-with-session-state), which causes bugs and makes things worse.

## Links

- [Google A2A Docs](https://google.github.io/adk-docs)
- [Google A2A Quickstart](https://google.github.io/adk-docs/get-started/quickstart)
- [Agent Weather Team Tutorial](https://google.github.io/adk-docs/tutorials/agent-team)
- [Agent Weather Team Without Colab](https://github.com/google/adk-docs/tree/main/examples/python/tutorial/agent_team/adk-tutorial)

## License

This example project is under MIT License, take it and enjoy!

<sup><sub>Sincerely, I prefer create internal modules (packages) in C Language than in Python.</sub></sup>
