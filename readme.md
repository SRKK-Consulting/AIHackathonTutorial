# Azure AI Foundry Agent Walkthrough

This tutorial provides a step-by-step guide to using Azure AI Foundry Agent Service, including how to provision a model, use AI Search as a knowledge base, attach Code Interpreter, and implement advanced tools like Function Calling and Code Interpreter. The tutorial assumes you have an Azure subscription and basic familiarity with Python and Azure CLI.

## Prerequisites

- **Azure Subscription**: Create a free account if you don't have one [here](https://azure.microsoft.com/free/).
- **Azure CLI**: Installed and configured. Sign in using `az login`.
- **Azure AI Foundry Project**: Set up in the Azure AI Foundry portal at [https://ai.azure.com](https://ai.azure.com).
- **Permissions**: Ensure you have the Azure AI Account Owner, Contributor, or Cognitive Services Contributor role at the subscription level.
- **Python Environment**: Python 3.8+ with required libraries (`azure-ai-projects`, `azure-identity`).
- **Environment Variables**: Set `PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`, and `API_VERSION` (e.g., `2025-05-15-preview` for preview features).

## 1. Provisioning a Model in Azure AI Foundry

To use Azure AI Foundry Agent Service, you must deploy a compatible model (e.g., GPT-4o, Llama, Mistral) to your Azure AI Foundry project.

### Steps to Provision a Model

1. **Navigate to Azure AI Foundry Portal**:
   - Go to [https://ai.azure.com](https://ai.azure.com) and sign in.
   - Select your project or create a new one by clicking **Create an agent** or **+ Create project**.

2. **Deploy a Model**:
   - From **My assets**, select **Models + endpoints** > **Deploy Model** > **Deploy Base Model**.
   - Choose a model (e.g., `gpt-4o`).
   - Configure deployment settings:
     - **Deployment Type**: Select **Global Standard**.
     - **Model Version**: Choose the latest (e.g., `2024-08-06`).
     - **Tokens Per Minute Rate Limit**: Set to at least 140k for optimal performance.
   - Click **Deploy** and wait for the deployment to complete.

3. **Retrieve Project Endpoint**:
   - Go to the project **Overview** page.
   - Under **Endpoints and keys** > **Libraries** > **Azure AI Foundry**, copy the project endpoint.
   - Set it as an environment variable:
     ```bash
     export PROJECT_ENDPOINT="https://<your_ai_service_name>.services.ai.azure.com/api/projects/<your_project_name>"
     ```

4. **Verify Model Deployment**:
   - Ensure the model deployment name (e.g., `gpt-4o`) is noted, as it will be used in agent creation.

**Note**: Check model availability and regional support in the [Azure AI Foundry Models documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/models).

## 2. Using AI Search as a Knowledge Base

Azure AI Search can be integrated as a knowledge base to enable Retrieval Augmented Generation (RAG) for agents, allowing them to retrieve and utilize internal documents or data.

### Steps to Set Up AI Search

1. **Create an Azure AI Search Resource**:
   - In the Azure portal, create a new Azure AI Search resource.
   - Configure the resource with a unique name and select a pricing tier (e.g., Basic or Standard).
   - Note the endpoint and API key.

2. **Index Data**:
   - Upload documents or data to the Azure AI Search service.
   - Create an index with fields relevant to your use case (e.g., document content, metadata).
   - Refer to the [Azure AI Search documentation](https://learn.microsoft.com/en-us/azure/search/) for indexing details.

3. **Connect AI Search to Azure AI Foundry**:
   - In the Azure AI Foundry portal, navigate to your project.
   - Add the Azure AI Search tool:
     - Go to **Agents** > **Setup** > **Add Tool**.
     - Select **Azure AI Search** and provide the endpoint and API key.
   - Alternatively, configure programmatically (see Section 4).

4. **Test the Integration**:
   - Send a query to the agent (e.g., "Find documents about project X") to verify that the agent retrieves relevant data from the Azure AI Search index.

## 3. Using Azure AI Foundry Agent Service

The Azure AI Foundry Agent Service allows you to create AI agents with tools like Code Interpreter and AI Search. Below is a Python example to create an agent with both tools attached.

## 4. Steps to use Azure AI Foundry Agent Service FAST API backend

Step 1: 
Run below script to activate the fastAPI (backend) 
```bash
python f_ag.py
```

Step 2: 
```python
run req.py to send a request to the fastAPI backend
```

## Recommendations: 
For deployment, this can be hosted on azure container apps/Azure kubenetes service.

## 5. Steps to use Agentic Workflow custom application, powered by Langgraph. 
Step 1: 
Update the parameters required to instantiate the LLM. 

Step 2: 
```python
Run python app.py
```

## Recommendations: 
To be deployed on Azure App Service. Please Refer to the documentation below. 


### Python Code to Create an Agent with Code Interpreter and AI Search

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool, AzureAISearchTool

# Set environment variables
project_endpoint = os.environ["PROJECT_ENDPOINT"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]

# Initialize AIProjectClient
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
    api_version="2025-05-15-preview"
)

# Create tools
code_interpreter = CodeInterpreterTool()
ai_search = AzureAISearchTool(
    search_endpoint=os.environ["AZURE_AI_SEARCH_ENDPOINT"],
    api_key=os.environ["AZURE_AI_SEARCH_API_KEY"],
    index_name="my-index"
)

# Create agent with tools
with project_client:
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="my-agent",
        instructions="You are a helpful agent that can execute code and search documents.",
        tools=[code_interpreter.definitions, ai_search.definitions]
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Send a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="Analyze sales data and search for related documents."
    )
    print(f"Created message, ID: {message['id']}")

    # Process the agent run
    run = project_client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id
    )
    print(f"Run completed with status: {run.status}")

    # Fetch and log messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message.role}, Content: {message.content}")

    # Clean up
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")
```

### Explanation

- **Environment Variables**: Ensure `PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`, `AZURE_AI_SEARCH_ENDPOINT`, and `AZURE_AI_SEARCH_API_KEY` are set.
- **Tools**: The `CodeInterpreterTool` enables Python code execution in a sandboxed environment, while `AzureAISearchTool` connects to an Azure AI Search index.
- **Agent Creation**: The agent is configured with instructions and tools to handle both code execution and document retrieval.
- **Thread and Messages**: A thread is created for conversation, and messages are sent to trigger agent actions.

**Note**: Replace placeholders like `my-index` with your actual Azure AI Search index name.

## 4. Advanced Agent Tools: Function Calling

Function Calling allows agents to invoke custom functions based on user queries, enhancing their ability to interact with external systems.

### Steps to Implement Function Calling

1. **Define a Function**:
   - Create a function with a docstring describing its parameters and return value.
   - Example: A function to fetch weather data.

2. **Integrate with Agent**:
   - Use `FunctionTool` to register the function with the agent.

### Python Code for Function Calling

```python
import json
import os
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool

# Define a custom function
def fetch_weather(location: str) -> str:
    """Fetches the weather information for the specified location.
    :param location: The location to fetch weather for.
    :return: Weather information as a JSON string.
    """
    mock_weather_data = {
        "New York": "Sunny, 25°C",
        "London": "Cloudy, 18°C",
        "Tokyo": "Rainy, 22°C"
    }
    weather = mock_weather_data.get(location, "Weather data not available.")
    return json.dumps({"weather": weather})

# Initialize AIProjectClient
project_endpoint = os.environ["PROJECT_ENDPOINT"]
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
    api_version="2025-05-15-preview"
)

# Create FunctionTool
user_functions = {fetch_weather}
functions = FunctionTool(functions=user_functions)

# Create agent with function calling
with project_client:
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="weather-agent",
        instructions="You are a weather bot that provides weather information.",
        tools=functions.definitions
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Send a message
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="What is the weather in New York?"
    )
    print(f"Created message, ID: {message['id']}")

    # Process the run
    run = project_client.agents.runs.create(
        thread_id=thread.id,
        agent_id=agent.id
    )
    print(f"Created run, ID: {run.id}")

    # Poll run status
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for tool_call in tool_calls:
                if tool_call.name == "fetch_weather":
                    output = fetch_weather("New York")
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
            project_client.agents.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
    print(f"Run completed with status: {run.status}")

    # Fetch and log messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message['role']}, Content: {message['content']}")

    # Clean up
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")
```

### Explanation

- **Function Definition**: The `fetch_weather` function is defined with a docstring that the agent uses to understand its purpose and parameters.
- **FunctionTool**: Registers the function with the agent, enabling it to be called based on user queries.
- **Run Polling**: The code polls the run status to handle tool calls, submitting outputs when required.

**Source**: Adapted from [Microsoft Learn: Function Calling](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/function-calling?tabs=python&pivots=python).

## 5. Advanced Agent Tools: Code Interpreter

The Code Interpreter allows agents to write and execute Python code in a secure sandbox environment, useful for tasks like data analysis and chart generation.

### Steps to Use Code Interpreter

1. **Enable Code Interpreter**:
   - Add the `CodeInterpreterTool` to the agent programmatically or via the Azure AI Foundry portal.
   - Optionally, upload files for the agent to process.

2. **Test with a Query**:
   - Send a query that requires code execution (e.g., "Create a pie chart of sales data").

### Python Code for Code Interpreter

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool

# Initialize AIProjectClient
project_endpoint = os.environ["PROJECT_ENDPOINT"]
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
    api_version="2025-05-15-preview"
)

# Create Code Interpreter tool
code_interpreter = CodeInterpreterTool()

# Create agent with Code Interpreter
with project_client:
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="data-analysis-agent",
        instructions="You are an AI assistant that can analyze data and generate charts.",
        tools=[code_interpreter.definitions]
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Send a message
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="Create a pie chart of sales data: Region A: 500, Region B: 300, Region C: 200."
    )
    print(f"Created message, ID: {message['id']}")

    # Process the run
    run = project_client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id
    )
    print(f"Run completed with status: {run.status}")

    # Fetch and log messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message.role}, Content: {message.content}")

    # Clean up
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")
```

### Explanation

- **CodeInterpreterTool**: Enables the agent to generate and execute Python code for tasks like chart creation.
- **Query Example**: The agent processes the query to generate a pie chart using libraries like Matplotlib in a sandboxed environment.
- **Output**: The agent may save generated files (e.g., charts as PNGs) to a specified directory.

**Source**: Adapted from [Microsoft Learn: Code Interpreter Samples](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/code-interpreter-samples?pivots=python).

## 6. Best Practices

- **Security**:
  - Never commit sensitive data (e.g., `.env` files) to version control. Add `.env` to `.gitignore`.
  - Use Azure Default Credentials for secure authentication.
  - Implement role-based access control (RBAC) and network isolation.

- **Performance**:
  - Use the latest API version (`2025-05-15-preview`) for access to preview features.
  - Monitor token usage, as Code Interpreter incurs additional charges beyond standard token fees.

- **Debugging**:
  - Enable tracing in Azure Monitor to log agent performance and tool calls.
  - Request the agent to display generated code for Code Interpreter debugging.

- **Cleanup**:
  - Delete agents and threads after use to avoid unnecessary costs.
  - Use `azd down --purge` to remove resources if no longer needed.

## 7. Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Azure AI Foundry Agent Service Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview)
- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [GitHub: Azure AI Foundry Samples](https://github.com/Azure-Samples/get-started-with-ai-agents)
- [Azure App Service Documentation Guide](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python?tabs=fastapi%2Cwindows%2Cazure-cli%2Cazure-cli-deploy%2Cdeploy-instructions-azportal%2Cterminal-bash%2Cdeploy-instructions-zip-azcli)