# AgentBox

[AgentBox](https://agentbox.space) AI sandboxes tools for enterprise-grade agents. Build, deploy, and scale with confidence.

## Run your first AgentBox Job

### 1. Install [agentbox-python-sdk](https://pypi.org/project/agentbox-python-sdk/)

```bash
pip install agentbox-python-sdk
```

### 2. Setup your AgentBox API key

1. Sign up to [AgentBox](https://agentbox.space)
2. Manager your [API key](https://agentbox.space/home/api-keys)
3. Create API key, and set environment variable with your API key

```
export AGENTBOX_API_KEY=ab_******
```

### 3. Execute code with AgentBox Job

```python
from agentbox import Sandbox

sbx = Sandbox(api_key="ab_******",
              template="template_id",
              timeout=120)
sbx.commands.run(cmd="ls /")
```

### 4. Documents

Visit [AgentBox Documents](https://agentbox.space/docs)
