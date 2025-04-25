# import os
# import sys

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# from client import BedRockClient, GroqClient
# from tool import wikipedia, code_executor, google
# from agent import Agent
# from agent.chat.streamlit_chat import StreamlitChat
# from client.config import ClientConfig
# from get_error import get_error_message

# from dotenv import load_dotenv

# load_dotenv()

# StreamlitChat.context(
#     {
#         "page_title": "QE Assistant",
#         "page_icon": "🚀",
#         "layout": "wide",
#         "initial_sidebar_state": "auto",
#         "menu_items": {
#             "Get Help": "https://www.extremelycoolapp.com/help",
#             "Report a bug": "https://www.extremelycoolapp.com/bug",
#             "About": "# This is a header. This is an *extremely* cool app!",
#         },
#     }
# )

# if not StreamlitChat.is_init_session():
#     file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "guideline.md")
#     with open(file, "r") as f:
#         instruction = f.read()
#     StreamlitChat.init_session(
#         Agent(
#             client=GroqClient(
#                 ClientConfig(
#                     model="llama3-70b-8192",
#                     temperature=0.2,
#                     api_key=os.getenv("GROQ_API_KEY"),
#                 )
#             ),
#             name="QE Regression Assistant",
#             system=f"""
#             You are the **QE Regression Assistant**, responsible for identifying and asserting error types based on the link to an error message.

#             1. **When provided with a link**:
#               - Use the `get_error_message` function to retrieve error details from the URL.

#             2. **Asserting the error type**:
#               - Based on the component and the provided guidelines, analyze the error message and determine the error type.
#               - The link might contain the information of which component for the error message.
#               - Present the results in a clear and structured markdown table format as shown below:
#               | Error ID   | Error Type       | Assert Reason                     |
#               |------------|------------------|-----------------------------------|

#               The Assert Reason should contains the component like "<component-name>: <reason-message>"
#               You can also add a table title to the markdown table.

#             **Guidelines**

#             {instruction}

#             Try to make your answer clearly and easy to read!

#             """,
#             tools=[get_error_message],
#             chat_console=StreamlitChat("QE Regression Assistant"),
#         )
#     )

# StreamlitChat.input_message()

# # python -m streamlit run qe_assistant.py
