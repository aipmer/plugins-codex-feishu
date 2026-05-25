# Workflows

## Summarize Recent Group Messages

1. Use `im_v1_chat_list` to find the target chat.
2. Use `im_v1_message_list` to fetch recent messages.
3. Summarize decisions, blockers, owners, and next actions.
4. Optionally send the summary back through `im_v1_message_create`.

## Bot-Style Feishu Reply

1. Use `wiki_v1_node_search` with the user's topic.
2. Resolve promising nodes with `wiki_v2_space_getNode`.
3. Read Docx content when the node points to a document.
4. Draft a concise answer for the user or group.
5. Send the reply with `im_v1_message_create`.

## Codex Project Digest Push

1. Collect the relevant Codex project progress inputs.
2. Summarize completed work, in-progress work, risks, and next steps.
3. Convert the summary into a Feishu-friendly message.
4. Preview the message locally before sending.
5. Send a short test message to the configured `open_id` or `chat_id`.
6. Send the digest to the target chat with `im_v1_message_create`.

Local command path:

```bash
npm run feishu:project-update -- --preview --file ./digest.md
npm run feishu:project-update -- --test --send
npm run feishu:project-update -- --send --file ./digest.md
```

If the command reports missing configuration, guide the user through `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_DEFAULT_RECEIVE_ID`, and `FEISHU_DEFAULT_RECEIVE_ID_TYPE` before sending.

## Docs/Wiki Retrieval To Doc Write-Back

1. Search Feishu Docs or Wiki by keyword.
2. Read the selected document content.
3. Summarize the background, decisions, risks, and next steps with Codex.
4. Import the final Markdown into Feishu Docs.
5. Send the created document reference back to the target chat.

See `examples/docs-wiki-to-doc.md`.

## Write Automation Result to Bitable

1. Locate `app_token` and `table_id`.
2. Use `feishu_openapi_request` to query or update the relevant Bitable endpoint.
3. Create or update the record.
4. Push a concise completion message to Feishu IM.

Recommended initial tables:

- Project status
- Release records
- Risk tracker
- Case study intake

See `examples/bitable-project-templates.md`.

## Event Subscription Extension

For bot mentions or passive message intake, use the bundled webhook receiver or deploy the same flow to your own service:

```text
Feishu event callback
  -> verify challenge
  -> verify token
  -> decrypt event when Encrypt Key is enabled
  -> normalize event
  -> call agent workflow
  -> send result with im_v1_message_create
```

Local receiver:

```bash
export FEISHU_VERIFICATION_TOKEN="xxx"
export FEISHU_ENCRYPT_KEY="xxx"

scripts/feishu_webhook_server.py
```

Cloudflare Workers, Vercel Functions, or an existing OpenClaw/Hermes service are suitable production hosts.

See `reference/webhook.md` for the Feishu Open Platform configuration checklist.
