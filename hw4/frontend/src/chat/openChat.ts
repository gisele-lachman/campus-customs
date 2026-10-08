// Lets any page open the floating chat window (e.g. "Ask the Bulldog about this").
export const OPEN_CHAT_EVENT = 'campus-customs:open-chat'

export function openChat() {
  window.dispatchEvent(new Event(OPEN_CHAT_EVENT))
}
