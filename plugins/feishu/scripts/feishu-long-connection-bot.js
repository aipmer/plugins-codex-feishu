#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const Lark = require('@larksuiteoapi/node-sdk');

const DEFAULT_REPLY_TEXT = '收到，我已接入 Codex Feishu 插件。';

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

function parseTextContent(content) {
  if (!content || typeof content !== 'string') {
    return '';
  }
  try {
    const parsed = JSON.parse(content);
    return parsed && typeof parsed.text === 'string' ? parsed.text : '';
  } catch (error) {
    return '';
  }
}

function shouldReply(data) {
  const message = data && data.message ? data.message : {};
  const sender = data && data.sender ? data.sender : {};

  if (sender.sender_type && sender.sender_type !== 'user') {
    return false;
  }
  if (message.chat_type !== 'group') {
    return false;
  }
  if (message.message_type !== 'text') {
    return false;
  }

  return Boolean(message.chat_id);
}

async function start() {
  const baseConfig = {
    appId: requiredEnv('FEISHU_APP_ID'),
    appSecret: requiredEnv('FEISHU_APP_SECRET'),
    appType: Lark.AppType.SelfBuild,
    domain: Lark.Domain.Feishu,
  };
  const replyText = (process.env.FEISHU_BOT_REPLY_TEXT || DEFAULT_REPLY_TEXT).trim() || DEFAULT_REPLY_TEXT;

  const client = new Lark.Client(baseConfig);
  const wsClient = new Lark.WSClient({
    ...baseConfig,
    loggerLevel: Lark.LoggerLevel.info,
  });

  const eventDispatcher = new Lark.EventDispatcher({}).register({
    'im.message.receive_v1': async (data) => {
      if (!shouldReply(data)) {
        return;
      }

      const { message } = data;
      parseTextContent(message.content);

      const response = await client.im.v1.message.create({
        params: {
          receive_id_type: 'chat_id',
        },
        data: {
          receive_id: message.chat_id,
          msg_type: 'text',
          content: JSON.stringify({ text: replyText }),
        },
      });

      console.log(JSON.stringify({
        event_type: 'im.message.receive_v1',
        chat_id: message.chat_id,
        source_message_id: message.message_id || null,
        reply_message_id: response && response.data ? response.data.message_id : null,
      }));
    },
  });

  console.log('Feishu long-connection bot starting...');
  console.log('Listening for im.message.receive_v1 group text messages.');

  wsClient.start({ eventDispatcher });
}

if (require.main === module) {
  start().catch((error) => {
    console.error('Feishu long-connection bot failed:', error.message);
    process.exit(1);
  });
}

module.exports = {
  parseTextContent,
  shouldReply,
  start,
};
