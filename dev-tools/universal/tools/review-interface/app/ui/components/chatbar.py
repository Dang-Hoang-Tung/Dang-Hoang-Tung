from app.ui.html import esc


def render(ai_name):
    name = esc(ai_name)
    return (
        '<div class="chat" id="chat">'
        f'<div class="chat-box" id="chatbox" hidden><div class="chat-log" id="chatlog"></div>'
        f'<div class="chat-wait" id="chatwait" hidden>{name} is replying…</div></div>'
        '<div class="chat-bar" id="chatbar">'
        f'<button type="button" class="chat-toggle" id="chattoggle" aria-expanded="false" aria-controls="chatbox">Chat with {name}</button>'
        f'<textarea id="chatinput" rows="1" placeholder="Ask {name} about this PR…" aria-label="Message {name}"></textarea>'
        '<button type="button" class="primary" id="chatsend">Send</button>'
        '</div></div>'
    )
