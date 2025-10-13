<h4 align="center">
  <a href="https://pypi.org/project/agentbox-python-sdk/">
    <img alt="Last 1 month downloads for the Python SDK" loading="lazy" width="200" height="20" decoding="async" data-nimg="1"
    style="color:transparent;width:auto;height:100%" src="https://img.shields.io/pypi/dm/agentbox-python-sdk?label=PyPI%20Downloads">
  </a>

  <a href="https://pypi.org/project/agentbox-python-sdk/">
    <img alt="Python Version Support" loading="lazy" width="200" height="20" decoding="async" data-nimg="1"
    style="color:transparent;width:auto;height:100%" src="https://img.shields.io/pypi/pyversions/agentbox-python-sdk?label=Python%20Versions">
  </a>
</h4>

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
export AGENTBOX_API_KEY=ag_******
```

### 3. Execute code with AgentBox Job

```python
from agentbox import Sandbox

sbx = Sandbox(api_key="ag_xxx_xxx_xxx",
              template="tpl_xxx_xxx_xxx",
              timeout=120)
sbx.commands.run(cmd="ls /")
```

### 4. Documents

Visit [AgentBox Documents](https://agentbox.space/docs)

## Contact us

For inquiries or support, feel free to reach out to us at:

[agentbox@mail.agentbox.cloud](mailto:agentbox@mail.agentbox.cloud)

