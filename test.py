from rich.console import Console
from rich.text import Text
from datetime import datetime

console = Console()


# Function to create a beautiful chat-like message
def chat_message(user, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    user_color = "cyan" if user == "User1" else "green"

    # Add a background color and borders for the message bubble
    user_text = Text(user, style=f"bold {user_color}")
    timestamp_text = Text(f"[{timestamp}]", style="dim")
    message_text = Text(message, style="bold white")

    # Use a message bubble effect
    message_bubble = f"[bold {user_color}]{user}[/]: [dim]({timestamp})[/]  {message}"

    console.print(f"🗨️  {message_bubble}", justify="left")


# Simulate chat
chat_message("User1", "Hello, how are you?")
chat_message("User2", "I'm doing well, thanks! How about you?")
chat_message("User1", "I'm good, just working on some projects!")
