# Privacy Policy

**WhatsApp Full Chat Screenshot** — last updated 2026-06-13

## Short version

This extension collects **nothing**. It has no servers, no analytics, no
tracking, no accounts, and makes no network requests. Everything happens
locally in your browser. Your messages never leave your computer.

## What the extension does with your data

- It reads the **currently open WhatsApp Web conversation** in your active tab
  only while you press *Capture full conversation*, in order to scroll through
  it and take screenshots.
- The screenshots are stitched into PNG file(s) **on your own machine** and
  saved to your browser's **Downloads** folder.
- No message content, image, contact, or metadata is sent anywhere. There is no
  remote endpoint of any kind.

## Permissions and why they are needed

| Permission                       | Why                                                                 |
| -------------------------------- | ------------------------------------------------------------------- |
| `activeTab` / `tabs`             | Capture the visible area of the WhatsApp tab you triggered.         |
| `scripting`                      | Inject the capture script into the WhatsApp tab on demand.          |
| `downloads`                      | Save the finished PNG(s) to your Downloads folder.                  |
| `storage`                        | Reserved for local settings; no personal data is stored.            |
| host: `https://web.whatsapp.com/*` | Limit the extension strictly to WhatsApp Web — nothing else.      |

## Data retention

None held by the extension. The only output is the PNG file(s) you chose to
create, stored locally by you.

## Contact

Jens Polomski — jens@snipki.de
