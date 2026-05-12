# WeChat 4 UIA Selectors

This file records the UIA nodes used by the current WeChat 4 implementation.

## Window

| Area | UIA field | Value |
| --- | --- | --- |
| Top-level window class | Win32 class | `Qt51514QWindowIcon` |
| Process | executable | `Weixin.exe` |
| UIA root class | `ClassName` | `mmui::MainWindow` |

## Chat

| Feature | ControlType | ClassName | AutomationId / Name |
| --- | --- | --- | --- |
| Current chat title | `TextControl` | varies | automation id ends with `current_chat_name_label` |
| Session list | `ListControl` | `mmui::XTableView` | `session_list` |
| Session item | `ListItemControl` | `mmui::ChatSessionCell` | session cell name contains visible chat text |
| Unread marker | `ListItemControl` | `mmui::ChatSessionCell` | numeric unread count appears as a line like `[1条]` in `Name`; muted sessions also expose `[N条]` and must be ignored |
| Message list | `ListControl` | `mmui::RecyclerListView` | `chat_message_list` |
| Text message item | `ListItemControl` | `mmui::ChatTextItemView` | message content in `Name` |
| Rich/bubble item | `ListItemControl` | `mmui::ChatBubbleItemView` / `mmui::ChatBubbleReferItemView` | message content in `Name` |
| Input box | `EditControl` | `mmui::ChatInputField` | `chat_input_field` |
| Send button | `ButtonControl` | `mmui::XOutlineButton` | name is the localized send text |
| Search box | `EditControl` | `mmui::XValidatorTextEdit` | name is the localized search text |

## Navigation

| Feature | ControlType | ClassName | Name |
| --- | --- | --- | --- |
| Chat tab | `ButtonControl` | `mmui::XTabBarItem` | localized WeChat tab name |
| Contact tab | `ButtonControl` | `mmui::XTabBarItem` | localized contacts tab name |

## Contacts

| Feature | ControlType | ClassName | AutomationId / Name |
| --- | --- | --- | --- |
| Contact list | `ListControl` | `mmui::StickyHeaderRecyclerListView` | `primary_table_.contact_list` |
| Contact group header | `ListItemControl` / group-like item | `mmui::ContactsCellGroupView` | name contains localized contacts text |
| Contact item | `ListItemControl` | `mmui::ContactsCellItemView` | contact display name in `Name` |
| New-friend entry | `ListItemControl` | `mmui::ContactsCellGroupView` | name is `新的朋友` |
| New-friend item | `ListItemControl` | `mmui::XTableCell` | request text and status in `Name` |
| Profile display name | `TextControl` | varies | automation id ends with `display_name_text` |
| Profile text field | `TextControl` | `mmui::ProfileTextView` | value in `Name` |

## Listener

Listener support is built on top of message UIA runtime ids:

- `get_all_message()` reads visible message items.
- `get_next_new_message()` compares `element.GetRuntimeId()` values.
- `MessageListener` polls `get_next_new_message()` and de-duplicates events by `Message.id`.
- The first listener poll records the current visible messages as the baseline and usually emits no event.

This is current-chat polling, not multi-chat background monitoring.
