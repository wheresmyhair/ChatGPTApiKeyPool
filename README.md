# OpenAIApiKeyPool
## Motivation
It seems that openai will force user to wait 20 seconds when one tries to post requests multiple times using the same key in a short period of time. This key pool function is designed with a cool down pool to avoid the "overheating" problem. See utils.py for more details.