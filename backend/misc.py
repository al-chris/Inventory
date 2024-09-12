import os
from langchain.agents import Tool, AgentExecutor, create_react_agent, create_tool_calling_agent
from langchain.prompts import StringPromptTemplate
from langchain.document_loaders import PyPDFLoader
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.schema import AgentAction, AgentFinish
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from typing import List, Union, Dict
import re
import google.generativeai as genai

# Set up your Google API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBx6_HFmP8XX5x49Gx5kWq_elUUItWLtv8"

# Initialize the search tool
search = DuckDuckGoSearchRun()

# Define the custom prompt template
class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"Action: {action.tool}\nAction Input: {action.tool_input}\nObservation: {observation}\nThought: I now know the result of using {action.tool}.\n"
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        return self.template.format(**kwargs)

# Define the prompt template
template = """
You are an AI assistant tasked with analyzing RFQ emails and finding potential suppliers for the requested items.

Your goal is to systematically work through each item in the RFQ and find websites or suppliers who sell those items at cost-effective prices, with a focus on wholesale suppliers ideally located in Nigeria. 
You will carefully reason through each item, and for each item, you'll execute the following steps:

1. **Extract the relevant details of the item** from the RFQ, such as product type, brand, specifications, quantity, and packaging information.
2. **Think about the technical specifications** or any special industry-related terms that might help refine the search.
3. **Generate a search query** using specific terms, including product descriptions, location, and supplier types.
4. **Search for potential suppliers** using the search tool and analyze the results.
5. **Evaluate the credibility of the supplier**: Consider whether they offer wholesale pricing, whether the supplier is based in or ships to Nigeria, and whether the products align with the RFQ.
6. **Return the links to relevant suppliers** for each item, and if possible, include multiple sources for comparison.

Given the following email, extract each item and its description, then use the search tool to find websites that are likely to have each item.

Email:
{email}

Tools:
{tools}

Use the following format for your reasoning and actions:

Thought: I have received the RFQ. I will start by identifying the first item and its specifications.
Action: Extract the first item
Observation: {Extracted Item Details}

Thought: I will now generate a detailed search query to find suppliers for the first item.
Action: Perform a search for suppliers of {Item Name} with the following query: "{Search Query}"
Observation: {Search Results}

Thought: I will evaluate the results based on the item specifications and supplier credibility.
Action: Record links to relevant suppliers
Observation: {Supplier Links}

Repeat this process for each item in the RFQ.

Final Answer: A list of items from the RFQ, each with its list of links to relevant suppliers.

{agent_scratchpad}
"""

# Define the tools
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="Useful for finding websites that might supply specific items"
    )
]

# Set up the prompt template
prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    input_variables=["tools", "tool_names", "email", "agent_scratchpad"]
)

# Define the output parser
def output_parser(llm_output: str) -> Union[AgentAction, AgentFinish]:
    if isinstance(llm_output, list):
        llm_output = ''.join([str(chunk) for chunk in llm_output])
    elif not isinstance(llm_output, str):
        llm_output = str(llm_output)

    if "Final Answer:" in llm_output:
        return AgentFinish(
            return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
            log=llm_output,
        )
    
    regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
    match = re.search(regex, llm_output, re.DOTALL)
    if not match:
        return AgentFinish(
            return_values={"output": "I couldn't determine which action to take. Please provide more information."},
            log=llm_output,
        )
    action = match.group(1).strip()
    action_input = match.group(2)
    return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

# Set up the Gemini model
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
gemini = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

# Create the LLM chain
# llm_chain = LLMChain(llm=gemini, prompt=prompt)
llm_chain = prompt | gemini

# Set up the agent
agent = create_tool_calling_agent(
    llm=gemini,
    tools=tools,
    prompt=prompt
)

# Create the agent executor
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

# Function to process the RFQ email
def get_supplier_info(email_content: str) -> Dict[str, List[str]]:
    # result = agent_executor.run(email=email_content)
    tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    tool_names = ", ".join([tool.name for tool in tools])
    result = agent_executor.invoke({
        "email": email_content,
        "tools": tool_strings,
        "tool_names": tool_names,
        "agent_scratchpad": ""
    })
    return result
    # Parse the result and return a dictionary of items and their potential supplier websites

def parse_supplier_info(result):
    # Get the 'output' field from the input dictionary
    output = result.get('output', '')
    print(f"Output content: {output}")  # Debug print

    # Find the Final Answer section
    match = re.search(r'Final Answer:\s*(.*?)(?:\n\n|$)', output, re.DOTALL)
    if not match:
        print("No 'Final Answer:' section found")  # Debug print
        return None

    final_answer = match.group(1).strip()
    print(f"Final Answer content: \n {final_answer}")  # Debug print
    return(f"""Final Answer content: \n {final_answer}""")

# Example usage
if __name__ == "__main__":
    rfq_email = """
    Subject: Request for Quotation - Office Supplies

    Dear Supplier,

    We are looking for quotations for the following items:

    1. Ergonomic Office Chair - High-back, adjustable armrests, lumbar support
    2. LED Desk Lamp - Adjustable brightness, color temperature control
    3. Wireless Keyboard and Mouse Combo - Quiet keys, long battery life
    4. 27-inch 4K Monitor - IPS panel, HDMI and DisplayPort inputs

    Please provide your best price and delivery time for each item.

    Thank you,
    Procurement Team
    """

    rfq_email2 = """
    # Request for Quotation (RFQ)

    ## 1. Company Information
    **Requesting Company:** TechInnovate Solutions
    **Contact Person:** Alex Johnson
    **Email:** alex.johnson@techinnovate.com
    **Phone:** (555) 123-4567

    ## 2. RFQ Details
    **RFQ Number:** ENG-2024-001
    **Date Issued:** September 6, 2024
    **Submission Deadline:** September 20, 2024, 5:00 PM EST

    ## 3. Items Requested

    ### 3.1 High-Precision Linear Actuators
    - Quantity: 50 units
    - Specifications:
    - Stroke Length: 100mm ± 0.01mm
    - Force Output: Minimum 500N
    - Operating Speed: 10mm/s to 50mm/s (adjustable)
    - Positioning Accuracy: ±0.005mm
    - Input Voltage: 24V DC
    - Duty Cycle: Minimum 80% at full load
    - Environmental Protection: IP65 or better
    - Operating Temperature Range: -10°C to 60°C

    ### 3.2 Industrial-Grade Pressure Sensors
    - Quantity: 200 units
    - Specifications:
    - Pressure Range: 0-100 bar
    - Accuracy: ±0.25% of full scale
    - Output Signal: 4-20 mA
    - Process Connection: 1/4" NPT
    - Material: 316L Stainless Steel
    - Operating Temperature: -40°C to 85°C
    - Shock Resistance: 100g, 11ms
    - Vibration Resistance: 20g, 10-2000 Hz

    ### 3.3 Programmable Logic Controllers (PLCs)
    - Quantity: 20 units
    - Specifications:
    - CPU: Dual-core processor, minimum 1 GHz
    - Memory: 4 GB RAM, 16 GB internal storage
    - I/O Capacity: Minimum 256 digital I/O points, 64 analog I/O points
    - Communication Protocols: EtherNet/IP, Modbus TCP, PROFINET
    - Programming Languages: Ladder Logic, Function Block, Structured Text
    - Power Supply: 24V DC
    - Operating Temperature: 0°C to 55°C
    - Certifications: CE, UL

    ## 4. Additional Requirements
    - All items must be new and unused
    - Items must comply with relevant ISO and IEC standards
    - Provide detailed technical datasheets for each item
    - Include warranty information and terms
    - Specify lead time for delivery
    - Provide pricing for different quantity brackets (if applicable)

    ## 5. Evaluation Criteria
    - Technical compliance with specifications (40%)
    - Price (30%)
    - Delivery timeline (15%)
    - Warranty and after-sales support (10%)
    - Company reputation and experience (5%)

    ## 6. Submission Instructions
    Please submit your quotation via email to procurement@techinnovate.com with the subject line "RFQ Response: ENG-2024-001" by the submission deadline.

    ## 7. Terms and Conditions
    - TechInnovate Solutions reserves the right to accept or reject any quotation
    - Partial quotations are acceptable, but preference may be given to suppliers who can provide all requested items
    - All prices should be quoted in USD and remain valid for 60 days from the submission date
    - Payment terms: Net 30 days after delivery and acceptance of goods

    For any questions or clarifications regarding this RFQ, please contact Alex Johnson at alex.johnson@techinnovate.com.
    """
    
    print(os.getcwd())
    loader = PyPDFLoader(os.getcwd() + "/backend/sample.pdf")
    doc = loader.load()
    result = get_supplier_info(doc)
    print(result)
    print(parse_supplier_info(result))