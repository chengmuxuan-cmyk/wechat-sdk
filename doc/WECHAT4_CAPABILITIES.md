# WeChat 4 Capabilities

This file records the current WeChat 4 implementation status. It is intentionally conservative: a capability is only marked usable after the SDK has a concrete implementation path.

## Usable Now

| Capability | API | WeChat 4 status | Notes |
| --- | --- | --- | --- |
| Detect client | `WeChatClient.auto()` | stable | Detects the WeChat 4 window/profile. |
| Client info | `client.info()` | stable | Returns profile, mode, language, and window metadata. |
| Current chat | `client.current_chat()` | stable | Reads the current chat title through UIA. |
| Session list | `client.get_session_list()` | stable | Reads visible session cells through UIA. |
| Unread sessions | `client.get_unread_sessions()` | partial | Parses numeric unread markers like `[1条]`; muted sessions and plain red dots are ignored. |
| Switch chat tab | `client.switch_to_chat_tab()` | partial | Foreground UI action. Depends on visible tab UIA names. |
| Switch contact tab | `client.switch_to_contact_tab()` | partial | Foreground UI action. Depends on visible tab UIA names. |
| Open chat | `client.chat_with(who)` | partial | Uses WeChat search and keyboard interaction. |
| Send text | `client.send_msg(text, who=...)` | partial | Uses clipboard and keyboard send path. |
| Send file | `client.send_file(path, who=...)` | partial | Uses Windows clipboard `CF_HDROP`. |
| Send image | `client.send_file("image.png", who=...)` | partial | No separate image API yet; image sending reuses file sending. |
| Current visible messages | `client.get_all_message()` | stable | Reads visible message UIA items in the current chat. |
| Next new messages | `client.get_next_new_message()` | stable | Uses UIA runtime ids as the primary de-duplication key. |
| Unread session messages | `client.get_unread_messages()` | partial | Opens unread sessions and returns the latest unread-count messages. |
| Load more messages | `client.load_more_message()` | partial | Scrolls upward in the current chat and returns visible messages after loading. |
| Current-chat history | `client.get_history()` | partial | Scrolls upward and collects UIA message items from the current chat. |
| Listener polling | `MessageListener.poll_once()` | partial | Polls `get_next_new_message()` for the current chat. The first poll builds the baseline. |
| Listener thread | `MessageListener.start()` / `stop()` | partial | Repeated current-chat polling. Not multi-chat monitoring. |
| Contact list | `client.get_all_friends()` | partial | Foreground contact tab UIA traversal. |
| Contact search | `client.search_contact(keyword)` | partial | Foreground contact search. |
| Contact details | `client.get_friend_details()` | partial | Reads visible profile UIA fields. |
| New-friend requests | `client.get_new_friends()` | partial | Reads the new-friend request list. It does not accept or add friends. |
| Group members | `client.get_group_members()` | partial | Implemented, but group work is intentionally postponed for now. |

## Partial Means

For WeChat 4, `partial` usually means one or more of these limitations apply:

- It requires WeChat to be visible and may move focus.
- It uses keyboard, mouse, or clipboard fallback instead of a pure background API.
- It depends on current visible UIA nodes and can be affected by WeChat UI changes.
- It may read only currently loaded/visible data unless the method explicitly scrolls.

## Not Implemented For WeChat 4

These capabilities remain unsupported in the current WeChat 4 implementation:

- Login and QR-code login flows.
- Online state and full account profile.
- Recent group discovery, sub windows, and chat close.
- URL cards, emojis, audio sending, typing text simulation.
- `@all`, `@member`, and structured `@me` detection.
- Full background history loading across chats.
- Quote, forward, merge forward, delete, multi-select, sender-info actions.
- Accepting/adding new friends and contact editing.
- Group create/add/remove/manage. Group-specific work is postponed.
- File download, file manager, batch file downloads.
- Image preview, image save, OCR.
- Dialog read/confirm/cancel.
- Moment/朋友圈 operations.

## Examples

```powershell
uv run python examples\smoke.py
uv run python examples\current_chat.py
uv run python examples\session_list.py
uv run python examples\read_messages.py
uv run python examples\message_history.py --pages 5 --limit 50
uv run python examples\send_text.py
uv run python examples\send_file.py
uv run python examples\send_image.py .\sample.png --who 文件传输助手
uv run python examples\listener.py
uv run python examples\current_chat_listener.py --seconds 30
uv run python examples\current_chat_auto_reply.py --reply "pong" --contains "ping" --seconds 60 --once
uv run python examples\unread_sessions.py
uv run python examples\unread_personal_auto_reply.py --reply "pong" --seconds 60 --once
uv run python examples\new_friends.py --pages 3
```

Run send examples only against chats you are comfortable testing with. The SDK does not fake sends.

## Auto Reply

Current auto reply is built on the listener:

1. `MessageListener.poll_once()` calls `client.get_next_new_message()`.
2. `get_next_new_message()` reads the current visible chat messages.
3. New messages are detected by comparing `Message.id`, which uses UIA runtime ids when available.
4. The callback can call `event.client.send_msg(..., who=event.chat_name)`.

Limitations:

- It monitors the currently open chat only.
- The first poll builds a baseline and usually does not trigger a reply.
- It may move focus because sending uses clipboard and keyboard interaction.
- It is not a global WeChat notification hook.

Unread personal auto reply is a separate foreground workflow:

1. Scan visible `ChatSessionCell.Name` values in the session list.
2. Treat lines like `[1条]` as unread-count markers.
3. Ignore muted sessions even if their text contains `[N条]`.
4. Ignore plain red dots because they do not expose a numeric unread count.
5. Skip obvious group/public/service sessions by name heuristics. `文件传输助手` is not hard-filtered.
6. Open each unread personal session and emit events for the latest unread-count messages.
7. Reply with `send_msg()`.

This workflow can reply to multiple personal chats such as A/B/C, but it will switch the active WeChat chat and can mark sessions as read. Group sessions are intentionally skipped for now.

## File And Image Notes

Sending files and images is available through `send_file`.

File download, file manager, image preview, image save, and OCR remain unsupported for WeChat 4 because the current probe did not expose reliable file/image message controls in the open chat. These should be implemented only after dumping a chat that contains real file and image messages and confirming their UIA classes, context menu entries, and save/download buttons.
