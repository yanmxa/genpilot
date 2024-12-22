import streamlit as st
import json

# Define the messages as dictionaries
messages = [
    {"role": "user", "content": "When was Chinese Academy of Sciences founded?"},
    {
        "role": "assistant",
        "name": "Assistant AI",
        "tool_calls": [
            {
                "id": "call_qtg9",
                "function": {
                    "name": "google",
                    "arguments": '{"keyword":"history of Chinese Academy of Sciences"}',
                },
                "type": "function",
            }
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "call_qtg9",
        "content": (
            "No description available\n\nTitle: Founding - Chinese Academy of Sciences\nSnippet: CAS was established on November 1, 1949, in Beijing, "
            "where it is headquartered. It was formed from several existing scientific institutes and soon welcomed ..."
        ),
    },
    {
        "role": "assistant",
        "name": "Assistant AI",
        "content": (
            "It seems like the tool has provided a wealth of information about the history of the Chinese Academy of Sciences. "
            "Based on the results, it appears that the Chinese Academy of Sciences was founded on November 1, 1949, in Beijing, China."
        ),
    },
]


# Define a function to render each message
def render_message(message):
    if message["role"] == "user":
        st.markdown(
            f"""
            <div style="
                border: 1px solid #0078D7; 
                padding: 15px; 
                border-radius: 10px; 
                background-color: #E3F2FD; 
                margin-bottom: 15px;">
                <strong>User:</strong>
                <p style="margin: 0;">{message['content']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif message["role"] == "assistant":
        if "content" in message:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #4CAF50; 
                    padding: 15px; 
                    border-radius: 10px; 
                    background-color: #E8F5E9; 
                    margin-bottom: 15px;">
                    <strong>{message.get('name', 'Assistant')}:</strong>
                    <p style="margin: 0;">{message['content']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                st.markdown(
                    f"""
                    <div style="
                        padding: 10px; 
                        border-radius: 5px; 
                        background-color: #FFF9C4; 
                        margin-bottom: 10px;">
                        <strong>🔧 Tool:</strong> {tool_name}<br>
                        <strong>📄 Args:</strong> {tool_args['keyword']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    elif message["role"] == "tool":
        with st.expander(
            f"🛠️ Tool Response (ID: {message['tool_call_id']})", expanded=False
        ):
            st.markdown(
                f"""
                <div style="
                    padding: 15px; 
                    border-radius: 8px; 
                    background-color: #FFF3E0; 
                    white-space: pre-wrap;">
                    {message['content']}
                </div>
                """,
                unsafe_allow_html=True,
            )


# Streamlit UI
st.title("Enhanced Chat Interaction UI")

# Render messages
for msg in messages:
    render_message(msg)
