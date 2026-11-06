from app.ui.html import esc

SEND = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'
CLOSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>'


def render(ai_name):
    name = esc(ai_name)
    return (
        '<div class="chat" id="chat">'
        f'<div class="chat-box" id="chatbox" hidden><div class="chat-grip" id="chatgrip" role="separator" aria-orientation="horizontal" aria-label="Resize chat history" title="Drag to resize"></div>'
        f'<div class="chat-head"><span class="chat-title"><i class="chat-dot"></i>{name}</span>'
        f'<button type="button" class="chat-close" id="chatclose" aria-label="Close chat history" title="Close">{CLOSE}</button></div>'
        '<div class="chat-log" id="chatlog"></div>'
        f'<div class="chat-wait" id="chatwait" hidden><span></span><span></span><span></span>{name} is replying…</div></div>'
        '<div class="chat-bar" id="chatbar">'
        f'<textarea id="chatinput" rows="1" placeholder="Ask {name} about this PR…" aria-label="Message {name}" aria-controls="chatbox"></textarea>'
        f'<button type="button" class="chat-send" id="chatsend" aria-label="Send" title="Send">{SEND}</button>'
        '</div></div>'
    )
