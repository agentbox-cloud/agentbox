<h4 align="left" style="display: flex; align-items: center;">
  <a href="https://pypi.org/project/agentbox-python-sdk/">
    <img alt="Last 1 month downloads for the Python SDK" loading="lazy" width="auto" height="20" decoding="async" 
    style="margin-right: 10px;"
    src="https://img.shields.io/pypi/dm/agentbox-python-sdk?label=PyPI%20Downloads&color=blue">
  </a>
  <a href="https://pypi.org/project/agentbox-python-sdk/">
    <img alt="Python >= 3.9" loading="lazy" width="auto" height="20" decoding="async" 
    style="margin-right: 10px;" 
    src="https://img.shields.io/badge/Python-3.9%2B-yellow">
  </a>
  <a href="https://paas.airacloud.com/">
    <img alt="Powered by AiraCloud" loading="lazy" width="auto" height="20" decoding="async" 
    style="margin-right: 10px;" 
    src="https://img.shields.io/badge/Powered%20by-AiraCloud-teal">
  </a>
  <a href="https://e2b.dev/">
    <img alt="Powered by E2B" loading="lazy" width="auto" height="20" decoding="async" 
    style="margin-right: 10px;" 
    src="https://img.shields.io/badge/Powered%20by-E2B-orange">
  </a>
  <a href="https://www.apache.org/licenses/LICENSE-2.0">
    <img alt="Apache License 2.0" loading="lazy" width="auto" height="20" decoding="async" 
    style="margin-right: 10px;" 
    src="https://img.shields.io/badge/License-Apache%202.0-lightgrey">
  </a>
</h4>

# AgentBox

[AgentBox](https://agentbox.cloud) AI sandboxes tools for enterprise-grade agents. Build, deploy, and scale with confidence.

It is **powered by [AiraCloud](https://paas.airacloud.com/)** and **[E2B](https://e2b.dev/)**, leveraging their robust infrastructure and advanced cloud capabilities to deliver a seamless, high-performance experience.


## Run your first AgentBox Job

### 1. Install [agentbox-python-sdk](https://pypi.org/project/agentbox-python-sdk/)

```bash
pip install agentbox-python-sdk
```

### 2. Setup your AgentBox API key

1. Sign up to [AgentBox](https://agentbox.cloud)
2. Manager your [API key](https://agentbox.cloud/home/api-keys)
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

Visit [AgentBox Documents](https://agentbox.cloud/docs)

## Contact us

For inquiries or support, feel free to reach out to us at:

[agentbox@mail.agentbox.cloud](mailto:agentbox@mail.agentbox.cloud)

