import streamlit as st
import os
import asyncio
from agents import Agent, Runner, WebSearchTool, FileSearchTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Ensure your OpenAI key is available from .env file
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
vector_store_id = os.environ["vector_store_id"]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = True
if "use_file_search" not in st.session_state:
    st.session_state.use_file_search = True
if "conversation_active" not in st.session_state:
    st.session_state.conversation_active = True

# Function to create agent with selected tools
def create_research_assistant():
    tools = []
    if st.session_state.use_web_search:
        tools.append(WebSearchTool())
    if st.session_state.use_file_search:
        tools.append(FileSearchTool(
            max_num_results=3,
            vector_store_ids=[vector_store_id],
        ))
    return Agent(
        name="Research Assistant",
        instructions="""You are a world class lawyer, capable of reasoning, finding weaknesses in briefs, using the legal documents that support your arguments and accessing files on Google Drive.  
        When you summarize documents such as briefs do so in clear and accurate language.  When you provide output that identifies weaknesses in the brief’s legal arguments be logical.  Cite case references. 
        You also are skilled in researching anything related to the law using resources at your disposal.  However, never ever suggest or use incorrect or unverifiable resources and case law.  Only access files that are publicly available or authorized for use.""",
        tools=tools,
    )

# Async wrapper for agent
async def get_research_response(question, history):
    agent = create_research_assistant()
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    prompt = f"Context of our conversation:\n{context}\n\nCurrent question: {question}"
    result = await Runner.run(agent, prompt)
    return result.final_output

# Streamlit UI
st.set_page_config(page_title="Research Assistant", layout="wide")
st.title("🔍 Research Assistant")
st.write("Ask me anything, and I'll search for information to help answer your questions.")

# Sidebar controls
st.sidebar.title("Search Settings")
st.sidebar.subheader("Select Search Sources")
web_search = st.sidebar.checkbox("Web Search", value=st.session_state.use_web_search, key="web_search_toggle")
file_search = st.sidebar.checkbox("Vector Store Search", value=st.session_state.use_file_search, key="file_search_toggle")

# Update search tool preferences
st.session_state.use_web_search = web_search
st.session_state.use_file_search = file_search

# Warn if no tools are selected
if not st.session_state.use_web_search and not st.session_state.use_file_search:
    st.sidebar.warning("Please select at least one search source")

# Sidebar conversation controls
st.sidebar.subheader("Conversation")

# Reserve spot for Save Conversation button at top
save_button_placeholder = st.sidebar.empty()

# Clear conversation button
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.experimental_rerun()

# End conversation button
if st.sidebar.button("End Conversation"):
    st.session_state.conversation_active = False
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Conversation ended. Leave the window open to restart it anytime. Otherwise you may close the browser window."
    })
    st.rerun()

# Example questions
with st.sidebar.expander("Example Questions"):
    st.markdown("""
    - What are the key findings in my vector store documents?
    - Find the latest research on AI Agents.
    - What are the best recipes for making cake.
    - Summarize the information about "TOPIC" from my documents.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🐙 Made by the Lonely Octopus Team with modifications by L.Mantese")

# Format messages to HTML
def format_messages_as_html(messages):
    html = """
    <html><head><style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    .user { color: blue; margin-bottom: 10px; }
    .assistant { color: green; margin-bottom: 20px; }
    .message { border-bottom: 1px solid #ddd; padding-bottom: 10px; }
    </style></head><body>
    <h2>Conversation Transcript</h2>
    """
    for msg in messages:
        role_class = "user" if msg["role"] == "user" else "assistant"
        content = msg["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        html += f'<div class="message {role_class}"><strong>{msg["role"].capitalize()}:</strong><br>{content}</div>'
    html += "</body></html>"
    return html

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_question = st.chat_input("Ask your research question")
if user_question:
    if not st.session_state.use_web_search and not st.session_state.use_file_search:
        st.error("Please select at least one search source in the sidebar")
    else:
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)
        with st.chat_message("assistant"):
            with st.spinner("Researching..."):
                response_placeholder = st.empty()
                response = asyncio.run(get_research_response(user_question, st.session_state.messages))
                response_placeholder.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ✅ NOW render the "Save Conversation" button using up-to-date messages
html_data = format_messages_as_html(st.session_state.messages)
save_button_placeholder.download_button(
    label="Save Conversation",
    data=html_data,
    file_name="conversation.html",
    mime="text/html",
)